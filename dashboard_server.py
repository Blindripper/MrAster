"""Aster Bot Dashboard server providing web UI for configuration, monitoring and history."""
from __future__ import annotations

import asyncio
import copy
import hashlib
import hmac
import json
import logging
import math
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

SHARE_IMAGES = {
    "high": ROOT_DIR / "high.jpg",
    "low": ROOT_DIR / "low.jpg",
}

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
    "ASTER_UNIVERSE_MAX": "0",
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
    "ASTER_MAX_OPEN_GLOBAL": "0",
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
    "ASTER_CHAT_OPENAI_API_KEY": "",
}

ALLOWED_ENV_KEYS = set(ENV_DEFAULTS.keys())


REALIZED_PNL_MATCH_PADDING_SECONDS = 180.0


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
log = logging.getLogger("dashboard.ai.chat")


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


def _fetch_realized_pnl_entries(env: Dict[str, Any], limit: int = 400) -> List[Dict[str, Any]]:
    base = (env.get("ASTER_EXCHANGE_BASE") or "https://fapi.asterdex.com").rstrip("/")
    api_key = (env.get("ASTER_API_KEY") or "").strip()
    api_secret = (env.get("ASTER_API_SECRET") or "").strip()
    if not api_key or not api_secret:
        return []
    if _is_truthy(env.get("ASTER_PAPER")):
        return []

    try:
        recv_window = int(float(env.get("ASTER_RECV_WINDOW", 10000)))
    except (TypeError, ValueError):
        recv_window = 10000

    try:
        limit_val = int(limit)
    except (TypeError, ValueError):
        limit_val = 400
    limit_val = max(50, min(limit_val, 1000))

    params = {
        "timestamp": int(time.time() * 1000),
        "recvWindow": recv_window,
        "incomeType": "REALIZED_PNL",
        "limit": limit_val,
    }
    ordered = [(k, params[k]) for k in sorted(params)]
    qs = urlencode(ordered, doseq=True)
    signature = hmac.new(api_secret.encode(), qs.encode(), hashlib.sha256).hexdigest()
    url = f"{base}/fapi/v1/income?{qs}&signature={signature}"
    headers = {"X-MBX-APIKEY": api_key, "Content-Type": "application/x-www-form-urlencoded"}

    try:
        resp = requests.get(url, headers=headers, timeout=8)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as exc:
        logger.debug("realized pnl fetch failed: %s", exc)
        return []

    if isinstance(payload, dict):
        if isinstance(payload.get("rows"), list):
            entries = payload["rows"]
        elif isinstance(payload.get("data"), list):
            entries = payload["data"]
        else:
            lists = [value for value in payload.values() if isinstance(value, list)]
            entries = lists[0] if lists else []
    else:
        entries = payload

    results: List[Dict[str, Any]] = []
    if not isinstance(entries, list):
        return results

    for item in entries:
        if not isinstance(item, dict):
            continue
        symbol_raw = item.get("symbol") or item.get("asset")
        if not symbol_raw:
            continue
        symbol = str(symbol_raw).upper().strip()
        if not symbol:
            continue

        income_val = _safe_float(item.get("income"))
        if income_val is None:
            income_val = _safe_float(item.get("realizedPnl"))
        if income_val is None:
            income_val = _safe_float(item.get("amount"))
        if income_val is None:
            continue

        time_raw = item.get("time") or item.get("T") or item.get("timestamp") or item.get("tradeTime")
        if time_raw is None:
            continue
        time_val = _safe_float(time_raw)
        if time_val is None:
            continue
        if time_val > 1e12:
            time_val /= 1000.0
        elif time_val > 1e10:
            time_val /= 1000.0

        entry: Dict[str, Any] = {
            "symbol": symbol,
            "income": income_val,
            "time": time_val,
        }

        for key in ("incomeType", "tradeId", "orderId", "positionSide", "matchOrderId"):
            if key in item:
                entry[key] = item.get(key)

        results.append(entry)

    results.sort(key=lambda e: e["time"])
    return results


def _parse_trade_timestamp(trade: Dict[str, Any], numeric_key: str, iso_key: str) -> Optional[float]:
    value = _safe_float(trade.get(numeric_key))
    if value is not None and value > 0:
        return value
    iso_value = trade.get(iso_key)
    if isinstance(iso_value, str) and iso_value:
        try:
            return datetime.fromisoformat(iso_value).timestamp()
        except ValueError:
            return None
    return None


def _merge_realized_pnl(history: List[Dict[str, Any]], realized: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not history or not realized:
        return history

    timeline: Dict[str, List[Dict[str, Any]]] = {}
    for entry in realized:
        symbol = entry.get("symbol")
        income = entry.get("income")
        ts = entry.get("time")
        if not symbol or income is None or ts is None:
            continue
        timeline.setdefault(symbol, []).append(entry)

    for entries in timeline.values():
        entries.sort(key=lambda item: item.get("time", 0))

    merged: List[Dict[str, Any]] = []
    for trade in history:
        record = dict(trade)
        symbol_raw = record.get("symbol")
        symbol = str(symbol_raw).upper().strip() if symbol_raw else ""
        if symbol and symbol in timeline:
            open_ts = _parse_trade_timestamp(record, "opened_at", "opened_at_iso")
            close_ts = _parse_trade_timestamp(record, "closed_at", "closed_at_iso")
            if close_ts is None and open_ts is not None:
                close_ts = open_ts
            if open_ts is None and close_ts is not None:
                open_ts = close_ts

            if open_ts is not None and close_ts is not None:
                window_start = min(open_ts, close_ts) - REALIZED_PNL_MATCH_PADDING_SECONDS
                window_end = max(open_ts, close_ts) + REALIZED_PNL_MATCH_PADDING_SECONDS
                candidates = timeline.get(symbol, [])
                matched: List[Dict[str, Any]] = []
                remaining: List[Dict[str, Any]] = []
                for entry in candidates:
                    ts = entry.get("time")
                    if ts is None:
                        continue
                    if window_start <= ts <= window_end:
                        matched.append(entry)
                    else:
                        remaining.append(entry)

                if matched:
                    realized_sum = sum(_safe_float(e.get("income")) or 0.0 for e in matched)
                    if record.get("pnl") is not None and "estimated_pnl" not in record:
                        try:
                            record["estimated_pnl"] = float(record.get("pnl") or 0.0)
                        except (TypeError, ValueError):
                            record["estimated_pnl"] = record.get("pnl")
                    record["realized_pnl"] = realized_sum
                    timeline[symbol] = remaining
        merged.append(record)

    return merged


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


def _fetch_most_traded_from_binance(limit: int = 20) -> List[Dict[str, Any]]:
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


class ProposalExecutionRequest(BaseModel):
    proposal_id: str = Field(..., min_length=4, alias="proposalId")

    class Config:
        allow_population_by_field_name = True


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


@app.get("/share/{variant}")
async def get_share_image(variant: str) -> FileResponse:
    key = (variant or "").strip().lower()
    path = SHARE_IMAGES.get(key)
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail="Share image not found")
    return FileResponse(path)


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
            detail = f"{entry['kind']} | {entry['headline']}"
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            if loop and not loop.is_closed():
                loop.create_task(loghub.push(f"AI_FEED {detail}", level="debug"))
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
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    except Exception:
        return None


