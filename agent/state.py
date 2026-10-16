"""
agent/state.py — Strongly typed state definition for the LangGraph agent (Rule 6).
Every key has an explicit type and default value.
"""
import operator
from typing import TypedDict, Optional, List, Dict, Any, Annotated


class AgentState(TypedDict):
    """Structured state container carried through all LangGraph nodes."""
    query: str
    ticker: str
    steps: List[Dict[str, Any]]
    price_data: Dict[str, Any]
    indicators: Dict[str, Any]
    news: List[Dict[str, Any]]
    fundamentals: Dict[str, Any]
    messages: Annotated[List[Dict[str, str]], operator.add]
    next_worker: str
    sender: str
    iterations: int
    final_answer: str
    error: Optional[str]


def create_initial_state(query: str, ticker: str = "") -> AgentState:
    """Create a clean AgentState with default values."""
    clean_ticker = (ticker or "").strip().upper()
    return {
        "query": query.strip(),
        "ticker": clean_ticker,
        "steps": [],
        "price_data": {},
        "indicators": {},
        "news": [],
        "fundamentals": {},
        "messages": [],
        "next_worker": "",
        "sender": "",
        "iterations": 0,
        "final_answer": "",
        "error": None,
    }

