"""Aster Bot Dashboard server providing web UI for configuration, monitoring and history."""
from __future__ import annotations

import asyncio
import json
import os
import shlex
import shutil
import signal
import sys
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import requests
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT_DIR = Path(__file__).resolve().parent
STATE_FILE = ROOT_DIR / os.getenv("ASTER_STATE_FILE", "aster_state.json")
STATIC_DIR = ROOT_DIR / "dashboard_static"
CONFIG_FILE = ROOT_DIR / "dashboard_config.json"

ENV_DEFAULTS: Dict[str, str] = {
    "ASTER_EXCHANGE_BASE": "https://fapi.asterdex.com",
    "ASTER_API_KEY": "",
    "ASTER_API_SECRET": "",
    "ASTER_RECV_WINDOW": "10000",
    "ASTER_WORKING_TYPE": "MARK_PRICE",
    "ASTER_LOGLEVEL": "DEBUG",
    "ASTER_PAPER": "false",
    "ASTER_RUN_ONCE": "false",
    "ASTER_MODE": "standard",
    "ASTER_QUOTE": "USDT",
    "ASTER_INCLUDE_SYMBOLS": "BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT,DOGEUSDT,ADAUSDT,LINKUSDT,AVAXUSDT,TRXUSDT,MATICUSDT,NEARUSDT,LTCUSDT,BCHUSDT,DOTUSDT,ATOMUSDT,ARBUSDT,APTUSDT,SUIUSDT,OPUSDT,BLUAIUSDT,HEMIUSDT,TURTLEUSDT,APRUSDT",
    "ASTER_EXCLUDE_SYMBOLS": "AMZNUSDT,APRUSDT",
    "ASTER_UNIVERSE_MAX": "40",
    "ASTER_UNIVERSE_ROTATE": "false",
    "ASTER_MIN_QUOTE_VOL_USDT": "75000",
    "ASTER_INTERVAL": "5m",
    "ASTER_HTF_INTERVAL": "30m",
    "ASTER_KLINES": "360",
    "ASTER_RSI_BUY_MIN": "51",
    "ASTER_RSI_SELL_MAX": "49",
    "ASTER_ALLOW_TREND_ALIGN": "true",
    "ASTER_ALIGN_RSI_PAD": "1.5",
    "ASTER_SPREAD_BPS_MAX": "0.009",
    "ASTER_WICKINESS_MAX": "0.985",
    "ASTER_MIN_EDGE_R": "0.08",
    "ASTER_DEFAULT_NOTIONAL": "120",
    "ASTER_RISK_PER_TRADE": "0.007",
    "ASTER_LEVERAGE": "3",
    "ASTER_PRESET_MODE": "mid",
    "ASTER_EQUITY_FRACTION": "0.25",
    "ASTER_MIN_NOTIONAL_USDT": "5",
    "ASTER_MAX_NOTIONAL_USDT": "300",
    "ASTER_SIZE_MULT": "1.0",
    "ASTER_SIZE_MULT_S": "1.0",
    "ASTER_SIZE_MULT_M": "1.4",
    "ASTER_SIZE_MULT_L": "1.9",
    "ASTER_SL_ATR_MULT": "1.3",
    "ASTER_TP_ATR_MULT": "2.0",
    "FAST_TP_ENABLED": "true",
    "FASTTP_MIN_R": "0.25",
    "FAST_TP_RET1": "-0.0010",
    "FAST_TP_RET3": "-0.0020",
    "FASTTP_SNAP_ATR": "0.25",
    "FASTTP_COOLDOWN_S": "45",
    "ASTER_MAX_OPEN_GLOBAL": "2",
    "ASTER_MAX_OPEN_PER_SYMBOL": "1",
    "ASTER_STATE_FILE": "aster_state.json",
    "ASTER_LOOP_SLEEP": "20",
    "ASTER_BANDIT_ENABLED": "true",
    "ASTER_ALPHA_ENABLED": "true",
    "ASTER_ALPHA_THRESHOLD": "0.55",
    "ASTER_ALPHA_WARMUP": "40",
    "ASTER_ALPHA_LR": "0.05",
    "ASTER_ALPHA_L2": "0.0005",
    "ASTER_ALPHA_MIN_CONF": "0.2",
    "ASTER_ALPHA_PROMOTE_DELTA": "0.15",
    "ASTER_ALPHA_REWARD_MARGIN": "0.05",
    "ASTER_HISTORY_MAX": "250",
    "ASTER_BOT_SCRIPT": "aster_multi_bot.py",
    "ASTER_OPENAI_API_KEY": "",
    "ASTER_AI_MODEL": "gpt-4o-mini",
    "ASTER_AI_DAILY_BUDGET_USD": "1000",
    "ASTER_AI_STRICT_BUDGET": "true",
    "ASTER_AI_SENTINEL_ENABLED": "true",
    "ASTER_AI_SENTINEL_DECAY_MINUTES": "90",
    "ASTER_AI_NEWS_ENDPOINT": "",
    "ASTER_AI_NEWS_API_KEY": "",
}

