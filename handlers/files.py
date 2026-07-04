"""
handlers/files.py — Receive files from users and upload to GoFile.
Handles: documents, videos, audio, photos, animations, voice, video notes.
"""

import asyncio
import logging
import os
import tempfile
from typing import Optional

import httpx
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    Update,
)
from telegram.constants import ChatAction
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from config import cfg
from database import get_settings, save_settings, stat_inc
from uploader import upload_file, get_direct_link
from utils import fmt_size, safe_filename, t

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Core: extract file info from any message type
# ─────────────────────────────────────────────────────────────────────────────

def _extract_file_info(message: Message) -> Optional[dict]:
    """Extract file_id, filename, and file_size from any file message."""
    obj = None
    filename = ""

    if message.document:
        obj = message.document
        filename = obj.file_name or ""
    elif message.video:
        obj = message.video
        filename = obj.file_name or f"video_{obj.file_unique_id}.mp4"
    elif message.audio:
        obj = message.audio
        filename = obj.file_name or f"audio_{obj.file_unique_id}.mp3"
    elif message.voice:
        obj = message.voice
        filename = f"voice_{obj.file_unique_id}.ogg"
    elif message.video_note:
        obj = message.video_note
        filename = f"video_note_{obj.file_unique_id}.mp4"
    elif message.animation:
        obj = message.animation
        filename = obj.file_name or f"animation_{obj.file_unique_id}.mp4"
    elif message.photo:
        # Pick the largest photo
        obj = message.photo[-1]
        filename = f"photo_{obj.file_unique_id}.jpg"
    else:
        return None

    return {
        "file_id": obj.file_id,
        "filename": safe_filename(filename),
        "file_size": obj.file_size or 0,
        "unique_id": obj.file_unique_id,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Download file from Telegram
# ─────────────────────────────────────────────────────────────────────────────

async def _download_from_telegram(
    file_id: str,
    dest_path: str,
) -> bool:
    """Stream-download a file from Telegram servers."""
    try:
        # Get file path from Telegram
        file_obj = await _bot.get_file(file_id)
        if not file_obj or not file_obj.file_path:
            return False

        # file_path may already be a full URL when base_file_url is set
        path = file_obj.file_path
        if path.startswith("http"):
            url = path
        else:
            url = f"{cfg.bot_api_url}/file/bot{cfg.bot_token}/{path}"

        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream("GET", url) as resp:
                resp.raise_for_status()
                with open(dest_path, "wb") as f:
                    async for chunk in resp.aiter_bytes(chunk_size=1024 * 1024):
                        f.write(chunk)
        return True
    except Exception as exc:
        logger.error("Telegram download failed: %s", exc)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Process one file: download → upload → send link
# ─────────────────────────────────────────────────────────────────────────────

async def _process_file(
    message: Message,
    context: ContextTypes.DEFAULT_TYPE,
    file_info: dict,
    reply_to: Message = None,
) -> None:
    chat_id = message.chat_id
    settings = await get_settings(chat_id)
    lang = settings.get("language", "en")
    target = reply_to or message

    file_size = file_info["file_size"]

    # Size check
    if file_size > cfg.max_file_size_bytes:
        await target.reply_html(
            t("error_too_large", lang,
              size=fmt_size(file_size),
              max=cfg.max_file_size_mb),
        )
        return

    filename = file_info["filename"]
    size_str = fmt_size(file_size)

    # Show uploading status
    status_msg = await target.reply_html(
        t("uploading", lang, filename=filename, size=size_str),
    )

    await stat_inc("uploads_started")

    # Download from Telegram to temp file
    os.makedirs(cfg.temp_dir, exist_ok=True)
    temp_path = os.path.join(cfg.temp_dir, f"{file_info['unique_id']}_{filename}")

    try:
        ok = await _download_from_telegram(file_info["file_id"], temp_path)
        if not ok:
            await stat_inc("uploads_failed")
            try:
                await status_msg.edit_text(t("error_download", lang))
            except TelegramError:
                pass
            return

        # Upload to GoFile
        result = await upload_file(temp_path, filename)

        if not result.success:
            await stat_inc("uploads_failed")
            try:
                await status_msg.edit_html(
                    t("error_upload", lang, error=result.error),
                )
            except TelegramError:
                pass
            return

        # Try to get direct link if token is available
        direct_link = ""
        if cfg.gofile_token and result.file_id:
            direct_link = await get_direct_link(result.file_id) or ""

        link = direct_link or result.link

        # Track total bytes uploaded
        actual_size = os.path.getsize(temp_path) if os.path.exists(temp_path) else file_size
        await stat_inc("uploads_success")
        await stat_inc("bytes_uploaded", amount=actual_size)

        # Build response
        if direct_link:
            text = t("uploaded_direct", lang,
                     filename=filename, size=fmt_size(actual_size), link=link)
        else:
            text = t("uploaded", lang,
                     filename=filename, size=fmt_size(actual_size), link=link)

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(t("copy_link", lang),
                                  callback_data=f"copy:{link}")]
        ])

        try:
            await status_msg.edit_text(
                text, reply_markup=keyboard, disable_web_page_preview=True,
            )
        except TelegramError:
            # Fallback: send new message if edit fails
            await target.reply_text(
                text, reply_markup=keyboard, disable_web_page_preview=True,
            )
            try:
                await status_msg.delete()
            except TelegramError:
                pass

    finally:
        # Always clean up temp file
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# Generic file handler — works for any file type
# ─────────────────────────────────────────────────────────────────────────────

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message:
        return

    user = update.effective_user
    if user and not cfg.is_allowed(user.id):
        await message.reply_text(t("error_forbidden"))
        return

    file_info = _extract_file_info(message)
    if not file_info:
        await message.reply_text(t("error_no_file"))
        return

    await _process_file(message, context, file_info)


# ─────────────────────────────────────────────────────────────────────────────
# Media group handler (albums)
# ─────────────────────────────────────────────────────────────────────────────

async def handle_media_group(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    message = update.effective_message
    if not message:
        return

    user = update.effective_user
    if user and not cfg.is_allowed(user.id):
        await message.reply_text(t("error_forbidden"))
        return

    # Collect all messages in the same media group
    group_id = message.media_group_id
    if not group_id:
        await handle_file(update, context)
        return

    # Store messages and process after a short delay
    pending = context.bot_data.setdefault("_pending_groups", {})

    if group_id not in pending:
        pending[group_id] = []
        # Schedule processing after 1.5 seconds (wait for all messages)
        asyncio.get_running_loop().call_later(
            1.5,
            lambda: asyncio.ensure_future(
                _process_group(pending.pop(group_id, []), context)
            ),
        )

    pending[group_id].append(message)


async def _process_group(
    messages: list,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Process a batch of media group messages."""
    for msg in messages:
        file_info = _extract_file_info(msg)
        if file_info:
            await _process_file(msg, context, file_info)


# ─────────────────────────────────────────────────────────────────────────────
# Copy-link callback
# ─────────────────────────────────────────────────────────────────────────────

async def callback_copy_link(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    if not query or not query.data:
        return

    await query.answer()

    # Extract link from callback data
    if query.data.startswith("copy:"):
        link = query.data[5:]
        try:
            await query.message.reply_text(link)
        except TelegramError:
            pass


# Bot reference set at init
_bot = None


def set_bot(bot) -> None:
    global _bot
    _bot = bot