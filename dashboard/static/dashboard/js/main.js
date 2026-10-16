/**
 * dashboard/static/dashboard/js/main.js
 * Handles form submission, agent progress animation, result rendering,
 * sparkline drawing, keyboard shortcuts, and local watchlist management.
 */

// ── DOM References ──────────────────────────────────────────────
const form            = document.getElementById("queryForm");
const tickerInput     = document.getElementById("tickerInput");
const queryInput      = document.getElementById("queryInput");
const runBtn          = document.getElementById("runBtn");
const progressSec     = document.getElementById("progressSection");
const progressTitle   = document.getElementById("progressTitle");
const stepsList       = document.getElementById("stepsList");
const agentSpinner    = document.getElementById("agentSpinner");
const resultsSec      = document.getElementById("resultsSection");
const emptyState      = document.getElementById("emptyState");
const historySec      = document.getElementById("historySection");
const historyList     = document.getElementById("historyList");
const watchlistSec    = document.getElementById("watchlistSection");
const watchlistList   = document.getElementById("watchlistList");
const queryPanel      = document.getElementById("queryPanel");
const clockEl         = document.getElementById("clock");
const sidebar         = document.getElementById("sidebar");
const burgerBtn       = document.getElementById("burgerBtn");
const pinTickerBtn    = document.getElementById("pinTickerBtn");
const sparklineCanvas = document.getElementById("priceSparkline");

let currentActiveTicker = "AAPL";

// ── Live Clock ──────────────────────────────────────────────────
function updateClock() {
  const now = new Date();
  clockEl.textContent = now.toLocaleTimeString("en-US", {
    hour: "2-digit", minute: "2-digit", second: "2-digit"
  });
}
setInterval(updateClock, 1000);
updateClock();

// ── Sidebar toggle (mobile) ─────────────────────────────────────
burgerBtn.addEventListener("click", () => {
  sidebar.classList.toggle("open");
});

// ── Quick prompt chips ──────────────────────────────────────────
document.querySelectorAll(".qp-chip").forEach(chip => {
  chip.addEventListener("click", () => {
    tickerInput.value = chip.dataset.t;
    queryInput.value  = chip.dataset.q;
    queryInput.focus();
  });
});

// ── Keyboard shortcut: Ctrl+Enter / Cmd+Enter ───────────────────
queryInput.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
    e.preventDefault();
    form.dispatchEvent(new Event("submit"));
  }
});

// ── Nav items view switcher ─────────────────────────────────────
document.querySelectorAll(".nav-item").forEach(item => {
  item.addEventListener("click", async (e) => {
    e.preventDefault();
    document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
    item.classList.add("active");

    const view = item.dataset.view;
    if (view === "history") {
      hideEl(queryPanel);
      hideEl(progressSec);
      hideEl(resultsSec);
      hideEl(emptyState);
      hideEl(watchlistSec);
      showEl(historySec);
      await loadHistory();
    } else if (view === "watchlist") {
      hideEl(queryPanel);
      hideEl(progressSec);
      hideEl(resultsSec);
      hideEl(emptyState);
      hideEl(historySec);
      showEl(watchlistSec);
      loadWatchlist();
    } else {
      showEl(queryPanel);
      hideEl(historySec);
      hideEl(watchlistSec);
      if (document.getElementById("resultTicker").textContent.trim() && !resultsSec.classList.contains("hidden")) {
        showEl(resultsSec);
      } else {
        showEl(emptyState);
      }
    }
  });
});

// ── Main Form Submit ────────────────────────────────────────────
form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const ticker = tickerInput.value.trim().toUpperCase() || "AAPL";
  const query  = queryInput.value.trim();

  if (!query) {
    shakeInput(queryInput);
    return;
  }

  await runAgent(ticker, query);
});

// ── Agent Run ───────────────────────────────────────────────────
async function runAgent(ticker, query) {
  hideEl(emptyState);
  hideEl(resultsSec);
  hideEl(historySec);
  hideEl(watchlistSec);
  showEl(progressSec);
  stepsList.innerHTML = "";
  agentSpinner.classList.remove("done");
  progressTitle.textContent = "Agent is thinking…";
  runBtn.disabled = true;

  try {
    const fakeSteps = [
      `Searching ticker for "${ticker}"`,
      "Fetching daily OHLCV price data",
      "Computing RSI, MACD & Bollinger Bands",
      "Fetching latest news & sentiment",
      "Retrieving company fundamentals",
      "Synthesising research report with AI",
    ];

    const fetchPromise = fetch("/analyze/", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ ticker, query }),
    });

    for (let i = 0; i < fakeSteps.length; i++) {
      await delay(400);
      addStep(i + 1, fakeSteps[i], false);
    }

    const res  = await fetchPromise;
    const data = await res.json();

    if (!res.ok) throw new Error(data.error || "Something went wrong.");

    await delay(150);
    markAllStepsDone();
    agentSpinner.classList.add("done");
    progressTitle.textContent = "Research complete ✓";

    await delay(500);
    hideEl(progressSec);
    renderResults(data);
    showEl(resultsSec);

  } catch (err) {
    progressTitle.textContent = `Error: ${err.message}`;
    agentSpinner.style.borderColor = "var(--red)";
    agentSpinner.style.borderTopColor = "var(--red)";
  } finally {
    runBtn.disabled = false;
  }
}

