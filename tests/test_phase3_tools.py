"""
tests/test_phase3_tools.py — Unit and integration tests for Phase 3 data tools.
Tests caching, ticker search, price series, news sentiment, and fundamentals.
"""
import os
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
import django
django.setup()

import pandas as pd
from tools.cache import set_cache, get_cache, is_fresh
from tools.search_ticker import search_ticker
from tools.price_fetch import get_price_data
from tools.news_fetch import get_news
from tools.fundamentals import get_fundamentals


class TestCacheHelper(unittest.TestCase):
    """Test disk cache behavior and TTL expiration."""

    def test_cache_roundtrip(self):
        key = "_test_sample_key"
        payload = {"symbol": "TEST", "value": 123.45}
        self.assertTrue(set_cache(key, payload))
        self.assertTrue(is_fresh(key, ttl_seconds=60))
        cached = get_cache(key, ttl_seconds=60)
        self.assertEqual(cached, payload)

    def test_cache_expiration(self):
        key = "_test_expired_key"
        set_cache(key, {"expired": True})
        self.assertFalse(is_fresh(key, ttl_seconds=0))
        self.assertIsNone(get_cache(key, ttl_seconds=0))


class TestSearchTicker(unittest.TestCase):
    """Test ticker symbol lookup."""

    def test_direct_ticker_fastpath(self):
        self.assertEqual(search_ticker("AAPL"), "AAPL")
        self.assertEqual(search_ticker("MSFT"), "MSFT")

    def test_company_name_search(self):
        ticker = search_ticker("Apple Inc")
        self.assertIsInstance(ticker, str)
        self.assertTrue(len(ticker) > 0)


class TestPriceFetch(unittest.TestCase):
    """Test OHLCV price fetching and DataFrame structure."""

    def test_get_price_data_returns_dataframe(self):
        df = get_price_data("AAPL")
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

        for col in ["open", "high", "low", "close", "volume"]:
            self.assertIn(col, df.columns)

        self.assertGreater(len(df), 20)
        self.assertTrue(df.index.is_monotonic_increasing)


class TestNewsFetch(unittest.TestCase):
    """Test news and sentiment parsing."""

    def test_get_news_structure(self):
        news = get_news("AAPL")
        self.assertIsInstance(news, list)
        self.assertGreater(len(news), 0)

        for item in news:
            self.assertIn("title", item)
            self.assertIn("sentiment", item)
            self.assertIn("score", item)
            self.assertIn(item["sentiment"], ["Very Positive", "Positive", "Neutral", "Negative", "Very Negative"])


class TestFundamentals(unittest.TestCase):
    """Test fundamental metrics extraction."""

    def test_get_fundamentals_structure(self):
        fund = get_fundamentals("AAPL")
        self.assertIsInstance(fund, dict)

        for key in ["market_cap", "pe_ratio", "eps", "sector", "52w_high", "52w_low"]:
            self.assertIn(key, fund)
            self.assertTrue(len(str(fund[key])) > 0)


if __name__ == "__main__":
    unittest.main()
