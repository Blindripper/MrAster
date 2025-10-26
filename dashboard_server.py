"""Aster Bot Dashboard server providing web UI for configuration, monitoring and history."""
from __future__ import annotations

import asyncio
import copy
import hashlib
import hmac
import json
import logging
import os
import re
import shlex
import shutil
import signal
import sys
import textwrap
import time
import uuid
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlencode

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
    "ASTER_INCLUDE_SYMBOLS": "",
    "ASTER_EXCLUDE_SYMBOLS": "",
    "ASTER_UNIVERSE_MAX": "40",
    "ASTER_UNIVERSE_ROTATE": "false",
    "ASTER_MIN_QUOTE_VOL_USDT": "150000",
    "ASTER_INTERVAL": "5m",
    "ASTER_HTF_INTERVAL": "30m",
    "ASTER_KLINES": "360",
    "ASTER_RSI_BUY_MIN": "51",
    "ASTER_RSI_SELL_MAX": "49",
    "ASTER_ALLOW_TREND_ALIGN": "true",
    "ASTER_ALIGN_RSI_PAD": "1.5",
    "ASTER_SPREAD_BPS_MAX": "0.009",
    "ASTER_WICKINESS_MAX": "0.985",
    "ASTER_MIN_EDGE_R": "0.06",
    "ASTER_DEFAULT_NOTIONAL": "120",
    "ASTER_RISK_PER_TRADE": "0.007",
    "ASTER_LEVERAGE": "3",
    "ASTER_PRESET_MODE": "mid",
    "ASTER_TREND_BIAS": "with",
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
    "ASTER_FUNDING_FILTER_ENABLED": "true",
    "ASTER_FUNDING_MAX_LONG": "0.0010",
    "ASTER_FUNDING_MAX_SHORT": "0.0010",
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
    "ASTER_AI_MODEL": "gpt-4o",
    "ASTER_AI_DAILY_BUDGET_USD": "20",
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


logger = logging.getLogger(__name__)