ALLOWED_ENV_KEYS = set(ENV_DEFAULTS.keys())


CG_ID: Dict[str, str] = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "BNB": "binancecoin",
    "SOL": "solana",
    "XRP": "ripple",
    "ADA": "cardano",
    "DOGE": "dogecoin",
    "TON": "the-open-network",
    "TRX": "tron",
    "LTC": "litecoin",
    "BCH": "bitcoin-cash",
    "LINK": "chainlink",
    "AVAX": "avalanche-2",
    "DOT": "polkadot",
    "MATIC": "matic-network",
    "ETC": "ethereum-classic",
    "UNI": "uniswap",
    "ATOM": "cosmos",
    "NEAR": "near",
    "APT": "aptos",
    "SUI": "sui",
    "ARB": "arbitrum",
    "OP": "optimism",
}


def build_logo_candidates(ticker: str, chain: Optional[str] = None, contract: Optional[str] = None) -> List[str]:
    t = (ticker or "").upper().strip()
    urls: List[str] = []
    if t in CG_ID:
        cid = CG_ID[t]
        urls.append(f"https://coin-logos.simplr.sh/images/{cid}/standard.png")
        urls.append(f"https://coin-logos.simplr.sh/images/{cid}/large.png")
    if chain and contract:
        urls.append(
            f"https://cdn.jsdelivr.net/gh/trustwallet/assets@master/blockchains/{chain}/assets/{contract}/logo.png"
        )
    if chain and not contract:
        urls.append(
            f"https://cdn.jsdelivr.net/gh/trustwallet/assets@master/blockchains/{chain}/info/logo.png"
        )
    urls.append(f"https://cdn.jsdelivr.net/gh/spothq/cryptocurrency-icons/128/color/{t.lower()}.png")
    return urls


LogoCacheKey = Tuple[str, Optional[str], Optional[str]]
LOGO_CACHE: Dict[LogoCacheKey, Dict[str, Any]] = {}


MOST_TRADED_CACHE: Dict[str, Any] = {"timestamp": 0.0, "payload": None}

BINANCE_24H_URL = "https://api.binance.com/api/v3/ticker/24hr"
BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
EXCLUDED_VOLUME_SUFFIXES = ("UPUSDT", "DOWNUSDT", "BULLUSDT", "BEARUSDT")


def _resolve_logo_sources(ticker: str, chain: Optional[str] = None, contract: Optional[str] = None) -> Dict[str, Any]:
    key: LogoCacheKey = (
        (ticker or "").upper().strip(),
        (chain or "").lower().strip() or None,
        (contract or "").lower().strip() or None,
    )
    cached = LOGO_CACHE.get(key)
    if cached:
        return cached

    candidates = build_logo_candidates(key[0], key[1], key[2])
    primary: Optional[str] = None
    fallbacks: List[str] = []
    for url in candidates:
        try:
            resp = requests.head(url, timeout=4, allow_redirects=True)
            if resp.status_code == 200 and not primary:
                primary = url
                continue
        except requests.RequestException:
            pass
        fallbacks.append(url)

    if not primary and candidates:
        primary = candidates[0]
        fallbacks = [u for u in candidates[1:]]
    elif primary:
        fallbacks = [u for u in candidates if u != primary]

    payload = {"logo": primary, "fallbacks": fallbacks, "candidates": candidates}
    LOGO_CACHE[key] = payload
    return payload


