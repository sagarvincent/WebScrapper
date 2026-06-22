"""In-memory background job manager for the web UI.

Each submitted JobSpec runs in its own daemon thread. Progress events from
``main.run`` are appended to a per-job event log that the UI polls with a
``since`` cursor, so the browser only ever pulls events it hasn't seen.
"""

import threading
import time
import uuid

from main import run


class JobRecord:
    def __init__(self, job_id, spec):
        self.id = job_id
        self.spec = spec
        self.status = "pending"  # pending | running | done | cancelled | error
        self.events = []
        self.collected = 0
        self.target = spec.volume
        self.output_path = None
        self.error = None
        self.created_at = time.time()
        self.cancel_event = threading.Event()
        self.lock = threading.Lock()

    def snapshot(self, since=0):
        with self.lock:
            return {
                "job_id": self.id,
                "status": self.status,
                "collected": self.collected,
                "target": self.target,
                "error": self.error,
                "has_output": self.output_path is not None,
                "events": self.events[since:],
                "total_events": len(self.events),
            }


class JobManager:
    def __init__(self):
        self._jobs = {}
        self._lock = threading.Lock()

    def start(self, spec):
        job_id = uuid.uuid4().hex
        record = JobRecord(job_id, spec)
        with self._lock:
            self._jobs[job_id] = record
        thread = threading.Thread(target=self._run, args=(record,), daemon=True)
        thread.start()
        return job_id

    def get(self, job_id):
        with self._lock:
            return self._jobs.get(job_id)

    def cancel(self, job_id):
        record = self.get(job_id)
        if record is not None:
            record.cancel_event.set()
            return True
        return False

    def _run(self, record):
        record.status = "running"

        def on_event(event):
            with record.lock:
                record.events.append(event)
                if event["type"] == "kept":
                    record.collected = event["collected"]
                    record.target = event["target"]
                elif event["type"] == "done":
                    record.output_path = event["output_path"]
                elif event["type"] == "error":
                    record.error = event.get("message")

        try:
            run(
                record.spec,
                on_event=on_event,
                job_id=record.id,
                cancel_event=record.cancel_event,
            )
            if record.cancel_event.is_set():
                record.status = "cancelled"
            elif record.error:
                record.status = "error"
            else:
                record.status = "done"
        except Exception as exc:  # surface unexpected failures to the UI
            record.error = str(exc)
            record.status = "error"
            on_event({"type": "error", "message": str(exc)})
