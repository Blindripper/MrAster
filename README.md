# MrAster Trading Bot

MrAster is a Python trading toolkit tailored for perpetual futures on Binance-compatible exchanges. The repository contains the following core pieces:

* `aster_multi_bot.py` – the main trading bot with signal logic, multi-armed bandit policy, and automated bracket-order handling.
* `ml_policy.py` – LinUCB-based bandit and optional alpha model that guide trade admission and position sizing when enabled.
* `brackets_guard.py` – a resilient guard process that repairs stop-loss and take-profit orders.
* `dashboard_server.py` + `dashboard_static/` – a FastAPI-powered dashboard for bot control, configuration, and log streaming.

## Recent improvements

* **HTTP hardening:** Configurable retries (`ASTER_HTTP_RETRIES`, `ASTER_HTTP_BACKOFF`, `ASTER_HTTP_TIMEOUT`) provide protection against transient REST failures.
* **Kline caching:** Frequently reused market data is cached for `ASTER_KLINE_CACHE_SEC` seconds with graceful fallbacks if the upstream API is unavailable.
* **Requirements file:** Installing all dependencies is now a single `pip install -r requirements.txt` away.

## Prerequisites

* Python ≥ 3.10 (recommended)
* A Binance or AsterDex compatible futures account for live trading
* Optional: paper-trading mode can run without exchange credentials

## Installation

```bash
# Clone the repository
git clone https://example.com/MrAster.git
cd MrAster

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

## Configuration

The bot is controlled via environment variables. Key parameters include:

| Variable | Description | Default |
| --- | --- | --- |
| `ASTER_API_KEY` / `ASTER_API_SECRET` | Exchange API credentials | empty |
| `ASTER_EXCHANGE_BASE` | REST endpoint (e.g. `https://fapi.binance.com`) | `https://fapi.asterdex.com` |
| `ASTER_PAPER` | Enable paper trading (`true`/`false`) | `false` |
| `ASTER_RUN_ONCE` | Run a single scan cycle | `false` |
| `ASTER_LOGLEVEL` | Log level (`DEBUG`, `INFO`, …) | `INFO` |
| `ASTER_HTTP_RETRIES` | Additional HTTP attempts after failures | `2` |
| `ASTER_HTTP_BACKOFF` | Base delay (seconds) for retries | `0.6` |
| `ASTER_HTTP_TIMEOUT` | Request timeout in seconds | `20` |
| `ASTER_KLINE_CACHE_SEC` | Lifetime of the kline cache | `45` |
| `ASTER_FUNDING_FILTER_ENABLED` | Skip trades when funding exceeds thresholds | `true` |
| `ASTER_FUNDING_MAX_LONG` | Maximum funding rate (decimal) for long entries | `0.0010` |
| `ASTER_FUNDING_MAX_SHORT` | Maximum absolute negative funding rate for short entries | `0.0010` |