def _is_truthy(value: Optional[str]) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _fetch_position_snapshot(env: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    base = (env.get("ASTER_EXCHANGE_BASE") or "https://fapi.asterdex.com").rstrip("/")
    api_key = (env.get("ASTER_API_KEY") or "").strip()
    api_secret = (env.get("ASTER_API_SECRET") or "").strip()
    if not api_key or not api_secret:
        return {}
    if _is_truthy(env.get("ASTER_PAPER")):
        return {}

    try:
        recv_window = int(float(env.get("ASTER_RECV_WINDOW", 10000)))
    except (TypeError, ValueError):
        recv_window = 10000

    params = {"timestamp": int(time.time() * 1000), "recvWindow": recv_window}
    ordered = [(k, params[k]) for k in sorted(params)]
    qs = urlencode(ordered, doseq=True)
    signature = hmac.new(api_secret.encode(), qs.encode(), hashlib.sha256).hexdigest()
    url = f"{base}/fapi/v2/positionRisk?{qs}&signature={signature}"
    headers = {"X-MBX-APIKEY": api_key, "Content-Type": "application/x-www-form-urlencoded"}

    try:
        resp = requests.get(url, headers=headers, timeout=8)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as exc:
        logger.debug("position snapshot fetch failed: %s", exc)
        return {}

    if isinstance(payload, dict):
        positions_raw = payload.get("positions") or payload.get("data") or []
    else:
        positions_raw = payload

    snapshot: Dict[str, Dict[str, Any]] = {}
    if not isinstance(positions_raw, list):
        return snapshot

    for item in positions_raw:
        if not isinstance(item, dict):
            continue
        symbol_raw = item.get("symbol")
        if not symbol_raw:
            continue
        symbol = str(symbol_raw).upper().strip()
        if not symbol:
            continue
        position_amt = _safe_float(item.get("positionAmt"))
        if position_amt is None or abs(position_amt) < 1e-12:
            continue

        entry_price = _safe_float(item.get("entryPrice"))
        mark_price = _safe_float(item.get("markPrice"))
        unrealized = _safe_float(item.get("unRealizedProfit"))
        leverage = _safe_float(item.get("leverage"))
        notional = None
        if entry_price is not None:
            notional = abs(position_amt) * entry_price

        roe = None
        if unrealized is not None and notional and notional > 0:
            try:
                roe = (unrealized / notional) * 100.0
            except ZeroDivisionError:
                roe = None

        snapshot[symbol] = {
            "symbol": symbol,
            "positionAmt": position_amt,
            "entryPrice": entry_price,
            "markPrice": mark_price,
            "unRealizedProfit": unrealized,
            "leverage": leverage,
            "roe_percent": roe,
            "updateTime": item.get("updateTime") or item.get("update_time"),
        }

    return snapshot


POSITION_HINT_KEYS = {"entry", "entryPrice", "qty", "quantity", "positionAmt", "side", "tp", "sl", "mark"}


def _looks_like_position_record(candidate: Dict[str, Any]) -> bool:
    if not isinstance(candidate, dict):
        return False
    if any(key in candidate for key in POSITION_HINT_KEYS):
        return True
    return False


def _merge_position_record(
    record: Dict[str, Any],
    snapshot: Dict[str, Dict[str, Any]],
    fallback_symbol: Optional[str] = None,
) -> Dict[str, Any]:
    symbol_candidates = [
        record.get("symbol"),
        record.get("sym"),
        record.get("ticker"),
        record.get("pair"),
        fallback_symbol,
    ]
    symbol: Optional[str] = None
    for candidate in symbol_candidates:
        if candidate:
            symbol = str(candidate).upper().strip()
            if symbol:
                break
    if not symbol:
        return record

    extra = snapshot.get(symbol)
    if not extra:
        return record

    merged = dict(record)

    entry_price = extra.get("entryPrice")
    if entry_price is not None:
        merged["entry"] = entry_price
        merged["entryPrice"] = entry_price
        merged["entry_price"] = entry_price

    mark_price = extra.get("markPrice")
    if mark_price is not None:
        merged["mark_price"] = mark_price
        merged["markPrice"] = mark_price
        merged["mark"] = mark_price

    position_amt = extra.get("positionAmt")
    if position_amt is not None:
        merged.setdefault("qty", position_amt)
        merged.setdefault("size", position_amt)
        merged["positionAmt"] = position_amt

    unrealized = extra.get("unRealizedProfit")
    if unrealized is not None:
        merged["pnl"] = unrealized
        merged["unrealized"] = unrealized
        merged["unrealizedProfit"] = unrealized

    roe = extra.get("roe_percent")
    if roe is not None:
        merged["roe"] = roe
        merged["roe_percent"] = roe
        merged["roi"] = roe
        merged["roi_percent"] = roe

    leverage = extra.get("leverage")
    if leverage is not None:
        merged.setdefault("leverage", leverage)

    update_time = extra.get("updateTime")
    if update_time is not None:
        merged.setdefault("updateTime", update_time)

    return merged


def _merge_position_payload(payload: Any, snapshot: Dict[str, Dict[str, Any]], fallback_symbol: Optional[str] = None) -> Any:
    if isinstance(payload, dict):
        if _looks_like_position_record(payload):
            return _merge_position_record(payload, snapshot, fallback_symbol)
        merged_dict: Dict[str, Any] = {}
        for key, value in payload.items():
            merged_dict[key] = _merge_position_payload(value, snapshot, key)
        return merged_dict
    if isinstance(payload, list):
        return [_merge_position_payload(item, snapshot, fallback_symbol) for item in payload]
    return payload


def enrich_open_positions(open_payload: Any, env: Dict[str, Any]) -> Any:
    if not open_payload:
        return open_payload

    snapshot = _fetch_position_snapshot(env)
    if not snapshot:
        return open_payload

    payload_copy = copy.deepcopy(open_payload)
    return _merge_position_payload(payload_copy, snapshot)

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
    primary: Optional[str]
    fallbacks: List[str]

    if candidates:
        primary = candidates[0]
        fallbacks = candidates[1:]
    else:
        primary = None
        fallbacks = []

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


class ChatMessagePayload(BaseModel):
    role: str
    content: str


class ChatRequestPayload(BaseModel):
    message: str = Field(..., min_length=1)
    history: List[ChatMessagePayload] = Field(default_factory=list)


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


def _append_manual_trade_request(request: Dict[str, Any]) -> Dict[str, Any]:
    request = dict(request)
    attempts = 0
    while attempts < 3:
        attempts += 1
        state = _read_state()
        queue = state.setdefault("manual_trade_requests", [])
        if not isinstance(queue, list):
            queue = []
        queue.append(request)
        state["manual_trade_requests"] = queue[-100:]
        try:
            STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True))
            return request
        except Exception as exc:
            logger.debug("Failed to persist manual trade request (attempt %s): %s", attempts, exc)
            time.sleep(0.05)
    raise RuntimeError("Could not persist manual trade request")


