"""Seed URL discovery.

Given a JobSpec, the URLSourcer turns the topic into search queries and
returns a prioritised list of seed URLs for the crawler to start from. It
uses DuckDuckGo search (the ``ddgs`` package), which requires no API key.
"""


class URLSourcer:
    def __init__(self, job_spec, max_results: int = 20):
        self.job_spec = job_spec
        self.max_results = max_results

    def get_seeds(self):
        """Return a list of seed URLs for the job's topic.

        Falls back to an empty list if the search backend is unavailable, so
        callers can degrade gracefully (e.g. prompt for manual seeds).
        """
        try:
            from ddgs import DDGS
        except ImportError:
            try:
                from duckduckgo_search import DDGS  # legacy package name
            except ImportError:
                return []

        urls = []
        seen = set()
        try:
            with DDGS() as ddgs:
                for result in ddgs.text(self.job_spec.topic, max_results=self.max_results):
                    url = result.get("href")
                    if url and url not in seen:
                        seen.add(url)
                        urls.append(url)
        except Exception:
            return urls

        return urls