def _fetch_price_change(symbol: str) -> Tuple[Optional[float], Optional[float]]:
    try:
        resp = requests.get(
            BINANCE_KLINES_URL,
            params={"symbol": symbol, "interval": "1m", "limit": 16},
            timeout=6,
        )
        resp.raise_for_status()
        candles = resp.json()
        if not candles:
            return None, None
        first_close = float(candles[0][4])
        last_close = float(candles[-1][4])
        if first_close <= 0:
            return last_close, None
        change = ((last_close - first_close) / first_close) * 100.0
        return last_close, change
    except (requests.RequestException, ValueError, TypeError, IndexError):
        return None, None


def _fetch_most_traded_from_binance(limit: int = 8) -> List[Dict[str, Any]]:
    resp = requests.get(BINANCE_24H_URL, timeout=8)
    resp.raise_for_status()
    payload = resp.json()
    filtered: List[Dict[str, Any]] = []

    for entry in payload:
        symbol = entry.get("symbol")
        if not symbol or not symbol.endswith("USDT"):
            continue
        if any(symbol.endswith(suffix) for suffix in EXCLUDED_VOLUME_SUFFIXES):
            continue
        try:
            volume_quote = float(entry.get("quoteVolume") or 0.0)
        except (TypeError, ValueError):
            continue
        if volume_quote <= 0:
            continue
        try:
            last_price = float(entry.get("lastPrice") or 0.0)
        except (TypeError, ValueError):
            last_price = 0.0
        base = symbol[:-4]
        asset = {
            "symbol": symbol,
            "base": base,
            "quote": "USDT",
            "price": last_price,
            "volume_quote": volume_quote,
            "change_15m": 0.0,
        }
        logo = _resolve_logo_sources(base)
        asset["logo"] = logo.get("logo")
        asset["logo_fallbacks"] = logo.get("fallbacks", [])
        asset["logo_candidates"] = logo.get("candidates", [])
        filtered.append(asset)

    filtered.sort(key=lambda item: item["volume_quote"], reverse=True)
    top_assets = filtered[:limit]

    for asset in top_assets:
        price, change = _fetch_price_change(asset["symbol"])
        if price:
            asset["price"] = price
        if change is not None:
            asset["change_15m"] = change

    return top_assets


async def get_most_traded_assets(force: bool = False) -> Dict[str, Any]:
    now = time.time()
    cached_payload = MOST_TRADED_CACHE.get("payload")
    cached_ts = MOST_TRADED_CACHE.get("timestamp", 0.0)
    if cached_payload and not force and now - cached_ts < 60:
        return cached_payload

    try:
        assets = await asyncio.to_thread(_fetch_most_traded_from_binance)
    except Exception:
        if cached_payload:
            return cached_payload
        return {"updated": datetime.utcnow().isoformat() + "Z", "assets": []}

    payload = {"updated": datetime.utcnow().isoformat() + "Z", "assets": assets}
    MOST_TRADED_CACHE["payload"] = payload
    MOST_TRADED_CACHE["timestamp"] = now
    return payload


def _load_config() -> Dict[str, Any]:
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text())
            env_cfg = data.get("env", {})
        except Exception:
            env_cfg = {}
    else:
        env_cfg = {}

    merged = {k: os.getenv(k, env_cfg.get(k, v)) for k, v in ENV_DEFAULTS.items()}
    config = {"env": merged}
    CONFIG_FILE.write_text(json.dumps(config, indent=2, sort_keys=True))
    return config


def _save_config(config: Dict[str, Any]) -> None:
    CONFIG_FILE.write_text(json.dumps(config, indent=2, sort_keys=True))


