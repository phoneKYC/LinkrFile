"""
utils/i18n.py — Internationalization (EN / AR).
Add more languages by adding keys to STRINGS.
"""

STRINGS: dict = {
    "en": {
        "start": (
            "👋 <b>Welcome to Linkr Bot!</b>\n\n"
            "Send me any file and I'll upload it to GoFile\n"
            "and give you a direct download link.\n\n"
            "📎 Supports: videos, audio, photos, documents, archives…\n"
            "📦 Up to 2 GB per file.\n"
            "⏳ Links expire after 10 days of inactivity.\n\n"
            "🔧 Use /settings to configure.\n"
            "ℹ️ Use /help for commands.\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "<b>Developed by IIDZII Dev</b>\n"
            "<i>Professional File-to-Link bot powered by GoFile</i>"
        ),
        "help": (
            "📖 <b>Commands</b>\n\n"
            "/start — Welcome message\n"
            "/help — This message\n"
            "/settings — Configure the bot\n"
            "/cancel — Cancel active upload\n\n"
            "<b>Usage:</b> Just send any file and I'll handle the rest!"
        ),
        "settings_menu": "⚙️ <b>Settings</b> for this chat:",
        "settings_language": "🌐 Language",
        "on": "✅ ON",
        "off": "❌ OFF",
        "uploading": "⬆️ Uploading <b>{filename}</b> ({size})…",
        "uploaded": (
            "✅ <b>File uploaded successfully!</b>\n\n"
            "📄 {filename}\n"
            "📦 {size}\n"
            "🔗 {link}\n"
            "⏳ Expires: 10 days of inactivity"
        ),
        "uploaded_direct": (
            "✅ <b>File uploaded successfully!</b>\n\n"
            "📄 {filename}\n"
            "📦 {size}\n"
            "🔗 <code>{link}</code>\n"
            "⏳ Expires: 10 days of inactivity"
        ),
        "copy_link": "📋 Copy Link",
        "error_no_file": "❌ No file detected. Please send a file.",
        "error_too_large": "❌ File too large ({size}). Max: {max}MB.",
        "error_upload": "❌ Upload failed:\n<code>{error}</code>",
        "error_download": "❌ Failed to download file from Telegram.",
        "error_forbidden": "⛔ You are not allowed to use this bot.",
        "cancelled": "🚫 Upload cancelled.",
        "cancel_nothing": "Nothing to cancel.",
        "stats_title": "📊 <b>Bot Statistics</b>",
        "stats_line": "• {key}: <b>{value}</b>",
        "admin_only": "⛔ Admin only.",
        "broadcast_usage": "Usage: /broadcast &lt;message&gt;",
    },
    "ar": {
        "start": (
            "👋 <b>مرحباً بك في Linkr Bot!</b>\n\n"
            "أرسل لي أي ملف وسأقوم برفعه لـ GoFile\n"
            "وأعطيك رابط تحميل مباشر.\n\n"
            "📎 يدعم: فيديو، صوت، صور، مستندات، ملفات مضغوطة…\n"
            "📦 حتى 2 جيجابايت للملف الواحد.\n"
            "⏳ الروابط تنتهي بعد 10 أيام بدون نشاط.\n\n"
            "🔧 استخدم /settings للإعدادات.\n"
            "ℹ️ استخدم /help للأوامر.\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "<b>تطوير بواسطة IIDZII Dev</b>\n"
            "<i>بوت احترافي لتحويل الملفات لروابط مدعوم بـ GoFile</i>"
        ),
        "help": (
            "📖 <b>الأوامر</b>\n\n"
            "/start — رسالة الترحيب\n"
            "/help — هذه الرسالة\n"
            "/settings — إعدادات البوت\n"
            "/cancel — إلغاء الرفع الحالي\n\n"
            "<b>الاستخدام:</b> فقط أرسل أي ملف وسأتعامل مع الباقي!"
        ),
        "settings_menu": "⚙️ <b>الإعدادات</b> لهذه المحادثة:",
        "settings_language": "🌐 اللغة",
        "on": "✅ مفعّل",
        "off": "❌ معطّل",
        "uploading": "⬆️ جارٍ رفع <b>{filename}</b> ({size})…",
        "uploaded": (
            "✅ <b>تم رفع الملف بنجاح!</b>\n\n"
            "📄 {filename}\n"
            "📦 {size}\n"
            "🔗 {link}\n"
            "⏳ ينتهي: بعد 10 أيام بدون نشاط"
        ),
        "uploaded_direct": (
            "✅ <b>تم رفع الملف بنجاح!</b>\n\n"
            "📄 {filename}\n"
            "📦 {size}\n"
            "🔗 <code>{link}</code>\n"
            "⏳ ينتهي: بعد 10 أيام بدون نشاط"
        ),
        "copy_link": "📋 نسخ الرابط",
        "error_no_file": "❌ لم يتم اكتشاف ملف. يرجى إرسال ملف.",
        "error_too_large": "❌ الملف كبير جداً ({size}). الحد الأقصى: {max} ميغابايت.",
        "error_upload": "❌ فشل الرفع:\n<code>{error}</code>",
        "error_download": "❌ فشل تنزيل الملف من تيليجرام.",
        "error_forbidden": "⛔ غير مسموح لك باستخدام هذا البوت.",
        "cancelled": "🚫 تم إلغاء الرفع.",
        "cancel_nothing": "لا يوجد شيء لإلغائه.",
        "stats_title": "📊 <b>إحصائيات البوت</b>",
        "stats_line": "• {key}: <b>{value}</b>",
        "admin_only": "⛔ للمشرفين فقط.",
        "broadcast_usage": "الاستخدام: /broadcast &lt;رسالة&gt;",
    },
}

SUPPORTED_LANGUAGES = list(STRINGS.keys())


def t(key: str, lang: str = "en", **kwargs) -> str:
    """Translate a key, falling back to English."""
    lang_map = STRINGS.get(lang) or STRINGS["en"]
    text = lang_map.get(key) or STRINGS["en"].get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    return text