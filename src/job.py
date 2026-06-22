"""Job specification for a scrape run.

A JobSpec captures what the user wants the scraper to do: what data to
collect, why, how urgently, and how much. Every component in the pipeline
reads from this single source of truth.
"""

import argparse
from dataclasses import dataclass

PURPOSES = ("ml_training", "analysis", "research")
URGENCIES = ("high", "medium", "low")
OUTPUT_FORMATS = ("jsonl", "csv", "json")

# Crawl behaviour tuned per urgency: (request_delay_seconds, max_depth).
# High urgency trades politeness/coverage for speed; low urgency crawls
# deeper and more politely.
_URGENCY_PROFILE = {
    "high": (0.0, 1),
    "medium": (0.5, 2),
    "low": (1.0, 3),
}


@dataclass
class JobSpec:
    topic: str
    purpose: str = "analysis"
    urgency: str = "medium"
    volume: int = 50
    output_format: str = "jsonl"

    def __post_init__(self):
        if self.purpose not in PURPOSES:
            raise ValueError(f"purpose must be one of {PURPOSES}, got {self.purpose!r}")
        if self.urgency not in URGENCIES:
            raise ValueError(f"urgency must be one of {URGENCIES}, got {self.urgency!r}")
        if self.output_format not in OUTPUT_FORMATS:
            raise ValueError(
                f"output_format must be one of {OUTPUT_FORMATS}, got {self.output_format!r}"
            )
        if self.volume <= 0:
            raise ValueError(f"volume must be positive, got {self.volume}")

    @property
    def request_delay(self) -> float:
        """Seconds to wait between requests, derived from urgency."""
        return _URGENCY_PROFILE[self.urgency][0]

    @property
    def max_depth(self) -> int:
        """Maximum crawl depth from a seed URL, derived from urgency."""
        return _URGENCY_PROFILE[self.urgency][1]


def parse_args(argv=None) -> JobSpec:
    """Build a JobSpec from command-line arguments."""
    parser = argparse.ArgumentParser(description="Scrape data from the web for a topic.")
    parser.add_argument("--topic", required=True, help="What data to collect")
    parser.add_argument("--purpose", choices=PURPOSES, default="analysis")
    parser.add_argument("--urgency", choices=URGENCIES, default="medium")
    parser.add_argument("--volume", type=int, default=50, help="Max records to collect")
    parser.add_argument("--format", dest="output_format", choices=OUTPUT_FORMATS, default="jsonl")
    parser.add_argument("--output", default=None, help="Output file path")

    args = parser.parse_args(argv)
    job = JobSpec(
        topic=args.topic,
        purpose=args.purpose,
        urgency=args.urgency,
        volume=args.volume,
        output_format=args.output_format,
    )
    return job, args.output
