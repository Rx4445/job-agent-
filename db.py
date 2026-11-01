import sqlite3
import json

DB_FILE = "jobs.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)
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
    conn.commit()
    conn.close()
def save_job(title, company, skills):
       conn = sqlite3.connect(DB_FILE)
       conn.execute(
           "INSERT INTO jobs (title, company, skills) VALUES (?, ?, ?)",
           (title, company, json.dumps(skills)),
       )
       conn.commit()
       conn.close()
def get_jobs():
    conn = sqlite3.connect(DB_FILE)
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

if __name__ == "__main__":
       init_db()
       for i in get_jobs():
           print(i)