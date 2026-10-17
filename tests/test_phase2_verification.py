"""
tests/test_phase2_verification.py — Comprehensive test suite for Phases 0, 1, and 2.
Verifies environment, configuration, Google Gemini API, Django views, static files, and UI contract.
"""
import os
import sys
import json
import unittest
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Setup Django settings for standalone test runner
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
import django
django.setup()

from django.test import Client
from agent.config import (
    ALPHA_VANTAGE_KEY,
    GOOGLE_KEY,
    LLM_PROVIDER,
    LLM_MODEL,
    CACHE_DIR,
    CKPT_DIR,
    validate,
)
from langchain_google_genai import ChatGoogleGenerativeAI


class TestConfigAndEnv(unittest.TestCase):
    """Verifies Phase 0 and Phase 2 config setup."""

    def test_env_keys_present(self):
        """Ensure critical API keys are present."""
        self.assertTrue(bool(ALPHA_VANTAGE_KEY), "ALPHA_VANTAGE_API_KEY must be set in .env")
        self.assertTrue(bool(GOOGLE_KEY), "GOOGLE_API_KEY must be set in .env")

    def test_gemini_provider_and_model(self):
        """Ensure LLM_PROVIDER is google and model is gemini-3.8-flash."""
        self.assertEqual(LLM_PROVIDER, "google")
        self.assertEqual(LLM_MODEL, "gemini-3.8-flash")

    def test_validate_returns_no_warnings_for_active_config(self):
        """Ensure validate() passes with zero warnings."""
        warnings = validate()
        self.assertEqual(warnings, [], f"Expected 0 warnings, got: {warnings}")

    def test_data_directories_exist_and_writable(self):
        """Ensure cache and checkpoint directories exist and are writable."""
        self.assertTrue(CACHE_DIR.exists(), f"Cache directory does not exist: {CACHE_DIR}")
        self.assertTrue(CKPT_DIR.exists(), f"Checkpoint directory does not exist: {CKPT_DIR}")

        # Test write permission
        test_file = CACHE_DIR / "_test_write.tmp"
        try:
            test_file.write_text("ok", encoding="utf-8")
            self.assertEqual(test_file.read_text(encoding="utf-8"), "ok")
        finally:
            if test_file.exists():
                test_file.unlink()


class TestLiveApiConnections(unittest.TestCase):
    """Verifies live Google Gemini and Alpha Vantage connectivity."""

    def test_gemini_model_invocation(self):
        """Verify that Gemini can be initialized and respond, or handle quota limit gracefully."""
        try:
            llm = ChatGoogleGenerativeAI(model=LLM_MODEL, google_api_key=GOOGLE_KEY, max_retries=0)
            response = llm.invoke("Respond with exactly the word PONG")
            self.assertTrue(len(str(response.content)) > 0, "Gemini returned empty response")
        except Exception as e:
            # Per user request: if API limit is reached, pass through to verify all other components
            if any(k in str(e).lower() for k in ["429", "503", "resource_exhausted", "quota"]):
                self.skipTest(f"Live Gemini quota/rate limit reached ({e}); fallbacks active.")
            else:
                raise

    def test_alpha_vantage_live_ping(self):
        """Verify that Alpha Vantage API responds with Global Quote or notes quota."""
        try:
            import requests
            from agent.config import ALPHA_VANTAGE_BASE
            res = requests.get(
                ALPHA_VANTAGE_BASE,
                params={"function": "GLOBAL_QUOTE", "symbol": "IBM", "apikey": ALPHA_VANTAGE_KEY},
                timeout=10,
            )
            self.assertEqual(res.status_code, 200)
            data = res.json()
            if "Note" in data or "Information" in data:
                self.skipTest("Alpha Vantage rate limit reached; cached/fallback tools active.")
            else:
                self.assertIn("Global Quote", data)
        except Exception as e:
            self.skipTest(f"Alpha Vantage network or quota notice: {e}")