// ── Render Results ──────────────────────────────────────────────
function renderResults(data) {
  currentActiveTicker = data.ticker || "AAPL";
  document.getElementById("resultTicker").textContent = currentActiveTicker;
  document.getElementById("resultPrice").textContent  = data.indicators?.price || "—";

  const signalEl = document.getElementById("resultSignal");
  const signal   = data.indicators?.signal || "Neutral";
  signalEl.textContent = signal;
  signalEl.className   = "result-signal " + signalClass(signal);

  updatePinButton();
  drawSparkline(sparklineCanvas, signal.toLowerCase().includes("bull"));

  // Indicators
  const indGrid = document.getElementById("indicatorsGrid");
  indGrid.innerHTML = "";
  const indicators = {
    "RSI (14)": data.indicators?.rsi,
    "MACD":     data.indicators?.macd,
    "SMA 20":   data.indicators?.sma_20,
    "SMA 50":   data.indicators?.sma_50,
    "Signal":   data.indicators?.signal,
    "Price":    data.indicators?.price,
  };

  for (const [name, value] of Object.entries(indicators)) {
    const cell = document.createElement("div");
    cell.className = "ind-cell";
    cell.innerHTML = `
      <div class="ind-name">${name}</div>
      <div class="ind-value ${valueClass(name, value)}">${value ?? "—"}</div>
    `;
    indGrid.appendChild(cell);
  }

  // Fundamentals
  const fundGrid = document.getElementById("fundamentalsGrid");
  fundGrid.innerHTML = "";
  const fundamentals = {
    "Market Cap": data.fundamentals?.market_cap,
    "P/E Ratio":  data.fundamentals?.pe_ratio,
    "EPS":        data.fundamentals?.eps,
    "Sector":     data.fundamentals?.sector,
    "52W High":   data.fundamentals?.["52w_high"],
    "52W Low":    data.fundamentals?.["52w_low"],
  };

  for (const [key, val] of Object.entries(fundamentals)) {
    const row = document.createElement("div");
    row.className = "fund-row";
    row.innerHTML = `
      <span class="fund-key">${key}</span>
      <span class="fund-val">${val ?? "—"}</span>
    `;
    fundGrid.appendChild(row);
  }

  // News
  const newsList = document.getElementById("newsList");
  newsList.innerHTML = "";
  (data.news || []).forEach(item => {
    const el = document.createElement("div");
    el.className = "news-item";
    el.innerHTML = `
      <span class="news-title">${item.title}</span>
      <span class="sentiment-badge ${sentimentClass(item.sentiment)}">${item.sentiment}</span>
    `;
    newsList.appendChild(el);
  });

  // Summary
  const summaryEl = document.getElementById("summaryText");
  summaryEl.innerHTML = markdownBold(data.summary || "No summary available.");
}

// ── Sparkline Drawing ───────────────────────────────────────────
function drawSparkline(canvas, isBullish) {
  if (!canvas || !canvas.getContext) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;

  ctx.clearRect(0, 0, w, h);
  ctx.beginPath();

  const color = isBullish ? "#22c55e" : "#4f87ff";
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.lineCap = "round";

  const points = isBullish
    ? [h * 0.8, h * 0.7, h * 0.75, h * 0.5, h * 0.55, h * 0.3, h * 0.2]
    : [h * 0.3, h * 0.4, h * 0.35, h * 0.6, h * 0.5, h * 0.7, h * 0.8];

  const step = w / (points.length - 1);
  ctx.moveTo(0, points[0]);
  for (let i = 1; i < points.length; i++) {
    ctx.lineTo(i * step, points[i]);
  }
  ctx.stroke();
}

// ── Watchlist Management ────────────────────────────────────────
function getWatchlist() {
  try {
    return JSON.parse(localStorage.getItem("finagent_watchlist") || "[]");
  } catch {
    return [];
  }
}

function saveWatchlist(list) {
  localStorage.setItem("finagent_watchlist", JSON.stringify(list));
}

function updatePinButton() {
  const list = getWatchlist();
  const isPinned = list.includes(currentActiveTicker);
  pinTickerBtn.textContent = isPinned ? "★ Pinned" : "☆ Pin";
  pinTickerBtn.style.color = isPinned ? "var(--amber)" : "var(--text2)";
}

pinTickerBtn.addEventListener("click", () => {
  let list = getWatchlist();
  if (list.includes(currentActiveTicker)) {
    list = list.filter(t => t !== currentActiveTicker);
  } else {
    list.push(currentActiveTicker);
  }
  saveWatchlist(list);
  updatePinButton();
});