CONFIG: Dict[str, Any] = _load_config()


class ConfigUpdate(BaseModel):
    env: Dict[str, str] = Field(default_factory=dict)


class BotStatus(BaseModel):
    running: bool
    pid: Optional[int]
    started_at: Optional[float]
    uptime_s: Optional[float]


class TradeStats(BaseModel):
    count: int
    total_pnl: float
    total_r: float
    win_rate: float
    best_trade: Optional[Dict[str, Any]]
    worst_trade: Optional[Dict[str, Any]]
    ai_hint: str


def _ensure_static_dir() -> None:
    if not STATIC_DIR.exists():
        STATIC_DIR.mkdir(parents=True, exist_ok=True)


_ensure_static_dir()


class LogHub:
    def __init__(self) -> None:
        self.buffer: deque = deque(maxlen=500)
        self.clients: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def register(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            history = list(self.buffer)
            self.clients.add(ws)
        for item in history:
            await self._safe_send(ws, item)

    async def unregister(self, ws: WebSocket) -> None:
        async with self._lock:
            self.clients.discard(ws)

    async def push(self, line: str, level: str = "info") -> None:
        payload = {
            "ts": time.time(),
            "line": line,
            "level": level,
        }
        async with self._lock:
            self.buffer.append(payload)
            clients = list(self.clients)
        for client in clients:
            await self._safe_send(client, payload)

    async def _safe_send(self, ws: WebSocket, payload: Dict[str, Any]) -> None:
        try:
            await ws.send_json({"type": "log", **payload})
        except Exception:
            await self.unregister(ws)


def _resolve_python() -> str:
    """Return an executable python interpreter for subprocesses."""

    exe = sys.executable
    if exe:
        path = Path(exe)
        if path.exists():
            return str(path)

    candidate = shutil.which("python3") or shutil.which("python")
    if not candidate:
        raise FileNotFoundError("Python interpreter not found for bot execution")
    return candidate


def _resolve_command_tokens(raw: Any) -> List[str]:
    """Normalise the configured bot command into a token list."""

    if isinstance(raw, (list, tuple)):
        tokens = [str(part).strip() for part in raw if str(part).strip()]
        if tokens:
            return tokens
        raise FileNotFoundError("Bot command is empty")

    value = str(raw or "").strip()
    if not value:
        value = "aster_multi_bot.py"

    # Allow JSON encoded lists from manual config edits.
    if value.startswith("[") and value.endswith("]"):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            tokens = [str(part).strip() for part in parsed if str(part).strip()]
            if tokens:
                return tokens
            raise FileNotFoundError("Bot command is empty")

    return shlex.split(value)


def _resolve_bot_command(env_cfg: Dict[str, str]) -> List[str]:
    """Build a subprocess command for launching the trading bot.

    The configuration may either point directly at a Python script or
    provide a full command with additional arguments. The function
    normalises relative paths so that they are resolved against the
    repository root and ensures the resulting command exists before
    execution.
    """

    tokens = _resolve_command_tokens(env_cfg.get("ASTER_BOT_SCRIPT"))
    if not tokens:
        raise FileNotFoundError("Bot command is empty")

    python_cmd = _resolve_python()

    def _resolve_path(token: str) -> str:
        path = Path(token)
        if not path.is_absolute():
            path = (ROOT_DIR / path).resolve()
        else:
            path = path.resolve()
        if not path.exists():
            raise FileNotFoundError(f"Bot script not found: {path}")
        return str(path)

    # If the command already specifies a Python interpreter we only need to
    # normalise the following script argument when it points inside the repo.
    first_token_lower = tokens[0].lower()
    if "python" in first_token_lower:
        resolved = [tokens[0]]
        for idx, token in enumerate(tokens[1:], start=1):
            if idx == 1 and token.endswith(".py"):
                try:
                    resolved.append(_resolve_path(token))
                    continue
                except FileNotFoundError:
                    pass
            resolved.append(token)
        return resolved

    # If only a script path is provided, run it with the detected python.
    if len(tokens) == 1:
        script_path = _resolve_path(tokens[0])
        return [python_cmd, script_path]

    # If the first token looks like a python script, prepend the interpreter.
    if tokens[0].endswith(".py"):
        script_path = _resolve_path(tokens[0])
        return [python_cmd, script_path, *tokens[1:]]

    # For arbitrary executables shipped with the repo we normalise their path
    # as well, otherwise we assume they can be resolved via PATH.
    exec_path = ROOT_DIR / tokens[0]
    if exec_path.exists():
        tokens[0] = str(exec_path.resolve())

    return tokens


class BotRunner:
    def __init__(self, loghub: LogHub) -> None:
        self.loghub = loghub
        self.process: Optional[asyncio.subprocess.Process] = None
        self._lock = asyncio.Lock()
        self._reader_task: Optional[asyncio.Task] = None
        self.started_at: Optional[float] = None

    async def status(self) -> BotStatus:
        running = self.process is not None and self.process.returncode is None
        uptime = time.time() - self.started_at if running and self.started_at else None
        pid = self.process.pid if running and self.process else None
        return BotStatus(running=running, pid=pid, started_at=self.started_at, uptime_s=uptime)

    async def start(self) -> None:
        async with self._lock:
            if self.process and self.process.returncode is None:
                raise RuntimeError("Bot is already running")
            env = os.environ.copy()
            env_cfg = CONFIG.get("env", {})
            env.update(env_cfg)
            command = _resolve_bot_command(env_cfg)
            env.setdefault("ASTER_LOGLEVEL", "DEBUG")
            try:
                await self.loghub.push(
                    "Launching bot: "
                    + " ".join(shlex.quote(part) for part in command),
                    level="system",
                )
                self.process = await asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    env=env,
                    cwd=str(ROOT_DIR),
                )
            except FileNotFoundError as exc:
                await self.loghub.push(str(exc), level="error")
                raise
            self.started_at = time.time()
            await self.loghub.push("Bot process started", level="system")
            self._reader_task = asyncio.create_task(self._pump_stdout())

    async def stop(self) -> None:
        async with self._lock:
            if not self.process:
                return
            proc = self.process
            if proc.returncode is None:
                try:
                    proc.send_signal(signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    await asyncio.wait_for(proc.wait(), timeout=10)
                except asyncio.TimeoutError:
                    proc.kill()
            self.process = None
            self.started_at = None
            await self.loghub.push("Bot process stopped", level="system")
        if self._reader_task:
            task = self._reader_task
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception as exc:  # pragma: no cover - best effort cleanup
                await self.loghub.push(
                    f"Log reader stopped with error: {exc}", level="error"
                )
            self._reader_task = None

    async def _pump_stdout(self) -> None:
        if not self.process or not self.process.stdout:
            return
        proc = self.process
        try:
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                text = line.decode("utf-8", errors="ignore").rstrip()
                await self.loghub.push(text)
        finally:
            if proc.returncode is None:
                await proc.wait()
            await self.loghub.push("Bot process finished", level="system")
            self.process = None
            self.started_at = None


loghub = LogHub()
runner = BotRunner(loghub)

app = FastAPI(title="Aster Bot Control Center")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def index() -> FileResponse:
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Dashboard build not found")
    return FileResponse(index_file)


@app.get("/api/config")
async def get_config() -> Dict[str, Any]:
    return CONFIG


@app.put("/api/config")
async def update_config(update: ConfigUpdate) -> Dict[str, Any]:
    env_cfg = CONFIG.setdefault("env", {})
    for key, value in update.env.items():
        if key not in ALLOWED_ENV_KEYS:
            raise HTTPException(status_code=400, detail=f"Unknown key: {key}")
        env_cfg[key] = str(value)
    _save_config(CONFIG)
    await loghub.push("Configuration updated", level="system")
    return CONFIG


@app.post("/api/bot/start")
async def start_bot() -> Dict[str, Any]:
    try:
        await runner.start()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"status": "started"}


