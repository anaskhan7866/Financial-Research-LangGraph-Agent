"""
agent/router.py — Conditional routing logic for the LangGraph agent cycle.
Enforces loop limits and routes around errors (Rule 7 & Rule 8).
"""
from agent.state import AgentState
from agent.config import MAX_ITERATIONS


def route_after_fetch(state: AgentState) -> str:
    """Decide next step after fetching financial data (legacy support)."""
    if state.get("error"):
        return "fallback"
    if state.get("iterations", 0) >= MAX_ITERATIONS:
        return "fallback"
    return "synthesize"


def route_supervisor(state: AgentState) -> str:
    """Route from Supervisor to the chosen worker or Synthesizer."""
    worker = (state.get("next_worker") or "").strip()
    mapping = {
        "quant_agent": "quant_agent",
        "quant_agent_node": "quant_agent",
        "sentiment_agent": "sentiment_agent",
        "sentiment_agent_node": "sentiment_agent",
        "fundamental_agent": "fundamental_agent",
        "fundamental_agent_node": "fundamental_agent",
        "synthesizer": "Synthesizer",
        "Synthesizer": "Synthesizer",
        "synthesize": "Synthesizer",
    }
    return mapping.get(worker, "Synthesizer")

