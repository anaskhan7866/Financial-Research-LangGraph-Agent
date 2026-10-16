"""
tests/test_phase4_indicators.py — Unit tests for Phase 4 technical indicators.
Verifies SMA, EMA, RSI, MACD, Bollinger Bands, and signal consensus.
"""
import os
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import pandas as pd
import numpy as np
from tools.indicators import (
    compute_sma,
    compute_ema,
    compute_rsi,
    compute_macd,
    compute_bollinger,
    compute_all_indicators,
    determine_signal,
)


class TestIndicators(unittest.TestCase):
    """Test indicator calculation mathematics and robustness."""

    def setUp(self):
        # 60 days of synthetic prices
        dates = pd.date_range("2026-01-01", periods=60)
        prices = [100.0 + i * 0.5 + (i % 3) for i in range(60)]
        self.df = pd.DataFrame({
            "open": prices,
            "high": [p + 1.0 for p in prices],
            "low": [p - 1.0 for p in prices],
            "close": prices,
            "volume": [1000000] * 60,
        }, index=dates)

    def test_sma_calculation(self):
        sma20 = compute_sma(self.df, 20)
        expected = float(self.df["close"].iloc[-20:].mean())
        self.assertAlmostEqual(sma20, expected, places=4)

    def test_ema_calculation(self):
        ema20 = compute_ema(self.df, 20)
        self.assertIsInstance(ema20, float)
        self.assertGreater(ema20, 0)

    def test_rsi_bounds_and_trends(self):
        # Rising price -> High RSI
        rsi = compute_rsi(self.df, 14)
        self.assertTrue(0 <= rsi <= 100)
        self.assertGreater(rsi, 50)

        # Strictly falling prices -> Low RSI
        falling_df = pd.DataFrame({"close": list(range(60, 0, -1))})
        falling_rsi = compute_rsi(falling_df, 14)
        self.assertLess(falling_rsi, 30)

    def test_macd_structure(self):
        macd_data = compute_macd(self.df, 12, 26, 9)
        self.assertIn("macd", macd_data)
        self.assertIn("signal", macd_data)
        self.assertIn("histogram", macd_data)
        self.assertAlmostEqual(
            macd_data["histogram"],
            round(macd_data["macd"] - macd_data["signal"], 2),
            places=2
        )

    def test_bollinger_bands(self):
        bb = compute_bollinger(self.df, 20, 2.0)
        self.assertGreaterEqual(bb["upper"], bb["middle"])
        self.assertGreaterEqual(bb["middle"], bb["lower"])

    def test_determine_signal(self):
        bull = determine_signal(rsi=25.0, macd=1.5, price=150.0, sma_50=140.0)
        self.assertEqual(bull, "Bullish")

        bear = determine_signal(rsi=75.0, macd=-1.5, price=130.0, sma_50=140.0)
        self.assertEqual(bear, "Bearish")

    def test_compute_all_indicators_contract(self):
        result = compute_all_indicators(self.df)
        expected_keys = [
            "price", "rsi", "macd", "sma_20", "sma_50",
            "bollinger_upper", "bollinger_lower", "signal"
        ]
        for key in expected_keys:
            self.assertIn(key, result)

        self.assertIn(result["signal"], ["Bullish", "Bearish", "Neutral"])
        self.assertTrue(result["price"].startswith("$"))

    def test_compute_all_indicators_empty_df_fallback(self):
        empty_df = pd.DataFrame()
        result = compute_all_indicators(empty_df)
        self.assertEqual(result["signal"], "Neutral")
        self.assertEqual(result["price"], "$0.00")


if __name__ == "__main__":
    unittest.main()
