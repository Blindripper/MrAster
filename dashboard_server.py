"""Aster Bot Dashboard server providing web UI for configuration, monitoring and history."""
from __future__ import annotations

import asyncio
import ast
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
from collections import OrderedDict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple
from urllib.parse import urlencode

import requests

from brackets_guard import BracketGuard
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

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
    "ASTER_DEFAULT_NOTIONAL": "1000",
    "ASTER_RISK_PER_TRADE": "0.02",
    "ASTER_LEVERAGE": "12",
    "ASTER_RISK_PROFILE": "aggressive",
    "ASTER_PRESET_MODE": "mid",
    "ASTER_TREND_BIAS": "with",
    "ASTER_EQUITY_FRACTION": "0.90",
    "ASTER_MIN_NOTIONAL_USDT": "5",
    "ASTER_MAX_NOTIONAL_USDT": "0",
    "ASTER_SIZE_MULT": "1.2",
    "ASTER_SIZE_MULT_S": "0.75",
    "ASTER_SIZE_MULT_M": "1.8",
    "ASTER_SIZE_MULT_L": "3.0",
    "ASTER_SIZE_MULT_FLOOR": "0.75",
    "ASTER_SIZE_MULT_CAP": "5.0",
    "ASTER_CONFIDENCE_SIZING": "true",
    "ASTER_CONFIDENCE_SIZE_MIN": "1.0",
    "ASTER_CONFIDENCE_SIZE_MAX": "3.0",
    "ASTER_CONFIDENCE_SIZE_BLEND": "1",
    "ASTER_CONFIDENCE_SIZE_EXP": "2.0",
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
    "ASTER_ALPHA_THRESHOLD": "0.50",
    "ASTER_ALPHA_WARMUP": "30",
    "ASTER_ALPHA_LR": "0.05",
    "ASTER_ALPHA_L2": "0.0005",
    "ASTER_ALPHA_MIN_CONF": "0.2",
    "ASTER_ALPHA_PROMOTE_DELTA": "0.15",
    "ASTER_ALPHA_REWARD_MARGIN": "0.05",
    "ASTER_HISTORY_MAX": "250",
    "ASTER_BOT_SCRIPT": "aster_multi_bot.py",
    "ASTER_OPENAI_API_KEY": "",
    "ASTER_AI_MODE": "false",
    "ASTER_AI_MODEL": "gpt-4.1",
    "ASTER_AI_DAILY_BUDGET_USD": "20",
    "ASTER_AI_STRICT_BUDGET": "true",
    "ASTER_AI_SENTINEL_ENABLED": "true",
    "ASTER_AI_SENTINEL_DECAY_MINUTES": "60",
    "ASTER_AI_CONF_SCALE": "25",
    "ASTER_AI_NEWS_ENDPOINT": "",
    "ASTER_AI_NEWS_API_KEY": "",
    "ASTER_CHAT_OPENAI_API_KEY": "",
    "ASTER_DASHBOARD_REALIZED_ENRICH": "false",
}

# Mapping of well-known asset names to their corresponding base tickers to
# improve natural-language symbol detection inside strategy copilot requests.
# The keys are base tickers (without the quote asset suffix) while the values
# enumerate common aliases that operators might use in chat instead of the
# official ticker symbol.
SYMBOL_SYNONYMS: Dict[str, Tuple[str, ...]] = {
    "BTC": ("BITCOIN", "XBT"),
    "ETH": ("ETHEREUM", "ETHER"),
    "SOL": ("SOLANA",),
    "XRP": ("RIPPLE",),
    "ADA": ("CARDANO",),
    "DOGE": ("DOGECOIN", "DOGE"),
    "BNB": ("BINANCE", "BINANCECOIN"),
    "DOT": ("POLKADOT",),
    "AVAX": ("AVALANCHE",),
    "MATIC": ("POLYGON",),
    "LTC": ("LITECOIN",),
    "LINK": ("CHAINLINK",),
    "ATOM": ("COSMOS",),
    "ETC": ("ETHEREUMCLASSIC", "ETHEREUM_CLASSIC"),
    "XMR": ("MONERO",),
    "NEAR": ("NEARPROTOCOL", "NEAR_PROTOCOL"),
    "APT": ("APTOS",),
    "ARB": ("ARBITRUM",),
    "FIL": ("FILECOIN",),
    "SUI": ("SUINETWORK", "SUI_NETWORK"),
}

ALLOWED_ENV_KEYS = set(ENV_DEFAULTS.keys())


REALIZED_PNL_MATCH_PADDING_SECONDS = 180.0


def _is_truthy(value: Optional[str]) -> bool:
    if value is None:
        return False
    token = str(value).strip().lower()
    return token in {"1", "true", "yes", "on"}


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
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return float(stripped.replace(",", ""))
        except ValueError:
            normalized = stripped.replace(",", "")
            match = re.search(r"-?\d+(?:\.\d+)?", normalized)
            if not match:
                return None
            numeric = match.group(0)
            try:
                return float(numeric)
            except ValueError:
                return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clean_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
    else:
        try:
            text = str(value).strip()
        except Exception:
            return None
    return text or None


def _normalize_string_list(values: Any, *, limit: int = 6) -> List[str]:
    normalized: List[str] = []
    if isinstance(values, list):
        for item in values:
            text = _clean_string(item)
            if text:
                normalized.append(text)
            if len(normalized) >= limit:
                break
    else:
        text = _clean_string(values)
        if text:
            normalized.append(text)
    return normalized


