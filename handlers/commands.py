"""
handlers/commands.py — /start, /help, /settings, /cancel
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import cfg
from database import get_settings, save_settings
from utils import t, SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)


async def _lang(update: Update) -> str:
    s = await get_settings(update.effective_chat.id)
    return s.get("language", "en")


# ─────────────────────────────────────────────────────────────────────────────
# /start
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user and not cfg.is_allowed(update.effective_user.id):
        await update.message.reply_text(t("error_forbidden"))
        return
    lang = await _lang(update)
    await update.message.reply_html(t("start", lang))


# ─────────────────────────────────────────────────────────────────────────────
# /help
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = await _lang(update)
    await update.message.reply_html(t("help", lang))


# ─────────────────────────────────────────────────────────────────────────────
# /settings
# ─────────────────────────────────────────────────────────────────────────────

def _settings_keyboard(s: dict, lang: str) -> InlineKeyboardMarkup:
    rows = []
    lang_buttons = []
    for code in SUPPORTED_LANGUAGES:
        marker = "✅ " if code == s["language"] else ""
        lang_buttons.append(
            InlineKeyboardButton(
                f"{marker}{code.upper()}", callback_data=f"lang:{code}"
            )
        )
    rows.append(lang_buttons)
    return InlineKeyboardMarkup(rows)


async def cmd_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    s = await get_settings(chat_id)
    lang = s.get("language", "en")
    kb = _settings_keyboard(s, lang)
    await update.message.reply_html(t("settings_menu", lang), reply_markup=kb)


# ─────────────────────────────────────────────────────────────────────────────
# Callback: language switch
# ─────────────────────────────────────────────────────────────────────────────

async def callback_settings(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()

    chat_id = update.effective_chat.id
    data = query.data

    if data.startswith("lang:"):
        lang_code = data[5:]
        await save_settings(chat_id, language=lang_code)
        s = await get_settings(chat_id)
        kb = _settings_keyboard(s, lang_code)
        try:
            await query.edit_message_reply_markup(reply_markup=kb)
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# /cancel
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = await _lang(update)
    await update.message.reply_text(t("cancel_nothing", lang))