def _append_ai_activity_entry(
    kind: str,
    headline: str,
    *,
    body: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
) -> None:
    entry: Dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "kind": str(kind or "info"),
        "headline": str(headline or kind or "info"),
    }
    if body:
        entry["body"] = str(body)
    if data is not None:
        try:
            entry["data"] = json.loads(json.dumps(data, default=lambda o: str(o)))
        except Exception:
            entry["data"] = data

    attempts = 0
    while attempts < 3:
        attempts += 1
        state = _read_state()
        feed = state.get("ai_activity")
        if not isinstance(feed, list):
            feed = []
        feed.append(entry)
        state["ai_activity"] = feed[-250:]
        try:
            STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True))
            return
        except Exception as exc:
            logger.debug("Failed to persist AI activity (attempt %s): %s", attempts, exc)
            time.sleep(0.05)


def _summarize_text(text: str, limit: int = 220) -> str:
    snippet = (text or "").strip()
    if len(snippet) <= limit:
        return snippet
    return snippet[: max(0, limit - 1)].rstrip() + "…"


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
            ai_hint="",
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


class AIChatEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._temperature_supported = True

    def _env(self) -> Dict[str, Any]:
        return self.config.get("env", {})

    def _current_state(
        self,
    ) -> Tuple[TradeStats, List[Dict[str, Any]], Dict[str, Any], List[Dict[str, Any]], Dict[str, Any]]:
        state = _read_state()
        history = state.get("trade_history", [])
        stats = _compute_stats(history)
        open_trades = state.get("live_trades", {})
        ai_activity = state.get("ai_activity", [])
        ai_budget = state.get("ai_budget", {})
        return stats, history, open_trades, ai_activity, ai_budget

    def _build_context_text(
        self,
        stats: TradeStats,
        history: List[Dict[str, Any]],
        open_trades: Dict[str, Any],
        ai_activity: List[Dict[str, Any]],
        ai_budget: Dict[str, Any],
    ) -> str:
        lines = [
            "You are the AI co-pilot for the MrAster autonomous strategy cockpit.",
            "Summarise telemetry, react to user questions, and surface concrete actions. You may queue trades for execution when the user explicitly instructs you to do so.",
            "Only queue a trade when the user clearly provides the symbol and direction; otherwise, ask a clarifying question.",
            "When you do queue a trade, include a single-line directive that starts with 'ACTION:' followed by compact JSON such as ACTION: {\"type\":\"open_trade\",\"symbol\":\"BTCUSDT\",\"side\":\"BUY\",\"size_multiplier\":1.0}.",
            "Keep the ACTION line on one line, avoid code fences, and mirror the user's language in the rest of the reply while staying concise but actionable.",
            (
                f"Performance: {stats.count} trades · total PNL {stats.total_pnl:.2f} USDT · "
                f"total R {stats.total_r:.2f} · win rate {(stats.win_rate * 100.0):.1f}%"
            ),
        ]
        if stats.ai_hint:
            lines.append(f"AI hint: {stats.ai_hint}")
        if ai_budget:
            limit = ai_budget.get("limit")
            spent = ai_budget.get("spent")
            if isinstance(limit, (int, float)) and limit:
                lines.append(f"AI budget: {spent:.2f} / {limit:.2f} USD consumed today.")
            elif isinstance(spent, (int, float)):
                lines.append(f"AI budget: {spent:.2f} USD spent today (no configured cap).")
        if open_trades:
            open_lines = []
            for sym, rec in list(open_trades.items())[:5]:
                side = rec.get("side")
                qty = rec.get("qty")
                entry = rec.get("entry")
                open_lines.append(f"{sym} {side} qty {qty} entry {entry}")
            lines.append("Open trades: " + "; ".join(open_lines))
        if history:
            recent = history[-5:]
            recent_lines = []
            for trade in reversed(recent):
                recent_lines.append(
                    f"{trade.get('symbol')} {trade.get('side')} pnl {float(trade.get('pnl', 0.0)):.2f}USDT"
                )
            lines.append("Recent history: " + "; ".join(recent_lines))
        if ai_activity:
            activity_lines = []
            for item in ai_activity[-5:][::-1]:
                headline = item.get("headline") or item.get("kind")
                body = item.get("body") or ""
                activity_lines.append(f"{headline}: {body}")
            lines.append("Latest AI activity: " + " | ".join(activity_lines))
        lines.append("Be transparent about assumptions and call out if data looks stale.")
        return "\n".join(lines)

    def _fallback_reply(
        self,
        message: str,
        stats: TradeStats,
        history: List[Dict[str, Any]],
        ai_activity: List[Dict[str, Any]],
        open_trades: Dict[str, Any],
        ai_budget: Dict[str, Any],
    ) -> str:
        env = self._env()
        parts = [
            (
                f"Currently tracking {stats.count} trades with {stats.total_pnl:.2f} USDT realised and "
                f"a win rate of {(stats.win_rate * 100.0):.1f}%."
            )
        ]
        if stats.ai_hint:
            parts.append(stats.ai_hint)
        if open_trades:
            open_fragments = []
            for sym, rec in list(open_trades.items())[:3]:
                side = rec.get("side")
                qty = rec.get("qty")
                open_fragments.append(f"{sym} {side} ({qty}) still open")
            parts.append("Open positions: " + ", ".join(open_fragments) + ".")
        if history:
            last = history[-1]
            parts.append(
                f"Last close: {last.get('symbol')} {last.get('side')} with {float(last.get('pnl', 0.0)):.2f} USDT PNL."
            )
        if ai_activity:
            latest = ai_activity[-1]
            parts.append(
                f"Latest AI event: {latest.get('headline', 'update')} — {latest.get('body', 'details pending')}"
            )
        if ai_budget:
            limit = ai_budget.get("limit")
            spent = ai_budget.get("spent")
            if isinstance(limit, (int, float)) and limit:
                parts.append(f"AI spend {spent:.2f}/{limit:.2f} USD today.")
            elif isinstance(spent, (int, float)):
                parts.append(f"AI spend {spent:.2f} USD today.")
        action_payload = self._infer_trade_action(message, env)
        if action_payload:
            parts.append(
                "Primary AI endpoint is offline; queuing obvious trade instructions heuristically."
            )
        parts.append(
            "LLM endpoint unreachable right now, so here's a heuristic response — focus on liquidity, risk, and your question"
        )
        parts.append(f"User prompt acknowledged: {message.strip()}")
        summary = " ".join(parts)
        if action_payload:
            action_json = json.dumps(action_payload, separators=(",", ":"))
            summary = f"{summary}\nACTION: {action_json}"
        return summary

    def _infer_trade_action(self, message: str, env: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not message:
            return None
        text = message.strip()
        if not text:
            return None
        lower = text.lower()
        request_triggers = (
            "open",
            "place",
            "start",
            "enter",
            "execute",
            "initiate",
            "add",
            "put on",
            "queue",
        )
        go_long_short = re.search(r"\bgo\s+(long|short)\b", lower)
        take_long_short = re.search(r"\btake\s+(the\s+)?(long|short)\b", lower)
        direct_request = any(trigger in lower for trigger in request_triggers)
        if not (direct_request or go_long_short or take_long_short or "buy" in lower or "sell" in lower):
            return None
        if "?" in text and not re.search(r"\b(can you|could you|please|let's|lets)\b", lower):
            return None
        side: Optional[str] = None
        if re.search(r"\bshort\b", lower) or re.search(r"\bsell\b", lower):
            side = "SELL"
        if re.search(r"\blong\b", lower) or re.search(r"\bbuy\b", lower):
            if side and side != "BUY":
                return None
            side = "BUY"
        if not side:
            return None
        if not (direct_request or go_long_short or take_long_short or (side == "BUY" and "buy" in lower) or (side == "SELL" and "sell" in lower)):
            return None
        symbol = self._extract_symbol_from_text(text, env)
        if not symbol:
            return None
        action: Dict[str, Any] = {"type": "open_trade", "symbol": symbol, "side": side}
        size_multiplier = self._infer_size_multiplier(lower)
        if size_multiplier is not None:
            action["size_multiplier"] = size_multiplier
        notional = self._infer_notional(lower)
        if notional is not None:
            action["notional"] = notional
        action["note"] = "Heuristic fallback while primary AI unavailable"
        return action

    def _extract_symbol_from_text(self, message: str, env: Dict[str, Any]) -> Optional[str]:
        if not message:
            return None
        default_quote = str(env.get("ASTER_QUOTE") or "USDT").upper() or "USDT"
        uppercase = message.upper()
        direct = re.findall(r"\b([A-Z]{2,12}USDT)\b", uppercase)
        if direct:
            return direct[0]
        slash_pairs = re.findall(r"\b([A-Z]{2,10})/([A-Z]{2,10})\b", uppercase)
        for base, quote in slash_pairs:
            if quote in {default_quote, "USDT", "USD"}:
                return f"{base}{quote if quote.endswith('T') else default_quote}"
        tokens = re.findall(r"[A-Za-z]{3,12}", message)
        stopwords = {
            "OPEN",
            "BUY",
            "SELL",
            "LONG",
            "SHORT",
            "PLEASE",
            "SMALL",
            "MEDIUM",
            "LARGE",
            "TINY",
            "POSITION",
            "TRADE",
            "ENTRY",
            "EXIT",
            "CAN",
            "YOU",
            "ME",
            "FOR",
            "THE",
            "A",
            "AN",
            "LET",
            "LETS",
            "US",
            "NOW",
            "TODAY",
            "PLEASE",
            "QUEUE",
            "PLACE",
            "START",
            "INITIATE",
            "EXECUTE",
            "ADD",
            "PUT",
            "ON",
            "SMALLER",
            "BIGGER",
            "HEDGE",
        }
        filtered_tokens: List[str] = []
        for raw in tokens:
            token = raw.upper()
            if token in stopwords:
                continue
            filtered_tokens.append(token)
        for token in filtered_tokens:
            if token.endswith(default_quote):
                return token
        for token in filtered_tokens:
            if len(token) < 2:
                continue
            if token.endswith("USD"):
                return token + "T"
            if token == default_quote:
                continue
            return f"{token}{default_quote}"
        return None

    def _infer_size_multiplier(self, lower: str) -> Optional[float]:
        size_map = {
            "tiny": 0.25,
            "small": 0.5,
            "starter": 0.5,
            "light": 0.5,
            "half": 0.6,
            "medium": 1.0,
            "base": 1.0,
            "standard": 1.0,
            "full": 1.2,
            "large": 1.5,
            "bigger": 1.5,
            "heavy": 1.7,
            "aggressive": 1.8,
            "double": 2.0,
            "max": 2.0,
        }
        for keyword, value in size_map.items():
            if keyword in lower:
                return value
        mult_match = re.search(r"(\d+(?:\.\d+)?)x", lower)
        if mult_match:
            try:
                return float(mult_match.group(1))
            except ValueError:
                return None
        return None

    def _infer_notional(self, lower: str) -> Optional[float]:
        notional_match = re.search(r"(\d+(?:\.\d+)?)\s*(usdt|usd|dollars?)\b", lower)
        if notional_match:
            try:
                return float(notional_match.group(1))
            except ValueError:
                return None
        currency_match = re.search(r"\b(?:notional|size|amount)\s*(\d+(?:\.\d+)?)\b", lower)
        if currency_match:
            try:
                return float(currency_match.group(1))
            except ValueError:
                return None
        return None

    def _format_local_reply(self, text: str) -> str:
        lines = []
        for segment in text.split("\n"):
            stripped = segment.strip()
            if not stripped:
                continue
            if stripped.upper().startswith("ACTION:"):
                lines.append(stripped)
            else:
                lines.append(textwrap.fill(stripped, width=96))
        return "\n".join(lines)

    def _extract_action(self, text: str) -> Optional[Dict[str, Any]]:
        if not text:
            return None
        action_pattern = re.compile(r"ACTION:\s*(\{.*\})", re.IGNORECASE)
        for raw_line in text.splitlines():
            line = raw_line.strip().strip("`>-")
            match = action_pattern.search(line)
            if not match:
                continue
            payload_text = match.group(1).strip().rstrip("`")
            try:
                return json.loads(payload_text)
            except json.JSONDecodeError:
                continue
        return None

    def _queue_trade_action(
        self, action: Dict[str, Any], message: str
    ) -> Optional[Dict[str, Any]]:
        if not isinstance(action, dict):
            return None
        action_type = str(action.get("type") or "").strip().lower()
        if action_type != "open_trade":
            return None
        symbol = str(action.get("symbol") or "").upper().strip()
        side = str(action.get("side") or "").upper().strip()
        if not symbol or side not in {"BUY", "SELL"}:
            return None
        request: Dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "type": "open_trade",
            "symbol": symbol,
            "side": side,
            "requested_at": time.time(),
            "status": "pending",
            "source": "chat",
            "message": message,
            "payload": action,
        }
        size_mult = action.get("size_multiplier")
        if size_mult is not None:
            try:
                request["size_multiplier"] = float(size_mult)
            except (TypeError, ValueError):
                pass
        notional = action.get("notional")
        if notional is not None:
            try:
                request["notional"] = float(notional)
            except (TypeError, ValueError):
                pass
        note = action.get("note")
        if isinstance(note, str) and note.strip():
            request["note"] = note.strip()
        try:
            stored = _append_manual_trade_request(request)
        except Exception as exc:
            logger.debug("Failed to queue manual trade request: %s", exc)
            return None
        return {
            "id": stored["id"],
            "symbol": stored["symbol"],
            "side": stored["side"],
            "status": stored["status"],
        }

    def respond(self, message: str, history_payload: List[ChatMessagePayload]) -> Dict[str, Any]:
        stats, history, open_trades, ai_activity, ai_budget = self._current_state()
        fallback = self._fallback_reply(message, stats, history, ai_activity, open_trades, ai_budget)
        env = self._env()
        api_key = (env.get("ASTER_OPENAI_API_KEY") or "").strip()
        model = (env.get("ASTER_AI_MODEL") or "gpt-4o").strip() or "gpt-4o"
        if not api_key:
            return {"reply": self._format_local_reply(fallback), "model": "local", "source": "fallback"}

        context_text = self._build_context_text(stats, history, open_trades, ai_activity, ai_budget)
        messages: List[Dict[str, str]] = [{"role": "system", "content": context_text}]
        for item in history_payload[-6:]:
            role = item.role.lower().strip()
            if role not in {"user", "assistant"}:
                continue
            messages.append({"role": role, "content": item.content})
        messages.append({"role": "user", "content": message})

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 400,
        }

        if self._temperature_supported:
            dash_temp = os.getenv("ASTER_DASHBOARD_AI_TEMPERATURE")
            if dash_temp:
                try:
                    parsed_temp = float(dash_temp)
                except ValueError:
                    parsed_temp = None
                    log.debug("Invalid ASTER_DASHBOARD_AI_TEMPERATURE=%s — ignoring", dash_temp)
                else:
                    if abs(parsed_temp - 1.0) > 1e-6:
                        payload["temperature"] = parsed_temp
            else:
                payload["temperature"] = 0.4

        _append_ai_activity_entry(
            "chat",
            "Chat prompt sent to AI",
            body=_summarize_text(message, 260),
            data={
                "source": "dashboard_chat",
                "direction": "outbound",
                "history_messages": len(messages) - 1,
            },
        )

        try:
            attempt = 0
            while True:
                resp = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30,
                )
                if resp.status_code < 400:
                    break
                body_snippet = (resp.text or "")[:160]
                lower_body = body_snippet.lower()
                if (
                    self._temperature_supported
                    and "temperature" in payload
                    and "temperature" in lower_body
                    and "default" in lower_body
                    and attempt == 0
                ):
                    payload.pop("temperature", None)
                    attempt += 1
                    self._temperature_supported = False
                    log.debug("Dashboard AI model rejected temperature override; retrying without it.")
                    continue
                resp.raise_for_status()

            data = resp.json()
            choices = data.get("choices") or []
            reply = choices[0]["message"]["content"] if choices else ""
            reply_text = (reply or "").strip()
            if not reply_text:
                reply_text = self._format_local_reply(fallback)
            action_payload = self._extract_action(reply_text)
            queued_action = self._queue_trade_action(action_payload, message) if action_payload else None
            response: Dict[str, Any] = {
                "reply": reply_text,
                "model": model,
                "source": "openai",
                "usage": data.get("usage"),
            }
            if queued_action:
                response["queued_action"] = queued_action

            log_data: Dict[str, Any] = {
                "source": "dashboard_chat",
                "direction": "inbound",
                "model": model,
            }
            usage = data.get("usage")
            if usage:
                log_data["usage"] = usage
            if queued_action:
                log_data["queued_action"] = queued_action
            _append_ai_activity_entry(
                "chat",
                "AI chat response received",
                body=_summarize_text(reply_text, 260),
                data=log_data,
            )
            return response
        except Exception as exc:
            awaitable = getattr(loghub, "push", None)
            if awaitable:
                try:
                    asyncio.create_task(loghub.push(f"AI chat fallback: {exc}", level="warning"))
                except RuntimeError:
                    pass
            reply_text = self._format_local_reply(fallback)
            action_payload = self._extract_action(reply_text)
            queued_action = self._queue_trade_action(action_payload, message) if action_payload else None
            response = {"reply": reply_text, "model": model, "source": "fallback"}
            if queued_action:
                response["queued_action"] = queued_action
            _append_ai_activity_entry(
                "warning",
                "Chat fallback response used",
                body=_summarize_text(reply_text, 260),
                data={
                    "source": "dashboard_chat",
                    "direction": "inbound",
                    "model": model,
                    "error": str(exc),
                },
            )
            return response


