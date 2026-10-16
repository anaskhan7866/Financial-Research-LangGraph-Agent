"""
tests/test_phase5_agent.py — Unit and integration tests for Phase 5 LangGraph agent.
Verifies state creation, nodes, graph assembly, and run_agent execution.
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

from agent.state import create_initial_state
from agent.nodes import resolve_ticker_node, fetch_data_node, synthesize_node
from agent.graph import build_graph, run_agent


class TestStateAndNodes(unittest.TestCase):
    """Test state management and individual node functions."""

    def test_create_initial_state(self):
        state = create_initial_state("Analyze Tesla stock", "TSLA")
        self.assertEqual(state["ticker"], "TSLA")
        self.assertEqual(state["query"], "Analyze Tesla stock")
        self.assertEqual(state["iterations"], 0)
        self.assertEqual(state["steps"], [])
        self.assertIsNone(state["error"])

    def test_resolve_ticker_node(self):
        state = create_initial_state("Analyze Microsoft", "")
        res = resolve_ticker_node(state)
        self.assertTrue(len(res["ticker"]) > 0)
        self.assertTrue(len(res["steps"]) > 0)

    def test_fetch_data_node(self):
        state = create_initial_state("AAPL query", "AAPL")
        res = fetch_data_node(state)
        self.assertIn("indicators", res)
        self.assertIn("fundamentals", res)
        self.assertIn("news", res)
        self.assertGreater(len(res["steps"]), 1)


class TestGraphExecution(unittest.TestCase):
    """Test compiled graph construction and execution."""

    def test_build_graph(self):
        app = build_graph()
        self.assertIsNotNone(app)

    def test_run_agent_contract(self):
        result = run_agent(query="Analyze Apple technicals and fundamentals", ticker="AAPL")
        self.assertEqual(result["ticker"], "AAPL")
        self.assertTrue(len(result["steps"]) >= 4)
        self.assertIn("rsi", result["indicators"])
        self.assertIn("market_cap", result["fundamentals"])
        self.assertIsInstance(result["news"], list)
        self.assertTrue(len(result["summary"]) > 20)


if __name__ == "__main__":
    unittest.main()
