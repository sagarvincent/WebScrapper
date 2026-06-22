"""Job and progress-event persistence.

Replaces the in-memory job registry from the single-process design. Job
metadata, live progress events, and cancellation flags all live in Postgres
so any web pod can read the status of a job any worker pod is running.

Events use an auto-incrementing ``id`` as the polling cursor: the UI passes
the highest id it has seen as ``since`` and gets only newer events back.
"""

import uuid

from psycopg.types.json import Json

from src import db
from src.job import JobSpec


def create_job(spec: JobSpec) -> str:
    job_id = uuid.uuid4().hex
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO jobs (id, topic, purpose, urgency, volume, output_format, "
            "status, target) VALUES (%s, %s, %s, %s, %s, %s, 'queued', %s)",
            (job_id, spec.topic, spec.purpose, spec.urgency, spec.volume,
             spec.output_format, spec.volume),
        )
    return job_id


def get_job(job_id: str):
    """Return the job row as a dict, or None if it does not exist."""
    with db.connect() as conn:
        cur = conn.execute(
            "SELECT id, topic, purpose, urgency, volume, output_format, status, "
            "collected, target, cancel_requested, error FROM jobs WHERE id = %s",
            (job_id,),
        )
        row = cur.fetchone()
    if row is None:
        return None
    keys = ("id", "topic", "purpose", "urgency", "volume", "output_format",
            "status", "collected", "target", "cancel_requested", "error")
    return dict(zip(keys, row))


def spec_for(job: dict) -> JobSpec:
    """Rebuild a JobSpec from a job row (used by the worker)."""
    return JobSpec(
        topic=job["topic"],
        purpose=job["purpose"],
        urgency=job["urgency"],
        volume=job["volume"],
        output_format=job["output_format"],
    )


def add_event(job_id: str, event: dict):
    """Persist a progress event and reflect 'kept'/'done' onto the job row."""
    event_type = event.get("type", "info")
    payload = {k: v for k, v in event.items() if k != "type"}
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO events (job_id, type, payload) VALUES (%s, %s, %s)",
            (job_id, event_type, Json(payload)),
        )
        if event_type == "kept":
            conn.execute(
                "UPDATE jobs SET collected = %s, target = %s WHERE id = %s",
                (event["collected"], event["target"], job_id),
            )
        elif event_type == "error":
            conn.execute(
                "UPDATE jobs SET error = %s WHERE id = %s",
                (event.get("message"), job_id),
            )


def get_events(job_id: str, since: int = 0):
    """Return events with id greater than ``since`` plus the new high-water id."""
    with db.connect() as conn:
        cur = conn.execute(
            "SELECT id, type, payload FROM events WHERE job_id = %s AND id > %s "
            "ORDER BY id",
            (job_id, since),
        )
        rows = cur.fetchall()
    events = [{"type": etype, **payload} for _id, etype, payload in rows]
    last_id = rows[-1][0] if rows else since
    return events, last_id


def set_status(job_id: str, status: str):
    with db.connect() as conn:
        conn.execute("UPDATE jobs SET status = %s WHERE id = %s", (status, job_id))


def request_cancel(job_id: str) -> bool:
    with db.connect() as conn:
        cur = conn.execute(
            "UPDATE jobs SET cancel_requested = TRUE WHERE id = %s", (job_id,)
        )
        return cur.rowcount > 0


def is_cancelled(job_id: str) -> bool:
    with db.connect() as conn:
        cur = conn.execute(
            "SELECT cancel_requested FROM jobs WHERE id = %s", (job_id,)
        )
        row = cur.fetchone()
    return bool(row and row[0])
