"""
agent/nodes.py — LangGraph multi-agent node execution functions.
Each node is a focused, isolated step under 40 lines (Rule 1 & Rule 3).
"""
from typing import Literal
from pydantic import BaseModel, Field
from agent.state import AgentState
from agent.prompts import SYSTEM_PROMPT, SYNTHESIS_PROMPT, SUPERVISOR_SYSTEM_PROMPT
from agent.llm import get_llm
from agent.config import logger, MAX_ITERATIONS
from tools.search_ticker import search_ticker
from tools.price_fetch import get_price_data
from tools.indicators import compute_all_indicators
from tools.fundamentals import get_fundamentals
from tools.news_fetch import get_news


class SupervisorDecision(BaseModel):
    """Pydantic structured output model for supervisor decisions."""
    next_worker: Literal["quant_agent", "sentiment_agent", "fundamental_agent", "Synthesizer"] = Field(
        description="Next worker to delegate to: 'quant_agent', 'sentiment_agent', 'fundamental_agent', or 'Synthesizer'."
    )
    reasoning: str = Field(
        default="",
        description="Brief justification for selecting this worker next."
    )


def resolve_ticker_node(state: AgentState) -> dict:
    """Identify stock ticker from query or provided ticker."""
    query = state.get("query", "")
    ticker = state.get("ticker", "").strip().upper()
    if not ticker:
        ticker = search_ticker(query)
    steps = list(state.get("steps", []))
    steps.append({"step": 1, "action": f"Identified ticker: {ticker}", "status": "done"})
    msg = {"sender": "resolve_ticker", "content": f"Identified ticker: {ticker}"}
    return {"ticker": ticker, "steps": steps, "sender": "resolve_ticker", "messages": [msg]}


def quant_agent_node(state: AgentState) -> dict:
    """Fetch price data and compute quantitative technical indicators."""
    ticker = state.get("ticker", "AAPL")
    steps = list(state.get("steps", []))
    try:
        df = get_price_data(ticker)
        indicators = compute_all_indicators(df)
        steps.append({"step": len(steps) + 1, "action": "Computed technical indicators & price history", "status": "done"})
        msg = {"sender": "quant_agent", "content": f"Quant completed: computed indicators for {ticker}."}
        return {
            "price_data": {"points": len(df)},
            "indicators": indicators,
            "steps": steps,
            "sender": "quant_agent",
            "messages": [msg],
        }
    except Exception as e:
        logger.error(f"Error in quant_agent_node: {e}")
        err_msg = {"sender": "quant_agent", "content": f"Quant error: {e}"}
        return {"error": str(e), "steps": steps, "sender": "quant_agent", "messages": [err_msg]}


def sentiment_agent_node(state: AgentState) -> dict:
    """Fetch recent news articles and evaluate sentiment."""
    ticker = state.get("ticker", "AAPL")
    steps = list(state.get("steps", []))
    try:
        news = get_news(ticker)
        steps.append({"step": len(steps) + 1, "action": "Analyzed market news & sentiment", "status": "done"})
        msg = {"sender": "sentiment_agent", "content": f"Sentiment completed: retrieved {len(news)} articles."}
        return {
            "news": news,
            "steps": steps,
            "sender": "sentiment_agent",
            "messages": [msg],
        }
    except Exception as e:
        logger.error(f"Error in sentiment_agent_node: {e}")
        err_msg = {"sender": "sentiment_agent", "content": f"Sentiment error: {e}"}
        return {"error": str(e), "steps": steps, "sender": "sentiment_agent", "messages": [err_msg]}


def fundamental_agent_node(state: AgentState) -> dict:
    """Retrieve fundamental company valuation and financial profile."""
    ticker = state.get("ticker", "AAPL")
    steps = list(state.get("steps", []))
    try:
        fundamentals = get_fundamentals(ticker)
        steps.append({"step": len(steps) + 1, "action": "Retrieved fundamental valuation", "status": "done"})
        msg = {"sender": "fundamental_agent", "content": f"Fundamentals completed for {ticker}."}
        return {
            "fundamentals": fundamentals,
            "steps": steps,
            "sender": "fundamental_agent",
            "messages": [msg],
        }
    except Exception as e:
        logger.error(f"Error in fundamental_agent_node: {e}")
        err_msg = {"sender": "fundamental_agent", "content": f"Fundamental error: {e}"}
        return {"error": str(e), "steps": steps, "sender": "fundamental_agent", "messages": [err_msg]}


def _fallback_supervisor_decision(state: AgentState) -> str:
    """Determine next worker deterministically when LLM is offline or in test."""
    senders = {m.get("sender") for m in state.get("messages", []) if isinstance(m, dict)}
    if "quant_agent" not in senders and not state.get("indicators"):
        return "quant_agent"
    if "fundamental_agent" not in senders and not state.get("fundamentals"):
        return "fundamental_agent"
    if "sentiment_agent" not in senders and not state.get("news"):
        return "sentiment_agent"
    return "Synthesizer"


