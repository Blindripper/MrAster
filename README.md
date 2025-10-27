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
- **Machine-learning policy** (`ml_policy.py`) combines contextual bandits with an optional alpha classifier to govern trade admission and sizing.

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

### AI Mode Explained

AI mode turns the strategy into an autonomous co-pilot that continuously supervises every trade candidate. Once you toggle the dashboard to **AI** (or set `ASTER_MODE=ai` / `ASTER_AI_MODE=true` in the environment) and provide an OpenAI API key, the bot instantiates the `AITradeAdvisor` and a `DailyBudgetTracker`. From that point on the workflow changes as follows:

1. **Signal intake** – The regular scanner still computes momentum, RSI, ATR, spread, funding, and trend context. These metrics are injected into the AI prompt together with the current bid/ask, base stop/take-profit distances, and per-symbol risk limits.
2. **Sentinel context** – The `NewsTrendSentinel` keeps a rolling cache of 24h ticker stats and optional external news. It adds hype and event-risk scores plus veto flags into the AI payload. A red sentinel label hard-blocks trades even before an AI request is made.
3. **AI decision** – For a classical signal the advisor calls `plan_trade()`. When no deterministic signal exists, it may still propose a discretionary trend trade via `plan_trend_trade()`. In both cases the model returns structured JSON that contains:
   - `take` / `decision` – whether to execute or skip the setup.
   - Sizing overrides (`size_multiplier`) that scale the standard bucket allocation, plus optional leverage hints.
   - Risk adjustments such as stop-loss / take-profit multipliers, FastTP tweaks, or explicit price levels.
   - A short `risk_note` and human-readable `explanation` that are shown in the dashboard activity feed.
4. **Budget enforcement** – Every completion is cost-estimated using the built-in pricing table. `DailyBudgetTracker` checks the projected spend before issuing a request and records the actual cost afterwards. If the configured daily limit is reached (and `ASTER_AI_STRICT_BUDGET=true`), further AI calls are skipped until the UTC day rolls over.
5. **Execution & telemetry** – Approved trades inherit the AI adjustments. The resulting rationale, sentinel state, and budget snapshot are persisted in `aster_state.json`, surfaced in the AI cockpit (decision feed, budget card, and chat), and included in post-mortems if a trade later hits a guardrail.

To activate AI mode safely:

- Provide `ASTER_OPENAI_API_KEY` (and optionally `ASTER_CHAT_OPENAI_API_KEY`, `ASTER_AI_MODEL`, `ASTER_AI_TEMPERATURE`, or dashboard overrides) in the AI control panel.
- Set a realistic `ASTER_AI_DAILY_BUDGET_USD` and choose whether the limit is strict.
- Optionally supply `ASTER_AI_NEWS_ENDPOINT` + token to enrich the sentinel with external events.
- Confirm that the dashboard shows an active AI budget and that the AI activity feed is producing decisions before letting it run unattended.

### NewsTrendSentinel Deep Dive

`NewsTrendSentinel` acts as a real-time risk gate before any AI or policy logic places a trade. It evaluates market volatility, trading activity, and optional external news per symbol, then produces the hype and event-risk scores that power the green/yellow/red labels in the dashboard.

#### Configuration

You configure the sentinel entirely through environment variables:

- `ASTER_AI_SENTINEL_ENABLED` (default `true`): Turns the module on, even when AI mode is disabled.
- `ASTER_AI_SENTINEL_DECAY_MINUTES` (default `90`): Retention period for cached evaluations.
- `ASTER_AI_NEWS_ENDPOINT`: Optional HTTP endpoint that returns the latest headlines for a symbol.
- `ASTER_AI_NEWS_API_KEY`: Optional bearer token that is passed as the `Authorization` header when calling the news endpoint.

When a news endpoint is present, the sentinel fetches up to six headlines per symbol. It accepts either a plain JSON array or an object with an `items`/`results` array. Network or parsing errors only generate log entries; the sentinel falls back to pure market data.

