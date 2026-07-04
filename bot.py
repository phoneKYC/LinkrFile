"""
bot.py — linkr-bot entry point.
A professional File-to-Link Telegram bot powered by GoFile.

Usage:
    python bot.py
"""

import logging
import os
import sys

from telegram import BotCommand
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from config import cfg

# ─────────────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=getattr(logging, cfg.log_level, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

logger = logging.getLogger("linkr-bot")


# ─────────────────────────────────────────────────────────────────────────────
# Create temp directory
# ─────────────────────────────────────────────────────────────────────────────

os.makedirs(cfg.temp_dir, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# Bot commands menu
# ─────────────────────────────────────────────────────────────────────────────

BOT_COMMANDS = [
    BotCommand("start", "Welcome message"),
    BotCommand("help", "Show all commands"),
    BotCommand("settings", "Configure the bot"),
    BotCommand("cancel", "Cancel active upload"),
    BotCommand("stats", "[Admin] Bot statistics"),
    BotCommand("broadcast", "[Admin] Broadcast a message"),
]


# ─────────────────────────────────────────────────────────────────────────────
# Build Application
# ─────────────────────────────────────────────────────────────────────────────

def build_app() -> Application:
    from handlers import (
        cmd_start, cmd_help, cmd_settings, cmd_cancel, callback_settings,
        handle_file, handle_media_group, callback_copy_link, set_bot,
        cmd_stats, cmd_broadcast,
    )

    builder = (
        Application.builder()
        .token(cfg.bot_token)
        .base_url(cfg.bot_api_url + "/bot")
        .base_file_url(cfg.bot_api_url + "/file/bot")
        .concurrent_updates(cfg.concurrent_updates)
        .read_timeout(120)
        .write_timeout(120)
        .connect_timeout(30)
        .pool_timeout(30)
    )

    app = builder.build()

    # ── Commands ──────────────────────────────────────────────
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("settings", cmd_settings))
    app.add_handler(CommandHandler("cancel", cmd_cancel))

    # ── Admin commands ────────────────────────────────────────
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("broadcast", cmd_broadcast))

    # ── Callbacks ─────────────────────────────────────────────
    app.add_handler(
        CallbackQueryHandler(callback_settings, pattern=r"^lang:")
    )
    app.add_handler(
        CallbackQueryHandler(callback_copy_link, pattern=r"^copy:")
    )

    # ── File handlers (private chats) ─────────────────────────
    # Single file messages
    file_filter = (
        filters.Document.ALL
        | filters.VIDEO
        | filters.AUDIO
        | filters.VOICE
        | filters.VIDEO_NOTE
        | filters.ANIMATION
        | filters.PHOTO
    ) & filters.ChatType.PRIVATE

    # Media groups (albums) — handled separately via media_group_id in handle_file

    # Regular single files (no media_group_id)
    single_file_filter = file_filter

    app.add_handler(MessageHandler(single_file_filter, handle_file))

    # ── Post-init ─────────────────────────────────────────────
    async def post_init(application: Application) -> None:
        # Give file handler access to the bot instance
        set_bot(application.bot)

        await application.bot.set_my_commands(BOT_COMMANDS)
        me = await application.bot.get_me()
        logger.info("🔗  linkr-bot started as @%s (id=%s)", me.username, me.id)
        logger.info(
            "⚙️   Max file: %sMB | GoFile token: %s",
            cfg.max_file_size_mb,
            "set" if cfg.gofile_token else "not set (guest mode)",
        )
        if cfg.gofile_token:
            logger.info("🔑  Direct links enabled")
        else:
            logger.info("ℹ️  Set GOFILE_TOKEN for direct download links")
        if cfg.whitelist:
            logger.info("🔒  Whitelist active: %s user(s)", len(cfg.whitelist))

    app.post_init = post_init  # type: ignore[assignment]

    return app


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    if not cfg.bot_token or cfg.bot_token == "12345678:ABC-DEF1234ghIkl-zyx57W2P0s":
        logger.critical(
            "BOT_TOKEN is not set! Copy .env.example to .env and fill it in."
        )
        sys.exit(1)

    app = build_app()
    logger.info("Starting polling...")
    app.run_polling(
        allowed_updates=[
            "message",
            "callback_query",
        ],
        drop_pending_updates=True,
        close_loop=True,
    )


if __name__ == "__main__":
    main()