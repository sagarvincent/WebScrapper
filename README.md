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
| Storage | [src/storage.py](src/storage.py) | SQLite store of raw pages + scored records (resumable). |
| Output | [src/output.py](src/output.py) | Writes JSONL / CSV / JSON. |

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

### Web UI

A Flask front-end wraps the same pipeline: fill in a form, watch live
progress, and download the result.

```bash
python app.py        # then open http://localhost:5000
```

Jobs run in a background thread ([webapp/jobs.py](webapp/jobs.py)); the page
polls a small JSON API ([app.py](app.py)) for streamed progress events and a
download link. The CLI and UI share one code path — `run()` in
[main.py](main.py) emits structured events both front-ends consume.

## Tests

```bash
python -m unittest test.unit.parserTest test.unit.HTMLFetcherTest
```
