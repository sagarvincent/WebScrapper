"""WebScrapper entry point.

Wires the traditional scraping pipeline together:

    JobSpec -> URLSourcer -> Crawler -> Fetcher -> Parser -> Filter
            -> Storage -> OutputFormatter

The user describes what data they need and the constraints (purpose,
urgency, volume); the pipeline sources URLs, crawls them politely, parses
each page, keeps the relevant ones, and writes the result to disk.

``run`` emits structured progress events through an optional ``on_event``
callback so other front-ends (the web UI) can stream progress, and accepts
a ``cancel_event`` so a long run can be stopped early.
"""

import uuid

from src.crawler import Crawler
from src.fetcher import Fetcher
from src.filter import Filter
from src.job import parse_args
from src.output import OutputFormatter
from src.parser import Parser
from src.storage import Storage
from src.url_sourcer import URLSourcer


def run(job, output_path=None, on_event=None, job_id=None, cancel_event=None):
    """Execute a scrape job.

    Emits events of these types via ``on_event`` (each a dict with a
    ``type`` key): ``info``, ``start``, ``kept``, ``error``, ``done``.
    Returns the output file path, or None if nothing was produced.
    """
    job_id = job_id or uuid.uuid4().hex
    output_path = output_path or f"scrape_{job_id[:8]}.{job.output_format}"

    def emit(event_type, **data):
        if on_event is not None:
            on_event({"type": event_type, **data})

    def cancelled():
        return cancel_event is not None and cancel_event.is_set()

    fetcher = Fetcher()
    parser = Parser()
    relevance = Filter(job)
    storage = Storage()

    try:
        emit("info", message=f"Sourcing seed URLs for '{job.topic}'")
        seeds = URLSourcer(job).get_seeds()
        if not seeds:
            emit("error", message="No seed URLs found for topic; nothing to crawl.")
            return None

        emit("start", topic=job.topic, volume=job.volume, seeds=len(seeds))

        crawler = Crawler(
            seeds,
            fetcher,
            max_depth=job.max_depth,
            request_delay=job.request_delay,
            max_pages=job.volume * 5,  # crawl headroom; filter trims to volume
        )

        for url, html in crawler.crawl():
            if cancelled():
                emit("info", message="Job cancelled.")
                break
            storage.save_page(url, html)
            parsed = parser.parse(html)
            score = relevance.score(parsed)
            if score >= relevance.threshold:
                storage.save_record(job_id, url, parsed, score)
                collected = storage.record_count(job_id)
                emit("kept", url=url, score=round(score, 3),
                     collected=collected, target=job.volume)
                if collected >= job.volume:
                    break

        records = storage.get_records(job_id)
        OutputFormatter(job).write(records, output_path)
        emit("done", output_path=output_path, count=len(records))
        return output_path
    finally:
        storage.close()


def _print_event(event):
    etype = event.get("type")
    if etype == "start":
        print(f"Collecting up to {event['volume']} records on "
              f"'{event['topic']}' from {event['seeds']} seeds")
    elif etype == "kept":
        print(f"  [{event['collected']}/{event['target']}] kept "
              f"{event['url']} (score={event['score']:.2f})")
    elif etype == "done":
        print(f"Wrote {event['count']} records to {event['output_path']}")
    else:  # info, error
        print(event.get("message", ""))


def main():
    job, output_path = parse_args()
    run(job, output_path, on_event=_print_event)


if __name__ == "__main__":
    main()
