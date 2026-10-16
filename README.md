# 🚀 FinAgent — Autonomous Financial Research Agent

An autonomous, stateful **ReAct (Reasoning and Acting)** financial research agent engineered with **LangGraph**, **Google Gemini (`gemini-3.8-flash`)**, and **Django**. It gathers live equity market feeds from Alpha Vantage, calculates rolling technical indicators with Pandas, and synthesizes institutional-grade investment reports autonomously through persistent state cycles.

---

## 🌟 Features

- **🤖 LangGraph ReAct Architecture**: Multi-step stateful reasoning graph that orchestrates data retrieval, mathematical computations, and report synthesis.
- **⚡ Google Gemini Integration**: Powered by `gemini-3.8-flash` via `langchain-google-genai` with automatic retry and graceful fallback mechanisms.
- **📊 Quantitative Technical Indicators**:
  - **RSI (14)**: Relative Strength Index for overbought/oversold momentum detection
  - **MACD**: Moving Average Convergence Divergence (12, 26, 9) with signal line and histogram
  - **Moving Averages**: 20-day and 50-day Simple & Exponential Moving Averages (SMA & EMA)
  - **Bollinger Bands**: 20-day volatility bands with 2.0 standard deviations
  - **Technical Consensus Signal**: Automated Bullish / Bearish / Neutral rating
- **🏢 Fundamental Overview**: Market Capitalization, P/E Ratio, Earnings Per Share (EPS), Sector, and 52-Week High/Low.
- **📰 Sentiment & News Catalyst**: Multi-source market news sentiment analysis scored into human-readable labels.
- **💾 Smart 2-Tier Caching**: Disk-based JSON cache (`data/cache/`) with TTL policies to prevent burning Alpha Vantage API limits.
- **📁 Persistent History & Watchlist**:
  - SQLite database history saving past research sessions
  - LocalStorage-backed Watchlist to pin and monitor favorite tickers
- **💎 Premium Glassmorphism UI**: High-end dark theme dashboard featuring live clock, animated agent step progress, interactive sparkline charts, and quick-prompt chips.

---

## 🏗️ Project Architecture

```
LangGraph Agent/
├── agent/                  # LangGraph core orchestration
│   ├── config.py           # Typed environment and settings loader
│   ├── graph.py            # Compiled StateGraph and run_agent runner
│   ├── llm.py              # LLM factory (Google Gemini 3.8 Flash)
│   ├── nodes.py            # Node execution functions
│   ├── prompts.py          # Financial analyst prompt templates
│   ├── router.py           # Conditional routing and iteration guards
│   └── state.py            # Strongly typed AgentState container
├── core/                   # Django project configuration
│   ├── settings.py         # Settings with static files and DB configuration
│   ├── urls.py             # Root URL routing
│   └── wsgi.py             # WSGI application entrypoint
├── dashboard/              # Web application
│   ├── migrations/         # Database migrations (ResearchSession)
│   ├── models.py           # SQLite persistence models
│   ├── views.py            # API and view controllers
│   ├── templates/          # HTML templates (index.html)
│   └── static/             # CSS & JS assets
│       ├── css/main.css    # Premium glassmorphic styling
│       └── js/main.js      # Frontend controller & UI animations
├── data/
│   ├── cache/              # 1-hour to 24-hour disk cache for API feeds
│   └── checkpoints/        # State checkpoints
├── tools/                  # Single-responsibility data tools
│   ├── cache.py            # Persistent cache read/write helper
│   ├── search_ticker.py    # Symbol search (SYMBOL_SEARCH)
│   ├── price_fetch.py      # Daily OHLCV data to Pandas DataFrame
│   ├── indicators.py       # Technical indicator mathematical engine
│   ├── fundamentals.py     # Company financial metrics (OVERVIEW)
│   └── news_fetch.py       # Market news and sentiment (NEWS_SENTIMENT)
└── tests/                  # Automated test suites across all phases
```

---

## ⚡ Quick Start

### 1. Prerequisites
- Python 3.10+
- Alpha Vantage API key (Free at [alphavantage.co](https://www.alphavantage.co/support/#api-key))
- Google Gemini API key (Free at [ai.google.dev](https://ai.google.dev))

### 2. Environment Configuration
Copy `.env.example` to `.env` and enter your keys:
```env
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
GOOGLE_API_KEY=your_gemini_api_key
LLM_PROVIDER=google
LLM_MODEL=gemini-3.8-flash
```

### 3. Run Database Migrations
```powershell
.\venv\Scripts\python manage.py migrate
```

### 4. Start the Development Server
```powershell
.\venv\Scripts\python manage.py runserver 8000
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser.

---

## 🧪 Running the Test Suite

Run all automated unit, integration, and mock tests:
```powershell
.\venv\Scripts\python -m unittest discover -s tests -p "test_*.py"
```

---

## 🛡️ Engineering Rules & Reliability
This project follows strict engineering standards defined in `RULES.md`:
1. **Readable Code**: All functions are kept under 40 lines.
2. **Humanized UI**: Technical metrics and raw JSON are translated into human-readable labels and formatted currencies.
3. **Graceful Fallbacks**: If Alpha Vantage API rate limits are reached, fallback datasets ensure uninterrupted agent operation and UI rendering.
4. **Zero Hardcoded Secrets**: All keys are strictly loaded via `.env` and shielded by `.gitignore`.
