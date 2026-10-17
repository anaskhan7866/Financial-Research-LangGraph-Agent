"""
agent/graph.py — Assembles and executes the LangGraph Financial Research Agent.
Implements a multi-agent star topology supervised workflow.
"""
from langgraph.graph import StateGraph, START, END
from agent.state import AgentState, create_initial_state
from agent.nodes import (
    resolve_ticker_node,
    supervisor_node,
    quant_agent_node,
    sentiment_agent_node,
    fundamental_agent_node,
    synthesize_node,
    check_fallback_data,
)
from agent.router import route_supervisor
from agent.config import logger


def build_graph():
    """Build and compile the multi-agent Supervisor-Worker workflow."""
    workflow = StateGraph(AgentState)

    workflow.add_node("ResolveTicker", resolve_ticker_node)
    workflow.add_node("Supervisor", supervisor_node)
    workflow.add_node("quant_agent", quant_agent_node)
    workflow.add_node("sentiment_agent", sentiment_agent_node)
    workflow.add_node("fundamental_agent", fundamental_agent_node)
    workflow.add_node("Synthesizer", synthesize_node)

    workflow.add_edge(START, "ResolveTicker")
    workflow.add_edge("ResolveTicker", "Supervisor")

    workflow.add_conditional_edges(
        "Supervisor",
        route_supervisor,
        {
            "quant_agent": "quant_agent",
            "sentiment_agent": "sentiment_agent",
            "fundamental_agent": "fundamental_agent",
            "Synthesizer": "Synthesizer",
        },
    )

    workflow.add_edge("quant_agent", "Supervisor")
    workflow.add_edge("sentiment_agent", "Supervisor")
    workflow.add_edge("fundamental_agent", "Supervisor")
    workflow.add_edge("Synthesizer", END)

    return workflow.compile()


# Global compiled graph instance
agent_app = build_graph()


def run_agent(query: str, ticker: str = "") -> dict:
    """
    Execute full agent cycle for a research inquiry.
    Returns dictionary conforming exactly to UI expectations.
    """
    logger.info(f"Starting agent run for query='{query}', ticker='{ticker}'")
    initial_state = create_initial_state(query=query, ticker=ticker)

    try:
        final_state = agent_app.invoke(initial_state)
    except Exception as e:
        logger.error(f"Error during graph execution: {e}")
        final_state = initial_state
        final_state["final_answer"] = f"Analysis could not be completed: {str(e)}"

    is_fallback = check_fallback_data(final_state)
    return {
        "ticker": final_state.get("ticker", "AAPL"),
        "query": final_state.get("query", query),
        "steps": final_state.get("steps", []),
        "fundamentals": final_state.get("fundamentals", {}),
        "indicators": final_state.get("indicators", {}),
        "news": final_state.get("news", []),
        "summary": final_state.get("final_answer", "No summary generated."),
        "is_fallback": is_fallback,
        "warning": (
            "⚠️ Market data provider temporarily unavailable. Displaying cached/modeled fallback data to keep your analysis uninterrupted."
            if is_fallback else None
        ),
    }