#### Data sources and caching

Every evaluation starts with the 24h ticker from the configured exchange. The raw ticker result is cached for 45 seconds to avoid rate limits. Completed sentinel evaluations are cached for 30 seconds, so repeated calls within that window return immediately. The optional `refresh()` helper pre-fills both caches during each bot cycle to keep the data warm.

#### Scoring and labeling

From the ticker payload the sentinel derives price change, quote volume, taker-buy ratio, high/low range, and intraday volatility. These metrics feed into:

- **Event risk** – A blend of volatility and trend strength. Large drawdowns (worse than −9 %) automatically escalate the label to at least orange/red.
- **Hype score** – Volume factor, price momentum, and buying pressure combined.
- **Label** – Green for low risk, yellow for medium risk or strong momentum, red for severe events (hard block). The sentinel also emits contextual events ("rally > 8 %", "high intraday volatility", …) that appear in the dashboard feed.
- **Actions** – `size_factor` scales later position sizes between 0 and 1.45, while `hard_block` aborts trades outright.

#### External news integration

If news is enabled, each headline contributes source, title, and a `severity`. Critical items bump event risk by 0.2, force the label to red, and activate the hard block so that no trade is opened while the alert is active.

#### State and downstream consumers

Each evaluation is written to `state["sentinel"][symbol]` with an ISO timestamp. The summary fields (`sentinel_event_risk`, `sentinel_hype`, `sentinel_label`) are injected into the execution context (`ctx`) so that the AI prompt, dashboard, and logs all have immediate access. `handle_symbol()` checks the sentinel before triggering AI calls; a red label stops the workflow instantly, while yellow labels throttle sizing and enforce stricter guardrails.

#### Typical usage

1. Set the relevant `ASTER_AI_SENTINEL_*` variables and (optionally) provide a news endpoint with authentication.
2. Start the bot or dashboard backend; the sentinel initializes automatically and keeps the cache fresh as part of each scan cycle.
3. Monitor the dashboard: yellow and red labels appear next to affected symbols, and hard blocks prevent the AI or manual execution from submitting orders during elevated risk.
4. Review the combined ticker/news events in the dashboard activity feed and post-mortem reports to understand why trades were throttled or vetoed.

### ML Policy Deep Dive

The ML policy in `ml_policy.py` mixes two LinUCB contextual bandits with an optional logistic alpha classifier. All of them consume the same ten-dimensional feature vector that `_vec_from_ctx` extracts from the bot context (ADX, ATR%, RSI, spreads, and more).

**Gate bandit (take vs. skip).** The first LinUCB instance decides whether a trade candidate should be taken. It keeps a feature covariance matrix `A` and a reward vector `b`, initialized with an L2 prior. For every decision it computes the expected reward plus an uncertainty bonus (`μ + α·s`). If that upper confidence bound drops below configurable margins the candidate is skipped. The gate supports ε-greedy exploration, warm-up boosts, and a "skip push" penalty to bias it toward caution when needed.

**Sizing bandit (S/M/L).** A second LinUCB instance picks the position bucket. Each size is treated as an arm by scaling the feature vector with a bucket-specific multiplier before evaluation. The arm with the highest UCB score wins; if sizing control is disabled, the policy defaults to the smallest bucket.

**Optional alpha model.** When `alpha_enabled` is set, a logistic regression model adds a probabilistic risk view. It performs online standardization (rolling mean/variance), appends a bias term, and outputs a confidence score through a sigmoid. Low confidence below a configurable threshold can force a skip, while high confidence may promote the chosen bucket to a larger size once sufficient warm-up data exists.

**Learning loop.** Training happens in the `note_exit` hook after every closed trade, using rewards derived from keywords such as realized R-multiples. The gate and sizing bandits update their `A` and `b` matrices with the outer product of the context vector and the received reward. The alpha model performs a weighted logistic gradient step (with L2 regularization) on positive or negative examples derived from reward margins.

