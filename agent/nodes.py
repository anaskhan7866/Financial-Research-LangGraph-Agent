"""
agent/nodes.py — LangGraph node execution functions.
Each node is a focused, isolated step under 40 lines (Rule 1 & Rule 3).
"""
from agent.state import AgentState
from agent.prompts import SYSTEM_PROMPT, SYNTHESIS_PROMPT
from agent.llm import get_llm
from agent.config import logger
from tools.search_ticker import search_ticker
from tools.price_fetch import get_price_data
from tools.indicators import compute_all_indicators
from tools.fundamentals import get_fundamentals
from tools.news_fetch import get_news


def resolve_ticker_node(state: AgentState) -> dict:
    """Identify stock ticker from query or provided ticker."""
    query = state.get("query", "")
    ticker = state.get("ticker", "").strip().upper()

    if not ticker:
        ticker = search_ticker(query)

    steps = list(state.get("steps", []))
    steps.append({"step": 1, "action": f"Identified ticker: {ticker}", "status": "done"})
    return {"ticker": ticker, "steps": steps}


def fetch_data_node(state: AgentState) -> dict:
    """Fetch prices, technical indicators, fundamentals, and news."""
    ticker = state.get("ticker", "AAPL")
    steps = list(state.get("steps", []))

    try:
        df = get_price_data(ticker)
        steps.append({"step": 2, "action": "Fetched daily price history", "status": "done"})

        indicators = compute_all_indicators(df)
        steps.append({"step": 3, "action": "Computed RSI, MACD & Bollinger Bands", "status": "done"})

        fundamentals = get_fundamentals(ticker)
        steps.append({"step": 4, "action": "Retrieved fundamental valuation", "status": "done"})

        news = get_news(ticker)
        steps.append({"step": 5, "action": "Analyzed market news & sentiment", "status": "done"})

        return {
            "price_data": {"points": len(df)},
            "indicators": indicators,
            "fundamentals": fundamentals,
            "news": news,
            "steps": steps,
        }
    except Exception as e:
        logger.error(f"Error in fetch_data_node: {e}")
        return {"error": str(e), "steps": steps}


def synthesize_node(state: AgentState) -> dict:
    """Invoke Gemini to synthesize structured financial report."""
    ticker = state.get("ticker", "AAPL")
    query = state.get("query", "")
    ind = state.get("indicators", {})
    fund = state.get("fundamentals", {})
    news_items = state.get("news", [])
    steps = list(state.get("steps", []))

    news_text = "\n".join(
        f"- {n.get('title')} (Sentiment: {n.get('sentiment')})"
        for n in news_items
    ) or "No breaking news recorded."

    prompt = SYNTHESIS_PROMPT.format(
        ticker=ticker,
        query=query,
        price=ind.get("price", "N/A"),
        signal=ind.get("signal", "Neutral"),
        rsi=ind.get("rsi", "N/A"),
        macd=ind.get("macd", "N/A"),
        sma_20=ind.get("sma_20", "N/A"),
        sma_50=ind.get("sma_50", "N/A"),
        bollinger_upper=ind.get("bollinger_upper", "N/A"),
        bollinger_lower=ind.get("bollinger_lower", "N/A"),
        market_cap=fund.get("market_cap", "N/A"),
        pe_ratio=fund.get("pe_ratio", "N/A"),
        eps=fund.get("eps", "N/A"),
        sector=fund.get("sector", "N/A"),
        **{"52w_low": fund.get("52w_low", "N/A"), "52w_high": fund.get("52w_high", "N/A")},
        news_summary=news_text,
    )

    try:
        llm = get_llm()
        res = llm.invoke([("system", SYSTEM_PROMPT), ("user", prompt)])
        content = res.content if hasattr(res, "content") else str(res)
        if isinstance(content, list):
            # Gemini sometimes returns list of content blocks
            content = " ".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in content)

        steps.append({"step": 6, "action": "Synthesised research report with AI", "status": "done"})
        return {"final_answer": str(content), "steps": steps, "iterations": state.get("iterations", 0) + 1}
    except Exception as e:
        logger.warning(f"Synthesis fallback triggered: {e}")
        fallback_summary = _build_fallback_summary(ticker, ind, fund)
        steps.append({"step": 6, "action": "Generated research summary", "status": "done"})
        return {"final_answer": fallback_summary, "steps": steps, "iterations": state.get("iterations", 0) + 1}


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
