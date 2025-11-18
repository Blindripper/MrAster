<div align="center">
  <img src="assets/mraster-logo.png" alt="MrAster logo" width="240" />
  <h1>MrAster Trading Bot</h1>
  <p><strong>Your friendly crypto futures co-pilot: watch the market, manage risk, and keep you in the loop.</strong></p>
  <p>
    <a href="#mraster-in-60-seconds">Why MrAster?</a>
    ·
    <a href="#quick-start">Quick start</a>
    ·
    <a href="#dashboard-at-a-glance">Dashboard tour</a>
    ·
    <a href="#under-the-hood-for-builders">Under the hood</a>
  </p>
</div>

<p align="center">
  <a href="https://www.python.org/" target="_blank"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python 3.10+" /></a>
  <a href="#dashboard-at-a-glance"><img src="https://img.shields.io/badge/Control-Clean%20web%20dashboard-8A2BE2" alt="Dashboard" /></a>
  <a href="#safety-first"><img src="https://img.shields.io/badge/Mode-Paper%20or%20live-FF8C00" alt="Modes" /></a>
  <a href="#safety-first"><img src="https://img.shields.io/badge/Reminder-Trading%20is%20risky-E63946" alt="Risk warning" /></a>
</p>

> “Flip on the backend, open the browser, and let the copilots do the heavy lifting.”

---

<a id="mraster-in-60-seconds"></a>

## ✨ MrAster in 60 seconds

- **Hands-off trading** – MrAster scans the futures market, suggests trades, and can execute them with built-in guardrails.
- **Always-on dashboard** – Start or stop the bot, adjust risk sliders, and read AI explanations from one friendly web page.
- **AI that respects your budget** – Daily spend caps, cool-downs, and a news sentinel keep the copilots helpful and affordable.
- **No guesswork setup** – Use paper mode to rehearse before you flip the switch to live orders.

<a id="quick-start"></a>

## 🚀 Quick start

1. **Set up Python**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
2. **Launch the backend**
   ```bash
   python dashboard_server.py
   # or enable auto-reload
   uvicorn dashboard_server:app --host 0.0.0.0 --port 8000
   ```
3. **Finish inside the browser**
   Open <http://localhost:8000>, connect your exchange keys (or paper mode), and follow the guided setup.

> Prefer running headless? Export `ASTER_PAPER=true` (optional) and call `python aster_multi_bot.py`. Add `ASTER_RUN_ONCE=true` to perform a single scan cycle.

<a id="dashboard-at-a-glance"></a>

## 🖥️ Dashboard at a glance

- **One-click control** – Start, stop, or relaunch the supervised bot (`aster_multi_bot.py`) without touching the terminal.
- **Live logs & alerts** – Follow every trade idea, AI response, and guardrail warning in real time.
- **Risk made simple** – Choose a preset (Low / Mid / High / ATT) or switch to Pro mode to edit every `ASTER_*` knob.
- **Safe config editing** – Update your environment securely; MrAster validates the fields before applying them.
- **AI copilots on display** – Read plain-language trade notes, see how much budget they’ve used, and chat back.
- **Performance snapshots** – Review PnL charts, trade history, and market heat maps without leaving the page.

<a id="safety-first"></a>

## 🛡️ Safety first

- **Paper mode**: rehearse strategies using simulated fills before trading real funds.
- **Budget caps**: AI helpers respect your daily USD limit unless you explicitly lift it.
- **Sentinel warnings**: breaking news, unusual funding, and volatility spikes surface instantly.
- **You stay in charge**: stop the bot, edit settings, or pause AI autonomy whenever you like.

<a id="under-the-hood-for-builders"></a>

## 🤓 Under the hood (for builders)

Curious about the engines, guardrails, and configuration surface? Expand the sections below for the full technical tour.

<details>
<summary><strong>AI Copilot Stack</strong></summary>

