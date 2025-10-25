# MrAster Trading Bot

MrAster is a full-featured toolkit for futures trading on Binance-compatible exchanges. The current release puts the interactive dashboard at the center of the workflow: start the backend once, control the bot from the browser, and only fall back to the CLI when you need a headless session.

## Table of Contents
- [Highlights](#highlights)
- [Dashboard-First Workflow](#dashboard-first-workflow)
  - [Quick Launch](#quick-launch)
  - [What You Can Do in the Dashboard](#what-you-can-do-in-the-dashboard)
  - [Optional CLI Operation](#optional-cli-operation)
- [Architecture Overview](#architecture-overview)
- [Configuration](#configuration)
  - [Core Variables](#core-variables)
  - [Strategy, Risk, and Positioning](#strategy-risk-and-positioning)
  - [AI, Automation, and Guardrails](#ai-automation-and-guardrails)
- [Security Notice](#security-notice)

## Highlights

### Trading Engine
- **RSI-based signals with trend confirmation** – thresholds and confirmation windows are controlled via `ASTER_*` environment variables or the dashboard editor.
- **Multi-armed bandit (`BanditPolicy`)** using LinUCB and an optional alpha model from `ml_policy.py` decides TAKE/SKIP as well as the size bucket (S/M/L).
- **Funding and spread filters** avoid trades in illiquid or expensive markets, while wickiness guards filter noisy candles.
- **Kline and 24h ticker caching** reduces API calls and shields against temporary exchange outages.

### Risk and Order Management
- **BracketGuard** (`brackets_guard.py`) repairs stop-loss and take-profit orders, respects the `working_type`, and supports both legacy and new bot signatures.
- **FastTP** reacts to adverse returns and trims positions using ATR-bound checkpoints.
- **Equity cache & position limits** (`ASTER_MAX_OPEN_*`, `ASTER_EQUITY_FRACTION`) keep total risk exposure in check.
- **Persistent state** (`aster_state.json`) stores open trades, policy data, and dashboard settings across sessions.

### AI and Automation
- **AITradeAdvisor** (AI mode) evaluates signals, adjusts leverage and position size, and explains decisions in its own activity feed.
- **News Sentinel** (`ASTER_AI_SENTINEL_*`) monitors external news feeds and can block trades around events.
- **Budget control** (`ASTER_AI_DAILY_BUDGET_USD`, `ASTER_AI_STRICT_BUDGET`) halts AI calls when the daily budget is exceeded.

### Observability & Resilience
- **HTTP hardening** configurable via `ASTER_HTTP_RETRIES`, `ASTER_HTTP_BACKOFF`, `ASTER_HTTP_TIMEOUT`.
- **Dashboard-native monitoring** with log streaming, bot process control, environment editing, AI chat, and analytics cards.
- **Self-contained requirements**: `pip install -r requirements.txt` is sufficient to get going.

## Dashboard-First Workflow

### Quick Launch
1. **Install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
2. **Start the dashboard backend**
   ```bash
   python dashboard_server.py
   # or with uvicorn hot reload
   uvicorn dashboard_server:app --host 0.0.0.0 --port 8000
   ```
3. **Open the web UI** at <http://localhost:8000> and finish the setup from the browser.

### What You Can Do in the Dashboard
- **Start, stop, and relaunch the bot** with a single click. The backend supervises the `aster_multi_bot.py` process and surfaces the PID, uptime, and exit reasons.
- **Watch the live logs** in detailed or compact form, toggle auto-scroll, and download the latest snapshot for audits.
- **Tune risk with presets**. Standard mode provides Low/Mid/High presets plus sliders for risk-per-trade and leverage; switching to Pro mode reveals every `ASTER_*` variable.
- **Edit configuration safely**. The environment editor writes to `dashboard_config.json`, validates keys, and syncs changes back into the running bot.
- **Manage credentials**. Dedicated inputs store exchange API keys and OpenAI credentials, isolating them from general config edits.
- **Track trading performance** through the PnL chart, trade history list, and aggregated trade summary.
- **Monitor the market** via the rolling "most traded" ticker strip and active position cards. Positions are refreshed directly from the exchange when credentials are present.
- **Use the AI copilots**. The AI activity feed shows automated decisions, budget consumption is visualized in the budget card, and the in-dashboard chat lets you ask the AI advisor contextual questions.
- **Stay informed**. News Sentinel warnings, budget guard status, and AI mode indicators are surfaced as soon as they update in the state file.

### Optional CLI Operation
You can still run the bot headlessly for cron jobs or servers without browsers:
```bash
export ASTER_PAPER=true        # optional paper trading
python aster_multi_bot.py
```
Set `ASTER_RUN_ONCE=true` to execute a single scan cycle. Use the CLI when the dashboard is unavailable; otherwise, the dashboard remains the recommended control center.

## Architecture Overview

```
├── aster_multi_bot.py      # Main entry point, signals, policy decisions, order routing
├── brackets_guard.py       # Background process for stop/TP repair
├── ml_policy.py            # LinUCB bandit & optional alpha model
├── dashboard_server.py     # FastAPI backend, websocket logs, process control
├── dashboard_static/       # Single-page app with Standard, Pro, and AI modes
└── requirements.txt        # Complete Python dependencies
```

The bot can run standalone or be controlled through the dashboard. Policy and state files are saved automatically and restored on the next startup.

## Configuration

All relevant parameters can be set via environment variables or edited in the dashboard (`dashboard_config.json`). Below is a curated overview. You can inspect the full list anytime through the dashboard editor or at the top of `aster_multi_bot.py`.

### Core Variables

| Variable | Default | Description |
| --- | --- | --- |
| `ASTER_API_KEY` / `ASTER_API_SECRET` | empty | API credentials for live trading. |
| `ASTER_EXCHANGE_BASE` | `https://fapi.asterdex.com` | REST endpoint for market and order data. |
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

### Strategy, Risk, and Positioning

| Variable | Default | Description |
| --- | --- | --- |
| `ASTER_INTERVAL` / `ASTER_HTF_INTERVAL` | `5m` / `30m` | Timeframes for signals and confirmation. |
| `ASTER_RSI_BUY_MIN` / `ASTER_RSI_SELL_MAX` | `52` / `48` | RSI bounds for long and short entries. |
| `ASTER_ALLOW_TREND_ALIGN` | `false` | Enforces trend alignment between timeframes. |
| `ASTER_TREND_BIAS` | `with` | Trade with or against the trend. |
| `ASTER_MIN_QUOTE_VOL_USDT` | `75000` | Minimum volume for tradable symbols. |
| `ASTER_SPREAD_BPS_MAX` | `0.0030` | Maximum tolerated bid/ask spread (bps). |
| `ASTER_WICKINESS_MAX` | `0.97` | Filter against overly volatile candles. |
| `ASTER_MIN_EDGE_R` | `0.30` | Minimum edge (in R) required to approve a trade. |
| `ASTER_DEFAULT_NOTIONAL` | `250` | Fallback notional when sizing fails. |
| `ASTER_RISK_PER_TRADE` | `0.006` | Share of equity per trade. |
| `ASTER_EQUITY_FRACTION` | `0.33` | Maximum equity utilization across open positions. |
| `ASTER_LEVERAGE` | `5` | Default leverage for orders. |
| `ASTER_MAX_OPEN_GLOBAL` | `4` | Global cap on concurrent positions. |
| `ASTER_MAX_OPEN_PER_SYMBOL` | `1` | Per-symbol position limit. |
| `ASTER_SL_ATR_MULT` / `ASTER_TP_ATR_MULT` | `1.0` / `1.6` | ATR multiples for stop and take-profit. |
| `FAST_TP_ENABLED` | `true` | Enables FastTP partial-profit protection. |
| `FASTTP_MIN_R` | `0.30` | Minimum R gain before FastTP triggers. |
| `FAST_TP_RET1` / `FAST_TP_RET3` | `-0.0010` / `-0.0020` | Pullback thresholds for FastTP. |
| `FASTTP_SNAP_ATR` | `0.25` | ATR distance for the snap mechanism. |
| `FASTTP_COOLDOWN_S` | `15` | Wait time between FastTP checks. |
| `ASTER_FUNDING_FILTER_ENABLED` | `true` | Enables funding limitations. |
| `ASTER_FUNDING_MAX_LONG` / `ASTER_FUNDING_MAX_SHORT` | `0.0010` | Funding caps per direction. |

### AI, Automation, and Guardrails

| Variable | Default | Description |
| --- | --- | --- |
| `ASTER_BANDIT_ENABLED` | `true` | Enables the LinUCB policy. |
| `ASTER_ALPHA_ENABLED` | `true` | Toggles the optional alpha model. |
| `ASTER_ALPHA_THRESHOLD` | `0.55` | Minimum confidence to approve a trade. |
| `ASTER_ALPHA_PROMOTE_DELTA` | `0.15` | Extra confidence required to upsize. |
| `ASTER_HISTORY_MAX` | `250` | Number of historical trades for analytics. |
| `ASTER_OPENAI_API_KEY` | empty | API key for AITradeAdvisor. |
| `ASTER_AI_MODEL` | `gpt-4o` | Model ID for AI analysis. |
| `ASTER_AI_DAILY_BUDGET_USD` | `1000` | Daily budget limit (USD). |
| `ASTER_AI_STRICT_BUDGET` | `true` | Stops AI calls after hitting the budget. |
| `ASTER_AI_SENTINEL_ENABLED` | `true` | Activates the News Sentinel. |
| `ASTER_AI_SENTINEL_DECAY_MINUTES` | `90` | Lifetime of a news warning. |
| `ASTER_AI_NEWS_ENDPOINT` | empty | External source for breaking news. |
| `ASTER_AI_NEWS_API_KEY` | empty | API token for the sentinel. |
| `ASTER_BRACKETS_QUEUE_FILE` | `brackets_queue.json` | Queue file for guard repairs. |

Additional variables (such as universe filters, per-bucket position sizing, or dashboard behavior) can be found directly in the source code or in the UI. Every change made in the dashboard is persisted to `dashboard_config.json` once confirmed.

## Security Notice
- Live trading carries significant risk: always test changes in paper mode first.
- Never commit or share API keys publicly.
- Even with caching enabled, regularly verify that market and order data are up to date.
- Configure budget and sentinel parameters deliberately to control AI costs and event risks.

Best of luck & happy trading! Contributions and issue reports are always welcome.
