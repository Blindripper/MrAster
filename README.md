<div align="center">
  <img src="assets/mraster-logo.png" alt="MrAster logo" width="240" />
  <h1>MrAster Trading Bot</h1>
  <p><strong>Full-spectrum futures automation with AI copilots, resilient guardrails, and a dashboard-first UX.</strong></p>
  <p>
    <a href="#-quick-start">Quick start</a>
    ·
    <a href="#-dashboard-experience">Dashboard tour</a>
    ·
    <a href="#-configuration-reference">Configuration</a>
    ·
    <a href="#-ai-mode-explained">AI mode</a>
  </p>
</div>

<p align="center">
  <a href="https://www.python.org/" target="_blank"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python 3.10+" /></a>
  <a href="#-multilingual-dashboard"><img src="https://img.shields.io/badge/Multi--language-8%20Locales-8A2BE2" alt="Multi-language UI" /></a>
  <a href="#-observability--resilience"><img src="https://img.shields.io/badge/Status-Dashboard%20native-FF8C00" alt="Dashboard native" /></a>
  <a href="#-security-notice"><img src="https://img.shields.io/badge/Trading-Handle%20with%20care-E63946" alt="Risk warning" /></a>
</p>

> "Start the backend once, run the show from the browser, and let the copilots fine-tune every position."

<details>
<summary><strong>Table of Contents</strong></summary>