def _normalize_strategy_blob(payload: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(payload, dict):
        return None

    strategy: Dict[str, Any] = {}
    name = _clean_string(payload.get("name"))
    if name:
        strategy["name"] = name

    objective = _clean_string(payload.get("objective") or payload.get("goal"))
    if objective:
        strategy["objective"] = objective

    why_active = _clean_string(
        payload.get("why_active")
        or payload.get("rationale")
        or payload.get("justification")
    )
    if why_active:
        strategy["why_active"] = why_active

    signals = _normalize_string_list(
        payload.get("market_signals") or payload.get("signals")
    )
    if signals:
        strategy["market_signals"] = signals[:6]

    actions_raw = payload.get("actions")
    actions: List[Dict[str, Any]] = []
    if isinstance(actions_raw, list):
        for idx, item in enumerate(actions_raw, start=1):
            title = None
            detail = None
            trigger = None
            if isinstance(item, dict):
                title = _clean_string(
                    item.get("title") or item.get("name") or item.get("step")
                )
                detail = _clean_string(
                    item.get("detail")
                    or item.get("instruction")
                    or item.get("action")
                )
                trigger = _clean_string(item.get("trigger") or item.get("condition"))
            else:
                detail = _clean_string(item)
            if not (title or detail):
                continue
            action_entry: Dict[str, Any] = {"title": title or f"Step {idx}"}
            if detail:
                action_entry["detail"] = detail
            if trigger:
                action_entry["trigger"] = trigger
            actions.append(action_entry)
            if len(actions) >= 6:
                break
    elif isinstance(actions_raw, dict):
        for key, value in actions_raw.items():
            detail = _clean_string(value)
            if not detail:
                continue
            action_entry = {
                "title": _clean_string(key) or f"Step {len(actions) + 1}",
                "detail": detail,
            }
            actions.append(action_entry)
            if len(actions) >= 6:
                break
    if actions:
        strategy["actions"] = actions

    risk_controls = _normalize_string_list(
        payload.get("risk_controls") or payload.get("risk_management")
    )
    if risk_controls:
        strategy["risk_controls"] = risk_controls[:6]

    return strategy or None


def _normalize_ai_budget(raw: Any) -> Dict[str, Any]:
    bucket: Dict[str, Any] = dict(raw) if isinstance(raw, dict) else {}
    history = bucket.get("history")
    if not isinstance(history, list):
        history = []
    bucket["history"] = history
    count_val = bucket.get("count")
    try:
        count = int(count_val)
    except (TypeError, ValueError):
        count = None
    if count is None:
        count = len(history)
    if count < len(history):
        count = len(history)
    bucket["count"] = max(count, 0)
    return bucket


def _summarize_playbook_snapshot_meta(meta: Optional[Dict[str, Any]]) -> Optional[str]:
    if not isinstance(meta, dict) or not meta:
        return None

    parts: List[str] = []

    technical = meta.get("technical")
    if isinstance(technical, (int, float)):
        try:
            parts.append(f"technical={int(technical)}")
        except Exception:
            pass

    sentinel = meta.get("sentinel")
    if isinstance(sentinel, (int, float)):
        try:
            parts.append(f"sentinel={int(sentinel)}")
        except Exception:
            pass

    avg_rsi = _safe_float(meta.get("technical_avg_rsi"))
    if avg_rsi is not None:
        parts.append(f"avgRSI={avg_rsi:.1f}")

    trend_up = _safe_float(meta.get("technical_trend_up_ratio"))
    if trend_up is not None:
        parts.append(f"trend↑={trend_up:.2f}")

    high_vol = _safe_float(meta.get("technical_high_volatility_ratio"))
    if high_vol is not None:
        parts.append(f"hiVOL={high_vol:.2f}")

    avg_event = _safe_float(meta.get("sentinel_avg_event_risk"))
    if avg_event is not None:
        parts.append(f"event={avg_event:.2f}")

    avg_hype = _safe_float(meta.get("sentinel_avg_hype_score"))
    if avg_hype is not None:
        parts.append(f"hype={avg_hype:.2f}")

    warnings = meta.get("sentinel_warnings")
    if isinstance(warnings, (int, float)) and warnings:
        parts.append(f"warnings={int(warnings)}")

    remaining = _safe_float(meta.get("budget_remaining"))
    limit = _safe_float(meta.get("budget_limit"))
    if remaining is not None and limit is not None:
        parts.append(f"budget {remaining:.2f}/{limit:.2f}")
    elif remaining is not None:
        parts.append(f"budget remaining={remaining:.2f}")

    if not parts:
        return None
    return " · ".join(parts)


def _aggregate_sentinel_overview(raw: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(raw, dict) or not raw:
        return None

    count = 0
    event_values: List[float] = []
    hype_values: List[float] = []
    warning_symbols = 0
    hard_blocks = 0
    max_event: Optional[Tuple[str, float]] = None

    for symbol, entry in raw.items():
        if not isinstance(entry, dict):
            continue
        count += 1

        event_risk = _safe_float(entry.get("event_risk"))
        if event_risk is not None:
            event_values.append(event_risk)
            if event_risk >= 0.25:
                warning_symbols += 1
            if not max_event or event_risk > max_event[1]:
                max_event = (str(symbol), event_risk)

        hype_score = _safe_float(entry.get("hype_score"))
        if hype_score is not None:
            hype_values.append(hype_score)

        actions = entry.get("actions")
        if isinstance(actions, dict) and actions.get("hard_block"):
            hard_blocks += 1

    if count <= 0:
        return None

    overview: Dict[str, Any] = {"count": count}
    if event_values:
        avg_event = sum(event_values) / float(len(event_values))
        overview["avg_event_risk"] = round(avg_event, 3)
    if hype_values:
        avg_hype = sum(hype_values) / float(len(hype_values))
        overview["avg_hype_score"] = round(avg_hype, 3)
    if warning_symbols:
        overview["warning_symbols"] = int(warning_symbols)
    if hard_blocks:
        overview["hard_blocks"] = int(hard_blocks)
    if max_event and max_event[0]:
        overview["max_event_risk"] = {
            "symbol": max_event[0],
            "value": round(max_event[1], 3),
        }
    return overview


def _extract_playbook_market_overview(state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    snapshot = state.get("playbook_snapshot")
    if isinstance(snapshot, dict):
        overview = snapshot.get("market_overview")
        if isinstance(overview, dict) and overview:
            return overview

    stored_overview = state.get("playbook_market_overview")
    if isinstance(stored_overview, dict) and stored_overview:
        return stored_overview

    sentinel_state = state.get("sentinel")
    sentinel_overview = _aggregate_sentinel_overview(sentinel_state)
    if sentinel_overview:
        return {"sentinel": sentinel_overview}
    return None


def _normalize_playbook_state(raw: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(raw, dict):
        return None

    active = raw.get("active")
    if not isinstance(active, dict):
        return None

    mode = str(active.get("mode") or "baseline")
    bias = str(active.get("bias") or "neutral")

    size_bias_raw = active.get("size_bias")
    size_bias: Dict[str, float] = {}
    if isinstance(size_bias_raw, dict):
        for key, raw_value in size_bias_raw.items():
            label = str(key or "").strip()
            if not label:
                continue
            value = _safe_float(raw_value)
            if value is None:
                continue
            size_bias[label.upper()] = value

    sl_bias = _safe_float(active.get("sl_bias"))
    if sl_bias is None:
        sl_bias = _safe_float(active.get("sl_atr_mult"))
    tp_bias = _safe_float(active.get("tp_bias"))
    if tp_bias is None:
        tp_bias = _safe_float(active.get("tp_atr_mult"))

    features_raw = active.get("features")
    features: List[Dict[str, Any]] = []
    if isinstance(features_raw, dict):
        for key, value in features_raw.items():
            numeric = _safe_float(value)
            if numeric is None:
                continue
            features.append({"name": str(key), "value": numeric})
        features.sort(key=lambda item: abs(item["value"]), reverse=True)
        features = features[:5]

    refreshed_raw = active.get("refreshed")
    if isinstance(refreshed_raw, (int, float)):
        if refreshed_raw <= 0:
            refreshed_raw = None
    elif isinstance(refreshed_raw, str):
        token = refreshed_raw.strip()
        if not token:
            refreshed_raw = None
        else:
            try:
                if float(token) <= 0:
                    refreshed_raw = None
            except (TypeError, ValueError):
                # keep non-numeric strings such as ISO timestamps
                pass
    refreshed_dt = _parse_activity_ts(refreshed_raw)
    refreshed_iso = refreshed_dt.isoformat() if refreshed_dt else None
    refreshed_epoch = refreshed_dt.timestamp() if refreshed_dt else None

    notes = active.get("notes") or active.get("note")
    note_text = None
    if isinstance(notes, str):
        stripped = notes.strip()
        note_text = stripped or None

    confidence = _safe_float(active.get("confidence"))
    if confidence is None:
        confidence = _safe_float(active.get("confidence_score"))

    strategy = _normalize_strategy_blob(active.get("strategy"))

    reason_text = _clean_string(active.get("reason"))
    if not reason_text and strategy:
        reason_text = strategy.get("why_active")

    result: Dict[str, Any] = {
        "mode": mode,
        "bias": bias,
    }
    if size_bias:
        result["size_bias"] = size_bias
    if sl_bias is not None:
        result["sl_bias"] = sl_bias
    if tp_bias is not None:
        result["tp_bias"] = tp_bias
    if features:
        result["features"] = features
    if refreshed_iso:
        result["refreshed"] = refreshed_iso
    if refreshed_epoch is not None:
        result["refreshed_ts"] = refreshed_epoch
    if note_text:
        result["notes"] = note_text
    if confidence is not None:
        result["confidence"] = confidence
    if reason_text:
        result["reason"] = reason_text
    if strategy:
        result["strategy"] = strategy

    return result


def _derive_playbook_state_from_activity(
    activity: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    if not isinstance(activity, list):
        return None

    for entry in reversed(activity):
        if not isinstance(entry, dict):
            continue

        mode_raw = entry.get("mode")
        bias_raw = entry.get("bias")
        size_bias_raw = entry.get("size_bias")
        sl_bias = entry.get("sl_bias")
        tp_bias = entry.get("tp_bias")
        features = entry.get("features")
        notes = entry.get("notes")
        confidence = entry.get("confidence")
        reason = entry.get("reason")
        strategy_raw = entry.get("strategy")

        has_details = any(
            value
            for value in (
                mode_raw,
                bias_raw,
                size_bias_raw,
                sl_bias,
                tp_bias,
                features,
                notes,
                confidence,
                reason,
                strategy_raw,
            )
        )
        if not has_details:
            continue

        result: Dict[str, Any] = {}
        if isinstance(mode_raw, str) and mode_raw.strip():
            result["mode"] = mode_raw.strip()
        if isinstance(bias_raw, str) and bias_raw.strip():
            result["bias"] = bias_raw.strip()

        if isinstance(size_bias_raw, dict):
            normalized_size: Dict[str, float] = {}
            for key, raw_value in size_bias_raw.items():
                label = str(key or "").strip()
                if not label:
                    continue
                value = _safe_float(raw_value)
                if value is None:
                    continue
                normalized_size[label.upper()] = value
            if normalized_size:
                result["size_bias"] = normalized_size

        for key, value in (("sl_bias", sl_bias), ("tp_bias", tp_bias)):
            numeric = _safe_float(value)
            if numeric is not None:
                result[key] = numeric

        if isinstance(features, list):
            filtered = [item for item in features if isinstance(item, dict)]
            if filtered:
                result["features"] = filtered

        if isinstance(notes, str) and notes.strip():
            result["notes"] = notes.strip()

        normalized_strategy = _normalize_strategy_blob(strategy_raw)
        if normalized_strategy:
            result["strategy"] = normalized_strategy

        reason_text = _clean_string(reason)
        if not reason_text and normalized_strategy:
            reason_text = normalized_strategy.get("why_active")
        if reason_text:
            result["reason"] = reason_text

        numeric_confidence = _safe_float(confidence)
        if numeric_confidence is not None:
            result["confidence"] = numeric_confidence

        result.setdefault("mode", "baseline")
        result.setdefault("bias", "neutral")

        ts_epoch = entry.get("ts_epoch")
        refreshed_iso = entry.get("ts")
        if not refreshed_iso and entry.get("ts"):
            try:
                refreshed_iso = str(entry.get("ts"))
            except Exception:
                refreshed_iso = None
        if ts_epoch is None and refreshed_iso:
            parsed = _parse_activity_ts(refreshed_iso)
            if parsed:
                ts_epoch = parsed.timestamp()
                refreshed_iso = parsed.isoformat()
        if ts_epoch is not None:
            result["refreshed_ts"] = float(ts_epoch)
        if refreshed_iso:
            result["refreshed"] = refreshed_iso

        if result:
            return result

    return None


def _is_placeholder_playbook(state: Optional[Dict[str, Any]]) -> bool:
    if not state:
        return True

    if state.get("refreshed_ts") or state.get("refreshed"):
        return False

    mode = str(state.get("mode") or "").strip().lower()
    bias = str(state.get("bias") or "").strip().lower()

    if mode and mode not in {"baseline"}:
        return False
    if bias and bias not in {"neutral"}:
        return False

    size_bias = state.get("size_bias")
    if isinstance(size_bias, dict):
        for value in size_bias.values():
            numeric = _safe_float(value)
            if numeric is None:
                continue
            if abs(numeric - 1.0) > 1e-6:
                return False

    if state.get("features") or state.get("notes") or state.get("confidence"):
        return False

    return True


def _resolve_playbook_state(
    raw_state: Any, activity: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    normalized = _normalize_playbook_state(raw_state)
    if not _is_placeholder_playbook(normalized):
        return normalized

    fallback = _derive_playbook_state_from_activity(activity)
    if not fallback:
        return normalized

    merged: Dict[str, Any] = dict(normalized) if isinstance(normalized, dict) else {}
    merged.update(fallback)
    return merged if merged else fallback


def _collect_playbook_activity(ai_activity: List[Any]) -> List[Dict[str, Any]]:
    if not isinstance(ai_activity, list):
        return []

    items: List[Dict[str, Any]] = []
    allowed_request_prefixes = ("playbook", "tuning")
    allowed_kind_prefixes = ("playbook", "tuning")
    disallowed_mode_prefixes = ("analysis", "strategy")
    for entry in ai_activity:
        if not isinstance(entry, dict):
            continue
        data = entry.get("data")
        headline = str(entry.get("headline") or "")
        normalized_headline = headline.lower()
        kind_label = str(entry.get("kind") or "")
        kind_normalized = kind_label.strip().lower()

        relevant = "playbook" in normalized_headline
        if not relevant and kind_normalized:
            if kind_normalized.startswith(allowed_kind_prefixes) or "playbook" in kind_normalized:
                relevant = True

        request_kind = None
        normalized_request_kind = ""
        request_id_hint: Optional[str] = None
        disallowed_mode = False
        normalized_mode = ""

        if isinstance(data, dict):
            raw_request_kind = data.get("request_kind")
            if isinstance(raw_request_kind, str):
                request_kind = raw_request_kind.strip() or None
            elif raw_request_kind is not None:
                request_kind = str(raw_request_kind)
            if request_kind:
                normalized_request_kind = request_kind.strip().lower()
                if normalized_request_kind.startswith(allowed_request_prefixes):
                    relevant = True
                else:
                    # Explicitly tagged as a different request – skip it entirely
                    continue
            raw_request_id = data.get("request_id")
            if isinstance(raw_request_id, str):
                request_id_hint = raw_request_id.strip() or None
            elif raw_request_id is not None:
                request_id_hint = str(raw_request_id)

            raw_mode = data.get("mode")
            if isinstance(raw_mode, str):
                normalized_mode = raw_mode.strip().lower()
                if normalized_mode.startswith(disallowed_mode_prefixes):
                    disallowed_mode = True

        if (
            not relevant
            and request_id_hint
            and request_id_hint.strip().lower().startswith(allowed_request_prefixes)
        ):
            relevant = True

        if request_id_hint:
            normalized_request_id = request_id_hint.strip().lower()
            if "::" in normalized_request_id:
                prefix = normalized_request_id.split("::", 1)[0]
                if prefix and prefix not in allowed_request_prefixes:
                    continue

        if not relevant and isinstance(data, dict):
            playbook_keys = {
                "mode",
                "bias",
                "size_bias",
                "sl_bias",
                "tp_bias",
                "sl_atr_mult",
                "tp_atr_mult",
                "snapshot_meta",
                "features",
            }
            if any(key in data for key in playbook_keys) and not disallowed_mode:
                relevant = True

        if not relevant:
            continue

        if disallowed_mode and not normalized_request_kind.startswith(allowed_request_prefixes):
            if not (request_id_hint and request_id_hint.strip().lower().startswith(allowed_request_prefixes)):
                if "playbook" not in normalized_headline and "playbook" not in kind_normalized:
                    continue

        record: Dict[str, Any] = {
            "kind": entry.get("kind"),
            "headline": headline,
        }

        timestamp = entry.get("ts")
        parsed_ts = _parse_activity_ts(timestamp)
        if parsed_ts:
            record["ts"] = parsed_ts.isoformat()
            record["ts_epoch"] = parsed_ts.timestamp()
        elif isinstance(timestamp, str):
            record["ts"] = timestamp

        body = entry.get("body")
        if isinstance(body, str):
            stripped_body = body.strip()
            if stripped_body:
                record["body"] = stripped_body

        if isinstance(data, dict):
            raw_request_id = data.get("request_id")
            request_id: Optional[str] = None
            if isinstance(raw_request_id, str):
                request_id = raw_request_id.strip() or None
            elif raw_request_id is not None:
                request_id = str(raw_request_id)
            if request_id:
                record["request_id"] = request_id

            if request_kind:
                record["request_kind"] = normalized_request_kind or request_kind

            reason = data.get("reason")
            if isinstance(reason, str):
                stripped_reason = reason.strip()
                if stripped_reason:
                    record["reason"] = stripped_reason

            notes = data.get("notes")
            if isinstance(notes, str):
                stripped_note = notes.strip()
                if stripped_note:
                    record["notes"] = stripped_note
            if "notes" not in record:
                note = data.get("note")
                if isinstance(note, str):
                    stripped_note = note.strip()
                    if stripped_note:
                        record["notes"] = stripped_note

            for key in ("mode", "bias"):
                value = data.get(key)
                if isinstance(value, str):
                    record[key] = value.strip()

            size_bias_raw = data.get("size_bias")
            if isinstance(size_bias_raw, dict):
                size_bias: Dict[str, float] = {}
                for key, raw_value in size_bias_raw.items():
                    label = str(key or "").strip()
                    if not label:
                        continue
                    value = _safe_float(raw_value)
                    if value is None:
                        continue
                    size_bias[label.upper()] = value
                if size_bias:
                    record["size_bias"] = size_bias

            sl_bias = _safe_float(data.get("sl_bias"))
            if sl_bias is None:
                sl_bias = _safe_float(data.get("sl_atr_mult"))
            if sl_bias is not None:
                record["sl_bias"] = sl_bias

            tp_bias = _safe_float(data.get("tp_bias"))
            if tp_bias is None:
                tp_bias = _safe_float(data.get("tp_atr_mult"))
            if tp_bias is not None:
                record["tp_bias"] = tp_bias

            confidence = _safe_float(data.get("confidence"))
            if confidence is None:
                confidence = _safe_float(data.get("confidence_score"))
            if confidence is not None:
                record["confidence"] = confidence

            features_raw = data.get("features")
            if isinstance(features_raw, dict):
                features: List[Dict[str, Any]] = []
                for key, value in features_raw.items():
                    numeric = _safe_float(value)
                    if numeric is None:
                        continue
                    features.append({"name": str(key), "value": numeric})
                features.sort(key=lambda item: abs(item["value"]), reverse=True)
                if features:
                    record["features"] = features[:5]

            strategy_blob = _normalize_strategy_blob(data.get("strategy"))
            if strategy_blob:
                record["strategy"] = strategy_blob
                if "reason" not in record and strategy_blob.get("why_active"):
                    record["reason"] = strategy_blob.get("why_active")

            snapshot_meta = data.get("snapshot_meta")
            summary = _summarize_playbook_snapshot_meta(snapshot_meta)
            if summary:
                record["snapshot_summary"] = summary

        items.append(record)

    return items[-40:]


def _build_playbook_process(
    activity: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    if not isinstance(activity, list):
        return []

    def _resolve_stage(entry: Dict[str, Any]) -> str:
        kind = str(entry.get("kind") or "").strip().lower()
        headline = str(entry.get("headline") or "").strip().lower()
        if kind == "query" or "refresh requested" in headline:
            return "requested"
        if kind in {"error", "alert"} or "failed" in headline:
            return "failed"
        if kind in {"playbook", "info", "tuning"} and (
            entry.get("mode")
            or entry.get("bias")
            or entry.get("size_bias")
            or entry.get("sl_bias")
            or entry.get("tp_bias")
        ):
            return "applied"
        return "info"

    grouped: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
    anonymous_counter = 0

    signal_fields = (
        "mode",
        "bias",
        "size_bias",
        "sl_bias",
        "tp_bias",
        "snapshot_summary",
        "notes",
    )

    for raw_entry in activity:
        if not isinstance(raw_entry, dict):
            continue
        entry = dict(raw_entry)
        request_id = entry.get("request_id")
        if isinstance(request_id, str):
            request_id = request_id.strip() or None
        stage = _resolve_stage(entry)

        if not request_id:
            has_signal_payload = any(entry.get(field) for field in signal_fields)
            if stage in {"applied", "failed"} and has_signal_payload:
                key = "anonymous:playbook"
            else:
                anonymous_counter += 1
                key = f"anonymous:{anonymous_counter}"
        else:
            key = request_id

        record = grouped.setdefault(
            key,
            {
                "request_id": request_id,
                "steps": [],
                "status": "pending",
            },
        )

        if stage == "failed":
            record["status"] = "failed"
        elif stage == "applied" and record.get("status") != "failed":
            record["status"] = "applied"

        ts_epoch = entry.get("ts_epoch")
        ts = entry.get("ts")
        if ts_epoch is not None:
            try:
                epoch = float(ts_epoch)
            except (TypeError, ValueError):
                epoch = None
            if epoch is not None:
                record.setdefault("requested_ts", epoch)
                if stage == "applied":
                    record["completed_ts"] = epoch
                elif stage == "failed":
                    record["failed_ts"] = epoch
        elif ts and record.get("requested_ts") is None:
            parsed = _parse_activity_ts(ts)
            if parsed:
                record["requested_ts"] = parsed.timestamp()
                record["requested_ts_iso"] = parsed.isoformat()

        for key_name in ("mode", "bias", "size_bias", "sl_bias", "tp_bias"):
            value = entry.get(key_name)
            if value is not None:
                record[key_name] = value

        snapshot_summary = entry.get("snapshot_summary")
        if snapshot_summary:
            record.setdefault("snapshot_summary", snapshot_summary)
        notes = entry.get("notes")
        if notes:
            record.setdefault("notes", notes)

        step = {
            "stage": stage,
            "kind": entry.get("kind"),
            "headline": entry.get("headline"),
            "body": entry.get("body"),
            "snapshot_summary": entry.get("snapshot_summary"),
            "ts": ts,
            "ts_epoch": ts_epoch,
        }
        record["steps"].append(step)
        if len(record["steps"]) > 8:
            record["steps"] = record["steps"][-8:]

    process: List[Dict[str, Any]] = []
    for key, record in grouped.items():
        steps = record.get("steps", [])
        record["steps"] = steps

        has_request_id = bool(record.get("request_id"))
        if not has_request_id:
            continue

        has_meaningful_stage = any(
            step.get("stage") in {"requested", "applied", "failed"} for step in steps
        )
        has_signal_payload = any(
            bool(record.get(field))
            for field in (
                "mode",
                "bias",
                "size_bias",
                "sl_bias",
                "tp_bias",
                "snapshot_summary",
                "notes",
            )
        )

        stages = [step.get("stage") for step in steps if step.get("stage")]
        pending_cycle_marker = (
            record.get("status") == "pending"
            and not has_signal_payload
            and not has_request_id
            and stages
            and all(stage == "requested" for stage in stages)
        )

        if pending_cycle_marker:
            continue

        if not (has_meaningful_stage or has_signal_payload):
            continue

        process.append(record)

    process.sort(
        key=lambda item: (
            -float(item.get("requested_ts") or 0.0),
            item.get("request_id") or "",
        )
    )
    return process[:12]


def _ai_request_count(ai_budget: Dict[str, Any]) -> Optional[int]:
    if not isinstance(ai_budget, dict):
        return None
    try:
        count = int(ai_budget.get("count"))
    except (TypeError, ValueError):
        return None
    return max(count, 0)


def _summarize_ai_budget_line(ai_budget: Dict[str, Any]) -> Optional[str]:
    if not isinstance(ai_budget, dict) or not ai_budget:
        return None
    limit_val = _safe_float(ai_budget.get("limit"))
    spent_val = _safe_float(ai_budget.get("spent"))
    request_count = _ai_request_count(ai_budget)
    request_phrase = None
    if request_count is not None:
        noun = "request" if request_count == 1 else "requests"
        request_phrase = f"{request_count} AI {noun} today"
    if limit_val is not None and limit_val > 0 and spent_val is not None:
        message = f"AI budget: {spent_val:.2f} / {limit_val:.2f} USD consumed today"
        if request_phrase:
            message += f" ({request_phrase})."
        else:
            message += "."
        return message
    if spent_val is not None:
        note = "no configured cap"
        if request_phrase:
            note += f"; {request_phrase}"
        return f"AI budget: {spent_val:.2f} USD spent today ({note})."
    if request_phrase:
        return f"AI budget requests so far: {request_phrase}."
    return None


def _build_snapshot_entry_from_record(
    record: Dict[str, Any], fallback_symbol: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    symbol = _resolve_symbol_from_record(record, fallback_symbol)
    if not symbol:
        return None

    position_amt = _extract_numeric_field(record, POSITION_NUMERIC_FIELD_ALIASES["position_amt"])
    if position_amt is None or abs(position_amt) < 1e-12:
        return None

    entry_price = _extract_numeric_field(record, POSITION_NUMERIC_FIELD_ALIASES["entry_price"])
    mark_price = _extract_numeric_field(record, POSITION_NUMERIC_FIELD_ALIASES["mark_price"])
    unrealized = _extract_numeric_field(record, POSITION_NUMERIC_FIELD_ALIASES["unrealized"])
    leverage = _extract_numeric_field(record, POSITION_NUMERIC_FIELD_ALIASES["leverage"])
    notional = _extract_numeric_field(record, POSITION_NUMERIC_FIELD_ALIASES["notional"])
    margin_val = _extract_numeric_field(record, POSITION_NUMERIC_FIELD_ALIASES["margin"])
    update_time = _extract_scalar_field(record, POSITION_TIME_FIELD_ALIASES)

    snapshot_entry: Dict[str, Any] = {
        k: v for k, v in record.items() if isinstance(v, (int, float, str, bool)) or v is None
    }
    snapshot_entry["symbol"] = symbol
    snapshot_entry["positionAmt"] = position_amt

    if entry_price is not None:
        snapshot_entry["entryPrice"] = entry_price
        snapshot_entry["entry"] = entry_price
        snapshot_entry["entry_price"] = entry_price

    if mark_price is not None:
        snapshot_entry["markPrice"] = mark_price
        snapshot_entry["mark"] = mark_price
        snapshot_entry["mark_price"] = mark_price

    if update_time is not None:
        snapshot_entry["updateTime"] = update_time

    if leverage is not None:
        snapshot_entry["leverage"] = leverage

    if notional is None:
        price_for_notional = None
        if mark_price is not None and mark_price > 0:
            price_for_notional = mark_price
        elif entry_price is not None and entry_price > 0:
            price_for_notional = entry_price
        if price_for_notional is not None:
            notional = abs(position_amt) * price_for_notional

    if notional is not None:
        snapshot_entry["notional"] = notional
        snapshot_entry["notional_usdt"] = notional
        snapshot_entry["notionalUsd"] = notional
        snapshot_entry["positionNotional"] = notional
        snapshot_entry["size_usdt"] = notional

    if (
        (margin_val is None or (isinstance(margin_val, (int, float)) and margin_val <= 0))
        and notional is not None
        and leverage
    ):
        try:
            if leverage > 0:
                margin_val = abs(notional) / leverage
        except ZeroDivisionError:
            margin_val = None

    if margin_val is not None:
        snapshot_entry["margin"] = margin_val
        snapshot_entry["positionMargin"] = margin_val
        snapshot_entry.setdefault("isolatedMargin", margin_val)
        snapshot_entry.setdefault("initialMargin", margin_val)

    computed_pnl: Optional[float] = None
    if entry_price is not None and mark_price is not None:
        try:
            computed_pnl = (mark_price - entry_price) * position_amt
        except Exception:
            computed_pnl = None

    if computed_pnl is not None:
        snapshot_entry["computedPnl"] = computed_pnl
        snapshot_entry["computed_pnl"] = computed_pnl

    if unrealized is not None and "unRealizedProfit" not in snapshot_entry:
        snapshot_entry["unRealizedProfit"] = unrealized

    pnl_value = computed_pnl if computed_pnl is not None else unrealized
    if pnl_value is not None:
        snapshot_entry["pnl"] = pnl_value
        snapshot_entry["pnl_usd"] = pnl_value
        snapshot_entry["pnl_usdt"] = pnl_value
        snapshot_entry["pnl_unrealized"] = pnl_value
        snapshot_entry["unrealized"] = pnl_value
        snapshot_entry["unrealizedProfit"] = pnl_value
        snapshot_entry["unRealizedProfit"] = pnl_value

    roe = None
    pnl_for_roe = computed_pnl if computed_pnl is not None else unrealized
    denominator = None
    if margin_val is not None and margin_val > 0:
        denominator = margin_val
    elif notional is not None and notional > 0:
        denominator = notional
    if pnl_for_roe is not None and denominator:
        try:
            roe = (pnl_for_roe / denominator) * 100.0
        except ZeroDivisionError:
            roe = None
    if roe is not None:
        snapshot_entry["roe_percent"] = roe
        snapshot_entry["roe"] = roe
        snapshot_entry["roe_pct"] = roe

    if position_amt > 0:
        snapshot_entry.setdefault("side", "BUY")
    elif position_amt < 0:
        snapshot_entry.setdefault("side", "SELL")

    return snapshot_entry


def _extract_positions_from_payload(payload: Any, fallback_symbol: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    collected: Dict[str, Dict[str, Any]] = {}

    def _collect(node: Any, current_fallback: Optional[str]) -> None:
        if isinstance(node, dict):
            symbol_hint = _resolve_symbol_from_record(node, current_fallback)
            if _looks_like_position_record(node):
                entry = _build_snapshot_entry_from_record(node, symbol_hint)
                if entry is not None:
                    symbol_key = entry.get("symbol")
                    if symbol_key:
                        existing = collected.get(symbol_key)
                        if existing:
                            existing.update({k: v for k, v in entry.items() if v is not None})
                        else:
                            collected[symbol_key] = entry
            for value in node.values():
                _collect(value, symbol_hint or current_fallback)
        elif isinstance(node, list):
            for item in node:
                _collect(item, current_fallback)

    _collect(payload, fallback_symbol)
    return collected


def _fetch_open_orders_snapshot_with_context(
    base: str, api_key: str, api_secret: str, recv_window: int
) -> Dict[str, Dict[str, Any]]:
    if not api_key or not api_secret:
        return {}

    params = {"timestamp": int(time.time() * 1000), "recvWindow": recv_window}
    ordered = [(k, params[k]) for k in sorted(params)]
    qs = urlencode(ordered, doseq=True)
    signature = hmac.new(api_secret.encode(), qs.encode(), hashlib.sha256).hexdigest()
    url = f"{base}/fapi/v1/openOrders?{qs}&signature={signature}"
    headers = {"X-MBX-APIKEY": api_key, "Content-Type": "application/x-www-form-urlencoded"}

    try:
        resp = requests.get(url, headers=headers, timeout=8)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as exc:
        logger.debug("open orders fetch failed: %s", exc)
        return {}

    if payload is None:
        return {}

    return _extract_positions_from_payload(payload)


def _fetch_open_orders_snapshot(env: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    base, api_key, api_secret, recv_window = _resolve_exchange_context(env)
    if not api_key or not api_secret:
        return {}
    if _is_truthy(env.get("ASTER_PAPER")):
        return {}
    return _fetch_open_orders_snapshot_with_context(base, api_key, api_secret, recv_window)


def _merge_snapshot_maps(
    target: Dict[str, Dict[str, Any]], source: Dict[str, Dict[str, Any]], *, prefer_existing: bool = True
) -> None:
    for symbol, payload in source.items():
        if not isinstance(payload, dict):
            continue
        existing = target.get(symbol)
        if existing is None:
            target[symbol] = dict(payload)
            continue
        for key, value in payload.items():
            if value is None:
                continue
            if prefer_existing and key in existing and existing.get(key) not in {None, ""}:
                continue
            existing[key] = value


def _fetch_position_risk_snapshot_with_context(
    base: str, api_key: str, api_secret: str, recv_window: int
) -> Dict[str, Dict[str, Any]]:
    if not api_key or not api_secret:
        return {}

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
        entry = _build_snapshot_entry_from_record(item)
        if entry is None:
            continue
        symbol = entry.get("symbol")
        if not symbol:
            continue
        snapshot[symbol] = entry

    return snapshot


def _fetch_position_risk_snapshot(env: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    base, api_key, api_secret, recv_window = _resolve_exchange_context(env)
    if not api_key or not api_secret:
        return {}
    if _is_truthy(env.get("ASTER_PAPER")):
        return {}
    return _fetch_position_risk_snapshot_with_context(base, api_key, api_secret, recv_window)


def _fetch_position_snapshot(env: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    base, api_key, api_secret, recv_window = _resolve_exchange_context(env)
    if not api_key or not api_secret:
        return {}
    if _is_truthy(env.get("ASTER_PAPER")):
        return {}

    snapshot = _fetch_open_orders_snapshot_with_context(base, api_key, api_secret, recv_window)
    if snapshot:
        fallback = _fetch_position_risk_snapshot_with_context(base, api_key, api_secret, recv_window)
        if fallback:
            _merge_snapshot_maps(snapshot, fallback, prefer_existing=True)
    else:
        snapshot = _fetch_position_risk_snapshot_with_context(base, api_key, api_secret, recv_window)

    if not snapshot:
        return {}

    try:
        bracket_levels = _fetch_position_brackets(env, snapshot.keys(), recv_window)
    except Exception as exc:
        logger.debug("position bracket fetch failed: %s", exc)
    else:
        if bracket_levels:
            for symbol_key, entry in snapshot.items():
                levels_for_symbol = bracket_levels.get(symbol_key)
                if not isinstance(levels_for_symbol, dict):
                    continue
                side_key = str(entry.get("side") or "").upper()
                if not side_key:
                    amt = _safe_float(entry.get("positionAmt") or entry.get("qty") or entry.get("size"))
                    if amt is not None:
                        if amt > 0:
                            side_key = "BUY"
                        elif amt < 0:
                            side_key = "SELL"
                bucket = levels_for_symbol.get(side_key) or levels_for_symbol.get("ANY")
                if not isinstance(bucket, dict):
                    continue
                take_px = bucket.get("take")
                stop_px = bucket.get("stop")
                if take_px is not None:
                    _apply_bracket_price(entry, "take", take_px)
                if stop_px is not None:
                    _apply_bracket_price(entry, "stop", stop_px)

    return snapshot


TAKE_PROFIT_FIELD_KEYS: Tuple[str, ...] = (
    "tp",
    "take",
    "take_price",
    "takePrice",
    "take_profit",
    "take_profit_price",
    "take_profit_next",
    "takeProfit",
    "takeProfitPrice",
    "takeProfitNext",
    "tp_price",
    "tpPrice",
    "tp_target",
    "tpTarget",
    "next_tp",
    "target",
    "target_price",
    "targetPrice",
)

STOP_LOSS_FIELD_KEYS: Tuple[str, ...] = (
    "sl",
    "stop",
    "stop_price",
    "stopPrice",
    "stop_price_next",
    "stopPriceNext",
    "stop_loss",
    "stop_loss_price",
    "stop_loss_next",
    "stopLoss",
    "stopLossPrice",
    "stopLossNext",
    "stop_target",
    "stopTarget",
    "stop_trigger",
    "stopTrigger",
    "next_stop",
)


def _apply_bracket_price(record: Dict[str, Any], kind: str, price: Any) -> None:
    if not isinstance(record, dict):
        return

    meta: Optional[Dict[str, Any]]
    numeric_price: Optional[float]

    if isinstance(price, dict):
        meta = dict(price)
        numeric_price = None
        for candidate in (
            meta.get("price"),
            meta.get("stopPrice"),
            meta.get("triggerPrice"),
            meta.get("limitPrice"),
        ):
            numeric_price = _safe_float(candidate)
            if numeric_price is not None:
                break
        if numeric_price is None:
            return
        meta["price"] = numeric_price
    else:
        meta = None
        numeric_price = _safe_float(price)
        if numeric_price is None:
            return

    if numeric_price <= 0:
        return

    keys = TAKE_PROFIT_FIELD_KEYS if kind == "take" else STOP_LOSS_FIELD_KEYS

    for key in keys:
        record[key] = numeric_price

    if meta is not None:
        normalized_meta: Dict[str, Any] = {"price": numeric_price}
        for field in ("type", "workingType", "positionSide", "source"):
            value = meta.get(field)
            if value is None:
                continue
            if isinstance(value, str):
                normalized_meta[field] = value
            else:
                normalized_meta[field] = value
        for flag in ("reduceOnly", "closePosition", "inferredReduceOnly"):
            if flag in meta:
                normalized_meta[flag] = bool(meta.get(flag))
        for extra_field in ("triggerPrice", "stopPrice", "limitPrice"):
            extra_val = _safe_float(meta.get(extra_field))
            if extra_val is not None:
                normalized_meta[extra_field] = extra_val
        record.setdefault("tp_sl_meta", {})[kind] = normalized_meta


def _entry_has_bracket_prices(record: Dict[str, Any]) -> bool:
    if not isinstance(record, dict):
        return False

    for key in TAKE_PROFIT_FIELD_KEYS + STOP_LOSS_FIELD_KEYS:
        if key not in record:
            continue
        if _safe_float(record.get(key)) not in {None, 0.0}:
            return True
    return False


def _fetch_position_brackets(
    env: Dict[str, Any],
    symbols: Iterable[str],
    recv_window: int,
) -> Dict[str, Dict[str, Dict[str, float]]]:
    base = (env.get("ASTER_EXCHANGE_BASE") or "https://fapi.asterdex.com").rstrip("/")
    api_key = (env.get("ASTER_API_KEY") or "").strip()
    api_secret = (env.get("ASTER_API_SECRET") or "").strip()
    if not api_key or not api_secret:
        return {}
    if _is_truthy(env.get("ASTER_PAPER")):
        return {}

    headers = {"X-MBX-APIKEY": api_key, "Content-Type": "application/x-www-form-urlencoded"}
    results: Dict[str, Dict[str, Dict[str, float]]] = {}
    seen: Set[str] = set()

    for raw_symbol in symbols:
        if not raw_symbol:
            continue
        symbol = str(raw_symbol).upper().strip()
        if not symbol or symbol in seen:
            continue
        seen.add(symbol)

        params = {
            "symbol": symbol,
            "timestamp": int(time.time() * 1000),
            "recvWindow": recv_window,
        }
        ordered = [(k, params[k]) for k in sorted(params)]
        qs = urlencode(ordered, doseq=True)
        signature = hmac.new(api_secret.encode(), qs.encode(), hashlib.sha256).hexdigest()
        url = f"{base}/fapi/v1/openOrders?{qs}&signature={signature}"

        try:
            resp = requests.get(url, headers=headers, timeout=8)
            resp.raise_for_status()
            payload = resp.json()
        except Exception as exc:
            logger.debug("open orders fetch failed for %s: %s", symbol, exc)
            continue

        if isinstance(payload, list):
            orders = payload
        elif isinstance(payload, dict):
            if isinstance(payload.get("orders"), list):
                orders = payload["orders"]
            elif isinstance(payload.get("data"), list):
                orders = payload["data"]
            else:
                lists = [value for value in payload.values() if isinstance(value, list)]
                orders = lists[0] if lists else []
        else:
            orders = []

        if not isinstance(orders, list) or not orders:
            continue

        for order in orders:
            if not isinstance(order, dict):
                continue
            order_type_raw = order.get("type")
            order_type = str(order_type_raw or "").upper()
            order_type_norm = order_type.replace("-", "_").replace(" ", "_")
            if "STOP" not in order_type_norm and "TAKE_PROFIT" not in order_type_norm:
                continue

            close_position = _is_truthy(order.get("closePosition"))
            reduce_only = _is_truthy(order.get("reduceOnly"))
            inferred_reduce = False

            if not close_position and not reduce_only:
                # Some venues omit these flags on reduce-only exit orders. In that
                # case we infer the intent from the declared side: take-profit/
                # stop orders that move in the opposite direction of the open
                # position are still valid bracket levels.
                order_side = str(order.get("side") or "").upper()
                position_side_hint = str(order.get("positionSide") or "").upper()
                if position_side_hint in {"LONG", "BOTH"}:
                    inferred_reduce = order_side == "SELL"
                elif position_side_hint == "SHORT":
                    inferred_reduce = order_side == "BUY"
                elif order_side in {"BUY", "SELL"}:
                    inferred_reduce = True
                if not inferred_reduce:
                    continue

            price_candidates = (
                order.get("stopPrice"),
                order.get("triggerPrice"),
                order.get("price"),
            )
            price_val: Optional[float] = None
            for candidate in price_candidates:
                price_val = _safe_float(candidate)
                if price_val is not None:
                    break
            if price_val is None:
                trigger = order.get("trigger")
                if isinstance(trigger, dict):
                    price_val = _safe_float(trigger.get("price"))
            if price_val is None:
                continue

            position_side_raw = str(order.get("positionSide") or "").upper()
            if position_side_raw in {"LONG", "BOTH"}:
                side_key = "BUY"
            elif position_side_raw == "SHORT":
                side_key = "SELL"
            else:
                order_side = str(order.get("side") or "").upper()
                if order_side == "SELL":
                    side_key = "BUY"
                elif order_side == "BUY":
                    side_key = "SELL"
                else:
                    side_key = "ANY"

            bucket = results.setdefault(symbol, {}).setdefault(side_key or "ANY", {})

            kind = "take" if "TAKE_PROFIT" in order_type_norm else "stop"
            existing = bucket.get(kind)
            if existing is not None:
                if isinstance(existing, dict):
                    existing_val = _safe_float(existing.get("price"))
                else:
                    try:
                        existing_val = float(existing)
                    except (TypeError, ValueError):
                        existing_val = None
            else:
                existing_val = None

            working_type_raw = order.get("workingType") or order.get("priceType")
            working_type = str(working_type_raw).upper().strip() if working_type_raw else None

            order_meta = {
                "price": price_val,
                "type": order_type,
                "workingType": working_type,
                "reduceOnly": bool(reduce_only or inferred_reduce),
                "closePosition": bool(close_position),
                "positionSide": position_side_raw or None,
                "source": "openOrders",
            }

            trigger_price_val = _safe_float(order.get("triggerPrice"))
            if trigger_price_val is not None:
                order_meta["triggerPrice"] = trigger_price_val

            stop_price_val = _safe_float(order.get("stopPrice"))
            if stop_price_val is not None and stop_price_val != trigger_price_val:
                order_meta["stopPrice"] = stop_price_val

            limit_price_val = _safe_float(order.get("price"))
            if limit_price_val is not None and limit_price_val != price_val:
                order_meta["limitPrice"] = limit_price_val

            if inferred_reduce and not reduce_only:
                order_meta["inferredReduceOnly"] = True

            if side_key == "BUY":
                if kind == "stop":
                    if existing_val is None or price_val > existing_val:
                        bucket[kind] = order_meta
                else:
                    if existing_val is None or price_val < existing_val:
                        bucket[kind] = order_meta
            elif side_key == "SELL":
                if kind == "stop":
                    if existing_val is None or price_val < existing_val:
                        bucket[kind] = order_meta
                else:
                    if existing_val is None or price_val > existing_val:
                        bucket[kind] = order_meta
            else:
                if existing_val is None:
                    bucket[kind] = order_meta

    return results


POSITION_HINT_KEYS = {"entry", "entryPrice", "qty", "quantity", "positionAmt", "side", "tp", "sl", "mark"}

POSITION_NUMERIC_FIELD_ALIASES = {
    "position_amt": (
        "positionAmt",
        "position_amt",
        "position_amount",
        "positionSize",
        "position_size",
        "positionQty",
        "position_qty",
        "qty",
        "quantity",
        "size",
        "size_contracts",
        "amount",
        "amount_contracts",
        "origQty",
        "executedQty",
        "baseQty",
        "base_quantity",
        "baseAmount",
        "base_amount",
    ),
    "entry_price": (
        "entryPrice",
        "entry_price",
        "entry",
        "avgEntryPrice",
        "avgPrice",
        "avg_price",
        "averagePrice",
        "average_price",
        "entryprice",
        "entryPriceValue",
        "entryValue",
    ),
    "mark_price": (
        "markPrice",
        "mark_price",
        "mark",
        "lastPrice",
        "last_price",
        "price",
        "marketPrice",
        "indexPrice",
        "markprice",
    ),
    "unrealized": (
        "unRealizedProfit",
        "unrealizedProfit",
        "unRealizedPnl",
        "unrealized",
        "pnl",
        "pnl_unrealized",
        "pnlUnrealized",
        "pnl_usd",
        "pnl_usdt",
        "pnlUsd",
        "pnlUsdt",
        "computedPnl",
        "computed_pnl",
    ),
    "notional": (
        "positionNotional",
        "position_notional",
        "notional",
        "notional_usdt",
        "notionalUsd",
        "notionalUSD",
        "size_usdt",
        "sizeUsd",
        "position_value",
        "positionValue",
        "notionalValue",
    ),
    "leverage": ("leverage", "lever", "leverage_value", "leverageValue"),
    "margin": (
        "positionMargin",
        "position_margin",
        "margin",
        "isolatedMargin",
        "initialMargin",
        "positionInitialMargin",
        "margin_usd",
        "marginUsd",
        "margin_usdt",
        "maintMargin",
        "maintenanceMargin",
    ),
}

POSITION_TIME_FIELD_ALIASES = (
    "updateTime",
    "update_time",
    "timestamp",
    "time",
    "openTime",
    "open_time",
    "createdTime",
    "created_time",
    "createdAt",
    "created_at",
)


def _extract_nested_value(candidate: Any, *, numeric: bool) -> Optional[Any]:
    if candidate is None:
        return None
    if isinstance(candidate, (list, tuple, set)):
        for item in candidate:
            value = _extract_nested_value(item, numeric=numeric)
            if value is not None:
                return value
        return None
    if isinstance(candidate, dict):
        for key in ("value", "amount", "qty", "quantity", "price", "notional", "num", "number"):
            if key not in candidate:
                continue
            value = _extract_nested_value(candidate.get(key), numeric=numeric)
            if value is not None:
                return value
        return None
    if numeric:
        return _safe_float(candidate)
    return candidate


def _extract_numeric_field(record: Dict[str, Any], aliases: Sequence[str]) -> Optional[float]:
    for key in aliases:
        if key not in record:
            continue
        value = _extract_nested_value(record.get(key), numeric=True)
        if value is not None:
            return value
    return None


def _extract_scalar_field(record: Dict[str, Any], aliases: Sequence[str]) -> Optional[Any]:
    for key in aliases:
        if key not in record:
            continue
        value = _extract_nested_value(record.get(key), numeric=False)
        if value is not None:
            return value
    return None


def _resolve_exchange_context(env: Dict[str, Any]) -> Tuple[str, str, str, int]:
    base = (env.get("ASTER_EXCHANGE_BASE") or "https://fapi.asterdex.com").rstrip("/")
    api_key = (env.get("ASTER_API_KEY") or "").strip()
    api_secret = (env.get("ASTER_API_SECRET") or "").strip()
    try:
        recv_window = int(float(env.get("ASTER_RECV_WINDOW", 10000)))
    except (TypeError, ValueError):
        recv_window = 10000
    return base, api_key, api_secret, recv_window


def _resolve_symbol_from_record(record: Dict[str, Any], fallback: Optional[str] = None) -> Optional[str]:
    candidates = [
        record.get("symbol"),
        record.get("sym"),
        record.get("ticker"),
        record.get("pair"),
        fallback,
    ]
    for candidate in candidates:
        text = _clean_string(candidate)
        if text:
            return text.upper()
    return None


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


def _infer_income_trade_side(entry: Dict[str, Any]) -> Optional[str]:
    """Best-effort inference of the executed side for a realized PnL entry."""

    side_candidates = [entry.get("side"), entry.get("positionSide")]
    for candidate in side_candidates:
        text = _clean_string(candidate)
        if not text:
            continue
        token = text.upper()
        if token in {"BUY", "SELL"}:
            return token
        if token in {"LONG", "SHORT"}:
            return "BUY" if token == "LONG" else "SELL"

    info = _clean_string(entry.get("info"))
    if info:
        match = re.search(r"side[:=]\s*(buy|sell)", info, flags=re.IGNORECASE)
        if match:
            return match.group(1).upper()
        info_upper = info.upper()
        if "SELL" in info_upper and "BUY" not in info_upper:
            return "SELL"
        if "BUY" in info_upper and "SELL" not in info_upper:
            return "BUY"

    return None


def _build_synthetic_trade_from_income(entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    symbol = _clean_string(entry.get("symbol") or entry.get("asset"))
    income_val = _safe_float(entry.get("income"))
    timestamp = _safe_float(entry.get("time"))

    if not symbol or income_val is None or timestamp is None:
        return None

    record: Dict[str, Any] = {
        "symbol": symbol,
        "pnl": float(income_val),
        "pnl_r": 0.0,
        "opened_at": float(timestamp),
        "closed_at": float(timestamp),
        "synthetic": True,
        "synthetic_source": "realized_income",
        "context": {"source": "realized_income"},
        "notes": ["Synthesized from exchange realized PnL feed."],
    }

    side = _infer_income_trade_side(entry)
    if side:
        record["side"] = side

    income_type = _clean_string(entry.get("incomeType"))
    if income_type:
        record["context"]["income_type"] = income_type

    info = _clean_string(entry.get("info"))
    if info:
        record["context"]["income_info"] = info

    for key in ("orderId", "matchOrderId", "tradeId"):
        if entry.get(key) is not None:
            record["context"][key.lower()] = entry.get(key)

    return record


def _merge_realized_pnl(history: List[Dict[str, Any]], realized: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    history_list = list(history or [])
    if not realized:
        return history_list

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
    for trade in history_list:
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
                    prev_pnl = _safe_float(record.get("pnl"))
                    prev_r = _safe_float(record.get("pnl_r"))
                    if prev_pnl is not None and "estimated_pnl" not in record:
                        try:
                            record["estimated_pnl"] = float(prev_pnl)
                        except (TypeError, ValueError):
                            record["estimated_pnl"] = prev_pnl
                    record["realized_pnl"] = realized_sum
                    record["pnl"] = realized_sum
                    new_r: Optional[float] = None
                    if (
                        prev_r is not None
                        and abs(prev_r) > 1e-9
                    ):
                        risk_reference = _safe_float(record.get("estimated_pnl"))
                        if risk_reference is None:
                            risk_reference = prev_pnl
                        if (
                            risk_reference is not None
                            and abs(risk_reference) > 1e-9
                        ):
                            risk_unit = risk_reference / prev_r
                            if (
                                risk_unit is not None
                                and math.isfinite(risk_unit)
                                and abs(risk_unit) > 1e-9
                            ):
                                new_r = realized_sum / risk_unit
                    if new_r is not None and math.isfinite(new_r):
                        record["pnl_r"] = new_r
                    timeline[symbol] = remaining
        merged.append(record)

    synthetic_trades: List[Dict[str, Any]] = []
    for entries in timeline.values():
        for entry in entries:
            synthetic = _build_synthetic_trade_from_income(entry)
            if synthetic:
                synthetic_trades.append(synthetic)

    synthetic_trades.sort(key=lambda item: item.get("closed_at", item.get("opened_at", 0)))
    merged.extend(synthetic_trades)

    return merged


def _is_realized_income_trade(record: Dict[str, Any]) -> bool:
    """Return True when a trade record represents a synthetic realized-income entry."""

    if not isinstance(record, dict):
        return False

    source = _clean_string(record.get("synthetic_source"))
    if source and source.lower() == "realized_income":
        return True

    # Some older synthetic entries were only tagged via the context metadata.
    # However, real trades may now include a context source label, so only
    # treat the context as authoritative when the record is explicitly marked
    # synthetic. This prevents legitimate trades from being filtered out of
    # the dashboard history while still hiding synthetic realized-income rows.
    if record.get("synthetic"):
        context = record.get("context")
        if isinstance(context, dict):
            ctx_source = _clean_string(context.get("source"))
            if ctx_source and ctx_source.lower() == "realized_income":
                return True

    return False


def _strip_realized_income_trades(history: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Drop realized-income synthetic trades from a history list."""

    filtered: List[Dict[str, Any]] = []
    for entry in history:
        if not _is_realized_income_trade(entry):
            filtered.append(entry)
    return filtered


def _build_history_summary(stats: TradeStats) -> Dict[str, Any]:
    avg_r = 0.0
    if stats.count:
        try:
            avg_r = float(stats.total_r or 0.0) / float(stats.count)
        except ZeroDivisionError:
            avg_r = 0.0
    summary = {
        "trades": int(stats.count or 0),
        "realized_pnl": float(stats.total_pnl or 0.0),
        "total_r": float(stats.total_r or 0.0),
        "avg_r": avg_r,
        "win_rate": float(stats.win_rate or 0.0),
        "wins": int(getattr(stats, "wins", 0) or 0),
        "losses": int(getattr(stats, "losses", 0) or 0),
        "draws": int(getattr(stats, "draws", 0) or 0),
    }
    return summary


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

    notional = extra.get("notional") or extra.get("notional_usdt") or extra.get("positionNotional")
    if notional is not None:
        merged.setdefault("notional", notional)
        merged.setdefault("notional_usdt", notional)
        merged.setdefault("notionalUsd", notional)
        merged.setdefault("positionNotional", notional)
        merged.setdefault("size_usdt", notional)

    position_amt = extra.get("positionAmt")
    if position_amt is not None:
        merged.setdefault("qty", position_amt)
        merged.setdefault("size", position_amt)
        merged["positionAmt"] = position_amt

    computed_pnl = extra.get("computedPnl")
    if computed_pnl is None:
        computed_pnl = extra.get("computed_pnl")
    unrealized = extra.get("unRealizedProfit")
    pnl_value = computed_pnl if computed_pnl is not None else unrealized
    if pnl_value is not None:
        merged["pnl"] = pnl_value
        merged["unrealized"] = pnl_value
        merged["unrealizedProfit"] = pnl_value
        merged["pnl_unrealized"] = pnl_value
        merged["pnl_usd"] = pnl_value
        merged["pnl_usdt"] = pnl_value
    if computed_pnl is not None:
        merged["computedPnl"] = computed_pnl
        merged["computed_pnl"] = computed_pnl
    if unrealized is not None:
        merged.setdefault("unRealizedProfit", unrealized)

    roe = extra.get("roe_percent")
    if roe is not None:
        merged["roe"] = roe
        merged["roe_percent"] = roe
        merged["roi"] = roe
        merged["roi_percent"] = roe

    leverage = extra.get("leverage")
    if leverage is not None:
        merged.setdefault("leverage", leverage)

    margin_candidates = [
        extra.get("margin"),
        extra.get("positionMargin"),
        extra.get("isolatedMargin"),
        extra.get("initialMargin"),
        extra.get("positionInitialMargin"),
    ]
    for margin_val in margin_candidates:
        if margin_val is None:
            continue
        try:
            numeric_margin = float(margin_val)
        except (TypeError, ValueError):
            numeric_margin = None
        if numeric_margin is None or numeric_margin <= 0:
            continue
        merged["margin"] = margin_val
        merged["positionMargin"] = margin_val
        merged.setdefault("isolatedMargin", margin_val)
        break

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
    snapshot = _fetch_position_snapshot(env)
    if not snapshot:
        return open_payload

    if not open_payload:
        return list(snapshot.values())

    payload_copy = copy.deepcopy(open_payload)
    merged_payload = _merge_position_payload(payload_copy, snapshot)

    def _register(record: Dict[str, Any]) -> None:
        if not isinstance(record, dict):
            return
        symbol_raw = record.get("symbol") or record.get("sym") or record.get("ticker") or record.get("pair")
        if not symbol_raw:
            return
        symbol_key = str(symbol_raw).upper().strip()
        if not symbol_key:
            return
        side_raw = record.get("side") or record.get("positionSide") or record.get("direction")
        if isinstance(side_raw, str):
            side_key = side_raw.strip().upper()
        else:
            side_key = None
        if not side_key:
            amount_val = _safe_float(record.get("positionAmt") or record.get("qty") or record.get("size"))
            if amount_val is not None:
                if amount_val > 0:
                    side_key = "BUY"
                elif amount_val < 0:
                    side_key = "SELL"
        composite_key = f"{symbol_key}:{side_key}" if side_key else symbol_key
        entry = combined.setdefault(composite_key, {})
        entry.update(record)
        entry.setdefault("symbol", symbol_key)
        if side_key:
            entry.setdefault("side", side_key)

    def _collect(payload: Any) -> None:
        if isinstance(payload, dict):
            if _looks_like_position_record(payload):
                _register(payload)
            else:
                for value in payload.values():
                    _collect(value)
        elif isinstance(payload, list):
            for item in payload:
                _collect(item)

    combined: Dict[str, Dict[str, Any]] = {}
    for extra in snapshot.values():
        _register(extra)
    _collect(merged_payload)

    if combined:
        _, api_key, api_secret, recv_window = _resolve_exchange_context(env)
        if api_key and api_secret and not _is_truthy(env.get("ASTER_PAPER")):
            missing_symbols: Set[str] = set()
            for composite_key, entry in combined.items():
                if _entry_has_bracket_prices(entry):
                    continue
                symbol_key, _, _ = composite_key.partition(":")
                if symbol_key:
                    missing_symbols.add(symbol_key)
            if missing_symbols:
                try:
                    bracket_levels = _fetch_position_brackets(env, missing_symbols, recv_window)
                except Exception as exc:
                    logger.debug("position bracket refresh failed: %s", exc)
                else:
                    for composite_key, entry in combined.items():
                        symbol_key, _, side_key = composite_key.partition(":")
                        if not symbol_key:
                            continue
                        side_hint = side_key or str(entry.get("side") or "").upper()
                        levels_for_symbol = bracket_levels.get(symbol_key)
                        if not isinstance(levels_for_symbol, dict):
                            continue
                        bucket = None
                        if side_hint:
                            bucket = levels_for_symbol.get(side_hint) or levels_for_symbol.get(side_hint.upper())
                        if not bucket:
                            bucket = levels_for_symbol.get("ANY")
                        if not isinstance(bucket, dict):
                            continue
                        take_px = bucket.get("take")
                        stop_px = bucket.get("stop")
                        if take_px is not None:
                            _apply_bracket_price(entry, "take", take_px)
                        if stop_px is not None:
                            _apply_bracket_price(entry, "stop", stop_px)

    if combined:
        return list(combined.values())
    return merged_payload

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

    if os.getenv("ASTER_RISK_PER_TRADE") is None:
        stored_risk = env_cfg.get("ASTER_RISK_PER_TRADE")
        default_risk = ENV_DEFAULTS.get("ASTER_RISK_PER_TRADE")
        looks_default = stored_risk is None or str(stored_risk).strip() == str(default_risk)
        if looks_default:
            preset = (merged.get("ASTER_PRESET_MODE") or "").strip().lower()
            mode = (merged.get("ASTER_MODE") or "").strip().lower()
            ai_flag = os.getenv("ASTER_AI_MODE")
            if ai_flag is None:
                ai_flag = merged.get("ASTER_AI_MODE")
            ai_enabled = mode == "ai" or _is_truthy(ai_flag)
            if ai_enabled and preset in {"high", "att"}:
                merged["ASTER_RISK_PER_TRADE"] = "0.10"

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
    wins: int = 0
    losses: int = 0
    draws: int = 0


class ChatMessagePayload(BaseModel):
    role: str
    content: str


class ChatRequestPayload(BaseModel):
    message: str = Field(..., min_length=1)
    history: List[ChatMessagePayload] = Field(default_factory=list)


class ProposalExecutionRequest(BaseModel):
    proposal_id: str = Field(..., min_length=4, alias="proposalId")

    model_config = ConfigDict(populate_by_name=True)


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


class PositionStream:
    """Broadcast real-time active position updates to connected clients."""

    def __init__(self, poll_interval: float = 1.0) -> None:
        self.clients: Set[WebSocket] = set()
        self._lock = asyncio.Lock()
        self._task: Optional[asyncio.Task] = None
        self._latest_payload: Optional[Any] = None
        self._last_signature: Optional[str] = None
        self.poll_interval = poll_interval

    async def register(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self.clients.add(ws)
            snapshot = copy.deepcopy(self._latest_payload)
        if snapshot is not None:
            await self._safe_send(ws, snapshot)

    async def unregister(self, ws: WebSocket) -> None:
        async with self._lock:
            self.clients.discard(ws)

    def start(self) -> None:
        if self._task and not self._task.done():
            return
        loop = asyncio.get_event_loop()
        self._task = loop.create_task(self._run())

    async def stop(self) -> None:
        if not self._task:
            return
        task = self._task
        self._task = None
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:  # pragma: no cover - shutdown best effort
            pass

    async def _run(self) -> None:
        while True:
            try:
                await self._refresh()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # pragma: no cover - diagnostic logging
                logger.debug("position stream refresh failed: %s", exc)
            await asyncio.sleep(self.poll_interval)

    async def _refresh(self) -> None:
        state = _read_state()
        open_payload = state.get("live_trades", {})
        signature = self._hash_payload(open_payload)
        if signature == self._last_signature:
            return
        env_cfg = CONFIG.get("env", {})
        try:
            enriched = await asyncio.to_thread(enrich_open_positions, open_payload, env_cfg)
        except Exception as exc:
            logger.debug("position stream enrichment error: %s", exc)
            enriched = open_payload
        self._last_signature = signature
        async with self._lock:
            self._latest_payload = enriched
            clients = list(self.clients)
        payload = {"type": "positions", "open": enriched}
        for ws in clients:
            await self._safe_send(ws, payload)

    def _hash_payload(self, payload: Any) -> str:
        try:
            encoded = json.dumps(
                payload,
                sort_keys=True,
                default=lambda obj: obj if isinstance(obj, (int, float, str, bool)) else repr(obj),
            ).encode("utf-8")
        except Exception:
            encoded = repr(payload).encode("utf-8", errors="ignore")
        return hashlib.sha1(encoded).hexdigest()

    async def _safe_send(self, ws: WebSocket, payload: Dict[str, Any]) -> None:
        try:
            await ws.send_json(payload)
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
position_stream = PositionStream()
runner = BotRunner(loghub)


@asynccontextmanager
async def dashboard_lifespan(_: FastAPI):
    position_stream.start()
    try:
        yield
    finally:
        await position_stream.stop()


app = FastAPI(title="Aster Bot Control Center", lifespan=dashboard_lifespan)
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


def _resolve_run_started_at(state: Dict[str, Any]) -> Optional[float]:
    run_started = _safe_float((state or {}).get("run_started_at"))
    if run_started is not None and run_started > 0:
        return run_started
    runner_started = getattr(runner, "started_at", None)
    fallback = _safe_float(runner_started)
    if fallback is not None and fallback > 0:
        return fallback
    return None


def _filter_history_for_run(
    history_entries: Iterable[Any], run_started_at: Optional[float]
) -> List[Dict[str, Any]]:
    filtered: List[Dict[str, Any]] = []
    collected: List[Dict[str, Any]] = []

    if run_started_at is None:
        for entry in history_entries:
            if isinstance(entry, dict):
                collected.append(entry)
        return collected

    cutoff = float(run_started_at)
    for entry in history_entries:
        if not isinstance(entry, dict):
            continue
        collected.append(entry)
        closed_ts = _safe_float(entry.get("closed_at"))
        opened_ts = _safe_float(entry.get("opened_at"))
        if closed_ts is not None and closed_ts >= cutoff:
            filtered.append(entry)
            continue
        if closed_ts is None and opened_ts is not None and opened_ts >= cutoff:
            filtered.append(entry)

    if filtered:
        return filtered

    # When the active run hasn't produced any trades yet, fall back to the
    # most recent historical entries so the trade history still renders.
    return collected


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


def _ensure_ai_budget_bucket(state: Dict[str, Any]) -> Dict[str, Any]:
    bucket = state.setdefault("ai_budget", {})
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if bucket.get("date") != today:
        bucket["date"] = today
        bucket["spent"] = 0.0
        bucket["history"] = []
        bucket["stats"] = {}
        bucket["count"] = 0
    bucket.setdefault("spent", 0.0)
    history = bucket.get("history")
    if not isinstance(history, list):
        history = []
    bucket["history"] = history
    stats = bucket.get("stats")
    if not isinstance(stats, dict):
        stats = {}
    bucket["stats"] = stats
    count_val = bucket.get("count")
    try:
        count = int(count_val)
    except (TypeError, ValueError):
        count = len(history)
    bucket["count"] = max(int(count or 0), len(history))
    return bucket


def _record_ai_budget_usage(cost: float, meta: Optional[Dict[str, Any]] = None) -> None:
    attempts = 0
    while attempts < 3:
        attempts += 1
        state = _read_state()
        bucket = _ensure_ai_budget_bucket(state)
        amount = max(0.0, float(cost or 0.0))
        try:
            meta_payload = json.loads(json.dumps(meta or {}, default=lambda o: str(o)))
        except Exception:
            meta_payload = meta or {}

        history = bucket.get("history") or []
        if not isinstance(history, list):
            history = []
        history.append({"ts": time.time(), "cost": float(amount), "meta": meta_payload})
        if len(history) > 48:
            history = history[-48:]
        bucket["history"] = history

        bucket["spent"] = float(bucket.get("spent", 0.0) or 0.0) + amount
        bucket["count"] = int(bucket.get("count", 0) or 0) + 1

        stats = bucket.get("stats")
        if not isinstance(stats, dict):
            stats = {}
        bucket["stats"] = stats

        model_key = str(meta_payload.get("model") or "default")
        kind_key = str(meta_payload.get("kind") or "unknown")

        for key in (
            f"{model_key}::{kind_key}",
            f"{model_key}::*",
            f"*::{kind_key}",
            "*::*",
        ):
            record = stats.setdefault(
                key, {"avg": 0.0, "n": 0, "last": 0.0, "updated": 0.0}
            )
            n = int(record.get("n", 0) or 0)
            avg = float(record.get("avg", 0.0) or 0.0)
            new_n = n + 1
            new_avg = ((avg * n) + amount) / max(new_n, 1)
            record.update(
                {
                    "avg": float(new_avg),
                    "n": new_n,
                    "last": float(amount),
                    "updated": time.time(),
                }
            )

        state["ai_budget"] = bucket
        try:
            STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True))
            return
        except Exception as exc:
            logger.debug("Failed to persist AI budget usage (attempt %s): %s", attempts, exc)
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
    symbol_side_index: Dict[str, str] = {}
    for entry in ai_activity:
        if not isinstance(entry, dict):
            continue
        data = entry.get("data")
        if not isinstance(data, dict):
            continue

        raw_origin_hint = data.get("origin") or data.get("plan_origin")
        origin_hint_clean = str(raw_origin_hint or "").strip()

        raw_request_kind = data.get("request_kind")
        request_kind_hint = None
        if isinstance(raw_request_kind, str):
            request_kind_hint = raw_request_kind.strip() or None
        elif raw_request_kind is not None:
            request_kind_hint = str(raw_request_kind)
        request_kind_normalized = (request_kind_hint or "").strip().lower()
        if request_kind_normalized.startswith("playbook"):
            continue

        raw_request_id = data.get("request_id")
        request_id = None
        if isinstance(raw_request_id, str):
            request_id = raw_request_id.strip() or None
        elif raw_request_id is not None:
            request_id = str(raw_request_id)
        request_id_normalized = (request_id or "").strip().lower()
        if request_id_normalized:
            prefix = request_id_normalized.split("::", 1)[0]
            if prefix.startswith("playbook"):
                continue
        if origin_hint_clean and origin_hint_clean.lower().startswith("playbook"):
            continue
        symbol_hint = str(data.get("symbol") or "").strip().upper()
        side_hint = str(data.get("side") or "").strip().upper()
        origin_hint = origin_hint_clean
        base_key = None
        if symbol_hint:
            fallback_side = side_hint or "UNKNOWN"
            base_key = f"{symbol_hint}::{fallback_side}"
        fallback_key = None
        if base_key:
            if origin_hint:
                fallback_key = f"{base_key}::{origin_hint.lower()}"
            else:
                fallback_key = base_key

        preferred_key = request_id or fallback_key or base_key
        if not preferred_key:
            continue

        record_key = None
        record = None

        if request_id:
            record_key = request_id
            record = requests.get(request_id)

        if record is None and fallback_key:
            record_key = fallback_key
            record = requests.get(fallback_key)

        if record is None and base_key and base_key in symbol_side_index:
            alias_key = symbol_side_index[base_key]
            record = requests.get(alias_key)
            if record is not None:
                record_key = alias_key

        if record is None:
            record_key = preferred_key
            record = {
                "id": preferred_key,
                "request_id": request_id,
                "symbol": symbol_hint,
                "side": side_hint or None,
                "origin": origin_hint or None,
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
            requests[record_key] = record
        else:
            if request_id and not record.get("request_id"):
                record["request_id"] = request_id
        if request_id and record_key != request_id:
            # Re-key the record under the resolved request id to prevent duplicates
            requests.pop(record_key, None)
            record_key = request_id
            record["id"] = request_id
            record["request_id"] = request_id
            requests[record_key] = record
        elif preferred_key and record_key != preferred_key:
            requests.pop(record_key, None)
            record_key = preferred_key
            record["id"] = preferred_key
            requests[record_key] = record
        if symbol_hint and not record.get("symbol"):
            record["symbol"] = symbol_hint
        if side_hint and not record.get("side"):
            record["side"] = side_hint
        if origin_hint and not record.get("origin"):
            record["origin"] = origin_hint
        ts = _parse_activity_ts(entry.get("ts"))
        ts_iso = ts.isoformat() if ts else None
        if ts_iso:
            record["updated_at"] = ts_iso
            if record.get("created_at") is None:
                record["created_at"] = ts_iso

        if base_key:
            symbol_side_index[base_key] = record_key

        kind = str(entry.get("kind") or "info").lower()
        record["events"].append(
            {
                "kind": kind,
                "headline": entry.get("headline"),
                "body": entry.get("body"),
                "ts": ts_iso,
            }
        )

        request_payload = data.get("request_payload")
        if request_payload is not None:
            record["request_payload"] = request_payload
        response_payload = data.get("response_payload")
        if response_payload is not None:
            record["response_payload"] = response_payload

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


def _extract_trade_volume(trade: Dict[str, Any]) -> float:
    if not isinstance(trade, dict):
        return 0.0

    def _lookup(candidate_key: str) -> Optional[float]:
        direct = _safe_float(trade.get(candidate_key))
        if direct is not None:
            return direct
        extra = trade.get("extra")
        if isinstance(extra, dict):
            nested = _safe_float(extra.get(candidate_key))
            if nested is not None:
                return nested
        context = trade.get("context")
        if isinstance(context, dict):
            nested = _safe_float(context.get(candidate_key))
            if nested is not None:
                return nested
        return None

    volume_keys = (
        "size_usdt",
        "notional",
        "notional_usdt",
        "notionalUsd",
        "positionNotional",
    )
    for key in volume_keys:
        volume_val = _lookup(key)
        if volume_val is not None and volume_val > 0:
            return float(abs(volume_val))

    qty_keys = ("qty", "size", "filled_qty", "amount")
    qty_val: Optional[float] = None
    for key in qty_keys:
        candidate = _lookup(key)
        if candidate is not None and abs(candidate) > 0:
            qty_val = abs(candidate)
            break

    price_keys = (
        "notional_price",
        "entry",
        "entry_price",
        "entryPrice",
        "price",
        "avg_price",
        "avgPrice",
        "mark",
        "mark_price",
        "exit",
        "exit_price",
        "exitPrice",
    )
    price_val: Optional[float] = None
    for key in price_keys:
        candidate = _lookup(key)
        if candidate is not None and candidate > 0:
            price_val = candidate
            break

    if qty_val and price_val:
        return float(abs(qty_val) * price_val)

    fills = trade.get("fills")
    if isinstance(fills, list):
        fill_volume = 0.0
        for fill in fills:
            if not isinstance(fill, dict):
                continue
            fill_qty = _safe_float(fill.get("qty") or fill.get("size"))
            fill_price = _safe_float(fill.get("price"))
            if fill_qty is None or fill_price is None:
                continue
            if fill_qty == 0 or fill_price <= 0:
                continue
            fill_volume += abs(fill_qty) * fill_price
        if fill_volume > 0:
            return float(fill_volume)

    return 0.0


def _estimate_history_volume(history: Iterable[Dict[str, Any]]) -> float:
    total = 0.0
    for trade in history or []:
        volume = _extract_trade_volume(trade)
        if volume <= 0:
            continue
        total += volume
    return total


def _compute_stats(history: List[Dict[str, Any]]) -> TradeStats:
    filtered_history: List[Dict[str, Any]] = []
    for entry in history or []:
        if not isinstance(entry, dict):
            continue
        if _is_realized_income_trade(entry):
            continue
        filtered_history.append(entry)

    if not filtered_history:
        return TradeStats(
            count=0,
            total_pnl=0.0,
            total_r=0.0,
            win_rate=0.0,
            best_trade=None,
            worst_trade=None,
            ai_hint="",
            wins=0,
            losses=0,
            draws=0,
        )
    total_pnl = sum(_extract_trade_pnl(h) for h in filtered_history)
    total_r = sum(float(h.get("pnl_r", 0.0) or 0.0) for h in filtered_history)
    wins = [h for h in filtered_history if _extract_trade_pnl(h) > 0]
    losses = [h for h in filtered_history if _extract_trade_pnl(h) < 0]
    count = len(filtered_history)
    win_rate = (len(wins) / count) if count else 0.0
    draws = max(count - len(wins) - len(losses), 0)
    best = max(filtered_history, key=_extract_trade_pnl)
    worst = min(filtered_history, key=_extract_trade_pnl)

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
        wins=len(wins),
        losses=len(losses),
        draws=draws,
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


def _extract_decision_confidence(state: Dict[str, Any]) -> Optional[float]:
    stats = state.get("decision_stats") if isinstance(state, dict) else None
    if not isinstance(stats, dict) or not stats:
        return None

    last_updated = stats.get("last_updated")
    if not last_updated:
        return None

    try:
        taken = int(stats.get("taken", 0) or 0)
    except (TypeError, ValueError):
        taken = 0
    try:
        rejected_total = int(stats.get("rejected_total", 0) or 0)
    except (TypeError, ValueError):
        rejected_total = 0

    if taken < 0:
        taken = 0
    if rejected_total < 0:
        rejected_total = 0

    decision_total = taken + rejected_total
    if decision_total <= 0:
        return None

    if taken <= 0:
        return None

    env_cfg = CONFIG.get("env") if isinstance(CONFIG, dict) else None
    scale_value = None
    if isinstance(env_cfg, dict):
        scale_value = _safe_float(env_cfg.get("ASTER_AI_CONF_SCALE"))
    if scale_value is None:
        scale_value = _safe_float(ENV_DEFAULTS.get("ASTER_AI_CONF_SCALE"))
    conf_scale = float(scale_value or 25.0)
    if conf_scale <= 0:
        conf_scale = 25.0

    progress = 1.0 - math.exp(-decision_total / conf_scale)
    if not math.isfinite(progress):
        return None

    acceptance_ratio = taken / decision_total if decision_total else 0.0
    if not math.isfinite(acceptance_ratio):
        acceptance_ratio = 0.0
    acceptance_ratio = max(0.0, min(1.0, acceptance_ratio))

    confidence = progress * acceptance_ratio
    return max(0.0, min(1.0, confidence))


def _extract_alpha_confidence(state: Dict[str, Any]) -> Optional[float]:
    decision_confidence = _extract_decision_confidence(state)
    if decision_confidence is not None:
        return decision_confidence

    policy = state.get("policy")
    if not isinstance(policy, dict):
        return None

    alpha_state = policy.get("alpha")
    if not isinstance(alpha_state, dict):
        return None

    train_count = _safe_float(alpha_state.get("train_count"))
    conf_scale = _safe_float(alpha_state.get("conf_scale"))
    min_conf = _safe_float(alpha_state.get("min_conf"))

    if train_count is None or train_count < 0:
        return None

    if conf_scale is None or conf_scale <= 0:
        conf_scale = 40.0

    if min_conf is None:
        env_cfg = CONFIG.get("env") if isinstance(CONFIG, dict) else None
        fallback = None
        if isinstance(env_cfg, dict):
            fallback = _safe_float(env_cfg.get("ASTER_ALPHA_MIN_CONF"))
        if fallback is None:
            fallback = _safe_float(ENV_DEFAULTS.get("ASTER_ALPHA_MIN_CONF"))
        min_conf = float(fallback or 0.0)

    baseline = 1.0 - math.exp(-train_count / conf_scale)
    if not math.isfinite(baseline):
        return None

    confidence = max(float(min_conf), baseline)
    return max(0.0, min(1.0, confidence))


def _cumulative_summary(
    state: Dict[str, Any],
    *,
    stats: Optional[TradeStats] = None,
    ai_budget: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    metrics = state.get("cumulative_metrics") or {}
    summary = {
        "total_trades": int(metrics.get("total_trades", 0) or 0),
        "total_pnl": float(metrics.get("total_pnl", 0.0) or 0.0),
        "wins": int(metrics.get("wins", 0) or 0),
        "losses": int(metrics.get("losses", 0) or 0),
        "draws": int(metrics.get("draws", 0) or 0),
    }

    total_volume = metrics.get("total_volume")
    try:
        summary["total_volume"] = float(total_volume or 0.0)
    except (TypeError, ValueError):
        summary["total_volume"] = 0.0

    if summary["total_volume"] <= 0:
        history_volume = _estimate_history_volume(state.get("trade_history", []))
        if history_volume > 0:
            summary["total_volume"] = max(summary["total_volume"], history_volume)

    realized_total: Optional[float] = None
    if stats is not None:
        realized_total = float(stats.total_pnl or 0.0)
        summary["total_trades"] = max(summary["total_trades"], int(stats.count or 0))
        summary["wins"] = max(summary["wins"], int(getattr(stats, "wins", 0) or 0))
        summary["losses"] = max(summary["losses"], int(getattr(stats, "losses", 0) or 0))
        summary["draws"] = max(summary["draws"], int(getattr(stats, "draws", 0) or 0))

    if realized_total is None:
        candidate = metrics.get("realized_pnl")
        candidate_val = _safe_float(candidate)
        if candidate_val is not None:
            realized_total = candidate_val

    if realized_total is None:
        realized_total = summary["total_pnl"]

    budget_source = ai_budget if ai_budget is not None else state.get("ai_budget", {})
    spent_val = _safe_float((budget_source or {}).get("spent"))
    spent = float(spent_val or 0.0)

    net_total = float(realized_total or 0.0) - spent
    summary["total_pnl"] = net_total
    summary["realized_pnl"] = float(realized_total or 0.0)
    summary["ai_budget_spent"] = spent

    confidence = _extract_alpha_confidence(state)
    if confidence is not None:
        summary["alpha_confidence"] = confidence

    updated_at = metrics.get("updated_at")
    if updated_at is not None:
        summary["updated_at"] = updated_at
    return summary


def _build_hero_metrics(
    cumulative: Dict[str, Any],
    stats: TradeStats,
    *,
    history_count: int = 0,
) -> Dict[str, Any]:
    summary = dict(cumulative or {})

    def _coerce_int(value: Any) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    wins = _coerce_int(summary.get("wins"))
    losses = _coerce_int(summary.get("losses"))
    draws = _coerce_int(summary.get("draws"))
    denominator = wins + losses + draws
    if stats.count:
        win_rate = float(stats.win_rate or 0.0)
    elif denominator > 0:
        win_rate = max(0.0, min(1.0, wins / denominator))
    else:
        win_rate = 0.0

    total_candidates = [
        _coerce_int(summary.get("total_trades")),
        _coerce_int(history_count),
        _coerce_int(stats.count),
    ]
    total_trades = max(total_candidates)

    realized = summary.get("realized_pnl")
    if realized is None:
        realized = float(stats.total_pnl or 0.0)

    hero_payload = {
        "total_trades": total_trades,
        "total_pnl": float(summary.get("total_pnl", 0.0) or 0.0),
        "realized_pnl": float(realized or 0.0),
        "ai_budget_spent": float(summary.get("ai_budget_spent", 0.0) or 0.0),
        "win_rate": win_rate,
        "wins": wins,
        "losses": losses,
        "draws": draws,
    }
    return hero_payload


class AIChatEngine:
    MODEL_PRICING: Dict[str, Dict[str, float]] = {
        "gpt-4o": {"input": 0.000005, "output": 0.000015},
        "gpt-4o-mini": {"input": 0.0000006, "output": 0.0000024},
        "o4-mini": {"input": 0.0000012, "output": 0.0000036},
        "gpt-4.1-mini": {"input": 0.0000006, "output": 0.0000024},
        "gpt-4.1": {"input": 0.000003, "output": 0.000009},
        "gpt-4-turbo": {"input": 0.000006, "output": 0.000018},
        "gpt-3.5-turbo": {"input": 0.0000005, "output": 0.0000015},
        "gpt-5": {"input": 0.000004, "output": 0.000012},
        "default": {"input": 0.000001, "output": 0.000003},
    }

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._temperature_supported = True
        self._market_universe_cache: Dict[str, Any] = {"symbols": [], "ts": 0.0}
        self._symbol_filters_cache: Dict[str, Dict[str, Any]] = {}
        self._symbol_filters_cache_ts: Dict[str, float] = {}

        # Avoid leaking book ticker calls for the same symbol in quick succession.
        self._price_cache: Dict[str, Tuple[float, float]] = {}
        self._bracket_guard: Optional[BracketGuard] = None
        self._bracket_guard_unavailable = False

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

    def _quote_asset(self) -> str:
        env = self._env()
        quote = (env.get("ASTER_QUOTE") or ENV_DEFAULTS.get("ASTER_QUOTE", "")).strip()
        return quote.upper()

    def _detect_symbols_in_text(self, text: str) -> List[str]:
        if not text:
            return []

        universe_list = self._market_universe_symbols()
        if not universe_list:
            return []
        universe: Set[str] = set(universe_list)

        symbol_positions: Dict[str, int] = {}

        def register(symbol: str, position: int) -> None:
            if symbol in universe and symbol not in symbol_positions:
                symbol_positions[symbol] = position

        uppercase_text = text.upper()
        try:
            direct_pattern = re.compile(r"\b([A-Z0-9:_-]{3,})\b")
        except re.error:
            direct_pattern = None
        if direct_pattern:
            for match in direct_pattern.finditer(uppercase_text):
                register(match.group(1), match.start())

        try:
            slash_pattern = re.compile(r"\b([A-Za-z0-9]{2,})/([A-Za-z0-9]{2,})\b")
        except re.error:
            slash_pattern = None
        if slash_pattern:
            for match in slash_pattern.finditer(text):
                combined = f"{match.group(1)}{match.group(2)}".upper()
                register(combined, match.start())

        quote = self._quote_asset()
        if quote:
            quote_len = len(quote)
            base_map: Dict[str, str] = {}
            for symbol in universe_list:
                if quote_len and symbol.endswith(quote):
                    base = symbol[:-quote_len]
                    if base:
                        base_map.setdefault(base, symbol)
                        for alias in SYMBOL_SYNONYMS.get(base, ()): 
                            alias_token = (alias or "").strip().upper()
                            if alias_token:
                                base_map.setdefault(alias_token, symbol)
            try:
                word_pattern = re.compile(r"\b([A-Za-z]{3,})\b")
            except re.error:
                word_pattern = None
            if word_pattern:
                for match in word_pattern.finditer(text):
                    base = match.group(1).upper()
                    if base in {"LONG", "SHORT", "BUY", "SELL"}:
                        continue
                    mapped = base_map.get(base)
                    if mapped:
                        register(mapped, match.start())

        ordered = sorted(symbol_positions.items(), key=lambda item: item[1])
        return [symbol for symbol, _ in ordered]

    def _build_analysis_prompt(
        self,
        *,
        universe_prompt: str,
        focus_symbols: Sequence[str] = (),
        user_question: Optional[str] = None,
    ) -> str:
        normalized_focus: List[str] = []
        seen: Set[str] = set()
        for raw in focus_symbols or ():
            symbol = (raw or "").strip().upper()
            if symbol and symbol not in seen:
                normalized_focus.append(symbol)
                seen.add(symbol)

        intro_parts: List[str] = ["You are the strategy copilot's market analyst."]
        if normalized_focus:
            if len(normalized_focus) == 1:
                intro_parts.append(
                    f"Focus exclusively on {normalized_focus[0]}. Provide a long and short evaluation for this market, "
                    "highlighting liquidity, funding, volatility regime, and any telemetry gaps."
                )
            else:
                formatted = ", ".join(normalized_focus)
                intro_parts.append(
                    f"Focus on these symbols: {formatted}. Cover each market separately, call out correlations, "
                    "liquidity constraints, and telemetry gaps affecting confidence."
                )
        else:
            intro_parts.append("Using the latest telemetry, produce a concise report.")
        if user_question:
            cleaned = user_question.strip()
            if cleaned:
                intro_parts.append(
                    f'The operator asked: "{cleaned}". Address this intent explicitly while following the structure below.'
                )
        intro = " ".join(part.strip() for part in intro_parts if part).strip()

        summary_line: str
        if normalized_focus:
            formatted = ", ".join(normalized_focus)
            summary_line = (
                "Market Snapshot — ≤150 words covering structure, volatility, liquidity, funding, sentiment, and catalysts for "
                f"{formatted}. Reference quantitative telemetry whenever possible and call out explicitly where data is stale "
                "or missing.\n"
            )
        else:
            summary_line = (
                "Market Summary — ≤150 words covering tone, volatility, liquidity, and risk. Reference concrete metrics from the "
                "telemetry and name at least four tickers drawn from the provided Aster universe or most-traded list; call out "
                "explicitly where data is stale or missing.\n"
            )

        prompt_parts: List[str] = []
        if intro:
            prompt_parts.append(intro.strip() + " ")
        universe_section = (universe_prompt or "").strip()
        if universe_section:
            prompt_parts.append(universe_section + " ")
        prompt_parts.append("Follow this structure exactly:\n")
        prompt_parts.append(summary_line)
        prompt_parts.append(
            "LONG Idea — Provide symbol, timeframe, thesis rooted in available numbers, entry zone with prices, invalidation, "
            "target, catalysts, and any data caveats.\n"
        )
        prompt_parts.append(
            "SHORT Idea — Same level of detail as the long idea.\n"
        )
        prompt_parts.append(
            "Trade Inputs — Bullet list that enumerates every field required for execution: symbol, direction, entry_plan "
            "(market or limit with price), entry_price, stop_loss, take_profit, position_size in USDT, timeframe, and "
            "confidence between 0 and 1. Use numeric values; if a figure cannot be justified from telemetry, write 'n/a' "
            "and explain why.\n"
        )
        prompt_parts.append(
            "After the narrative, emit one ACTION line per idea using: ACTION: {\"type\":\"propose_trade\",...}. The JSON "
            "must include type=\"propose_trade\", symbol, direction (LONG/SHORT), entry_kind (market/limit), entry_price (or null "
            "for market), stop_loss, take_profit, notional (USDT), timeframe, confidence (0-1), and a concise note tying back to "
            "the analysis. Keep each ACTION line on a single line with valid JSON. Finish by reminding the operator that they can "
            "click \"Take trade proposals\" to queue execution."
        )
        return "".join(prompt_parts)

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

    def _pricing_for_model(self, model: str) -> Dict[str, float]:
        return self.MODEL_PRICING.get(model, self.MODEL_PRICING["default"])

    def _estimate_request_cost(
        self, model: str, usage: Optional[Dict[str, Any]]
    ) -> Optional[float]:
        if not usage:
            return None
        pricing = self._pricing_for_model(model)

        prompt_tokens = usage.get("prompt_tokens")
        completion_tokens = usage.get("completion_tokens")
        if prompt_tokens is None:
            prompt_tokens = usage.get("input_tokens")
        if completion_tokens is None:
            completion_tokens = usage.get("output_tokens")

        try:
            prompt_val = float(prompt_tokens or 0.0)
            completion_val = float(completion_tokens or 0.0)
        except (TypeError, ValueError):
            return None

        return (
            prompt_val * pricing.get("input", 0.0)
            + completion_val * pricing.get("output", 0.0)
        )

    def _record_dashboard_ai_usage(
        self,
        kind: str,
        model: str,
        usage: Optional[Dict[str, Any]],
        *,
        key_source: Optional[str] = None,
        note: Optional[str] = None,
    ) -> None:
        cost = self._estimate_request_cost(model, usage)
        if cost is None:
            cost = 0.0025
        meta: Dict[str, Any] = {
            "kind": kind,
            "model": model,
            "source": "dashboard",
        }
        if key_source:
            meta["key_source"] = key_source
        if usage:
            meta["usage"] = usage
        if note:
            meta["note"] = note
        _record_ai_budget_usage(cost, meta)

    def _extract_trade_proposals(self, text: str) -> List[Dict[str, Any]]:
        if not text:
            return []
        proposals: List[Dict[str, Any]] = []

        def _extract_object(buffer: str, start_index: int) -> Tuple[Optional[str], int]:
            brace_index = buffer.find("{", start_index)
            if brace_index == -1:
                return None, start_index
            depth = 0
            string_char: Optional[str] = None
            escape = False
            idx = brace_index
            while idx < len(buffer):
                ch = buffer[idx]
                if string_char:
                    if escape:
                        escape = False
                    elif ch == "\\":
                        escape = True
                    elif ch == string_char:
                        string_char = None
                else:
                    if ch in {'"', "'"}:
                        string_char = ch
                    elif ch == "{":
                        depth += 1
                    elif ch == "}":
                        if depth > 0:
                            depth -= 1
                            if depth == 0:
                                return buffer[brace_index : idx + 1], idx + 1
                idx += 1
            return None, start_index

        def _parse_payload(raw_payload: str) -> Optional[Dict[str, Any]]:
            cleaned = raw_payload.strip()
            cleaned = cleaned.rstrip(",;`").strip()
            try:
                payload = json.loads(cleaned)
            except json.JSONDecodeError:
                normalized = re.sub(r"\bnull\b", "None", cleaned, flags=re.IGNORECASE)
                normalized = re.sub(r"\btrue\b", "True", normalized, flags=re.IGNORECASE)
                normalized = re.sub(r"\bfalse\b", "False", normalized, flags=re.IGNORECASE)
                try:
                    payload = ast.literal_eval(normalized)
                except (ValueError, SyntaxError):
                    return None
            if not isinstance(payload, dict):
                return None
            return payload

        search_pos = 0
        action_pattern = re.compile(r"action\s*:", re.IGNORECASE)
        while True:
            match = action_pattern.search(text, search_pos)
            if not match:
                break
            object_text, end_index = _extract_object(text, match.end())
            if object_text:
                payload = _parse_payload(object_text)
                if payload:
                    action_type = str(payload.get("type") or "").strip().lower()
                    if action_type in {"propose_trade", "trade_proposal", "trade_plan"}:
                        proposals.append(payload)
                search_pos = max(end_index, match.end())
            else:
                search_pos = match.end()

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
            if value is None:
                continue
            if value > 0:
                return value
            if value == 0:
                return 0.0
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

    def _parse_confidence(self, *values: Any) -> Tuple[Optional[float], Optional[str]]:
        numeric: Optional[float] = None
        label: Optional[str] = None

        keyword_levels: List[Tuple[Tuple[str, ...], float]] = [
            (("very high", "strong", "excellent", "very bullish", "high conviction"), 0.85),
            (("high", "bullish", "positive", "favorable"), 0.7),
            (("medium", "moderate", "balanced", "neutral"), 0.5),
            (("very low", "poor", "negative", "very bearish"), 0.15),
            (("low", "cautious", "bearish", "weak"), 0.3),
        ]

        for raw in values:
            if raw is None:
                continue
            if isinstance(raw, (int, float)):
                numeric = float(raw)
                if label is None:
                    label = format(float(raw), ".2f")
                break
            if not isinstance(raw, str):
                continue
            cleaned = raw.strip()
            if not cleaned:
                continue
            if label is None:
                label = cleaned
            numbers = self._extract_numbers(cleaned)
            if numbers:
                numeric = numbers[0]
                break
            lowered = cleaned.lower()
            if lowered in {"n/a", "na", "none", "unknown"}:
                label = "N/A"
                continue
            for keywords, level in keyword_levels:
                if any(keyword in lowered for keyword in keywords):
                    numeric = level
                    break
            if numeric is not None:
                break

        if numeric is not None:
            if numeric < 0:
                numeric = 0.0
            elif numeric > 1:
                if numeric <= 100:
                    numeric = numeric / 100.0
                else:
                    numeric = 1.0
            numeric = max(0.0, min(numeric, 1.0))
            if label is None:
                label = f"{numeric:.0%}"

        if isinstance(label, str):
            label = label.strip()
            if not label:
                label = None

        return numeric, label

    def _extract_structured_trade_proposals(self, text: str) -> List[Dict[str, Any]]:
        try:
            thesis_matches = list(
                re.finditer(r"(?:\*\*)?Thesis(?:\*\*)?:\s*", text, flags=re.IGNORECASE)
            )
        except re.error:
            return []
        if not thesis_matches:
            return []

        default_notional = self._default_proposal_notional()
        if default_notional is None:
            return []

        trade_input_hints: Dict[str, str] = {}
        try:
            for sym, side in re.findall(
                r"(?:\*\*)?([A-Z0-9]{3,})\s+(Long|Short)(?:\*\*)?",
                text,
                flags=re.IGNORECASE,
            ):
                trade_input_hints[sym.upper()] = side.upper()
        except re.error:
            trade_input_hints = {}

        try:
            idea_headers = list(
                re.finditer(
                    r"(?:\*\*)?(Long|Short)\s+Idea(?:\*\*)?",
                    text,
                    flags=re.IGNORECASE,
                )
            )
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
            thesis_line_match = re.search(
                r"(?:\*\*)?Thesis(?:\*\*)?:\s*(.+)", block, re.IGNORECASE
            )
            if not thesis_line_match:
                continue
            thesis_line = thesis_line_match.group(1).strip()
            if not thesis_line:
                continue

            symbol: Optional[str] = None
            symbol_line_match = re.search(
                r"(?:\*\*)?Symbol(?:\*\*)?:\s*([A-Z0-9:_\-/]+)",
                block,
                re.IGNORECASE,
            )
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

            invalidation_match = re.search(
                r"(?:\*\*)?Invalidation(?:\*\*)?:\s*([^\n]+)",
                block,
                re.IGNORECASE,
            )
            invalidation_numbers = (
                self._extract_numbers(invalidation_match.group(1)) if invalidation_match else []
            )
            stop_loss = invalidation_numbers[0] if invalidation_numbers else None

            target_match = re.search(
                r"(?:\*\*)?Target(?:\*\*)?:\s*([^\n]+)", block, re.IGNORECASE
            )
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
            catalysts_match = re.search(
                r"(?:\*\*)?Catalysts?(?:\*\*)?:\s*([^\n]+)",
                block,
                re.IGNORECASE,
            )
            if catalysts_match:
                catalysts = catalysts_match.group(1).strip()
                if catalysts:
                    note_parts.append(f"Catalysts: {catalysts}")
            caveats_match = re.search(
                r"(?:\*\*)?(?:Data\s+)?Caveats?(?:\*\*)?:\s*([^\n]+)",
                block,
                re.IGNORECASE,
            )
            if caveats_match:
                caveats = caveats_match.group(1).strip()
                if caveats:
                    note_parts.append(f"Data Caveats: {caveats}")
            note = " | ".join(note_parts)
            if note and len(note) > 320:
                note = note[:317] + "…"

            timeframe: Optional[str] = None
            timeframe_match = re.search(
                r"(?:\*\*)?Time\s*[-–—]?\s*frame(?:\*\*)?\s*(?::|[-–—])\s*([^\n]+)",
                block,
                re.IGNORECASE,
            )
            if timeframe_match:
                raw_timeframe = timeframe_match.group(1)
                if isinstance(raw_timeframe, str):
                    cleaned = raw_timeframe.strip()
                    if cleaned:
                        timeframe = cleaned
            else:
                horizon_match = re.search(
                    r"(?:\*\*)?(Time|Holding)\s*Horizon(?:\*\*)?:\s*([^\n]+)",
                    block,
                    re.IGNORECASE,
                )
                if horizon_match:
                    raw_timeframe = horizon_match.group(2)
                    if isinstance(raw_timeframe, str):
                        cleaned = raw_timeframe.strip()
                        if cleaned:
                            timeframe = cleaned

            confidence_line_match = re.search(
                r"(?:\*\*)?Confidence(?:\s+Score)?(?:\*\*)?\s*(?::|[-–—])\s*([^\n]+)",
                block,
                re.IGNORECASE,
            )
            confidence: Optional[float] = None
            confidence_label: Optional[str] = None
            if confidence_line_match:
                raw_confidence = confidence_line_match.group(1)
                confidence, confidence_label = self._parse_confidence(raw_confidence)

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
                "confidence": confidence,
                "confidence_label": confidence_label,
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
            default_notional = self._default_proposal_notional()
            if default_notional is not None:
                notional = default_notional
            else:
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

        confidence, confidence_label = self._parse_confidence(
            raw.get("confidence"),
            raw.get("conviction"),
            raw.get("probability"),
            raw.get("confidence_label"),
            raw.get("confidence_text"),
        )

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
            "confidence_label": confidence_label,
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
        else:
            label = proposal.get("confidence_label")
            if isinstance(label, str) and label.strip():
                parts.append(f"Conf {label.strip()}")

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

    @staticmethod
    def _format_decimal(value: float) -> str:
        text = f"{float(value):.12f}".rstrip("0").rstrip(".")
        return text or "0"

    @staticmethod
    def _round_to_step(value: float, step: float) -> float:
        if step <= 0:
            return float(value)
        steps = math.floor(value / step + 1e-12)
        return float(steps * step)

    def _maybe_rescale_price_levels(
        self,
        symbol: str,
        side: str,
        entry_price: Optional[float],
        stop_loss: Optional[float],
        take_profit: Optional[float],
        price_hint: Optional[float] = None,
    ) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
        """Detect and correct values parsed with locale thousand separators.

        Some tenants render prices like ``3.930`` to represent ``3,930``.
        When these values are parsed naively they become ~3.93 which is far
        away from the real market price.  Compare the parsed value with the
        live book ticker and, if a simple power-of-ten multiplier aligns the
        numbers, rescale the entire bracket accordingly.
        """

        hint = price_hint

        def ensure_hint() -> Optional[float]:
            nonlocal hint
            if hint is None:
                hint = self._fetch_price(symbol, side)
            return hint

        def best_factor(raw_value: Optional[float]) -> float:
            reference = ensure_hint()
            if (
                reference is None
                or raw_value is None
                or raw_value <= 0
                or reference <= 0
            ):
                return 1.0
            base_diff = abs(raw_value - reference) / max(abs(reference), 1e-9)
            best = 1.0
            best_diff = base_diff
            for factor in (10.0, 100.0, 1000.0):
                scaled = raw_value * factor
                diff = abs(scaled - reference) / max(abs(reference), 1e-9)
                if diff + 1e-6 < best_diff:
                    best = factor
                    best_diff = diff
            if best != 1.0 and best_diff <= 0.05 and best_diff <= base_diff * 0.5:
                return best
            return 1.0

        factor = 1.0
        if entry_price is not None:
            factor = best_factor(entry_price)
        if factor == 1.0:
            for candidate in (stop_loss, take_profit):
                factor = best_factor(candidate)
                if factor != 1.0:
                    break

        if factor != 1.0:
            entry_price = entry_price * factor if entry_price is not None else None
            stop_loss = stop_loss * factor if stop_loss is not None else None
            take_profit = take_profit * factor if take_profit is not None else None

        return entry_price, stop_loss, take_profit, hint

    def _symbol_filters(self, symbol: str) -> Optional[Dict[str, float]]:
        normalized = (symbol or "").upper().strip()
        if not normalized:
            return None

        cache_entry = self._symbol_filters_cache.get(normalized)
        cached_ts = self._symbol_filters_cache_ts.get(normalized, 0.0)
        if cache_entry and time.time() - cached_ts < 1800:
            return cache_entry

        env = self._env()
        base = (env.get("ASTER_EXCHANGE_BASE") or ENV_DEFAULTS.get("ASTER_EXCHANGE_BASE") or "").rstrip("/")
        if not base:
            return None

        try:
            resp = requests.get(
                f"{base}/fapi/v1/exchangeInfo",
                params={"symbol": normalized},
                timeout=8,
            )
            resp.raise_for_status()
            payload = resp.json()
        except Exception as exc:
            logger.debug("Failed to fetch symbol filters for %s: %s", normalized, exc)
            return None

        data: Optional[Dict[str, Any]] = None
        if isinstance(payload, dict):
            symbols_payload = payload.get("symbols")
            if isinstance(symbols_payload, list) and symbols_payload:
                data = next((entry for entry in symbols_payload if entry.get("symbol") == normalized), None)
            elif payload.get("symbol") == normalized:
                data = payload
        if not isinstance(data, dict):
            return None

        filters = data.get("filters", [])
        tick = None
        step = None
        min_qty = None
        min_notional = None
        for filt in filters:
            if not isinstance(filt, dict):
                continue
            filter_type = str(filt.get("filterType") or "").upper()
            if filter_type == "PRICE_FILTER":
                tick = self._safe_float(filt.get("tickSize"))
            elif filter_type == "LOT_SIZE":
                step = self._safe_float(filt.get("stepSize"))
                min_qty = self._safe_float(filt.get("minQty"))
            elif filter_type in {"MIN_NOTIONAL", "MIN_NOTIONAL_FILTER"}:
                min_notional = self._safe_float(filt.get("notional")) or self._safe_float(filt.get("minNotional"))

        normalized_filters = {
            "tickSize": tick or 0.0,
            "stepSize": step or 0.0,
            "minQty": min_qty or 0.0,
            "minNotional": min_notional or 0.0,
        }
        self._symbol_filters_cache[normalized] = normalized_filters
        self._symbol_filters_cache_ts[normalized] = time.time()
        return normalized_filters

    def _fetch_price(self, symbol: str, side: str) -> Optional[float]:
        normalized_symbol = (symbol or "").upper().strip()
        if not normalized_symbol:
            return None

        cache_key = f"{normalized_symbol}:{side}"
        cached = self._price_cache.get(cache_key)
        now = time.time()
        if cached and now - cached[1] < 5.0:
            return cached[0]

        env = self._env()
        base = (env.get("ASTER_EXCHANGE_BASE") or ENV_DEFAULTS.get("ASTER_EXCHANGE_BASE") or "").rstrip("/")
        if not base:
            return None

        try:
            resp = requests.get(
                f"{base}/fapi/v1/ticker/bookTicker",
                params={"symbol": normalized_symbol},
                timeout=6,
            )
            resp.raise_for_status()
            payload = resp.json()
        except Exception as exc:
            logger.debug("Failed to fetch book ticker for %s: %s", normalized_symbol, exc)
            return None

        price: Optional[float] = None
        if isinstance(payload, dict):
            if side == "BUY":
                price = self._safe_float(payload.get("askPrice")) or self._safe_float(payload.get("price"))
            else:
                price = self._safe_float(payload.get("bidPrice")) or self._safe_float(payload.get("price"))
        if price is None:
            price = self._safe_float(payload) if isinstance(payload, (int, float)) else None

        if price is not None:
            self._price_cache[cache_key] = (price, now)
        return price

    def _signed_request(self, method: str, path: str, params: Dict[str, Any]) -> Any:
        env = self._env()
        base = (env.get("ASTER_EXCHANGE_BASE") or ENV_DEFAULTS.get("ASTER_EXCHANGE_BASE") or "").rstrip("/")
        api_key = (env.get("ASTER_API_KEY") or ENV_DEFAULTS.get("ASTER_API_KEY") or "").strip()
        api_secret = (env.get("ASTER_API_SECRET") or ENV_DEFAULTS.get("ASTER_API_SECRET") or "").strip()
        if not base or not api_key or not api_secret:
            raise RuntimeError("Aster API credentials are required to place trades.")

        try:
            recv_window = int(float(env.get("ASTER_RECV_WINDOW", 10000)))
        except (TypeError, ValueError):
            recv_window = 10000

        payload = dict(params or {})
        payload["timestamp"] = int(time.time() * 1000)
        payload["recvWindow"] = recv_window
        ordered = [(k, payload[k]) for k in sorted(payload)]
        qs = urlencode(ordered, doseq=True)
        signature = hmac.new(api_secret.encode(), qs.encode(), hashlib.sha256).hexdigest()
        url = f"{base}{path}?{qs}&signature={signature}"
        headers = {"X-MBX-APIKEY": api_key, "Content-Type": "application/x-www-form-urlencoded"}

        try:
            response = requests.request(method.upper(), url, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.HTTPError as exc:
            detail = ""
            if exc.response is not None:
                try:
                    payload = exc.response.json()
                    detail = json.dumps(payload)
                except ValueError:
                    detail = exc.response.text or ""
            message = detail or str(exc)
            logger.debug("Aster API request failed: %s", message)
            raise RuntimeError(detail or "Aster API rejected the trade request") from exc
        except requests.RequestException as exc:
            logger.debug("Aster API request error: %s", exc)
            raise RuntimeError("Unable to reach the Aster API") from exc

        try:
            return response.json()
        except ValueError:
            return {}

    def _get_bracket_guard(self) -> Optional[BracketGuard]:
        if self._bracket_guard_unavailable:
            return None
        if self._bracket_guard is not None:
            return self._bracket_guard

        env = self._env()
        base = (env.get("ASTER_EXCHANGE_BASE") or ENV_DEFAULTS.get("ASTER_EXCHANGE_BASE") or "").rstrip("/")
        api_key = (env.get("ASTER_API_KEY") or ENV_DEFAULTS.get("ASTER_API_KEY") or "").strip()
        api_secret = (env.get("ASTER_API_SECRET") or ENV_DEFAULTS.get("ASTER_API_SECRET") or "").strip()
        if not base or not api_key or not api_secret:
            self._bracket_guard_unavailable = True
            return None

        try:
            recv_window = int(float(env.get("ASTER_RECV_WINDOW", 10000)))
        except (TypeError, ValueError):
            recv_window = 10000

        working_type = (
            env.get("ASTER_WORKING_TYPE")
            or ENV_DEFAULTS.get("ASTER_WORKING_TYPE")
            or "MARK_PRICE"
        ).upper()

        try:
            guard = BracketGuard(
                working_type=working_type,
                recv_window=recv_window,
                base_url=base,
                api_key=api_key,
                api_secret=api_secret,
            )
        except Exception as exc:
            logger.debug("Failed to initialize bracket guard: %s", exc)
            return None

        self._bracket_guard = guard
        return guard

    def _place_trade_proposal(self, proposal_id: str, proposal: Dict[str, Any]) -> Dict[str, Any]:
        env = self._env()
        if _is_truthy(env.get("ASTER_PAPER")):
            raise RuntimeError("Disable paper trading to place live orders via the Aster API.")

        symbol = (proposal.get("symbol") or "").upper().strip()
        direction = (proposal.get("direction") or "").upper().strip()
        if not symbol or direction not in {"LONG", "SHORT"}:
            raise RuntimeError("Trade proposal is missing symbol or direction")

        side = "BUY" if direction == "LONG" else "SELL"
        entry_kind = str(proposal.get("entry_kind") or "market").lower()
        entry_price = self._safe_float(proposal.get("entry_price"))
        stop_loss = self._safe_float(proposal.get("stop_loss"))
        take_profit = self._safe_float(proposal.get("take_profit"))
        notional = self._safe_float(proposal.get("notional"))

        if notional is None or notional <= 0:
            raise RuntimeError("Trade proposal is missing a notional amount")

        price_hint: Optional[float] = None
        if entry_kind == "limit":
            price_hint = self._fetch_price(symbol, side)

        entry_price, stop_loss, take_profit, price_hint = self._maybe_rescale_price_levels(
            symbol,
            side,
            entry_price,
            stop_loss,
            take_profit,
            price_hint,
        )

        if entry_kind == "limit":
            if entry_price is None or entry_price <= 0:
                raise RuntimeError("Limit entries require a valid entry price")
            live_price = price_hint
            if live_price is None or live_price <= 0:
                live_price = self._fetch_price(symbol, side)
            if live_price is not None and live_price > 0:
                reference_price = live_price
                entry_price = live_price
                entry_kind = "market"
            else:
                reference_price = entry_price
        else:
            reference_price = entry_price or price_hint or self._fetch_price(symbol, side)
            if reference_price is None or reference_price <= 0:
                raise RuntimeError("Unable to determine a price for market execution")
            entry_kind = "market"

        filters = self._symbol_filters(symbol) or {}
        tick_size = float(filters.get("tickSize") or 0.0)
        step_size = float(filters.get("stepSize") or 0.0)
        min_qty = float(filters.get("minQty") or 0.0)
        min_notional = float(filters.get("minNotional") or 0.0)

        qty = notional / max(reference_price, 1e-12)
        qty = max(0.0, qty)
        if step_size > 0:
            qty = self._round_to_step(qty, step_size)
        if qty <= 0:
            raise RuntimeError("Calculated order quantity is too small")
        if min_qty > 0 and qty < min_qty:
            raise RuntimeError("Calculated order quantity falls below the minimum lot size")
        if min_notional > 0 and qty * reference_price < min_notional:
            raise RuntimeError("Order notional is below the exchange minimum")

        order_params: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET" if entry_kind == "market" else "LIMIT",
            "quantity": self._format_decimal(qty),
        }

        if entry_kind == "limit":
            limit_price = reference_price
            if tick_size > 0:
                limit_price = self._round_to_step(limit_price, tick_size)
            order_params["price"] = self._format_decimal(limit_price)
            order_params["timeInForce"] = "GTC"
            reference_price = limit_price

        working_type = (env.get("ASTER_WORKING_TYPE") or ENV_DEFAULTS.get("ASTER_WORKING_TYPE") or "MARK_PRICE").upper()

        def _validate_level(level: Optional[float], kind: str) -> Optional[float]:
            if level is None or level <= 0:
                return None
            if tick_size > 0:
                level = self._round_to_step(level, tick_size)
            if kind == "stop" and direction == "LONG" and level >= reference_price:
                raise RuntimeError("Stop-loss must be below the entry price for long positions")
            if kind == "stop" and direction == "SHORT" and level <= reference_price:
                raise RuntimeError("Stop-loss must be above the entry price for short positions")
            if kind == "take" and direction == "LONG" and level <= reference_price:
                raise RuntimeError("Take-profit must be above the entry price for long positions")
            if kind == "take" and direction == "SHORT" and level >= reference_price:
                raise RuntimeError("Take-profit must be below the entry price for short positions")
            return level

        stop_level = _validate_level(stop_loss, "stop")
        take_level = _validate_level(take_profit, "take")

        def _build_bracket_payload(kind: str, trigger_price: float) -> str:
            payload = {
                "type": "STOP_MARKET" if kind == "SL" else "TAKE_PROFIT_MARKET",
                "trigger": {"type": working_type, "price": self._format_decimal(trigger_price)},
                "closePosition": True,
            }
            return json.dumps(payload, separators=(",", ":"))

        if stop_level is not None:
            order_params["stopLoss"] = _build_bracket_payload("SL", stop_level)
        if take_level is not None:
            order_params["takeProfit"] = _build_bracket_payload("TP", take_level)

        response = self._signed_request("POST", "/fapi/v1/order", order_params)

        execution_details = {
            "order": response,
            "quantity": qty,
            "entry_price": reference_price,
            "notional": qty * reference_price,
            "proposal_id": proposal_id,
        }
        if stop_level is not None:
            execution_details["stop_loss"] = stop_level
        if take_level is not None:
            execution_details["take_profit"] = take_level

        if stop_level is not None or take_level is not None:
            guard = self._get_bracket_guard()
            if guard is not None:
                try:
                    guard.ensure_after_entry(symbol, side, float(qty), reference_price, stop_level, take_level)
                except TypeError:
                    try:
                        guard.ensure_after_entry(symbol, side, stop_level, take_level)
                    except Exception as exc:
                        logger.debug(
                            "Bracket guard (legacy) ensure failed for %s: %s", symbol, exc
                        )
                except Exception as exc:
                    logger.debug("Bracket guard ensure failed for %s: %s", symbol, exc)
        return execution_details

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
            ("o1", "reasoning"),
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
        elif normalized.startswith("o1"):
            traits["modalities"] = ["text"]
            traits["reasoning"] = {"effort": "medium"}
            traits["legacy_supported"] = False
        elif normalized.startswith("gpt-4.1"):
            # Treat the GPT-4.1 family like GPT-4o for transport selection. While the
            # Responses API is the preferred interface, some tenants only have
            # legacy Chat Completions access wired up; falling back keeps the
            # dashboard behaviour aligned with the GPT-4o path when the modern
            # endpoint rejects the request (e.g. 400 errors).
            traits["legacy_supported"] = True

        return traits

    def _call_openai_responses(
        self,
        headers: Dict[str, str],
        model: str,
        messages: List[Dict[str, str]],
        temperature: Optional[float],
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        normalized_input: List[Dict[str, Any]] = []
        system_chunks: List[str] = []
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
                            # normalising legacy ``input_text``/``output_text`` segments
                            # to the ``text`` segments expected by the Responses API.
                            normalized_type = str(p_type or "text")
                            if normalized_type in {"input_text", "output_text"}:
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
            if role == "system":
                for part in content_parts:
                    if part.get("type") in {"text", "input_text"}:
                        system_chunks.append(part.get("text", ""))
                # Do not include individual system entries directly; they will be merged
                # into a single system block below to match the Responses API contract.
                continue
            normalized_input.append({"role": role, "content": content_parts})

        if not normalized_input:
            raise ValueError("No valid messages to send to Responses API")

        traits = self._model_traits(model)

        payload: Dict[str, Any] = {
            "model": model,
            "input": normalized_input,
            "max_output_tokens": 400,
        }
        if system_chunks:
            system_text = "\n\n".join(
                chunk.strip() for chunk in system_chunks if str(chunk).strip()
            )
            if system_text:
                payload["input"] = [
                    {
                        "role": "system",
                        "content": [{"type": "text", "text": system_text}],
                    },
                    *payload["input"],
                ]
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
        Dict[str, Any],
    ]:
        state = _read_state()
        history = state.get("trade_history", [])
        stats = _compute_stats(history)
        open_trades = state.get("live_trades", {})
        ai_activity = state.get("ai_activity", [])
        ai_budget = _normalize_ai_budget(state.get("ai_budget", {}))
        decision_stats = _decision_summary(state)
        recent_plans = self._recent_plan_summaries(state.get("ai_recent_plans"))
        technical_snapshot = state.get("technical_snapshot", {})
        if not isinstance(technical_snapshot, dict):
            technical_snapshot = {}
        overlays = self._copilot_context_overlay(state, ai_budget)
        return (
            stats,
            history,
            open_trades,
            ai_activity,
            ai_budget,
            decision_stats,
            recent_plans,
            technical_snapshot,
            overlays,
        )

    def _copilot_context_overlay(
        self,
        state: Dict[str, Any],
        ai_budget: Dict[str, Any],
    ) -> Dict[str, Any]:
        overlay: Dict[str, Any] = {}
        playbook_bucket = state.get("ai_playbook") if isinstance(state, dict) else None
        activity_source = state.get("ai_activity") if isinstance(state, dict) else None
        if isinstance(activity_source, list):
            playbook_activity = _collect_playbook_activity(activity_source)
        else:
            playbook_activity = []
        resolved_playbook = _resolve_playbook_state(playbook_bucket, playbook_activity)
        if not resolved_playbook and isinstance(playbook_bucket, dict):
            resolved_playbook = playbook_bucket.get("active")

        if isinstance(resolved_playbook, dict) and resolved_playbook:
            mode = str(resolved_playbook.get("mode") or "baseline")
            bias = str(resolved_playbook.get("bias") or "neutral")
            size_bias = resolved_playbook.get("size_bias") or {}
            try:
                buy_bias = float((size_bias or {}).get("BUY", 1.0) or 1.0)
            except (TypeError, ValueError):
                buy_bias = 1.0
            try:
                sell_bias = float((size_bias or {}).get("SELL", 1.0) or 1.0)
            except (TypeError, ValueError):
                sell_bias = 1.0
            try:
                sl_bias = float(resolved_playbook.get("sl_bias", 1.0) or 1.0)
            except (TypeError, ValueError):
                sl_bias = 1.0
            try:
                tp_bias = float(resolved_playbook.get("tp_bias", 1.0) or 1.0)
            except (TypeError, ValueError):
                tp_bias = 1.0
            features = resolved_playbook.get("features")
            feature_blurbs: List[str] = []
            if isinstance(features, dict):
                ranked_pairs = [
                    (name, value)
                    for name, value in features.items()
                    if isinstance(value, (int, float))
                ]
            elif isinstance(features, list):
                ranked_pairs = [
                    (str(item.get("name")), item.get("value"))
                    for item in features
                    if isinstance(item, dict)
                ]
            else:
                ranked_pairs = []
            ranked_pairs = [
                (name, float(value))
                for name, value in ranked_pairs
                if name and isinstance(value, (int, float))
            ]
            ranked_pairs.sort(key=lambda pair: abs(pair[1]), reverse=True)
            for name, value in ranked_pairs[:2]:
                feature_blurbs.append(f"{name} {value:+.2f}")
            snippet = (
                f"Active playbook: {mode} ({bias}) · size BUY {buy_bias:.2f}/SELL {sell_bias:.2f} · SL×{sl_bias:.2f} · TP×{tp_bias:.2f}"
            )
            if feature_blurbs:
                snippet += " · " + ", ".join(feature_blurbs)
            overlay["playbook_line"] = snippet
        sentinel_state = state.get("sentinel") if isinstance(state, dict) else None
        if isinstance(sentinel_state, dict) and sentinel_state:
            counts: Dict[str, int] = {}
            peak_risk = 0.0
            peak_symbol: Optional[str] = None
            avg_hype = 0.0
            hype_samples = 0
            for symbol, payload in sentinel_state.items():
                if not isinstance(payload, dict):
                    continue
                label = str(payload.get("label", "")).lower()
                counts[label] = counts.get(label, 0) + 1
                try:
                    event_risk = float(payload.get("event_risk", 0.0) or 0.0)
                except (TypeError, ValueError):
                    event_risk = 0.0
                if event_risk > peak_risk:
                    peak_risk = event_risk
                    peak_symbol = symbol
                try:
                    hype_score = float(payload.get("hype_score", 0.0) or 0.0)
                except (TypeError, ValueError):
                    hype_score = None
                if hype_score is not None:
                    avg_hype += hype_score
                    hype_samples += 1
            pieces: List[str] = []
            if counts.get("red"):
                pieces.append(f"red={counts['red']}")
            if counts.get("yellow"):
                pieces.append(f"yellow={counts['yellow']}")
            if counts.get("green"):
                pieces.append(f"green={counts['green']}")
            if peak_symbol:
                pieces.append(f"peak {peak_symbol} risk={peak_risk:.2f}")
            if hype_samples:
                pieces.append(f"avg hype={avg_hype / max(hype_samples, 1):.2f}")
            if pieces:
                overlay["sentinel_line"] = "Sentinel risk: " + " · ".join(pieces)
        history = ai_budget.get("history") if isinstance(ai_budget, dict) else None
        spent_val = _safe_float(ai_budget.get("spent")) if isinstance(ai_budget, dict) else None
        limit_val = _safe_float(ai_budget.get("limit")) if isinstance(ai_budget, dict) else None
        count_val = _ai_request_count(ai_budget) if isinstance(ai_budget, dict) else None
        if isinstance(history, list) and history:
            costs: List[float] = []
            first_ts: Optional[float] = None
            last_ts: Optional[float] = None
            for item in history[-12:]:
                if not isinstance(item, dict):
                    continue
                try:
                    costs.append(float(item.get("cost", 0.0) or 0.0))
                except (TypeError, ValueError):
                    continue
                try:
                    ts_val = float(item.get("ts", 0.0) or 0.0)
                except (TypeError, ValueError):
                    ts_val = None
                if ts_val is not None:
                    if first_ts is None:
                        first_ts = ts_val
                    last_ts = ts_val
            if costs:
                avg_cost = sum(costs) / len(costs)
                pace: Optional[float] = None
                if first_ts is not None and last_ts is not None and last_ts > first_ts:
                    hours = max((last_ts - first_ts) / 3600.0, 1e-3)
                    pace = len(costs) / hours
                parts = [f"avg cost {avg_cost:.4f} USD"]
                if pace is not None:
                    parts.append(f"~{pace:.1f} req/hr")
                if spent_val is not None and limit_val is not None:
                    parts.insert(0, f"spent {spent_val:.2f}/{limit_val:.2f} USD")
                elif spent_val is not None:
                    parts.insert(0, f"spent {spent_val:.2f} USD")
                if count_val is not None:
                    parts.append(f"count {count_val}")
                overlay["budget_trend_line"] = "AI budget trend: " + " · ".join(parts)
        tuning_overrides = state.get("tuning_overrides")
        if not isinstance(tuning_overrides, dict):
            tuning_state = state.get("param_tuning") if isinstance(state, dict) else None
            if isinstance(tuning_state, dict):
                tuning_overrides = tuning_state.get("overrides")
        if isinstance(tuning_overrides, dict) and tuning_overrides:
            size_bias = tuning_overrides.get("size_bias") or {}
            size_bits: List[str] = []
            if isinstance(size_bias, dict):
                for bucket in ("S", "M", "L"):
                    try:
                        size_bits.append(f"{bucket}:{float(size_bias.get(bucket, 1.0)):.2f}")
                    except (TypeError, ValueError):
                        continue
            line_parts: List[str] = []
            if size_bits:
                line_parts.append("size " + "/".join(size_bits))
            for key, label in (("sl_atr_mult", "SL"), ("tp_atr_mult", "TP")):
                try:
                    value = float(tuning_overrides.get(key, 1.0) or 1.0)
                except (TypeError, ValueError):
                    value = None
                if value is not None:
                    line_parts.append(f"{label}×{value:.2f}")
            try:
                confidence = float(tuning_overrides.get("confidence", 0.0) or 0.0)
            except (TypeError, ValueError):
                confidence = None
            if confidence is not None:
                line_parts.append(f"confidence {confidence:.2f}")
            if line_parts:
                overlay["tuning_line"] = "Parameter tuner overrides: " + " · ".join(line_parts)
        budget_learning = state.get("ai_budget_learning") if isinstance(state, dict) else None
        if isinstance(budget_learning, dict):
            symbols = budget_learning.get("symbols")
            if isinstance(symbols, dict) and symbols:
                ranked = sorted(
                    (
                        (sym, float((payload or {}).get("bias", 1.0) or 1.0), float((payload or {}).get("skip_weight", 0.0) or 0.0))
                        for sym, payload in symbols.items()
                        if isinstance(payload, dict)
                    ),
                    key=lambda item: (item[1], -item[2]),
                )
                for sym, bias, skip_weight in ranked:
                    if bias < 0.95 or skip_weight > 0.5:
                        overlay["budget_learner_line"] = (
                            f"Budget learner: {sym} bias {bias:.2f} · skip_weight {skip_weight:.2f}"
                        )
                        break
        return overlay

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
        extra_context: Dict[str, Any],
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
        if extra_context:
            for key in (
                "playbook_line",
                "sentinel_line",
                "budget_trend_line",
                "tuning_line",
                "budget_learner_line",
            ):
                value = extra_context.get(key)
                if isinstance(value, str) and value.strip():
                    lines.append(value)
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
        budget_summary = _summarize_ai_budget_line(ai_budget)
        if budget_summary:
            lines.append(budget_summary)
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
        budget_summary = _summarize_ai_budget_line(ai_budget)
        if budget_summary:
            parts.append(budget_summary)
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

    def _record_copilot_position(
        self,
        state: Dict[str, Any],
        proposal_id: str,
        normalized: Dict[str, Any],
        execution: Dict[str, Any],
        opened_ts: float,
    ) -> None:
        symbol = str(normalized.get("symbol") or "").upper().strip()
        direction = str(normalized.get("direction") or "").upper().strip()
        if not symbol or direction not in {"LONG", "SHORT"}:
            return

        side = "BUY" if direction == "LONG" else "SELL"
        entry_price = self._safe_float(
            execution.get("entry_price") if isinstance(execution, dict) else None
        )
        if entry_price is None:
            entry_price = self._safe_float(normalized.get("entry_price"))

        notional = self._safe_float(normalized.get("notional"))
        if notional is None and isinstance(execution, dict):
            notional = self._safe_float(execution.get("notional"))

        quantity = None
        if isinstance(execution, dict):
            quantity = self._safe_float(execution.get("quantity"))
        if quantity is None and notional is not None and entry_price not in {None, 0.0}:
            try:
                quantity = notional / float(entry_price)
            except (TypeError, ValueError, ZeroDivisionError):
                quantity = None
        quantity = self._safe_float(quantity)

        stop_loss = self._safe_float(normalized.get("stop_loss"))
        take_profit = self._safe_float(normalized.get("take_profit"))

        record: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "direction": direction,
            "entry_kind": normalized.get("entry_kind") or "market",
            "bucket": "copilot",
            "status": "open",
        }

        if entry_price is not None:
            record["entry"] = entry_price
            record["entry_price"] = entry_price
            record.setdefault("ctx", {})
            record["ctx"]["mid_price"] = entry_price
        if notional is not None:
            try:
                notional_val = float(notional)
            except (TypeError, ValueError):
                notional_val = None
            else:
                record["notional"] = notional_val
                record["notional_usdt"] = notional_val
                record["positionNotional"] = notional_val
        if quantity is not None:
            try:
                qty_abs = abs(float(quantity))
            except (TypeError, ValueError):
                qty_abs = None
            else:
                record["qty"] = qty_abs
                record["size"] = qty_abs
                signed_qty = qty_abs if side == "BUY" else -qty_abs
                record["positionAmt"] = signed_qty
        if stop_loss is not None:
            record["sl"] = stop_loss
            record["stop_loss"] = stop_loss
        if take_profit is not None:
            record["tp"] = take_profit
            record["take_profit"] = take_profit

        if isinstance(opened_ts, (int, float)) and math.isfinite(opened_ts):
            record["opened_at"] = opened_ts
            try:
                record["opened_at_iso"] = datetime.fromtimestamp(opened_ts, tz=timezone.utc).isoformat()
            except Exception:
                pass

        ctx_block = record.setdefault("ctx", {})
        ctx_block.setdefault("source", "copilot_proposal")
        ctx_block.setdefault("mode", "dashboard")

        if isinstance(execution, dict) and execution:
            try:
                record["execution"] = json.loads(json.dumps(execution))
            except Exception:
                record["execution"] = execution

        ai_meta: Dict[str, Any] = {
            "source": "copilot_proposal",
            "proposal_id": proposal_id,
        }
        for key in ("timeframe", "note"):
            value = normalized.get(key)
            if isinstance(value, str):
                trimmed = value.strip()
                if trimmed:
                    ai_meta[key] = trimmed
        for numeric_key in ("confidence", "risk_reward", "size_multiplier"):
            numeric_value = self._safe_float(normalized.get(numeric_key))
            if numeric_value is not None:
                ai_meta[numeric_key] = numeric_value
        if ai_meta:
            record["ai"] = ai_meta

        live_trades = state.get("live_trades")
        if not isinstance(live_trades, dict):
            live_trades = {}

        existing = live_trades.get(symbol)
        if isinstance(existing, dict):
            merged_record = {**existing, **record}
            existing_ctx = existing.get("ctx") if isinstance(existing.get("ctx"), dict) else None
            record_ctx = record.get("ctx") if isinstance(record.get("ctx"), dict) else None
            if existing_ctx or record_ctx:
                merged_ctx: Dict[str, Any] = {}
                if existing_ctx:
                    merged_ctx.update(existing_ctx)
                if record_ctx:
                    merged_ctx.update(record_ctx)
                merged_record["ctx"] = merged_ctx
            existing_ai = existing.get("ai") if isinstance(existing.get("ai"), dict) else None
            record_ai = record.get("ai") if isinstance(record.get("ai"), dict) else None
            if existing_ai or record_ai:
                merged_ai: Dict[str, Any] = {}
                if existing_ai:
                    merged_ai.update(existing_ai)
                if record_ai:
                    merged_ai.update(record_ai)
                merged_record["ai"] = merged_ai
        else:
            merged_record = record

        try:
            sanitized = json.loads(json.dumps(merged_record, default=lambda o: str(o)))
        except Exception:
            sanitized = merged_record

        live_trades[symbol] = sanitized
        state["live_trades"] = live_trades

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

            now_ts = time.time()
            try:
                execution = self._place_trade_proposal(proposal_key, normalized)
            except Exception as exc:
                target["status"] = "failed"
                target["error"] = str(exc)
                target["payload"] = normalized
                state["ai_trade_proposals"] = queue
                try:
                    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True))
                except Exception:
                    pass
                raise

            target["status"] = "executed"
            target["executed_at"] = now_ts
            target["payload"] = normalized
            target["execution"] = execution
            target.pop("error", None)
            state["ai_trade_proposals"] = queue
            self._record_copilot_position(state, proposal_key, normalized, execution, now_ts)
            try:
                STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True))
            except Exception as exc:
                logger.debug("Failed to persist proposal status for %s: %s", proposal_key, exc)

            public = {**normalized, "id": proposal_key, "status": "executed", "executed_at": now_ts}
            if execution:
                public["execution"] = execution
            _append_ai_activity_entry(
                "analysis",
                f"Trade proposal executed ({symbol} {direction})",
                data={
                    "proposal_id": proposal_key,
                    "execution": execution,
                    "source": "dashboard_chat",
                },
            )
            return {"proposal": public, "execution": execution}

        raise RuntimeError("unable to queue trade proposal")

    def _execute_analysis_prompt(
        self,
        *,
        context_text: str,
        prompt: str,
        fallback: str,
        model: str,
        key_candidates: List[Tuple[str, str]],
        default_temperature: float,
        proposals_source: str,
        ensure_follow_up: bool = True,
        message_for_action: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
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
                    log.debug("Invalid ASTER_DASHBOARD_AI_TEMPERATURE=%s — ignoring", dash_temp)
                else:
                    if abs(parsed_temp - 1.0) > 1e-6:
                        temperature_override = parsed_temp
            else:
                temperature_override = default_temperature

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

            self._record_dashboard_ai_usage(
                "analysis", model, usage, key_source=label, note="strategy_copilot"
            )
            if not reply_text:
                reply_text = fallback

            action_payload = self._extract_action(reply_text)
            queued_action = (
                self._queue_trade_action(action_payload, message_for_action)
                if action_payload
                else None
            )

            proposals_raw = self._extract_trade_proposals(reply_text)
            stored_proposals = self._store_trade_proposals(proposals_raw, source=proposals_source)
            if proposals_raw:
                action_line = re.compile(r"^\s*ACTION:\s*\{", re.IGNORECASE)
                cleaned_lines = [
                    line for line in reply_text.splitlines() if not action_line.match(line.strip())
                ]
                reply_text = "\n".join(cleaned_lines)

            formatted = self._format_local_reply(reply_text)
            if ensure_follow_up:
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
            if queued_action:
                response["queued_action"] = queued_action

            meta = {
                "attempted_keys": list(attempted_keys),
                "key_source": label,
                "usage": usage,
                "stored_proposals": stored_proposals,
                "queued_action": queued_action,
                "error": None,
            }
            return response, meta

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

        action_payload = self._extract_action(fallback_text)
        queued_action = (
            self._queue_trade_action(action_payload, message_for_action)
            if action_payload
            else None
        )

        formatted = self._format_local_reply(fallback_text)
        if ensure_follow_up:
            formatted = self._ensure_analysis_follow_up(formatted)

        response = {"analysis": formatted, "model": model, "source": "fallback"}
        if queued_action:
            response["queued_action"] = queued_action

        meta = {
            "attempted_keys": list(attempted_keys),
            "key_source": None,
            "usage": None,
            "stored_proposals": None,
            "queued_action": queued_action,
            "error": last_exc,
        }
        return response, meta

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
            copilot_overlay,
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
        focus_symbols = self._detect_symbols_in_text(message)[:3]
        if not key_candidates:
            notice = (
                "Dashboard chat requires an OpenAI API key. "
                "Add ASTER_CHAT_OPENAI_API_KEY or reuse ASTER_OPENAI_API_KEY "
                "in the AI controls to start chatting with the strategy copilot."
            )
            formatted_notice = self._format_local_reply(notice)
            formatted_notice = self._ensure_analysis_follow_up(formatted_notice)
            response = {
                "analysis": formatted_notice,
                "reply": formatted_notice,
                "model": "local",
                "source": "missing_chat_key",
            }
            if focus_symbols:
                response["analysis_focus"] = focus_symbols
            return response
        model = (env.get("ASTER_AI_MODEL") or "gpt-4.1").strip() or "gpt-4.1"

        context_text = self._build_context_text(
            stats,
            history,
            open_trades,
            ai_activity,
            ai_budget,
            decision_stats,
            recent_plans,
            technical_snapshot,
            copilot_overlay,
        )
        universe_symbols = self._market_universe_symbols()
        if focus_symbols:
            formatted_focus = ", ".join(focus_symbols)
            universe_prompt = (
                f"Anchor your analysis to the requested market{'s' if len(focus_symbols) > 1 else ''}: {formatted_focus}. "
                "Cross-check liquidity, funding, and volatility against broader market telemetry and note any data gaps."
            )
        else:
            if universe_symbols:
                sample = ", ".join(universe_symbols[:40])
                if len(universe_symbols) > 40:
                    sample = f"{sample}, …"
                universe_prompt = (
                    f"The full Aster perpetual universe contains {len(universe_symbols)} symbols: {sample}. "
                    "Scan this entire list when selecting candidates and call out when liquidity or data gaps limit confidence."
                )
            else:
                universe_prompt = (
                    "Work across the entire set of Aster-listed perpetual pairs, not just the currently traded majors."
                )

        prompt = self._build_analysis_prompt(
            universe_prompt=universe_prompt,
            focus_symbols=focus_symbols,
            user_question=message,
        )

        outbound_headline = "Manual analysis requested"
        if focus_symbols:
            outbound_headline = f"Manual analysis requested ({', '.join(focus_symbols)})"
        _append_ai_activity_entry(
            "analysis",
            outbound_headline,
            body=_summarize_text(message, 260),
            data={
                "source": "dashboard_chat",
                "direction": "outbound",
                "mode": "analysis",
                "focus_symbols": focus_symbols,
            },
        )

        response, meta = self._execute_analysis_prompt(
            context_text=context_text,
            prompt=prompt,
            fallback=fallback,
            model=model,
            key_candidates=key_candidates,
            default_temperature=0.4,
            proposals_source="chat_analysis",
            ensure_follow_up=True,
            message_for_action=message,
        )

        inbound_data: Dict[str, Any] = {
            "source": "dashboard_chat",
            "direction": "inbound",
            "mode": "analysis",
            "focus_symbols": focus_symbols,
        }
        key_source = meta.get("key_source")
        if key_source:
            inbound_data["key_source"] = key_source
        usage = meta.get("usage")
        if usage:
            inbound_data["usage"] = usage
        queued_action = meta.get("queued_action")
        if queued_action:
            inbound_data["queued_action"] = queued_action

        trade_proposals = response.get("trade_proposals")
        if trade_proposals:
            inbound_data["trade_proposals"] = [item.get("id") for item in trade_proposals]

        if response.get("source") == "openai":
            inbound_headline = "Manual analysis received"
            if focus_symbols:
                inbound_headline = f"Manual analysis received ({', '.join(focus_symbols)})"
            _append_ai_activity_entry(
                "analysis",
                inbound_headline,
                body=_summarize_text(response.get("analysis", ""), 260),
                data=inbound_data,
            )
        else:
            inbound_data["attempted_keys"] = meta.get("attempted_keys", [])
            error_obj = meta.get("error")
            if error_obj:
                inbound_data["error"] = str(error_obj)
            _append_ai_activity_entry(
                "warning",
                "Manual analysis fallback used",
                body=_summarize_text(response.get("analysis", ""), 260),
                data=inbound_data,
            )

        if focus_symbols:
            response["analysis_focus"] = focus_symbols
        response["reply"] = response.get("analysis", "")
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
            copilot_overlay,
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

        model = (env.get("ASTER_AI_MODEL") or "gpt-4.1").strip() or "gpt-4.1"
        context_text = self._build_context_text(
            stats,
            history,
            open_trades,
            ai_activity,
            ai_budget,
            decision_stats,
            recent_plans,
            technical_snapshot,
            copilot_overlay,
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
        prompt = self._build_analysis_prompt(
            universe_prompt=universe_prompt,
            focus_symbols=[],
            user_question=None,
        )

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

        response, meta = self._execute_analysis_prompt(
            context_text=context_text,
            prompt=prompt,
            fallback=fallback,
            model=model,
            key_candidates=key_candidates,
            default_temperature=0.3,
            proposals_source="analysis",
            ensure_follow_up=True,
        )

        if response.get("source") == "openai":
            log_data: Dict[str, Any] = {
                "source": "dashboard_chat",
                "direction": "inbound",
                "model": model,
                "key_source": meta.get("key_source"),
                "mode": "analysis",
            }
            usage = meta.get("usage")
            if usage:
                log_data["usage"] = usage
            trade_proposals = response.get("trade_proposals")
            if trade_proposals:
                log_data["trade_proposals"] = [item.get("id") for item in trade_proposals]
            _append_ai_activity_entry(
                "analysis",
                "Market analysis received",
                body=_summarize_text(response.get("analysis", ""), 260),
                data=log_data,
            )
            return response

        attempt_list = meta.get("attempted_keys", [])
        last_error = meta.get("error")
        fallback_text = response.get("analysis", "")
        data: Dict[str, Any] = {
            "source": "dashboard_chat",
            "direction": "inbound",
            "mode": "analysis",
            "attempted_keys": attempt_list,
        }
        if last_error:
            data["error"] = str(last_error)
        _append_ai_activity_entry(
            "warning",
            "Market analysis fallback used",
            body=_summarize_text(fallback_text, 260),
            data=data,
        )
        return response


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
    history_source = state.get("trade_history", [])
    if not isinstance(history_source, list):
        history_source = []
    run_started_at = _resolve_run_started_at(state)
    filtered_history = _filter_history_for_run(history_source, run_started_at)
    history_window: List[Dict[str, Any]] = [dict(entry) for entry in filtered_history[-200:]]

    stats_history: List[Dict[str, Any]] = history_window
    display_history: List[Dict[str, Any]] = []
    for entry in _strip_realized_income_trades(stats_history):
        normalized = dict(entry)
        normalized["opened_at_iso"] = _format_ts(entry.get("opened_at"))
        normalized["closed_at_iso"] = _format_ts(entry.get("closed_at"))
        display_history.append(normalized)

    env_cfg = CONFIG.get("env", {}) if isinstance(CONFIG, dict) else {}
    open_trades = state.get("live_trades", {})
    try:
        enriched_open = await asyncio.to_thread(enrich_open_positions, open_trades, env_cfg)
    except Exception as exc:
        logger.debug("active position enrichment failed: %s", exc)
        enriched_open = open_trades
    stats = _compute_stats(stats_history)
    decision_stats = _decision_summary(state)
    ai_budget = _normalize_ai_budget(state.get("ai_budget", {}))
    ai_activity_raw = state.get("ai_activity", [])
    if isinstance(ai_activity_raw, list):
        # Preserve chronological ordering so analysis entries appear before
        # subsequent execution events in the feed. Only the most recent
        # window is returned to keep the payload compact.
        ai_activity = list(ai_activity_raw[-120:])
    else:
        ai_activity = []
    ai_requests = _summarize_ai_requests(ai_activity)
    playbook_activity = _collect_playbook_activity(ai_activity)
    playbook_state = _resolve_playbook_state(state.get("ai_playbook"), playbook_activity)
    playbook_process = _build_playbook_process(playbook_activity)
    market_overview = _extract_playbook_market_overview(state)
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
    cumulative_summary = _cumulative_summary(state, stats=stats, ai_budget=ai_budget)
    history_summary = _build_history_summary(stats)
    hero_metrics = _build_hero_metrics(
        cumulative_summary,
        stats,
        history_count=len(display_history),
    )

    return {
        "open": enriched_open,
        "history": display_history[::-1],
        "stats": stats.dict(),
        "decision_stats": decision_stats,
        "cumulative_stats": cumulative_summary,
        "history_summary": history_summary,
        "hero_metrics": hero_metrics,
        "ai_budget": ai_budget,
        "ai_activity": ai_activity,
        "ai_requests": ai_requests,
        "playbook": playbook_state,
        "playbook_activity": playbook_activity,
        "playbook_process": playbook_process,
        "playbook_market_overview": market_overview,
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


@app.websocket("/ws/positions")
async def ws_positions(ws: WebSocket) -> None:
    await position_stream.register(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        await position_stream.unregister(ws)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("dashboard_server:app", host="0.0.0.0", port=8000, reload=False)
