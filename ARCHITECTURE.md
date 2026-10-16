# 🏦 Autonomous Financial Research Agent — Architecture Blueprint

> **Purpose**: A ReAct (Reasoning + Acting) stateful agent built with LangGraph that fetches live equity data via Alpha Vantage, computes rolling technical indicators with Pandas, and autonomously answers multi-step financial queries through persistent state cycles.

---

## 📐 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER / CLI / UI                          │
└─────────────────────────────┬───────────────────────────────────┘
                              │  natural language query
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LANGGRAPH AGENT CORE                       │
│                                                                 │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌─────────┐  │
│   │  REASON  │───▶│   ACT    │───▶│ OBSERVE  │───▶│  DONE?  │  │
│   │  (LLM)   │    │ (Tools)  │    │ (Parse)  │    │  Node   │  │
│   └──────────┘    └──────────┘    └──────────┘    └────┬────┘  │
│         ▲                                               │       │
│         └───────────────────────────────────────────────┘       │
│                    Persistent State (AgentState)                │
└─────────────────────────────────────────────────────────────────┘
                              │  structured answer
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     RESPONSE FORMATTER                          │
│           (Markdown report / JSON / CLI output)                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Tech Stack

| Layer            | Technology                          | Role                                  |
|------------------|-------------------------------------|---------------------------------------|
| Agent Framework  | **LangGraph** (StateGraph)          | Stateful ReAct loop, node routing     |
| LLM              | **OpenAI GPT-4o / Gemini Pro**      | Reasoning & tool-call decisions       |
| Data Source      | **Alpha Vantage REST API**          | Live & historical equity OHLCV data   |
| Data Processing  | **Pandas + NumPy**                  | Rolling indicators, data wrangling    |
| HTTP Client      | **httpx / requests**                | Async-ready API calls                 |
| Config           | **python-dotenv**                   | Secrets & env vars                    |
| UI (optional)    | **Streamlit**                       | Human-friendly chat interface         |
| Storage          | **SQLite / JSON file**              | State checkpointing & memory          |
| Testing          | **pytest**                          | Unit & integration tests              |

---

## 📁 Folder Structure

```
LangGraph Agent/
│
├── ARCHITECTURE.md          ← You are here
├── RULES.md                 ← Development rules & constraints
├── .env                     ← API keys (never commit)
├── .env.example             ← Template for env vars
├── requirements.txt         ← Python dependencies
├── README.md                ← Project overview & setup guide
│
├── agent/                   ← Core agent logic
│   ├── __init__.py
│   ├── graph.py             ← LangGraph StateGraph definition
│   ├── state.py             ← AgentState TypedDict
│   ├── nodes.py             ← reason / act / observe / done nodes
│   ├── router.py            ← Conditional edge logic
│   └── prompts.py           ← System & tool-call prompts
│
├── tools/                   ← Agent-callable tools (actions)
│   ├── __init__.py
│   ├── price_fetch.py       ← Alpha Vantage: fetch OHLCV data
│   ├── indicators.py        ← Pandas: SMA, EMA, RSI, MACD, BB
│   ├── news_fetch.py        ← Alpha Vantage: company news & sentiment
│   ├── fundamentals.py      ← Alpha Vantage: overview, EPS, P/E
│   └── search_ticker.py     ← Symbol search / autocomplete
│
├── data/                    ← Runtime data & cache
│   ├── cache/               ← Cached API responses (avoid re-fetching)
│   └── checkpoints/         ← LangGraph state snapshots (SQLite)
│
├── ui/                      ← Optional Streamlit frontend
│   ├── app.py               ← Main Streamlit app
│   ├── components.py        ← Reusable UI widgets
│   └── styles.css           ← Custom CSS theming
│
├── tests/                   ← Test suite
│   ├── test_tools.py
│   ├── test_agent.py
│   └── test_indicators.py
│
└── scripts/                 ← Utility scripts
    └── run_agent.py         ← CLI entry point
```

---

## 🔄 Agent State (`AgentState`)

The entire agent cycle shares one persistent state dict:

```python
class AgentState(TypedDict):
    query:          str           # original user question
    messages:       list          # full conversation / tool call history
    ticker:         str           # resolved stock symbol e.g. "AAPL"
    price_data:     dict          # raw OHLCV DataFrame (serialized)
    indicators:     dict          # computed SMA/EMA/RSI/MACD values
    news:           list          # recent news headlines + sentiment
    fundamentals:   dict          # P/E, EPS, market cap, sector
    tool_calls:     list          # log of every tool invoked
    iterations:     int           # loop counter (prevent infinite cycles)
    final_answer:   str           # formatted markdown research report
    error:          str | None    # last error message if any
```

---

## 🔁 ReAct Graph Flow (LangGraph Nodes)

