"""WebScrapper entry point.

Wires the traditional scraping pipeline together:

    JobSpec -> URLSourcer -> Crawler -> Fetcher -> Parser -> Filter
            -> Storage -> OutputFormatter

The user describes what data they need and the constraints (purpose,
urgency, volume); the pipeline sources URLs, crawls them politely, parses
each page, keeps the relevant ones, and writes the result to disk.
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


def run(job, output_path=None):
    job_id = uuid.uuid4().hex
    output_path = output_path or f"scrape_{job_id[:8]}.{job.output_format}"

    fetcher = Fetcher()
    parser = Parser()
    relevance = Filter(job)
    storage = Storage()

    seeds = URLSourcer(job).get_seeds()
    if not seeds:
        print("No seed URLs found for topic; nothing to crawl.")
        return None

    crawler = Crawler(
        seeds,
        fetcher,
        max_depth=job.max_depth,
        request_delay=job.request_delay,
        max_pages=job.volume * 5,  # crawl headroom; filter trims to volume
    )

    print(f"Job {job_id[:8]}: collecting up to {job.volume} records on '{job.topic}'")
    for url, html in crawler.crawl():
        storage.save_page(url, html)
        parsed = parser.parse(html)
        score = relevance.score(parsed)
        if score >= relevance.threshold:
            storage.save_record(job_id, url, parsed, score)
            collected = storage.record_count(job_id)
            print(f"  [{collected}/{job.volume}] kept {url} (score={score:.2f})")
            if collected >= job.volume:
                break

    records = storage.get_records(job_id)
    OutputFormatter(job).write(records, output_path)
    storage.close()

    print(f"Wrote {len(records)} records to {output_path}")
    return output_path


def main():
    job, output_path = parse_args()
    run(job, output_path)


if __name__ == "__main__":
    main()
