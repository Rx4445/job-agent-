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

if __name__ == "__main__":
       init_db()
       save_job("Test Engineer", "Test Co", ["Python", "SQL"])
       print("Saved one test job")