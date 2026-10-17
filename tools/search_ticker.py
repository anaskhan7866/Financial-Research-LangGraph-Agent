"""
tools/search_ticker.py — Resolves company names and user queries to ticker symbols.
Optimized for yfinance supporting US and Indian equities (.NS, .BO) (Rule 5).
"""
import re
from agent.config import logger
from tools.cache import get_cache, set_cache

CACHE_TTL_TICKER = 86400  # 24 hours

COMMON_TICKERS = {
    "apple": "AAPL",
    "microsoft": "MSFT",
    "tesla": "TSLA",
    "nvidia": "NVDA",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "amazon": "AMZN",
    "meta": "META",
    "facebook": "META",
    "netflix": "NFLX",
    "reliance": "RELIANCE.NS",
    "reliance industries": "RELIANCE.NS",
    "tata motors": "TATAMOTORS.NS",
    "tata": "TATAMOTORS.NS",
    "tcs": "TCS.NS",
    "infosys": "INFY",
    "wipro": "WIPRO.NS",
    "hdfc": "HDFCBANK.NS",
    "hdfc bank": "HDFCBANK.NS",
    "icici": "ICICIBANK.NS",
    "icici bank": "ICICIBANK.NS",
    "lenskart": "LENS",
    "lenska": "LENS",
    "ibm": "IBM",
}


def search_ticker(query: str) -> str:
    """Find best stock ticker for a given query or company name."""
    raw = (query or "").strip()
    if not raw:
        return "AAPL"

    cleaned = raw.lstrip("$").strip()
    clean_upper = cleaned.upper()
    clean_lower = cleaned.lower()

    # 1. Accept Indian ticker formats (e.g. RELIANCE.NS, TCS.BO, TATAMOTORS.BSE)
    if re.match(r"^[A-Z0-9\-\_]{1,15}\.(NS|BO|BSE)$", clean_upper):
        return clean_upper

    # 2. Standard 1-5 letter US/Global tickers (e.g. AAPL, MSFT, INFY)
    if cleaned.isalpha() and 1 <= len(cleaned) <= 5:
        return clean_upper

    # 3. Direct match in common companies dictionary
    if clean_lower in COMMON_TICKERS:
        return COMMON_TICKERS[clean_lower]

    # 4. Check cache
    cache_key = f"ticker_search_{clean_lower}"
    cached = get_cache(cache_key, CACHE_TTL_TICKER)
    if cached:
        return cached

    # 5. Extract from conversational query or fallback
    ticker = _resolve_company_heuristics(clean_lower)
    set_cache(cache_key, ticker)
    return ticker


def _resolve_company_heuristics(query_lower: str) -> str:
    """Search common mappings or fallback to benchmark ticker."""
    for name, sym in COMMON_TICKERS.items():
        if re.search(rf"\b{re.escape(name)}\b", query_lower):
            logger.info(f"Resolved '{query_lower}' to '{sym}' via keyword heuristic")
            return sym

    # Check if query contains Indian indicators or defaults to US AAPL
    if any(k in query_lower for k in ["india", "nifty", "bse", "nse"]):
        logger.info(f"Fallback for '{query_lower}': using Indian benchmark RELIANCE.NS")
        return "RELIANCE.NS"

    logger.info(f"Fallback for '{query_lower}': using US benchmark AAPL")
    return "AAPL"
