"""Worker-side job execution.

``run_job`` is the function RQ workers pull off the queue. It loads the job
row, rebuilds the JobSpec, and runs the existing pipeline (``main.run``),
persisting every progress event and honouring cancellation — all through
Postgres so the web tier sees progress live.
"""

import time

from webapp import jobstore


class DbCancelToken:
    """Adapts ``main.run``'s ``cancel_event`` interface to a DB flag.

    ``main.run`` only calls ``.is_set()``. We poll the ``cancel_requested``
    column but cache the result briefly so a tight crawl loop does not hammer
    the database.
    """

    def __init__(self, job_id: str, ttl: float = 2.0):
        self.job_id = job_id
        self.ttl = ttl
        self._cached = False
        self._checked_at = 0.0

    def is_set(self) -> bool:
        if self._cached:
            return True  # cancellation is sticky; no need to re-check
        now = time.monotonic()
        if now - self._checked_at >= self.ttl:
            self._cached = jobstore.is_cancelled(self.job_id)
            self._checked_at = now
        return self._cached


def run_job(job_id: str):
    # Imported here so the worker process loads the pipeline lazily.
    from main import run

    job = jobstore.get_job(job_id)
    if job is None:
        return
    spec = jobstore.spec_for(job)

    jobstore.set_status(job_id, "running")

    def on_event(event):
        jobstore.add_event(job_id, event)

    cancel_token = DbCancelToken(job_id)
    try:
        run(spec, on_event=on_event, job_id=job_id, cancel_event=cancel_token)
        if cancel_token.is_set():
            jobstore.set_status(job_id, "cancelled")
        elif jobstore.get_job(job_id)["error"]:
            jobstore.set_status(job_id, "error")
        else:
            jobstore.set_status(job_id, "done")
    except Exception as exc:  # surface unexpected failures to the UI
        jobstore.add_event(job_id, {"type": "error", "message": str(exc)})
        jobstore.set_status(job_id, "error")
        raise
