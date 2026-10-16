"""
tools/search_ticker.py — Resolves company names to stock ticker symbols.
Uses Alpha Vantage SYMBOL_SEARCH with 24-hour disk caching (Rule 5).
"""
import requests
from agent.config import ALPHA_VANTAGE_BASE, ALPHA_VANTAGE_KEY, logger
from tools.cache import get_cache, set_cache

CACHE_TTL_TICKER = 86400  # 24 hours


def search_ticker(query: str) -> str:
    """
    Find best stock ticker for a given query or company name.
    Example: 'Apple Inc' -> 'AAPL', 'tesla' -> 'TSLA'.
    """
    cleaned = (query or "").strip()
    if not cleaned:
        return "AAPL"

    # Fast path if already a clean ticker format
    if cleaned.isalpha() and 1 <= len(cleaned) <= 5 and cleaned.isupper():
        return cleaned

    cache_key = f"ticker_search_{cleaned.lower()}"
    cached = get_cache(cache_key, CACHE_TTL_TICKER)
    if cached:
        return cached

    ticker = _fetch_ticker_from_api(cleaned)
    set_cache(cache_key, ticker)
    return ticker


def _fetch_ticker_from_api(query: str) -> str:
    """Query Alpha Vantage SYMBOL_SEARCH endpoint."""
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

        # Check for rate limit or empty response
        if "Note" in data or "Information" in data:
            logger.warning(f"Alpha Vantage rate limit reached in search_ticker: {data}")

    except Exception as e:
        logger.error(f"Error searching ticker for '{query}': {e}")

    # Fallback heuristic: first word uppercase if short, else AAPL
    first_word = query.split()[0].upper()
    return first_word if (first_word.isalpha() and len(first_word) <= 5) else "AAPL"