@app.post("/api/bot/stop")
async def stop_bot() -> Dict[str, Any]:
    await runner.stop()
    return {"status": "stopped"}


@app.get("/api/bot/status", response_model=BotStatus)
async def bot_status() -> BotStatus:
    return await runner.status()


@app.get("/api/markets/most-traded")
async def most_traded() -> Dict[str, Any]:
    return await get_most_traded_assets()


def _read_state() -> Dict[str, Any]:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            return {}
    return {}


def _format_ts(ts: Optional[float]) -> Optional[str]:
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(ts).isoformat()
    except Exception:
        return None


def _compute_stats(history: List[Dict[str, Any]]) -> TradeStats:
    if not history:
        return TradeStats(
            count=0,
            total_pnl=0.0,
            total_r=0.0,
            win_rate=0.0,
            best_trade=None,
            worst_trade=None,
            ai_hint="No trades yet — start the bot to collect more data.",
        )
    total_pnl = sum(float(h.get("pnl", 0.0) or 0.0) for h in history)
    total_r = sum(float(h.get("pnl_r", 0.0) or 0.0) for h in history)
    wins = [h for h in history if (h.get("pnl", 0.0) or 0.0) > 0]
    losses = [h for h in history if (h.get("pnl", 0.0) or 0.0) < 0]
    count = len(history)
    win_rate = (len(wins) / count) if count else 0.0
    best = max(history, key=lambda h: h.get("pnl", 0.0))
    worst = min(history, key=lambda h: h.get("pnl", 0.0))

    hint: str
    if count < 10:
        hint = "Limited data so far — observe a few more trades before tweaking parameters."
    elif win_rate > 0.6 and total_r > 0:
        hint = "Strong performance! Consider nudging the size multiplier slightly higher."
    elif win_rate < 0.4 and total_r < 0:
        hint = "Caution: performance is lagging. Review spread/RSI filters or switch to PAPER mode for fine-tuning."
    else:
        hint = "Steady progress. Keep watching PnL and refine the RSI/ATR multipliers gradually."

    return TradeStats(
        count=count,
        total_pnl=total_pnl,
        total_r=total_r,
        win_rate=win_rate,
        best_trade=best,
        worst_trade=worst,
        ai_hint=hint,
    )


