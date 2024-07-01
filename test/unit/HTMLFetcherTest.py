## -- script to test the working of fetcher.
# should take in a url and return the html resource.
# cases:
# 1.URL validity --> proper form
# 2.empty URL --> inform and skip to next
# 3.resource not found --> inform and skip to next
# 4.proper URL --> fetch and return proper html code.


import unittest
from unittest.mock import patch
from src.fetcher import Fetcher

class TestHTMLFetcher(unittest.TestCase):
    @patch('requests.get')
    def test_valid_url():
        pass

    @patch('requests.get')    
    def test_empty_url():
        pass 

    @patch('requests.get')
    def test_not_found():
        pass

    @patch('requests.get')
    def test_fetching():
        pass 

if __name__ == '__main__':
    unittest.main()