chat_engine = AIChatEngine(CONFIG)

@app.get("/api/trades")
async def trades() -> Dict[str, Any]:
    state = _read_state()
    history: List[Dict[str, Any]] = state.get("trade_history", [])[-200:]
    for item in history:
        item["opened_at_iso"] = _format_ts(item.get("opened_at"))
        item["closed_at_iso"] = _format_ts(item.get("closed_at"))
    open_trades = state.get("live_trades", {})
    env_cfg = CONFIG.get("env", {})
    try:
        enriched_open = await asyncio.to_thread(enrich_open_positions, open_trades, env_cfg)
    except Exception as exc:
        logger.debug("active position enrichment failed: %s", exc)
        enriched_open = open_trades
    stats = _compute_stats(history)
    decision_stats = _decision_summary(state)
    ai_budget = state.get("ai_budget", {})
    ai_activity_raw = state.get("ai_activity", [])
    if isinstance(ai_activity_raw, list):
        # Preserve chronological ordering so analysis entries appear before
        # subsequent execution events in the feed. Only the most recent
        # window is returned to keep the payload compact.
        ai_activity = list(ai_activity_raw[-120:])
    else:
        ai_activity = []
    return {
        "open": enriched_open,
        "history": history[::-1],
        "stats": stats.dict(),
        "decision_stats": decision_stats,
        "ai_budget": ai_budget,
        "ai_activity": ai_activity,
    }


@app.post("/api/ai/chat")
async def ai_chat(payload: ChatRequestPayload) -> Dict[str, Any]:
    message = (payload.message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    return chat_engine.respond(message, payload.history)


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
