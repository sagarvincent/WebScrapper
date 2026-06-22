"""Postgres persistence for scraped data.

Stores raw HTML and the parsed/scored records so a run can be inspected or
re-exported without re-crawling. Backed by the shared Postgres database
(see ``src/db.py``) so every web and worker pod sees the same data.

The public methods keep the same names and signatures the pipeline used
under SQLite, so ``main.run`` is unchanged.
"""

from psycopg.types.json import Json

from src import db


class Storage:
    def __init__(self):
        self.conn = db.connect()

    def save_page(self, url: str, raw_html: str):
        self.conn.execute(
            "INSERT INTO pages (url, raw_html) VALUES (%s, %s) "
            "ON CONFLICT (url) DO UPDATE SET raw_html = EXCLUDED.raw_html, "
            "fetched_at = now()",
            (url, raw_html),
        )

    def save_record(self, job_id: str, url: str, data: dict, relevance_score: float):
        self.conn.execute(
            "INSERT INTO records (job_id, url, data_json, relevance_score) "
            "VALUES (%s, %s, %s, %s)",
            (job_id, url, Json(data), relevance_score),
        )

    def record_count(self, job_id: str) -> int:
        cur = self.conn.execute(
            "SELECT COUNT(*) FROM records WHERE job_id = %s", (job_id,)
        )
        return cur.fetchone()[0]

    def get_records(self, job_id: str):
        cur = self.conn.execute(
            "SELECT url, data_json, relevance_score FROM records "
            "WHERE job_id = %s ORDER BY relevance_score DESC",
            (job_id,),
        )
        return [
            {"url": url, "data": data_json, "relevance_score": score}
            for url, data_json, score in cur.fetchall()
        ]

    def close(self):
        self.conn.close()
