"""Breadth-first web crawler.

Starting from one or more seed URLs, the crawler walks links breadth-first
up to a maximum depth, deduplicates visited URLs, and respects each site's
robots.txt. It yields fetched HTML pages to the pipeline; it does not parse
or store them itself.
"""

import time
from collections import deque
from urllib.parse import urljoin, urldefrag, urlparse
from urllib.robotparser import RobotFileParser

from bs4 import BeautifulSoup


class Crawler:
    def __init__(self, seed_urls, fetcher, max_depth: int = 2,
                 request_delay: float = 0.5, max_pages: int = 1000):
        if isinstance(seed_urls, str):
            seed_urls = [seed_urls]
        self.seed_urls = list(seed_urls)
        self.fetcher = fetcher
        self.max_depth = max_depth
        self.request_delay = request_delay
        self.max_pages = max_pages

        self.visited = set()
        self._robots_cache = {}

    def crawl(self):
        """Yield (url, html) for each successfully fetched page.

        The pipeline consumes this generator and may stop early once it has
        collected enough records.
        """
        queue = deque((url, 0) for url in self.seed_urls)
        pages_fetched = 0

        while queue and pages_fetched < self.max_pages:
            url, depth = queue.popleft()
            url, _ = urldefrag(url)

            if url in self.visited:
                continue
            self.visited.add(url)

            if not self._allowed(url):
                continue

            html = self.fetcher.fetch(url)
            if self.request_delay:
                time.sleep(self.request_delay)
            if html is None:
                continue

            pages_fetched += 1
            yield url, html

            if depth < self.max_depth:
                for link in self._extract_links(url, html):
                    if link not in self.visited:
                        queue.append((link, depth + 1))

    def _allowed(self, url: str) -> bool:
        """Check robots.txt for the URL's host, caching per host."""
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False

        host = f"{parsed.scheme}://{parsed.netloc}"
        rp = self._robots_cache.get(host)
        if host not in self._robots_cache:
            rp = RobotFileParser()
            rp.set_url(urljoin(host, "/robots.txt"))
            try:
                rp.read()
            except Exception:
                # If robots.txt is unreachable, default to allowing.
                rp = None
            self._robots_cache[host] = rp

        if rp is None:
            return True
        return rp.can_fetch("*", url)

    @staticmethod
    def _extract_links(base_url: str, html: str):
        """Return absolute http(s) links found in the page."""
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for anchor in soup.find_all("a", href=True):
            absolute = urljoin(base_url, anchor["href"])
            absolute, _ = urldefrag(absolute)
            if urlparse(absolute).scheme in ("http", "https"):
                links.append(absolute)
        return links
