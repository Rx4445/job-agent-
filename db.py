import hashlib
import json
import sqlite3

DB_FILE = "jobs.db"


def init_db(db_path: str = DB_FILE):
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            skills TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS candidate_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_hash TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            experience_years INTEGER NOT NULL,
            field TEXT NOT NULL,
            skills TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def save_job(title, company, skills, db_path: str = DB_FILE):
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO jobs (title, company, skills) VALUES (?, ?, ?)",
        (title, company, json.dumps(skills)),
    )
    conn.commit()
    conn.close()


def get_jobs(db_path: str = DB_FILE):
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT id, title, company, skills FROM jobs").fetchall()
    conn.close()
    jobs = []
    for row in rows:
        jobs.append(
            {
                "id": row[0],
                "title": row[1],
                "company": row[2],
                "skills": json.loads(row[3]),
            }
        )
    return jobs


def compute_resume_hash(resume_text: str) -> str:
    """Computes a deterministic SHA-256 fingerprint for resume text."""
    return hashlib.sha256(resume_text.strip().encode("utf-8")).hexdigest()


def save_candidate_profile(
    resume_hash: str,
    name: str,
    experience_years: int,
    field: str,
    skills: list[str],
    db_path: str = DB_FILE,
) -> None:
    """Caches an extracted candidate profile in SQLite using its SHA-256 hash."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        INSERT OR REPLACE INTO candidate_profile (resume_hash, name, experience_years, field, skills, updated_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (resume_hash, name, experience_years, field, json.dumps(skills)),
    )
    conn.commit()
    conn.close()


def get_candidate_profile(resume_hash: str, db_path: str = DB_FILE) -> dict | None:
    """Fetches a cached candidate profile by resume hash, or None if not found."""
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT name, experience_years, field, skills FROM candidate_profile WHERE resume_hash = ?",
        (resume_hash,),
    ).fetchone()
    conn.close()
    if row is None:
        return None
    return {
        "name": row[0],
        "experience_years": row[1],
        "field": row[2],
        "skills": json.loads(row[3]),
    }


if __name__ == "__main__":
    init_db()
    for i in get_jobs():
        print(i)
