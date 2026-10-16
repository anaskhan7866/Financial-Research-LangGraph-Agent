"""
tests/test_agent_mocked.py — Unit tests for agent nodes and graph using mocked LLM and tools.
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

import pandas as pd
from agent.state import create_initial_state
from agent.router import route_after_fetch
from agent.graph import run_agent


class TestAgentMocked(unittest.TestCase):
    """Test agent routing and execution with mocks."""

    def test_router_conditions(self):
        # Normal state -> synthesize
        normal_state = create_initial_state("query", "AAPL")
        self.assertEqual(route_after_fetch(normal_state), "synthesize")

        # Error state -> fallback
        error_state = create_initial_state("query", "AAPL")
        error_state["error"] = "Network timeout"
        self.assertEqual(route_after_fetch(error_state), "fallback")

        # Exceeded iterations -> fallback
        max_state = create_initial_state("query", "AAPL")
        max_state["iterations"] = 15
        self.assertEqual(route_after_fetch(max_state), "fallback")

    @patch("agent.nodes.get_llm")
    @patch("agent.nodes.get_price_data")
    @patch("agent.nodes.get_fundamentals")
    @patch("agent.nodes.get_news")
    def test_mocked_graph_run(self, mock_news, mock_fund, mock_prices, mock_llm):
        # Setup mock returns
        mock_prices.return_value = pd.DataFrame({
            "close": [100.0, 102.0, 104.0, 105.0],
            "open": [99.0, 101.0, 103.0, 104.0],
            "high": [101.0, 103.0, 105.0, 106.0],
            "low": [98.0, 100.0, 102.0, 103.0],
            "volume": [1000, 1000, 1000, 1000],
        })
        mock_fund.return_value = {
            "market_cap": "$2.5T", "pe_ratio": "25.0", "eps": "$5.00",
            "sector": "Tech", "52w_high": "$120", "52w_low": "$90"
        }
        mock_news.return_value = [
            {"title": "Positive trend", "url": "#", "sentiment": "Positive", "score": 0.4}
        ]

        mock_llm_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Mocked comprehensive research summary for AAPL."
        mock_llm_instance.invoke.return_value = mock_response
        mock_llm.return_value = mock_llm_instance

        result = run_agent(query="Test query", ticker="AAPL")
        self.assertEqual(result["ticker"], "AAPL")
        self.assertIn("indicators", result)
        self.assertIn("fundamentals", result)
        self.assertIn("Mocked comprehensive research summary", result["summary"])


if __name__ == "__main__":
    unittest.main()