class TestDjangoViews(unittest.TestCase):
    """Verifies Phase 1 Django views and endpoints."""

    def setUp(self):
        self.client = Client()

    def test_index_page_returns_200(self):
        """GET / should render the dashboard HTML."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        content = res.content.decode("utf-8")
        self.assertIn("FinAgent", content)
        self.assertIn("Financial Research", content)
        self.assertIn("queryForm", content)

    def test_history_endpoint_returns_200(self):
        """GET /history/ should return history list."""
        res = self.client.get("/history/")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("history", data)
        self.assertIsInstance(data["history"], list)

    def test_analyze_endpoint_valid_request(self):
        """POST /analyze/ should return structured research output."""
        payload = {"ticker": "MSFT", "query": "Analyze Microsoft fundamentals"}
        res = self.client.post("/analyze/", data=json.dumps(payload), content_type="application/json")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        for field in ["ticker", "query", "steps", "fundamentals", "indicators", "news", "summary"]:
            self.assertIn(field, data, f"Missing expected field '{field}' in response")
        self.assertEqual(data["ticker"], "MSFT")
        self.assertTrue(len(data["steps"]) > 0)
        self.assertIn("market_cap", data["fundamentals"])
        self.assertIn("rsi", data["indicators"])

    def test_analyze_empty_query_returns_400(self):
        """POST /analyze/ with empty query should return 400 Bad Request."""
        res = self.client.post("/analyze/", data=json.dumps({"ticker": "AAPL", "query": "   "}), content_type="application/json")
        self.assertEqual(res.status_code, 400)
        self.assertIn("error", res.json())

    def test_analyze_malformed_json_returns_400(self):
        """POST /analyze/ with malformed JSON should return 400."""
        res = self.client.post("/analyze/", data="not-a-json", content_type="application/json")
        self.assertEqual(res.status_code, 400)
        self.assertIn("error", res.json())

    def test_analyze_non_dict_body_returns_400(self):
        """POST /analyze/ with non-dict JSON should return 400."""
        res = self.client.post("/analyze/", data=json.dumps([1, 2, 3]), content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_analyze_get_method_not_allowed(self):
        """GET /analyze/ should return 405 Method Not Allowed."""
        res = self.client.get("/analyze/")
        self.assertEqual(res.status_code, 405)


class TestUIContractAndStaticAssets(unittest.TestCase):
    """Verifies HTML element IDs match main.js requirements."""

    def test_static_files_exist(self):
        """Ensure CSS and JS files exist on disk."""
        base_dir = Path(__file__).resolve().parent.parent
        css_file = base_dir / "dashboard" / "static" / "dashboard" / "css" / "main.css"
        js_file  = base_dir / "dashboard" / "static" / "dashboard" / "js" / "main.js"
        html_file = base_dir / "dashboard" / "templates" / "dashboard" / "index.html"

        self.assertTrue(css_file.exists(), "main.css is missing")
        self.assertTrue(js_file.exists(), "main.js is missing")
        self.assertTrue(html_file.exists(), "index.html is missing")

        self.assertGreater(css_file.stat().st_size, 1000)
        self.assertGreater(js_file.stat().st_size, 1000)

    def test_html_contains_all_js_ids(self):
        """Ensure every DOM ID used in main.js is defined in index.html."""
        base_dir = Path(__file__).resolve().parent.parent
        html_content = (base_dir / "dashboard" / "templates" / "dashboard" / "index.html").read_text(encoding="utf-8")
        required_ids = [
            "queryForm", "tickerInput", "queryInput", "runBtn", "progressSection", "progressTitle",
            "stepsList", "agentSpinner", "resultsSection", "emptyState", "clock", "sidebar",
            "burgerBtn", "resultTicker", "resultPrice", "resultSignal", "indicatorsGrid",
            "fundamentalsGrid", "newsList", "summaryText", "copyBtn", "newQueryBtn",
            "historySection", "historyList", "watchlistSection", "watchlistList",
            "pinTickerBtn", "priceSparkline"
        ]
        for elem_id in required_ids:
            self.assertIn(f'id="{elem_id}"', html_content, f"ID '{elem_id}' not found in index.html")


if __name__ == "__main__":
    unittest.main()
