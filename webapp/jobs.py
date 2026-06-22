"""Job submission facade for the web tier.

In the decoupled design this no longer runs jobs in-process. ``start``
records the job in Postgres and enqueues it on Redis for a worker to pick
up; reads and cancellation delegate to the shared job store. All durable
state lives in Postgres (see ``webapp/jobstore.py``), so the web tier is
stateless and horizontally scalable.
"""

import os

from redis import Redis
from rq import Queue

from src.job import JobSpec
from webapp import jobstore

QUEUE_NAME = "scrapes"
JOB_TIMEOUT = int(os.environ.get("JOB_TIMEOUT", "3600"))  # seconds

_redis = None
_queue = None


def get_queue() -> Queue:
    """Lazily create the RQ queue, shared by the web tier and worker."""
    global _redis, _queue
    if _queue is None:
        url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        _redis = Redis.from_url(url)
        _queue = Queue(QUEUE_NAME, connection=_redis)
    return _queue


class JobManager:
    def start(self, spec: JobSpec) -> str:
        job_id = jobstore.create_job(spec)
        get_queue().enqueue("webapp.tasks.run_job", job_id, job_timeout=JOB_TIMEOUT)
        return job_id

    def get(self, job_id: str):
        return jobstore.get_job(job_id)

    def cancel(self, job_id: str) -> bool:
        return jobstore.request_cancel(job_id)

    def snapshot(self, job_id: str, since: int = 0):
        """Build the status payload the UI polls for.

        Returns None if the job does not exist. The JSON shape matches the
        previous in-memory design so the front-end is unchanged: ``events``
        plus a ``total_events`` cursor (here the highest event id seen).
        """
        job = jobstore.get_job(job_id)
        if job is None:
            return None
        events, last_id = jobstore.get_events(job_id, since=since)
        return {
            "job_id": job_id,
            "status": job["status"],
            "collected": job["collected"],
            "target": job["target"],
            "error": job["error"],
            "has_output": job["status"] in ("done", "cancelled") and job["collected"] > 0,
            "events": events,
            "total_events": last_id,
        }
