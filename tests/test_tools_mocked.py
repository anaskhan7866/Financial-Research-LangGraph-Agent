"""
tests/test_tools_mocked.py — Unit tests with mocked network responses.
Validates data tool parsing and formatting without relying on live network or API quotas.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add project root to sys.path
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
    """Test tools using mocked external HTTP requests."""

    @patch("tools.search_ticker.requests.get")
    def test_search_ticker_parsing(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "bestMatches": [
                {"1. symbol": "NVDA", "2. name": "NVIDIA Corporation"}
            ]
        }
        mock_get.return_value = mock_resp

        result = search_ticker("Nvidia Corp")
        self.assertEqual(result, "NVDA")

    @patch("tools.price_fetch.requests.get")
    def test_price_fetch_parsing(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "Time Series (Daily)": {
                "2026-03-01": {"1. open": "100", "2. high": "105", "3. low": "99", "4. close": "104", "5. volume": "50000"},
                "2026-03-02": {"1. open": "104", "2. high": "108", "3. low": "103", "4. close": "107", "5. volume": "60000"},
            }
        }
        mock_get.return_value = mock_resp

        # Bypass cache
        with patch("tools.price_fetch.get_cache", return_value=None):
            df = get_price_data("TEST_MOCK_TICKER")
            self.assertEqual(len(df), 2)
            self.assertEqual(df["close"].iloc[-1], 107.0)

    @patch("tools.news_fetch.requests.get")
    def test_news_sentiment_translation(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "feed": [
                {"title": "Breakthrough AI launch", "url": "https://example.com/1", "overall_sentiment_score": "0.45"},
                {"title": "Regulatory scrutiny rises", "url": "https://example.com/2", "overall_sentiment_score": "-0.40"},
            ]
        }
        mock_get.return_value = mock_resp

        with patch("tools.news_fetch.get_cache", return_value=None):
            news = get_news("TEST_NEWS_TICKER")
            self.assertEqual(len(news), 2)
            self.assertEqual(news[0]["sentiment"], "Very Positive")
            self.assertEqual(news[1]["sentiment"], "Very Negative")

    @patch("tools.fundamentals.requests.get")
    def test_fundamentals_formatting(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "Symbol": "MSFT",
            "MarketCapitalization": "3150000000000",
            "PERatio": "34.2",
            "EPS": "11.85",
            "Sector": "Technology",
            "52WeekHigh": "450.00",
            "52WeekLow": "300.00",
        }
        mock_get.return_value = mock_resp

        with patch("tools.fundamentals.get_cache", return_value=None):
            fund = get_fundamentals("TEST_FUND_TICKER")
            self.assertEqual(fund["market_cap"], "$3.15T")
            self.assertEqual(fund["pe_ratio"], "34.2")
            self.assertEqual(fund["eps"], "$11.85")


if __name__ == "__main__":
    unittest.main()
