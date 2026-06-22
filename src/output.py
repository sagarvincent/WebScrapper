"""Output formatting.

Writes collected records to disk in the format requested by the job:
JSON Lines (good for streaming into ML training pipelines), CSV (good for
spreadsheet/analysis tooling), or a single JSON array.
"""

import csv
import json


class OutputFormatter:
    def __init__(self, job_spec):
        self.job_spec = job_spec

    def write(self, records, output_path: str):
        fmt = self.job_spec.output_format
        if fmt == "jsonl":
            self._write_jsonl(records, output_path)
        elif fmt == "csv":
            self._write_csv(records, output_path)
        elif fmt == "json":
            self._write_json(records, output_path)
        else:
            raise ValueError(f"Unsupported output format: {fmt}")

    def _write_jsonl(self, records, path):
        with open(path, "w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _write_json(self, records, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(list(records), f, ensure_ascii=False, indent=2)

    def _write_csv(self, records, path):
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["url", "relevance_score", "text"])
            for record in records:
                writer.writerow([
                    record.get("url", ""),
                    record.get("relevance_score", ""),
                    self._flatten_text(record.get("data", {})),
                ])

    def _flatten_text(self, node) -> str:
        parts = []
        if isinstance(node, dict):
            if "text" in node:
                parts.append(node["text"])
            for child in node.get("children", []):
                parts.append(self._flatten_text(child))
        return " ".join(p for p in parts if p)