function loadWatchlist() {
  const list = getWatchlist();
  if (list.length === 0) {
    watchlistList.innerHTML = "<p class='watchlist-empty'>Your watchlist is empty. Pin stocks using the '☆ Pin' button on any report!</p>";
    return;
  }

  watchlistList.innerHTML = "";
  list.forEach(ticker => {
    const card = document.createElement("div");
    card.className = "watchlist-card";
    card.innerHTML = `
      <div class="watchlist-card-header">
        <span class="watchlist-ticker">$${ticker}</span>
        <button class="btn-ghost btn-sm remove-pin-btn" title="Remove">✕</button>
      </div>
      <button class="btn-ghost btn-sm run-wl-btn">Research ${ticker}</button>
    `;

    card.querySelector(".remove-pin-btn").addEventListener("click", () => {
      saveWatchlist(getWatchlist().filter(t => t !== ticker));
      loadWatchlist();
    });

    card.querySelector(".run-wl-btn").addEventListener("click", () => {
      tickerInput.value = ticker;
      queryInput.value = `Give me a full technical and fundamental analysis for ${ticker}`;
      hideEl(watchlistSec);
      showEl(queryPanel);
      document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
      document.querySelector('[data-view="research"]')?.classList.add("active");
      form.dispatchEvent(new Event("submit"));
    });

    watchlistList.appendChild(card);
  });
}

// ── History Management ──────────────────────────────────────────
async function loadHistory() {
  historyList.innerHTML = "<p class='history-loading'>Loading past research sessions...</p>";
  try {
    const res = await fetch("/history/");
    const data = await res.json();
    const items = data.history || [];

    if (items.length === 0) {
      historyList.innerHTML = "<p class='history-empty'>No past research sessions yet. Run an analysis above!</p>";
      return;
    }

    historyList.innerHTML = "";
    items.forEach(session => {
      const card = document.createElement("div");
      card.className = "history-card";
      card.innerHTML = `
        <div class="history-card-header">
          <span class="history-ticker">$${session.ticker}</span>
          <span class="history-date">${session.created_at}</span>
        </div>
        <p class="history-query">"${session.query}"</p>
        <button class="btn-ghost btn-sm history-btn">View Report</button>
      `;
      card.querySelector(".history-btn").addEventListener("click", () => {
        hideEl(historySec);
        showEl(queryPanel);
        renderResults(session);
        showEl(resultsSec);
        document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
        document.querySelector('[data-view="research"]')?.classList.add("active");
      });
      historyList.appendChild(card);
    });
  } catch (err) {
    historyList.innerHTML = `<p class='history-empty'>Failed to load history: ${err.message}</p>`;
  }
}

// ── Copy report ─────────────────────────────────────────────────
document.getElementById("copyBtn").addEventListener("click", () => {
  const text = document.getElementById("summaryText").textContent;
  navigator.clipboard.writeText(text).then(() => {
    const btn = document.getElementById("copyBtn");
    btn.textContent = "✓ Copied!";
    setTimeout(() => {
      btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>Copy Report`;
    }, 2000);
  });
});

// ── New Query button ────────────────────────────────────────────
document.getElementById("newQueryBtn").addEventListener("click", () => {
  hideEl(resultsSec);
  showEl(emptyState);
  queryInput.value  = "";
  tickerInput.value = "";
  queryInput.focus();
});

// ── Helpers ─────────────────────────────────────────────────────
function showEl(el) { if (el) el.classList.remove("hidden"); }
function hideEl(el) { if (el) el.classList.add("hidden"); }
function delay(ms)  { return new Promise(r => setTimeout(r, ms)); }

function addStep(num, text, done = false) {
  const li = document.createElement("li");
  li.className = `step-item${done ? " done" : ""}`;
  li.innerHTML = `<span class="step-num">${done ? "" : num}</span>${text}`;
  stepsList.appendChild(li);
}

function markAllStepsDone() {
  document.querySelectorAll(".step-item").forEach(item => {
    item.classList.add("done");
    item.querySelector(".step-num").textContent = "";
  });
}

function shakeInput(el) {
  el.style.animation = "none";
  el.offsetHeight; // reflow
  el.style.animation = "shake 0.4s ease";
  setTimeout(() => (el.style.animation = ""), 400);
}

function signalClass(signal = "") {
  const s = signal.toLowerCase();
  if (s.includes("bull") || s.includes("buy"))  return "bullish";
  if (s.includes("bear") || s.includes("sell")) return "bearish";
  return "";
}

function sentimentClass(sentiment = "") {
  const map = {
    "very positive": "very-positive",
    "positive":      "positive",
    "neutral":       "neutral",
    "negative":      "negative",
    "very negative": "negative",
  };
  return map[sentiment.toLowerCase()] || "neutral";
}

function valueClass(name, value) {
  if (!value || isNaN(parseFloat(value))) return "";
  const n = parseFloat(value);
  if (name === "RSI (14)") {
    if (n > 70) return "bearish";
    if (n < 30) return "bullish";
  }
  if (name === "MACD") return n > 0 ? "bullish" : "bearish";
  return "";
}

function markdownBold(text) {
  return text.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
}

// ── Shake animation ─────────────────────────────────────────────
const style = document.createElement("style");
style.textContent = `
  @keyframes shake {
    0%, 100% { transform: translateX(0); }
    20%, 60%  { transform: translateX(-6px); }
    40%, 80%  { transform: translateX(6px); }
  }
`;
document.head.appendChild(style);
