"""Output formatting.

Renders collected records in the format requested by the job: JSON Lines
(good for streaming into ML training pipelines), CSV (good for
spreadsheet/analysis tooling), or a single JSON array.

``format_records`` returns the formatted text in memory so the web tier can
stream a download straight from the database without writing a file to disk.
``write`` persists that same text to a path for the CLI.
"""

import csv
import io
import json

# MIME type per output format, used when streaming downloads.
CONTENT_TYPES = {
    "jsonl": "application/x-ndjson",
    "json": "application/json",
    "csv": "text/csv",
}


class OutputFormatter:
    def __init__(self, job_spec):
        self.job_spec = job_spec

    def format_records(self, records) -> str:
        """Return the records rendered as a single string in the job's format."""
        fmt = self.job_spec.output_format
        if fmt == "jsonl":
            return "".join(
                json.dumps(record, ensure_ascii=False) + "\n" for record in records
            )
        if fmt == "json":
            return json.dumps(list(records), ensure_ascii=False, indent=2)
        if fmt == "csv":
            return self._to_csv(records)
        raise ValueError(f"Unsupported output format: {fmt}")

    def content_type(self) -> str:
        return CONTENT_TYPES.get(self.job_spec.output_format, "application/octet-stream")

    def write(self, records, output_path: str):
        text = self.format_records(records)
        # csv writer already emits platform newlines; avoid doubling them.
        newline = "" if self.job_spec.output_format == "csv" else None
        with open(output_path, "w", encoding="utf-8", newline=newline) as f:
            f.write(text)

    def _to_csv(self, records) -> str:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["url", "relevance_score", "text"])
        for record in records:
            writer.writerow([
                record.get("url", ""),
                record.get("relevance_score", ""),
                self._flatten_text(record.get("data", {})),
            ])
        return buffer.getvalue()

    def _flatten_text(self, node) -> str:
        parts = []
        if isinstance(node, dict):
            if "text" in node:
                parts.append(node["text"])
            for child in node.get("children", []):
                parts.append(self._flatten_text(child))
        return " ".join(p for p in parts if p)
