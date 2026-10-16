"""
agent/config.py — Central config loader.
Reads all values from .env and exposes typed constants.
Every module imports from here — never calls os.getenv() directly.
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (one level up from this file)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# ── Alpha Vantage ─────────────────────────────────────────────────
ALPHA_VANTAGE_KEY: str  = os.getenv("ALPHA_VANTAGE_API_KEY", "")
ALPHA_VANTAGE_BASE: str = "https://www.alphavantage.co/query"

# ── LLM ──────────────────────────────────────────────────────────
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "google")      # google | openai
LLM_MODEL: str    = os.getenv("LLM_MODEL", "gemini-3.8-flash")
OPENAI_KEY: str   = os.getenv("OPENAI_API_KEY", "")
GOOGLE_KEY: str   = os.getenv("GOOGLE_API_KEY", "")

# ── Agent ─────────────────────────────────────────────────────────
MAX_ITERATIONS: int = int(os.getenv("MAX_AGENT_ITERATIONS", "10"))
CACHE_TTL: int      = int(os.getenv("CACHE_TTL_SECONDS", "3600"))

# ── Paths ─────────────────────────────────────────────────────────
ROOT_DIR: Path   = Path(__file__).resolve().parent.parent
CACHE_DIR: Path  = ROOT_DIR / "data" / "cache"
CKPT_DIR: Path   = ROOT_DIR / "data" / "checkpoints"

# Ensure data directories exist at import time
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CKPT_DIR.mkdir(parents=True, exist_ok=True)

# ── Logging ──────────────────────────────────────────────────────
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("finagent")


def validate() -> list[str]:
    """
    Check required env vars are set.
    Returns a list of human-readable warning messages (empty = all good).
    """
    warnings = []
    if not ALPHA_VANTAGE_KEY or "your_" in ALPHA_VANTAGE_KEY.lower():
        warnings.append("ALPHA_VANTAGE_API_KEY is not set — data tools will fail.")

    if LLM_PROVIDER == "google":
        if not GOOGLE_KEY or "your_" in GOOGLE_KEY.lower():
            warnings.append("GOOGLE_API_KEY is not set — Gemini LLM reasoning will fail.")
    elif LLM_PROVIDER == "openai":
        if not OPENAI_KEY or "your_" in OPENAI_KEY.lower():
            warnings.append("OPENAI_API_KEY is not set — OpenAI LLM reasoning will fail.")
    else:
        warnings.append(f"Unsupported LLM_PROVIDER '{LLM_PROVIDER}'. Must be 'google' or 'openai'.")

    return warnings
