# 📜 RULES.md — Development Rules & Constraints
## Autonomous Financial Research Agent

> **HOW TO USE**: Before making ANY code change, run through the checklist at the bottom of this file. If any rule is violated, fix the violation first.

---

## 🔴 RULE 1 — Keep Code Short & Simple

| ✅ DO | ❌ DON'T |
|-------|---------|
| Write functions under 30 lines | Write monolithic 200-line functions |
| One function = one job | Combine fetching + parsing + saving in one blob |
| Use descriptive variable names | Use `x`, `tmp`, `data2` as names |
| Break complex logic into helper functions | Nest 5 levels of if-else |

**Enforcement**: If a function exceeds 40 lines, it MUST be split.

---

## 🔴 RULE 2 — Humanize the UI

Every user-facing surface (Streamlit, CLI output, error messages) must feel natural and readable.

### UI Rules:
- **No raw JSON** shown to the user — always format it as readable text or a table
- **Progress messages** must be plain English: `"Fetching Apple stock data..."` not `"Calling TIME_SERIES_DAILY endpoint"`
- **Numbers** must be formatted: `$1,234.56` not `1234.5623`
- **Dates** must be human: `"Oct 15, 2026"` not `"2026-10-15T00:00:00Z"`
- **Errors** must explain what happened AND what the user can do: `"Couldn't find ticker. Try the full company name."` not `"KeyError: 'Global Quote'"`
- **Sentiment scores** must translate to words: `0.85 → "Very Positive"`, `-0.3 → "Slightly Negative"`

---

## 🔴 RULE 3 — One File, One Responsibility

Each Python module must have a single, clear purpose.

| File | Only Does |
|------|-----------|
| `agent/graph.py` | Builds the LangGraph StateGraph |
| `agent/nodes.py` | Defines node functions (reason, act, observe) |
| `agent/state.py` | Defines `AgentState` TypedDict only |
| `tools/price_fetch.py` | Fetches price data from Alpha Vantage only |
| `tools/indicators.py` | Computes technical indicators only |
| `ui/app.py` | Streamlit layout only, no business logic |

**Enforcement**: If a file imports from more than 3 other project modules, consider splitting it.

---

## 🔴 RULE 4 — Never Hardcode Secrets

- All API keys go in `.env` only
- All `.env` values are accessed via `os.getenv()` or `python-dotenv`
- `.env` is NEVER committed to git — always in `.gitignore`
- `.env.example` always exists with placeholder values

```python
# ✅ Correct
import os
api_key = os.getenv("ALPHA_VANTAGE_API_KEY")

# ❌ Wrong
api_key = "ABC123XYZ"
```

---

## 🔴 RULE 5 — Cache All External API Calls

- Every Alpha Vantage call must check the local cache first
- Cache TTL = 1 hour (configurable via `CACHE_TTL_SECONDS` env var)
- Cache key = `f"{endpoint}_{ticker}_{interval}"`
- Cache location = `data/cache/`
- On cache miss → fetch → save to cache → return

**Why**: Free tier = 25 req/day. One bad loop can exhaust the entire daily quota.

---

## 🔴 RULE 6 — Protect the Agent Loop

- `AgentState.iterations` must increment on every loop
- Router node must check: `if state["iterations"] >= MAX_AGENT_ITERATIONS: return "done"`
- Default `MAX_AGENT_ITERATIONS = 10`
- Every tool call must be wrapped in `try/except` — errors go to `state["error"]`, not crash the app

---

## 🔴 RULE 7 — Follow the Architecture

Before adding ANY new file or module:
1. Check `ARCHITECTURE.md` — does this file already exist?
2. Does the new file fit into one of the existing folders (`agent/`, `tools/`, `ui/`, `tests/`)?
3. If adding a new tool, register it in `tools/__init__.py`
4. If adding a new node, wire it in `agent/graph.py`
5. Never put business logic in `ui/app.py`

---

## 🔴 RULE 8 — Write Tests for Every Tool

Every function in `tools/` must have a corresponding test in `tests/`.

```
tools/price_fetch.py    →  tests/test_tools.py::test_get_price_data
tools/indicators.py     →  tests/test_indicators.py::test_compute_rsi
tools/news_fetch.py     →  tests/test_tools.py::test_get_news_sentiment
```

Tests must mock Alpha Vantage API calls — no real network calls in tests.

---

## 🔴 RULE 9 — Consistent Error Handling

All errors follow this pattern:

```python
# ✅ Correct pattern
try:
    result = fetch_data(ticker)
except Exception as e:
    return {"error": f"Could not fetch data for {ticker}: {str(e)}"}
```

- Never use bare `except:` — always `except Exception as e:`
- Always log the error: `logger.error(f"...")`
- Surface a human-friendly message to the user (see Rule 2)

---

## 🔴 RULE 10 — State is the Single Source of Truth

- Data ONLY lives in `AgentState` during a run
- Node functions must return a **partial state dict** — never mutate state directly
- No global variables for runtime data
- If a node needs data, it reads it from `state`, not from a global

```python
# ✅ Correct — return partial state update
def reason_node(state: AgentState) -> dict:
    ...
    return {"messages": updated_messages, "iterations": state["iterations"] + 1}

# ❌ Wrong — mutating global
GLOBAL_DATA = {}
def reason_node(state):
    GLOBAL_DATA["ticker"] = "AAPL"
```

---

## ✅ PRE-CHANGE CHECKLIST

> Run through this BEFORE every code change. If any item is violated, fix it first.

```
□ 1. Does the function I'm writing stay under 40 lines?
□ 2. Is any user-facing text human-readable (no raw JSON, no raw dates)?
□ 3. Is this new code in the correct file per ARCHITECTURE.md?
□ 4. Are there any hardcoded API keys or secrets?
□ 5. Is the Alpha Vantage call going through the cache layer?
□ 6. Is the agent loop iteration counter being incremented?
□ 7. Are all errors caught and stored in state["error"]?
□ 8. Does the new tool/function have a test?
□ 9. Is state mutated correctly (return partial dict, not in-place)?
□ 10. Does the UI show something meaningful to the user at each step?
```

---

## 📏 Quick Reference Limits

| Thing                    | Limit              |
|--------------------------|--------------------|
| Max function length      | 40 lines           |
| Max file length          | 200 lines          |
| Max agent loop iterations| 10 (configurable)  |
| API cache TTL            | 3600 seconds       |
| Max imports per file     | 8 (prefer fewer)   |
| Nesting depth            | 3 levels max       |

---

*These rules exist to keep the project maintainable, human-friendly, and safe. When in doubt, simpler is better.*

*Last updated: 2026-10-16 | Version: 1.0.0*