def _parse_activity_ts(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except Exception:
            return None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            return None
    return None


def _summarize_ai_requests(
    ai_activity: List[Dict[str, Any]],
    limit: int = 40,
) -> List[Dict[str, Any]]:
    requests: Dict[str, Dict[str, Any]] = {}
    for entry in ai_activity:
        if not isinstance(entry, dict):
            continue
        data = entry.get("data")
        if not isinstance(data, dict):
            continue
        raw_request_id = data.get("request_id")
        request_id = None
        if isinstance(raw_request_id, str):
            request_id = raw_request_id.strip() or None
        elif raw_request_id is not None:
            request_id = str(raw_request_id)
        symbol_hint = str(data.get("symbol") or "").strip().upper()
        side_hint = str(data.get("side") or "").strip().upper()
        fallback_key = None
        if symbol_hint:
            fallback_side = side_hint or "UNKNOWN"
            fallback_key = f"{symbol_hint}::{fallback_side}"

        key = request_id or fallback_key
        if not key:
            continue
        record = requests.get(key)
        if record is None and request_id and fallback_key and fallback_key in requests:
            # Merge historical placeholder keyed by symbol into the resolved request id
            record = requests.pop(fallback_key)
            if record is not None:
                key = request_id
                record["id"] = request_id
                record["request_id"] = request_id
                requests[key] = record
        if record is None:
            record = {
                "id": key,
                "request_id": request_id,
                "symbol": symbol_hint,
                "side": side_hint or None,
                "status": "pending",
                "decision": None,
                "take": None,
                "confidence": None,
                "size_multiplier": None,
                "sl_multiplier": None,
                "tp_multiplier": None,
                "notes": [],
                "decision_reason": None,
                "decision_note": None,
                "risk_note": None,
                "events": [],
                "created_at": None,
                "updated_at": None,
            }
            requests[key] = record
        else:
            if request_id and not record.get("request_id"):
                record["request_id"] = request_id
        if symbol_hint and not record.get("symbol"):
            record["symbol"] = symbol_hint
        if side_hint and not record.get("side"):
            record["side"] = side_hint
        ts = _parse_activity_ts(entry.get("ts"))
        ts_iso = ts.isoformat() if ts else None
        if ts_iso:
            record["updated_at"] = ts_iso
            if record.get("created_at") is None:
                record["created_at"] = ts_iso

        kind = str(entry.get("kind") or "info").lower()
        record["events"].append(
            {
                "kind": kind,
                "headline": entry.get("headline"),
                "body": entry.get("body"),
                "ts": ts_iso,
            }
        )

        numeric_fields = {
            "confidence": "confidence",
            "size_multiplier": "size_multiplier",
            "sl_multiplier": "sl_multiplier",
            "tp_multiplier": "tp_multiplier",
        }
        for source_key, target_key in numeric_fields.items():
            value = data.get(source_key)
            try:
                numeric_value = float(value)
            except (TypeError, ValueError):
                continue
            if not math.isfinite(numeric_value):
                continue
            record[target_key] = numeric_value

        text_fields = {
            "decision_reason": "decision_reason",
            "decision_note": "decision_note",
            "risk_note": "risk_note",
        }
        for source_key, target_key in text_fields.items():
            raw_value = data.get(source_key)
            if isinstance(raw_value, str):
                cleaned = " ".join(raw_value.split())
                if cleaned:
                    record[target_key] = cleaned

        raw_notes = data.get("notes")
        if isinstance(raw_notes, list):
            for note in raw_notes:
                if isinstance(note, str):
                    cleaned = " ".join(note.split())
                    if cleaned and cleaned not in record["notes"]:
                        record["notes"].append(cleaned)

        decision_label = data.get("decision")
        if isinstance(decision_label, str) and decision_label.strip():
            record["decision"] = decision_label.strip()

        if kind == "query":
            if record.get("status") not in {"accepted", "rejected"}:
                record["status"] = "pending"
        elif kind == "response":
            if record.get("status") not in {"accepted", "rejected"}:
                record["status"] = "responded"
        elif kind == "decision":
            take_value = data.get("take")
            if isinstance(take_value, bool):
                record["take"] = take_value
            if record.get("decision") is None:
                headline = entry.get("headline")
                if isinstance(headline, str) and headline.strip():
                    record["decision"] = headline.strip()
            if record.get("take") is True:
                record["status"] = "accepted"
            elif record.get("take") is False:
                record["status"] = "rejected"
            else:
                decision_text = (record.get("decision") or "").lower()
                if "reject" in decision_text:
                    record["status"] = "rejected"
                elif any(keyword in decision_text for keyword in ("approve", "accept", "take")):
                    record["status"] = "accepted"
                else:
                    record["status"] = "decided"
        elif kind == "analysis" and record.get("status") == "pending":
            record["status"] = "analysed"

    summaries = list(requests.values())
    summaries.sort(key=lambda item: item.get("updated_at") or "", reverse=True)
    if limit > 0:
        summaries = summaries[:limit]
    for item in summaries:
        notes = item.get("notes")
        if isinstance(notes, list) and not notes:
            item["notes"] = []
    return summaries


def _extract_trade_pnl(trade: Dict[str, Any]) -> float:
    if not isinstance(trade, dict):
        return 0.0
    for key in ("realized_pnl", "realizedPnl", "pnl"):
        value = trade.get(key)
        if value is None:
            continue
        numeric = _safe_float(value)
        if numeric is not None:
            return numeric
    return 0.0


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
    total_pnl = sum(_extract_trade_pnl(h) for h in history)
    total_r = sum(float(h.get("pnl_r", 0.0) or 0.0) for h in history)
    wins = [h for h in history if _extract_trade_pnl(h) > 0]
    losses = [h for h in history if _extract_trade_pnl(h) < 0]
    count = len(history)
    win_rate = (len(wins) / count) if count else 0.0
    best = max(history, key=_extract_trade_pnl)
    worst = min(history, key=_extract_trade_pnl)

    hint: str
    if count < 10:
        hint = ""
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


def _friendly_decision_reason(reason: Optional[str]) -> Optional[str]:
    if reason is None:
        return None
    token = str(reason).strip()
    if not token:
        return None
    lookup = {
        "sentinel_block": "Sentinel block",
        "sentinel_veto": "Sentinel veto",
        "policy_filter": "Policy filter",
        "fallback_rules": "Fallback rules",
        "no_signal": "No valid signal",
        "plan_timeout": "AI plan timeout",
        "plan_pending": "AI plan pending",
        "trend_timeout": "Trend scan timeout",
        "trend_pending": "Trend scan pending",
        "ai_trend_skip": "AI declined trend setup",
        "ai_trend_invalid": "AI returned invalid trend setup",
    }
    normalized = token.lower()
    if normalized in lookup:
        return lookup[normalized]
    return token.replace("_", " ").strip().capitalize()


def _cumulative_summary(state: Dict[str, Any]) -> Dict[str, Any]:
    metrics = state.get("cumulative_metrics") or {}
    summary = {
        "total_trades": int(metrics.get("total_trades", 0) or 0),
        "total_pnl": float(metrics.get("total_pnl", 0.0) or 0.0),
        "wins": int(metrics.get("wins", 0) or 0),
        "losses": int(metrics.get("losses", 0) or 0),
        "draws": int(metrics.get("draws", 0) or 0),
    }
    updated_at = metrics.get("updated_at")
    if updated_at is not None:
        summary["updated_at"] = updated_at
    return summary


class AIChatEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._temperature_supported = True
        self._market_universe_cache: Dict[str, Any] = {"symbols": [], "ts": 0.0}

    @staticmethod
    def _split_symbols(value: Optional[str]) -> List[str]:
        if not value:
            return []
        return [part.strip().upper() for part in str(value).split(",") if part.strip()]

    @staticmethod
    def _parse_symbols_from_html(text: str, default_quote: str) -> List[str]:
        try:
            matches = re.findall(r'data-symbol="([A-Z0-9:_-]+)"', text, flags=re.IGNORECASE)
            if not matches:
                matches = re.findall(r'"symbol"\s*:\s*"([A-Z0-9:_-]+)"', text, flags=re.IGNORECASE)
        except re.error:
            return []
        symbols = {m.upper() for m in matches}
        if default_quote:
            q = default_quote.upper()
            symbols = {s for s in symbols if s.endswith(q)}
        return sorted(symbols)

    def _fetch_markets_symbols(self, env: Dict[str, Any]) -> List[str]:
        base = (env.get("ASTER_EXCHANGE_BASE") or ENV_DEFAULTS.get("ASTER_EXCHANGE_BASE") or "").rstrip("/")
        quote = (env.get("ASTER_QUOTE") or ENV_DEFAULTS.get("ASTER_QUOTE", "")).strip()
        markets_url = (env.get("ASTER_MARKETS_URL") or "").strip()
        if not markets_url:
            if base:
                markets_url = f"{base}/fapi/v1/exchangeInfo"
            else:
                return []
        try:
            resp = requests.get(markets_url, timeout=10)
            resp.raise_for_status()
        except Exception as exc:
            log.debug("Could not fetch markets from %s: %s", markets_url, exc)
            return []

        try:
            payload = resp.json()
        except ValueError:
            return self._parse_symbols_from_html(resp.text, quote)

        symbols: List[str] = []
        q = quote.upper() if quote else ""
        for entry in payload.get("symbols", []):
            sym = str(entry.get("symbol", "")).upper()
            if not sym:
                continue
            if q and str(entry.get("quoteAsset", "")).upper() != q:
                continue
            status = str(entry.get("status", "")).upper()
            if status and status != "TRADING":
                continue
            symbols.append(sym)

        if not symbols:
            return self._parse_symbols_from_html(resp.text, quote)

        return sorted(set(symbols))

    def _market_universe_symbols(self) -> List[str]:
        now = time.time()
        cache = self._market_universe_cache
        if cache and cache.get("symbols") and now - float(cache.get("ts", 0.0)) < 1800:
            return list(cache.get("symbols", []))

        env = self._env()
        include = self._split_symbols(env.get("ASTER_INCLUDE_SYMBOLS"))
        if include:
            symbols = include
        else:
            symbols = self._fetch_markets_symbols(env)
        exclude = set(self._split_symbols(env.get("ASTER_EXCLUDE_SYMBOLS")))
        if exclude:
            symbols = [sym for sym in symbols if sym not in exclude]

        unique_sorted = sorted(dict.fromkeys(sym for sym in symbols if sym))
        self._market_universe_cache = {"symbols": unique_sorted, "ts": now}
        return list(unique_sorted)

    @staticmethod
    def _ensure_analysis_follow_up(text: str) -> str:
        follow_up = (
            "To place a trade for you, click \"Take trade proposals\" or provide the symbol, direction (LONG/SHORT), "
            "entry plan (market or limit with price), stop-loss, take-profit, and desired position size or notional. "
            "Should the bot execute trades based on this analysis once you share those details?"
        )
        normalized = text.lower()
        if "should the bot" in normalized and "take trade proposals" in normalized:
            return text
        if not text.strip():
            return follow_up
        trimmed = text.rstrip()
        joiner = "\n\n" if trimmed else ""
        return f"{trimmed}{joiner}{follow_up}"

    def _extract_trade_proposals(self, text: str) -> List[Dict[str, Any]]:
        if not text:
            return []
        proposals: List[Dict[str, Any]] = []
        action_pattern = re.compile(r"ACTION:\s*(\{.*\})", re.IGNORECASE)
        for raw_line in text.splitlines():
            line = raw_line.strip().strip("`>-")
            match = action_pattern.search(line)
            if not match:
                continue
            payload_text = match.group(1).strip().rstrip("`")
            try:
                payload = json.loads(payload_text)
            except json.JSONDecodeError:
                continue
            if not isinstance(payload, dict):
                continue
            action_type = str(payload.get("type") or "").strip().lower()
            if action_type not in {"propose_trade", "trade_proposal", "trade_plan"}:
                continue
            proposals.append(payload)

        if proposals:
            return proposals

        structured = self._extract_structured_trade_proposals(text)
        if structured:
            proposals.extend(structured)
        return proposals

    def _default_proposal_notional(self) -> Optional[float]:
        env = self._env()
        candidates = (
            env.get("ASTER_AI_DEFAULT_NOTIONAL"),
            env.get("ASTER_DEFAULT_NOTIONAL"),
            ENV_DEFAULTS.get("ASTER_AI_DEFAULT_NOTIONAL"),
            ENV_DEFAULTS.get("ASTER_DEFAULT_NOTIONAL"),
        )
        for raw in candidates:
            value = self._safe_float(raw)
            if value and value > 0:
                return value
        return None

    @staticmethod
    def _extract_numbers(text: str) -> List[float]:
        if not text:
            return []
        try:
            matches = re.findall(r"-?\d+(?:[.,]\d+)?", text)
        except re.error:
            return []
        numbers: List[float] = []
        for raw in matches:
            normalized = raw.replace(",", "")
            try:
                numbers.append(float(normalized))
            except ValueError:
                continue
        return numbers

    def _extract_structured_trade_proposals(self, text: str) -> List[Dict[str, Any]]:
        try:
            thesis_matches = list(re.finditer(r"\*\*Thesis\*\*:\s*", text, flags=re.IGNORECASE))
        except re.error:
            return []
        if not thesis_matches:
            return []

        default_notional = self._default_proposal_notional()
        if default_notional is None:
            return []

        trade_input_hints: Dict[str, str] = {}
        try:
            for sym, side in re.findall(r"\*\*([A-Z0-9]{3,})\s+(Long|Short)\*\*", text, flags=re.IGNORECASE):
                trade_input_hints[sym.upper()] = side.upper()
        except re.error:
            trade_input_hints = {}

        try:
            idea_headers = list(re.finditer(r"\*\*(Long|Short)\s+Idea\*\*", text, flags=re.IGNORECASE))
        except re.error:
            idea_headers = []

        proposals: List[Dict[str, Any]] = []

        def header_direction(position: int) -> Optional[str]:
            direction: Optional[str] = None
            for header in idea_headers:
                if header.start() < position:
                    direction = header.group(1).upper()
                else:
                    break
            return direction

        for idx, match in enumerate(thesis_matches):
            start = match.start()
            end = thesis_matches[idx + 1].start() if idx + 1 < len(thesis_matches) else len(text)
            block = text[start:end]
            thesis_line_match = re.search(r"\*\*Thesis\*\*:\s*(.+)", block, re.IGNORECASE)
            if not thesis_line_match:
                continue
            thesis_line = thesis_line_match.group(1).strip()
            if not thesis_line:
                continue

            symbol: Optional[str] = None
            symbol_line_match = re.search(r"\*\*Symbol\*\*:\s*([A-Z0-9:_\-/]+)", block, re.IGNORECASE)
            if symbol_line_match:
                raw_symbol = symbol_line_match.group(1).strip()
                if raw_symbol:
                    sanitized = re.sub(r"[^A-Z0-9:_-]", "", raw_symbol.upper())
                    if sanitized:
                        symbol = sanitized.replace("/", "")
            try:
                symbol_candidates = re.findall(r"\b([A-Z]{2,}[A-Z0-9]{0,})\b", thesis_line)
            except re.error:
                symbol_candidates = []
            for candidate in symbol_candidates:
                normalized_candidate = candidate.upper().replace("/", "")
                if normalized_candidate in {"LONG", "SHORT"}:
                    continue
                if normalized_candidate.endswith(("USDT", "USDC", "USD", "PERP")) or len(normalized_candidate) >= 6:
                    symbol = normalized_candidate
                    break
            if not symbol:
                continue

            entry_line_match = re.search(r"Entry[^\n]*", block, re.IGNORECASE)
            entry_numbers = self._extract_numbers(entry_line_match.group(0)) if entry_line_match else []
            entry_price: Optional[float] = None
            entry_label: Optional[str] = None
            if entry_numbers:
                if len(entry_numbers) >= 2:
                    low, high = sorted(entry_numbers[:2])
                    entry_price = (low + high) / 2.0
                    entry_label = f"Zone {low:.2f}-{high:.2f}"
                else:
                    entry_price = entry_numbers[0]
            entry_kind = "limit" if entry_price is not None else "market"

            invalidation_match = re.search(r"Invalidation\*\*:\s*([^\n]+)", block, re.IGNORECASE)
            invalidation_numbers = (
                self._extract_numbers(invalidation_match.group(1)) if invalidation_match else []
            )
            stop_loss = invalidation_numbers[0] if invalidation_numbers else None

            target_match = re.search(r"Target\*\*:\s*([^\n]+)", block, re.IGNORECASE)
            target_numbers = self._extract_numbers(target_match.group(1)) if target_match else []
            take_profit = target_numbers[0] if target_numbers else None

            if stop_loss is None or take_profit is None:
                continue

            direction: Optional[str] = trade_input_hints.get(symbol)
            if not direction:
                header_hint = header_direction(start)
                if header_hint:
                    direction = header_hint
            if not direction:
                if re.search(r"\bshort\b", thesis_line, re.IGNORECASE) or re.search(
                    r"\bbearish\b", block, re.IGNORECASE
                ):
                    direction = "SHORT"
                elif re.search(r"\blong\b", thesis_line, re.IGNORECASE) or re.search(
                    r"\bbullish\b", block, re.IGNORECASE
                ):
                    direction = "LONG"

            if not direction and entry_price is not None:
                if take_profit > entry_price and (stop_loss < entry_price if stop_loss is not None else False):
                    direction = "LONG"
                elif take_profit < entry_price and (stop_loss > entry_price if stop_loss is not None else False):
                    direction = "SHORT"

            if not direction and entry_price is not None:
                direction = "LONG" if take_profit >= entry_price else "SHORT"

            if not direction:
                continue

            note_parts = [thesis_line]
            catalysts_match = re.search(r"Catalysts\*\*:\s*([^\n]+)", block, re.IGNORECASE)
            if catalysts_match:
                catalysts = catalysts_match.group(1).strip()
                if catalysts:
                    note_parts.append(f"Catalysts: {catalysts}")
            caveats_match = re.search(r"Data Caveats\*\*:\s*([^\n]+)", block, re.IGNORECASE)
            if caveats_match:
                caveats = caveats_match.group(1).strip()
                if caveats:
                    note_parts.append(f"Data Caveats: {caveats}")
            note = " | ".join(note_parts)
            if note and len(note) > 320:
                note = note[:317] + "…"

            timeframe: Optional[str] = None
            timeframe_match = re.search(r"Time\s*-?\s*frame\*\*:\s*([^\n]+)", block, re.IGNORECASE)
            if timeframe_match:
                raw_timeframe = timeframe_match.group(1)
                if isinstance(raw_timeframe, str):
                    cleaned = raw_timeframe.strip()
                    if cleaned:
                        timeframe = cleaned
            else:
                horizon_match = re.search(r"(Time|Holding)\s*Horizon\*\*:\s*([^\n]+)", block, re.IGNORECASE)
                if horizon_match:
                    raw_timeframe = horizon_match.group(2)
                    if isinstance(raw_timeframe, str):
                        cleaned = raw_timeframe.strip()
                        if cleaned:
                            timeframe = cleaned

            proposal: Dict[str, Any] = {
                "type": "propose_trade",
                "symbol": symbol,
                "direction": direction,
                "entry_kind": entry_kind,
                "entry_price": entry_price,
                "entry_label": entry_label,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "notional": default_notional,
                "timeframe": timeframe,
                "confidence": None,
                "note": note,
            }
            proposals.append(proposal)

        return proposals

    def _normalize_trade_proposal(self, raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not isinstance(raw, dict):
            return None
        symbol = str(raw.get("symbol") or raw.get("ticker") or "").upper().strip()
        if not symbol:
            return None
        direction_raw = str(raw.get("direction") or raw.get("side") or "").upper().strip()
        if direction_raw in {"BUY", "LONG"}:
            direction = "LONG"
        elif direction_raw in {"SELL", "SHORT"}:
            direction = "SHORT"
        else:
            return None

        entry_obj = raw.get("entry") if isinstance(raw.get("entry"), dict) else None
        entry_kind_raw = (
            (entry_obj.get("kind") if entry_obj else None)
            or (entry_obj.get("type") if entry_obj else None)
            or raw.get("entry_kind")
            or raw.get("entry_type")
            or raw.get("entry_plan")
            or raw.get("execution")
        )
        entry_kind = str(entry_kind_raw or "").strip().lower()
        entry_price = None
        entry_label = None
        if entry_obj:
            entry_price = self._safe_float(
                entry_obj.get("price")
                or entry_obj.get("level")
                or entry_obj.get("target")
                or entry_obj.get("zone")
            )
            label_candidate = entry_obj.get("label") or entry_obj.get("note")
            if isinstance(label_candidate, str) and label_candidate.strip():
                entry_label = label_candidate.strip()
        else:
            entry_price = self._safe_float(
                raw.get("entry_price")
                or raw.get("entry")
                or raw.get("entry_level")
                or raw.get("entry_target")
            )
        if not entry_kind:
            if entry_price is None:
                entry_kind = "market"
            else:
                entry_kind = "limit"
        elif entry_kind in {"market", "market_price", "market-order", "market_order"}:
            entry_kind = "market"
        elif entry_kind in {"limit", "limit_order", "limit-order"}:
            entry_kind = "limit"
        else:
            entry_kind = "limit" if entry_price is not None else "market"

        stop_loss = self._safe_float(
            raw.get("stop_loss")
            or raw.get("stop")
            or raw.get("stop_price")
            or raw.get("invalidation")
            or (entry_obj.get("stop") if entry_obj else None)
        )
        if stop_loss is not None and stop_loss <= 0:
            stop_loss = None

        take_profit = self._safe_float(
            raw.get("take_profit")
            or raw.get("tp")
            or raw.get("target")
            or raw.get("tp_price")
            or raw.get("profit_target")
            or (entry_obj.get("take_profit") if entry_obj else None)
        )
        if take_profit is not None and take_profit <= 0:
            take_profit = None

        notional = self._safe_float(
            raw.get("notional")
            or raw.get("notional_usdt")
            or raw.get("size")
            or raw.get("position_size")
            or raw.get("amount")
        )
        if notional is not None and notional <= 0:
            notional = None

        size_multiplier = self._safe_float(
            raw.get("size_multiplier")
            or raw.get("size_mult")
            or raw.get("risk_multiplier")
        )
        if size_multiplier is not None and size_multiplier <= 0:
            size_multiplier = None

        if notional is None and size_multiplier is None:
            return None

        timeframe = None
        timeframe_candidates = (
            raw.get("timeframe"),
            raw.get("time_frame"),
            raw.get("timeFrame"),
            raw.get("time_horizon"),
            raw.get("time horizon"),
            raw.get("horizon"),
            raw.get("window"),
            raw.get("holding_period"),
            raw.get("holding_horizon"),
            raw.get("duration"),
        )
        for candidate in timeframe_candidates:
            if candidate is None:
                continue
            text = str(candidate).strip()
            if text:
                timeframe = text
                break

        note = raw.get("note") or raw.get("thesis") or raw.get("rationale")
        if isinstance(note, str):
            note = note.strip()
        else:
            note = None

        confidence = self._safe_float(raw.get("confidence") or raw.get("conviction") or raw.get("probability"))
        if confidence is not None:
            if confidence < 0:
                confidence = 0.0
            elif confidence > 1:
                if confidence <= 100:
                    confidence = confidence / 100.0
                else:
                    confidence = 1.0
            confidence = max(0.0, min(confidence, 1.0))

        risk_reward = self._safe_float(
            raw.get("risk_reward") or raw.get("rr") or raw.get("reward_risk") or raw.get("rrr")
        )

        normalized: Dict[str, Any] = {
            "symbol": symbol,
            "direction": direction,
            "entry_kind": entry_kind,
            "entry_price": entry_price,
            "entry_label": entry_label,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "notional": notional,
            "size_multiplier": size_multiplier,
            "timeframe": timeframe or None,
            "confidence": confidence,
            "risk_reward": risk_reward,
            "note": note,
        }
        return normalized

    def _store_trade_proposals(
        self,
        proposals: List[Dict[str, Any]],
        *,
        source: str,
    ) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        for payload in proposals:
            norm = self._normalize_trade_proposal(payload)
            if norm:
                normalized.append(norm)
        if not normalized:
            return []

        attempts = 0
        stored: List[Dict[str, Any]] = []
        while attempts < 3:
            attempts += 1
            state = _read_state()
            queue = state.get("ai_trade_proposals")
            if not isinstance(queue, list):
                queue = []
            existing_keys = {
                (
                    str((item.get("payload") or {}).get("symbol") or "").upper(),
                    str((item.get("payload") or {}).get("direction") or "").upper(),
                    str((item.get("payload") or {}).get("entry_kind") or ""),
                    float((item.get("payload") or {}).get("entry_price") or 0.0),
                    float((item.get("payload") or {}).get("stop_loss") or 0.0),
                    float((item.get("payload") or {}).get("take_profit") or 0.0),
                    float((item.get("payload") or {}).get("notional") or 0.0),
                    float((item.get("payload") or {}).get("size_multiplier") or 0.0),
                )
                for item in queue
                if isinstance(item, dict)
            }
            updated_queue = list(queue)
            appended: List[Dict[str, Any]] = []
            for norm in normalized:
                key = (
                    norm.get("symbol"),
                    norm.get("direction"),
                    norm.get("entry_kind"),
                    float(norm.get("entry_price") or 0.0),
                    float(norm.get("stop_loss") or 0.0),
                    float(norm.get("take_profit") or 0.0),
                    float(norm.get("notional") or 0.0),
                    float(norm.get("size_multiplier") or 0.0),
                )
                if key in existing_keys:
                    continue
                proposal_id = str(uuid.uuid4())
                ts = time.time()
                record = {
                    "id": proposal_id,
                    "ts": ts,
                    "status": "pending",
                    "source": source,
                    "payload": norm,
                }
                updated_queue.append(record)
                public_entry = {**norm, "id": proposal_id, "status": "pending", "ts": ts}
                appended.append(public_entry)
                existing_keys.add(key)
            if not appended:
                return []
            state["ai_trade_proposals"] = updated_queue[-40:]
            try:
                STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True))
                stored = appended
                break
            except Exception as exc:
                logger.debug("Failed to persist trade proposals (attempt %s): %s", attempts, exc)
                time.sleep(0.05)
        return stored

    @staticmethod
    def _format_proposal_note(proposal: Dict[str, Any]) -> str:
        parts: List[str] = []
        timeframe = proposal.get("timeframe")
        if isinstance(timeframe, str) and timeframe:
            parts.append(timeframe)
        confidence = proposal.get("confidence")
        if isinstance(confidence, (int, float)):
            parts.append(f"Conf {confidence:.2f}")

        def _fmt_price(value: Optional[float]) -> Optional[str]:
            if value is None:
                return None
            try:
                return format(float(value), ".6g")
            except (TypeError, ValueError):
                return None

        price_bits: List[str] = []
        entry_kind = proposal.get("entry_kind")
        entry_price = proposal.get("entry_price")
        if entry_kind == "limit" and entry_price is not None:
            formatted = _fmt_price(entry_price)
            if formatted:
                price_bits.append(f"Entry {formatted}")
        stop_loss = _fmt_price(proposal.get("stop_loss"))
        if stop_loss:
            price_bits.append(f"SL {stop_loss}")
        take_profit = _fmt_price(proposal.get("take_profit"))
        if take_profit:
            price_bits.append(f"TP {take_profit}")
        if price_bits:
            parts.append(" · ".join(price_bits))
        note = proposal.get("note")
        if isinstance(note, str) and note:
            parts.append(note)
        return " | ".join(parts)

    def _env(self) -> Dict[str, Any]:
        return self.config.get("env", {})

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(number):
            return None
        return number

    def _recent_plan_summaries(self, raw: Any) -> List[Dict[str, Any]]:
        summaries: List[Dict[str, Any]] = []
        if not isinstance(raw, list):
            return summaries
        for entry in raw[-12:]:
            if not isinstance(entry, dict):
                continue
            plan = entry.get("plan")
            if not isinstance(plan, dict):
                continue
            key = str(entry.get("key") or "")
            parts = [part for part in key.split("::") if part]
            symbol = plan.get("symbol") or None
            side = plan.get("side") or None
            if len(parts) >= 2 and not symbol:
                symbol = parts[1]
            if len(parts) >= 3 and not side:
                side = parts[2]
            summary: Dict[str, Any] = {
                "symbol": str(symbol).upper() if symbol else None,
                "side": str(side).upper() if side else None,
                "decision": plan.get("decision"),
                "take": bool(plan.get("take", False)),
                "note": plan.get("decision_note") or plan.get("risk_note"),
                "size_multiplier": self._safe_float(plan.get("size_multiplier")),
                "confidence": self._safe_float(plan.get("confidence")),
                "entry_price": self._safe_float(plan.get("entry_price")),
                "stop_loss": self._safe_float(plan.get("stop_loss")),
                "take_profit": self._safe_float(plan.get("take_profit")),
                "explanation": plan.get("explanation"),
                "ts": self._safe_float(entry.get("ts")) or 0.0,
            }
            summaries.append(summary)
        summaries.sort(key=lambda item: item.get("ts", 0.0), reverse=True)
        return summaries

    def _beta_header_for_model(self, model: str) -> Optional[str]:
        normalized = (model or "").strip().lower()
        if not normalized:
            return None

        beta_requirements = (
            ("gpt-5", "gpt-5"),
            ("gpt-4.1", "gpt-4.1"),
            ("o4", "o4"),
            ("o3", "o3"),
        )
        for prefix, header_value in beta_requirements:
            if normalized.startswith(prefix):
                return header_value
        return None

    def _model_traits(self, model: str) -> Dict[str, Any]:
        normalized = (model or "").strip().lower()
        traits = {
            "modalities": None,
            "reasoning": None,
            "legacy_supported": True,
        }
        if not normalized:
            return traits

        if normalized.startswith("gpt-5") or normalized.startswith("o4"):
            traits["modalities"] = ["text"]
            traits["reasoning"] = {"effort": "medium"}
            traits["legacy_supported"] = False
        elif normalized.startswith("o3"):
            traits["modalities"] = ["text"]
            traits["reasoning"] = {"effort": "medium"}
            traits["legacy_supported"] = False
        elif normalized.startswith("gpt-4.1"):
            traits["modalities"] = ["text"]
            traits["legacy_supported"] = False

        return traits

    def _call_openai_responses(
        self,
        headers: Dict[str, str],
        model: str,
        messages: List[Dict[str, str]],
        temperature: Optional[float],
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        normalized_input: List[Dict[str, Any]] = []
        for item in messages:
            if not isinstance(item, dict):
                continue
            role = str(item.get("role") or "").strip() or "user"
            raw_content = item.get("content")
            content_parts: List[Dict[str, str]] = []
            if isinstance(raw_content, str):
                stripped = raw_content.strip()
                if stripped:
                    content_parts.append({"type": "text", "text": stripped})
            elif isinstance(raw_content, list):
                for part in raw_content:
                    if isinstance(part, dict):
                        p_type = part.get("type")
                        text = part.get("text")
                        if isinstance(text, str) and text.strip():
                            # Respect explicit types if provided by the caller, while
                            # normalising legacy ``input_text`` segments to the modern
                            # ``text`` type expected by the Responses API.
                            normalized_type = str(p_type or "text")
                            if normalized_type == "input_text":
                                normalized_type = "text"
                            content_parts.append(
                                {
                                    "type": normalized_type,
                                    "text": text.strip(),
                                }
                            )
                    elif isinstance(part, str) and part.strip():
                        content_parts.append({"type": "text", "text": part.strip()})
            if not content_parts:
                continue
            normalized_input.append({"role": role, "content": content_parts})

        traits = self._model_traits(model)

        payload: Dict[str, Any] = {
            "model": model,
            "input": normalized_input,
            "max_output_tokens": 400,
        }
        if traits["modalities"]:
            payload["modalities"] = traits["modalities"]
        if traits["reasoning"]:
            payload["reasoning"] = traits["reasoning"]
        if temperature is not None:
            payload["temperature"] = temperature

        resp = requests.post(
            "https://api.openai.com/v1/responses",
            headers=headers,
            json=payload,
            timeout=30,
        )
        if resp.status_code >= 400:
            resp.raise_for_status()

        data = resp.json()
        text_chunks: List[str] = []
        for item in data.get("output", []):
            if not isinstance(item, dict):
                continue
            if item.get("type") != "message":
                continue
            contents = item.get("content") or []
            for piece in contents:
                if not isinstance(piece, dict):
                    continue
                piece_type = piece.get("type")
                if piece_type in {"output_text", "text"}:
                    text_chunks.append(piece.get("text", ""))
        if not text_chunks:
            output_text = data.get("output_text")
            if isinstance(output_text, list):
                text_chunks.extend(str(part) for part in output_text if part)
            elif isinstance(output_text, str):
                text_chunks.append(output_text)
        reply_text = "\n".join(chunk.strip() for chunk in text_chunks if str(chunk).strip())
        return reply_text.strip(), data.get("usage")

    def _call_openai_legacy_chat(
        self,
        headers: Dict[str, str],
        model: str,
        messages: List[Dict[str, str]],
        temperature: Optional[float],
        prior_exc: Optional[Exception] = None,
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": 400,
        }
        if temperature is not None and self._temperature_supported:
            payload["temperature"] = temperature

        attempt = 0
        while True:
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30,
            )
            if resp.status_code < 400:
                data = resp.json()
                choices = data.get("choices") or []
                reply = choices[0]["message"].get("content") if choices else ""
                return (reply or "").strip(), data.get("usage")

            body_snippet = (resp.text or "")[:160]
            lower_body = body_snippet.lower()
            if (
                self._temperature_supported
                and temperature is not None
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

            try:
                resp.raise_for_status()
            except Exception as exc:
                if prior_exc:
                    raise exc from prior_exc
                raise

    def _call_openai_chat(
        self,
        headers: Dict[str, str],
        model: str,
        messages: List[Dict[str, str]],
        temperature: Optional[float],
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        last_exc: Optional[Exception] = None
        traits = self._model_traits(model)
        try:
            return self._call_openai_responses(headers, model, messages, temperature)
        except Exception as exc:
            last_exc = exc

        if not traits.get("legacy_supported", True):
            if last_exc:
                raise last_exc
            raise

        return self._call_openai_legacy_chat(headers, model, messages, temperature, prior_exc=last_exc)

    def _current_state(
        self,
    ) -> Tuple[
        TradeStats,
        List[Dict[str, Any]],
        Dict[str, Any],
        List[Dict[str, Any]],
        Dict[str, Any],
        Dict[str, Any],
        List[Dict[str, Any]],
        Dict[str, Any],
    ]:
        state = _read_state()
        history = state.get("trade_history", [])
        stats = _compute_stats(history)
        open_trades = state.get("live_trades", {})
        ai_activity = state.get("ai_activity", [])
        ai_budget = state.get("ai_budget", {})
        decision_stats = _decision_summary(state)
        recent_plans = self._recent_plan_summaries(state.get("ai_recent_plans"))
        technical_snapshot = state.get("technical_snapshot", {})
        if not isinstance(technical_snapshot, dict):
            technical_snapshot = {}
        return (
            stats,
            history,
            open_trades,
            ai_activity,
            ai_budget,
            decision_stats,
            recent_plans,
            technical_snapshot,
        )

    def _build_context_text(
        self,
        stats: TradeStats,
        history: List[Dict[str, Any]],
        open_trades: Dict[str, Any],
        ai_activity: List[Dict[str, Any]],
        ai_budget: Dict[str, Any],
        decision_stats: Dict[str, Any],
        recent_plans: List[Dict[str, Any]],
        technical_snapshot: Dict[str, Any],
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
        if stats.best_trade:
            best = stats.best_trade
            best_symbol = best.get("symbol")
            best_side = best.get("side")
            try:
                best_pnl = float(best.get("pnl", 0.0) or 0.0)
            except (TypeError, ValueError):
                best_pnl = 0.0
            lines.append(
                f"Best trade: {best_symbol} {best_side} realised {best_pnl:.2f} USDT."
            )
        if stats.worst_trade:
            worst = stats.worst_trade
            worst_symbol = worst.get("symbol")
            worst_side = worst.get("side")
            try:
                worst_pnl = float(worst.get("pnl", 0.0) or 0.0)
            except (TypeError, ValueError):
                worst_pnl = 0.0
            lines.append(
                f"Toughest trade: {worst_symbol} {worst_side} ended at {worst_pnl:.2f} USDT."
            )
        if ai_budget:
            limit = ai_budget.get("limit")
            spent = ai_budget.get("spent")
            if isinstance(limit, (int, float)) and limit:
                lines.append(f"AI budget: {spent:.2f} / {limit:.2f} USD consumed today.")
            elif isinstance(spent, (int, float)):
                lines.append(f"AI budget: {spent:.2f} USD spent today (no configured cap).")
        if decision_stats:
            taken = int(decision_stats.get("taken", 0) or 0)
            rejected_total = int(decision_stats.get("rejected_total", 0) or 0)
            rejected = decision_stats.get("rejected") or {}
            top_reject: Optional[Tuple[str, int]] = None
            if isinstance(rejected, dict):
                items = [
                    (str(reason), int(count or 0)) for reason, count in rejected.items()
                ]
                if items:
                    items.sort(key=lambda pair: pair[1], reverse=True)
                    top_reject = items[0]
            summary = f"Decision stats: {taken} taken / {rejected_total} rejected"
            if top_reject and top_reject[1] > 0:
                summary += f" (top reject: {top_reject[0]} ×{top_reject[1]})."
            else:
                summary += "."
            lines.append(summary)
        if open_trades:
            open_lines = []
            for sym, rec in list(open_trades.items())[:5]:
                side = rec.get("side")
                qty = rec.get("qty")
                entry = rec.get("entry")
                try:
                    qty_val = float(qty)
                except (TypeError, ValueError):
                    qty_val = 0.0
                try:
                    entry_val = float(entry)
                except (TypeError, ValueError):
                    entry_val = 0.0
                ctx = rec.get("ctx") or {}
                mark = ctx.get("mid_price") or ctx.get("mid")
                try:
                    mark_val = float(mark)
                except (TypeError, ValueError):
                    mark_val = None
                detail_bits = [f"qty {qty_val:.4f}"]
                if entry_val:
                    detail_bits.append(f"entry {entry_val:.4f}")
                if mark_val and entry_val:
                    delta = mark_val - entry_val if side == "BUY" else entry_val - mark_val
                    detail_bits.append(f"Δ {delta:.4f}")
                ai_meta = rec.get("ai", {})
                if isinstance(ai_meta, dict):
                    note = ai_meta.get("decision_note") or ai_meta.get("risk_note")
                    if isinstance(note, str) and note.strip():
                        detail_bits.append(note.strip())
                open_lines.append(f"{sym} {side} ({', '.join(detail_bits)})")
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
                data = item.get("data") or {}
                detail_parts: List[str] = []
                if isinstance(data, dict):
                    symbol = data.get("symbol")
                    if symbol:
                        detail_parts.append(str(symbol))
                    side = data.get("side")
                    if side:
                        detail_parts.append(str(side))
                    decision = data.get("decision")
                    take_flag = data.get("take")
                    if decision:
                        if isinstance(take_flag, bool):
                            action = "enter trade" if take_flag else "skip trade"
                            detail_parts.append(f"decision {decision} ({action})")
                        else:
                            detail_parts.append(f"decision {decision}")
                    elif isinstance(take_flag, bool):
                        detail_parts.append("action enter trade" if take_flag else "action skip trade")
                    size_mult = data.get("size_multiplier")
                    sl_mult = data.get("sl_multiplier")
                    tp_mult = data.get("tp_multiplier")
                    confidence = data.get("confidence")
                    try:
                        if confidence is not None:
                            detail_parts.append(f"confidence {float(confidence):.2f}")
                    except (TypeError, ValueError):
                        pass
                    for label, value in (
                        ("size×", size_mult),
                        ("SL×", sl_mult),
                        ("TP×", tp_mult),
                    ):
                        try:
                            if value is not None:
                                detail_parts.append(f"{label}{float(value):.2f}")
                        except (TypeError, ValueError):
                            continue
                    reason_label = _friendly_decision_reason(data.get("decision_reason"))
                    if reason_label:
                        detail_parts.append(f"reason {reason_label}")
                note_candidates: List[str] = []
                if isinstance(data, dict):
                    for key in ("decision_note", "risk_note", "explanation"):
                        raw = data.get(key)
                        if isinstance(raw, str):
                            cleaned = " ".join(raw.split())
                            if cleaned:
                                note_candidates.append(cleaned)
                    notes_list = data.get("notes")
                    if isinstance(notes_list, (list, tuple)):
                        for raw in notes_list:
                            if isinstance(raw, str):
                                cleaned = " ".join(raw.split())
                                if cleaned:
                                    note_candidates.append(cleaned)
                note_text = ""
                if note_candidates:
                    note_text = textwrap.shorten(
                        " · ".join(dict.fromkeys(note_candidates)),
                        width=160,
                        placeholder="…",
                    )
                message = str(body).strip()
                if note_text:
                    message = f"{message} — {note_text}" if message else note_text
                detail = f" [{'; '.join(detail_parts)}]" if detail_parts else ""
                if message:
                    activity_lines.append(f"{headline}: {message}{detail}")
                else:
                    activity_lines.append(f"{headline}{detail}")
            lines.append("Latest AI activity: " + " | ".join(activity_lines))
        if recent_plans:
            plan_lines = []
            for plan in recent_plans[:4]:
                symbol = plan.get("symbol") or "?"
                side = plan.get("side") or plan.get("decision", "?")
                take = "take" if plan.get("take") else str(plan.get("decision", "skip"))
                details: List[str] = []
                size_mult = plan.get("size_multiplier")
                if isinstance(size_mult, (int, float)):
                    details.append(f"size×{size_mult:.2f}")
                confidence = plan.get("confidence")
                if isinstance(confidence, (int, float)):
                    details.append(f"confidence {confidence:.2f}")
                entry_px = plan.get("entry_price")
                take_px = plan.get("take_profit")
                stop_px = plan.get("stop_loss")
                price_bits = []
                if isinstance(entry_px, (int, float)) and entry_px > 0:
                    price_bits.append(f"entry {entry_px:.4f}")
                if isinstance(take_px, (int, float)) and take_px > 0:
                    price_bits.append(f"tp {take_px:.4f}")
                if isinstance(stop_px, (int, float)) and stop_px > 0:
                    price_bits.append(f"sl {stop_px:.4f}")
                if price_bits:
                    details.extend(price_bits)
                note = plan.get("note") or plan.get("explanation")
                snippet = note.strip() if isinstance(note, str) else ""
                detail_txt = f" ({', '.join(details)})" if details else ""
                if snippet:
                    plan_lines.append(f"{symbol} {side} → {take}{detail_txt} :: {snippet}")
                else:
                    plan_lines.append(f"{symbol} {side} → {take}{detail_txt}")
            lines.append("Recent AI plans: " + " | ".join(plan_lines))
        if technical_snapshot:
            snapshot_items: List[Tuple[str, Dict[str, Any]]] = []
            for sym, rec in technical_snapshot.items():
                if not isinstance(rec, dict):
                    continue
                snapshot_items.append((sym, rec))
            if snapshot_items:
                snapshot_items.sort(
                    key=lambda item: float(item[1].get("ts", 0.0) or 0.0),
                    reverse=True,
                )
                tech_bits: List[str] = []
                for sym, rec in snapshot_items[:5]:
                    parts: List[str] = [sym]
                    direction = rec.get("supertrend_dir")
                    if isinstance(direction, (int, float)):
                        if direction > 0:
                            parts.append("↑")
                        elif direction < 0:
                            parts.append("↓")
                        else:
                            parts.append("→")
                    price = rec.get("price")
                    if isinstance(price, (int, float)) and price > 0:
                        parts.append(f"px {price:.4f}")
                    rsi_val = rec.get("rsi")
                    if isinstance(rsi_val, (int, float)):
                        parts.append(f"RSI {rsi_val:.1f}")
                    stoch_d = rec.get("stoch_rsi_d")
                    if isinstance(stoch_d, (int, float)):
                        parts.append(f"StochD {stoch_d:.1f}")
                    bb_pos = rec.get("bb_pos")
                    if isinstance(bb_pos, (int, float)):
                        parts.append(f"BB% {bb_pos * 100.0:.0f}")
                    atr_pct = rec.get("atr_pct")
                    if isinstance(atr_pct, (int, float)):
                        parts.append(f"ATR% {atr_pct * 100.0:.2f}")
                    adx_val = rec.get("adx")
                    if isinstance(adx_val, (int, float)):
                        parts.append(f"ADX {adx_val:.1f}")
                    supertrend_val = rec.get("supertrend")
                    if isinstance(supertrend_val, (int, float)) and supertrend_val > 0:
                        parts.append(f"ST {supertrend_val:.4f}")
                    tech_bits.append(" ".join(parts))
                if tech_bits:
                    lines.append("Technical snapshot: " + " | ".join(tech_bits))
        most_traded_payload = MOST_TRADED_CACHE.get("payload") if MOST_TRADED_CACHE else None
        assets = []
        if isinstance(most_traded_payload, dict):
            raw_assets = most_traded_payload.get("assets")
            if isinstance(raw_assets, list):
                assets = raw_assets[:5]
        if assets:
            market_bits = []
            for asset in assets:
                symbol = asset.get("symbol") or asset.get("base")
                try:
                    price = float(asset.get("price", 0.0) or 0.0)
                except (TypeError, ValueError):
                    price = 0.0
                try:
                    change = float(asset.get("change_15m", 0.0) or 0.0)
                except (TypeError, ValueError):
                    change = 0.0
                try:
                    volume = float(asset.get("volume_quote", 0.0) or 0.0)
                except (TypeError, ValueError):
                    volume = 0.0
                if volume >= 1_000_000_000:
                    volume_txt = f"{volume / 1_000_000_000:.1f}B"
                elif volume >= 1_000_000:
                    volume_txt = f"{volume / 1_000_000:.1f}M"
                else:
                    volume_txt = f"{volume:.0f}"
                price_txt = f"{price:.4f}" if price > 0 else "n/a"
                market_bits.append(
                    f"{symbol} price≈{price_txt} · {change:+.2f}% · vol≈{volume_txt}"
                )
            updated = most_traded_payload.get("updated")
            header = "Most-traded majors"
            if isinstance(updated, str) and updated:
                header += f" (updated {updated})"
            lines.append(f"{header}: " + "; ".join(market_bits))
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
        proposal_id: Optional[str] = None
        if isinstance(action.get("proposal_id"), str):
            proposal_id = action["proposal_id"].strip() or None
        if proposal_id is None:
            payload_inner = action.get("payload")
            if isinstance(payload_inner, dict):
                raw_id = payload_inner.get("proposal_id")
                if isinstance(raw_id, str):
                    proposal_id = raw_id.strip() or None
        if proposal_id:
            request["proposal_id"] = proposal_id
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

    def execute_trade_proposal(self, proposal_id: str) -> Dict[str, Any]:
        proposal_key = str(proposal_id or "").strip()
        if not proposal_key:
            raise ValueError("proposal_id required")

        attempts = 0
        while attempts < 3:
            attempts += 1
            state = _read_state()
            queue = state.get("ai_trade_proposals")
            if not isinstance(queue, list):
                queue = []
            target_index: Optional[int] = None
            for idx, item in enumerate(queue):
                if not isinstance(item, dict):
                    continue
                if str(item.get("id") or "") == proposal_key:
                    target_index = idx
                    break
            if target_index is None:
                raise LookupError("proposal not found")

            target = queue[target_index]
            status = str(target.get("status") or "pending").lower()
            if status in {"queued", "executed", "completed"}:
                raise RuntimeError("proposal already processed")

            normalized = self._normalize_trade_proposal(target.get("payload") or {})
            if not normalized:
                raise RuntimeError("proposal is missing required trade data")

            symbol = normalized.get("symbol")
            direction = normalized.get("direction")
            if not symbol or direction not in {"LONG", "SHORT"}:
                raise RuntimeError("proposal is invalid")

            if normalized.get("notional") is None and normalized.get("size_multiplier") is None:
                raise RuntimeError("proposal requires size or notional before execution")

            side = "BUY" if direction == "LONG" else "SELL"
            payload = {**normalized, "proposal_id": proposal_key, "source": "analysis_proposal"}
            note = self._format_proposal_note(normalized)
            action: Dict[str, Any] = {
                "type": "open_trade",
                "symbol": symbol,
                "side": side,
                "note": note or f"AI proposal {symbol} {direction}",
                "payload": payload,
            }
            action["proposal_id"] = proposal_key
            if normalized.get("size_multiplier") is not None:
                action["size_multiplier"] = normalized["size_multiplier"]
            if normalized.get("notional") is not None:
                action["notional"] = normalized["notional"]

            message = f"Executing trade proposal {symbol} {direction}"
            queued = self._queue_trade_action(action, message)
            if not queued:
                target["status"] = "failed"
                state["ai_trade_proposals"] = queue
                try:
                    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True))
                except Exception:
                    pass
                raise RuntimeError("failed to queue trade proposal")

            now_ts = time.time()
            target["status"] = "queued"
            target["queued_at"] = now_ts
            target["queue_ref"] = queued
            target["payload"] = normalized
            state["ai_trade_proposals"] = queue
            try:
                STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True))
            except Exception as exc:
                logger.debug("Failed to persist proposal status for %s: %s", proposal_key, exc)

            public = {**normalized, "id": proposal_key, "status": "queued", "queued_at": now_ts}
            _append_ai_activity_entry(
                "analysis",
                f"Trade proposal queued ({symbol} {direction})",
                data={
                    "proposal_id": proposal_key,
                    "queued_action": queued,
                    "source": "dashboard_chat",
                },
            )
            return {"proposal": public, "queued_action": queued}

        raise RuntimeError("unable to queue trade proposal")

    def respond(self, message: str, history_payload: List[ChatMessagePayload]) -> Dict[str, Any]:
        (
            stats,
            history,
            open_trades,
            ai_activity,
            ai_budget,
            decision_stats,
            recent_plans,
            technical_snapshot,
        ) = self._current_state()
        fallback = self._fallback_reply(
            message, stats, history, ai_activity, open_trades, ai_budget
        )
        env = self._env()
        chat_api_key = (env.get("ASTER_CHAT_OPENAI_API_KEY") or "").strip()
        primary_api_key = (env.get("ASTER_OPENAI_API_KEY") or "").strip()
        key_candidates: List[Tuple[str, str]] = []
        if chat_api_key:
            key_candidates.append(("dashboard chat key", chat_api_key))
        if primary_api_key and primary_api_key != chat_api_key:
            key_candidates.append(("trading AI key", primary_api_key))
        if not key_candidates:
            notice = (
                "Dashboard chat requires an OpenAI API key. "
                "Add ASTER_CHAT_OPENAI_API_KEY or reuse ASTER_OPENAI_API_KEY "
                "in the AI controls to start chatting with the strategy copilot."
            )
            return {
                "reply": self._format_local_reply(notice),
                "model": "local",
                "source": "missing_chat_key",
            }
        model = (env.get("ASTER_AI_MODEL") or "gpt-4o").strip() or "gpt-4o"

        context_text = self._build_context_text(
            stats,
            history,
            open_trades,
            ai_activity,
            ai_budget,
            decision_stats,
            recent_plans,
            technical_snapshot,
        )
        messages: List[Dict[str, str]] = [{"role": "system", "content": context_text}]
        for item in history_payload[-6:]:
            role = item.role.lower().strip()
            if role not in {"user", "assistant"}:
                continue
            messages.append({"role": role, "content": item.content})
        messages.append({"role": "user", "content": message})

        beta_header = self._beta_header_for_model(model)
        temperature_override: Optional[float] = None
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
                        temperature_override = parsed_temp
            else:
                temperature_override = 0.4

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

        attempted_keys: List[str] = []
        last_exc: Optional[Exception] = None

        for label, api_key in key_candidates:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            if beta_header:
                headers["OpenAI-Beta"] = beta_header
            attempted_keys.append(label)
            try:
                reply_text, usage = self._call_openai_chat(
                    headers,
                    model,
                    messages,
                    temperature_override,
                )
            except Exception as exc:
                last_exc = exc
                log.debug("AI chat request failed using %s: %s", label, exc)
                continue

            if not reply_text:
                reply_text = self._format_local_reply(fallback)
            action_payload = self._extract_action(reply_text)
            queued_action = self._queue_trade_action(action_payload, message) if action_payload else None
            response: Dict[str, Any] = {
                "reply": reply_text,
                "model": model,
                "source": "openai",
                "usage": usage,
            }
            if queued_action:
                response["queued_action"] = queued_action

            log_data: Dict[str, Any] = {
                "source": "dashboard_chat",
                "direction": "inbound",
                "model": model,
                "key_source": label,
            }
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

        awaitable = getattr(loghub, "push", None)
        if last_exc and awaitable:
            try:
                asyncio.create_task(
                    loghub.push(
                        f"AI chat fallback: {last_exc}",
                        level="warning",
                    )
                )
            except RuntimeError:
                pass

        fallback_text = fallback
        extra_lines: List[str] = []
        if attempted_keys:
            attempted = ", ".join(attempted_keys)
            extra_lines.append(f"AI backend unreachable after trying the {attempted}.")
        if last_exc:
            extra_lines.append(f"Last error: {last_exc}")
        if extra_lines:
            fallback_text = "\n".join([fallback_text, *extra_lines])

        reply_text = self._format_local_reply(fallback_text)
        action_payload = self._extract_action(reply_text)
        queued_action = self._queue_trade_action(action_payload, message) if action_payload else None
        response = {"reply": reply_text, "model": model, "source": "fallback"}
        if queued_action:
            response["queued_action"] = queued_action
        data: Dict[str, Any] = {
            "source": "dashboard_chat",
            "direction": "inbound",
            "model": model,
            "attempted_keys": attempted_keys,
        }
        if last_exc:
            data["error"] = str(last_exc)
        _append_ai_activity_entry(
            "warning",
            "Chat fallback response used",
            body=_summarize_text(reply_text, 260),
            data=data,
        )
        return response


    def analyze_market(self) -> Dict[str, Any]:
        (
            stats,
            history,
            open_trades,
            ai_activity,
            ai_budget,
            decision_stats,
            recent_plans,
            technical_snapshot,
        ) = self._current_state()
        now = time.time()
        cached_payload = MOST_TRADED_CACHE.get("payload")
        cached_ts = MOST_TRADED_CACHE.get("timestamp", 0.0)
        if not cached_payload or now - float(cached_ts or 0.0) > 60:
            try:
                assets = _fetch_most_traded_from_binance()
            except Exception as exc:
                log.debug("Failed to refresh most-traded cache: %s", exc)
            else:
                payload = {
                    "updated": datetime.utcnow().isoformat() + "Z",
                    "assets": assets,
                }
                MOST_TRADED_CACHE["payload"] = payload
                MOST_TRADED_CACHE["timestamp"] = now
        fallback = self._fallback_reply(
            "Provide a neutral market status update with potential long and short angles.",
            stats,
            history,
            ai_activity,
            open_trades,
            ai_budget,
        )
        env = self._env()
        chat_api_key = (env.get("ASTER_CHAT_OPENAI_API_KEY") or "").strip()
        primary_api_key = (env.get("ASTER_OPENAI_API_KEY") or "").strip()
        key_candidates: List[Tuple[str, str]] = []
        if chat_api_key:
            key_candidates.append(("dashboard chat key", chat_api_key))
        if primary_api_key and primary_api_key != chat_api_key:
            key_candidates.append(("trading AI key", primary_api_key))
        if not key_candidates:
            notice = (
                "Dashboard market analysis requires an OpenAI API key. "
                "Add ASTER_CHAT_OPENAI_API_KEY or reuse ASTER_OPENAI_API_KEY "
                "in the AI controls to run Analyze Market."
            )
            formatted_notice = self._format_local_reply(notice)
            formatted_notice = self._ensure_analysis_follow_up(formatted_notice)
            return {
                "analysis": formatted_notice,
                "model": "local",
                "source": "missing_chat_key",
            }

        model = (env.get("ASTER_AI_MODEL") or "gpt-4o").strip() or "gpt-4o"
        context_text = self._build_context_text(
            stats,
            history,
            open_trades,
            ai_activity,
            ai_budget,
            decision_stats,
            recent_plans,
            technical_snapshot,
        )
        universe_symbols = self._market_universe_symbols()
        if universe_symbols:
            sample = ", ".join(universe_symbols[:40])
            if len(universe_symbols) > 40:
                sample = f"{sample}, …"
            universe_prompt = (
                f"The full Aster perpetual universe contains {len(universe_symbols)} symbols: {sample}. "
                "Scan this entire list when selecting candidates and call out when liquidity or data gaps limit confidence. "
            )
        else:
            universe_prompt = (
                "Work across the entire set of Aster-listed perpetual pairs, not just the currently traded majors. "
            )
        prompt = (
            "You are the strategy copilot's market analyst. Using the latest telemetry, produce a concise report. "
            f"{universe_prompt}Follow this structure exactly:\n"
            "Market Summary — ≤150 words covering tone, volatility, liquidity, and risk. Reference concrete metrics from the "
            "telemetry and name at least four tickers drawn from the provided Aster universe or most-traded list; call out "
            "explicitly where data is stale or missing.\n"
            "LONG Idea — Provide symbol, timeframe, thesis rooted in available numbers, entry zone with prices, invalidation, "
            "target, catalysts, and any data caveats.\n"
            "SHORT Idea — Same level of detail as the long idea.\n"
            "Trade Inputs — Bullet list that enumerates every field required for execution: symbol, direction, entry_plan "
            "(market or limit with price), entry_price, stop_loss, take_profit, position_size in USDT, timeframe, and "
            "confidence between 0 and 1. Use numeric values; if a figure cannot be justified from telemetry, write 'n/a' "
            "and explain why.\n"
            "After the narrative, emit one ACTION line per idea using: ACTION: {\"type\":\"propose_trade\",...}. The JSON "
            "must include type=\"propose_trade\", symbol, direction (LONG/SHORT), entry_kind (market/limit), entry_price (or null "
            "for market), stop_loss, take_profit, notional (USDT), timeframe, confidence (0-1), and a concise note tying back to the "
            "analysis. Keep each ACTION line on a single line with valid JSON. Finish by reminding the operator that they can click "
            "\"Take trade proposals\" to queue execution."
        )
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": context_text},
            {"role": "user", "content": prompt},
        ]

        beta_header = self._beta_header_for_model(model)
        temperature_override: Optional[float] = None
        if self._temperature_supported:
            dash_temp = os.getenv("ASTER_DASHBOARD_AI_TEMPERATURE")
            if dash_temp:
                try:
                    parsed_temp = float(dash_temp)
                except ValueError:
                    parsed_temp = None
                    log.debug(
                        "Invalid ASTER_DASHBOARD_AI_TEMPERATURE=%s — ignoring", dash_temp
                    )
                else:
                    if abs(parsed_temp - 1.0) > 1e-6:
                        temperature_override = parsed_temp
            else:
                temperature_override = 0.3

        _append_ai_activity_entry(
            "analysis",
            "Manual market analysis requested",
            body="Operator requested long/short ideas via Analyze Market.",
            data={
                "source": "dashboard_chat",
                "direction": "outbound",
                "mode": "analysis",
            },
        )

        attempted_keys: List[str] = []
        last_exc: Optional[Exception] = None

        for label, api_key in key_candidates:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            if beta_header:
                headers["OpenAI-Beta"] = beta_header
            attempted_keys.append(label)
            try:
                reply_text, usage = self._call_openai_chat(
                    headers,
                    model,
                    messages,
                    temperature_override,
                )
            except Exception as exc:
                last_exc = exc
                log.debug("Market analysis request failed using %s: %s", label, exc)
                continue

            if not reply_text:
                reply_text = fallback
            proposals_raw = self._extract_trade_proposals(reply_text)
            stored_proposals = self._store_trade_proposals(proposals_raw, source="analysis")
            if proposals_raw:
                action_line = re.compile(r"^\s*ACTION:\s*\{", re.IGNORECASE)
                cleaned_lines = [
                    line for line in reply_text.splitlines() if not action_line.match(line.strip())
                ]
                reply_text = "\n".join(cleaned_lines)
            formatted = self._format_local_reply(reply_text)
            formatted = self._ensure_analysis_follow_up(formatted)
            response: Dict[str, Any] = {
                "analysis": formatted,
                "model": model,
                "source": "openai",
            }
            if usage:
                response["usage"] = usage
            if stored_proposals:
                response["trade_proposals"] = stored_proposals

            log_data: Dict[str, Any] = {
                "source": "dashboard_chat",
                "direction": "inbound",
                "model": model,
                "key_source": label,
                "mode": "analysis",
            }
            if usage:
                log_data["usage"] = usage
            if stored_proposals:
                log_data["trade_proposals"] = [item.get("id") for item in stored_proposals]
            _append_ai_activity_entry(
                "analysis",
                "Market analysis received",
                body=_summarize_text(formatted, 260),
                data=log_data,
            )
            return response

        awaitable = getattr(loghub, "push", None)
        if last_exc and awaitable:
            try:
                asyncio.create_task(
                    loghub.push(
                        f"AI market analysis fallback: {last_exc}",
                        level="warning",
                    )
                )
            except RuntimeError:
                pass

        fallback_text = fallback
        extra_lines: List[str] = []
        if attempted_keys:
            attempted = ", ".join(attempted_keys)
            extra_lines.append(
                f"AI backend unreachable after trying the {attempted}."
            )
        if last_exc:
            extra_lines.append(f"Last error: {last_exc}")
        if extra_lines:
            fallback_text = "\n".join([fallback_text, *extra_lines])

        formatted = self._format_local_reply(fallback_text)
        formatted = self._ensure_analysis_follow_up(formatted)
        data: Dict[str, Any] = {
            "source": "dashboard_chat",
            "direction": "inbound",
            "mode": "analysis",
            "attempted_keys": attempted_keys,
        }
        if last_exc:
            data["error"] = str(last_exc)
        _append_ai_activity_entry(
            "warning",
            "Market analysis fallback used",
            body=_summarize_text(formatted, 260),
            data=data,
        )
        return {"analysis": formatted, "model": model, "source": "fallback"}


