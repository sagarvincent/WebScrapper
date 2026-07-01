"""Relevance filtering.

Scores parsed pages against the job topic by keyword overlap and keeps only
those above a threshold. The threshold is stricter for ML training data
(where noise hurts model quality) and looser for exploratory analysis.
"""

import re

_WORD = re.compile(r"[a-z0-9]+")

# Minimum fraction of topic keywords that must appear in a page.
_THRESHOLD = {
    "ml_training": 0.6,
    "analysis": 0.3,
    "research": 0.4,
}


class Filter:
    def __init__(self, job_spec):
        self.job_spec = job_spec
        self.keywords = set(_WORD.findall(job_spec.topic.lower()))
        self.threshold = _THRESHOLD.get(job_spec.purpose, 0.3)

    def score(self, record: dict) -> float:
        """Fraction of topic keywords present in the record's text."""
        if not self.keywords:
            return 1.0
        text = self._collect_text(record).lower()
        words = set(_WORD.findall(text))
        if not words:
            return 0.0
        hits = sum(1 for kw in self.keywords if kw in words)
        return hits / len(self.keywords)

    def is_relevant(self, record: dict) -> bool:
        return self.score(record) >= self.threshold

    def _collect_text(self, node) -> str:
        """Recursively gather all text from a parsed node tree."""
        parts = []
        if isinstance(node, dict):
            if "text" in node:
                parts.append(node["text"])
            for child in node.get("children", []):
                parts.append(self._collect_text(child))
        return " ".join(parts)
