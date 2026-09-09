"""
db_manager.py - إدارة قاعدة البيانات عشان نتحقق إن الشغلانة جديدة
"""
import sqlite3
import os
from src.config import DB_PATH


def init_db():
    """إنشاء قاعدة البيانات لو مش موجودة"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS jobs_seen (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id      TEXT UNIQUE,
            title       TEXT,
            company     TEXT,
            location    TEXT,
            url         TEXT,
            source      TEXT,
            applied_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def is_new_job(job_id: str) -> bool:
    """بيرجع True لو الشغلانة دي لسه ماتبعتناش عليها"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT 1 FROM jobs_seen WHERE job_id = ?", (job_id,))
    result = c.fetchone()
    conn.close()
    return result is None


def mark_job_as_applied(job: dict):
    """بيحفظ الشغلانة في قاعدة البيانات بعد ما نبعت عليها"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT OR IGNORE INTO jobs_seen (job_id, title, company, location, url, source)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        job.get("id"),
        job.get("title"),
        job.get("company"),
        job.get("location"),
        job.get("url"),
        job.get("source"),
    ))
    conn.commit()
    conn.close()


def get_all_applied_jobs() -> list:
    """بيجيب كل الشغلانات اللي اتبعنا عليها"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT title, company, location, url, source, applied_at FROM jobs_seen ORDER BY applied_at DESC")
    rows = c.fetchall()
    conn.close()
    return [
        {"title": r[0], "company": r[1], "location": r[2],
         "url": r[3], "source": r[4], "applied_at": r[5]}
        for r in rows
    ]