**Persistence.** Each component implements `to_dict`/`from_dict`, so the full training state—including covariance matrices, reward vectors, scaler statistics, and alpha weights—can be serialized and restored between sessions.

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
| `ASTER_EXCHANGE_BASE` | `https://fapi.asterdex.com` | REST endpoint for market and order data (set to e.g. `https://fapi.binance.com` for Binance Futures, or your paper-trading mirror). |
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

*The dashboard seeds the environment with the values shown here (51/49 RSI bounds, 0.007 risk share). If you launch the CLI without the dashboard, the internal fallbacks default to 52/48 and 0.006 until you override them via environment variables or `dashboard_config.json`.*

### AI, Automation, and Guardrails

| Variable | Default | Description |
| --- | --- | --- |
| `ASTER_BANDIT_ENABLED` | `true` | Enables the LinUCB policy. |
| `ASTER_ALPHA_ENABLED` | `true` | Toggles the optional alpha model. |
| `ASTER_ALPHA_THRESHOLD` | `0.55` | Minimum confidence to approve a trade. |
| `ASTER_ALPHA_PROMOTE_DELTA` | `0.15` | Extra confidence required to upsize. |
| `ASTER_HISTORY_MAX` | `250` | Number of historical trades for analytics. |
| `ASTER_OPENAI_API_KEY` | empty | API key for AITradeAdvisor. |
| `ASTER_CHAT_OPENAI_API_KEY` | empty | Optional dashboard chat-only OpenAI key. Falls back to `ASTER_OPENAI_API_KEY` when blank. |
| `ASTER_AI_MODEL` | `gpt-4o` | Model ID for AI analysis. |
| `ASTER_AI_DAILY_BUDGET_USD` | `20` | Daily budget limit (USD). |
| `ASTER_AI_STRICT_BUDGET` | `true` | Stops AI calls after hitting the budget. |
| `ASTER_AI_MIN_INTERVAL_SECONDS` | `8` | Cooldown before the AI re-evaluates the same symbol. |
| `ASTER_AI_SENTINEL_ENABLED` | `true` | Activates the News Sentinel. |
| `ASTER_AI_SENTINEL_DECAY_MINUTES` | `90` | Lifetime of a news warning. |
| `ASTER_AI_NEWS_ENDPOINT` | empty | External source for breaking news. |
| `ASTER_AI_NEWS_API_KEY` | empty | API token for the sentinel. |
| `ASTER_BRACKETS_QUEUE_FILE` | `brackets_queue.json` | Queue file for guard repairs. |

### Persistence Files

The dashboard stack keeps a few JSON files in the repository root so that state survives restarts:

- **`aster_state.json`** – primary store for open positions, AI telemetry, sentinel state, and dashboard UI preferences. Delete it to force a clean slate when the data becomes inconsistent.
- **`dashboard_config.json`** – mirrors the environment editor. Back it up if you maintain multiple presets, or remove it to revert to the seeded defaults shown above.
- **`brackets_queue.json`** – maintained by `brackets_guard.py` to reconcile stop/TP orders. If you spot repeated bracket repair attempts, archive the file for analysis and then remove it to reset the queue.

Stop the backend before editing or deleting these files to avoid partial writes. When in doubt, move the files out of the repository to keep a snapshot before starting a fresh session.

Additional variables (such as universe filters, per-bucket position sizing, or dashboard behavior) can be found directly in the source code or in the UI. Every change made in the dashboard is persisted to `dashboard_config.json` once confirmed.

## Security Notice
- Live trading carries significant risk: always test changes in paper mode first.
- Never commit or share API keys publicly.
- Even with caching enabled, regularly verify that market and order data are up to date.
- Configure budget and sentinel parameters deliberately to control AI costs and event risks.

Best of luck & happy trading! Contributions and issue reports are always welcome.
