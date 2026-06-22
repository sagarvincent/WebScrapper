"""Flask web UI for WebScrapper.

Serves a single-page form to submit a scrape job, then exposes a small JSON
API the page polls for live progress and results:

    GET  /                       -> the UI
    POST /api/jobs               -> start a job, returns {job_id}
    GET  /api/jobs/<id>?since=N  -> status + new events since cursor N
    POST /api/jobs/<id>/cancel   -> request cancellation
    GET  /api/jobs/<id>/download -> download the output file

Run with:  python app.py
"""

import os

from flask import Flask, abort, jsonify, render_template, request, send_file

from src.job import JobSpec, OUTPUT_FORMATS, PURPOSES, URGENCIES
from webapp.jobs import JobManager

app = Flask(__name__)
manager = JobManager()


@app.route("/")
def index():
    return render_template(
        "index.html",
        purposes=PURPOSES,
        urgencies=URGENCIES,
        formats=OUTPUT_FORMATS,
    )


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
    record = manager.get(job_id)
    if record is None:
        abort(404)
    try:
        since = int(request.args.get("since", 0))
    except ValueError:
        since = 0
    return jsonify(record.snapshot(since=since))


@app.post("/api/jobs/<job_id>/cancel")
def cancel_job(job_id):
    if not manager.cancel(job_id):
        abort(404)
    return jsonify(ok=True)


@app.get("/api/jobs/<job_id>/download")
def download(job_id):
    record = manager.get(job_id)
    if record is None or not record.output_path:
        abort(404)
    path = os.path.abspath(record.output_path)
    if not os.path.exists(path):
        abort(404)
    return send_file(path, as_attachment=True, download_name=os.path.basename(path))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
