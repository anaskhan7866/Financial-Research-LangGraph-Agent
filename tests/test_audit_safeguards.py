"""
tests/test_audit_safeguards.py — Targeted audit tests for Phase 7 edge cases.
Covers ticker normalization, supervisor fallbacks, iteration caps, and SQLite DB pruning.
"""
import os
import sys
import unittest
from unittest.mock import patch
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
import django
django.setup()

from tools.search_ticker import search_ticker
from agent.state import create_initial_state
from agent.nodes import (
    resolve_ticker_node,
    supervisor_node,
    _fallback_supervisor_decision,
    _decide_next_worker,
)
from agent.router import route_supervisor
from agent.config import MAX_ITERATIONS
from dashboard.models import ResearchSession
from dashboard.views import _persist_session


class TestTickerNormalizationAudit(unittest.TestCase):
    """Verifies Area 1: Ticker sanitization, fast-path, and fallback."""

    def test_lowercase_and_company_name_resolution(self):
        """Ensure common company names map to appropriate tickers."""
        self.assertEqual(search_ticker("reliance"), "RELIANCE.BSE")
        self.assertEqual(search_ticker("tata motors"), "TATAMOTORS.BSE")
        self.assertEqual(search_ticker("infosys"), "INFY")
        self.assertEqual(search_ticker("lenska"), "LENS")

    def test_dollar_sign_and_whitespace_strip(self):
        """Ensure leading $ and messy whitespace are sanitized."""
        self.assertEqual(search_ticker("  $aapl  "), "AAPL")
        self.assertEqual(search_ticker("$MSFT"), "MSFT")

    def test_phrase_ticker_extraction(self):
        """Ensure company names within conversational queries are detected."""
        self.assertEqual(search_ticker("Tell me about reliance industries"), "RELIANCE.BSE")
        self.assertEqual(search_ticker("What is the trend for tata motors?"), "TATAMOTORS.BSE")

    @patch("tools.search_ticker.requests.get")
    def test_api_failure_benchmark_fallback(self, mock_get):
        """Ensure Alpha Vantage errors gracefully fallback to benchmark US ticker."""
        mock_get.side_effect = Exception("Alpha Vantage API timeout")
        self.assertEqual(search_ticker("UnknownNonexistentCompany"), "AAPL")

    def test_resolve_ticker_node_sanitization(self):
        """Ensure resolve_ticker_node sanitizes lowercase ticker in state."""
        state = create_initial_state(query="Analyze reliance", ticker="reliance")
        result = resolve_ticker_node(state)
        self.assertEqual(result["ticker"], "RELIANCE.BSE")


class TestSupervisorRoutingAudit(unittest.TestCase):
    """Verifies Area 2: Edge-case routing, fallbacks, and infinite loop prevention."""

    def test_fallback_supervisor_progression(self):
        """Ensure fallback supervisor completes quant, fundamental, and sentiment before Synthesizer."""
        state = create_initial_state("Analyze Apple", "AAPL")
        self.assertEqual(_fallback_supervisor_decision(state), "quant_agent")

        state["messages"].append({"sender": "quant_agent", "content": "Done"})
        self.assertEqual(_fallback_supervisor_decision(state), "fundamental_agent")

        state["messages"].append({"sender": "fundamental_agent", "content": "Done"})
        self.assertEqual(_fallback_supervisor_decision(state), "sentiment_agent")

        state["messages"].append({"sender": "sentiment_agent", "content": "Done"})
        self.assertEqual(_fallback_supervisor_decision(state), "Synthesizer")

    def test_iteration_limit_enforced_in_supervisor_and_router(self):
        """Ensure exceeding MAX_ITERATIONS immediately routes to Synthesizer."""
        state = create_initial_state("Analyze Apple", "AAPL")
        state["iterations"] = MAX_ITERATIONS

        self.assertEqual(_fallback_supervisor_decision(state), "Synthesizer")
        self.assertEqual(_decide_next_worker(state), "Synthesizer")
        self.assertEqual(route_supervisor(state), "Synthesizer")

    @patch("agent.nodes.get_llm")
    def test_llm_exception_triggers_graceful_fallback(self, mock_llm):
        """Ensure LLM structured output exceptions fallback cleanly."""
        mock_llm.side_effect = RuntimeError("LLM unavailable")
        state = create_initial_state("Analyze Apple", "AAPL")
        decision = supervisor_node(state)
        self.assertEqual(decision["next_worker"], "quant_agent")

    def test_router_handles_unexpected_string(self):
        """Ensure router maps unexpected worker strings to Synthesizer."""
        self.assertEqual(route_supervisor({"next_worker": "invalid_worker_xyz"}), "Synthesizer")
        self.assertEqual(route_supervisor({"next_worker": ""}), "Synthesizer")


class TestDatabasePruningAudit(unittest.TestCase):
    """Verifies Area 4: Safe pruning past 50 records under SQLite."""

    def setUp(self):
        ResearchSession.objects.all().delete()

    def tearDown(self):
        ResearchSession.objects.all().delete()

    def test_safe_pruning_past_50_limit(self):
        """Ensure batch creation past 50 records prunes excess cleanly."""
        for i in range(52):
            ResearchSession.objects.create(
                ticker=f"T{i:02d}",
                query=f"Query {i}",
                summary=f"Summary {i}",
            )
        self.assertEqual(ResearchSession.objects.count(), 52)

        # Trigger persist session which runs atomic prune
        _persist_session("NEW", "Query New", {"summary": "Summary New"})

        # Count must now be capped at 50
        count = ResearchSession.objects.count()
        self.assertLessEqual(count, 50)


if __name__ == "__main__":
    unittest.main()
