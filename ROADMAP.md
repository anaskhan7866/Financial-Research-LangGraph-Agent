# 🗺️ BUILD ROADMAP — Autonomous Financial Research Agent
### Complete step-by-step guide from start to finish

> **How to use**: Work top to bottom. Tick each checkbox as you complete it.  
> Check `RULES.md` before every change. Check `ARCHITECTURE.md` before every new file.

---

## 📊 Overall Progress

| Phase | Name                          | Status      |
|-------|-------------------------------|-------------|
| 0     | Project Foundation            | ✅ Done      |
| 1     | Django UI                     | ✅ Done      |
| 2     | Environment & Config          | 🔲 Next      |
| 3     | Data Tools (Alpha Vantage)    | 🔲 Pending   |
| 4     | Technical Indicators          | 🔲 Pending   |
| 5     | LangGraph Agent Core          | 🔲 Pending   |
| 6     | Wire Agent into Django        | 🔲 Pending   |
| 7     | Persistent Memory & History   | 🔲 Pending   |
| 8     | Testing                       | 🔲 Pending   |
| 9     | Polish & Final Touches        | 🔲 Pending   |

---

## ✅ PHASE 0 — Project Foundation *(Already Done)*

- [x] Created `ARCHITECTURE.md` — full project blueprint
- [x] Created `RULES.md` — 10 dev rules + pre-change checklist
- [x] Created Python virtual environment (`venv/`)
- [x] Installed all dependencies via `requirements.txt`
- [x] Scaffolded Django project (`core/`) and app (`dashboard/`)
- [x] Created project folder structure:
  ```
  agent/   tools/   data/cache/   data/checkpoints/
  ```

---

## ✅ PHASE 1 — Django UI *(Already Done)*

- [x] `core/settings.py` — Django config with dotenv, static files
- [x] `core/urls.py` — root URL router
- [x] `dashboard/urls.py` — app URL patterns
- [x] `dashboard/views.py` — index + `/analyze/` + `/history/` views
  - Mock response that mirrors real agent output shape
- [x] `dashboard/templates/dashboard/index.html` — full dashboard HTML
  - Sidebar, topbar, query panel, progress steps, results cards
- [x] `dashboard/static/dashboard/css/main.css` — premium dark UI
  - Glassmorphism, CSS variables, animations, responsive layout
- [x] `dashboard/static/dashboard/js/main.js` — agent flow JS
  - Animated steps, result rendering, copy button, live clock
- [x] Server running at `http://127.0.0.1:8000`

---

## 🔲 PHASE 2 — Environment & Config Setup *(Do This First)*

> **Goal**: Make secrets, API keys, and settings safely available to all modules.

### Steps:

- [ ] **2.1** Copy `.env.example` → `.env` and fill in your real API keys:
  ```bash
  ALPHA_VANTAGE_API_KEY=your_key   # get free at alphavantage.co
  OPENAI_API_KEY=your_key          # or GOOGLE_API_KEY for Gemini
  DJANGO_SECRET_KEY=generate_one
  ```

- [ ] **2.2** Create `agent/__init__.py` — empty init file

- [ ] **2.3** Create `agent/config.py` — central config loader:
  ```python
  # Reads from .env, exposes typed constants
  ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
  LLM_PROVIDER      = os.getenv("LLM_PROVIDER", "openai")
  MAX_ITERATIONS    = int(os.getenv("MAX_AGENT_ITERATIONS", 10))
  CACHE_TTL         = int(os.getenv("CACHE_TTL_SECONDS", 3600))
  ```

- [ ] **2.4** Create `tools/__init__.py` — empty init file

- [ ] **2.5** Create `.gitignore`:
  ```
  venv/   .env   __pycache__/   *.pyc
  db.sqlite3   staticfiles/   data/cache/
  ```

---

## 🔲 PHASE 3 — Data Tools (Alpha Vantage API)

> **Goal**: Build the 5 agent tools that fetch live financial data.  
> Each tool is one file, one job (Rule 3). All calls are cached (Rule 5).