- **AITradeAdvisor** assembles every request with regime stats, orderbook context, and structured prompts, then fans them out through a thread pool (respecting caching and per-model price sheets) before handing back JSON plans with overrides and explanations.
- **DailyBudgetTracker + BudgetLearner** double-gate spending: the tracker keeps a rolling ledger with per-model averages, while the learner tilts symbol budgets and skips expensive calls when recent edge deteriorates, all updated after each OpenAI response.
- **NewsTrendSentinel** (`ASTER_AI_SENTINEL_*`) fuses 24h market stats with optional external news into event-risk labels, size clamps, and hype multipliers before the advisor ever sees the trade.
- **PostmortemLearning** distils qualitative trade reviews into persistent numeric features so the next plan “remembers” what the last exit taught us.
- **ParameterTuner** harvests trade outcomes, recomputes size/ATR biases, and only escalates to LLM suggestions once enough statistically relevant history is captured.
- **PlaybookManager** refreshes a living playbook of market regimes, directives, and structured risk adjustments that the advisor injects into every payload.
- **Pending queue & concurrency guards** throttle autonomy with `ASTER_AI_CONCURRENCY`, `ASTER_AI_PENDING_LIMIT`, and global cool-downs so AI calls never overwhelm the exchange or your budget while still surfacing queued intents in the dashboard feed.

</details>

<details>
<summary><strong>Trading Engine</strong></summary>

- **RSI-driven signals with trend confirmation** configurable via `ASTER_*` environment variables or the dashboard editor.
- **Multi-armed bandit policy (`BanditPolicy`)** blends LinUCB exploration with the optional alpha model (`ml_policy.py`) to decide TAKE/SKIP and size buckets (S/M/L).
- **Market hygiene filters** keep the feed clean: funding and spread guards, wickiness filters, and cached klines/24h tickers smooth out exchange noise.
- **Oracle-aware non-arbitrage guard** clamps the mark/oracle gap using the premium index (per Jez, 2025) and steers entries away from funding traps.

</details>

<details>
<summary><strong>Risk & Order Management</strong></summary>

- **BracketGuard** (`brackets_guard.py`) repairs stop-loss and take-profit orders while respecting both legacy and new bot signatures.
- **FastTP** trims adverse moves with ATR-bound checkpoints and cooldown logic.
- **Equity and exposure caps** (`ASTER_MAX_OPEN_*`, `ASTER_EQUITY_FRACTION`) plus persistent state (`aster_state.json`) ensure continuity across restarts.

</details>

<details>
<summary><strong>Observability & Resilience</strong></summary>

- **Dashboard-native monitoring** covers log streaming, process control, environment editing, AI chat, and analytics cards.
- **HTTP guardrails** via `ASTER_HTTP_RETRIES`, `ASTER_HTTP_BACKOFF`, and `ASTER_HTTP_TIMEOUT` harden network calls.
- **Single dependency pass** — `pip install -r requirements.txt` brings in everything you need.

</details>

<details>
<summary><strong>Configuration reference</strong></summary>

| Variable | Default | Description |
| --- | --- | --- |
| `ASTER_API_KEY` / `ASTER_API_SECRET` | empty | API credentials for live trading. |
| `ASTER_EXCHANGE_BASE` | `https://fapi.asterdex.com` | REST endpoint for market and order data (set e.g. to `https://fapi.binance.com` for Binance Futures, or your paper-trading mirror). |
| `ASTER_PAPER` | `false` | Enables the paper-trading adapter. |
| `ASTER_RUN_ONCE` | `false` | Executes exactly one scan cycle. |
| `ASTER_LOGLEVEL` | `INFO` | Logging verbosity (`DEBUG`, `INFO`, ...). |
| `ASTER_MODE` | `standard` | Default dashboard mode (`standard`, `pro`, `ai`). |
| `ASTER_LOOP_SLEEP` | `10` | Pause between scans in seconds. |
| `ASTER_STATE_FILE` | `aster_state.json` | Persistence file for bot and AI state. |
| `ASTER_HTTP_RETRIES` | `2` | Additional HTTP retry attempts. |
| `ASTER_HTTP_BACKOFF` | `0.6` | Base wait time (seconds) between retries. |
| `ASTER_HTTP_TIMEOUT` | `20` | HTTP timeout in seconds. |
| `ASTER_KLINE_CACHE_SEC` | `9` | Lifetime of the kline cache. |

</details>

<details>
<summary><strong>Strategy, risk, and positioning</strong></summary>

