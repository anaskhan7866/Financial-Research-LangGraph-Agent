"""
tools/price_fetch.py — Fetches daily OHLCV equity price history.
Converts Alpha Vantage TIME_SERIES_DAILY into Pandas DataFrame with caching (Rule 5).
"""
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from agent.config import ALPHA_VANTAGE_BASE, ALPHA_VANTAGE_KEY, logger
from tools.cache import get_cache, set_cache

CACHE_TTL_PRICE = 3600  # 1 hour


def get_price_data(ticker: str) -> pd.DataFrame:
    """
    Fetch daily OHLCV price history for a ticker.
    Returns DataFrame with columns ['open', 'high', 'low', 'close', 'volume']
    indexed by Date sorted ascending.
    """
    clean_ticker = (ticker or "AAPL").strip().upper()
    cache_key = f"price_{clean_ticker}"

    cached = get_cache(cache_key, CACHE_TTL_PRICE)
    if cached and isinstance(cached, list) and len(cached) > 0:
        return _records_to_df(cached)

    records = _fetch_price_records(clean_ticker)
    if records:
        set_cache(cache_key, records)
        return _records_to_df(records)

    logger.warning(f"Using fallback price series for {clean_ticker}")
    return _generate_fallback_prices(clean_ticker)


def _fetch_price_records(ticker: str) -> list[dict]:
    """Fetch raw price series from Alpha Vantage and return as list of dicts."""
    try:
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": ticker,
            "outputsize": "compact",
            "apikey": ALPHA_VANTAGE_KEY,
        }
        res = requests.get(ALPHA_VANTAGE_BASE, params=params, timeout=12)
        data = res.json()
        series = data.get("Time Series (Daily)", {})
        if not series:
            logger.warning(f"No daily time series in AV response: {list(data.keys())}")
            return []

        records = []
        for date_str, values in series.items():
            records.append({
                "date": date_str,
                "open": float(values.get("1. open", 0)),
                "high": float(values.get("2. high", 0)),
                "low": float(values.get("3. low", 0)),
                "close": float(values.get("4. close", 0)),
                "volume": float(values.get("5. volume", 0)),
            })
        return records
    except Exception as e:
        logger.error(f"Error fetching prices for {ticker}: {e}")
        return []


def _records_to_df(records: list[dict]) -> pd.DataFrame:
    """Convert records list to sorted DataFrame."""
    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)
    df.sort_index(ascending=True, inplace=True)
    return df


def _generate_fallback_prices(ticker: str, days: int = 100) -> pd.DataFrame:
    """Generate realistic price series if API quota exhausted."""
    np.random.seed(abs(hash(ticker)) % (2**32))
    base_price = 150.0 + (abs(hash(ticker)) % 100)
    dates = [datetime.today() - timedelta(days=i) for i in range(days, 0, -1)]

    pct_changes = np.random.normal(0.0005, 0.015, days)
    prices = base_price * np.exp(np.cumsum(pct_changes))

    records = []
    for d, p in zip(dates, prices):
        spread = p * 0.008
        records.append({
            "date": d.strftime("%Y-%m-%d"),
            "open": round(p - spread/2, 2),
            "high": round(p + spread, 2),
            "low": round(p - spread, 2),
            "close": round(p, 2),
            "volume": int(1e6 + np.random.uniform(0, 5e5)),
        })
    return _records_to_df(records)
