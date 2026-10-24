import sqlite3
from pathlib import Path
from datetime import datetime
DB_PATH = Path(__file__).resolve().parent.parent / "jobapply.sqlite3"

def connect():
    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, company TEXT, url TEXT UNIQUE,
        source TEXT, status TEXT DEFAULT 'Review', saved_at TEXT)""")
    con.commit()
    return con

def init_db():
    con = connect()
    con.close()

def save_search_results(jobs, status="Found"):
    con = connect()
    for j in jobs:
        url = (j.get("url") or "").strip()
        if not url:
            continue
        con.execute("INSERT OR IGNORE INTO jobs(title,company,url,source,status,saved_at) VALUES(?,?,?,?,?,?)",
                    (j.get("title",""), j.get("company",""), url, j.get("source",""), status,
                     datetime.now().strftime("%Y-%m-%d %H:%M")))
    con.commit()
    con.close()

def list_saved_jobs():
    con = connect()
    rows = con.execute("SELECT id,title,company,url,source,status,saved_at FROM jobs ORDER BY id DESC").fetchall()
    con.close()
    return rows

def update_status(job_id, status):
    con = connect()
    con.execute("UPDATE jobs SET status=? WHERE id=?", (status, job_id))
    con.commit()
    con.close()
