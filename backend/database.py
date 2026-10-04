import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blood_matcher.db")


@contextmanager
def get_db():
    """Open a connection, commit on success, always close."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS donors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                blood_group TEXT NOT NULL,
                city TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT NOT NULL,
                token TEXT NOT NULL,
                is_available INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS contact_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                donor_id INTEGER NOT NULL,
                seeker_name TEXT NOT NULL,
                seeker_phone TEXT NOT NULL,
                seeker_blood_group TEXT NOT NULL,
                city TEXT NOT NULL,
                units_needed INTEGER NOT NULL,
                urgency TEXT CHECK(urgency IN ('LOW','MEDIUM','HIGH','CRITICAL')) DEFAULT 'HIGH',
                status TEXT CHECK(status IN ('PENDING','ACCEPTED','REJECTED')) DEFAULT 'PENDING',
                seeker_token TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (donor_id) REFERENCES donors(id)
            )
        """)


init_db()
