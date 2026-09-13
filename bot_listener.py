"""
bot_listener.py - بوت تيليجرام تفاعلي يفضل شغال ويستقبل أوامرك
"""
import time
import logging
import requests
from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from src.db_manager import init_db, is_new_job, mark_job_as_applied, get_all_applied_jobs
from src.scraper import get_all_jobs
from src.email_sender import send_application, get_recipient_email

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def send_msg(chat_id: str, text: str, parse_mode: str = "Markdown") -> bool:
    try:
        payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
        r = requests.post(f"{API_URL}/sendMessage", json=payload, timeout=10)
        if r.status_code != 200:
            payload.pop("parse_mode", None)
            r = requests.post(f"{API_URL}/sendMessage", json=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        log.error(f"Error sending message: {e}")
        return False


def set_bot_commands():
    """تسجيل أوامر المنيو في تيليجرام تلقائياً"""
    commands = [
        {"command": "search", "description": "🔍 بدء البحث عن وظائف الآن"},
        {"command": "latest", "description": "📋 عرض آخر الوظائف المسجلة"},
        {"command": "status", "description": "📊 حالة البوت والإحصائيات"},
        {"command": "help", "description": "ℹ️ المساعدة والتعليمات"}
    ]
    try:
        requests.post(f"{API_URL}/setMyCommands", json={"commands": commands}, timeout=10)
    except Exception as e:
        log.warning(f"Could not set commands: {e}")


def handle_search(chat_id: str):
    send_msg(chat_id, "🔭 *بدأت البحث عن وظائف القبة الفلكية الآن...*\n⏳ قد يستغرق البحث دقيقة للتحقق من جميع المواقع.")
    init_db()
    all_jobs = get_all_jobs()
    new_jobs = []
    applied_count = 0

    for job in all_jobs:
        job_id = job.get("id", "")
        if not is_new_job(job_id):
            continue

        new_jobs.append(job)
        recipient = get_recipient_email(job)
        email_sent = False
        if recipient:
            email_sent = send_application(job, recipient)
            if email_sent:
                applied_count += 1

        mark_job_as_applied(job)

        status_text = "✅ تم إرسال الـ CV تلقائياً" if email_sent else "⚠️ مطلوب تقديم يدوي (لم نجد إيميل مباشر)"
        msg = (
            f"🆕 *وظيفة جديدة عُثر عليها!*\n\n"
            f"📌 *المسمى:* {job.get('title', 'N/A')}\n"
            f"🏢 *المؤسسة:* {job.get('company', 'N/A')}\n"
            f"📍 *المكان:* {job.get('location', 'N/A')}\n"
            f"🌐 *المصدر:* {job.get('source', 'N/A')}\n"
            f"🔗 [رابط الوظيفة]({job.get('url', '#')})\n\n"
            f"{status_text}"
        )
        send_msg(chat_id, msg)

    summary = (
        f"🏁 *اكتمل البحث!*\n\n"
        f"🔍 إجمالي النتائج: *{len(all_jobs)}*\n"
        f"🆕 وظائف جديدة: *{len(new_jobs)}*\n"
        f"📧 إيميلات أرسلت: *{applied_count}*"
    )
    if not new_jobs:
        summary += "\n\n😴 لا توجد وظائف جديدة مضافة في هذه اللحظة."

    send_msg(chat_id, summary)


def handle_latest(chat_id: str):
    init_db()
    jobs = get_all_applied_jobs()
    if not jobs:
        send_msg(chat_id, "📭 لا توجد وظائف مسجلة في قاعدة البيانات حتى الآن.")
        return

    msg = "📋 *آخر الوظائف المسجلة في قاعدة البيانات:*\n\n"
    for j in jobs[:8]:
        msg += f"• *{j.get('title')}* @ {j.get('company')}\n  📍 {j.get('location')} | 🌐 {j.get('source')}\n  🔗 [فتح الرابط]({j.get('url')})\n\n"

    send_msg(chat_id, msg)


def handle_status(chat_id: str):
    init_db()
    jobs = get_all_applied_jobs()
    msg = (
        f"📊 *حالة البوت:*\n\n"
        f"🟢 البوت يعمل ومستعد لتلقي الأوامر.\n"
        f"💾 إجمالي الوظائف في قاعدة البيانات: *{len(jobs)}*"
    )
    send_msg(chat_id, msg)


def handle_help(chat_id: str):
    msg = (
        "👋 *أهلاً بك في بوت Planetarium Job Hunter!*\n\n"
        "الأوامر المتاحة:\n"
        "• /search - يبدأ فحص المواقع فوراً ويبعتلك الجديد\n"
        "• /latest - يعرض آخر الوظائف التي تم العثور عليها\n"
        "• /status - إحصائيات وقاعدة البيانات\n"
        "• /help - عرض هذه الرسالة"
    )
    send_msg(chat_id, msg)


def main():
    if not TELEGRAM_BOT_TOKEN:
        log.error("❌ TELEGRAM_BOT_TOKEN غير محدد في config!")
        return

    log.info("🚀 بدء تشغيل بوت التيليجرام التفاعلي (bot_listener)...")
    set_bot_commands()
    offset = 0

    while True:
        try:
            url = f"{API_URL}/getUpdates?timeout=30&offset={offset}"
            resp = requests.get(url, timeout=35)
            if resp.status_code != 200:
                time.sleep(5)
                continue

            data = resp.json()
            for update in data.get("result", []):
                offset = update["update_id"] + 1
                msg = update.get("message", {})
                text = (msg.get("text") or "").strip().lower()
                chat_id = str(msg.get("chat", {}).get("id", ""))

                # التحقق من الـ Chat ID لضمان الخصوصية
                if TELEGRAM_CHAT_ID and chat_id != str(TELEGRAM_CHAT_ID):
                    log.warning(f"محاولة وصول غير مصرح بها من chat_id: {chat_id}")
                    continue

                log.info(f"📩 تم استلام أمر: {text} من {chat_id}")

                if text in ("/search", "search", "/hunt"):
                    handle_search(chat_id)
                elif text in ("/latest", "latest"):
                    handle_latest(chat_id)
                elif text in ("/status", "status"):
                    handle_status(chat_id)
                elif text in ("/start", "/help", "help"):
                    handle_help(chat_id)
                else:
                    send_msg(chat_id, "❓ أمر غير معروف. اضغط على /search للبحث عن وظائف أو /help للمساعدة.")

        except Exception as e:
            log.error(f"خطأ في حلقة الاستقبال: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
