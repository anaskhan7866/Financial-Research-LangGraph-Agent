"""
tools/indicators.py — Computes technical indicators with Pandas.
Pure Python/Pandas mathematical calculations (SMA, EMA, RSI, MACD, Bollinger Bands).
"""
import pandas as pd
from agent.config import logger


def compute_sma(df: pd.DataFrame, window: int = 20) -> float:
    """Compute Simple Moving Average of close price."""
    if df.empty or len(df) < window:
        return float(df["close"].iloc[-1]) if not df.empty else 0.0
    return float(df["close"].rolling(window=window).mean().iloc[-1])


def compute_ema(df: pd.DataFrame, window: int = 20) -> float:
    """Compute Exponential Moving Average of close price."""
    if df.empty or len(df) < window:
        return float(df["close"].iloc[-1]) if not df.empty else 0.0
    return float(df["close"].ewm(span=window, adjust=False).mean().iloc[-1])


def compute_rsi(df: pd.DataFrame, period: int = 14) -> float:
    """Compute Relative Strength Index (RSI 14)."""
    if df.empty or len(df) < period + 1:
        return 50.0

    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    rs = avg_gain.iloc[-1] / (avg_loss.iloc[-1] + 1e-9)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return float(round(rsi, 2))


def compute_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    """Compute MACD, Signal line, and Histogram."""
    if df.empty or len(df) < slow + signal:
        return {"macd": 0.0, "signal": 0.0, "histogram": 0.0}

    ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
    macd_series = ema_fast - ema_slow
    signal_series = macd_series.ewm(span=signal, adjust=False).mean()

    m = float(macd_series.iloc[-1])
    s = float(signal_series.iloc[-1])
    return {
        "macd": round(m, 2),
        "signal": round(s, 2),
        "histogram": round(m - s, 2),
    }


def compute_bollinger(df: pd.DataFrame, window: int = 20, num_std: float = 2.0) -> dict:
    """Compute Upper, Middle, and Lower Bollinger Bands."""
    if df.empty or len(df) < window:
        p = float(df["close"].iloc[-1]) if not df.empty else 0.0
        return {"upper": p, "middle": p, "lower": p}

    middle = df["close"].rolling(window=window).mean().iloc[-1]
    std = df["close"].rolling(window=window).std().iloc[-1]
    return {
        "upper": round(float(middle + (num_std * std)), 2),
        "middle": round(float(middle), 2),
        "lower": round(float(middle - (num_std * std)), 2),
    }


def determine_signal(rsi: float, macd: float, price: float, sma_50: float) -> str:
    """Derive human-readable technical consensus signal."""
    bullish_votes = 0
    bearish_votes = 0

    if rsi < 30:
        bullish_votes += 1  # oversold bounce potential
    elif rsi > 70:
        bearish_votes += 1  # overbought exhaustion

    if macd > 0:
        bullish_votes += 1
    elif macd < 0:
        bearish_votes += 1

    if price > sma_50:
        bullish_votes += 1
    elif price < sma_50:
        bearish_votes += 1

    if bullish_votes >= 2:
        return "Bullish"
    if bearish_votes >= 2:
        return "Bearish"
    return "Neutral"


def compute_all_indicators(df: pd.DataFrame) -> dict:
    """
    Run full technical suite and return formatted dict matching UI schema.
    """
    if df.empty:
        return {
            "rsi": "50.0", "macd": "0.00", "sma_20": "$0.00",
            "sma_50": "$0.00", "price": "$0.00", "signal": "Neutral"
        }

    price = float(df["close"].iloc[-1])
    sma_20 = compute_sma(df, 20)
    sma_50 = compute_sma(df, 50)
    rsi = compute_rsi(df, 14)
    macd_dict = compute_macd(df, 12, 26, 9)
    bb = compute_bollinger(df, 20, 2.0)
    signal = determine_signal(rsi, macd_dict["macd"], price, sma_50)

    return {
        "price": f"${price:.2f}",
        "rsi": f"{rsi:.1f}",
        "macd": f"{macd_dict['macd']:.2f}",
        "sma_20": f"${sma_20:.2f}",
        "sma_50": f"${sma_50:.2f}",
        "bollinger_upper": f"${bb['upper']:.2f}",
        "bollinger_lower": f"${bb['lower']:.2f}",
        "signal": signal,
    }