Refer to the [dashboard environment configuration reference](#dashboard-environment-configuration-reference) for a full description of every toggle that can be edited through the UI.

Strategy parameters (RSI limits, ATR multipliers, position sizing, trading universe, and more) can also be configured through environment variables. Check the top section of `aster_multi_bot.py` or the dashboard (`/api/config`) for the full list.

For local development you can load a `.env` file (via `python-dotenv` or manual exports before launching the bot).

## Running the bot

```bash
# Enable paper mode, then launch the bot
export ASTER_PAPER=true
python aster_multi_bot.py
```

*Press `CTRL+C` (or send SIGTERM) to gracefully finish the current scan cycle.*

You can execute a single analysis pass by setting `ASTER_RUN_ONCE=true`. Runtime state (trades, policy, FastTP cooldowns) is persisted in `aster_state.json`.

### Machine-learning trading policy

The optional reinforcement-learning layer lives in `ml_policy.py` and is switched on by setting `ASTER_BANDIT_ENABLED=true` (enabled by default). When active, the bot loads or creates a persisted `BanditPolicy` and consults it for every candidate signal to decide whether to open a trade and which size bucket (`S`, `M`, `L`) to use. Trade outcomes are fed back into the policy via `note_entry`/`note_exit`, allowing the LinUCB model and alpha estimator to keep learning between runs.

## Using the dashboard

1. Ensure dashboard dependencies (`fastapi`, `uvicorn`) are installed.
2. Start the dashboard:

   ```bash
   python dashboard_server.py
   # or with reload support:
   uvicorn dashboard_server:app --host 0.0.0.0 --port 8000
   ```

3. Open your browser: `http://localhost:8000`
4. Stream logs live (`/ws/logs`), edit configuration, and manage the bot process via the action buttons.

### Dashboard modes and presets

The control center now ships with two personas:

* **Default mode (presets):** Designed for quick launches. Pick between **Low**, **Mid**, and **High** trading intensity and adjust two guardrails:
  * **Risk per trade** – percentage of account equity allocated to a single position. The slider ranges from 0.25% to 5%.
  * **Leverage** – capped at **5×** to prevent excessive exposure. Use the slider to align with your exchange limit.
  The activity feed card shows a curated subset of live events (fills, warnings, and notices) so newcomers can stay focused on what matters.
* **Pro-Mode:** Toggle the switch in the header to reveal the full environment editor and the verbose debug log stream. All `ASTER_*` variables can be changed live; the save action writes them to `dashboard_config.json` so subsequent launches reuse them.

### Dashboard environment configuration reference

Every field in the **Environment configuration** card maps directly to an environment variable that the FastAPI server injects into the trading bot. Defaults are shown alongside a summary of the behaviour they control.

| Variable | Default | Purpose |
| --- | --- | --- |
| `ASTER_EXCHANGE_BASE` | `https://fapi.asterdex.com` | REST endpoint for market data and order routing. Switch when targeting another Binance-compatible cluster. |
| `ASTER_API_KEY` | empty | API key for authenticated calls. Leave blank in paper trading. |
| `ASTER_API_SECRET` | empty | API secret that matches the key above. |
| `ASTER_RECV_WINDOW` | `10000` | Binance recvWindow (ms) to tolerate clock drift on signed requests. |
| `ASTER_WORKING_TYPE` | `MARK_PRICE` | Determines whether stops/TPs are evaluated against `MARK_PRICE` or `CONTRACT_PRICE`. |
| `ASTER_LOGLEVEL` | `DEBUG` | Logging verbosity for the bot process (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `ASTER_PAPER` | `false` | When `true`, enables the simulated exchange adapter. |
| `ASTER_RUN_ONCE` | `false` | Exit after a single scan loop instead of running continuously. |
| `ASTER_QUOTE` | `USDT` | Quote asset used for portfolio sizing and filters. |
| `ASTER_INCLUDE_SYMBOLS` | `BTCUSDT,…` | Comma-separated allowlist of tradable instruments. |
| `ASTER_EXCLUDE_SYMBOLS` | `AMZNUSDT,APRUSDT` | Comma-separated blocklist of pairs to ignore even if included elsewhere. |
| `ASTER_UNIVERSE_MAX` | `40` | Maximum number of symbols kept in the active trading universe. |
| `ASTER_UNIVERSE_ROTATE` | `false` | When enabled, rotates the universe periodically to explore fresh markets. |
| `ASTER_MIN_QUOTE_VOL_USDT` | `75000` | Minimum 24h quote volume required for a symbol to be tradable. |
| `ASTER_INTERVAL` | `5m` | Primary timeframe for signal generation. |
| `ASTER_HTF_INTERVAL` | `30m` | Higher timeframe used for confirmation and trend alignment. |
| `ASTER_KLINES` | `360` | Number of klines pulled per symbol for indicator calculations. |
| `ASTER_RSI_BUY_MIN` | `51` | Lower RSI bound that enables long entries (values above indicate momentum). |
| `ASTER_RSI_SELL_MAX` | `49` | Upper RSI bound that enables short entries. |
| `ASTER_ALLOW_TREND_ALIGN` | `true` | Toggle to require alignment between lower and higher timeframe RSI. |
| `ASTER_ALIGN_RSI_PAD` | `1.5` | Margin applied to RSI thresholds when enforcing trend alignment. |
| `ASTER_SPREAD_BPS_MAX` | `0.009` | Maximum bid/ask spread (in basis points) tolerated before skipping a trade. |
| `ASTER_WICKINESS_MAX` | `0.985` | Rejects symbols whose candlesticks show excessive wicks (volatility proxy). |
| `ASTER_MIN_EDGE_R` | `0.08` | Minimum estimated edge (in R) required to approve a signal. |
| `ASTER_DEFAULT_NOTIONAL` | `120` | Fallback position size in notional terms when sizing heuristics cannot decide. |
| `ASTER_RISK_PER_TRADE` | `0.007` | Fraction of equity risked on each trade when computing position size. |
| `ASTER_LEVERAGE` | `3` | Default leverage multiplier requested on the exchange. |
| `ASTER_EQUITY_FRACTION` | `0.25` | Cap on the fraction of account equity that can be allocated simultaneously. |
| `ASTER_MIN_NOTIONAL_USDT` | `5` | Smallest order size (USDT) allowed after sizing rules are applied. |
| `ASTER_MAX_NOTIONAL_USDT` | `300` | Hard ceiling on the notional per trade. |
| `ASTER_SIZE_MULT` | `1.0` | Global multiplier applied to all position sizes. |
| `ASTER_SIZE_MULT_S` | `1.0` | Additional multiplier for “Small” bandit bucket trades. |
| `ASTER_SIZE_MULT_M` | `1.4` | Additional multiplier for “Medium” bucket trades. |
| `ASTER_SIZE_MULT_L` | `1.9` | Additional multiplier for “Large” bucket trades. |
| `ASTER_SL_ATR_MULT` | `1.3` | Stop-loss distance expressed as ATR multiples. |
| `ASTER_TP_ATR_MULT` | `2.0` | Base take-profit distance in ATR multiples. |
| `FAST_TP_ENABLED` | `true` | Enables the FastTP mechanism that trims risk during adverse moves. |
| `FASTTP_MIN_R` | `0.25` | Minimum unrealized R gain before FastTP considers partial exits. |
| `FAST_TP_RET1` | `-0.0010` | First return checkpoint for FastTP to react (decimal). |
| `FAST_TP_RET3` | `-0.0020` | Secondary return checkpoint for deeper pullbacks. |
| `FASTTP_SNAP_ATR` | `0.25` | ATR distance used to “snap” FastTP exits near price. |
| `FASTTP_COOLDOWN_S` | `45` | Cooldown between FastTP checks to avoid thrashing. |
| `ASTER_MAX_OPEN_GLOBAL` | `2` | Max simultaneous positions across all symbols. |
| `ASTER_MAX_OPEN_PER_SYMBOL` | `1` | Max concurrent positions per individual instrument. |
| `ASTER_STATE_FILE` | `aster_state.json` | Location of the bot state file used for persistence. |
| `ASTER_LOOP_SLEEP` | `20` | Delay (seconds) between scan iterations. |
| `ASTER_BANDIT_ENABLED` | `true` | Enables the LinUCB bandit for signal vetting and sizing. |
| `ASTER_HISTORY_MAX` | `250` | Number of historic trades retained for analytics and AI hints. |

The dashboard creates `dashboard_config.json` and writes changed environment values back to disk. Trades, open positions, and AI hints are driven by `aster_state.json`.

Update to new version with (so you don't destroy your .venv): git fetch --all --prune && git reset --hard @{u} && git clean -fd -e .venv/.

## Safety & disclaimers

* Live trading involves substantial financial risk—thoroughly test every change in paper mode first.
* Never commit API keys to the repository or expose them publicly.
* Because of the caching layer, historical data can survive short exchange outages. Double-check that the prices you trade on are still current.

Good luck and happy trading! Contributions and issues are welcome.
