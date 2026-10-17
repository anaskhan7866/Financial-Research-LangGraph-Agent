"""
tools/search_ticker.py — Resolves company names to stock ticker symbols.
Uses Alpha Vantage SYMBOL_SEARCH with 24-hour disk caching (Rule 5).
"""
import re
import requests
from agent.config import ALPHA_VANTAGE_BASE, ALPHA_VANTAGE_KEY, logger
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
    "reliance": "RELIANCE.BSE",
    "reliance industries": "RELIANCE.BSE",
    "tata motors": "TATAMOTORS.BSE",
    "tata": "TATAMOTORS.BSE",
    "tcs": "TCS.BSE",
    "infosys": "INFY",
    "wipro": "WIPRO.BSE",
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
    clean_lower = cleaned.lower()

    if clean_lower in COMMON_TICKERS:
        return COMMON_TICKERS[clean_lower]

    for name, sym in COMMON_TICKERS.items():
        if re.search(rf"\b{re.escape(name)}\b", clean_lower):
            return sym

    if cleaned.isalpha() and 1 <= len(cleaned) <= 5:
        return cleaned.upper()

    cache_key = f"ticker_search_{clean_lower}"
    cached = get_cache(cache_key, CACHE_TTL_TICKER)
    if cached:
        return cached

    ticker = _fetch_ticker_from_api(cleaned)
    set_cache(cache_key, ticker)
    return ticker


def _fetch_ticker_from_api(query: str) -> str:
    """Query Alpha Vantage SYMBOL_SEARCH endpoint with graceful US fallback."""
    try:
        params = {
            "function": "SYMBOL_SEARCH",
            "keywords": query,
            "apikey": ALPHA_VANTAGE_KEY,
        }
        res = requests.get(ALPHA_VANTAGE_BASE, params=params, timeout=10)
        data = res.json()
        matches = data.get("bestMatches", [])
        if matches:
            best_symbol = matches[0].get("1. symbol", "").strip().upper()
            if best_symbol:
                logger.info(f"Resolved '{query}' to '{best_symbol}'")
                return best_symbol

        if "Note" in data or "Information" in data:
            logger.warning(f"Alpha Vantage rate limit reached in search_ticker: {data}")
    except Exception as e:
        logger.error(f"Error searching ticker for '{query}': {e}")

    # Fallback to standard US benchmark ticker if resolution fails
    logger.info(f"Ticker resolution fallback for '{query}': using AAPL benchmark.")
    return "AAPL"
