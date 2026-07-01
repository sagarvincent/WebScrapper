"""HTTP fetching for the scraper.

Fetcher handles the mechanical job of turning a URL into HTML. It retries
transient failures with backoff and rotates a small pool of user agents to
reduce the chance of being blocked. A Selenium path is available for
JavaScript-heavy pages that do not render their content server-side.
"""

import time

import requests

DEFAULT_USER_AGENTS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
)


class Fetcher:
    def __init__(self, timeout: float = 10.0, max_retries: int = 3,
                 user_agents=DEFAULT_USER_AGENTS):
        self.timeout = timeout
        self.max_retries = max_retries
        self.user_agents = list(user_agents)
        self._ua_index = 0
        self.session = requests.Session()

    def _next_user_agent(self) -> str:
        ua = self.user_agents[self._ua_index % len(self.user_agents)]
        self._ua_index += 1
        return ua

    def fetch(self, url: str):
        """Fetch HTML over HTTP, returning the body or None on failure.

        Retries transient errors (timeouts, connection errors, 5xx) with
        exponential backoff. Returns None for client errors (4xx) and after
        exhausting retries.
        """
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(
                    url,
                    timeout=self.timeout,
                    headers={"User-Agent": self._next_user_agent()},
                )
            except requests.RequestException:
                self._backoff(attempt)
                continue

            if response.status_code == 200:
                return response.text
            if 400 <= response.status_code < 500:
                # Client error — retrying will not help.
                return None
            # 5xx or other: retry.
            self._backoff(attempt)

        return None

    def fetch_js(self, url: str):
        """Fetch a JavaScript-rendered page using a headless browser.

        Selenium is imported lazily so the common HTTP path has no hard
        dependency on a browser driver being installed.
        """
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
        except ImportError:
            return None

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument(f"user-agent={self._next_user_agent()}")
        driver = None
        try:
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(self.timeout)
            driver.get(url)
            return driver.page_source
        except Exception:
            return None
        finally:
            if driver is not None:
                driver.quit()

    def _backoff(self, attempt: int):
        time.sleep(2 ** attempt * 0.5)
