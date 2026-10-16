"""
tools/cache.py — Simple, persistent disk cache for API responses.
Prevents duplicate Alpha Vantage API calls and respects rate limits (Rule 5).
"""
import json
import time
from pathlib import Path
from agent.config import CACHE_DIR, CACHE_TTL, logger


def _get_cache_path(key: str) -> Path:
    """Sanitize cache key and return path."""
    safe_key = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in key.lower())
    return CACHE_DIR / f"{safe_key}.json"


def is_fresh(key: str, ttl_seconds: int = CACHE_TTL) -> bool:
    """Check if cache file exists and has not expired."""
    path = _get_cache_path(key)
    if not path.exists():
        return False
    try:
        age = time.time() - path.stat().st_mtime
        return age < ttl_seconds
    except OSError:
        return False


def get_cache(key: str, ttl_seconds: int = CACHE_TTL):
    """
    Retrieve cached data if fresh. Returns None if missing or expired.
    """
    if not is_fresh(key, ttl_seconds):
        return None
    path = _get_cache_path(key)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            logger.debug(f"Cache HIT for key '{key}'")
            return data
    except Exception as e:
        logger.warning(f"Failed to read cache for '{key}': {e}")
        return None


def set_cache(key: str, data) -> bool:
    """
    Save JSON-serializable data to disk cache.
    Returns True if successful, False otherwise.
    """
    path = _get_cache_path(key)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.debug(f"Cache SET for key '{key}'")
        return True
    except Exception as e:
        logger.warning(f"Failed to write cache for '{key}': {e}")
        return False
