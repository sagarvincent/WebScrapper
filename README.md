# WebScrapper

A configurable web scraper that collects data from across the internet for
ML training and analysis. You describe **what** you need, **why**, **how
soon**, and **how much** — the scraper sources URLs, crawls them politely,
parses each page, keeps the relevant ones, and writes the result to disk.

## Design

This uses a **traditional pipeline** architecture — deterministic,
debuggable stages, each with a single responsibility:

```
JobSpec ─▶ URLSourcer ─▶ Crawler ─▶ Fetcher ─▶ Parser ─▶ Filter ─▶ Storage ─▶ Output
```

| Stage | Module | Responsibility |
|-------|--------|----------------|
| JobSpec | [src/job.py](src/job.py) | Captures the request: topic, purpose, urgency, volume, format. Urgency drives crawl delay/depth. |
| URLSourcer | [src/url_sourcer.py](src/url_sourcer.py) | Turns the topic into seed URLs via web search. |
| Crawler | [src/crawler.py](src/crawler.py) | Breadth-first link walk with dedup + robots.txt. |
| Fetcher | [src/fetcher.py](src/fetcher.py) | HTTP with retries/backoff + UA rotation; optional Selenium for JS pages. |
| Parser | [src/parser.py](src/parser.py) | HTML → canonical recursive node tree (`tag`/`attrs`/`text`/`children`). |
| Filter | [src/filter.py](src/filter.py) | Keyword-overlap relevance scoring; threshold varies by purpose. |
| Storage | [src/storage.py](src/storage.py) | Postgres store of raw pages + scored records (shared across pods). |
| Output | [src/output.py](src/output.py) | Renders JSONL / CSV / JSON (to disk for the CLI, or streamed on demand for downloads). |

### Why a pipeline (not an AI-agent orchestrator)?

For high-volume, repeatable data collection a deterministic pipeline is
cheaper, faster, and easier to debug than an LLM-driven agent. Each stage is
independently testable and swappable. An agent layer could later sit *on
top* — choosing seeds, tuning the filter, or interpreting a natural-language
request into a `JobSpec` — without changing the core pipeline.

## Usage

```bash
pip install -r requirements.txt

python main.py --topic "renewable energy statistics" \
               --purpose ml_training \
               --urgency medium \
               --volume 100 \
               --format jsonl \
               --output data.jsonl
```

- `--purpose`: `ml_training` | `analysis` | `research` (controls filter strictness)
- `--urgency`: `high` | `medium` | `low` (controls crawl delay and depth)
- `--volume`: target number of records
- `--format`: `jsonl` | `csv` | `json`

> **Note:** persistence is now Postgres, so the CLI needs a database. Point
> `PG_DSN` at one (e.g. `docker compose up postgres`), or just use the web UI
> via Docker Compose below, which wires everything up for you.

### Web UI

A Flask front-end wraps the same pipeline: fill in a form, watch live
progress, and download the result. The CLI and UI share one code path —
`run()` in [main.py](main.py) emits structured events both front-ends consume.

## Deployment — decoupled & horizontally scalable

The web UI is split into a **stateless web tier** and a **scalable worker
tier**, with all state in shared services so any pod can serve any job:

```
 web pods (Flask, N replicas)        ── stateless: create / poll / cancel / download
   │ enqueue job_id                     ▲ read status + events
   ▼                                    │
 Redis (RQ queue)              Postgres (jobs, events, records, pages)
   │ dequeue                            ▲ write progress + results
   ▼                                    │
 worker pods (RQ, M replicas) ── run the pipeline (main.run) ─┘
```

Why: the original design kept job state in one process's memory and SQLite on
local disk, so it couldn't run more than one replica. Moving state to Postgres
(durable, shared) and work to a Redis/RQ queue makes the web tier stateless
and lets crawl throughput scale independently by adding workers. Downloads are
formatted **on demand from the database**, so there is no shared file store to
manage. Components: [webapp/jobs.py](webapp/jobs.py) (enqueue),
[webapp/tasks.py](webapp/tasks.py) (worker task), [webapp/jobstore.py](webapp/jobstore.py)
(state), [src/db.py](src/db.py) (Postgres), [worker.py](worker.py) (RQ worker).

### Local (Docker Compose)

```bash
docker compose up --build           # web at http://localhost:8000
docker compose up --scale worker=3  # scale the worker tier
```

### Kubernetes

Manifests live in [k8s/](k8s/) (web Deployment + Service + Ingress + HPA,
worker Deployment, Postgres StatefulSet, Redis, ConfigMap/Secret). Per-cluster
spots — image registry, `ingressClassName`, `storageClassName`, and the demo
Secret — are flagged inline.

```bash
docker build -t webscrapper:0.2 .
# local cluster: kind load docker-image webscrapper:0.2   (or: minikube image load)
kubectl apply -f k8s/
kubectl get pods
kubectl scale deploy/worker --replicas=5     # scale crawl throughput
```

Worker autoscaling on queue depth needs [KEDA](https://keda.sh)'s Redis scaler
(a follow-up); the included HPA scales the web tier on CPU.

## Tests

```bash
python -m unittest test.unit.parserTest test.unit.HTMLFetcherTest
```