| Variable | Default | Description |
| --- | --- | --- |
| `ASTER_INTERVAL` / `ASTER_HTF_INTERVAL` | `5m` / `30m` | Timeframes for signals and confirmation. |
| `ASTER_RSI_BUY_MIN` / `ASTER_RSI_SELL_MAX` | `51` / `49`* | RSI bounds for long and short entries. |
| `ASTER_CONT_PULLBACK_STOCH_WARN` / `ASTER_CONT_PULLBACK_STOCH_MAX` | `65.0` / `85.0` | Soft/hard thresholds for the continuation pullback guard (set to `0` to disable, or raise to loosen the filter). |
| `ASTER_ALLOW_TREND_ALIGN` | `false` | Enforces trend alignment between timeframes. |
| `ASTER_TREND_BIAS` | `with` | Trade with or against the trend. |
| `ASTER_MIN_QUOTE_VOL_USDT` | `150000` | Minimum volume for tradable symbols. |
| `ASTER_SPREAD_BPS_MAX` | `0.0020` | Maximum tolerated bid/ask spread (bps). |
| `ASTER_WICKINESS_MAX` | `0.97` | Filter against overly volatile candles. |
| `ASTER_MIN_EDGE_R` | `0.30` | Minimum edge (in R) required to approve a trade. |
| `ASTER_DEFAULT_NOTIONAL` | `1000` | Baseline notional for trades when no adaptive sizing data is available (raised to 1000 USDT by the aggressive risk profile). |
| `ASTER_SIZE_MULT_FLOOR` | `0.75` | Minimum position-size multiplier for autonomous trades (set higher to keep the AI close to the configured baseline stake). |
| `ASTER_MAX_NOTIONAL_USDT` | `0` | Optional hard cap on order notional (set to `0` to let leverage and equity guards decide). |
| `ASTER_SIZE_MULT_CAP` | `5.0` | Maximum position-size multiplier allowed after all adjustments. |
| `ASTER_CONFIDENCE_SIZING` | `true` | Enables confidence-weighted sizing. When `true`, AI confidence blends between the configured multiplier bounds. |
| `ASTER_CONFIDENCE_SIZE_MIN` / `ASTER_CONFIDENCE_SIZE_MAX` | `1.0` / `3.0` | Lower and upper multiplier targets when confidence-based sizing is active (identical values lock the multiplier to a fixed × value). |
| `ASTER_CONFIDENCE_SIZE_BLEND` / `ASTER_CONFIDENCE_SIZE_EXP` | `1` / `2.0` | Blend weight between baseline and confidence target, plus the exponent shaping the curve (values >1 favour high confidence). |
| `ASTER_RISK_PER_TRADE` | `0.02`* | Share of equity per trade (floor enforced by the aggressive risk profile; balanced/conservative modes lower it). |
| `ASTER_EQUITY_FRACTION` | `0.90` | Maximum equity utilization across open positions (tuned upward by the aggressive profile, with lower ceilings in other profiles). |
| `ASTER_LEVERAGE` | `12` | Default leverage floor for orders. Dashboard presets apply 4× (Low), 10× (Mid), or the per-symbol exchange maximum (High / ATT). |
| `ASTER_RISK_PROFILE` | `aggressive` | Bundled sizing preset (`conservative`, `balanced`, `aggressive`) that bumps leverage, equity usage, and multiplier floors in one toggle. |
| `ASTER_MAX_OPEN_GLOBAL` | `0` | Global cap on concurrent positions (0 = unlimited, rely on equity guard). |
| `ASTER_MAX_OPEN_PER_SYMBOL` | `1` | Per-symbol position limit (0 = unlimited, netting on exchange). |
| `ASTER_SL_ATR_MULT` / `ASTER_TP_ATR_MULT` | `1.0` / `1.6` | ATR multiples for stop and take-profit. |
| `ASTER_TREND_SL_BIAS_RANGE` | `0.35` | Extends/tightens the initial stop based on recorded trend quality (0 = disabled). |
| `ASTER_MAX_HOLD_SECONDS` | `600` | Time-based stop: when the trade is still red after this many seconds, the bot flattens it. |
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
| `ASTER_NON_ARB_SKIP_GAP` | `0.0030` | Absolute mark/oracle gap that forces a skip regardless of direction. |

*When launched from the dashboard, values seed to 51/49 RSI and inherit the selected risk profile (default `aggressive`, i.e. a 0.02 risk share — High preset in AI mode still escalates to 0.10). CLI-only launches fall back to 52/48 and the profile floor until overridden or synced via `dashboard_config.json`.*