```
START
  │
  ▼
[reason]  ──── LLM decides: which tool to call next? or done?
  │
  ▼
[act]  ──── Execute the chosen tool (price, indicator, news, etc.)
  │
  ▼
[observe]  ──── Parse tool output, inject result into state
  │
  ▼
[router]  ──── Conditional edge:
                ├── needs more info → back to [reason]
                ├── error occurred  → [handle_error]
                └── done            → [format_answer]
  │
  ▼
[format_answer]  ──── Build final markdown research report
  │
  ▼
END
```

**Max iterations guard**: `iterations >= 10` forces END to prevent runaway loops.

---

## 🛠️ Tools (Agent Actions)

### 1. `get_price_data(ticker, interval, outputsize)`
- **Source**: Alpha Vantage `TIME_SERIES_DAILY` / `TIME_SERIES_INTRADAY`
- **Returns**: Pandas DataFrame with OHLCV columns
- **Cache**: 1-hour TTL to avoid rate limit hits

### 2. `compute_indicators(df, indicators_list)`
- **Source**: Pandas / NumPy (no external API)
- **Indicators**: SMA(20/50/200), EMA(12/26), RSI(14), MACD, Bollinger Bands
- **Returns**: Dict of indicator series + latest values

### 3. `get_news_sentiment(ticker)`
- **Source**: Alpha Vantage `NEWS_SENTIMENT`
- **Returns**: List of `{title, url, sentiment_score, relevance}` dicts

### 4. `get_fundamentals(ticker)`
- **Source**: Alpha Vantage `OVERVIEW`
- **Returns**: Dict of P/E, EPS, market cap, sector, 52-week high/low

### 5. `search_ticker(company_name)`
- **Source**: Alpha Vantage `SYMBOL_SEARCH`
- **Returns**: Best-match ticker symbol

---

## 🔌 Alpha Vantage API Endpoints Used

| Endpoint               | Function              | Rate Limit      |
|------------------------|-----------------------|-----------------|
| `TIME_SERIES_DAILY`    | Daily OHLCV prices    | 25 req/day free |
| `TIME_SERIES_INTRADAY` | Intraday OHLCV        | 25 req/day free |
| `OVERVIEW`             | Company fundamentals  | 25 req/day free |
| `NEWS_SENTIMENT`       | News + sentiment      | 25 req/day free |
| `SYMBOL_SEARCH`        | Ticker lookup         | 25 req/day free |

> **Note**: Free tier = 25 requests/day. Use response caching aggressively.

---

## 📊 Technical Indicators Reference

| Indicator               | Window   | Signal Interpretation             |
|-------------------------|----------|-----------------------------------|
| SMA (Simple MA)         | 20, 50   | Trend direction                   |
| EMA (Exponential MA)    | 12, 26   | Faster trend response             |
| RSI (Relative Strength) | 14       | >70 overbought, <30 oversold      |
| MACD                    | 12,26,9  | Momentum crossovers               |
| Bollinger Bands         | 20, 2σ   | Volatility / breakout signals     |

---

## 🌊 Data Flow Diagram

```
Alpha Vantage API
       │
       ▼
  price_fetch.py ──► raw JSON ──► Pandas DataFrame
       │
       ▼
  indicators.py ──► rolling calculations ──► indicator dict
       │
       ▼
  AgentState (price_data + indicators)
       │
       ▼
  LLM Reasoning Node ──► synthesizes findings ──► final_answer
```

---

## 🔐 Environment Variables (`.env`)

```bash
ALPHA_VANTAGE_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here          # or GOOGLE_API_KEY for Gemini
LLM_PROVIDER=openai                   # openai | google
LLM_MODEL=gpt-4o                      # model name
CACHE_TTL_SECONDS=3600                # 1 hour cache
MAX_AGENT_ITERATIONS=10               # loop guard
LOG_LEVEL=INFO
```

---

## 🚀 Entry Points

| Mode  | Command                        | Description             |
|-------|--------------------------------|-------------------------|
| CLI   | `python scripts/run_agent.py`  | Terminal-based query    |
| UI    | `streamlit run ui/app.py`      | Web chat interface      |
| Test  | `pytest tests/`                | Run full test suite     |

---

## 📌 Key Design Decisions

1. **ReAct over Chain** — ReAct lets the agent pick tools based on partial results, making it adaptive.
2. **Persistent State** — LangGraph's `StateGraph` carries all data between nodes — no repeated API calls.
3. **Response Caching** — All Alpha Vantage calls are cached to disk to respect the 25 req/day free limit.
4. **Short Modules** — Each file does one thing only — easy to debug, test, and swap out.
5. **Humanized UI** — Streamlit shows progress steps and readable summaries, not raw JSON.

---

*Last updated: 2026-10-16 | Version: 1.0.0*
