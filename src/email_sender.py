"""
email_sender.py - بيبعت إيميل احترافي مع الـ CV
"""
import re
import smtplib
import logging
import os
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText
from email.mime.base      import MIMEBase
from email               import encoders
from src.config import (
    GMAIL_ADDRESS, GMAIL_APP_PASSWORD,
    YOUR_NAME, YOUR_PHONE, YOUR_EMAIL,
    SMTP_HOST, SMTP_PORT, CV_PATH
)

log = logging.getLogger(__name__)

HEADERS_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def build_cover_letter(job: dict, language: str = "en") -> str:
    """بيبني cover letter مخصوص لكل شغلانة"""

    title   = job.get("title",   "Planetarium Operator")
    company = job.get("company", "Your Organization")

    if language == "ar":
        return f"""السيد/السيدة المسؤول عن التوظيف المحترم،

تحية طيبة وبعد،

أتقدم بكل احترام لشغل وظيفة **{title}** في مؤسستكم الموقرة **{company}**، وذلك إيماناً مني بأن خبرتي في مجال تشغيل القبب الفلكية تجعلني مرشحاً مناسباً لهذا الدور.

**ما أقدمه:**
• خبرة عملية في تشغيل أنظمة القبة الفلكية الرقمية
• مهارة في تقديم العروض الفلكية للجمهور العام والمتخصص
• إلمام تام بأجهزة العرض وبرامج إدارة القبة
• شغف حقيقي بنشر الوعي الفلكي وتعليم علوم الفضاء

أرفق مع هذا الطلب سيرتي الذاتية كاملة، وأتطلع إلى فرصة مناقشة كيف يمكنني المساهمة في رؤية مؤسستكم.

مع خالص التقدير والاحترام،
{YOUR_NAME}
📞 {YOUR_PHONE}
📧 {YOUR_EMAIL}
"""
    else:
        return f"""Dear Hiring Manager at {company},

I am writing to express my strong interest in the **{title}** position at **{company}**. 
As a dedicated planetarium professional with hands-on experience in dome operations, 
I am excited about the opportunity to contribute to your organization.

**What I bring to the role:**
• Proven experience operating digital planetarium projection systems
• Expertise in delivering captivating astronomical presentations to diverse audiences
• Technical proficiency with dome management software and projection equipment
• A genuine passion for astronomy education and public science outreach

I have attached my CV for your review and would welcome the opportunity to discuss 
how my skills and experience align with your needs.

Thank you for your time and consideration.

Best regards,
{YOUR_NAME}
📞 {YOUR_PHONE}
📧 {YOUR_EMAIL}
"""


def detect_language(job: dict) -> str:
    """بيحدد لغة الشغلانة (عربي أو إنجليزي)"""
    text = f"{job.get('title','')} {job.get('company','')} {job.get('location','')}"
    arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    return "ar" if arabic_chars > 5 else "en"


def get_recipient_email(job: dict) -> str | None:
    """
    بيحاول يجيب إيميل التواصل بطريقتين:
    1. لو الشغلانة نفسها فيها contact_email بياخده مباشرة
    2. بيزور صفحة الشغلانة ويجيب الإيميل بالـ regex
    """
    # أولاً: إيميل مباشر في بيانات الشغلانة
    if job.get("contact_email"):
        return job.get("contact_email")

    # ثانياً: زور صفحة الشغلانة وجيب الإيميل منها
    url = job.get("url", "")
    if not url or "linkedin.com" in url:
        # LinkedIn بيحجب الـ scrapers — مفيش فايدة
        return None

    try:
        resp = requests.get(
            url,
            headers={"User-Agent": HEADERS_UA},
            timeout=12,
        )
        if resp.status_code != 200:
            return None

        # جيب كل الإيميلات في الصفحة بالـ regex
        email_pattern = r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
        emails_found = re.findall(email_pattern, resp.text)

        # فلتر الإيميلات المزعجة أو الغير مفيدة
        blacklist_keywords = [
            "noreply", "no-reply", "donotreply", "notifications",
            "mailer", "support@linkedin", "jobs@linkedin",
            "info@indeed", "noreply@indeed", "privacy@",
            "legal@", "abuse@", "security@",
        ]

        for email in emails_found:
            if not any(bl in email.lower() for bl in blacklist_keywords):
                log.info(f"   📧 لقينا إيميل تواصل: {email}")
                return email

        log.debug(f"   ℹ️  مش لاقي إيميل في: {url[:60]}")
    except Exception as e:
        log.debug(f"   ℹ️  فشل جيب الإيميل من {url[:60]}: {e}")

    return None


def send_application(job: dict, recipient_email: str) -> bool:
    """بيبعت طلب التوظيف مع الـ CV"""

    if not os.path.exists(CV_PATH):
        log.error(f"❌ الـ CV مش موجود في {CV_PATH}!")
        return False

    lang = detect_language(job)
    cover = build_cover_letter(job, language=lang)
    title = job.get("title", "Planetarium Operator")
    company = job.get("company", "")

    subject_en = f"Application for {title} – {YOUR_NAME}"
    subject_ar = f"تقديم على وظيفة {title} – {YOUR_NAME}"
    subject = subject_ar if lang == "ar" else subject_en

    try:
        msg = MIMEMultipart()
        msg["From"]    = GMAIL_ADDRESS
        msg["To"]      = recipient_email
        msg["Subject"] = subject

        # إضافة الـ cover letter
        msg.attach(MIMEText(cover, "plain", "utf-8"))

        # إضافة الـ CV
        with open(CV_PATH, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{YOUR_NAME}_CV.pdf"'
            )
            msg.attach(part)

        # إرسال الإيميل
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, recipient_email, msg.as_string())

        log.info(f"✅ اتبعت إيميل على: {title} @ {company} → {recipient_email}")
        return True

    except Exception as e:
        log.error(f"❌ فشل الإرسال على {company}: {e}")
        return False
