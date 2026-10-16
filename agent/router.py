"""
agent/router.py — Conditional routing logic for the LangGraph agent cycle.
Enforces loop limits and routes around errors (Rule 7 & Rule 8).
"""
from agent.state import AgentState
from agent.config import MAX_ITERATIONS


def route_after_fetch(state: AgentState) -> str:
    """
    Decide next step after fetching financial data.
    """
    if state.get("error"):
        return "fallback"
    if state.get("iterations", 0) >= MAX_ITERATIONS:
        return "fallback"
    return "synthesize"
