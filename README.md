<p align="center">
  <img src="https://img.icons8.com/color/96/link.png" width="96" height="96" alt="linkr-bot logo"/>
</p>

<h1 align="center">linkr-bot</h1>

<p align="center">
  <b>بوت تيليجرام احترافي لتحويل الملفات إلى روابط تحميل مباشرة</b><br/>
  <i>Professional Telegram File-to-Link bot powered by GoFile</i>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue.svg" alt="Python 3.12"/>
  <img src="https://img.shields.io/badge/GoFile-API-green.svg" alt="GoFile API"/>
  <img src="https://img.shields.io/badge/Max_File-2GB-orange.svg" alt="2GB"/>
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License"/>
  <img src="https://img.shields.io/badge/Developer-IIDZII%20Dev-red.svg" alt="IIDZII Dev"/>
</p>

<p align="center">
  <a href="#-المميزات">المميزات</a> &bull;
  <a href="#-التثبيت-السريع">التثبيت</a> &bull;
  <a href="#-الأوامر">الأوامر</a> &bull;
  <a href="#%EF%B8%8F-deployment-guides">Deployment</a> &bull;
  <a href="#-هيكل-المشروع">الهيكل</a>
</p>

---

## ✨ المميزات | Features

- **رفع تلقائي** — أرسل أي ملف ويُرفع تلقائياً لـ GoFile
- **جميع أنواع الملفات** — فيديو، صوت، صور، مستندات، أرشيفات...
- **رابط تحميل مباشر** — مع أو بدون GoFile Token
- **زر نسخ الرابط** — زر شفاف لنسخ الرابط بنقرة واحدة
- **صفر تخزين محلي** — الملف يُمرّر stream من تيليجرام → GoFile
- **خفيف جداً** — بدون ffmpeg، Docker image ~80MB فقط
- **ثنائي اللغة** — الإنجليزية والعربية
- **إحصائيات** — تتبع الملفات المرفوعة وحجمها

---

## ⚡ التثبيت السريع | Quick Start

### الطريقة 1: تشغيل محلي

```bash
git clone https://github.com/IIDZII-Dev/linkr-bot.git
cd linkr-bot

cp .env.example .env
# عدّل .env وضع BOT_TOKEN

pip install -r requirements.txt
python bot.py
```

### الطريقة 2: Docker

```bash
git clone https://github.com/IIDZII-Dev/linkr-bot.git
cd linkr-bot
cp .env.example .env
docker compose up -d
```

---

## 📖 الأوامر | Commands

| الأمر | الوصف | الوصول |
|-------|-------|--------|
| `/start` | رسالة الترحيب | الجميع |
| `/help` | عرض الأوامر | الجميع |
| `/settings` | تغيير اللغة | الجميع |
| `/cancel` | إلغاء الرفع | الجميع |
| `/stats` | إحصائيات البوت | مشرفون |
| `/broadcast` | إرسال رسالة جماعية | مشرفون |

> **الاستخدام:** أرسل أي ملف مباشرة وسيتم رفعه تلقائياً!

---

## ⚙️ المتغيرات البيئية | Environment Variables

| المتغير | مطلوب؟ | الوصف | الافتراضي |
|---------|--------|-------|-----------|
| `BOT_TOKEN` | ✅ نعم | توكن البوت من @BotFather | — |
| `BOT_API_URL` | لا | عنوان API | `https://api.telegram.org` |
| `GOFILE_TOKEN` | لا | توكن GoFile (للروابط المباشرة) | — |
| `MAX_FILE_SIZE` | لا | الحد الأقصى للملف (MB) | `50` |
| `CONCURRENT_UPDATES` | لا | التحديثات المتزامنة | `30` |
| `DEFAULT_LANGUAGE` | لا | اللغة الافتراضية | `en` |
| `WHITELIST` | لا | قائمة المستخدمين المسموحين | (الكل) |
| `ADMINS` | لا | معرّفات المشرفين | — |
| `LOG_LEVEL` | لا | مستوى السجل | `INFO` |

### GoFile Token (اختياري)

بدون Token: البوت يرفع كضيف ويرجع **رابط صفحة التحميل**.

مع Token: البوت يرجع **رابط تحميل مباشر** (بدون صفحة وسيطة).

