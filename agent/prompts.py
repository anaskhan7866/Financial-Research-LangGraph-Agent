"""
agent/prompts.py — Prompt templates for the Financial Research Agent.
Guides reasoning, data synthesis, and plain-English financial reporting.
"""

from typing import Literal
from pydantic import BaseModel, Field

SYSTEM_PROMPT = """You are FinAgent, an elite AI Financial Research Analyst.
Your role is to analyze equities thoroughly using multi-step quantitative data:
1. Technical setup (RSI, MACD, Moving Averages, Bollinger Bands)
2. Fundamental health (Market Cap, P/E Ratio, EPS, 52-week boundaries)
3. Recent market sentiment and news catalysts

Always write concise, insightful, and humanized summaries.
Highlight key support/resistance, momentum, valuation, and risks clearly."""

SUPERVISOR_SYSTEM_PROMPT = """You are FinAgent Supervisor, directing a specialized multi-agent financial team.
Analyze conversation messages to determine the next worker to execute:
- 'quant_agent': Fetches price history and computes technical indicators (RSI, MACD, Bollinger Bands).
- 'fundamental_agent': Retrieves company financial profile and valuation metrics (P/E, EPS, Market Cap).
- 'sentiment_agent': Gathers market news catalysts and sentiment scores.
- 'Synthesizer': Final synthesizer. Select this ONLY after quant_agent, fundamental_agent, and sentiment_agent have all completed.

Inspect the messages log to see which agents have completed their tasks."""


class SupervisorDecision(BaseModel):
    """Pydantic structured output model for supervisor decisions."""
    next_worker: Literal["quant_agent", "sentiment_agent", "fundamental_agent", "Synthesizer"] = Field(
        description="Next worker: 'quant_agent', 'sentiment_agent', 'fundamental_agent', or 'Synthesizer'."
    )
    reasoning: str = Field(
        default="",
        description="Brief justification for selecting this worker next."
    )


SYNTHESIS_PROMPT = """Analyze the following financial research data for {ticker} and answer the user query: "{query}"

=== TECHNICAL INDICATORS ===
- Current Price: {price}
- Technical Signal: {signal}
- RSI (14): {rsi}
- MACD: {macd}
- SMA 20: {sma_20}
- SMA 50: {sma_50}
- Bollinger Bands: Upper {bollinger_upper} | Lower {bollinger_lower}

=== FUNDAMENTALS ===
- Market Cap: {market_cap}
- P/E Ratio: {pe_ratio}
- EPS: {eps}
- Sector: {sector}
- 52-Week Range: {52w_low} - {52w_high}

=== NEWS & SENTIMENT ===
{news_summary}

Write a structured, readable research report with:
1. Executive Overview (Current price and overall technical & fundamental setup)
2. Technical Momentum (RSI interpretation, MACD momentum, moving average trends)
3. Fundamental Valuation (P/E, profitability, market position)
4. Catalysts & Sentiment (News drivers and market sentiment)
5. Actionable Outlook & Key Levels

Use markdown bold for key numbers and levels. Keep it punchy, professional, and accessible."""


def build_synthesis_prompt(state: dict) -> str:
    """Construct synthesis prompt from current state (Rule 1 & Rule 3)."""
    ticker = state.get("ticker", "AAPL")
    query = state.get("query", "")
    ind = state.get("indicators", {})
    fund = state.get("fundamentals", {})
    news_items = state.get("news", [])
    news_text = "\n".join(
        f"- {n.get('title')} (Sentiment: {n.get('sentiment')})"
        for n in news_items
    ) if news_items else "No breaking news recorded."
    return SYNTHESIS_PROMPT.format(
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
        news_summary=news_text,
        **{"52w_low": fund.get("52w_low", "N/A"), "52w_high": fund.get("52w_high", "N/A")},
    )


def build_fallback_summary(ticker: str, ind: dict, fund: dict) -> str:
    """Produce structured markdown report when LLM is unavailable."""
    price = ind.get("price", "$0.00")
    signal = ind.get("signal", "Neutral")
    rsi = ind.get("rsi", "50.0")
    macd = ind.get("macd", "0.00")
    sma_20 = ind.get("sma_20", "N/A")
    sma_50 = ind.get("sma_50", "N/A")
    mcap = fund.get("market_cap", "N/A")
    pe = fund.get("pe_ratio", "N/A")
    eps = fund.get("eps", "N/A")
    sector = fund.get("sector", "General")
    b_low = ind.get("bollinger_lower", "N/A")
    b_high = ind.get("bollinger_upper", "N/A")

    return (
        f"**{ticker}** is currently trading at **{price}**, reflecting a **{signal}** technical posture.\n\n"
        f"**Technical Momentum**: The RSI stands at **{rsi}**, indicating balanced momentum. "
        f"MACD is at **{macd}** with the 20-day SMA at {sma_20} and 50-day SMA at {sma_50}.\n\n"
        f"**Fundamental Valuation**: Market capitalization is **{mcap}** with a trailing P/E of **{pe}** "
        f"and EPS of {eps} in the {sector} sector.\n\n"
        f"**Outlook**: Watch key Bollinger levels between {b_low} and {b_high} for directional confirmation."
    )
