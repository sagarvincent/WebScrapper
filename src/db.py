"""Shared Postgres access for the decoupled deployment.

Both the web tier and the worker tier talk to the same Postgres database;
this module centralises the connection string and the schema so neither tier
hardcodes either. The DSN is read from the ``PG_DSN`` environment variable
(falling back to a local default for development).
"""

import os

import psycopg

DEFAULT_DSN = "postgresql://scraper:scraper@localhost:5432/scraper"


def dsn() -> str:
    return os.environ.get("PG_DSN", DEFAULT_DSN)


def connect():
    """Open a new autocommit connection.

    Connections are cheap to open per unit of work here and avoid sharing a
    single connection across threads/requests, so each caller opens and
    closes its own (typically via ``with connect() as conn``).
    """
    return psycopg.connect(dsn(), autocommit=True)


SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id              TEXT PRIMARY KEY,
    topic           TEXT NOT NULL,
    purpose         TEXT NOT NULL,
    urgency         TEXT NOT NULL,
    volume          INTEGER NOT NULL,
    output_format   TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'queued',
    collected       INTEGER NOT NULL DEFAULT 0,
    target          INTEGER NOT NULL DEFAULT 0,
    cancel_requested BOOLEAN NOT NULL DEFAULT FALSE,
    error           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS events (
    id          BIGSERIAL PRIMARY KEY,
    job_id      TEXT NOT NULL REFERENCES jobs(id),
    type        TEXT NOT NULL,
    payload     JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS events_job_id_idx ON events (job_id, id);

CREATE TABLE IF NOT EXISTS records (
    id              BIGSERIAL PRIMARY KEY,
    job_id          TEXT NOT NULL,
    url             TEXT NOT NULL,
    data_json       JSONB NOT NULL,
    relevance_score DOUBLE PRECISION NOT NULL
);
CREATE INDEX IF NOT EXISTS records_job_id_idx ON records (job_id);

CREATE TABLE IF NOT EXISTS pages (
    url         TEXT PRIMARY KEY,
    raw_html    TEXT,
    fetched_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


def init_schema():
    """Create all tables if they do not exist. Safe to call repeatedly."""
    with connect() as conn:
        conn.execute(SCHEMA)
