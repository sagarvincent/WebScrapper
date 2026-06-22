"""SQLite persistence for scraped data.

Stores raw HTML and the parsed/scored records separately so a run can be
inspected, resumed, or re-exported without re-crawling. Uses the stdlib
sqlite3 module — no external database needed.
"""

import json
import sqlite3
import time


class Storage:
    def __init__(self, db_path: str = "scraper.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS pages (
                url        TEXT PRIMARY KEY,
                raw_html   TEXT,
                fetched_at REAL
            );
            CREATE TABLE IF NOT EXISTS records (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id          TEXT,
                url             TEXT,
                data_json       TEXT,
                relevance_score REAL
            );
            """
        )
        self.conn.commit()

    def save_page(self, url: str, raw_html: str):
        self.conn.execute(
            "INSERT OR REPLACE INTO pages (url, raw_html, fetched_at) VALUES (?, ?, ?)",
            (url, raw_html, time.time()),
        )
        self.conn.commit()

    def save_record(self, job_id: str, url: str, data: dict, relevance_score: float):
        self.conn.execute(
            "INSERT INTO records (job_id, url, data_json, relevance_score) VALUES (?, ?, ?, ?)",
            (job_id, url, json.dumps(data, ensure_ascii=False), relevance_score),
        )
        self.conn.commit()

    def record_count(self, job_id: str) -> int:
        cur = self.conn.execute(
            "SELECT COUNT(*) AS n FROM records WHERE job_id = ?", (job_id,)
        )
        return cur.fetchone()["n"]

    def get_records(self, job_id: str):
        cur = self.conn.execute(
            "SELECT url, data_json, relevance_score FROM records WHERE job_id = ? "
            "ORDER BY relevance_score DESC",
            (job_id,),
        )
        return [
            {
                "url": row["url"],
                "data": json.loads(row["data_json"]),
                "relevance_score": row["relevance_score"],
            }
            for row in cur.fetchall()
        ]

    def close(self):
        self.conn.close()