### 3.1 — Cache Helper
**File**: `tools/cache.py`
- [ ] Write `get_cache(key)` — reads JSON from `data/cache/{key}.json`
- [ ] Write `set_cache(key, data)` — writes JSON with timestamp
- [ ] Write `is_fresh(key)` — checks if cache file is within TTL
- [ ] All 4 API tools will call this before hitting the network

### 3.2 — Ticker Search Tool
**File**: `tools/search_ticker.py`
- [ ] Function: `search_ticker(company_name: str) -> str`
- [ ] Calls Alpha Vantage `SYMBOL_SEARCH` endpoint
- [ ] Returns best-match ticker (e.g. `"Apple Inc"` → `"AAPL"`)
- [ ] Caches result for 24 hours

### 3.3 — Price Fetch Tool
**File**: `tools/price_fetch.py`
- [ ] Function: `get_price_data(ticker: str) -> pd.DataFrame`
- [ ] Calls Alpha Vantage `TIME_SERIES_DAILY` endpoint
- [ ] Converts JSON → Pandas DataFrame: `open, high, low, close, volume`
- [ ] Caches result for 1 hour | Returns last 100 trading days

### 3.4 — News & Sentiment Tool
**File**: `tools/news_fetch.py`
- [ ] Function: `get_news(ticker: str) -> list[dict]`
- [ ] Calls Alpha Vantage `NEWS_SENTIMENT` endpoint
- [ ] Returns: `[{title, url, sentiment_score, sentiment_label}]`
- [ ] Translates raw score → human label:
  - `> 0.35` → `"Very Positive"` | `> 0.15` → `"Positive"`
  - `-0.15 to 0.15` → `"Neutral"` | `< -0.35` → `"Very Negative"`
- [ ] Caches for 30 minutes

### 3.5 — Fundamentals Tool
**File**: `tools/fundamentals.py`
- [ ] Function: `get_fundamentals(ticker: str) -> dict`
- [ ] Calls Alpha Vantage `OVERVIEW` endpoint
- [ ] Returns: `{market_cap, pe_ratio, eps, sector, 52w_high, 52w_low}`
- [ ] Formats numbers nicely: `2940000000000` → `"$2.94T"`
- [ ] Caches for 6 hours (fundamentals change slowly)

---

## 🔲 PHASE 4 — Technical Indicators (Pandas)

> **Goal**: Compute all rolling indicators from the price DataFrame.  
> Pure Python/Pandas — no external API calls needed.

**File**: `tools/indicators.py`

- [ ] **4.1** `compute_sma(df, window) -> float`
  - `df["close"].rolling(window).mean().iloc[-1]`

- [ ] **4.2** `compute_ema(df, window) -> float`
  - `df["close"].ewm(span=window, adjust=False).mean().iloc[-1]`

- [ ] **4.3** `compute_rsi(df, period=14) -> float`
  - Formula: `RSI = 100 - (100 / (1 + avg_gain / avg_loss))`
  - Return latest RSI value as float

- [ ] **4.4** `compute_macd(df) -> dict`
  - MACD line = EMA(12) - EMA(26)
  - Signal line = EMA(9) of MACD
  - Returns: `{macd, signal, histogram}`

- [ ] **4.5** `compute_bollinger(df) -> dict`
  - Middle = SMA(20) | Upper = Middle + 2σ | Lower = Middle - 2σ
  - Returns: `{upper, middle, lower}`

- [ ] **4.6** `compute_all(df) -> dict`
  - Calls all above functions, returns full indicator dict
  - This is the only function the agent will call

---

## 🔲 PHASE 5 — LangGraph Agent Core

> **Goal**: Build the stateful ReAct loop that orchestrates all tools.  
> This is the brain of the entire project.

### 5.1 — Agent State
**File**: `agent/state.py`
- [ ] Define `AgentState(TypedDict)`:
  ```python
  query:        str
  messages:     list
  ticker:       str
  price_data:   dict
  indicators:   dict
  news:         list
  fundamentals: dict
  tool_calls:   list
  iterations:   int
  final_answer: str
  error:        str | None
  ```