*High/ATT presets without a manual `ASTER_LEVERAGE` override now auto-select the lowest leverage rung that still covers the strategy's default notional when AI mode is active, preventing exchange-imposed notional caps from throttling position size.*

</details>

<details>
<summary><strong>AI, automation, and guardrails</strong></summary>

| Variable | Default | Description |
| --- | --- | --- |
| `ASTER_BANDIT_ENABLED` | `true` | Enables the LinUCB policy. |
| `ASTER_AI_MODE` | `false` | Forces AI runtime even if the dashboard default is Standard/Pro. Equivalent to setting `ASTER_MODE=ai`.|
| `ASTER_ALPHA_ENABLED` | `true` | Toggles the optional alpha model. |
| `ASTER_ALPHA_THRESHOLD` | `0.50` | Minimum confidence to approve a trade. |
| `ASTER_ALPHA_WARMUP` | `30` | Minimum trades recorded before the alpha model can veto or promote. |
| `ASTER_ALPHA_PROMOTE_DELTA` | `0.15` | Extra confidence required to upsize. |
| `ASTER_HISTORY_MAX` | `250` | Number of historical trades for analytics. |
| `ASTER_OPENAI_API_KEY` | empty | API key for AITradeAdvisor. |
| `ASTER_CHAT_OPENAI_API_KEY` | empty | Optional dashboard chat-only OpenAI key; falls back to `ASTER_OPENAI_API_KEY`. |
| `ASTER_AI_MODEL` | `gpt-4.1` | Model ID for AI analysis. |
| `ASTER_AI_DAILY_BUDGET_USD` | `20` | Daily budget limit (USD). Ignored when `ASTER_PRESET_MODE` is `high` or `att`. |
| `ASTER_AI_STRICT_BUDGET` | `true` | Stops AI calls after hitting the budget. |
| `ASTER_AI_MIN_INTERVAL_SECONDS` | `3` | Cooldown before the AI re-evaluates the same symbol. |
| `ASTER_AI_CONCURRENCY` | `4` | Maximum concurrent LLM requests dispatched via the advisor thread pool.|
| `ASTER_AI_PENDING_LIMIT` | `max(4, 3×concurrency)` | Cap on queued AI jobs before falling back to heuristics.|
| `ASTER_AI_GLOBAL_COOLDOWN_SECONDS` | `1.0` | Global pause enforced between requests to prevent API bursts.|
| `ASTER_AI_PLAN_TIMEOUT_SECONDS` | `45` | Maximum wait for a pending AI plan before reverting to fallbacks.|
| `ASTER_AI_SENTINEL_ENABLED` | `true` | Activates the News Sentinel. |
| `ASTER_AI_SENTINEL_DECAY_MINUTES` | `60` | Lifetime of a news warning. |
| `ASTER_AI_NEWS_ENDPOINT` | empty | External source for breaking news. |
| `ASTER_AI_NEWS_API_KEY` | empty | API token for the sentinel. |
| `ASTER_AI_TEMPERATURE` | `0.3` | Optional creativity override (set `1.0` for provider default).|
| `ASTER_AI_DEBUG_STATE` | `false` | Turns on verbose logging and debug payload dumps for AI workflows.|
| `ASTER_BRACKETS_QUEUE_FILE` | `brackets_queue.json` | Queue file for guard repairs. |

</details>

<details>
<summary><strong>Persistence files</strong></summary>

- **`aster_state.json`** – Primary store for open positions, AI telemetry, sentinel state, and dashboard UI preferences. Delete it to force a clean slate when data becomes inconsistent.
- **`dashboard_config.json`** – Mirrors the environment editor. Back it up for multiple presets or remove it to revert to seeded defaults.
- **`brackets_queue.json`** – Maintained by `brackets_guard.py` to reconcile stop/TP orders. Archive then remove if you observe repeated repair attempts.

Stop the backend before editing or deleting these files to avoid partial writes; move them out of the repository if you need a snapshot before a fresh session.

</details>

## 🔐 Security notice

- Live trading carries significant risk: always rehearse in paper mode before committing real funds.
- Keep API keys private and rotate them regularly.
- Even with caching enabled, confirm that market and order data stay fresh.
- Tune budget and sentinel parameters to match your risk appetite.

Happy trading—and if you spot a bug or have an idea, open an issue or pull request!
