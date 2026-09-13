"""
telegram_notify.py - بيبعتلك تنبيه على تيليجرام
"""
import requests
import logging
from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

log = logging.getLogger(__name__)


def send_telegram(message: str) -> bool:
    """بيبعت رسالة على تيليجرام"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.warning("⚠️ تيليجرام مش متضبط (TELEGRAM_BOT_TOKEN أو TELEGRAM_CHAT_ID ناقص)")
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id":    TELEGRAM_CHAT_ID,
            "text":       message,
            "parse_mode": "Markdown",
        }
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code != 200:
            # لو فشل بسبب Markdown غير متوافق نبعتها كـ plain text
            payload.pop("parse_mode", None)
            resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        log.error(f"Telegram error: {e}")
        return False


def notify_job_found(job: dict, email_sent: bool) -> None:
    """بيبعت تنبيه لما نلاقي شغلانة جديدة"""
    status = "✅ اتبعت الـ CV" if email_sent else "⚠️ محتاج تتقدم يدوياً"
    msg = (
        f"🔭 *شغلانة قبة فلكية جديدة!*\n\n"
        f"📌 *الوظيفة:* {job.get('title', 'N/A')}\n"
        f"🏢 *الشركة:* {job.get('company', 'N/A')}\n"
        f"📍 *المكان:* {job.get('location', 'N/A')}\n"
        f"🌐 *المصدر:* {job.get('source', 'N/A')}\n"
        f"🔗 [افتح الشغلانة]({job.get('url', '#')})\n\n"
        f"{status}"
    )
    send_telegram(msg)


def notify_daily_summary(total_found: int, total_applied: int, jobs: list) -> None:
    """بيبعت ملخص يومي"""
    msg = (
        f"📊 *تقرير البوت اليومي*\n\n"
        f"🔍 شغلانات اتلقت: *{total_found}*\n"
        f"📧 إيميلات اتبعت: *{total_applied}*\n\n"
    )
    if jobs:
        msg += "*آخر الشغلانات:*\n"
        for j in jobs[:5]:
            msg += f"• {j.get('title')} @ {j.get('company')} ({j.get('location')})\n"

    if total_found == 0:
        msg += "\n😴 مفيش شغلانات جديدة الدورة دي."

    send_telegram(msg)


def notify_error(error_msg: str) -> None:
    """بيبعت تنبيه لو فيه خطأ"""
    msg = f"❌ *خطأ في البوت*\n\n```{error_msg}```"
    send_telegram(msg)


def notify_startup() -> None:
    """بيبعت تنبيه إن البوت اشتغل"""
    send_telegram(
        "🚀 *Planetarium Job Hunter Bot*\n"
        "البوت اشتغل وبيدور على شغلانات القبة الفلكية... 🔭"
    )
