# 🔭 Planetarium Job Hunter Bot

بوت أوتوماتيك بيدور على شغلانات القبة الفلكية في الدول العربية ويبعت الـ CV أوتوماتيك.

---

## ⚡ خطوات الإعداد (مرة واحدة بس)

### الخطوة 1 - رفع المشروع على GitHub

1. اعمل Repository جديد على [github.com](https://github.com) (خليه Private 🔒)
2. ارفع الملفات دي عليه

---

### الخطوة 2 - حول الـ CV لـ base64

افتح PowerShell وشغّل:

```powershell
# غير المسار لمسار الـ CV بتاعك
[Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\path\to\your\CV.pdf")) | Set-Clipboard
```

هيتنسخ تلقائياً في الـ clipboard.

---

### الخطوة 3 - اعمل Telegram Bot

1. افتح تيليجرام وابحث عن **@BotFather**
2. ابعته: `/newbot`
3. اختار اسم للبوت: مثلاً `PlanetariumJobHunter`
4. هيديك **TOKEN** - احتفظ بيه
5. افتح البوت وابعته أي رسالة
6. افتح اللينك ده في المتصفح (غير YOUR_TOKEN):
   ```
   https://api.telegram.org/botYOUR_TOKEN/getUpdates
   ```
7. جوه الـ JSON هتلاقي "chat":{"id": XXXXXXX} - ده الـ Chat ID بتاعك

---

### الخطوة 4 - اعمل Gmail App Password

1. روح myaccount.google.com/security
2. فعّل 2-Step Verification لو مش مفعّل
3. روح App Passwords (ابحث عنها في الـ search)
4. اختار Mail → Windows Computer
5. هيديك كلمة سر مكونة من 16 حرف - احتفظ بيها

---

### الخطوة 5 - أضف الـ Secrets على GitHub

في الـ Repository بتاعك: Settings → Secrets and variables → Actions → New repository secret

أضف الـ Secrets دي واحدة واحدة:

| الاسم | القيمة |
|---|---|
| GMAIL_ADDRESS | إيميلك على Gmail |
| GMAIL_APP_PASSWORD | الـ App Password (16 حرف) |
| TELEGRAM_BOT_TOKEN | التوكن من BotFather |
| TELEGRAM_CHAT_ID | الـ Chat ID بتاعك |
| YOUR_NAME | اسمك الكامل |
| YOUR_PHONE | رقم تليفونك |
| CV_BASE64 | الكود اللي اتنسخ من الخطوة 2 |

---

### الخطوة 6 - شغّل البوت

1. روح Actions في الـ Repository
2. فعّل الـ Actions لو مطلوب منك
3. اضغط على "Planetarium Job Hunter"
4. اضغط "Run workflow" لتجربته أول مرة
5. بعدها بيشتغل أوتوماتيك كل 6 ساعات

---

## المواقع اللي بيسكان عليها

- Google Jobs (بيجمع من كل المواقع)
- Bayt.com (الشرق الأوسط)
- Wuzzuf.net (مصر)
- GulfJobs.com (الخليج)
- LinkedIn (مصر + السعودية + الإمارات + الكويت + قطر)
- Indeed (السعودية + الإمارات + مصر + الكويت + قطر)

---

## كلمات البحث

Planetarium, Dome Operator, Dome Projectionist, Digital Planetarium,
Full Dome, Sky Theater, Star Theater, Astronomy Center,
قبة فلكية, مشغل قبة, مشغل عروض فلكية, مركز فلكي, قبة النجوم