### 5.2 — Prompts
**File**: `agent/prompts.py`
- [ ] `SYSTEM_PROMPT` — tells the LLM it is a financial research analyst
- [ ] `TOOL_DESCRIPTIONS` — describes each tool in plain English for the LLM
- [ ] `SUMMARY_PROMPT` — template for generating the final report

### 5.3 — Agent Nodes
**File**: `agent/nodes.py`

- [ ] **`reason_node(state)`**
  - Sends current state + messages to LLM
  - LLM decides: call a tool OR write final answer
  - Returns: `{messages: updated, iterations: +1}`

- [ ] **`act_node(state)`**
  - Reads LLM's tool-call decision
  - Routes to the correct tool function
  - Wraps in `try/except` — errors go to `state["error"]`
  - Returns: updated state field (`price_data`, `news`, etc.)

- [ ] **`observe_node(state)`**
  - Formats tool result into a readable observation message
  - Appends to `messages`
  - Returns: `{messages: updated}`

- [ ] **`format_answer_node(state)`**
  - Calls LLM one final time with all collected data
  - Generates markdown research report
  - Returns: `{final_answer: str}`

- [ ] **`handle_error_node(state)`**
  - Formats error into a user-friendly message
  - Returns: `{final_answer: error_message}`

### 5.4 — Router
**File**: `agent/router.py`
- [ ] `route(state) -> str` — conditional edge function:
  - Returns `"act"` if LLM chose a tool
  - Returns `"done"` if answer is ready
  - Returns `"done"` if `iterations >= MAX_ITERATIONS`
  - Returns `"error"` if `state["error"]` is set

### 5.5 — Graph Assembly
**File**: `agent/graph.py`
- [ ] Create `StateGraph(AgentState)`
- [ ] Add nodes: `reason`, `act`, `observe`, `format_answer`, `handle_error`
- [ ] Wire edges:
  ```
  START         → reason
  reason        → [router] → act | format_answer | handle_error
  act           → observe
  observe       → reason   (loop back)
  format_answer → END
  handle_error  → END
  ```
- [ ] Compile: `graph = builder.compile()`
- [ ] Export: `run_agent(query, ticker) -> dict`

---

## 🔲 PHASE 6 — Wire Agent into Django

> **Goal**: Replace the mock response with the real LangGraph agent.

**File**: `dashboard/views.py`

- [ ] **6.1** Import: `from agent.graph import run_agent`
- [ ] **6.2** Replace `_mock_agent_response()` with:
  ```python
  response = run_agent(query=query, ticker=ticker)
  ```
- [ ] **6.3** Add 30-second timeout guard using `threading` or `asyncio`
- [ ] **6.4** Test end-to-end: query UI → real Alpha Vantage data → real report

---

## 🔲 PHASE 7 — Persistent Memory & History

> **Goal**: Save every research session and display history in the sidebar.

### 7.1 — Django Model
**File**: `dashboard/models.py`
- [ ] `ResearchSession` model:
  ```python
  ticker, query, summary, indicators_json,
  fundamentals_json, news_json, created_at
  ```
- [ ] Run: `python manage.py makemigrations && python manage.py migrate`

### 7.2 — Save sessions
**File**: `dashboard/views.py`
- [ ] Save `ResearchSession` after every agent run
- [ ] Keep last 50 sessions — delete older ones automatically

### 7.3 — History API
**File**: `dashboard/views.py`
- [ ] Update `history()` to return last 10 sessions from DB
- [ ] Response: `[{ticker, query, summary, created_at}]`

### 7.4 — History UI
**File**: `dashboard/static/dashboard/js/main.js`
- [ ] On sidebar "History" click → fetch `/history/` → render list
- [ ] Click any history item → re-populate results section

---

## 🔲 PHASE 8 — Testing

> **Goal**: Verify every tool and agent node works correctly.

