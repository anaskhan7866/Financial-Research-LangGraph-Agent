"""
tests/test_tools_mocked.py — Unit tests with mocked yfinance responses.
Validates data tool parsing and formatting without relying on live network or external quotas.
"""
import os
import sys
import unittest
from unittest.mock import patch
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
import django
django.setup()

from tools.search_ticker import search_ticker
from tools.price_fetch import get_price_data
from tools.news_fetch import get_news
from tools.fundamentals import get_fundamentals


class TestToolsMocked(unittest.TestCase):
    """Test data tools using mocked yfinance structures."""

    def test_search_ticker_parsing(self):
        """Test ticker symbol lookup, Indian formats, and keyword heuristics."""
        self.assertEqual(search_ticker("NVDA"), "NVDA")
        self.assertEqual(search_ticker("RELIANCE.NS"), "RELIANCE.NS")
        self.assertEqual(search_ticker("TCS.BO"), "TCS.BO")
        self.assertEqual(search_ticker("Nvidia Corp"), "NVDA")
        self.assertEqual(search_ticker("Analyze tata motors"), "TATAMOTORS.NS")

    @patch("tools.price_fetch.yf.Ticker")
    def test_price_fetch_parsing(self, mock_ticker):
        """Test OHLCV history extraction and DataFrame formatting."""
        dates = pd.to_datetime(["2026-03-01", "2026-03-02"])
        mock_df = pd.DataFrame({
            "Open": [100.0, 104.0],
            "High": [105.0, 108.0],
            "Low": [99.0, 103.0],
            "Close": [104.0, 107.0],
            "Volume": [50000.0, 60000.0],
        }, index=dates)
        mock_ticker.return_value.history.return_value = mock_df

        with patch("tools.price_fetch.get_cache", return_value=None):
            df = get_price_data("TEST_MOCK_TICKER")
            self.assertEqual(len(df), 2)
            self.assertEqual(df["close"].iloc[-1], 107.0)
            self.assertIn("open", df.columns)
            self.assertIn("volume", df.columns)

    @patch("tools.news_fetch.yf.Ticker")
    def test_news_sentiment_translation(self, mock_ticker):
        """Test news headline mapping and Neutral sentiment contract."""
        mock_ticker.return_value.news = [
            {"title": "Breakthrough AI launch", "link": "https://example.com/1"},
            {"title": "Regulatory scrutiny rises", "link": "https://example.com/2"},
        ]

        with patch("tools.news_fetch.get_cache", return_value=None):
            news = get_news("TEST_NEWS_TICKER")
            self.assertEqual(len(news), 2)
            self.assertEqual(news[0]["sentiment"], "Neutral")
            self.assertEqual(news[0]["score"], 0.0)
            self.assertEqual(news[0]["title"], "Breakthrough AI launch")
            self.assertEqual(news[0]["url"], "https://example.com/1")

    @patch("tools.fundamentals.yf.Ticker")
    def test_fundamentals_formatting(self, mock_ticker):
        """Test fundamentals extraction and currency formatting."""
        mock_ticker.return_value.info = {
            "marketCap": 3150000000000,
            "trailingPE": 34.2,
            "trailingEps": 11.85,
            "sector": "Technology",
            "fiftyTwoWeekHigh": 450.00,
            "fiftyTwoWeekLow": 300.00,
        }

        with patch("tools.fundamentals.get_cache", return_value=None):
            fund = get_fundamentals("TEST_FUND_TICKER")
            self.assertEqual(fund["market_cap"], "$3.15T")
            self.assertEqual(fund["pe_ratio"], "34.2")
            self.assertEqual(fund["eps"], "$11.85")
            self.assertEqual(fund["sector"], "Technology")
            self.assertEqual(fund["52w_high"], "$450.00")
            self.assertEqual(fund["52w_low"], "$300.00")


if __name__ == "__main__":
    unittest.main()
