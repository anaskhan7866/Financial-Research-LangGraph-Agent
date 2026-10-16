"""
tests/test_supervisor_architecture.py — Tests for Multi-Agent Supervisor-Worker Architecture.
Verifies AgentState reducers, specialized nodes, Pydantic structured routing, and graph topology.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
import django
django.setup()

from agent.state import create_initial_state, AgentState
from agent.nodes import (
    SupervisorDecision,
    resolve_ticker_node,
    supervisor_node,
    quant_agent_node,
    sentiment_agent_node,
    fundamental_agent_node,
    synthesize_node,
)
from agent.router import route_supervisor
from agent.graph import build_graph, run_agent


class TestSupervisorWorkerArchitecture(unittest.TestCase):
    """Test suite for supervisor-worker multi-agent design."""

    def test_state_structure(self):
        """Test state fields and default initialization."""
        state = create_initial_state("Analyze AAPL", "AAPL")
        self.assertEqual(state["ticker"], "AAPL")
        self.assertIn("messages", state)
        self.assertIn("next_worker", state)
        self.assertIn("sender", state)
        self.assertEqual(state["next_worker"], "")
        self.assertEqual(state["sender"], "")

    def test_pydantic_supervisor_decision_schema(self):
        """Verify SupervisorDecision Pydantic schema."""
        decision = SupervisorDecision(next_worker="quant_agent", reasoning="Needs quant data")
        self.assertEqual(decision.next_worker, "quant_agent")
        self.assertEqual(decision.reasoning, "Needs quant data")

        decision_synth = SupervisorDecision(next_worker="Synthesizer")
        self.assertEqual(decision_synth.next_worker, "Synthesizer")

    @patch("agent.nodes.compute_all_indicators")
    @patch("agent.nodes.get_price_data")
    def test_quant_agent_node(self, mock_price, mock_indicators):
        """Test quant agent updates payload and appends success message."""
        mock_price.return_value = pd.DataFrame({"close": [150.0, 155.0]})
        mock_indicators.return_value = {"rsi": 55.0, "macd": 1.2}

        state = create_initial_state("Analyze AAPL", "AAPL")
        res = quant_agent_node(state)

        self.assertIn("indicators", res)
        self.assertIn("price_data", res)
        self.assertEqual(res["sender"], "quant_agent")
        self.assertTrue(any(m["sender"] == "quant_agent" for m in res["messages"]))

    @patch("agent.nodes.get_news")
    def test_sentiment_agent_node(self, mock_news):
        """Test sentiment agent updates payload and appends success message."""
        mock_news.return_value = [{"title": "Strong growth", "sentiment": "Positive"}]

        state = create_initial_state("Analyze AAPL", "AAPL")
        res = sentiment_agent_node(state)

        self.assertIn("news", res)
        self.assertEqual(res["sender"], "sentiment_agent")
        self.assertTrue(any(m["sender"] == "sentiment_agent" for m in res["messages"]))

    @patch("agent.nodes.get_fundamentals")
    def test_fundamental_agent_node(self, mock_fundamentals):
        """Test fundamental agent updates payload and appends success message."""
        mock_fundamentals.return_value = {"market_cap": "$3T", "pe_ratio": "30"}

        state = create_initial_state("Analyze AAPL", "AAPL")
        res = fundamental_agent_node(state)

        self.assertIn("fundamentals", res)
        self.assertEqual(res["sender"], "fundamental_agent")
        self.assertTrue(any(m["sender"] == "fundamental_agent" for m in res["messages"]))

    def test_supervisor_node_fallback_progression(self):
        """Test supervisor routes sequentially when LLM is unavailable."""
        state = create_initial_state("Analyze AAPL", "AAPL")

        # 1. Initially needs quant
        res1 = supervisor_node(state)
        self.assertEqual(res1["next_worker"], "quant_agent")

        # 2. Once quant completed, needs fundamental
        state["messages"].append({"sender": "quant_agent", "content": "Done"})
        res2 = supervisor_node(state)
        self.assertEqual(res2["next_worker"], "fundamental_agent")

        # 3. Once fundamental completed, needs sentiment
        state["messages"].append({"sender": "fundamental_agent", "content": "Done"})
        res3 = supervisor_node(state)
        self.assertEqual(res3["next_worker"], "sentiment_agent")

        # 4. Once all completed, routes to Synthesizer
        state["messages"].append({"sender": "sentiment_agent", "content": "Done"})
        res4 = supervisor_node(state)
        self.assertEqual(res4["next_worker"], "Synthesizer")

    def test_route_supervisor_mapping(self):
        """Test router helper maps next_worker strings properly."""
        self.assertEqual(route_supervisor({"next_worker": "quant_agent"}), "quant_agent")
        self.assertEqual(route_supervisor({"next_worker": "sentiment_agent"}), "sentiment_agent")
        self.assertEqual(route_supervisor({"next_worker": "fundamental_agent"}), "fundamental_agent")
        self.assertEqual(route_supervisor({"next_worker": "Synthesizer"}), "Synthesizer")
        self.assertEqual(route_supervisor({"next_worker": "unknown"}), "Synthesizer")

    @patch("agent.nodes.get_llm")
    @patch("agent.nodes.get_price_data")
    @patch("agent.nodes.get_fundamentals")
    @patch("agent.nodes.get_news")
    def test_full_graph_execution(self, mock_news, mock_fund, mock_price, mock_llm):
        """Test end-to-end star graph execution with mocked LLM."""
        mock_price.return_value = pd.DataFrame({"close": [150.0, 155.0]})
        mock_fund.return_value = {"market_cap": "$3T", "pe_ratio": "30"}
        mock_news.return_value = [{"title": "Good news", "sentiment": "Positive"}]

        mock_llm_inst = MagicMock()
        mock_resp = MagicMock()
        mock_resp.content = "Multi-agent comprehensive financial summary."
        mock_llm_inst.invoke.return_value = mock_resp
        mock_llm.return_value = mock_llm_inst

        result = run_agent("Analyze Apple", "AAPL")
        self.assertEqual(result["ticker"], "AAPL")
        self.assertIn("indicators", result)
        self.assertIn("fundamentals", result)
        self.assertIn("news", result)
        self.assertIn("summary", result)
        self.assertIn("steps", result)
        self.assertIn("Multi-agent comprehensive financial summary", result["summary"])


if __name__ == "__main__":
    unittest.main()
