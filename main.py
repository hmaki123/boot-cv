"""
main.py - نقطة البداية - الدورة الرئيسية للبوت
"""
import logging
import sys
from src.config      import CV_PATH
from src.db_manager  import init_db, is_new_job, mark_job_as_applied
from src.scraper     import get_all_jobs
from src.email_sender import send_application, get_recipient_email
from src.telegram_notify import (
    notify_startup, notify_job_found,
    notify_daily_summary, notify_error
)
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("data/bot.log", encoding="utf-8"),
    ]
)
log = logging.getLogger(__name__)


def run():
    log.info("=" * 60)
    log.info("🔭 Planetarium Job Hunter Bot - بدء الدورة")
    log.info("=" * 60)

    # تأكد إن قاعدة البيانات موجودة
    init_db()
    os.makedirs("data", exist_ok=True)

    # تأكد إن الـ CV موجود
    if not os.path.exists(CV_PATH):
        msg = f"❌ الـ CV مش موجود! ضع الـ CV في: {CV_PATH}"
        log.error(msg)
        notify_error(msg)
        return

    # ابعت تنبيه إن البوت اشتغل
    notify_startup()

    # جيب كل الشغلانات من المواقع
    log.info("\n🔍 بيدور على شغلانات...")
    all_jobs = get_all_jobs()

    new_jobs     = []
    applied_jobs = []

    for job in all_jobs:
        job_id = job.get("id", "")

        # تحقق إن الشغلانة جديدة
        if not is_new_job(job_id):
            log.debug(f"⏭️  تجاهل (سبق التقديم): {job.get('title')} @ {job.get('company')}")
            continue

        new_jobs.append(job)
        log.info(f"\n🆕 شغلانة جديدة: {job.get('title')} @ {job.get('company')}")
        log.info(f"   📍 {job.get('location')} | 🌐 {job.get('source')}")
        log.info(f"   🔗 {job.get('url')}")

        # حاول تبعت الإيميل
        recipient = get_recipient_email(job)
        email_sent = False

        if recipient:
            email_sent = send_application(job, recipient)
            if email_sent:
                applied_jobs.append(job)
        else:
            log.info(f"   ⚠️  مش لاقي إيميل تواصل - محتاج تتقدم يدوياً")

        # سجل الشغلانة في قاعدة البيانات
        mark_job_as_applied(job)

        # ابعت تنبيه تيليجرام
        notify_job_found(job, email_sent)

    # ملخص الدورة
    log.info("\n" + "=" * 60)
    log.info(f"📊 انتهت الدورة:")
    log.info(f"   🔍 إجمالي شغلانات: {len(all_jobs)}")
    log.info(f"   🆕 شغلانات جديدة: {len(new_jobs)}")
    log.info(f"   📧 إيميلات اتبعت: {len(applied_jobs)}")
    log.info("=" * 60)

    # ابعت الملخص اليومي على تيليجرام
    notify_daily_summary(len(new_jobs), len(applied_jobs), new_jobs)


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        log.exception(f"💥 خطأ غير متوقع: {e}")
        notify_error(str(e))
        sys.exit(1)
