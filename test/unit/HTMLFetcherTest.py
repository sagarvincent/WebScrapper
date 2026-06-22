"""Tests for the HTTP fetcher.

Covers the behaviours the pipeline relies on:
  1. a 200 response returns the body
  2. a 4xx response returns None without retrying
  3. a 5xx response is retried, then gives up
  4. a network exception is retried, then gives up
"""

import unittest
from unittest.mock import MagicMock, patch

from src.fetcher import Fetcher


def make_response(status_code, text=""):
    response = MagicMock()
    response.status_code = status_code
    response.text = text
    return response


class TestHTMLFetcher(unittest.TestCase):
    def setUp(self):
        # No real delays during tests.
        self.fetcher = Fetcher(max_retries=3)
        self.fetcher._backoff = lambda attempt: None

    def test_valid_url_returns_html(self):
        with patch.object(self.fetcher.session, "get",
                          return_value=make_response(200, "<html>ok</html>")) as get:
            result = self.fetcher.fetch("http://example.com")
        self.assertEqual(result, "<html>ok</html>")
        self.assertEqual(get.call_count, 1)

    def test_client_error_returns_none_without_retry(self):
        with patch.object(self.fetcher.session, "get",
                          return_value=make_response(404)) as get:
            result = self.fetcher.fetch("http://example.com/missing")
        self.assertIsNone(result)
        self.assertEqual(get.call_count, 1)

    def test_server_error_retries_then_gives_up(self):
        with patch.object(self.fetcher.session, "get",
                          return_value=make_response(503)) as get:
            result = self.fetcher.fetch("http://example.com")
        self.assertIsNone(result)
        self.assertEqual(get.call_count, 3)

    def test_network_exception_retries_then_gives_up(self):
        import requests
        with patch.object(self.fetcher.session, "get",
                          side_effect=requests.ConnectionError()) as get:
            result = self.fetcher.fetch("http://example.com")
        self.assertIsNone(result)
        self.assertEqual(get.call_count, 3)


if __name__ == "__main__":
    unittest.main()
