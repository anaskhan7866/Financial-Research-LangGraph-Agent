"""
tests/test_phase6_7_integration.py — Integration tests for Phase 6 (Agent in Django) and Phase 7 (Database History).
Verifies end-to-end execution through Django views and SQLite persistence.
"""
import os
import sys
import json
import unittest
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
import django
django.setup()

from django.test import Client
from dashboard.models import ResearchSession


class TestPhase6And7(unittest.TestCase):
    """Test full cycle: Django view -> LangGraph agent -> SQLite database."""

    def setUp(self):
        self.client = Client()

    def test_analyze_persists_session_and_returns_payload(self):
        initial_count = ResearchSession.objects.count()

        payload = {"ticker": "AAPL", "query": "Analyze Apple financial indicators"}
        res = self.client.post(
            "/analyze/",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()

        # Validate agent contract
        self.assertEqual(data["ticker"], "AAPL")
        self.assertIn("summary", data)
        self.assertIn("indicators", data)
        self.assertIn("fundamentals", data)
        self.assertIn("news", data)

        # Validate database persistence
        new_count = ResearchSession.objects.count()
        self.assertEqual(new_count, initial_count + 1)

        latest = ResearchSession.objects.first()
        self.assertEqual(latest.ticker, "AAPL")
        self.assertEqual(latest.query, payload["query"])

    def test_history_endpoint_returns_saved_sessions(self):
        # Create a test session
        ResearchSession.objects.create(
            ticker="NVDA",
            query="Analyze NVDA AI market position",
            summary="Strong growth",
            indicators={"rsi": "62.5", "signal": "Bullish"},
            fundamentals={"market_cap": "$3.1T"},
            news=[]
        )

        res = self.client.get("/history/")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("history", data)
        self.assertGreater(len(data["history"]), 0)

        first = data["history"][0]
        self.assertIn("ticker", first)
        self.assertIn("query", first)
        self.assertIn("created_at", first)


if __name__ == "__main__":
    unittest.main()
