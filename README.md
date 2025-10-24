# MrAster Trading Bot

MrAster is a Python trading toolkit tailored for perpetual futures on Binance-compatible exchanges. The repository contains the following core pieces:

* `aster_multi_bot.py` – the main trading bot with signal logic, multi-armed bandit policy, and automated bracket-order handling.
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

The dashboard creates `dashboard_config.json` and writes changed environment values back to disk. Trades, open positions, and AI hints are driven by `aster_state.json`.

## Safety & disclaimers

* Live trading involves substantial financial risk—thoroughly test every change in paper mode first.
* Never commit API keys to the repository or expose them publicly.
* Because of the caching layer, historical data can survive short exchange outages. Double-check that the prices you trade on are still current.

Good luck and happy trading! Contributions and issues are welcome.
