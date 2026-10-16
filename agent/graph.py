"""
agent/graph.py — Assembles and executes the LangGraph Financial Research Agent.
Exposes run_agent() which returns structured research matching the frontend contract.
"""
from langgraph.graph import StateGraph, START, END
from agent.state import AgentState, create_initial_state
from agent.nodes import resolve_ticker_node, fetch_data_node, synthesize_node
from agent.router import route_after_fetch
from agent.config import logger


def build_graph():
    """Build and compile the LangGraph workflow."""
    workflow = StateGraph(AgentState)

    workflow.add_node("resolve_ticker", resolve_ticker_node)
    workflow.add_node("fetch_data", fetch_data_node)
    workflow.add_node("synthesize", synthesize_node)

    workflow.add_edge(START, "resolve_ticker")
    workflow.add_edge("resolve_ticker", "fetch_data")
    workflow.add_conditional_edges(
        "fetch_data",
        route_after_fetch,
        {
            "synthesize": "synthesize",
            "fallback": "synthesize",
        }
    )
    workflow.add_edge("synthesize", END)

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

    return {
        "ticker": final_state.get("ticker", "AAPL"),
        "query": final_state.get("query", query),
        "steps": final_state.get("steps", []),
        "fundamentals": final_state.get("fundamentals", {}),
        "indicators": final_state.get("indicators", {}),
        "news": final_state.get("news", []),
        "summary": final_state.get("final_answer", "No summary generated."),
    }