### 8.1 — Tool Tests
**File**: `tests/test_tools.py`
- [ ] `test_search_ticker()` — mock HTTP, check ticker output
- [ ] `test_get_price_data()` — mock API, check DataFrame shape
- [ ] `test_get_news()` — mock API, check sentiment translation
- [ ] `test_get_fundamentals()` — mock API, check number formatting
- All tests use `unittest.mock.patch` — no real API calls

### 8.2 — Indicator Tests
**File**: `tests/test_indicators.py`
- [ ] `test_compute_rsi()` — known data in, expected RSI out
- [ ] `test_compute_macd()` — check MACD & signal values
- [ ] `test_compute_bollinger()` — check upper/lower band math
- [ ] `test_compute_all()` — check full output dict has correct keys

### 8.3 — Agent Tests
**File**: `tests/test_agent.py`
- [ ] `test_reason_node()` — mock LLM, check state update
- [ ] `test_router()` — all 3 routing scenarios
- [ ] `test_full_run()` — mock everything, run full graph, check answer

### 8.4 — Run All Tests
```bash
.\venv\Scripts\activate
pytest tests/ -v
```

---

## 🔲 PHASE 9 — Polish & Final Touches

> **Goal**: Make the app production-ready and polished for real users.

### 9.1 — UI Enhancements
- [ ] Add **price sparkline chart** in the result header (HTML canvas)
- [ ] Add **skeleton loaders** while results are loading
- [ ] Add **keyboard shortcut** `Ctrl+Enter` to submit the query
- [ ] Show **rate limit warning** banner when near 25 req/day limit
- [ ] Add **watchlist** feature — save/pin tickers to localStorage

### 9.2 — README
**File**: `README.md`
- [ ] Project description + screenshot
- [ ] Step-by-step setup guide (clone → venv → .env → runserver)
- [ ] Feature list
- [ ] API key setup guide with links

### 9.3 — Error Handling Review
- [ ] Invalid ticker → `"Couldn't find XYZXYZ. Try the full company name."`
- [ ] Missing API key → `"Alpha Vantage key not set. See .env.example"`
- [ ] Network error → show cached data with `"Showing cached data"` label

### 9.4 — Performance
- [ ] Add response caching for `/analyze/` endpoint (same ticker+query)
- [ ] Add `gunicorn` to requirements for production
- [ ] Compress and minify CSS/JS for production

### 9.5 — Final Checklist Before Calling it Done
- [ ] Every tool in `tools/` has a matching test
- [ ] No hardcoded secrets anywhere in the codebase
- [ ] All functions are under 40 lines (Rule 1)
- [ ] `.env` is listed in `.gitignore`
- [ ] UI shows human-readable text everywhere — no raw JSON visible
- [ ] `README.md` is complete and accurate

---

## 🏁 Definition of Done

The project is **complete** when all of these are true:

```
✅ User types a company name or ticker → real live data is fetched
✅ RSI, MACD, SMA, EMA, Bollinger Bands computed with Pandas
✅ News sentiment fetched and translated to plain English
✅ Company fundamentals shown in formatted, readable numbers
✅ LangGraph ReAct loop orchestrates all steps with persistent state
✅ Full AI research report rendered in human-readable markdown
✅ Every session saved to database and viewable in history
✅ All tests passing
✅ No raw JSON shown to the user anywhere in the UI
```

---

## 📅 Suggested Build Order (Day by Day)

| Day | Phase | Work                                      |
|-----|-------|-------------------------------------------|
| 1   | 2     | `.env` setup, `config.py`, `.gitignore`   |
| 2   | 3     | Cache helper + Ticker Search + Price Fetch|
| 3   | 3     | News + Fundamentals tools                 |
| 4   | 4     | All 5 indicator functions                 |
| 5   | 5.1–3 | Agent state + prompts + nodes             |
| 6   | 5.4–5 | Router + graph assembly + compile         |
| 7   | 6     | Wire agent into Django, end-to-end test   |
| 8   | 7     | Models, history API, history UI           |
| 9   | 8     | Write and run all tests                   |
| 10  | 9     | Polish, README, final review              |

---

*Last updated: 2026-10-16 | Current phase: **2 — Environment & Config***
