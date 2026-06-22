"""Flask web UI for WebScrapper (stateless tier).

Serves the form and a small JSON API. Jobs are recorded in Postgres and run
by separate worker pods; this tier holds no job state in memory, so it can
be scaled to any number of replicas behind a load balancer.

    GET  /                       -> the UI
    GET  /healthz                -> liveness/readiness probe
    POST /api/jobs               -> record + enqueue a job, returns {job_id}
    GET  /api/jobs/<id>?since=N   -> status + new events since cursor N
    POST /api/jobs/<id>/cancel    -> request cancellation
    GET  /api/jobs/<id>/download  -> stream results formatted on demand

Run locally with:  python app.py
"""

import os

from flask import Flask, Response, abort, jsonify, render_template, request

from src import db
from src.job import JobSpec, OUTPUT_FORMATS, PURPOSES, URGENCIES
from src.output import OutputFormatter
from src.storage import Storage
from webapp import jobstore
from webapp.jobs import JobManager, get_queue

app = Flask(__name__)
manager = JobManager()

# Ensure tables exist on startup so a fresh deployment is self-initialising.
db.init_schema()


@app.route("/")
def index():
    return render_template(
        "index.html",
        purposes=PURPOSES,
        urgencies=URGENCIES,
        formats=OUTPUT_FORMATS,
    )


@app.get("/healthz")
def healthz():
    try:
        with db.connect() as conn:
            conn.execute("SELECT 1")
        get_queue().connection.ping()
    except Exception as exc:
        return jsonify(status="unhealthy", error=str(exc)), 503
    return jsonify(status="ok")


@app.post("/api/jobs")
def create_job():
    data = request.get_json(silent=True) or {}
    try:
        spec = JobSpec(
            topic=(data.get("topic") or "").strip(),
            purpose=data.get("purpose", "analysis"),
            urgency=data.get("urgency", "medium"),
            volume=int(data.get("volume", 50)),
            output_format=data.get("format", "jsonl"),
        )
    except (ValueError, TypeError) as exc:
        return jsonify(error=str(exc)), 400

    if not spec.topic:
        return jsonify(error="topic is required"), 400

    job_id = manager.start(spec)
    return jsonify(job_id=job_id), 201


@app.get("/api/jobs/<job_id>")
def job_status(job_id):
    try:
        since = int(request.args.get("since", 0))
    except ValueError:
        since = 0
    snapshot = manager.snapshot(job_id, since=since)
    if snapshot is None:
        abort(404)
    return jsonify(snapshot)


@app.post("/api/jobs/<job_id>/cancel")
def cancel_job(job_id):
    if not manager.cancel(job_id):
        abort(404)
    return jsonify(ok=True)


@app.get("/api/jobs/<job_id>/download")
def download(job_id):
    job = jobstore.get_job(job_id)
    if job is None:
        abort(404)

    storage = Storage()
    try:
        records = storage.get_records(job_id)
    finally:
        storage.close()

    spec = jobstore.spec_for(job)
    formatter = OutputFormatter(spec)
    body = formatter.format_records(records)
    filename = f"scrape_{job_id[:8]}.{spec.output_format}"
    return Response(
        body,
        mimetype=formatter.content_type(),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
