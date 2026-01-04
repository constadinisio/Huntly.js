# storage.py
import sqlite3
from datetime import datetime

DB_PATH = "jobs.db"

def _c():
    return sqlite3.connect(DB_PATH)

def init_db():
    """
    Crea la tabla si no existe y agrega columnas nuevas si faltan.
    (Migración simple por ALTER TABLE)
    """
    with _c() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS jobs(
            job_id TEXT PRIMARY KEY,
            url TEXT,
            title TEXT,
            description TEXT,
            budget TEXT,
            date TEXT,
            proposal TEXT,
            status TEXT,
            created_at TEXT
        )
        """)
        c.commit()

        # Si venís de una DB vieja, intentamos agregar columnas que falten
        existing_cols = set()
        for row in c.execute("PRAGMA table_info(jobs)"):
            existing_cols.add(row[1])

        def add_col(name: str, coldef: str):
            if name not in existing_cols:
                c.execute(f"ALTER TABLE jobs ADD COLUMN {name} {coldef}")
                c.commit()

        add_col("description", "TEXT")
        add_col("budget", "TEXT")
        add_col("date", "TEXT")
        add_col("proposal", "TEXT")
        add_col("status", "TEXT")
        add_col("created_at", "TEXT")

def upsert_job(
    job_id: str,
    url: str,
    title: str,
    description: str = "",
    budget: str = "",
    date: str = "",
    proposal: str = "",
    status: str = "pending_interest",
):
    init_db()
    with _c() as c:
        c.execute("""
        INSERT OR REPLACE INTO jobs
        (job_id, url, title, description, budget, date, proposal, status, created_at)
        VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            job_id,
            url,
            title,
            description,
            budget,
            date,
            proposal,
            status,
            datetime.utcnow().isoformat()
        ))
        c.commit()

def get_job(job_id: str):
    init_db()
    with _c() as c:
        row = c.execute("""
            SELECT job_id, url, title, description, budget, date, proposal, status
            FROM jobs
            WHERE job_id=?
        """, (job_id,)).fetchone()

        if not row:
            return None

        return {
            "job_id": row[0],
            "url": row[1],
            "title": row[2],
            "description": row[3] or "",
            "budget": row[4] or "",
            "date": row[5] or "",
            "proposal": row[6] or "",
            "status": row[7] or "",
        }

def set_status(job_id: str, status: str):
    init_db()
    with _c() as c:
        c.execute(
            "UPDATE jobs SET status=? WHERE job_id=?",
            (status, job_id)
        )
        c.commit()

def set_proposal(job_id: str, proposal: str, status: str = "pending_send"):
    init_db()
    with _c() as c:
        c.execute(
            "UPDATE jobs SET proposal=?, status=? WHERE job_id=?",
            (proposal, status, job_id)
        )
        c.commit()