للحصول على Token:
1. أنشئ حساباً على [gofile.io](https://gofile.io)
2. اذهب لصفحة حسابك
3. انسخ API Token
4. ضعه في `GOFILE_TOKEN`

---

## 🌐 Deployment Guides

### 1. Railway 🚂 (الموصى بها)

```bash
# 1. أنشئ مشروعاً على https://railway.app
# 2. Deploy from GitHub repo
# 3. أضف المتغيرات:
#    BOT_TOKEN = your_token_here
```

**Railway CLI:**
```bash
npm install -g @railway/cli
railway login
railway init
railway variables set BOT_TOKEN=your_token_here
railway up
```

**ملاحظات Railway:**
- البوت يعمل كـ worker عبر `Procfile`
- `runtime.txt` يحدد Python 3.12
- الملفات تُخزن مؤقتاً في `/tmp` (تتنظف تلقائياً)
- لا يحتاج ffmpeg أو حزم إضافية
- 1GB كافي جداً (البوت لا يخزن شيئاً)

---

### 2. Render 🎨

```bash
# 1. New → Web Service
# 2. ربط المستودع
# 3. Build Command: pip install -r requirements.txt
# 4. Start Command: python bot.py
```

---

### 3. Heroku 🟣

```bash
heroku create your-bot-name
heroku buildpacks:set heroku/python
heroku config:set BOT_TOKEN=your_token_here
git push heroku main
```

> `Procfile` يحدد `worker: python bot.py` — نوع التطبيق = Worker

---

### 4. Koyeb ⚡

```bash
# 1. Create Service → GitHub
# 2. Build type: Dockerfile
# 3. أضف BOT_TOKEN في Environment variables
```

---

### 5. Fly.io ✈️

```bash
curl -L https://fly.io/install.sh | sh
fly auth login
fly launch
fly secrets set BOT_TOKEN=your_token_here
fly deploy
```

---

### 6. VPS (Ubuntu/Debian)

```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-venv git
git clone https://github.com/IIDZII-Dev/linkr-bot.git
cd linkr-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env && nano .env
python bot.py
```

**كمخدمة systemd:**
```bash
sudo tee /etc/systemd/system/linkr-bot.service << 'EOF'
[Unit]
Description=linkr-bot Telegram Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/home/your_username/linkr-bot
Environment=PATH=/home/your_username/linkr-bot/venv/bin
ExecStart=/home/your_username/linkr-bot/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable linkr-bot
sudo systemctl start linkr-bot
```

---

### 7. Docker عام

```bash
git clone https://github.com/IIDZII-Dev/linkr-bot.git
cd linkr-bot
cp .env.example .env && nano .env
docker compose up -d

# أو مباشرة:
docker build -t linkr-bot .
docker run -d --name linkr-bot \
  --env BOT_TOKEN=your_token_here \
  --restart unless-stopped \
  linkr-bot
```

---

## 🏗️ هيكل المشروع | Project Structure

```
linkr-bot/
├── bot.py                 # نقطة الدخول
├── config.py              # إعدادات البيئة
├── database.py            # SQLite (إعدادات + إحصائيات)
├── uploader.py            # GoFile API client
├── handlers/
│   ├── __init__.py
│   ├── commands.py        # /start /help /settings /cancel
│   ├── files.py           # استقبال الملفات + الرفع لـ GoFile
│   └── admin.py           # /stats /broadcast
├── utils/
│   ├── __init__.py
│   ├── i18n.py            # الترجمة (EN/AR)
│   └── helpers.py         # تنسيق الحجم + أسماء الملفات
├── Procfile               # Railway / Heroku
├── runtime.txt            # نسخة Python
├── nixpacks.toml          # Railway Nixpacks
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

---

## 🔧 كيف يعمل | How It Works

```
المستخدم يرسل ملف
        ↓
البوت يُنزّل الملف من تيليجرام (stream → /tmp)
        ↓
البوت يرفع الملف لـ GoFile API
        ↓
البوت يحذف الملف المؤقت فوراً
        ↓
البوت يرسل رابط التحميل مع زر "نسخ"
```

**لا يتم تخزين أي ملف محلياً** — البوت خفيف ومناسب لأي خادم.

---

## 🌍 الترجمة | Localization

لإضافة لغة جديدة، أضفها في `utils/i18n.py`:

```python
STRINGS["fr"] = {
    "start": "Bienvenue sur Linkr Bot!\n\nDéveloppé par IIDZII Dev",
    "help": "📖 <b>Commandes</b>\n\n/start — Message de bienvenue\n...",
    # ... أضف كل المفاتيح
}
```

---

## 🛡️ الأمان | Security

- يعمل بمستخدم غير root في Docker
- المتغيرات الحساسة من البيئة فقط
- لا يُخزن أي بيانات شخصية أو ملفات
- القائمة البيضاء تقيّد الوصول
- `.env` مستبعد من Git

---

## 🤝 المساهمة | Contributing

1. Fork المشروع
2. أنشئ فرعاً جديداً (`git checkout -b feature/amazing`)
3. أرسل التعديلات (`git commit -m 'Add amazing feature'`)
4. ارفع الفرع (`git push origin feature/amazing`)
5. افتح Pull Request

---

## 📄 الترخيص | License

هذا المشروع مرخص تحت رخصة [MIT](LICENSE).

Developed with ❤️ by **[IIDZII Dev](https://github.com/IIDZII-Dev)**