chat_engine = AIChatEngine(CONFIG)


@app.post("/api/ai/analyze")
async def ai_analyze() -> Dict[str, Any]:
    return chat_engine.analyze_market()


@app.post("/api/ai/proposals/execute")
async def ai_execute_proposal(request: ProposalExecutionRequest) -> Dict[str, Any]:
    try:
        return chat_engine.execute_trade_proposal(request.proposal_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Proposal not found") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/trades")
async def trades() -> Dict[str, Any]:
    state = _read_state()
    raw_history: List[Any] = state.get("trade_history", [])[-200:]
    history: List[Dict[str, Any]] = []
    for entry in raw_history:
        if isinstance(entry, dict):
            record = dict(entry)
        else:
            continue
        record["opened_at_iso"] = _format_ts(record.get("opened_at"))
        record["closed_at_iso"] = _format_ts(record.get("closed_at"))
        history.append(record)

    env_cfg = CONFIG.get("env", {})

    realized_entries: List[Dict[str, Any]] = []
    if history:
        try:
            fetch_limit = max(len(history) * 3, 200)
            realized_entries = await asyncio.to_thread(
                _fetch_realized_pnl_entries, env_cfg, fetch_limit
            )
        except Exception as exc:
            logger.debug("realized pnl enrichment failed: %s", exc)
            realized_entries = []

    if realized_entries:
        history = _merge_realized_pnl(history, realized_entries)

    open_trades = state.get("live_trades", {})
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
    ai_requests = _summarize_ai_requests(ai_activity)
    proposals: List[Dict[str, Any]] = []
    raw_proposals = state.get("ai_trade_proposals")
    if isinstance(raw_proposals, list):
        for entry in raw_proposals[-40:]:
            if not isinstance(entry, dict):
                continue
            payload = entry.get("payload")
            if not isinstance(payload, dict):
                continue
            record = dict(payload)
            record["id"] = entry.get("id")
            record["status"] = entry.get("status")
            record["ts"] = entry.get("ts")
            if entry.get("queued_at") is not None:
                record["queued_at"] = entry.get("queued_at")
            proposals.append(record)
    return {
        "open": enriched_open,
        "history": history[::-1],
        "stats": stats.dict(),
        "decision_stats": decision_stats,
        "cumulative_stats": _cumulative_summary(state),
        "ai_budget": ai_budget,
        "ai_activity": ai_activity,
        "ai_requests": ai_requests,
        "ai_trade_proposals": proposals,
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
