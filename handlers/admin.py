"""
handlers/admin.py — Admin-only commands: /stats, /broadcast
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from config import cfg
from database import stat_all
from utils import t

logger = logging.getLogger(__name__)


def _admin_check(user_id: int | None) -> bool:
    if user_id is None:
        return False
    return cfg.is_admin(user_id)


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not _admin_check(user.id if user else None):
        await update.message.reply_text(t("admin_only"))
        return

    stats = await stat_all()
    if not stats:
        await update.message.reply_text("No stats yet.")
        return

    lines = [t("stats_title")]
    for key, value in sorted(stats.items()):
        label = key.replace("_", " ").title()
        if "bytes" in key:
            from utils import fmt_size
            lines.append(f"• {label}: <b>{fmt_size(value)}</b>")
        else:
            lines.append(t("stats_line", key=label, value=value))

    await update.message.reply_html("\n".join(lines))


async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not _admin_check(user.id if user else None):
        await update.message.reply_text(t("admin_only"))
        return

    if not context.args:
        await update.message.reply_html(t("broadcast_usage"))
        return

    text = " ".join(context.args)
    targets = cfg.whitelist | cfg.admins
    if not targets:
        await update.message.reply_text("No users in whitelist/admins.")
        return

    sent = 0
    failed = 0
    for uid in targets:
        try:
            await context.bot.send_message(chat_id=uid, text=text)
            sent += 1
        except Exception as exc:
            logger.warning("Broadcast to %s failed: %s", uid, exc)
            failed += 1

    await update.message.reply_text(
        f"📣 Broadcast complete.\n✅ Sent: {sent}\n❌ Failed: {failed}"
    )