- [✨ Highlights](#-highlights)
  - [AI Copilot Stack](#ai-copilot-stack)
  - [Trading Engine](#trading-engine)
  - [Risk and Order Management](#risk-and-order-management)
  - [Observability & Resilience](#-observability--resilience)
- [🚀 Quick Start](#-quick-start)
- [🖥️ Dashboard Experience](#-dashboard-experience)
- [🌍 Multilingual Dashboard](#-multilingual-dashboard)
- [🤖 AI Mode Explained](#-ai-mode-explained)
  - [Learning Loops & Self-Tuning](#learning-loops--self-tuning)
- [🧭 Architecture Overview](#-architecture-overview)
- [⚙️ Configuration Reference](#-configuration-reference)
- [🔐 Security Notice](#-security-notice)

</details>

## ✨ Highlights

### AI Copilot Stack
- **AITradeAdvisor** weighs dozens of technical, sentiment, and risk factors to deliver TAKE/SKIP calls, size overrides, leverage hints, and natural-language rationale in one JSON response.
- **News Sentinel** (`ASTER_AI_SENTINEL_*`) feeds macro and hype scores into the advisor, vetoing trades when event risk spikes.
- **PostmortemLearning** (see [Learning Loops & Self-Tuning](#learning-loops--self-tuning)) captures qualitative LLM annotations from completed trades and feeds them back as numeric features for future plans.
- **ParameterTuner** continuously recomputes stop-loss/take-profit multipliers and bucket-specific size biases, escalating to structured LLM calls only when a statistically meaningful sample is available.
- **PlaybookManager** synthesises regime playbooks — momentum, mean-reversion, volatility compression — that the advisor injects into every payload to stay aligned with the prevailing market mode.
- **BudgetLearner** keeps OpenAI spend proportional to realised edge, downshifting cost-per-symbol when performance deteriorates.
- **Budget-aware orchestration** with `ASTER_AI_DAILY_BUDGET_USD`, `ASTER_AI_STRICT_BUDGET`, and per-request price cards in the dashboard make the copilot economical to run—while the High and ATT presets intentionally remove the cap for maximum autonomy.

### Trading Engine
- **RSI-driven signals with trend confirmation** configurable via `ASTER_*` environment variables or the dashboard editor.
- **Multi-armed bandit policy (`BanditPolicy`)** blends LinUCB exploration with the optional alpha model (`ml_policy.py`) to decide TAKE/SKIP and size buckets (S/M/L).
- **Market hygiene filters** keep the feed clean: funding and spread guards, wickiness filters, and cached klines/24h tickers smooth out exchange noise.
- **Oracle-aware non-arbitrage guard** clamps the mark/oracle gap using the premium index (per Jez, 2025) and steers entries away from funding traps.

### Risk and Order Management
- **BracketGuard** (`brackets_guard.py`) repairs stop-loss and take-profit orders while respecting both legacy and new bot signatures.
- **FastTP** trims adverse moves with ATR-bound checkpoints and cooldown logic.
- **Equity and exposure caps** (`ASTER_MAX_OPEN_*`, `ASTER_EQUITY_FRACTION`) plus persistent state (`aster_state.json`) ensure continuity across restarts.

### 🛰️ Observability & Resilience
- **Dashboard-native monitoring** covers log streaming, process control, environment editing, AI chat, and analytics cards.
- **HTTP guardrails** via `ASTER_HTTP_RETRIES`, `ASTER_HTTP_BACKOFF`, and `ASTER_HTTP_TIMEOUT` harden network calls.
- **Single dependency pass** — `pip install -r requirements.txt` brings in everything you need.

## 🚀 Quick Start

1. **Install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
2. **Launch the dashboard backend**
   ```bash
   python dashboard_server.py
   # or with uvicorn hot reload
   uvicorn dashboard_server:app --host 0.0.0.0 --port 8000
   ```
3. **Open the web UI** at <http://localhost:8000> and finish the setup from the browser.

> Need headless operation? Export `ASTER_PAPER=true` (optional) and run `python aster_multi_bot.py`. Set `ASTER_RUN_ONCE=true` for a single scan cycle.

## 🖥️ Dashboard Experience

- **One-click bot control**: start, stop, or relaunch the supervised `aster_multi_bot.py` process and inspect PID, uptime, and exit reasons.
- **Live log streaming** with auto-scroll toggles, compact/detailed views, and downloadable snapshots.
- **Risk presets & pro mode**: switch between Standard (Low/Mid/High presets + sliders) and Pro (full `ASTER_*` surface) on demand; High and ATT automatically lift the AI spend cap for uncapped execution.
- **Safe configuration editing** writes to `dashboard_config.json`, validates keys, and syncs changes back into the running bot.
- **Credential vaulting** keeps exchange and OpenAI keys isolated from general config edits.
- **Performance analytics**: PnL charts, trade history, aggregated trade summaries, and market heat-strips update continuously.
- **AI copilots**: review explanations, monitor budget usage, and chat with the advisor directly in the dashboard.
- **Sentinel awareness**: event warnings, budget guards, and AI status surface instantly from the state file.

## 🌍 Multilingual Dashboard

The single-page app ships with eight fully translated locales and instant language switching—no reloads required. Supported languages today:

- English (EN)
- Deutsch / German (DE)
- Español / Spanish (ES)
- Français / French (FR)
- Türkçe / Turkish (TR)
- 한국어 / Korean (KO)
- Русский / Russian (RU)
- 中文（普通话） / Chinese (Mandarin) (ZH)

Language buttons in the header update all UI labels, cards, and helper copy by pulling localized strings from `dashboard_static/app.js`.

## 🤖 AI Mode Explained

When you toggle the dashboard to **AI** (or set `ASTER_MODE=ai` / `ASTER_AI_MODE=true`) and provide `ASTER_OPENAI_API_KEY`, the workflow upgrades itself:

1. **Signal intake** – Momentum, RSI, ATR, spread, funding, and trend context flow into the AI payload alongside bid/ask levels, stop/TP distances, and per-symbol risk limits.
2. **Sentinel context** – `NewsTrendSentinel` caches 24h ticker stats and optional external news to inject hype/event-risk scores and veto flags.
3. **Context enrichment** – `PostmortemLearning`, `ParameterTuner`, and `PlaybookManager` inject their latest feature vectors, regime hints, and bias multipliers before every request. `BudgetLearner` can temporarily downscale AI help for symbols that underperform.
4. **AI decision** – The advisor calls `plan_trade()` for classical signals or `plan_trend_trade()` for discretionary setups, returning JSON with TAKE/SKIP, sizing overrides, leverage hints, and human-readable explanations.
5. **Budget enforcement** – `DailyBudgetTracker` estimates cost, enforces `ASTER_AI_DAILY_BUDGET_USD`, and respects `ASTER_AI_STRICT_BUDGET` before every API call.
6. **Execution & telemetry** – Approved trades inherit AI adjustments and persist rationale, sentinel state, and budget snapshots in `aster_state.json` for dashboard visualization and post-mortems.

> **Learning loop.** The `note_exit` hook updates bandit matrices, the alpha model, and AI learning stores after every closed trade, with state serialized through `to_dict`/`from_dict` so progress survives restarts.

### Learning Loops & Self-Tuning

The AI stack keeps improving as it trades. Four cooperating services share the persistent state stored in `aster_state.json`:

- **PostmortemLearning** translates qualitative LLM trade reviews (e.g., “macro event,” “liquidity gap”) into weighted numeric signals that reappear in future trade payloads, letting the advisor learn from discretionary notes.
- **ParameterTuner** records per-trade features, recomputes local stop/take biases, and periodically asks the LLM for structured JSON overrides once enough evidence accumulates.
- **PlaybookManager** snapshots market breadth, volatility, and sentiment, then refreshes a playbook (“momentum squeeze,” “sideways chop”) that the advisor uses as regime context.
- **BudgetLearner** tracks token spend vs. realised reward for each symbol and throttles costly post-mortems or tuning calls when edge deteriorates.

Every component is transparent inside the dashboard: AI call receipts, current playbook, post-mortem feature weights, and tuning overrides are surfaced in the AI panel so you can audit the loop in real time.

## 🧭 Architecture Overview

```text
├── aster_multi_bot.py      # Signal engine, policy decisions, order routing
├── brackets_guard.py       # Background process for stop/TP repair
├── ml_policy.py            # LinUCB bandit & optional alpha model
├── dashboard_server.py     # FastAPI backend, websocket logs, process control
├── dashboard_static/       # Single-page app with Standard, Pro, AI modes
├── assets/                 # Project media (logo, etc.)
└── requirements.txt        # Python dependencies
```

Run the bot standalone or from the dashboard; policy and state files reload automatically on startup.

## ⚙️ Configuration Reference

All variables can be edited via environment overrides or through the dashboard (`dashboard_config.json`). The tables below capture the most commonly tuned options; the full list lives in `aster_multi_bot.py` and in the UI editor.

<details>
<summary><strong>Core Variables</strong></summary>

| Variable | Default | Description |
| --- | --- | --- |
| `ASTER_API_KEY` / `ASTER_API_SECRET` | empty | API credentials for live trading. |
| `ASTER_EXCHANGE_BASE` | `https://fapi.asterdex.com` | REST endpoint for market and order data (set e.g. to `https://fapi.binance.com` for Binance Futures, or your paper-trading mirror). |
| `ASTER_PAPER` | `false` | Enables the paper-trading adapter. |
| `ASTER_RUN_ONCE` | `false` | Executes exactly one scan cycle. |
| `ASTER_LOGLEVEL` | `INFO` | Logging verbosity (`DEBUG`, `INFO`, ...). |
| `ASTER_MODE` | `standard` | Default dashboard mode (`standard`, `pro`, `ai`). |
| `ASTER_LOOP_SLEEP` | `30` | Pause between scans in seconds. |
| `ASTER_STATE_FILE` | `aster_state.json` | Persistence file for bot and AI state. |
| `ASTER_HTTP_RETRIES` | `2` | Additional HTTP retry attempts. |
| `ASTER_HTTP_BACKOFF` | `0.6` | Base wait time (seconds) between retries. |
| `ASTER_HTTP_TIMEOUT` | `20` | HTTP timeout in seconds. |
| `ASTER_KLINE_CACHE_SEC` | `45` | Lifetime of the kline cache. |

</details>

<details>
<summary><strong>Strategy, Risk, and Positioning</strong></summary>

| Variable | Default | Description |
| --- | --- | --- |
| `ASTER_INTERVAL` / `ASTER_HTF_INTERVAL` | `5m` / `30m` | Timeframes for signals and confirmation. |
| `ASTER_RSI_BUY_MIN` / `ASTER_RSI_SELL_MAX` | `51` / `49`* | RSI bounds for long and short entries. |
| `ASTER_ALLOW_TREND_ALIGN` | `false` | Enforces trend alignment between timeframes. |
| `ASTER_TREND_BIAS` | `with` | Trade with or against the trend. |
| `ASTER_MIN_QUOTE_VOL_USDT` | `150000` | Minimum volume for tradable symbols. |
| `ASTER_SPREAD_BPS_MAX` | `0.0030` | Maximum tolerated bid/ask spread (bps). |
| `ASTER_WICKINESS_MAX` | `0.97` | Filter against overly volatile candles. |
| `ASTER_MIN_EDGE_R` | `0.30` | Minimum edge (in R) required to approve a trade. |
| `ASTER_DEFAULT_NOTIONAL` | `250` | Fallback notional when sizing fails. |
| `ASTER_RISK_PER_TRADE` | `0.007`* | Share of equity per trade. |
| `ASTER_EQUITY_FRACTION` | `0.33` | Maximum equity utilization across open positions. |
| `ASTER_LEVERAGE` | `5` | Default leverage for orders. |
| `ASTER_MAX_OPEN_GLOBAL` | `0` | Global cap on concurrent positions (0 = unlimited, rely on equity guard). |
| `ASTER_MAX_OPEN_PER_SYMBOL` | `1` | Per-symbol position limit (0 = unlimited, netting on exchange). |
| `ASTER_SL_ATR_MULT` / `ASTER_TP_ATR_MULT` | `1.0` / `1.6` | ATR multiples for stop and take-profit. |
| `FAST_TP_ENABLED` | `true` | Enables FastTP partial-profit protection. |
| `FASTTP_MIN_R` | `0.30` | Minimum R gain before FastTP triggers. |
| `FAST_TP_RET1` / `FAST_TP_RET3` | `-0.0010` / `-0.0020` | Pullback thresholds for FastTP. |
| `FASTTP_SNAP_ATR` | `0.25` | ATR distance for the snap mechanism. |
| `FASTTP_COOLDOWN_S` | `15` | Wait time between FastTP checks. |
| `ASTER_FUNDING_FILTER_ENABLED` | `true` | Enables funding limitations. |
| `ASTER_FUNDING_MAX_LONG` / `ASTER_FUNDING_MAX_SHORT` | `0.0010` | Funding caps per direction. |
| `ASTER_NON_ARB_FILTER_ENABLED` | `true` | Activates the mark/oracle clamp derived from Jez (2025) to avoid negative-funding arbitrage. |
| `ASTER_NON_ARB_CLAMP_BPS` | `0.0005` | Width of the clamp applied to the premium (±bps). |
| `ASTER_NON_ARB_EDGE_THRESHOLD` | `0.00005` | Funding edge tolerated before the guard blocks a biased entry. |
| `ASTER_NON_ARB_SKIP_GAP` | `0.0015` | Absolute mark/oracle gap that forces a skip regardless of direction. |

*When launched from the dashboard, values seed to 51/49 RSI and 0.007 risk share. CLI-only launches fall back to 52/48 and 0.006 until overridden or synced via `dashboard_config.json`.*

</details>

<details>
<summary><strong>AI, Automation, and Guardrails</strong></summary>

| Variable | Default | Description |
| --- | --- | --- |
| `ASTER_BANDIT_ENABLED` | `true` | Enables the LinUCB policy. |
| `ASTER_ALPHA_ENABLED` | `true` | Toggles the optional alpha model. |
| `ASTER_ALPHA_THRESHOLD` | `0.55` | Minimum confidence to approve a trade. |
| `ASTER_ALPHA_PROMOTE_DELTA` | `0.15` | Extra confidence required to upsize. |
| `ASTER_HISTORY_MAX` | `250` | Number of historical trades for analytics. |
| `ASTER_OPENAI_API_KEY` | empty | API key for AITradeAdvisor. |
| `ASTER_CHAT_OPENAI_API_KEY` | empty | Optional dashboard chat-only OpenAI key; falls back to `ASTER_OPENAI_API_KEY`. |
| `ASTER_AI_MODEL` | `gpt-4o` | Model ID for AI analysis. |
| `ASTER_AI_DAILY_BUDGET_USD` | `20` | Daily budget limit (USD). Ignored when `ASTER_PRESET_MODE` is `high` or `att`. |
| `ASTER_AI_STRICT_BUDGET` | `true` | Stops AI calls after hitting the budget. |
| `ASTER_AI_MIN_INTERVAL_SECONDS` | `8` | Cooldown before the AI re-evaluates the same symbol. |
| `ASTER_AI_SENTINEL_ENABLED` | `true` | Activates the News Sentinel. |
| `ASTER_AI_SENTINEL_DECAY_MINUTES` | `90` | Lifetime of a news warning. |
| `ASTER_AI_NEWS_ENDPOINT` | empty | External source for breaking news. |
| `ASTER_AI_NEWS_API_KEY` | empty | API token for the sentinel. |
| `ASTER_BRACKETS_QUEUE_FILE` | `brackets_queue.json` | Queue file for guard repairs. |

</details>

<details>
<summary><strong>Persistence Files</strong></summary>

- **`aster_state.json`** – Primary store for open positions, AI telemetry, sentinel state, and dashboard UI preferences. Delete it to force a clean slate when data becomes inconsistent.
- **`dashboard_config.json`** – Mirrors the environment editor. Back it up for multiple presets or remove it to revert to seeded defaults.
- **`brackets_queue.json`** – Maintained by `brackets_guard.py` to reconcile stop/TP orders. Archive then remove if you observe repeated repair attempts.

Stop the backend before editing or deleting these files to avoid partial writes; move them out of the repository if you need a snapshot before a fresh session.

</details>

## 🔐 Security Notice

- Live trading carries significant risk: always trial changes in paper mode first.
- Never commit or expose API keys.
- Even with caching enabled, verify that market and order data remain fresh.
- Calibrate budget and sentinel parameters deliberately to control AI cost and event risk.

Best of luck & happy trading! Contributions and issue reports are always welcome.
