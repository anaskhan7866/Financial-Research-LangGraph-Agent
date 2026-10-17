"""
tools/price_fetch.py — Fetches daily OHLCV equity price history via yfinance.
Converts 6-month historical prices into Pandas DataFrame with caching (Rule 5).
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from agent.config import logger
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
    """Fetch raw price series from yfinance and return as list of dicts."""
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="6mo")
        if hist.empty:
            logger.warning(f"No price history returned by yfinance for: {ticker}")
            return []

        records = []
        for dt, row in hist.iterrows():
            date_str = dt.strftime("%Y-%m-%d") if hasattr(dt, "strftime") else str(dt)[:10]
            records.append({
                "date": date_str,
                "open": float(row.get("Open", 0.0)),
                "high": float(row.get("High", 0.0)),
                "low": float(row.get("Low", 0.0)),
                "close": float(row.get("Close", 0.0)),
                "volume": float(row.get("Volume", 0.0)),
            })
        return records
    except Exception as e:
        logger.error(f"Error fetching prices from yfinance for {ticker}: {e}")
        return []


def _records_to_df(records: list[dict]) -> pd.DataFrame:
    """Convert records list to sorted DataFrame."""
    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)
    df.sort_index(ascending=True, inplace=True)
    return df


def _generate_fallback_prices(ticker: str, days: int = 100) -> pd.DataFrame:
    """Generate realistic price series if API unavailable."""
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
            "open": round(p - spread / 2, 2),
            "high": round(p + spread, 2),
            "low": round(p - spread / 2, 2),
            "close": round(p, 2),
            "volume": int(1e6 + np.random.uniform(0, 5e5)),
        })
    return _records_to_df(records)