def _decide_next_worker(state: AgentState) -> str:
    """Call LLM with structured output or fallback to deterministic router."""
    if state.get("iterations", 0) >= MAX_ITERATIONS:
        return "Synthesizer"
    try:
        llm = get_llm()
        structured_llm = llm.with_structured_output(SupervisorDecision)
        log = "\n".join(f"[{m.get('sender', '')}]: {m.get('content', '')}" for m in state.get("messages", []))
        prompt = f"Query: {state.get('query')}\nTicker: {state.get('ticker')}\nLog:\n{log}"
        decision = structured_llm.invoke([("system", SUPERVISOR_SYSTEM_PROMPT), ("user", prompt)])
        if isinstance(decision, SupervisorDecision):
            return decision.next_worker
        if isinstance(decision, dict) and "next_worker" in decision:
            return decision["next_worker"]
        if hasattr(decision, "next_worker") and isinstance(decision.next_worker, str):
            return decision.next_worker
    except Exception as e:
        logger.warning(f"Supervisor structured output fallback: {e}")
    return _fallback_supervisor_decision(state)


def supervisor_node(state: AgentState) -> dict:
    """Analyze messages and delegate tasks to specialists or Synthesizer."""
    next_worker = _decide_next_worker(state)
    new_iter = state.get("iterations", 0) + 1
    msg = {"sender": "supervisor", "content": f"Dispatched task to: {next_worker}"}
    return {
        "next_worker": next_worker,
        "sender": "supervisor",
        "iterations": new_iter,
        "messages": [msg],
    }


def _build_synthesis_prompt(state: AgentState) -> str:
    """Construct synthesis prompt from current state."""
    ticker = state.get("ticker", "AAPL")
    query = state.get("query", "")
    ind = state.get("indicators", {})
    fund = state.get("fundamentals", {})
    news_text = "\n".join(
        f"- {n.get('title')} (Sentiment: {n.get('sentiment')})"
        for n in state.get("news", [])
    ) or "No breaking news recorded."
    return SYNTHESIS_PROMPT.format(
        ticker=ticker, query=query, price=ind.get("price", "N/A"),
        signal=ind.get("signal", "Neutral"), rsi=ind.get("rsi", "N/A"),
        macd=ind.get("macd", "N/A"), sma_20=ind.get("sma_20", "N/A"),
        sma_50=ind.get("sma_50", "N/A"), bollinger_upper=ind.get("bollinger_upper", "N/A"),
        bollinger_lower=ind.get("bollinger_lower", "N/A"), market_cap=fund.get("market_cap", "N/A"),
        pe_ratio=fund.get("pe_ratio", "N/A"), eps=fund.get("eps", "N/A"),
        sector=fund.get("sector", "N/A"), news_summary=news_text,
        **{"52w_low": fund.get("52w_low", "N/A"), "52w_high": fund.get("52w_high", "N/A")},
    )


def synthesize_node(state: AgentState) -> dict:
    """Invoke LLM to synthesize structured financial report."""
    ticker = state.get("ticker", "AAPL")
    steps = list(state.get("steps", []))
    prompt = _build_synthesis_prompt(state)
    try:
        llm = get_llm()
        res = llm.invoke([("system", SYSTEM_PROMPT), ("user", prompt)])
        content = res.content if hasattr(res, "content") else str(res)
        if isinstance(content, list):
            content = " ".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in content)
        steps.append({"step": len(steps) + 1, "action": "Synthesised research report with AI", "status": "done"})
        answer = str(content)
    except Exception as e:
        logger.warning(f"Synthesis fallback triggered: {e}")
        steps.append({"step": len(steps) + 1, "action": "Generated research summary", "status": "done"})
        answer = _build_fallback_summary(ticker, state.get("indicators", {}), state.get("fundamentals", {}))

    return {
        "final_answer": answer,
        "steps": steps,
        "sender": "Synthesizer",
        "iterations": state.get("iterations", 0) + 1,
    }


def _build_fallback_summary(ticker: str, ind: dict, fund: dict) -> str:
    """Produce structured markdown report when LLM is unavailable."""
    return (
        f"**{ticker}** is currently trading at **{ind.get('price', '$0.00')}**, "
        f"reflecting a **{ind.get('signal', 'Neutral')}** technical posture.\n\n"
        f"**Technical Momentum**: The RSI stands at **{ind.get('rsi', '50.0')}**, indicating "
        f"balanced buying pressure. MACD is at **{ind.get('macd', '0.00')}** with the 20-day SMA "
        f"at {ind.get('sma_20', 'N/A')} and 50-day SMA at {ind.get('sma_50', 'N/A')}.\n\n"
        f"**Fundamental Valuation**: Market capitalization is **{fund.get('market_cap', 'N/A')}** "
        f"with a trailing P/E of **{fund.get('pe_ratio', 'N/A')}** and EPS of {fund.get('eps', 'N/A')} "
        f"in the {fund.get('sector', 'General')} sector.\n\n"
        f"**Outlook**: Watch key Bollinger levels between {ind.get('bollinger_lower', 'N/A')} "
        f"and {ind.get('bollinger_upper', 'N/A')} for directional confirmation."
    )


def fetch_data_node(state: AgentState) -> dict:
    """Legacy helper for backward compatibility."""
    q_res = quant_agent_node(state)
    f_res = fundamental_agent_node(state)
    s_res = sentiment_agent_node(state)
    return {
        "price_data": q_res.get("price_data", {}),
        "indicators": q_res.get("indicators", {}),
        "fundamentals": f_res.get("fundamentals", {}),
        "news": s_res.get("news", []),
        "steps": q_res.get("steps", []) + f_res.get("steps", []) + s_res.get("steps", []),
    }
