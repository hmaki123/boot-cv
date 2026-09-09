"""
config.py - إعدادات البوت والكلمات المفتاحية
"""
import os

# ===== بيانات المستخدم (من GitHub Secrets) =====
GMAIL_ADDRESS      = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")
YOUR_NAME          = os.environ.get("YOUR_NAME", "")
YOUR_PHONE         = os.environ.get("YOUR_PHONE", "")
YOUR_EMAIL         = os.environ.get("GMAIL_ADDRESS", "")

# ===== كلمات البحث =====
SEARCH_KEYWORDS = [
    # إنجليزي
    "planetarium",
    "dome operator",
    "dome projectionist",
    "digital planetarium",
    "full dome",
    "fulldome",
    "sky theater",
    "astronomy center operator",
    "star theater",
    "astronomical dome",
    "celestial theater",
    # عربي
    "قبة فلكية",
    "مشغل قبة",
    "مدير قبة فلكية",
    "مشغل عروض فلكية",
    "مركز فلكي",
    "مسرح فلكي",
    "قبة النجوم",
    "عروض القبة",
]

# ===== الدول العربية المستهدفة =====
ARAB_COUNTRIES = [
    "Egypt", "Saudi Arabia", "UAE", "Kuwait", "Qatar",
    "Bahrain", "Oman", "Jordan", "Lebanon", "Iraq",
    "Libya", "Tunisia", "Algeria", "Morocco", "Sudan",
    "مصر", "السعودية", "الإمارات", "الكويت", "قطر",
    "البحرين", "عُمان", "الأردن", "لبنان", "العراق",
]

ARAB_COUNTRY_CODES = [
    "EG", "SA", "AE", "KW", "QA", "BH", "OM",
    "JO", "LB", "IQ", "LY", "TN", "DZ", "MA", "SD"
]

# ===== إعدادات البوت =====
DB_PATH = "data/jobs_seen.db"
CV_PATH = "cv/CV.pdf"
CHECK_INTERVAL_HOURS = 6

# ===== إعدادات الإيميل =====
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
