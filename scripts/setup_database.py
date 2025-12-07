#!/usr/bin/env python3
import os
import sqlite3
from backend.config import get_db_path


def ensure_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def main():
    db_path = get_db_path()
    ensure_dir(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT,
            category TEXT,
            source TEXT,
            description TEXT,
            discovered_at TIMESTAMP,
            raw_data TEXT,
            status TEXT DEFAULT 'new',
            llm_analysis TEXT,
            confidence_score REAL,
            verdict TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT,
            event_type TEXT,
            event_data TEXT,
            timestamp TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects (id)
        )
        """
    )
    conn.commit()
    conn.close()
    print(f"База инициализирована по пути {db_path}")


if __name__ == "__main__":
    main()