def _decision_summary(state: Dict[str, Any]) -> Dict[str, Any]:
    stats = state.get("decision_stats") or {}
    taken = int(stats.get("taken", 0) or 0)
    taken_by_bucket = {
        str(key): int(value or 0)
        for key, value in (stats.get("taken_by_bucket") or {}).items()
    }
    rejected_raw = stats.get("rejected") or {}
    rejected = {str(key): int(value or 0) for key, value in rejected_raw.items()}
    rejected_total = int(stats.get("rejected_total", 0) or 0)
    if rejected_total <= 0:
        rejected_total = sum(rejected.values())
    return {
        "taken": taken,
        "taken_by_bucket": taken_by_bucket,
        "rejected": rejected,
        "rejected_total": rejected_total,
        "last_updated": stats.get("last_updated"),
    }


@app.get("/api/trades")
async def trades() -> Dict[str, Any]:
    state = _read_state()
    history: List[Dict[str, Any]] = state.get("trade_history", [])[-200:]
    for item in history:
        item["opened_at_iso"] = _format_ts(item.get("opened_at"))
        item["closed_at_iso"] = _format_ts(item.get("closed_at"))
    open_trades = state.get("live_trades", {})
    stats = _compute_stats(history)
    decision_stats = _decision_summary(state)
    ai_budget = state.get("ai_budget", {})
    return {
        "open": open_trades,
        "history": history[::-1],
        "stats": stats.dict(),
        "decision_stats": decision_stats,
        "ai_budget": ai_budget,
    }


@app.websocket("/ws/logs")
async def ws_logs(ws: WebSocket) -> None:
    await loghub.register(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        await loghub.unregister(ws)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("dashboard_server:app", host="0.0.0.0", port=8000, reload=False)
