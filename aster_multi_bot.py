#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
aster_multi_bot.py
Beibehaltener Funktionsumfang + robuste Optimierungen:

- Logging sauber (sichtbar ohne externes Setup)
- 24h-Ticker-Cache (weniger API-Calls)
- Equity-Cache im RiskManager (weniger /balance)
- Bracket-Setzen kompatibel (neu: qty+entry, Fallback: alte Signatur)
- FastTP: TP-Replace mit korrekt gesetztem side=BUY/SELL
- /positionRisk nur 1× pro Zyklus; pos_map an handle_symbol() übergeben
- ML-Policy Hooks: decide(ctx)->TAKE/SKIP+size_bucket, note_entry/exit
- ENV-getriebene Signalkontrollen:
  * RSI-Schwellen per ENV (ASTER_RSI_BUY_MIN/ASTER_RSI_SELL_MAX)
  * Optionaler Trend-Align-Fallback (ASTER_ALLOW_TREND_ALIGN + ASTER_ALIGN_RSI_PAD)
"""

import asyncio
import os
import time
import math
import statistics
import json
import uuid
import hmac
import hashlib
import logging
import signal
import textwrap
import re
import copy
import threading
from pathlib import Path
from datetime import datetime, timezone, date
from urllib.parse import urlencode
from typing import Dict, List, Tuple, Optional, Any, Callable, Sequence, Set, Iterable

from collections import OrderedDict, deque
from concurrent.futures import Future

import requests

from openai_client import OpenAIClient, OpenAIError

try:  # optional dependency, used for real-time user-data streams
    import websocket  # type: ignore
except Exception:  # pragma: no cover - optional, handled at runtime
    websocket = None

from decimal import Decimal
from requests.exceptions import RequestException

try:
    import numpy as np  # noqa: F401
except Exception:
    raise RuntimeError("Dieses Modul benötigt numpy. Bitte: pip install numpy")

from ml_policy import BanditPolicy, FEATURES as POLICY_FEATURES
from ai_extensions import (
    BudgetLearner,
    ParameterTuner,
    PlaybookManager,
    PostmortemLearning,
)
from brackets_guard import BracketGuard, replace_tp_for_open_position as _bg_replace_tp

# ========= Logging =========
LOGFMT = "%(asctime)s │ %(levelname)-5s │ %(name)s │ %(message)s"
DATEFMT = "%Y-%m-%d %H:%M:%S"
_level = os.getenv("ASTER_LOGLEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, _level, logging.INFO), format=LOGFMT, datefmt=DATEFMT, force=True)
log = logging.getLogger("aster")

# ========= ENV / Defaults =========
BASE = os.getenv("ASTER_EXCHANGE_BASE", "https://fapi.asterdex.com").rstrip("/")
API_KEY = os.getenv("ASTER_API_KEY", "")
API_SECRET = os.getenv("ASTER_API_SECRET", "")
RECV_WINDOW = int(os.getenv("ASTER_RECV_WINDOW", "10000"))

MODE = os.getenv("ASTER_MODE", "standard").strip().lower()
PRESET_MODE = os.getenv("ASTER_PRESET_MODE", "mid").strip().lower()
AI_MODE_ENABLED = MODE == "ai" or os.getenv("ASTER_AI_MODE", "").lower() in ("1", "true", "yes", "on")
# Allow falling back to the standard OPENAI_API_KEY environment variable so
# existing setups keep working without extra configuration.
OPENAI_API_KEY = os.getenv("ASTER_OPENAI_API_KEY", "").strip()
if not OPENAI_API_KEY:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
CHAT_OPENAI_API_KEY = os.getenv("ASTER_CHAT_OPENAI_API_KEY", "").strip()
AI_MODEL = os.getenv("ASTER_AI_MODEL", "gpt-4o").strip() or "gpt-4o"
AI_DAILY_BUDGET = float(os.getenv("ASTER_AI_DAILY_BUDGET_USD", "20") or 0)
if PRESET_MODE in {"high", "att"}:
    if AI_DAILY_BUDGET > 0:
        log.info("Preset %s forces unlimited AI budget (overriding %.2f USD cap)", PRESET_MODE.upper(), AI_DAILY_BUDGET)
    AI_DAILY_BUDGET = 0.0
AI_STRICT_BUDGET = os.getenv("ASTER_AI_STRICT_BUDGET", "true").lower() in ("1", "true", "yes", "on")
SENTINEL_ENABLED = os.getenv("ASTER_AI_SENTINEL_ENABLED", "true").lower() in ("1", "true", "yes", "on")
SENTINEL_DECAY_MINUTES = float(os.getenv("ASTER_AI_SENTINEL_DECAY_MINUTES", "60") or 60)
SENTINEL_NEWS_ENDPOINT = os.getenv("ASTER_AI_NEWS_ENDPOINT", "").strip()
SENTINEL_NEWS_TOKEN = os.getenv("ASTER_AI_NEWS_API_KEY", "").strip()
SENTINEL_ONCHAIN_ENDPOINT = os.getenv("ASTER_AI_ONCHAIN_ENDPOINT", "").strip()
SENTINEL_ONCHAIN_TOKEN = os.getenv("ASTER_AI_ONCHAIN_API_KEY", "").strip() or SENTINEL_NEWS_TOKEN
SENTINEL_SOCIAL_ENDPOINT = os.getenv("ASTER_AI_SOCIAL_ENDPOINT", "").strip()
SENTINEL_SOCIAL_TOKEN = os.getenv("ASTER_AI_SOCIAL_API_KEY", "").strip() or SENTINEL_NEWS_TOKEN
SENTINEL_OPTIONS_ENDPOINT = os.getenv("ASTER_AI_OPTIONS_ENDPOINT", "").strip()
SENTINEL_OPTIONS_TOKEN = os.getenv("ASTER_AI_OPTIONS_API_KEY", "").strip() or SENTINEL_NEWS_TOKEN
SENTINEL_MODEL = os.getenv("ASTER_AI_SENTINEL_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
SENTINEL_AI_TTL = max(120.0, float(os.getenv("ASTER_AI_SENTINEL_AI_TTL_SECONDS", "600") or 600))
AI_MIN_INTERVAL_SECONDS = float(os.getenv("ASTER_AI_MIN_INTERVAL_SECONDS", "8") or 0.0)
AI_CONCURRENCY = max(1, int(os.getenv("ASTER_AI_CONCURRENCY", "3") or 1))
AI_GLOBAL_COOLDOWN = max(0.0, float(os.getenv("ASTER_AI_GLOBAL_COOLDOWN_SECONDS", "2.0") or 0.0))
AI_PLAN_TIMEOUT = max(10.0, float(os.getenv("ASTER_AI_PLAN_TIMEOUT_SECONDS", "45") or 0.0))
_default_pending_limit = max(4, AI_CONCURRENCY * 3)
AI_PENDING_LIMIT = max(
    AI_CONCURRENCY,
    int(os.getenv("ASTER_AI_PENDING_LIMIT", str(_default_pending_limit)) or _default_pending_limit),
)

X_NEWS_ENABLED = os.getenv("ASTER_X_NEWS_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
X_NEWS_COOKIES_PATH = os.getenv("ASTER_X_AUTH_FILE", "xAuth.json").strip() or "xAuth.json"
X_NEWS_CACHE_TTL = max(120.0, float(os.getenv("ASTER_X_NEWS_CACHE_TTL_SECONDS", "900") or 900.0))
X_NEWS_LIMIT = max(5, int(os.getenv("ASTER_X_NEWS_LIMIT", "30") or 30))
X_NEWS_SCROLL_ATTEMPTS = max(4, int(os.getenv("ASTER_X_NEWS_SCROLL_ATTEMPTS", "25") or 25))
X_NEWS_SCROLL_DELAY = max(0.25, float(os.getenv("ASTER_X_NEWS_SCROLL_DELAY", "1.2") or 1.2))
X_NEWS_FEED = os.getenv("ASTER_X_NEWS_FEED", "top").strip().lower() or "top"

_OPENAI_CLIENT: Optional[OpenAIClient] = None


_SENSITIVE_FIELD_NAMES: Set[str] = {
    "ASTER_API_KEY",
    "Aster_API_KEY",
    "ASTER_API_SECRET",
    "ASTER_OPENAI_API_KEY",
    "ASTER_CHAT_OPENAI_API_KEY",
}
_REDACTED_TOKEN = "********"


def _collect_sensitive_tokens() -> Tuple[str, ...]:
    tokens: List[str] = []
    for candidate in (
        API_KEY,
        API_SECRET,
        OPENAI_API_KEY,
        CHAT_OPENAI_API_KEY,
        os.getenv("ASTER_API_KEY", "").strip(),
        os.getenv("ASTER_API_SECRET", "").strip(),
        os.getenv("ASTER_OPENAI_API_KEY", "").strip(),
        os.getenv("ASTER_CHAT_OPENAI_API_KEY", "").strip(),
        os.getenv("OPENAI_API_KEY", "").strip(),
    ):
        if not candidate:
            continue
        if candidate not in tokens:
            tokens.append(candidate)
    return tuple(tokens)


_SENSITIVE_TOKEN_VALUES: Tuple[str, ...] = _collect_sensitive_tokens()


def _mask_sensitive_text(text: str) -> str:
    if not isinstance(text, str) or not text:
        return text
    masked = text
    for token in _SENSITIVE_TOKEN_VALUES:
        if token:
            masked = masked.replace(token, _REDACTED_TOKEN)
    return masked


def _mask_sensitive_payload(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized: Dict[Any, Any] = {}
        for key, item in value.items():
            if isinstance(key, str) and key in _SENSITIVE_FIELD_NAMES:
                sanitized[key] = _REDACTED_TOKEN
            else:
                sanitized[key] = _mask_sensitive_payload(item)
        return sanitized
    if isinstance(value, list):
        return [_mask_sensitive_payload(item) for item in value]
    if isinstance(value, tuple):
        return [_mask_sensitive_payload(item) for item in value]
    if isinstance(value, set):
        return [_mask_sensitive_payload(item) for item in value]
    if isinstance(value, str):
        return _mask_sensitive_text(value)
    try:
        text = str(value)
    except Exception:
        return value
    masked_text = _mask_sensitive_text(text)
    if masked_text != text:
        return masked_text
    return value


def _shared_openai_client() -> Optional[OpenAIClient]:
    global _OPENAI_CLIENT
    if not OPENAI_API_KEY:
        return None
    if _OPENAI_CLIENT is None:
        max_conn = max(4, AI_CONCURRENCY * 2)
        _OPENAI_CLIENT = OpenAIClient(
            OPENAI_API_KEY,
            default_model=AI_MODEL,
            max_connections=max_conn,
        )
    return _OPENAI_CLIENT


SENTINEL_RESPONSE_SCHEMA: Dict[str, Any] = {
    "name": "sentinel_enrichment",
    "schema": {
        "type": "object",
        "properties": {
            "event_risk": {"type": "number"},
            "hype_score": {"type": "number"},
            "label": {
                "type": "string",
                "enum": ["green", "yellow", "red"],
            },
            "size_factor": {"type": "number"},
            "rationale": {"type": "string"},
            "highlights": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": ["event_risk", "hype_score", "label"],
        "additionalProperties": False,
    },
}

if AI_MODE_ENABLED and not OPENAI_API_KEY:
    log.warning(
        "AI mode is enabled but no OpenAI API key was provided via ASTER_OPENAI_API_KEY or OPENAI_API_KEY."
        " AI requests will remain disabled until a key is configured."
    )

QUOTE = os.getenv("ASTER_QUOTE", "USDT")
INTERVAL = os.getenv("ASTER_INTERVAL", "5m")
HTF_INTERVAL = os.getenv("ASTER_HTF_INTERVAL", "30m")
KLINES = int(os.getenv("ASTER_KLINES", "360"))

DEFAULT_MARKETS_URL = os.getenv(
    "ASTER_MARKETS_URL", f"{BASE}/fapi/v1/exchangeInfo"
).strip()


def _split_env_symbols(value: str) -> List[str]:
    return [s.strip().upper() for s in value.split(",") if s.strip()]


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


def _fetch_markets_symbols(default_quote: str) -> List[str]:
    if not DEFAULT_MARKETS_URL:
        return []
    try:
        resp = requests.get(DEFAULT_MARKETS_URL, timeout=10)
        resp.raise_for_status()
    except Exception as exc:
        log.debug("Could not fetch markets from %s: %s", DEFAULT_MARKETS_URL, exc)
        return []

    try:
        payload = resp.json()
    except ValueError:
        return _parse_symbols_from_html(resp.text, default_quote)

    symbols = []
    q = default_quote.upper() if default_quote else ""
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
        return _parse_symbols_from_html(resp.text, default_quote)

    return sorted(set(symbols))


def _resolve_include_symbols(default_quote: str) -> List[str]:
    env_symbols = _split_env_symbols(os.getenv("ASTER_INCLUDE_SYMBOLS", ""))
    if env_symbols:
        return env_symbols
    symbols = _fetch_markets_symbols(default_quote)
    if symbols:
        log.info("Loaded %d default symbols from Aster markets", len(symbols))
    return symbols


INCLUDE = _resolve_include_symbols(QUOTE)
EXCLUDE = set(_split_env_symbols(os.getenv("ASTER_EXCLUDE_SYMBOLS", "")))
# Standardmäßig alle Symbole scannen; via ENV begrenzen
UNIVERSE_MAX = int(os.getenv("ASTER_UNIVERSE_MAX", "0"))
UNIVERSE_ROTATE = os.getenv("ASTER_UNIVERSE_ROTATE", "true").lower() in ("1", "true", "yes", "on")

ORDERBOOK_DEPTH_LIMIT = max(5, min(1000, int(os.getenv("ASTER_ORDERBOOK_DEPTH_LIMIT", "60") or 60)))
ORDERBOOK_PREFETCH = max(0, int(os.getenv("ASTER_ORDERBOOK_PREFETCH", "14") or 14))
ORDERBOOK_TTL = max(0.5, float(os.getenv("ASTER_ORDERBOOK_TTL", "2.5") or 2.5))
ORDERBOOK_ON_DEMAND = max(0, int(os.getenv("ASTER_ORDERBOOK_ON_DEMAND", "6") or 6))


USER_STREAM_ENABLED = os.getenv("ASTER_USER_STREAM", "true").lower() in ("1", "true", "yes", "on")


def _int_env(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except Exception:
        return max(0, int(default))
    return max(0, value)


def _parse_leverage_env(raw_value: Optional[str], fallback: float) -> float:
    token = str(raw_value or "").strip()
    if not token:
        return float(fallback)
    lowered = token.lower()
    if lowered in {"max", "unlimited", "∞", "infinite", "inf"}:
        return float("inf")
    try:
        numeric = float(token)
    except (TypeError, ValueError):
        return float(fallback)
    if numeric <= 0:
        return float("inf")
    return float(numeric)


def _coerce_positive_float(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(numeric) or numeric <= 0:
        return 0.0
    return float(numeric)


def _coerce_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(numeric):
        return default
    return float(numeric)


def _coerce_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    try:
        return int(str(value).strip())
    except Exception:
        try:
            return int(float(value))
        except Exception:
            return default


MIN_QUOTE_VOL = float(os.getenv("ASTER_MIN_QUOTE_VOL_USDT", "150000"))
SPREAD_BPS_MAX = float(os.getenv("ASTER_SPREAD_BPS_MAX", "0.0030"))  # 0.30 %
WICKINESS_MAX = float(os.getenv("ASTER_WICKINESS_MAX", "0.97"))
MIN_EDGE_R = float(os.getenv("ASTER_MIN_EDGE_R", "0.30"))

BANDIT_FLAG = os.getenv("ASTER_BANDIT_ENABLED", "true").lower() in ("1", "true", "yes", "on")
BANDIT_ENABLED = BANDIT_FLAG and not AI_MODE_ENABLED
SIZE_MULT_BASE = float(os.getenv("ASTER_SIZE_MULT", "1.00"))
SIZE_MULT_S = float(os.getenv("ASTER_SIZE_MULT_S", str(SIZE_MULT_BASE)))
SIZE_MULT_M = float(os.getenv("ASTER_SIZE_MULT_M", str(1.4 * SIZE_MULT_BASE)))
SIZE_MULT_L = float(os.getenv("ASTER_SIZE_MULT_L", str(1.9 * SIZE_MULT_BASE)))
SIZE_MULT_FLOOR = max(0.0, min(5.0, float(os.getenv("ASTER_SIZE_MULT_FLOOR", "0.0"))))
SIZE_MULT_CAP = max(0.1, float(os.getenv("ASTER_SIZE_MULT_CAP", "3.0")))

CONFIDENCE_SIZING_ENABLED = os.getenv("ASTER_CONFIDENCE_SIZING", "true").lower() in (
    "1",
    "true",
    "yes",
    "on",
)
CONFIDENCE_SIZING_MIN = max(0.0, float(os.getenv("ASTER_CONFIDENCE_SIZE_MIN", "1.0")))
CONFIDENCE_SIZING_MAX = max(
    CONFIDENCE_SIZING_MIN,
    float(os.getenv("ASTER_CONFIDENCE_SIZE_MAX", "3.0")),
)
CONFIDENCE_SIZING_BLEND = min(
    1.0,
    max(0.0, float(os.getenv("ASTER_CONFIDENCE_SIZE_BLEND", "1"))),
)
CONFIDENCE_SIZING_EXP = max(0.2, float(os.getenv("ASTER_CONFIDENCE_SIZE_EXP", "2.0")))

ALPHA_ENABLED = os.getenv("ASTER_ALPHA_ENABLED", "true").lower() in ("1", "true", "yes", "on")
ALPHA_THRESHOLD = float(os.getenv("ASTER_ALPHA_THRESHOLD", "0.55"))
ALPHA_WARMUP = int(os.getenv("ASTER_ALPHA_WARMUP", "40"))
ALPHA_LR = float(os.getenv("ASTER_ALPHA_LR", "0.05"))
ALPHA_L2 = float(os.getenv("ASTER_ALPHA_L2", "0.0005"))
ALPHA_MIN_CONF = float(os.getenv("ASTER_ALPHA_MIN_CONF", "0.2"))
ALPHA_PROMOTE_DELTA = float(os.getenv("ASTER_ALPHA_PROMOTE_DELTA", "0.15"))
ALPHA_REWARD_MARGIN = float(os.getenv("ASTER_ALPHA_REWARD_MARGIN", "0.05"))

DEFAULT_NOTIONAL = float(os.getenv("ASTER_DEFAULT_NOTIONAL", "250"))
RISK_PER_TRADE = float(os.getenv("ASTER_RISK_PER_TRADE", "0.006"))
_PRESET_LEVERAGE_DEFAULTS = {
    "low": "4",
    "mid": "10",
    "high": "max",
    "att": "max",
}
_leverage_seed = os.getenv("ASTER_LEVERAGE")
if not _leverage_seed:
    _leverage_seed = _PRESET_LEVERAGE_DEFAULTS.get(PRESET_MODE, "10")
LEVERAGE_SOURCE = str(_leverage_seed or "10")
LEVERAGE = _parse_leverage_env(LEVERAGE_SOURCE, 10.0)
LEVERAGE_IS_UNLIMITED = not math.isfinite(LEVERAGE)
EQUITY_FRACTION = float(os.getenv("ASTER_EQUITY_FRACTION", "0.66"))
MIN_NOTIONAL_ENV = float(os.getenv("ASTER_MIN_NOTIONAL_USDT", "5"))
MAX_NOTIONAL_USDT = float(os.getenv("ASTER_MAX_NOTIONAL_USDT", "0"))  # 0 = kein Cap

SL_ATR_MULT = float(os.getenv("ASTER_SL_ATR_MULT", "1.00"))
TP_ATR_MULT = float(os.getenv("ASTER_TP_ATR_MULT", "1.60"))

FAST_TP_ENABLED = os.getenv("FAST_TP_ENABLED", "true").lower() in ("1", "true", "yes", "on")
FASTTP_MIN_R = float(os.getenv("FASTTP_MIN_R", "0.30"))
FAST_TP_RET1 = float(os.getenv("FAST_TP_RET1", "-0.0010"))
FAST_TP_RET3 = float(os.getenv("FAST_TP_RET3", "-0.0020"))
FASTTP_SNAP_ATR = float(os.getenv("FASTTP_SNAP_ATR", "0.25"))
FASTTP_COOLDOWN_S = int(os.getenv("FASTTP_COOLDOWN_S", "15"))

FUNDING_FILTER_ENABLED = os.getenv("ASTER_FUNDING_FILTER_ENABLED", "true").lower() in ("1", "true", "yes", "on")
FUNDING_MAX_LONG = float(os.getenv("ASTER_FUNDING_MAX_LONG", "0.0010"))  # 0.10 %
FUNDING_MAX_SHORT = float(os.getenv("ASTER_FUNDING_MAX_SHORT", "0.0010"))  # 0.10 %

NON_ARB_FILTER_ENABLED = os.getenv("ASTER_NON_ARB_FILTER_ENABLED", "true").lower() in ("1", "true", "yes", "on")
NON_ARB_CLAMP_BPS = abs(float(os.getenv("ASTER_NON_ARB_CLAMP_BPS", "0.0005"))) or 0.0005
NON_ARB_EDGE_THRESHOLD = abs(float(os.getenv("ASTER_NON_ARB_EDGE_THRESHOLD", "0.00005")))
NON_ARB_SKIP_GAP = abs(float(os.getenv("ASTER_NON_ARB_SKIP_GAP", str(NON_ARB_CLAMP_BPS * 3.0))))

HTTP_RETRIES = max(0, int(os.getenv("ASTER_HTTP_RETRIES", "2")))
HTTP_BACKOFF = max(0.0, float(os.getenv("ASTER_HTTP_BACKOFF", "0.6")))
HTTP_TIMEOUT = max(5.0, float(os.getenv("ASTER_HTTP_TIMEOUT", "20")))
KLINE_CACHE_SEC = max(5.0, float(os.getenv("ASTER_KLINE_CACHE_SEC", "45")))

MAX_OPEN_GLOBAL = _int_env("ASTER_MAX_OPEN_GLOBAL", 0)
MAX_OPEN_PER_SYMBOL = _int_env("ASTER_MAX_OPEN_PER_SYMBOL", 1)

_ROOT_DIR = Path(__file__).resolve().parent
_STATE_FILE_ENV = os.getenv("ASTER_STATE_FILE", "aster_state.json")
STATE_FILE = _ROOT_DIR / _STATE_FILE_ENV
PAPER = os.getenv("ASTER_PAPER", "false").lower() in ("1", "true", "yes", "on")

LOOP_SLEEP = int(os.getenv("ASTER_LOOP_SLEEP", "30"))  # Sekunden
WORKING_TYPE = os.getenv("ASTER_WORKING_TYPE", "MARK_PRICE")  # an Guard weitergeben
QUOTE_VOLUME_COOLDOWN_CYCLES = max(
    0, int(os.getenv("ASTER_QUOTE_VOLUME_COOLDOWN_CYCLES", "500"))
)

# Signalkontrolle (neu, per ENV einstellbar)
RSI_BUY_MIN = float(os.getenv("ASTER_RSI_BUY_MIN", "52"))
RSI_SELL_MAX = float(os.getenv("ASTER_RSI_SELL_MAX", "48"))
ALLOW_ALIGN = os.getenv("ASTER_ALLOW_TREND_ALIGN", "false").lower() in ("1", "true", "yes", "on")
ALIGN_RSI_PAD = float(os.getenv("ASTER_ALIGN_RSI_PAD", "1.0"))
TREND_BIAS = os.getenv("ASTER_TREND_BIAS", "with").strip().lower()
CONTRARIAN = TREND_BIAS in ("against", "att", "contrarian")

# ========= Utils =========
def ema(data: List[float], period: int) -> List[float]:
    if not data:
        return []
    k = 2.0 / (period + 1.0)
    out = [data[0]]
    for x in data[1:]:
        out.append(out[-1] + k * (x - out[-1]))
    return out


def _sma_series(values: List[float], period: int) -> List[float]:
    if not values:
        return []
    window: deque = deque()
    running = 0.0
    out: List[float] = []
    for val in values:
        window.append(val)
        running += val
        if len(window) > period and period > 0:
            running -= window.popleft()
        count = len(window)
        avg = running / count if count else 0.0
        out.append(avg)
    return out


def _rolling_std(values: List[float], period: int) -> List[float]:
    if not values:
        return []
    window: deque = deque()
    sum_x = 0.0
    sum_x2 = 0.0
    out: List[float] = []
    for val in values:
        window.append(val)
        sum_x += val
        sum_x2 += val * val
        if len(window) > period and period > 0:
            removed = window.popleft()
            sum_x -= removed
            sum_x2 -= removed * removed
        count = len(window)
        if count <= 0:
            out.append(0.0)
            continue
        mean = sum_x / count
        variance = max(0.0, (sum_x2 / count) - (mean * mean))
        out.append(math.sqrt(variance))
    return out


def bollinger_bands(
    closes: List[float], period: int = 20, std_mult: float = 2.0
) -> Tuple[List[float], List[float], List[float], List[float]]:
    if not closes:
        return [], [], [], []
    middle = _sma_series(closes, period)
    stds = _rolling_std(closes, period)
    upper: List[float] = []
    lower: List[float] = []
    width: List[float] = []
    for mid, std in zip(middle, stds):
        band_shift = std_mult * std
        upper_val = mid + band_shift
        lower_val = mid - band_shift
        upper.append(upper_val)
        lower.append(lower_val)
        width.append(max(upper_val - lower_val, 0.0))
    return upper, middle, lower, width


def stoch_rsi(
    closes: List[float], period: int = 14, smooth_k: int = 3, smooth_d: int = 3
) -> Tuple[List[float], List[float]]:
    if not closes:
        return [], []
    rsi_vals = rsi(closes, period)
    if not rsi_vals:
        return [], []
    stoch: List[float] = []
    if period <= 0:
        stoch.extend([50.0] * len(rsi_vals))
    else:
        min_deque: deque = deque()
        max_deque: deque = deque()
        for idx, val in enumerate(rsi_vals):
            while min_deque and min_deque[-1][0] >= val:
                min_deque.pop()
            min_deque.append((val, idx))
            while max_deque and max_deque[-1][0] <= val:
                max_deque.pop()
            max_deque.append((val, idx))

            boundary = idx - period + 1
            while min_deque and min_deque[0][1] < boundary:
                min_deque.popleft()
            while max_deque and max_deque[0][1] < boundary:
                max_deque.popleft()

            if idx + 1 < period:
                stoch.append(50.0)
                continue

            low = min_deque[0][0]
            high = max_deque[0][0]
            rng = max(high - low, 1e-9)
            stoch.append(((val - low) / rng) * 100.0)
    k_line = _sma_series(stoch, max(smooth_k, 1))
    d_line = _sma_series(k_line, max(smooth_d, 1))
    return k_line, d_line


def supertrend_indicator(
    kl: Sequence[Sequence[float]], period: int = 10, multiplier: float = 3.0
) -> Tuple[List[float], List[float]]:
    n = len(kl)
    if n < period + 2:
        return [0.0] * n, [0.0] * n
    highs = [float(row[2]) for row in kl]
    lows = [float(row[3]) for row in kl]
    closes = [float(row[4]) for row in kl]

    tr: List[float] = [0.0] * n
    for i in range(1, n):
        tr[i] = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )

    atr: List[float] = [0.0] * n
    if period <= 0:
        period = 1
    initial_slice = tr[1 : period + 1]
    if not initial_slice:
        return [0.0] * n, [0.0] * n
    atr_val = sum(initial_slice) / float(len(initial_slice))
    for i in range(period, n):
        if i == period:
            atr[i] = atr_val
        else:
            atr_val = ((atr[i - 1] * (period - 1)) + tr[i]) / float(period)
            atr[i] = atr_val
    for i in range(period):
        atr[i] = atr_val

    basic_upper = [0.0] * n
    basic_lower = [0.0] * n
    for i in range(n):
        hl2 = (highs[i] + lows[i]) / 2.0
        shift = multiplier * atr[i]
        basic_upper[i] = hl2 + shift
        basic_lower[i] = hl2 - shift

    final_upper = list(basic_upper)
    final_lower = list(basic_lower)
    supertrend_line = [0.0] * n
    direction = [0.0] * n

    for i in range(period, n):
        if i > period:
            if (basic_upper[i] < final_upper[i - 1]) or (closes[i - 1] > final_upper[i - 1]):
                final_upper[i] = basic_upper[i]
            else:
                final_upper[i] = final_upper[i - 1]

            if (basic_lower[i] > final_lower[i - 1]) or (closes[i - 1] < final_lower[i - 1]):
                final_lower[i] = basic_lower[i]
            else:
                final_lower[i] = final_lower[i - 1]

            prev_dir = direction[i - 1]
            if prev_dir >= 0 and final_lower[i] < final_lower[i - 1]:
                final_lower[i] = final_lower[i - 1]
            if prev_dir <= 0 and final_upper[i] > final_upper[i - 1]:
                final_upper[i] = final_upper[i - 1]

        if closes[i] > final_upper[i]:
            direction[i] = 1.0
        elif closes[i] < final_lower[i]:
            direction[i] = -1.0
        else:
            direction[i] = direction[i - 1] if i > 0 else 0.0

        supertrend_line[i] = final_lower[i] if direction[i] >= 0 else final_upper[i]

    for i in range(period):
        direction[i] = direction[period]
        supertrend_line[i] = supertrend_line[period]

    return supertrend_line, direction


def rsi(closes: List[float], period: int = 14) -> List[float]:
    if len(closes) < period + 1:
        return [50.0] * len(closes)
    gains, losses = [0.0], [0.0]
    for i in range(1, len(closes)):
        ch = closes[i] - closes[i - 1]
        gains.append(max(0.0, ch))
        losses.append(max(0.0, -ch))
    avg_gain = sum(gains[1: period + 1]) / period
    avg_loss = sum(losses[1: period + 1]) / period
    out = [50.0] * period
    for i in range(period + 1, len(closes) + 1):
        g = gains[i - 1]; l = losses[i - 1]
        avg_gain = (avg_gain * (period - 1) + g) / period
        avg_loss = (avg_loss * (period - 1) + l) / period
        rs = avg_gain / (avg_loss + 1e-12)
        out.append(100.0 - (100.0 / (1.0 + rs)))
    return out[-len(closes):]

def atr_abs_from_klines(kl: List[List[float]], period: int = 14) -> float:
    if len(kl) < period + 1:
        return 0.0
    trs: List[float] = []
    prev_close = float(kl[0][4])
    for i in range(1, len(kl)):
        h = float(kl[i][2]); l = float(kl[i][3]); c = float(kl[i][4])
        tr = max(h - l, abs(h - prev_close), abs(l - prev_close))
        trs.append(tr); prev_close = c
    if not trs:
        return 0.0
    return sum(trs[-period:]) / float(period)

def adx_latest(kl: List[List[float]], period: int = 14) -> Tuple[float, float]:
    """Return (adx_last, delta) for the most recent bar."""
    n = len(kl)
    if n <= period + 1:
        return 25.0, 0.0
    highs = [float(k[2]) for k in kl]
    lows = [float(k[3]) for k in kl]
    closes = [float(k[4]) for k in kl]
    tr: List[float] = []
    plus_dm: List[float] = []
    minus_dm: List[float] = []
    for i in range(1, n):
        up = highs[i] - highs[i - 1]
        down = lows[i - 1] - lows[i]
        plus_dm.append(up if up > down and up > 0 else 0.0)
        minus_dm.append(down if down > up and down > 0 else 0.0)
        tr.append(max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1])))
    if len(tr) < period:
        return 25.0, 0.0

    def _dx_at(idx: int) -> float:
        start = idx - period + 1
        if start < 0:
            start = 0
        tr_sum = sum(tr[start: idx + 1])
        if tr_sum <= 0:
            return 0.0
        plus_sum = sum(plus_dm[start: idx + 1])
        minus_sum = sum(minus_dm[start: idx + 1])
        plus_di = 100.0 * (plus_sum / tr_sum)
        minus_di = 100.0 * (minus_sum / tr_sum)
        denom = plus_di + minus_di
        if denom <= 0:
            return 0.0
        return 100.0 * abs(plus_di - minus_di) / denom

    dx_vals = [_dx_at(i) for i in range(period - 1, len(tr))]
    if not dx_vals:
        return 25.0, 0.0
    last_slice = dx_vals[-period:] if len(dx_vals) >= period else dx_vals
    adx_last = sum(last_slice) / float(len(last_slice))
    if len(dx_vals) > period:
        prev_slice = dx_vals[-2 * period: -period]
        adx_prev = sum(prev_slice) / float(len(prev_slice)) if prev_slice else adx_last
    else:
        adx_prev = adx_last
    return adx_last, adx_last - adx_prev

def round_price(symbol: str, price: float, tick: float) -> float:
    if tick <= 0:
        return float(price)
    steps = math.floor(price / tick + 1e-12)
    return float(steps * tick)

def _format_decimal(value: float) -> str:
    s = f"{float(value):.12f}".rstrip("0").rstrip(".")
    return s or "0"


def format_qty(qty: float, step: float) -> str:
    q = max(0.0, math.floor(qty / step) * step)
    return _format_decimal(q)


def build_bracket_payload(kind: str, side: str, price: float, position_side: Optional[str] = None) -> str:
    """Create the attached-stop/take-profit payload for the entry order.

    Binance-compatible futures endpoints expect the payload to only carry the
    trigger meta data. Passing an explicit ``side`` inside the nested JSON
    causes Aster's API to silently drop the bracket instructions, which is why
    we mirror the format used by ``BracketGuard`` ("closePosition" implicitly
    closes on the opposing side). The helper also accepts an optional
    ``position_side`` to remain compatible with hedge-mode accounts.
    """

    kind_norm = kind.upper()
    payload = {
        "type": "STOP_MARKET" if kind_norm in {"SL", "STOP"} else "TAKE_PROFIT_MARKET",
        "trigger": {
            "type": WORKING_TYPE,
            "price": _format_decimal(price),
        },
        "closePosition": True,
    }
    if position_side:
        payload["positionSide"] = position_side
    return json.dumps(payload, separators=(",", ":"))


def clamp(value: float, lower: float, upper: float) -> float:
    if lower > upper:
        lower, upper = upper, lower
    return max(lower, min(upper, value))


def _confidence_size_target(confidence: float) -> float:
    conf = max(0.0, min(1.0, float(confidence)))
    span = max(0.0, CONFIDENCE_SIZING_MAX - CONFIDENCE_SIZING_MIN)
    if span <= 0:
        return max(0.0, CONFIDENCE_SIZING_MIN)
    scaled = CONFIDENCE_SIZING_MIN + (conf ** CONFIDENCE_SIZING_EXP) * span
    return max(0.0, scaled)


class DailyBudgetTracker:
    def __init__(self, state: Dict[str, Any], limit: float, strict: bool = True):
        self._state = state
        self.limit = max(0.0, float(limit or 0.0))
        self.strict = bool(strict)

    def _bucket(self) -> Dict[str, Any]:
        bucket = self._state.setdefault("ai_budget", {})
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if bucket.get("date") != today:
            bucket["date"] = today
            bucket["spent"] = 0.0
            bucket["history"] = []
            bucket["stats"] = {}
            bucket["count"] = 0
        bucket.setdefault("spent", 0.0)
        history = bucket.setdefault("history", [])
        bucket.setdefault("stats", {})
        count_val = bucket.get("count")
        if not isinstance(count_val, (int, float)):
            count_val = len(history)
        bucket["count"] = max(int(count_val or 0), len(history))
        return bucket

    def spent(self) -> float:
        bucket = self._bucket()
        return float(bucket.get("spent", 0.0) or 0.0)

    def remaining(self) -> Optional[float]:
        if self.limit <= 0:
            return None
        return max(0.0, self.limit - self.spent())

    def can_spend(
        self,
        estimate: float,
        *,
        kind: Optional[str] = None,
        model: Optional[str] = None,
    ) -> bool:
        estimate = max(0.0, float(estimate or 0.0))
        if estimate <= 0:
            avg = self.average_cost(kind=kind, model=model)
            if avg is not None:
                estimate = avg
        if self.limit <= 0:
            return True
        allowed = (self.spent() + estimate) <= self.limit
        return allowed or not self.strict

    def record(self, cost: float, meta: Optional[Dict[str, Any]] = None) -> None:
        bucket = self._bucket()
        amount = max(0.0, float(cost or 0.0))
        bucket["spent"] = float(bucket.get("spent", 0.0) or 0.0) + amount
        history = bucket.get("history") or []
        history.append({
            "ts": time.time(),
            "cost": float(amount),
            "meta": meta or {},
        })
        if len(history) > 48:
            history = history[-48:]
        bucket["history"] = history
        bucket["count"] = int(bucket.get("count", 0) or 0) + 1
        stats = bucket.setdefault("stats", {})
        model_key = str((meta or {}).get("model") or "default")
        kind_key = str((meta or {}).get("kind") or "unknown")

        def _update_stats(key: str) -> None:
            rec = stats.setdefault(key, {"avg": 0.0, "n": 0, "last": 0.0, "updated": 0.0})
            n = int(rec.get("n", 0) or 0)
            avg = float(rec.get("avg", 0.0) or 0.0)
            new_n = n + 1
            new_avg = ((avg * n) + amount) / max(new_n, 1)
            rec.update({"avg": float(new_avg), "n": new_n, "last": float(amount), "updated": time.time()})

        for key in (
            f"{model_key}::{kind_key}",
            f"{model_key}::*",
            f"*::{kind_key}",
            "*::*",
        ):
            _update_stats(key)
        self._state["ai_budget"] = bucket

    def snapshot(self) -> Dict[str, Any]:
        bucket = self._bucket()
        remaining = self.remaining()
        return {
            "date": bucket.get("date"),
            "spent": float(bucket.get("spent", 0.0) or 0.0),
            "limit": float(self.limit),
            "remaining": remaining,
            "history": list(bucket.get("history") or [])[-12:],
            "strict": self.strict,
            "stats": bucket.get("stats", {}),
            "count": int(bucket.get("count", 0) or 0),
        }

    def average_cost(self, *, kind: Optional[str] = None, model: Optional[str] = None) -> Optional[float]:
        stats = self._bucket().get("stats") or {}
        keys: List[str] = []
        model_key = str(model) if model else None
        kind_key = str(kind) if kind else None
        if model_key is not None and kind_key is not None:
            keys.append(f"{model_key}::{kind_key}")
        if model_key is not None:
            keys.append(f"{model_key}::*")
        if kind_key is not None:
            keys.append(f"*::{kind_key}")
        keys.append("*::*")
        for key in keys:
            rec = stats.get(key)
            if rec and rec.get("n", 0):
                return float(rec.get("avg", 0.0) or 0.0)
        return None


class NewsTrendSentinel:
    def __init__(
        self,
        exchange: "Exchange",
        state: Dict[str, Any],
        enabled: bool = True,
        decay_minutes: float = SENTINEL_DECAY_MINUTES,
        ai_client: Optional[OpenAIClient] = None,
    ):
        self.exchange = exchange
        self.state = state
        self.enabled = bool(enabled)
        self._ticker_cache: Dict[str, Dict[str, Any]] = {}
        self._last_payload: Dict[str, Dict[str, Any]] = {}
        self._decay = max(60.0, float(decay_minutes or 0) * 60.0)
        self._ai_client: Optional[OpenAIClient] = ai_client or _shared_openai_client()
        self._pending_ai: Dict[str, Dict[str, Any]] = {}
        self._ai_cache: Dict[str, Dict[str, Any]] = {}
        self._news_scraper: Optional[Any] = None
        self._news_scraper_unavailable = not X_NEWS_ENABLED
        self._news_scraper_error_logged = False
        self._news_error_cls: Optional[type] = None
        self._news_cache: Dict[str, Dict[str, Any]] = {}

    def set_ai_client(self, client: Optional[OpenAIClient]) -> None:
        if client is not None:
            self._ai_client = client

    def _consume_ai_enrichment(self, symbol: str) -> None:
        slot = self._pending_ai.get(symbol)
        if not slot:
            return
        future = slot.get("future")
        if not isinstance(future, Future):
            self._pending_ai.pop(symbol, None)
            return
        if not future.done():
            age = time.time() - float(slot.get("ts", 0.0))
            if age > 45.0:
                try:
                    future.cancel()
                except Exception:
                    pass
                self._pending_ai.pop(symbol, None)
            return
        self._pending_ai.pop(symbol, None)
        try:
            text, _usage, _raw = future.result()
        except Exception as exc:
            log.debug(f"sentinel ai enrichment failed {symbol}: {exc}")
            return
        if not text:
            return
        try:
            payload = json.loads(text)
        except Exception as exc:
            log.debug(f"sentinel ai enrichment parse failed {symbol}: {exc}")
            return
        payload["ts"] = time.time()
        self._ai_cache[symbol] = payload

    def _schedule_ai_enrichment(self, symbol: str, payload: Dict[str, Any], ctx: Optional[Dict[str, Any]]) -> None:
        if not self._ai_client or not self.enabled:
            return
        now = time.time()
        cached = self._ai_cache.get(symbol)
        if cached and now - float(cached.get("ts", 0.0)) < SENTINEL_AI_TTL:
            return
        if symbol in self._pending_ai:
            return
        events = payload.get("events") or []
        base_risk = float(payload.get("event_risk", 0.0) or 0.0)
        if not events and base_risk < 0.45:
            return
        request_payload: Dict[str, Any] = {
            "symbol": symbol,
            "events": events,
            "metrics": {
                "event_risk": base_risk,
                "hype_score": float(payload.get("hype_score", 0.0) or 0.0),
                "label": payload.get("label", "green"),
            },
        }
        meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
        if isinstance(meta, dict):
            request_payload["metrics"].update(
                {
                    "price_change_pct": meta.get("price_change_pct"),
                    "quote_volume": meta.get("quote_volume"),
                    "buy_ratio": meta.get("buy_ratio"),
                    "volatility": meta.get("volatility"),
                }
            )
        signals = payload.get("signals")
        if isinstance(signals, dict):
            request_payload["metrics"].update(
                {
                    "onchain_pressure": signals.get("sentinel_onchain_pressure"),
                    "social_sentiment": signals.get("sentinel_social_sentiment"),
                    "options_skew": signals.get("sentinel_options_skew"),
                }
            )
        if isinstance(ctx, dict):
            context_map = {}
            for key in ("htf_trend_up", "htf_trend_down", "sentinel_soft_block", "trend"):
                if key in ctx:
                    context_map[key] = ctx.get(key)
            if context_map:
                request_payload["context"] = context_map
        system_prompt = (
            "You enrich market sentinel telemetry for an automated crypto futures bot. "
            "Return strict JSON with event_risk (0-1), hype_score (0-1), label (green/yellow/red), "
            "size_factor (0-3 range), a concise rationale (<=80 words), and bullet highlights array."
        )
        try:
            user_payload = json.dumps(request_payload, sort_keys=True)
        except Exception as exc:
            log.debug(f"sentinel enrichment serialization failed {symbol}: {exc}")
            return
        try:
            future = self._ai_client.submit(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_payload},
                ],
                model=SENTINEL_MODEL,
                response_format={"type": "json_schema", "json_schema": SENTINEL_RESPONSE_SCHEMA},
                metadata={"component": "sentinel", "symbol": symbol},
                temperature=0.0,
                max_output_tokens=360,
            )
        except Exception as exc:
            log.debug(f"sentinel enrichment dispatch failed {symbol}: {exc}")
            return
        self._pending_ai[symbol] = {"future": future, "ts": now}

    def _apply_ai_enrichment(self, symbol: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        enriched = self._ai_cache.get(symbol)
        if not isinstance(enriched, dict):
            return payload
        ts = float(enriched.get("ts", 0.0))
        if time.time() - ts > SENTINEL_AI_TTL:
            return payload
        def _num(val: Any, default: float = 0.0) -> float:
            try:
                return float(val)
            except Exception:
                return default

        base_risk = float(payload.get("event_risk", 0.0) or 0.0)
        llm_risk = clamp(_num(enriched.get("event_risk"), base_risk), 0.0, 1.0)
        payload["event_risk"] = clamp((base_risk * 2.0 + llm_risk) / 3.0, 0.0, 1.0)

        base_hype = float(payload.get("hype_score", 0.0) or 0.0)
        llm_hype = clamp(_num(enriched.get("hype_score"), base_hype), 0.0, 1.0)
        payload["hype_score"] = clamp((base_hype * 2.0 + llm_hype) / 3.0, 0.0, 1.0)

        base_label = str(payload.get("label", "green")).lower()
        llm_label = str(enriched.get("label", base_label)).lower()
        severity = {"green": 0, "yellow": 1, "red": 2}
        if severity.get(llm_label, 0) > severity.get(base_label, 0):
            payload["label"] = llm_label

        size_factor = _num(payload.get("actions", {}).get("size_factor", 1.0), 1.0)
        llm_size = clamp(_num(enriched.get("size_factor"), size_factor), 0.0, 3.0)
        blended = clamp((size_factor + llm_size) / 2.0, 0.0, 3.0)
        payload.setdefault("actions", {})["size_factor"] = blended

        rationale = enriched.get("rationale")
        ai_meta = payload.setdefault("ai_meta", {})
        if isinstance(rationale, str) and rationale.strip():
            ai_meta["rationale"] = rationale.strip()
        highlights = enriched.get("highlights")
        if isinstance(highlights, list):
            cleaned = [str(item).strip() for item in highlights if str(item).strip()]
            if cleaned:
                ai_meta["highlights"] = cleaned
        return payload

    def prime_ticker_cache(self, payload: Dict[str, Dict[str, Any]]) -> None:
        if not payload:
            return
        now = time.time()
        for sym, rec in payload.items():
            if not sym or not isinstance(rec, dict):
                continue
            self._ticker_cache[sym] = {"ts": now, "payload": dict(rec)}

    def refresh(self, symbols: List[str], prefetched: Optional[Dict[str, Dict[str, Any]]] = None) -> None:
        if not self.enabled:
            return
        if prefetched:
            self.prime_ticker_cache(prefetched)
        elif not self._ticker_cache:
            try:
                bulk = self.exchange.get_ticker_24hr()
            except Exception as exc:
                log.debug(f"sentinel bulk ticker fetch failed: {exc}")
                bulk = None
            mapping: Dict[str, Dict[str, Any]] = {}
            if isinstance(bulk, list):
                for entry in bulk:
                    sym = entry.get("symbol") if isinstance(entry, dict) else None
                    if sym:
                        mapping[sym] = entry
            elif isinstance(bulk, dict) and bulk.get("symbol"):
                mapping[str(bulk.get("symbol"))] = bulk
            if mapping:
                self.prime_ticker_cache(mapping)
        for sym in symbols:
            try:
                self.evaluate(sym, {}, store_only=True)
            except Exception:
                continue

    def _fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        if not self.enabled:
            return {}
        now = time.time()
        cached = self._ticker_cache.get(symbol)
        if cached and (now - cached.get("ts", 0.0)) < 45:
            return cached.get("payload", {})
        try:
            payload = self.exchange.get_ticker_24hr(symbol)
        except Exception as exc:
            log.debug(f"sentinel ticker fetch failed {symbol}: {exc}")
            payload = {}
        self._ticker_cache[symbol] = {"ts": now, "payload": payload}
        return payload or {}

    def _news_events(self, symbol: str) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        if SENTINEL_NEWS_ENDPOINT:
            try:
                headers = {}
                params = {"symbol": symbol}
                if SENTINEL_NEWS_TOKEN:
                    headers["Authorization"] = f"Bearer {SENTINEL_NEWS_TOKEN}"
                resp = requests.get(
                    SENTINEL_NEWS_ENDPOINT,
                    params=params,
                    headers=headers,
                    timeout=6,
                )
                resp.raise_for_status()
                data = resp.json()
                items = data if isinstance(data, list) else data.get("items") or data.get("results") or []
                events: List[Dict[str, Any]] = []
                for item in items[:6]:
                    title = str(item.get("title") or item.get("headline") or "Event").strip()
                    source = str(item.get("source") or item.get("origin") or "news").strip()
                    severity = str(item.get("severity") or item.get("label") or "info").strip()
                    events.append({
                        "headline": title,
                        "source": source,
                        "severity": severity.lower(),
                    })
                return events
            except Exception as exc:
                log.debug(f"sentinel news fetch failed {symbol}: {exc}")
        return self._local_news_events(symbol)

    def _ensure_local_news_scraper(self):
        if self._news_scraper_unavailable:
            return None
        if self._news_scraper is not None:
            return self._news_scraper
        try:
            from news import NewsScraper, NewsScraperError  # type: ignore
        except Exception as exc:
            log.debug(f"sentinel local news unavailable: {exc}")
            self._news_scraper_unavailable = True
            return None
        feed = X_NEWS_FEED if X_NEWS_FEED in {"top", "live"} else "top"
        try:
            scraper = NewsScraper(
                cookies_path=X_NEWS_COOKIES_PATH,
                feed=feed,
                tweet_limit=X_NEWS_LIMIT,
                scroll_delay=X_NEWS_SCROLL_DELAY,
                scroll_attempts=X_NEWS_SCROLL_ATTEMPTS,
                cache_ttl=X_NEWS_CACHE_TTL,
            )
        except Exception as exc:
            log.debug(f"sentinel local news init failed: {exc}")
            self._news_scraper_unavailable = True
            return None
        self._news_scraper = scraper
        try:
            self._news_error_cls = NewsScraperError  # type: ignore[name-defined]
        except Exception:
            self._news_error_cls = None
        return self._news_scraper

    def _local_news_events(self, symbol: str) -> List[Dict[str, Any]]:
        scraper = self._ensure_local_news_scraper()
        if scraper is None:
            return []
        now = time.time()
        cached = self._news_cache.get(symbol)
        if cached and now - float(cached.get("ts", 0.0)) < X_NEWS_CACHE_TTL:
            return cached.get("events", [])
        try:
            posts = scraper.fetch(symbol, limit=X_NEWS_LIMIT)
        except Exception as exc:
            if self._news_error_cls and isinstance(exc, self._news_error_cls):
                self._news_scraper_unavailable = True
            if isinstance(exc, FileNotFoundError):
                self._news_scraper_unavailable = True
            if not self._news_scraper_error_logged:
                log.debug(f"sentinel x news fetch failed {symbol}: {exc}")
                self._news_scraper_error_logged = True
            return []
        events: List[Dict[str, Any]] = []
        engagement_scores: List[float] = []
        feed_name = getattr(scraper, "feed", X_NEWS_FEED)
        for post in posts:
            if not isinstance(post, dict):
                continue
            text = str(post.get("text") or "").strip()
            if not text:
                continue
            headline = text.replace("\n", " ").strip()
            if len(headline) > 220:
                headline = headline[:217].rstrip() + "…"
            source = str(post.get("handle") or post.get("author") or "x-top-post").strip() or "x-top-post"
            entry: Dict[str, Any] = {
                "headline": headline,
                "source": source,
                "severity": "info",
            }
            url = post.get("url")
            if isinstance(url, str) and url:
                entry["url"] = url
            timestamp = post.get("timestamp")
            if isinstance(timestamp, str) and timestamp:
                entry["timestamp"] = timestamp
            for key in ("likes", "retweets", "replies"):
                value = post.get(key)
                if isinstance(value, (int, float)):
                    entry[key] = int(value)
            events.append(entry)
            engagement = 0.0
            for weight, key in ((0.6, "retweets"), (0.5, "likes"), (0.3, "replies")):
                value = post.get(key)
                if isinstance(value, (int, float)):
                    engagement += float(value) * weight
            if engagement:
                engagement_scores.append(engagement)
        hype = 0.0
        if events:
            base_ratio = min(1.0, len(events) / max(1, scraper.tweet_limit))
            hype = max(0.0, min(1.0, base_ratio * 0.6))
            if engagement_scores:
                top_score = max(engagement_scores)
                hype = min(1.0, max(hype, hype + min(0.4, top_score / 5000.0)))
        meta: Dict[str, Any] = {
            "source": "x-top-posts",
            "post_count": len(events),
            "query": symbol,
        }
        meta["feed"] = feed_name
        meta["tweet_limit"] = getattr(scraper, "tweet_limit", X_NEWS_LIMIT)
        if engagement_scores:
            meta["top_engagement"] = max(engagement_scores)
            meta["avg_engagement"] = sum(engagement_scores) / len(engagement_scores)
        self._news_cache[symbol] = {
            "ts": now,
            "events": events,
            "hype": hype,
            "meta": meta,
        }
        summary = {
            "symbol": symbol,
            "query": symbol,
            "feed": feed_name,
            "count": len(events),
            "hype": round(hype, 4),
            "tweet_limit": getattr(scraper, "tweet_limit", X_NEWS_LIMIT),
            "meta": meta,
            "events": events[: min(len(events), 5)],
            "cached": False,
            "fetched_at": now,
        }
        log.debug("X_NEWS_RESULT %s", json.dumps(summary, ensure_ascii=False))
        return events

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        if isinstance(value, (int, float)):
            try:
                return float(value)
            except (TypeError, ValueError):
                return None
        if isinstance(value, str):
            token = value.strip()
            if not token:
                return None
            try:
                return float(token)
            except (TypeError, ValueError):
                return None
        return None

    def _fetch_external_payload(
        self,
        endpoint: str,
        token: str,
        symbol: str,
        *,
        timeout: float = 6.0,
    ) -> Optional[Dict[str, Any]]:
        if not endpoint:
            return None
        try:
            headers = {}
            params = {"symbol": symbol}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            resp = requests.get(endpoint, params=params, headers=headers, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list):
                return {"items": data}
            if isinstance(data, dict):
                return data
        except Exception as exc:
            log.debug(f"sentinel external fetch failed %s: %s", symbol, exc)
        return None

    def _normalize_external_events(
        self,
        source: str,
        payload: Iterable[Any],
        *,
        limit: int = 4,
    ) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        if not payload:
            return events
        for raw in list(payload)[:limit]:
            if isinstance(raw, dict):
                title = raw.get("title") or raw.get("headline") or raw.get("name") or raw.get("event")
                detail = raw.get("detail") or raw.get("description")
                severity = raw.get("severity") or raw.get("label") or raw.get("type")
                when = raw.get("time") or raw.get("ts") or raw.get("timestamp")
            else:
                title = str(raw)
                detail = None
                severity = None
                when = None
            entry: Dict[str, Any] = {"source": source}
            if isinstance(title, str) and title.strip():
                entry["headline"] = title.strip()
            if isinstance(detail, str) and detail.strip():
                entry["detail"] = detail.strip()
            if isinstance(severity, str) and severity.strip():
                entry["severity"] = severity.strip().lower()
            val = self._safe_float(when)
            if val is not None:
                entry["ts"] = val
            if entry.get("headline"):
                events.append(entry)
        return events

    def _parse_external_payload(
        self,
        prefix: str,
        payload: Optional[Dict[str, Any]],
    ) -> Tuple[Dict[str, float], List[Dict[str, Any]]]:
        if not isinstance(payload, dict):
            return {}, []
        metrics: Dict[str, float] = {}
        def _ingest_block(block: Any) -> None:
            if not isinstance(block, dict):
                return
            for key, value in block.items():
                if key in {"events", "alerts", "signals", "items", "highlights"}:
                    continue
                num = self._safe_float(value)
                if num is None:
                    continue
                metrics[f"{prefix}_{str(key)}"] = num

        _ingest_block(payload)
        meta_block = payload.get("metrics")
        _ingest_block(meta_block)
        nested = payload.get("data")
        if isinstance(nested, dict):
            _ingest_block(nested)
        events_payload: List[Any] = []
        for key in ("events", "alerts", "signals", "items", "highlights"):
            chunk = payload.get(key)
            if isinstance(chunk, list):
                events_payload.extend(chunk)
        events = self._normalize_external_events(prefix, events_payload)
        return metrics, events

    def _select_metric(
        self,
        metrics: Dict[str, float],
        keys: Sequence[str],
        *,
        default: float = 0.0,
        clamp_min: float = -1.0,
        clamp_max: float = 1.0,
    ) -> float:
        for key in keys:
            for metric_key, value in metrics.items():
                if metric_key == key or metric_key.endswith(f"_{key}") or metric_key.split("_", 1)[-1] == key:
                    return clamp(value, clamp_min, clamp_max)
        return default

    def _collect_external_metrics(
        self, symbol: str
    ) -> Tuple[Dict[str, float], Dict[str, Any], List[Dict[str, Any]]]:
        summary: Dict[str, float] = {}
        meta: Dict[str, Any] = {}
        events: List[Dict[str, Any]] = []

        onchain_payload = self._fetch_external_payload(
            SENTINEL_ONCHAIN_ENDPOINT, SENTINEL_ONCHAIN_TOKEN, symbol
        )
        if onchain_payload:
            onchain_metrics, onchain_events = self._parse_external_payload("onchain", onchain_payload)
            if onchain_metrics:
                meta["onchain"] = onchain_metrics
                summary["sentinel_onchain_pressure"] = self._select_metric(
                    onchain_metrics,
                    ("pressure", "risk", "whale_score", "whale_pressure"),
                    clamp_min=-1.0,
                    clamp_max=1.0,
                )
                summary["sentinel_onchain_flow"] = self._select_metric(
                    onchain_metrics,
                    ("netflow", "net_flow", "flow", "exchange_flow", "stable_netflow"),
                    clamp_min=-1.0,
                    clamp_max=1.0,
                )
                summary["sentinel_onchain_exchange_inflow"] = self._select_metric(
                    onchain_metrics,
                    ("exchange_inflow", "inflow"),
                    clamp_min=0.0,
                    clamp_max=2.0,
                )
            if onchain_events:
                events.extend(onchain_events)

        social_payload = self._fetch_external_payload(
            SENTINEL_SOCIAL_ENDPOINT, SENTINEL_SOCIAL_TOKEN, symbol
        )
        if social_payload:
            social_metrics, social_events = self._parse_external_payload("social", social_payload)
            if social_metrics:
                meta["social"] = social_metrics
                summary["sentinel_social_sentiment"] = self._select_metric(
                    social_metrics,
                    ("sentiment", "score", "hype", "bullish_score"),
                    clamp_min=-1.0,
                    clamp_max=1.0,
                )
                summary["sentinel_social_volume"] = self._select_metric(
                    social_metrics,
                    ("volume", "message_volume", "buzz"),
                    clamp_min=0.0,
                    clamp_max=2.0,
                )
            if social_events:
                events.extend(social_events)

        options_payload = self._fetch_external_payload(
            SENTINEL_OPTIONS_ENDPOINT, SENTINEL_OPTIONS_TOKEN, symbol
        )
        if options_payload:
            options_metrics, options_events = self._parse_external_payload("options", options_payload)
            if options_metrics:
                meta["options"] = options_metrics
                summary["sentinel_options_skew"] = self._select_metric(
                    options_metrics,
                    ("skew", "risk_reversal", "rr", "delta_skew"),
                    clamp_min=-1.5,
                    clamp_max=1.5,
                )
                summary["sentinel_options_iv_rank"] = self._select_metric(
                    options_metrics,
                    ("iv_rank", "iv_percentile", "vol_rank"),
                    clamp_min=0.0,
                    clamp_max=1.0,
                )
            if options_events:
                events.extend(options_events)

        return summary, meta, events

    def _evaluate_from_ticker(self, symbol: str, ticker: Dict[str, Any]) -> Dict[str, Any]:
        price_change = 0.0
        quote_volume = 0.0
        taker_buy_quote = 0.0
        last_price = 0.0
        high_price = 0.0
        low_price = 0.0
        try:
            price_change = float(ticker.get("priceChangePercent", 0.0) or 0.0)
        except Exception:
            price_change = 0.0
        try:
            quote_volume = float(ticker.get("quoteVolume", 0.0) or 0.0)
        except Exception:
            quote_volume = 0.0
        try:
            taker_buy_quote = float(ticker.get("takerBuyQuoteVolume", 0.0) or 0.0)
        except Exception:
            taker_buy_quote = 0.0
        try:
            last_price = float(ticker.get("lastPrice", 0.0) or 0.0)
        except Exception:
            last_price = 0.0
        try:
            high_price = float(ticker.get("highPrice", 0.0) or 0.0)
        except Exception:
            high_price = 0.0
        try:
            low_price = float(ticker.get("lowPrice", 0.0) or 0.0)
        except Exception:
            low_price = 0.0

        spread_range = max(0.0, high_price - low_price)
        volatility = 0.0
        if last_price > 0.0:
            volatility = spread_range / max(last_price, 1e-9)

        buy_ratio = taker_buy_quote / max(quote_volume, 1e-9)
        volume_factor = clamp(math.log10(max(quote_volume, 1.0)), 0.0, 9.0) / 9.0
        trend_factor = clamp(abs(price_change) / 18.0, 0.0, 1.0)
        bias_factor = clamp(abs(buy_ratio - 0.5) * 1.8, 0.0, 1.0)

        event_risk = clamp(volatility * 1.2 + trend_factor * 0.5, 0.0, 1.0)
        if price_change < -9.0:
            event_risk = max(event_risk, 0.78)
        hype_score = clamp((volume_factor * 0.55) + (trend_factor * 0.55) + (bias_factor * 0.3), 0.0, 1.0)

        label = "green"
        hard_block = False
        if event_risk >= 0.82:
            label = "red"
            hard_block = True
        elif event_risk >= 0.55:
            label = "yellow"
        elif hype_score >= 0.7 and price_change >= 4.0:
            label = "yellow"

        size_factor = 1.0
        if label == "yellow":
            size_factor = 0.6
        if label == "red":
            size_factor = 0.0
        if label == "green" and hype_score > 0.7 and price_change > 0:
            size_factor = clamp(1.0 + (hype_score - 0.6), 1.0, 1.35)

        events: List[Dict[str, Any]] = []
        if price_change >= 8.0:
            events.append({
                "headline": f"{symbol} rallied {price_change:.1f}% in 24h",
                "source": "exchange",
                "severity": "positive",
            })
        if price_change <= -8.0:
            events.append({
                "headline": f"{symbol} dropped {abs(price_change):.1f}% in 24h",
                "source": "exchange",
                "severity": "warning",
            })
        if volatility > 0.12:
            events.append({
                "headline": "High intraday volatility detected",
                "source": "exchange",
                "severity": "warning",
            })

        return {
            "event_risk": float(clamp(event_risk, 0.0, 1.0)),
            "hype_score": float(clamp(hype_score, 0.0, 1.0)),
            "label": label,
            "actions": {"size_factor": float(size_factor), "hard_block": hard_block},
            "events": events,
            "meta": {
                "price_change_pct": price_change,
                "quote_volume": quote_volume,
                "buy_ratio": buy_ratio,
                "volatility": volatility,
            },
        }

    def evaluate(
        self,
        symbol: str,
        ctx: Optional[Dict[str, Any]] = None,
        *,
        store_only: bool = False,
    ) -> Dict[str, Any]:
        if not self.enabled:
            return {
                "label": "green",
                "event_risk": 0.0,
                "hype_score": 0.0,
                "actions": {"size_factor": 1.0, "hard_block": False},
                "events": [],
            }

        now = time.time()
        cached = self._last_payload.get(symbol)
        if cached and (now - cached.get("ts", 0.0)) < 30:
            payload = cached.get("payload", {})
        else:
            ticker = self._fetch_ticker(symbol)
            payload = self._evaluate_from_ticker(symbol, ticker)
            external_events = self._news_events(symbol)
            if external_events:
                payload["events"] = (payload.get("events") or []) + external_events
                severe = any(e.get("severity") == "critical" for e in external_events)
                if severe:
                    payload["event_risk"] = clamp(payload.get("event_risk", 0.0) + 0.2, 0.0, 1.0)
                    payload["label"] = "red"
                    payload.setdefault("actions", {})["hard_block"] = True
            cached_news = self._news_cache.get(symbol)
            if cached_news:
                ts_cached = float(cached_news.get("ts", 0.0) or 0.0)
                if now - ts_cached > X_NEWS_CACHE_TTL * 1.5:
                    self._news_cache.pop(symbol, None)
                else:
                    hype_bonus = float(cached_news.get("hype", 0.0) or 0.0)
                    if hype_bonus:
                        base_hype = float(payload.get("hype_score", 0.0) or 0.0)
                        payload["hype_score"] = clamp(max(base_hype, hype_bonus), 0.0, 1.0)
                    meta_block = cached_news.get("meta")
                    if isinstance(meta_block, dict):
                        external_meta_block = payload.setdefault("meta", {}).setdefault("external", {})
                        external_meta_block["x_social"] = dict(meta_block)
            extra_metrics, external_meta, extra_events = self._collect_external_metrics(symbol)
            if extra_events:
                payload["events"] = (payload.get("events") or []) + extra_events
            if external_meta:
                payload.setdefault("meta", {}).setdefault("external", {}).update(external_meta)
            if extra_metrics:
                signals = dict(extra_metrics)
                payload["signals"] = signals
                onchain_pressure = float(signals.get("sentinel_onchain_pressure", 0.0) or 0.0)
                social_sentiment = float(signals.get("sentinel_social_sentiment", 0.0) or 0.0)
                options_skew = float(signals.get("sentinel_options_skew", 0.0) or 0.0)
                onchain_flow = float(signals.get("sentinel_onchain_flow", 0.0) or 0.0)
                if onchain_pressure > 0.4:
                    payload["event_risk"] = clamp(
                        float(payload.get("event_risk", 0.0) or 0.0) + (onchain_pressure - 0.35) * 0.3,
                        0.0,
                        1.0,
                    )
                elif onchain_pressure < -0.45:
                    payload["event_risk"] = clamp(
                        float(payload.get("event_risk", 0.0) or 0.0) + (onchain_pressure + 0.35) * 0.2,
                        0.0,
                        1.0,
                    )
                if onchain_flow > 0.5:
                    payload.setdefault("actions", {}).setdefault("size_factor", 1.0)
                    payload["actions"]["size_factor"] = clamp(
                        float(payload["actions"]["size_factor"]) * (1.0 - min(onchain_flow, 1.0) * 0.25),
                        0.0,
                        1.2,
                    )
                if social_sentiment:
                    payload["hype_score"] = clamp(
                        float(payload.get("hype_score", 0.0) or 0.0)
                        + social_sentiment * 0.2,
                        0.0,
                        1.0,
                    )
                if options_skew < -0.3:
                    payload["event_risk"] = clamp(
                        float(payload.get("event_risk", 0.0) or 0.0) + abs(options_skew) * 0.2,
                        0.0,
                        1.0,
                    )
                elif options_skew > 0.35:
                    payload["event_risk"] = clamp(
                        float(payload.get("event_risk", 0.0) or 0.0) - options_skew * 0.15,
                        0.0,
                        1.0,
                    )
            payload = {
                "event_risk": float(payload.get("event_risk", 0.0) or 0.0),
                "hype_score": float(payload.get("hype_score", 0.0) or 0.0),
                "label": payload.get("label", "green"),
                "actions": payload.get("actions", {"size_factor": 1.0, "hard_block": False}),
                "events": payload.get("events", []),
                "meta": payload.get("meta", {}),
                "signals": payload.get("signals", {}),
            }
            self._last_payload[symbol] = {"ts": now, "payload": payload}

        self._consume_ai_enrichment(symbol)
        self._schedule_ai_enrichment(symbol, payload, ctx)
        payload = self._apply_ai_enrichment(symbol, payload)

        sentinel_state = self.state.setdefault("sentinel", {})
        sentinel_state[symbol] = {
            **payload,
            "updated": datetime.now(timezone.utc).isoformat(),
        }
        if ctx is not None:
            ctx["sentinel_event_risk"] = float(payload.get("event_risk", 0.0) or 0.0)
            ctx["sentinel_hype"] = float(payload.get("hype_score", 0.0) or 0.0)
            ctx["sentinel_label"] = payload.get("label", "green")
            signals = payload.get("signals")
            if isinstance(signals, dict):
                for key in (
                    "sentinel_onchain_pressure",
                    "sentinel_onchain_flow",
                    "sentinel_social_sentiment",
                    "sentinel_social_volume",
                    "sentinel_options_skew",
                    "sentinel_options_iv_rank",
                ):
                    val = signals.get(key)
                    if isinstance(val, (int, float)):
                        ctx[key] = float(val)
        if store_only:
            return payload
        return payload
POSTMORTEM_VOLATILITY_SCORES: Dict[str, float] = {
    "spike": 0.85,
    "shock": 0.9,
    "expansion": 0.6,
    "impulse": 0.55,
    "grind": 0.2,
    "balanced": 0.1,
    "range": -0.2,
    "compression": -0.55,
    "squeeze": -0.5,
    "whipsaw": -0.65,
    "chop": -0.6,
    "calm": -0.25,
}

POSTMORTEM_EXECUTION_SCORES: Dict[str, float] = {
    "ideal": 0.8,
    "precise": 0.75,
    "fast": 0.55,
    "front_run": 0.35,
    "partial": -0.25,
    "slow": -0.5,
    "late": -0.7,
    "slipped": -0.6,
    "chased": -0.55,
    "staggered": -0.2,
}

POSTMORTEM_LIQUIDITY_SCORES: Dict[str, float] = {
    "thick": 0.35,
    "deep": 0.4,
    "maker_friendly": 0.3,
    "stable": 0.2,
    "neutral": 0.0,
    "thin": -0.45,
    "fragile": -0.55,
    "one_sided": -0.4,
    "toxic": -0.65,
}


def _score_category(label: Any, table: Dict[str, float]) -> Optional[float]:
    if label is None:
        return None
    if isinstance(label, (int, float)):
        try:
            return max(min(float(label), 1.0), -1.0)
        except (TypeError, ValueError):
            return None
    token = str(label).strip().lower()
    if not token:
        return None
    normalized = re.sub(r"[^a-z0-9]+", "_", token)
    if normalized in table:
        return table[normalized]
    for key, value in table.items():
        if key in normalized:
            return value
    return None


class AITradeAdvisor:
    STAT_KEY_WHITELIST = {
        "atr_abs",
        "atr_pct",
        "expected_r",
        "funding",
        "htf_trend_down",
        "htf_trend_up",
        "last_price",
        "mid_price",
        "qv_score",
        "regime_adx",
        "regime_slope",
        "rsi",
        "spread_bps",
        "lob_imbalance_5",
        "lob_imbalance_10",
        "lob_depth_ratio",
        "lob_gap_score",
        "lob_wall_score",
        "orderbook_bias",
        "orderbook_levels",
        "trend",
        "wickiness",
    }
    STAT_PREFIX_WHITELIST = ("adx", "ema_", "slope_")
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
    CACHE_LIMIT = 64
    RECENT_PLAN_LIMIT = 160

    def __init__(
        self,
        api_key: str,
        model: str,
        budget: DailyBudgetTracker,
        state: Optional[Dict[str, Any]] = None,
        *,
        enabled: bool = True,
        wakeup_cb: Optional[Callable[[str], None]] = None,
        activity_logger: Optional[
            Callable[[str, str, Dict[str, Any], Optional[str]], None]
        ] = None,
        leverage_lookup: Optional[Callable[[str], float]] = None,
    ) -> None:
        self.api_key = (api_key or "").strip()
        self.model = (model or "gpt-4o").strip()
        self.budget = budget
        self.state = state if isinstance(state, dict) else {}
        self.enabled = bool(enabled and self.api_key)
        self._temperature_supported = True
        self._temperature_override = self._resolve_temperature()
        self._cache: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
        self._recent_plans: "OrderedDict[str, Tuple[float, Dict[str, Any], bool, float]]" = OrderedDict()
        self._pending_requests: Dict[str, Dict[str, Any]] = {}
        self._pending_order: deque[str] = deque()
        self._base_min_interval = max(0.0, AI_MIN_INTERVAL_SECONDS)
        self._min_interval = self._base_min_interval
        self._base_global_cooldown = max(0.0, AI_GLOBAL_COOLDOWN)
        self._last_global_interval = self._base_global_cooldown
        self._last_global_request = 0.0
        self._plan_timeout = AI_PLAN_TIMEOUT
        self._pending_limit = AI_PENDING_LIMIT
        self._plan_delivery_ttl = max(self._base_min_interval * 3.0, 90.0)
        self._ready_callback = wakeup_cb
        self._activity_logger = activity_logger
        self._leverage_lookup = leverage_lookup
        self._client = _shared_openai_client() if self.enabled else None
        self._load_persistent_state()
        state_bucket = self.state if self.state is not None else {}
        self.postmortem_learning = PostmortemLearning(state_bucket)
        self.parameter_tuner = ParameterTuner(
            state_bucket, request_fn=self._structured_request
        )
        self.playbook_manager = PlaybookManager(
            state_bucket,
            request_fn=self._structured_request,
            event_cb=self._handle_playbook_event,
        )
        self.budget_learner = BudgetLearner(state_bucket)
        self._playbook_request_meta: Dict[str, Dict[str, Any]] = {}

    def set_leverage_lookup(self, lookup: Optional[Callable[[str], float]]) -> None:
        self._leverage_lookup = lookup

    def _strategy_leverage_limit(self) -> Optional[float]:
        preset_value: Optional[str] = None
        leverage_limit: Optional[float] = None
        leverage_defined = False

        def _interpret_leverage(raw: Any) -> None:
            nonlocal leverage_limit, leverage_defined
            if leverage_defined:
                return
            if isinstance(raw, (int, float)):
                numeric = float(raw)
                if not math.isfinite(numeric) or numeric <= 0:
                    leverage_limit = None
                else:
                    leverage_limit = float(numeric)
                leverage_defined = True
                return
            if raw is None:
                return
            token = str(raw).strip()
            if not token:
                return
            lowered = token.lower()
            if lowered in {"max", "unlimited", "∞", "infinite", "inf"}:
                leverage_limit = None
                leverage_defined = True
                return
            try:
                numeric = float(token)
            except (TypeError, ValueError):
                return
            if not math.isfinite(numeric) or numeric <= 0:
                leverage_limit = None
            else:
                leverage_limit = float(numeric)
            leverage_defined = True

        state_bucket = self.state if isinstance(self.state, dict) else None
        if state_bucket:
            for key in ("preset_mode", "preset", "strategy_preset", "risk_preset"):
                raw = state_bucket.get(key)
                if isinstance(raw, str) and raw.strip():
                    preset_value = raw
                    break
            _interpret_leverage(state_bucket.get("ASTER_LEVERAGE"))
            if not leverage_defined:
                config_bucket = state_bucket.get("config")
                if isinstance(config_bucket, dict):
                    _interpret_leverage(config_bucket.get("ASTER_LEVERAGE"))
                    env_cfg = config_bucket.get("env")
                    if isinstance(env_cfg, dict):
                        raw = env_cfg.get("ASTER_PRESET_MODE")
                        if isinstance(raw, str) and raw.strip():
                            preset_value = preset_value or raw
                        _interpret_leverage(env_cfg.get("ASTER_LEVERAGE"))
            if not leverage_defined:
                env_cfg = state_bucket.get("env")
                if isinstance(env_cfg, dict):
                    raw = env_cfg.get("ASTER_PRESET_MODE")
                    if isinstance(raw, str) and raw.strip():
                        preset_value = preset_value or raw
                    _interpret_leverage(env_cfg.get("ASTER_LEVERAGE"))

        if not leverage_defined:
            _interpret_leverage(os.getenv("ASTER_LEVERAGE"))
        if not leverage_defined:
            _interpret_leverage(LEVERAGE_SOURCE)
        if leverage_defined:
            return leverage_limit

        if not preset_value:
            preset_value = os.getenv("ASTER_PRESET_MODE", PRESET_MODE)

        if not preset_value:
            return None

        preset = str(preset_value).strip().lower()
        if preset == "low":
            return 4.0
        if preset == "mid":
            return 10.0
        if preset in {"high", "att"}:
            return None
        return None

    def _resolve_leverage_cap(self, symbol: Optional[str]) -> Optional[float]:
        strategy_limit = self._strategy_leverage_limit()
        if not symbol or not self._leverage_lookup:
            return strategy_limit

        try:
            resolved = float(self._leverage_lookup(symbol))
        except Exception:
            resolved = float("nan")

        cap: Optional[float]
        if math.isfinite(resolved) and resolved > 0:
            cap = resolved
        else:
            cap = None

        if strategy_limit is not None and strategy_limit > 0:
            if cap is None:
                return float(strategy_limit)
            cap = min(cap, float(strategy_limit))

        if cap is None or cap <= 0:
            return None
        return cap

    def _clamp_leverage_value(
        self,
        symbol: str,
        value: float,
        fallback: Optional[float] = None,
    ) -> float:
        cap = self._resolve_leverage_cap(symbol)
        baseline = None
        if isinstance(fallback, (int, float)) and math.isfinite(float(fallback)):
            baseline = max(1.0, float(fallback))
        if cap is None and baseline is not None:
            cap = baseline
        numeric = max(1.0, float(value))
        if cap is not None and cap > 0:
            return clamp(numeric, 1.0, cap)
        default_limit = None
        if math.isfinite(LEVERAGE) and LEVERAGE > 0:
            default_limit = LEVERAGE
        elif baseline is not None:
            default_limit = baseline
        if default_limit is not None and default_limit > 0:
            return clamp(numeric, 1.0, default_limit)
        return numeric

    def _log_budget_block(self, kind: str, estimate: Optional[float] = None) -> None:
        if not self._activity_logger:
            return
        if self.budget.limit <= 0:
            return
        remaining = self.budget.remaining()
        if remaining is None:
            return
        min_required = max(0.0, float(estimate or 0.0))
        if remaining > 0 and (min_required <= 0 or remaining > min_required):
            return
        payload = {
            "ai_request": True,
            "request_kind": kind,
            "request_estimate": float(min_required),
            "budget_limit": float(self.budget.limit),
            "budget_spent": float(self.budget.spent()),
            "budget_remaining": float(remaining or 0.0),
            "strict": bool(self.budget.strict),
        }
        body = (
            "Daily AI request budget exhausted. Increase the limit or wait for the"
            " UTC reset."
        )
        self._activity_logger("alert", "AI budget exhausted", payload, body)

    def _new_request_id(self, kind: str, throttle_key: Optional[str] = None) -> str:
        prefix_bits: List[str] = []
        kind_part = re.sub(r"[^a-z0-9]+", "-", (kind or "").strip().lower())
        if kind_part:
            prefix_bits.append(kind_part[:16])
        if throttle_key:
            throttle_part = re.sub(r"[^a-z0-9]+", "-", throttle_key.strip().lower())
            if throttle_part:
                prefix_bits.append(throttle_part[-24:])
        prefix = "::".join(prefix_bits) if prefix_bits else "request"
        token = uuid.uuid4().hex[:12]
        return f"{prefix}:{token}"

    def _load_persistent_state(self) -> None:
        if not self.state:
            return
        cache_blob = self.state.get("ai_plan_cache")
        if isinstance(cache_blob, list):
            for entry in cache_blob:
                if not isinstance(entry, dict):
                    continue
                key = entry.get("key")
                plan = entry.get("plan") or entry.get("value")
                if not key or not isinstance(plan, dict):
                    continue
                self._cache[key] = copy.deepcopy(plan)
        while len(self._cache) > self.CACHE_LIMIT:
            self._cache.popitem(last=False)
        recent_blob = self.state.get("ai_recent_plans")
        if isinstance(recent_blob, list):
            for entry in recent_blob:
                if not isinstance(entry, dict):
                    continue
                key = entry.get("key")
                plan = entry.get("plan")
                ts = entry.get("ts")
                if not key or not isinstance(plan, dict):
                    continue
                try:
                    ts_val = float(ts)
                except Exception:
                    ts_val = time.time()
                delivered = bool(entry.get("delivered", False))
                interval_raw = entry.get("min_interval")
                try:
                    interval_val = float(interval_raw)
                except Exception:
                    interval_val = self._base_min_interval
                self._recent_plans[key] = (
                    ts_val,
                    copy.deepcopy(plan),
                    delivered,
                    float(interval_val),
                )
        while len(self._recent_plans) > self.RECENT_PLAN_LIMIT:
            self._recent_plans.popitem(last=False)

    def _persist_state(self) -> None:
        if not self.state:
            return
        cache_dump: List[Dict[str, Any]] = []
        for key, value in list(self._cache.items())[-self.CACHE_LIMIT:]:
            cache_dump.append({"key": key, "plan": copy.deepcopy(value)})
        recent_dump: List[Dict[str, Any]] = []
        for key, (ts, plan, delivered, interval) in list(self._recent_plans.items())[
            -self.RECENT_PLAN_LIMIT:
        ]:
            recent_dump.append(
                {
                    "key": key,
                    "ts": float(ts),
                    "plan": copy.deepcopy(plan),
                    "delivered": bool(delivered),
                    "min_interval": float(interval),
                }
            )
        self.state["ai_plan_cache"] = cache_dump
        self.state["ai_recent_plans"] = recent_dump

    def _sanitize_for_json(self, value: Any, depth: int = 0) -> Any:
        if depth >= 10:
            return str(value)
        if value is None:
            return None
        if isinstance(value, (bool, int)):
            return value
        if isinstance(value, float):
            return value if math.isfinite(value) else 0.0
        if isinstance(value, str):
            return value
        if isinstance(value, (datetime, date)):
            try:
                return value.isoformat()
            except Exception:
                return str(value)
        if isinstance(value, Decimal):
            try:
                return float(value)
            except Exception:
                return str(value)
        try:
            import numpy as np

            if isinstance(value, np.generic):
                return self._sanitize_for_json(value.item(), depth=depth + 1)
        except Exception:
            pass
        if isinstance(value, dict):
            sanitized: Dict[str, Any] = {}
            for key, sub in value.items():
                if isinstance(key, str):
                    key_str = key
                elif isinstance(key, (int, float, bool)):
                    key_str = str(key)
                else:
                    key_str = repr(key)
                sanitized[key_str] = self._sanitize_for_json(sub, depth + 1)
            return sanitized
        if isinstance(value, (list, tuple, set, deque)):
            return [self._sanitize_for_json(item, depth + 1) for item in list(value)]
        if hasattr(value, "_asdict") and callable(getattr(value, "_asdict")):
            try:
                return self._sanitize_for_json(value._asdict(), depth + 1)
            except Exception:
                return str(value)
        return str(value)

    def _structured_request(
        self, kind: str, payload: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        kind = str(kind or "").lower()
        if kind not in {"tuning", "playbook"}:
            return None
        playbook_snapshot_meta: Optional[Dict[str, Any]] = None
        if kind == "tuning":
            system_prompt = (
                "You tune risk parameters for an automated trading bot. Given the recent trade summaries, "
                "respond with JSON containing sl_atr_mult, tp_atr_mult, size_bias (object mapping bucket to multiplier), "
                "confidence (0-1) and optional note. Keep multipliers between 0.5 and 2.5."
            )
            estimate = 0.0012
        else:
            system_prompt = (
                "You act as the autonomous playbook strategist for an automated trading bot. Analyse the telemetry snapshot "
                "and respond with JSON describing the updated playbook. Return the fields: request_id (echo the provided value), "
                "mode, bias, confidence (0-1), size_bias (BUY/SELL multipliers between 0.4 and 2.5), sl_bias (0.4-2.5), tp_bias "
                "(0.6-3.0), features (object mapping focus keywords to numeric weights between -1 and 1), strategy (object with "
                "name, objective, why_active, market_signals array, actions array of objects with title/detail and optional "
                "trigger, and risk_controls array), plus optional notes. Respond with valid JSON only."
            )
            estimate = 0.0018
        try:
            user_payload = payload or {}
        except Exception:
            return None
        if not isinstance(user_payload, dict):
            user_payload = {"payload": payload}
        request_id = self._new_request_id(kind, kind)
        payload_with_id = dict(user_payload)
        payload_with_id["request_id"] = request_id
        if kind == "playbook":
            playbook_snapshot_meta = self._summarize_playbook_snapshot(user_payload)
            self._note_playbook_request(request_id, playbook_snapshot_meta)
        try:
            sanitized_payload = self._sanitize_for_json(payload_with_id)
            user_prompt = json.dumps(
                sanitized_payload,
                sort_keys=True,
                separators=(",", ":"),
            )
        except Exception as exc:
            log.debug("AI request payload serialization failed (%s): %s", kind, exc)
            if kind == "playbook":
                self._note_playbook_failure(
                    request_id,
                    "serialization_error",
                    playbook_snapshot_meta,
                )
            return None
        meta: Dict[str, Any] = {"request_id": request_id}
        symbol_hint = user_payload.get("symbol") if isinstance(user_payload, dict) else None
        if symbol_hint:
            meta["symbol"] = symbol_hint
        if kind == "playbook" and playbook_snapshot_meta:
            meta["snapshot_meta"] = playbook_snapshot_meta
        if kind == "tuning":
            try:
                self._note_tuning_request(request_id, payload_with_id)
            except Exception:
                pass
        response = self._chat(
            system_prompt,
            user_prompt,
            kind=kind,
            budget_estimate=estimate,
            request_meta=meta or None,
        )
        if not response:
            if kind == "playbook":
                self._note_playbook_failure(
                    request_id,
                    "no_response",
                    playbook_snapshot_meta,
                )
            return None
        parsed = self._parse_structured(response)
        if isinstance(parsed, dict):
            parsed.setdefault("request_id", request_id)
            if kind == "tuning":
                try:
                    self._note_tuning_response(parsed)
                except Exception:
                    pass
            return parsed
        if kind == "playbook":
            self._note_playbook_failure(
                request_id,
                "invalid_response",
                playbook_snapshot_meta,
            )
        return None

    def inject_context_features(self, symbol: str, ctx: Dict[str, Any]) -> None:
        if not isinstance(ctx, dict):
            return
        try:
            if self.postmortem_learning:
                pm_features = self.postmortem_learning.context_features(symbol or "*")
                for key, value in pm_features.items():
                    ctx[key] = float(value)
        except Exception:
            pass
        try:
            if self.parameter_tuner:
                self.parameter_tuner.inject_context(ctx)
        except Exception:
            pass
        try:
            if self.playbook_manager:
                active = self.playbook_manager.active()
                features = active.get("features", {}) if isinstance(active, dict) else {}
                ctx["playbook_mode"] = active.get("mode", "baseline") if isinstance(active, dict) else "baseline"
                ctx["playbook_bias"] = active.get("bias", "neutral") if isinstance(active, dict) else "neutral"
                ctx["playbook_breakout_bias"] = float((features or {}).get("playbook_breakout_bias", 0.0))
                ctx["playbook_range_bias"] = float((features or {}).get("playbook_range_bias", 0.0))
                ctx["playbook_trend_bias"] = float((features or {}).get("playbook_trend_bias", 0.0))
        except Exception:
            pass
        try:
            if self.budget_learner:
                ctx["budget_bias"] = float(
                    self.budget_learner.context_bias(symbol or "*")
                )
                snapshot = self.budget_learner.context_snapshot(symbol or "*")
                for key, value in snapshot.items():
                    if isinstance(value, (int, float)):
                        ctx[f"budget_{key}"] = float(value)
                    elif isinstance(value, str):
                        ctx[f"budget_{key}"] = value
        except Exception:
            pass
        cap = self._resolve_leverage_cap(symbol)
        if cap is not None:
            ctx["max_leverage"] = float(cap)

    def maybe_refresh_playbook(self, snapshot: Dict[str, Any]) -> None:
        try:
            if self.playbook_manager:
                self.playbook_manager.maybe_refresh(snapshot)
        except Exception:
            pass

    def _summarize_playbook_snapshot(
        self, snapshot: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        meta: Dict[str, Any] = {}
        if isinstance(snapshot, dict):
            technical = snapshot.get("technical")
            if isinstance(technical, dict):
                meta["technical"] = len(technical)
            sentinel = snapshot.get("sentinel")
            if isinstance(sentinel, dict):
                meta["sentinel"] = len(sentinel)
            trades = snapshot.get("recent_trades")
            if isinstance(trades, list):
                meta["recent_trades"] = len(trades)
            budget = snapshot.get("budget")
            if isinstance(budget, dict):
                for key in ("remaining", "limit", "spent"):
                    value = budget.get(key)
                    try:
                        if value is not None:
                            meta[f"budget_{key}"] = float(value)
                    except (TypeError, ValueError):
                        continue
            timestamp = snapshot.get("timestamp")
            if isinstance(timestamp, (int, float)):
                meta["timestamp"] = float(timestamp)
        return meta

    @staticmethod
    def _format_snapshot_meta(meta: Optional[Dict[str, Any]]) -> str:
        if not meta:
            return "No snapshot data captured yet"
        parts: List[str] = []
        if "technical" in meta:
            parts.append(f"tech={int(meta['technical'])}")
        if "sentinel" in meta:
            parts.append(f"sentinel={int(meta['sentinel'])}")
        if "recent_trades" in meta:
            parts.append(f"trades={int(meta['recent_trades'])}")
        if (
            "budget_remaining" in meta
            or "budget_limit" in meta
            or "budget_spent" in meta
        ):
            limit = meta.get("budget_limit")
            spent = meta.get("budget_spent")
            remaining = meta.get("budget_remaining")
            budget_bits: List[str] = []
            if spent is not None and limit is not None:
                budget_bits.append(f"spent={spent:.2f}/{limit:.2f}")
            if remaining is not None:
                if limit is not None and spent is None:
                    budget_bits.append(f"remaining={remaining:.2f}/{limit:.2f}")
                else:
                    budget_bits.append(f"remaining={remaining:.2f}")
            if not budget_bits and limit is not None:
                budget_bits.append(f"limit={limit:.2f}")
            if budget_bits:
                parts.append("budget " + " · ".join(budget_bits))
        if not parts:
            return "Snapshot collected but empty"
        return " · ".join(parts)

    def _note_playbook_request(
        self, request_id: str, snapshot_meta: Optional[Dict[str, Any]]
    ) -> None:
        summary = self._format_snapshot_meta(snapshot_meta)
        log.info(
            "Playbook AI request queued (request_id=%s): %s",
            request_id,
            summary,
        )
        data: Dict[str, Any] = {
            "ai_request": True,
            "request_id": request_id,
            "request_kind": "playbook",
        }
        if snapshot_meta:
            data["snapshot_meta"] = snapshot_meta
        self._log_ai_activity(
            "query",
            "Playbook refresh requested",
            body=summary,
            data=data,
            force=True,
        )
        if request_id:
            self._playbook_request_meta[request_id] = snapshot_meta or {}

    def _summarize_tuning_overrides(
        self, overrides: Optional[Dict[str, Any]]
    ) -> Tuple[str, Dict[str, float]]:
        if not isinstance(overrides, dict):
            return "", {}
        sl = self._coerce_float(overrides.get("sl_atr_mult"))
        if sl is None:
            sl = self._coerce_float(overrides.get("sl_bias"))
        tp = self._coerce_float(overrides.get("tp_atr_mult"))
        if tp is None:
            tp = self._coerce_float(overrides.get("tp_bias"))
        size_bias_raw = overrides.get("size_bias")
        size_bias: Dict[str, float] = {}
        if isinstance(size_bias_raw, dict):
            for key, value in size_bias_raw.items():
                label = str(key or "").strip().upper()
                if not label:
                    continue
                numeric = self._coerce_float(value)
                if numeric is None:
                    continue
                size_bias[label] = numeric
        parts: List[str] = []
        if sl is not None:
            parts.append(f"SL×{sl:.2f}")
        if tp is not None:
            parts.append(f"TP×{tp:.2f}")
        if size_bias:
            priority = ("BUY", "SELL", "LONG", "SHORT", "S", "M", "L")
            ordered: List[str] = []
            seen: Set[str] = set()
            for token in priority:
                if token in size_bias and token not in seen:
                    ordered.append(f"{token} {size_bias[token]:.2f}")
                    seen.add(token)
            for token in sorted(size_bias.keys()):
                if token not in seen:
                    ordered.append(f"{token} {size_bias[token]:.2f}")
            if ordered:
                parts.append("size " + " / ".join(ordered))
        summary = " · ".join(parts)
        return summary, size_bias

    def _note_tuning_request(self, request_id: str, payload: Dict[str, Any]) -> None:
        trades = payload.get("trades")
        trade_count = len(trades) if isinstance(trades, list) else 0
        overrides = payload.get("overrides")
        if not overrides:
            context = payload.get("context")
            if isinstance(context, dict):
                overrides = context.get("current_overrides")
        summary, _ = self._summarize_tuning_overrides(overrides)
        parts: List[str] = []
        if trade_count:
            parts.append(f"{trade_count} trades")
        if summary:
            parts.append(summary)
        latest_note = None
        context = payload.get("context") if isinstance(payload.get("context"), dict) else None
        if context:
            note_text = context.get("latest_note")
            if isinstance(note_text, str) and note_text.strip():
                latest_note = note_text.strip()
        body_lines: List[str] = []
        if parts:
            body_lines.append(" · ".join(parts))
        if latest_note:
            body_lines.append(f"Recent note: {latest_note}")
        body = "\n".join(body_lines) if body_lines else "No context provided"
        data = {
            "ai_request": True,
            "request_id": request_id,
            "request_kind": "tuning",
        }
        self._log_ai_activity(
            "query",
            "Parameter tuning requested",
            body=body,
            data=data,
            force=True,
        )

    def _note_tuning_response(self, overrides: Dict[str, Any]) -> None:
        if not isinstance(overrides, dict):
            return
        request_id = overrides.get("request_id")
        if isinstance(request_id, str):
            request_id = request_id.strip() or None
        else:
            request_id = str(request_id) if request_id is not None else None
        summary, size_bias = self._summarize_tuning_overrides(overrides)
        confidence = self._coerce_float(
            overrides.get("confidence") or overrides.get("confidence_score")
        )
        note_text = overrides.get("note") or overrides.get("notes")
        if isinstance(note_text, str):
            note_text = note_text.strip() or None
        else:
            note_text = None
        parts: List[str] = []
        if summary:
            parts.append(summary)
        if confidence is not None:
            parts.append(f"confidence {confidence:.2f}")
        body = " · ".join(parts)
        if note_text:
            body = f"{body}\nNote: {note_text}" if body else f"Note: {note_text}"
        data: Dict[str, Any] = {
            "ai_request": True,
            "request_kind": "tuning",
            "size_bias": size_bias,
        }
        sl = self._coerce_float(overrides.get("sl_atr_mult") or overrides.get("sl_bias"))
        tp = self._coerce_float(overrides.get("tp_atr_mult") or overrides.get("tp_bias"))
        if sl is not None:
            data["sl_atr_mult"] = sl
        if tp is not None:
            data["tp_atr_mult"] = tp
        if confidence is not None:
            data["confidence"] = confidence
        if note_text:
            data["notes"] = note_text
        if request_id:
            data["request_id"] = request_id
        self._log_ai_activity(
            "tuning",
            "Parameter tuning update",
            body=body or "No overrides returned",
            data=data,
            force=True,
        )

    def _note_playbook_failure(
        self,
        request_id: str,
        reason: str,
        snapshot_meta: Optional[Dict[str, Any]],
    ) -> None:
        summary = self._format_snapshot_meta(snapshot_meta)
        log.warning(
            "Playbook AI request %s failed: %s",
            request_id or "<unknown>",
            reason,
        )
        body = f"Reason: {reason}"
        if summary:
            body = f"{body}\nSnapshot: {summary}"
        data: Dict[str, Any] = {
            "ai_request": True,
            "request_id": request_id,
            "request_kind": "playbook",
            "reason": reason,
        }
        if snapshot_meta:
            data["snapshot_meta"] = snapshot_meta
        self._log_ai_activity(
            "error",
            "Playbook refresh failed",
            body=body,
            data=data,
            force=True,
        )
        if request_id:
            self._playbook_request_meta.pop(request_id, None)

    def _summarize_playbook_active(
        self, playbook: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        mode = str(playbook.get("mode") or "baseline")
        bias = str(playbook.get("bias") or "neutral")
        size_bias_raw = playbook.get("size_bias") or {}
        if not isinstance(size_bias_raw, dict):
            size_bias_raw = {}
        try:
            size_buy = float(size_bias_raw.get("BUY", 1.0) or 1.0)
        except (TypeError, ValueError):
            size_buy = 1.0
        try:
            size_sell = float(size_bias_raw.get("SELL", 1.0) or 1.0)
        except (TypeError, ValueError):
            size_sell = 1.0
        try:
            sl_bias = float(playbook.get("sl_bias", 1.0) or 1.0)
        except (TypeError, ValueError):
            sl_bias = 1.0
        try:
            tp_bias = float(playbook.get("tp_bias", 1.0) or 1.0)
        except (TypeError, ValueError):
            tp_bias = 1.0
        features_raw = playbook.get("features")
        features: Dict[str, float] = {}
        if isinstance(features_raw, dict):
            for key, value in features_raw.items():
                try:
                    features[str(key)] = float(value)
                except (TypeError, ValueError):
                    continue
        top_features = sorted(
            features.items(), key=lambda item: abs(item[1]), reverse=True
        )[:3]
        focus_parts = [
            f"{key}={value:+.2f}" for key, value in top_features if abs(value) >= 0.05
        ]
        summary = (
            f"{mode} mode ({bias}) · size BUY {size_buy:.2f} / SELL {size_sell:.2f}"
            f" · SL×{sl_bias:.2f} · TP×{tp_bias:.2f}"
        )
        if focus_parts:
            summary += "\nFocus: " + ", ".join(focus_parts)
        notes = playbook.get("notes") or playbook.get("note")
        data: Dict[str, Any] = {
            "ai_request": True,
            "mode": mode,
            "bias": bias,
            "size_bias": {"BUY": size_buy, "SELL": size_sell},
            "sl_bias": sl_bias,
            "tp_bias": tp_bias,
            "request_kind": "playbook",
        }
        if features:
            data["features"] = {
                key: value for key, value in top_features
            }
        if isinstance(notes, str) and notes.strip():
            data["notes"] = notes.strip()
        return summary, data

    def _handle_playbook_event(
        self,
        event: str,
        payload: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        if event != "applied" or not isinstance(payload, dict):
            return
        summary, activity_data = self._summarize_playbook_active(payload)
        request_id: Optional[str] = None
        raw_request_id = payload.get("request_id")
        if isinstance(raw_request_id, str):
            request_id = raw_request_id.strip() or None
        if not request_id and context:
            raw = context.get("raw") if isinstance(context, dict) else None
            if isinstance(raw, dict):
                rid = raw.get("request_id")
                if isinstance(rid, str):
                    request_id = rid.strip() or None
        if request_id:
            activity_data["request_id"] = request_id
        stored_meta = self._playbook_request_meta.pop(request_id, None) if request_id else None
        snapshot_meta = stored_meta
        if not snapshot_meta and context and isinstance(context, dict):
            snap = context.get("snapshot")
            if isinstance(snap, dict):
                snapshot_meta = self._summarize_playbook_snapshot(snap)
        if snapshot_meta:
            activity_data["snapshot_meta"] = snapshot_meta
        notes = payload.get("notes") or payload.get("note")
        body = summary
        if isinstance(notes, str) and notes.strip():
            note_text = notes.strip()
            body = f"{summary}\nNote: {note_text}"
            activity_data["notes"] = note_text
        log.info(
            "Playbook updated%s: %s",
            f" (request_id={request_id})" if request_id else "",
            summary,
        )
        self._log_ai_activity(
            "playbook",
            f"Playbook updated: {payload.get('mode', 'baseline')}",
            body=body,
            data=activity_data,
            force=True,
        )

    def _prune_pending_queue(self) -> None:
        if not self._pending_order:
            return
        stale: List[str] = []
        for key in list(self._pending_order):
            info = self._pending_requests.get(key)
            if not info:
                stale.append(key)
                continue
            future = info.get("future")
            if isinstance(future, Future) and future.done():
                stale.append(key)
                continue
            if info.get("cancelled"):
                stale.append(key)
        for key in stale:
            self._pending_requests.pop(key, None)
            try:
                self._pending_order.remove(key)
            except ValueError:
                pass

    def _has_pending_capacity(self, key: str) -> bool:
        self._prune_pending_queue()
        info = self._pending_requests.get(key)
        if info:
            future = info.get("future")
            if isinstance(future, Future) and not future.done():
                return False
            if future is None and not info.get("cancelled"):
                # Request is queued but not yet dispatched – wait for it to settle
                return False
        if self._pending_limit <= 0:
            return True
        return len(self._pending_requests) < self._pending_limit

    def _register_pending_key(self, key: str) -> None:
        if key in self._pending_order:
            return
        self._prune_pending_queue()
        self._pending_order.append(key)

    def _remove_pending_entry(self, key: str) -> None:
        self._pending_requests.pop(key, None)
        try:
            self._pending_order.remove(key)
        except ValueError:
            pass

    def _active_pending(self) -> int:
        count = 0
        for info in self._pending_requests.values():
            fut = info.get("future")
            if isinstance(fut, Future) and not fut.done():
                count += 1
        return count

    def _pending_stub(
        self,
        fallback: Dict[str, Any],
        reason: str,
        note: str,
        *,
        throttle_key: Optional[str] = None,
        pending: bool = True,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        plan = {**fallback}
        plan["take"] = False
        plan["decision"] = "skip"
        plan["decision_reason"] = reason
        plan["decision_note"] = note
        plan.setdefault("explanation", "")
        if pending:
            plan["_pending"] = True
        else:
            plan.pop("_pending", None)
        if throttle_key:
            plan["_pending_key"] = throttle_key
        if not request_id:
            request_id = plan.get("request_id") or fallback.get("request_id")
        if not request_id:
            token = uuid.uuid4().hex[:12]
            prefix = str(throttle_key or "pending")
            request_id = f"{prefix}:{token}"
        plan["request_id"] = request_id
        fallback["request_id"] = request_id
        return plan

    def _mark_pending_notified(self, throttle_key: str) -> bool:
        info = self._pending_requests.get(throttle_key)
        if not info:
            return False
        if info.get("notified"):
            return False
        info["notified"] = True
        return True

    def should_log_pending(self, plan: Optional[Dict[str, Any]]) -> bool:
        if not isinstance(plan, dict):
            return True
        throttle_key = plan.get("_pending_key")
        if not isinstance(throttle_key, str) or not throttle_key:
            return True
        return self._mark_pending_notified(throttle_key)

    def _estimate_tokens(self, text: str) -> float:
        if not text:
            return 0.0
        # crude heuristic: average 4 characters per token
        return max(1.0, len(text) / 4.0)

    def _estimate_prospective_cost(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        completion_hint: float = 320.0,
    ) -> float:
        pricing = self._pricing()
        prompt_tokens = self._estimate_tokens(system_prompt) + self._estimate_tokens(user_prompt)
        return (
            prompt_tokens * pricing.get("input", 0.0)
            + completion_hint * pricing.get("output", 0.0)
        )

    def _dispatch_request(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        kind: str,
        budget_estimate: float,
        request_meta: Optional[Dict[str, Any]] = None,
    ) -> Optional[Future]:
        return self._submit_chat_request(
            system_prompt,
            user_prompt,
            kind=kind,
            budget_estimate=budget_estimate,
            request_meta=request_meta,
        )

    def _notify_ready(self, throttle_key: str) -> None:
        if not self._ready_callback:
            return
        try:
            self._ready_callback(throttle_key)
        except Exception as exc:
            log.debug(f"ready callback failed for {throttle_key}: {exc}")

    def _attach_future_callback(self, throttle_key: str, future: Optional[Future]) -> None:
        if not isinstance(future, Future):
            return
        try:
            future.add_done_callback(lambda _fut, key=throttle_key: self._notify_ready(key))
        except Exception as exc:
            log.debug(f"future callback attach failed for {throttle_key}: {exc}")

    def _process_pending_request(
        self,
        throttle_key: str,
        fallback: Dict[str, Any],
        now: float,
        min_interval: Optional[float] = None,
        global_cooldown: Optional[float] = None,
    ) -> Tuple[Optional[str], Optional[Any]]:
        info = self._pending_requests.get(throttle_key)
        if not info:
            return None, None
        if not isinstance(fallback, dict):
            log.debug(
                "pending request %s provided non-dict fallback (%s); coercing to empty plan",
                throttle_key,
                type(fallback).__name__,
            )
            fallback = {}
        if min_interval is not None:
            try:
                info["min_interval"] = max(0.0, float(min_interval))
            except Exception:
                pass
        guard_interval = info.get("global_cooldown")
        if global_cooldown is not None:
            try:
                guard_interval = max(0.0, float(global_cooldown))
            except Exception:
                guard_interval = guard_interval
        if guard_interval is None:
            guard_interval = self._base_global_cooldown
        try:
            guard_interval = max(0.0, float(guard_interval))
        except Exception:
            guard_interval = self._base_global_cooldown
        if global_cooldown is not None:
            info["global_cooldown"] = guard_interval
        kind = str(info.get("kind", "plan"))
        note = info.get("note") or "Waiting for AI plan response"
        future = info.get("future")
        if future is None:
            if not self.enabled or not self._client:
                self._remove_pending_entry(throttle_key)
                disabled_plan = self._pending_stub(
                    fallback,
                    f"{kind}_disabled",
                    "AI planning disabled; using fallback heuristics.",
                    throttle_key=throttle_key,
                    pending=False,
                    request_id=info.get("request_id"),
                )
                disabled_plan["take"] = bool(fallback.get("take", True))
                disabled_plan["decision"] = "take" if disabled_plan["take"] else "skip"
                return "fallback", disabled_plan
            ready_after = float(info.get("ready_after", now) or now)
            if ready_after <= now and self._client:
                cooldown_ok = guard_interval <= 0 or (now - self._last_global_request) >= guard_interval
                concurrency_ok = self._active_pending() < AI_CONCURRENCY
                if cooldown_ok and concurrency_ok:
                    future = self._dispatch_request(
                        info.get("system_prompt", ""),
                        info.get("user_prompt", ""),
                        kind=kind,
                        budget_estimate=float(info.get("estimate", 0.0) or 0.0),
                        request_meta=info.get("request_meta"),
                    )
                    if future:
                        info["future"] = future
                        info["dispatched_at"] = now
                        self._last_global_request = now
                        self._last_global_interval = guard_interval
                        note = "Waiting for AI plan response"
                        self._attach_future_callback(throttle_key, future)
                    else:
                        self._remove_pending_entry(throttle_key)
                        self._recent_plan_store(
                            throttle_key,
                            fallback,
                            now,
                            min_interval=info.get("min_interval"),
                        )
                        return "fallback", fallback
                else:
                    info["ready_after"] = now + max(0.5, guard_interval or 0.5)
            stub = self._pending_stub(
                fallback,
                f"{kind}_pending",
                note,
                throttle_key=throttle_key,
                request_id=info.get("request_id"),
            )
            if stub.get("request_id") and not info.get("request_id"):
                info["request_id"] = stub["request_id"]
            return "pending", stub
        if isinstance(future, Future) and future.done():
            self._remove_pending_entry(throttle_key)
            try:
                response = future.result()
            except Exception as exc:
                log.debug(f"AI future exception for %s: %s", throttle_key, exc)
                response = None
            return "response", {"response": response, "info": info}
        dispatched_at = float(info.get("dispatched_at", now) or now)
        if (now - dispatched_at) > self._plan_timeout:
            try:
                if isinstance(future, Future):
                    future.cancel()
            finally:
                self._remove_pending_entry(throttle_key)
            timeout_plan = self._pending_stub(
                fallback,
                f"{kind}_timeout",
                "AI request timed out; using fallback heuristics.",
                throttle_key=throttle_key,
                pending=False,
                request_id=info.get("request_id"),
            )
            timeout_plan["take"] = bool(fallback.get("take", True))
            timeout_plan["decision"] = "take" if timeout_plan["take"] else "skip"
            timeout_plan["ai_fallback"] = True
            self._recent_plan_store(
                throttle_key,
                fallback,
                now,
                min_interval=info.get("min_interval"),
            )
            return "timeout", timeout_plan
        stub = self._pending_stub(
            fallback,
            f"{kind}_pending",
            note,
            throttle_key=throttle_key,
            request_id=info.get("request_id"),
        )
        if stub.get("request_id") and not info.get("request_id"):
            info["request_id"] = stub["request_id"]
        return "pending", stub

    def _finalize_response(
        self,
        throttle_key: str,
        fallback: Dict[str, Any],
        info: Optional[Dict[str, Any]],
        response_text: Optional[str],
        now: Optional[float] = None,
    ) -> Dict[str, Any]:
        now = now if now is not None else time.time()
        meta = info or {}
        cache_key_ready = meta.get("cache_key") if isinstance(meta, dict) else None
        request_id: Optional[str] = None
        if isinstance(meta, dict):
            raw_id = meta.get("request_id")
            if isinstance(raw_id, str):
                request_id = raw_id.strip() or None
            elif raw_id is not None:
                request_id = str(raw_id)
        if not request_id and isinstance(fallback, dict):
            fallback_id = fallback.get("request_id")
            if isinstance(fallback_id, str):
                request_id = fallback_id.strip() or None
            elif fallback_id is not None:
                request_id = str(fallback_id)
        if request_id and isinstance(fallback, dict):
            fallback.setdefault("request_id", request_id)
        min_interval = None
        if isinstance(meta, dict):
            meta_interval = meta.get("min_interval")
            if meta_interval is not None:
                try:
                    min_interval = max(0.0, float(meta_interval))
                except Exception:
                    min_interval = None
        if not response_text:
            self._recent_plan_store(
                throttle_key,
                fallback,
                now,
                min_interval=min_interval,
            )
            return fallback
        parsed = self._parse_structured(response_text)
        if not isinstance(parsed, dict):
            self._recent_plan_store(
                throttle_key,
                fallback,
                now,
                min_interval=min_interval,
            )
            return fallback
        request_payload: Optional[Dict[str, Any]] = None
        if isinstance(meta, dict):
            payload_raw = meta.get("user_payload")
            if isinstance(payload_raw, dict):
                request_payload = payload_raw
            elif isinstance(payload_raw, str):
                try:
                    request_payload = json.loads(payload_raw)
                except Exception:
                    request_payload = None
            if request_payload is None:
                prompt_raw = meta.get("user_prompt")
                if isinstance(prompt_raw, str):
                    try:
                        request_payload = json.loads(prompt_raw)
                    except Exception:
                        request_payload = None

        kind = str(meta.get("kind", "plan")) if isinstance(meta, dict) else "plan"
        request_id = None
        if isinstance(meta, dict):
            raw_id = meta.get("request_id")
            if isinstance(raw_id, str):
                request_id = raw_id.strip() or None
            elif raw_id is not None:
                request_id = str(raw_id)
        if not request_id and isinstance(request_payload, dict):
            payload_id = request_payload.get("request_id")
            if isinstance(payload_id, str):
                request_id = payload_id.strip() or None
            elif payload_id is not None:
                request_id = str(payload_id)

        if kind == "trend":
            plan_ready = self._apply_trend_plan_overrides(
                fallback,
                parsed,
                request_payload=request_payload,
            )
        else:
            plan_ready = self._apply_plan_overrides(
                fallback,
                parsed,
                request_payload=request_payload,
            )
        if isinstance(plan_ready, dict) and request_id:
            plan_ready.setdefault("request_id", request_id)
        if cache_key_ready:
            self._cache_store(str(cache_key_ready), plan_ready)
        self._recent_plan_store(
            throttle_key,
            plan_ready,
            now,
            delivered=False,
            min_interval=min_interval,
        )
        return plan_ready

    def flush_pending(self) -> List[Tuple[str, Dict[str, Any]]]:
        ready: List[Tuple[str, Dict[str, Any]]] = []
        if not self._pending_requests:
            return ready
        now = time.time()
        keys = list(self._pending_order) if self._pending_order else list(self._pending_requests.keys())
        for throttle_key in keys:
            info = self._pending_requests.get(throttle_key)
            if not info:
                continue
            fallback = info.get("fallback")
            if not isinstance(fallback, dict):
                log.debug(
                    "pending request %s missing fallback payload; using empty defaults",
                    throttle_key,
                )
                fallback = {}
            status, payload = self._process_pending_request(
                throttle_key,
                fallback,
                now,
                min_interval=info.get("min_interval") if isinstance(info, dict) else None,
                global_cooldown=info.get("global_cooldown") if isinstance(info, dict) else None,
            )
            if status != "response":
                continue
            bundle = payload or {}
            response_text = bundle.get("response") if isinstance(bundle, dict) else None
            meta = bundle.get("info") if isinstance(bundle, dict) else info
            plan_ready = self._finalize_response(throttle_key, fallback, meta, response_text, now)
            if isinstance(plan_ready, dict):
                ready.append((throttle_key, plan_ready))
        return ready

    def _normalize_symbol(self, symbol: Any) -> str:
        return str(symbol or "").strip().upper()

    def _normalize_side(self, side: Any) -> str:
        token = str(side or "").strip().upper()
        return token or "UNKNOWN"

    def _coerce_float(self, value: Any) -> Optional[float]:
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return None
        return None

    def _extract_stat_block(self, ctx: Dict[str, Any]) -> Dict[str, float]:
        stats: Dict[str, float] = {}
        if not isinstance(ctx, dict):
            return stats
        for key, raw in ctx.items():
            if key in self.STAT_KEY_WHITELIST or any(key.startswith(prefix) for prefix in self.STAT_PREFIX_WHITELIST):
                num = self._coerce_float(raw)
                if num is not None and math.isfinite(num):
                    stats[key] = num
        return stats

    def _summarize_sentinel(self, sentinel: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(sentinel, dict):
            return {}
        summary: Dict[str, Any] = {}
        label = sentinel.get("label")
        if isinstance(label, str) and label:
            summary["label"] = label
        event_risk = self._coerce_float(sentinel.get("event_risk"))
        if event_risk is not None and math.isfinite(event_risk):
            summary["event_risk"] = event_risk
        hype_score = self._coerce_float(sentinel.get("hype_score"))
        if hype_score is not None and math.isfinite(hype_score):
            summary["hype_score"] = hype_score
        signals = sentinel.get("signals")
        if isinstance(signals, dict):
            for key in (
                "sentinel_onchain_pressure",
                "sentinel_social_sentiment",
                "sentinel_options_skew",
            ):
                value = self._coerce_float(signals.get(key))
                if value is not None and math.isfinite(value):
                    summary[key] = value
        return summary

    def _pricing(self) -> Dict[str, float]:
        return self.MODEL_PRICING.get(self.model, self.MODEL_PRICING["default"])

    def _estimate_cost(self, usage: Optional[Dict[str, Any]]) -> Optional[float]:
        if not usage:
            return None
        pricing = self._pricing()
        try:
            prompt_tokens = float(usage.get("prompt_tokens", 0) or 0)
            completion_tokens = float(usage.get("completion_tokens", 0) or 0)
        except Exception:
            return None
        return (
            prompt_tokens * pricing.get("input", 0.0)
            + completion_tokens * pricing.get("output", 0.0)
        )

    def _resolve_temperature(self) -> Optional[float]:
        raw = os.getenv("ASTER_AI_TEMPERATURE")
        if raw is None or not raw.strip():
            return 0.3
        raw = raw.strip()
        try:
            value = float(raw)
        except ValueError:
            log.debug("Invalid ASTER_AI_TEMPERATURE=%s — using default 0.3", raw)
            return 0.3
        if abs(value - 1.0) <= 1e-6:
            return None
        return value

    def _normalize_payload(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {k: self._normalize_payload(value[k]) for k in sorted(value)}
        if isinstance(value, (list, tuple)):
            return [self._normalize_payload(v) for v in value]
        if isinstance(value, float):
            if not math.isfinite(value):
                return 0.0
            return round(value, 6)
        if isinstance(value, (int, bool)):
            return value
        return value

    def _cache_key(self, kind: str, system_prompt: str, payload: Dict[str, Any]) -> str:
        normalized = {
            "kind": kind,
            "system": system_prompt,
            "payload": self._normalize_payload(payload),
        }
        serial = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
        return hashlib.sha1(serial.encode("utf-8")).hexdigest()

    def _cache_lookup(self, key: str) -> Optional[Dict[str, Any]]:
        if key not in self._cache:
            return None
        self._cache.move_to_end(key)
        return copy.deepcopy(self._cache[key])

    def _cache_store(self, key: str, value: Dict[str, Any]) -> None:
        clean_value = copy.deepcopy(value)
        if isinstance(clean_value, dict):
            clean_value.pop("request_id", None)
        self._cache[key] = clean_value
        self._cache.move_to_end(key)
        while len(self._cache) > self.CACHE_LIMIT:
            self._cache.popitem(last=False)
        self._persist_state()

    def _recent_plan_lookup(
        self,
        key: str,
        now: Optional[float] = None,
        min_interval: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        if key not in self._recent_plans:
            return None
        if now is None:
            now = time.time()
        ts, plan, delivered, stored_interval = self._recent_plans[key]
        age = now - ts
        interval = self._base_min_interval
        if min_interval is not None:
            try:
                interval = float(min_interval)
            except Exception:
                interval = self._base_min_interval
        elif stored_interval is not None:
            try:
                interval = float(stored_interval)
            except Exception:
                interval = self._base_min_interval
        plan_ttl = self._plan_delivery_ttl
        if interval > 0:
            plan_ttl = max(self._plan_delivery_ttl, interval * 3.0)
        if age > plan_ttl:
            self._recent_plans.pop(key, None)
            return None
        if delivered and interval > 0 and age > interval:
            return None
        self._recent_plans.move_to_end(key)
        new_delivered = delivered
        if not delivered:
            new_delivered = True
        if min_interval is not None and min_interval >= 0:
            interval = float(interval)
        self._recent_plans[key] = (ts, plan, new_delivered, interval)
        try:
            self._persist_state()
        except Exception:
            pass
        return copy.deepcopy(plan)

    def _recent_plan_store(
        self,
        key: str,
        plan: Dict[str, Any],
        now: Optional[float] = None,
        *,
        delivered: bool = True,
        min_interval: Optional[float] = None,
    ) -> None:
        if now is None:
            now = time.time()
        plan_copy = copy.deepcopy(plan)
        if isinstance(plan_copy, dict):
            plan_copy.pop("request_id", None)
        interval = self._base_min_interval
        if min_interval is not None:
            try:
                interval = max(0.0, float(min_interval))
            except Exception:
                interval = self._base_min_interval
        self._recent_plans[key] = (now, plan_copy, bool(delivered), float(interval))
        self._recent_plans.move_to_end(key)
        while len(self._recent_plans) > self.RECENT_PLAN_LIMIT:
            self._recent_plans.popitem(last=False)
        self._persist_state()

    def consume_recent_plan(self, key: str) -> Optional[Dict[str, Any]]:
        if not key:
            return None
        bundle = self._recent_plans.pop(key, None)
        if not bundle:
            return None
        try:
            self._persist_state()
        except Exception:
            # Persistence issues should not block delivering the plan.
            pass
        _, plan, _, _ = bundle
        return copy.deepcopy(plan)

    def consume_signal_plan(self, symbol: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        if not symbol:
            return None
        symbol_key = self._normalize_symbol(symbol)
        prefix = f"plan::{symbol_key}::"
        now = time.time()
        selected_key: Optional[str] = None
        selected_side: Optional[str] = None
        selected_plan: Optional[Dict[str, Any]] = None
        for key, (ts, plan, delivered, interval) in list(self._recent_plans.items()):
            if not key.startswith(prefix):
                continue
            age = now - ts
            plan_ttl = self._plan_delivery_ttl
            if interval > 0:
                plan_ttl = max(self._plan_delivery_ttl, interval * 3.0)
            if age > plan_ttl:
                self._recent_plans.pop(key, None)
                continue
            if delivered and interval > 0 and age > interval:
                continue
            if not isinstance(plan, dict):
                continue
            selected_key = key
            selected_side = key.rsplit("::", 1)[-1]
            selected_plan = copy.deepcopy(plan)
            break
        if not selected_key or not selected_plan:
            return None
        self._recent_plans.pop(selected_key, None)
        try:
            self._persist_state()
        except Exception:
            pass
        return str(selected_side or "").upper(), selected_plan

    def _compute_ai_intervals(
        self,
        symbol: str,
        sentinel: Optional[Dict[str, Any]],
        ctx: Optional[Dict[str, Any]],
    ) -> Dict[str, float]:
        base_symbol = self._base_min_interval if self._base_min_interval > 0 else 0.0
        base_global = self._base_global_cooldown if self._base_global_cooldown > 0 else 0.0
        event_risk = 0.0
        hype_score = 0.0
        if isinstance(sentinel, dict):
            try:
                event_risk = clamp(float(sentinel.get("event_risk", 0.0) or 0.0), 0.0, 1.0)
            except Exception:
                event_risk = 0.0
            try:
                hype_score = clamp(float(sentinel.get("hype_score", 0.0) or 0.0), 0.0, 1.0)
            except Exception:
                hype_score = 0.0
        playbook_active: Dict[str, Any] = {}
        if self.playbook_manager:
            try:
                playbook_active = self.playbook_manager.active()
            except Exception:
                playbook_active = {}
        if isinstance(playbook_active, dict):
            features = playbook_active.get("features") if isinstance(playbook_active.get("features"), dict) else {}
            if isinstance(features, dict):
                for key in ("sentinel_event_risk", "event_risk"):
                    if key in features:
                        try:
                            event_risk = max(event_risk, clamp(float(features[key]), 0.0, 1.0))
                        except Exception:
                            continue
        sentinel_pressure = clamp(event_risk * 0.7 + hype_score * 0.3, 0.0, 1.0)
        ai_confidence = 0.0
        if isinstance(playbook_active, dict):
            confidence_raw = playbook_active.get("confidence") or playbook_active.get("confidence_score")
            if confidence_raw is not None:
                try:
                    ai_confidence = clamp(float(confidence_raw), 0.0, 1.0)
                except Exception:
                    ai_confidence = 0.0
            features = playbook_active.get("features") if isinstance(playbook_active.get("features"), dict) else {}
        else:
            features = {}
        if isinstance(ctx, dict):
            for key in ("playbook_confidence", "tuning_confidence"):
                if key in ctx:
                    try:
                        ai_confidence = max(ai_confidence, clamp(float(ctx[key]), 0.0, 1.0))
                    except Exception:
                        continue
        regime_heat = 0.0
        if isinstance(features, dict):
            slope_val = features.get("regime_slope")
            adx_val = features.get("regime_adx")
            vol_val = features.get("regime_volatility") or features.get("volatility_z")
            slope_score = 0.0
            adx_score = 0.0
            vol_score = 0.0
            try:
                slope_score = clamp(abs(float(slope_val)) / 0.9, 0.0, 1.0)
            except Exception:
                slope_score = 0.0
            try:
                adx_score = clamp(float(adx_val) / 45.0, 0.0, 1.0)
            except Exception:
                adx_score = 0.0
            try:
                vol_score = clamp(abs(float(vol_val)) / 2.2, 0.0, 1.0)
            except Exception:
                vol_score = 0.0
            regime_heat = clamp((slope_score * 0.55) + (adx_score * 0.3) + (vol_score * 0.15), 0.0, 1.0)
        remaining = self.budget.remaining()
        if remaining is None or self.budget.limit <= 0:
            budget_ratio = 1.0
        else:
            try:
                budget_ratio = clamp(remaining / max(self.budget.limit, 1e-6), 0.0, 1.0)
            except Exception:
                budget_ratio = 1.0
        quality = clamp(
            ai_confidence * 0.55 + regime_heat * 0.25 + (1.0 - sentinel_pressure) * 0.2,
            0.0,
            1.0,
        )
        pressure_bonus = clamp(sentinel_pressure * (0.6 + 0.3 * ai_confidence), 0.0, 0.95)
        symbol_interval = base_symbol
        if base_symbol > 0:
            down_factor = clamp(1.0 - pressure_bonus, 0.35, 1.1)
            up_factor = 1.0 + clamp(0.45 - quality, 0.0, 0.45) * 0.35
            symbol_interval = base_symbol * down_factor * up_factor
            if budget_ratio < 0.35:
                budget_scale = clamp((0.35 - budget_ratio) / 0.35, 0.0, 1.0)
                symbol_interval *= 1.0 + budget_scale * 0.8
            symbol_interval = clamp(symbol_interval, max(base_symbol * 0.35, 1.5), base_symbol * 2.4)
        else:
            symbol_interval = 0.0
            if budget_ratio < 0.3:
                symbol_interval = clamp((0.3 - budget_ratio) * 6.0, 0.0, 8.0)
        global_interval = base_global
        if base_global > 0:
            down_factor_g = clamp(1.0 - pressure_bonus * 0.7, 0.25, 1.1)
            up_factor_g = 1.0 + clamp(0.5 - quality, 0.0, 0.5) * 0.45
            global_interval = base_global * down_factor_g * up_factor_g
            if budget_ratio < 0.35:
                budget_scale = clamp((0.35 - budget_ratio) / 0.35, 0.0, 1.0)
                global_interval *= 1.0 + budget_scale * 1.1
            global_interval = max(0.5, global_interval)
        else:
            global_interval = 0.0
            if symbol_interval <= 0 and budget_ratio < 0.25:
                global_interval = max(0.5, (0.25 - budget_ratio) * 4.0)
        return {
            "symbol_interval": float(symbol_interval),
            "global_interval": float(global_interval),
            "event_risk": float(event_risk),
            "confidence": float(ai_confidence),
            "budget_ratio": float(budget_ratio),
            "regime_heat": float(regime_heat),
        }

    def _ensure_bounds(self, text: str, fallback: str) -> str:
        base_words = [w for w in re.split(r"\s+", (text or "").strip()) if w]
        if len(base_words) < 12:
            filler = [w for w in re.split(r"\s+", (fallback or "").strip()) if w]
            idx = 0
            while len(base_words) < 12 and filler:
                base_words.append(filler[idx % len(filler)])
                idx += 1
        if len(base_words) < 6:
            base_words.extend(["trade", "context", "risk", "sizing", "check"])
        if len(base_words) > 70:
            base_words = base_words[:70]
        text = " ".join(base_words).strip()
        if text and not text.endswith("."):
            text += "."
        return text

    async def _async_chat_request(
        self,
        messages: List[Dict[str, Any]],
        *,
        kind: str,
        request_meta: Optional[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]],
    ) -> Optional[str]:
        if not self.enabled or not self._client:
            return None
        temperature = self._temperature_override if self._temperature_supported else None
        attempt = 0
        while True:
            try:
                text, usage, _raw = await self._client._acreate_with_fallback(
                    messages=messages,
                    model=self.model,
                    temperature=temperature,
                    response_format={"type": "text"},
                    metadata=metadata,
                    max_output_tokens=700,
                )
            except OpenAIError as exc:
                if (
                    self._temperature_supported
                    and temperature is not None
                    and exc.should_retry_without_temperature
                    and attempt == 0
                ):
                    temperature = None
                    self._temperature_supported = False
                    attempt += 1
                    log.debug("AI model rejected temperature override; retrying without it.")
                    continue
                raise
            text = (text or "").strip()
            usage_payload = usage if isinstance(usage, dict) else None
            cost = self._estimate_cost(usage_payload)
            if cost is None:
                cost = 0.0025
            meta_payload = {"kind": kind, "model": self.model, "usage": usage_payload}
            self.budget.record(cost, meta_payload)
            try:
                if hasattr(self, "budget_learner") and self.budget_learner:
                    self.budget_learner.record_cost(kind, cost, request_meta)
            except Exception:
                pass
            return text or None

    def _submit_chat_request(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        kind: str,
        budget_estimate: float,
        request_meta: Optional[Dict[str, Any]],
    ) -> Optional[Future]:
        if not self.enabled or not self._client:
            return None
        estimate = max(0.0, float(budget_estimate or 0.0))
        if estimate <= 0:
            estimate = self._estimate_prospective_cost(system_prompt, user_prompt)
        if not self.budget.can_spend(estimate, kind=kind, model=self.model):
            log.info("AI daily budget exhausted — skipping %s request.", kind)
            self._log_budget_block(kind, estimate)
            return None

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        request_id_value: Optional[str] = None
        if isinstance(request_meta, dict):
            raw_id = request_meta.get("request_id")
            if isinstance(raw_id, str):
                request_id_value = raw_id.strip() or None
            elif raw_id is not None:
                request_id_value = str(raw_id)
        if request_id_value:
            messages.insert(
                1,
                {
                    "role": "system",
                    "content": (
                        f"The request_id for this task is '{request_id_value}'. "
                        "Return JSON that includes the exact same request_id field."
                    ),
                },
            )

        metadata = {"component": "trade_advisor", "kind": kind}
        if request_id_value:
            metadata["request_id"] = request_id_value
        if isinstance(request_meta, dict):
            symbol_hint = request_meta.get("symbol")
            if symbol_hint:
                metadata["symbol"] = str(symbol_hint)

        coroutine = self._async_chat_request(
            messages,
            kind=kind,
            request_meta=request_meta,
            metadata=metadata,
        )
        return asyncio.run_coroutine_threadsafe(coroutine, self._client.loop)

    def _chat(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        kind: str,
        budget_estimate: float = 0.0,
        request_meta: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        future = self._submit_chat_request(
            system_prompt,
            user_prompt,
            kind=kind,
            budget_estimate=budget_estimate,
            request_meta=request_meta,
        )
        if not isinstance(future, Future):
            return None
        try:
            return future.result()
        except Exception as exc:
            log.debug(f"AI request failed ({kind}): {exc}")
            return None

    @staticmethod
    def _extract_choice_content(choice: Dict[str, Any]) -> str:
        """Normalize the various chat completion payload shapes to plain text."""
        if not isinstance(choice, dict):
            return ""
        message = choice.get("message") or {}
        if not isinstance(message, dict):
            return ""
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, dict):
            text = content.get("text")
            return str(text or "") if text is not None else ""
        if isinstance(content, list):
            parts: List[str] = []
            for block in content:
                if isinstance(block, dict):
                    block_type = str(block.get("type") or "").lower()
                    if block_type in {"text", "output_text", "message"}:
                        text_val = block.get("text")
                        if isinstance(text_val, str):
                            parts.append(text_val)
                            continue
                        if isinstance(text_val, dict):
                            nested = text_val.get("value")
                            if isinstance(nested, str):
                                parts.append(nested)
                                continue
                    text_val = block.get("content")
                    if isinstance(text_val, str):
                        parts.append(text_val)
                        continue
                    if isinstance(text_val, dict):
                        nested = text_val.get("value")
                        if isinstance(nested, str):
                            parts.append(nested)
                elif isinstance(block, str):
                    parts.append(block)
            if parts:
                return "".join(parts)
        refusal = message.get("refusal")
        if isinstance(refusal, str):
            return refusal
        return ""

    def _parse_structured(self, content: str) -> Optional[Dict[str, Any]]:
        if not content:
            return None

        text = content.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Prefer JSON fenced blocks (```json ... ```)
        fence_pattern = re.compile(r"```(?:json)?\s*([\s\S]+?)```", re.IGNORECASE)
        for match in fence_pattern.finditer(text):
            block = match.group(1).strip()
            if not block:
                continue
            try:
                return json.loads(block)
            except json.JSONDecodeError:
                continue

        # Fallback: scan for the first decodable object within the string.
        decoder = json.JSONDecoder()
        idx = 0
        length = len(text)
        while idx < length:
            brace_idx = text.find("{", idx)
            if brace_idx == -1:
                break
            try:
                obj, end = decoder.raw_decode(text, brace_idx)
            except json.JSONDecodeError:
                idx = brace_idx + 1
                continue
            if isinstance(obj, dict):
                return obj
            idx = max(end, brace_idx + 1)
            continue

        return None

    def _fallback_plan(
        self,
        symbol: str,
        side: str,
        price: float,
        base_sl: float,
        base_tp: float,
        ctx: Dict[str, Any],
        sentinel: Dict[str, Any],
        atr_abs: float,
    ) -> Dict[str, Any]:
        label = sentinel.get("label", "green")
        event_risk = float(sentinel.get("event_risk", 0.0) or 0.0)
        hype_score = float(sentinel.get("hype_score", 0.0) or 0.0)
        size_factor = float(sentinel.get("actions", {}).get("size_factor", 1.0) or 1.0)
        risk_bias = 1.0
        if label == "yellow":
            risk_bias = 0.6
        elif label == "red":
            risk_bias = 0.0
        else:
            risk_bias = 1.0 + max(0.0, hype_score - 0.55) * 0.35
        cap_mult = SIZE_MULT_CAP if SIZE_MULT_CAP > 0 else 1.8
        size_multiplier = clamp(
            size_factor * risk_bias,
            max(0.0, SIZE_MULT_FLOOR),
            cap_mult,
        )

        sl_mult = 1.0
        tp_mult = 1.0
        if event_risk > 0.6:
            sl_mult = 1.25
            tp_mult = 0.9
        elif hype_score > 0.65:
            tp_mult = 1.35 if side == "BUY" else 1.2
        elif event_risk < 0.25 and hype_score < 0.35:
            sl_mult = 0.95
            tp_mult = 1.05

        cap = self._resolve_leverage_cap(symbol)
        baseline = cap
        if baseline is None:
            if math.isfinite(LEVERAGE) and LEVERAGE > 0:
                baseline = LEVERAGE
            else:
                baseline = 10.0
        leverage_target = float(baseline) * (
            0.5 if event_risk > 0.6 else (1.0 + hype_score * 0.25)
        )
        leverage = self._clamp_leverage_value(symbol, leverage_target, fallback=baseline)

        fasttp_overrides: Optional[Dict[str, Any]] = None
        if event_risk > 0.55:
            fasttp_overrides = {
                "enabled": True,
                "min_r": min(FASTTP_MIN_R, 0.28),
                "ret1": FAST_TP_RET1 * 0.7,
                "ret3": FAST_TP_RET3 * 0.7,
                "snap_atr": max(FASTTP_SNAP_ATR * 0.8, 0.1),
            }

        explanation = (
            f"Signal suggests a {side.lower()} on {symbol}. Sentinel reports {label} risk (event={event_risk:.2f}, hype={hype_score:.2f}), "
            f"so trade size is adjusted to {size_multiplier:.2f}× baseline and leverage steered to {leverage:.1f}×. "
            f"Stop distance scaled {sl_mult:.2f}× ATR, target {tp_mult:.2f}× ATR. "
            + (
                "Fast take-profit stays default to let the move run."
                if not fasttp_overrides
                else "Fast take-profit tightened for quicker risk release."
            )
        )

        explanation = self._ensure_bounds(explanation, explanation)

        return {
            "symbol": symbol,
            "size_multiplier": size_multiplier,
            "sl_multiplier": sl_mult,
            "tp_multiplier": tp_mult,
            "leverage": leverage,
            "fasttp_overrides": fasttp_overrides,
            "risk_note": label,
            "explanation": explanation,
            "event_risk": event_risk,
            "hype_score": hype_score,
            "max_leverage_cap": cap,
            "take": True,
            "decision": "take",
            "decision_reason": "fallback_rules",
            "decision_note": "Signal cleared heuristics. Proceeding with adjusted sizing and risk bounds.",
            "entry_price": float(price),
            "stop_loss": float(price - base_sl if side == "BUY" else price + base_sl),
            "take_profit": float(price + base_tp if side == "BUY" else price - base_tp),
        }

    def _apply_plan_overrides(
        self,
        fallback: Dict[str, Any],
        parsed: Dict[str, Any],
        *,
        request_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        plan = {**fallback}
        plan["take"] = bool(fallback.get("take", True))
        plan["decision"] = "take" if plan["take"] else "skip"
        if fallback.get("decision_reason"):
            plan["decision_reason"] = fallback.get("decision_reason")
        if fallback.get("decision_note"):
            plan["decision_note"] = fallback.get("decision_note")
        size_multiplier = parsed.get("size_multiplier")
        sl_multiplier = parsed.get("sl_multiplier")
        tp_multiplier = parsed.get("tp_multiplier")
        leverage = parsed.get("leverage")
        fasttp_overrides = parsed.get("fasttp_overrides")
        explanation = parsed.get("explanation")
        risk_note = parsed.get("risk_note")
        decision_raw = parsed.get("decision")
        take_raw = parsed.get("take")
        decision_reason = parsed.get("decision_reason") or parsed.get("reason")
        decision_note = parsed.get("decision_note") or parsed.get("note")
        confidence = parsed.get("confidence") or parsed.get("score")
        confidence_value: Optional[float] = None

        symbol_hint: Optional[str] = None
        if isinstance(request_payload, dict):
            raw_symbol = request_payload.get("symbol") or request_payload.get("asset")
            if isinstance(raw_symbol, str) and raw_symbol.strip():
                symbol_hint = raw_symbol.strip().upper()
            elif isinstance(request_payload.get("context"), dict):
                ctx_symbol = request_payload["context"].get("symbol")
                if isinstance(ctx_symbol, str) and ctx_symbol.strip():
                    symbol_hint = ctx_symbol.strip().upper()
        if not symbol_hint and isinstance(fallback.get("symbol"), str):
            symbol_hint = str(fallback.get("symbol")).strip().upper()

        take = plan["take"]
        if isinstance(take_raw, bool):
            take = bool(take_raw)
        elif isinstance(decision_raw, str):
            token = decision_raw.strip().lower()
            if token in {"take", "enter", "proceed", "accept", "go"}:
                take = True
            elif token in {"skip", "avoid", "pass", "reject", "stop"}:
                take = False
        plan["take"] = bool(take)
        plan["decision"] = "take" if plan["take"] else "skip"
        if isinstance(decision_reason, str) and decision_reason.strip():
            plan["decision_reason"] = decision_reason.strip()
        if isinstance(decision_note, str) and decision_note.strip():
            plan["decision_note"] = decision_note.strip()

        if isinstance(size_multiplier, (int, float)):
            plan["size_multiplier"] = clamp(
                float(size_multiplier),
                0.0,
                SIZE_MULT_CAP,
            )
        if isinstance(sl_multiplier, (int, float)):
            plan["sl_multiplier"] = clamp(float(sl_multiplier), 0.5, 2.5)
        if isinstance(tp_multiplier, (int, float)):
            plan["tp_multiplier"] = clamp(float(tp_multiplier), 0.5, 3.0)
        if isinstance(leverage, (int, float)):
            fallback_cap = fallback.get("max_leverage_cap")
            plan["leverage"] = self._clamp_leverage_value(
                symbol_hint or fallback.get("symbol", ""),
                float(leverage),
                fallback=fallback_cap or fallback.get("leverage"),
            )
        if isinstance(fasttp_overrides, dict):
            fallback_fasttp = fallback.get("fasttp_overrides")
            if isinstance(fallback_fasttp, dict):
                base_min_r = fallback_fasttp.get("min_r", FASTTP_MIN_R)
            else:
                base_min_r = FASTTP_MIN_R
            overrides = {
                "enabled": bool(fasttp_overrides.get("enabled", True)),
                "min_r": float(fasttp_overrides.get("min_r", base_min_r)),
                "ret1": float(fasttp_overrides.get("ret1", FAST_TP_RET1)),
                "ret3": float(fasttp_overrides.get("ret3", FAST_TP_RET3)),
                "snap_atr": float(fasttp_overrides.get("snap_atr", FASTTP_SNAP_ATR)),
            }
            plan["fasttp_overrides"] = overrides
        if isinstance(risk_note, str) and risk_note.strip():
            plan["risk_note"] = risk_note.strip()
        if isinstance(explanation, str):
            if explanation.strip():
                plan["explanation"] = self._ensure_bounds(explanation, fallback.get("explanation", ""))
            else:
                plan["explanation"] = ""
        else:
            plan["explanation"] = fallback.get("explanation")
        if isinstance(confidence, (int, float)):
            confidence_value = clamp(float(confidence), 0.0, 1.0)
            plan["confidence"] = confidence_value
        elif isinstance(confidence, str):
            token = confidence.strip()
            if token:
                try:
                    if token.endswith("%"):
                        numeric = float(token.rstrip("% ")) / 100.0
                    else:
                        numeric = float(token)
                except (TypeError, ValueError):
                    numeric = None
                else:
                    confidence_value = clamp(float(numeric), 0.0, 1.0)
                    plan["confidence"] = confidence_value

        if CONFIDENCE_SIZING_ENABLED and confidence_value is not None:
            target_mult = _confidence_size_target(confidence_value)
            current_mult = plan.get("size_multiplier")
            if isinstance(current_mult, (int, float)) and current_mult > 0:
                base_mult = float(current_mult)
            else:
                base_mult = float(fallback.get("size_multiplier", target_mult) or target_mult)
            base_mult = max(0.0, base_mult)
            blended = (base_mult * (1.0 - CONFIDENCE_SIZING_BLEND)) + (
                target_mult * CONFIDENCE_SIZING_BLEND
            )
            plan["size_multiplier"] = clamp(
                blended,
                max(0.0, SIZE_MULT_FLOOR),
                SIZE_MULT_CAP,
            )

        entry_px = (
            parsed.get("entry_price")
            or parsed.get("entry")
            or parsed.get("entry_px")
            or parsed.get("entryPrice")
        )
        if isinstance(entry_px, (int, float)) and entry_px > 0:
            plan["entry_price"] = float(entry_px)
        stop_px = (
            parsed.get("stop_loss")
            or parsed.get("stop")
            or parsed.get("stopPrice")
            or parsed.get("sl")
        )
        if isinstance(stop_px, (int, float)) and stop_px > 0:
            plan["stop_loss"] = float(stop_px)
        tp_px = (
            parsed.get("take_profit")
            or parsed.get("tp")
            or parsed.get("target")
            or parsed.get("target_price")
        )
        if isinstance(tp_px, (int, float)) and tp_px > 0:
            plan["take_profit"] = float(tp_px)
        return plan

    def _apply_trend_plan_overrides(
        self,
        fallback: Dict[str, Any],
        parsed: Dict[str, Any],
        request_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        plan = {**fallback}
        decision_reason = parsed.get("decision_reason") or parsed.get("reason")
        decision_note = parsed.get("decision_note") or parsed.get("note")
        if isinstance(decision_reason, str) and decision_reason.strip():
            plan["decision_reason"] = decision_reason.strip()
        if isinstance(decision_note, str) and decision_note.strip():
            plan["decision_note"] = decision_note.strip()

        decision_raw = parsed.get("decision")
        take_raw = parsed.get("take")
        take = bool(plan.get("take", False))
        if isinstance(take_raw, bool):
            take = bool(take_raw)
        elif isinstance(decision_raw, str):
            token = decision_raw.strip().lower()
            if token in {"take", "enter", "proceed", "buy", "sell", "long", "short"}:
                take = True
            elif token in {"skip", "avoid", "pass", "reject", "stop"}:
                take = False
        plan["take"] = take
        plan["decision"] = "take" if take else "skip"

        side_raw = parsed.get("side") or parsed.get("direction")
        side_norm: Optional[str] = None
        if isinstance(side_raw, str):
            side_norm = side_raw.strip().upper()
        if side_norm not in {"BUY", "SELL"}:
            fallback_side = fallback.get("side")
            if isinstance(fallback_side, str):
                token = fallback_side.strip().upper()
                if token in {"BUY", "SELL"}:
                    side_norm = token
        if side_norm not in {"BUY", "SELL"} and isinstance(request_payload, dict):
            req_side = request_payload.get("side")
            if not isinstance(req_side, str):
                context = request_payload.get("context") if isinstance(request_payload, dict) else None
                if isinstance(context, dict):
                    req_side = context.get("side")
            if isinstance(req_side, str):
                token = req_side.strip().upper()
                if token in {"BUY", "SELL"}:
                    side_norm = token
        if not side_norm and isinstance(decision_raw, str):
            token = decision_raw.strip().lower()
            if token in {"buy", "long"}:
                side_norm = "BUY"
            elif token in {"sell", "short"}:
                side_norm = "SELL"
        if side_norm in {"BUY", "SELL"}:
            plan["side"] = side_norm

        size_multiplier = parsed.get("size_multiplier")
        sl_multiplier = parsed.get("sl_multiplier")
        tp_multiplier = parsed.get("tp_multiplier")
        leverage = parsed.get("leverage")
        fasttp_overrides = parsed.get("fasttp_overrides") or parsed.get("fast_tp")
        risk_note = parsed.get("risk_note")
        explanation = parsed.get("explanation") or parsed.get("rationale")
        confidence = parsed.get("confidence") or parsed.get("score")

        symbol_hint: Optional[str] = None
        if isinstance(request_payload, dict):
            raw_symbol = request_payload.get("symbol") or request_payload.get("asset")
            if isinstance(raw_symbol, str) and raw_symbol.strip():
                symbol_hint = raw_symbol.strip().upper()
        if not symbol_hint and isinstance(fallback.get("symbol"), str):
            symbol_hint = str(fallback.get("symbol")).strip().upper()

        if isinstance(size_multiplier, (int, float)):
            plan["size_multiplier"] = clamp(float(size_multiplier), 0.0, 2.0)
        if isinstance(sl_multiplier, (int, float)):
            plan["sl_multiplier"] = clamp(float(sl_multiplier), 0.5, 2.5)
        if isinstance(tp_multiplier, (int, float)):
            plan["tp_multiplier"] = clamp(float(tp_multiplier), 0.5, 3.0)
        if isinstance(leverage, (int, float)):
            fallback_cap = fallback.get("max_leverage_cap")
            plan["leverage"] = self._clamp_leverage_value(
                symbol_hint or fallback.get("symbol", ""),
                float(leverage),
                fallback=fallback_cap or fallback.get("leverage"),
            )
        if isinstance(fasttp_overrides, dict):
            plan["fasttp_overrides"] = {
                "enabled": bool(fasttp_overrides.get("enabled", True)),
                "min_r": float(fasttp_overrides.get("min_r", FASTTP_MIN_R)),
                "ret1": float(fasttp_overrides.get("ret1", FAST_TP_RET1)),
                "ret3": float(fasttp_overrides.get("ret3", FAST_TP_RET3)),
                "snap_atr": float(fasttp_overrides.get("snap_atr", FASTTP_SNAP_ATR)),
            }
        if isinstance(risk_note, str) and risk_note.strip():
            plan["risk_note"] = risk_note.strip()
        if isinstance(explanation, str) and explanation.strip():
            plan["explanation"] = self._ensure_bounds(explanation, fallback.get("explanation", ""))
        if isinstance(confidence, (int, float)):
            plan["confidence"] = clamp(float(confidence), 0.0, 1.0)
        elif isinstance(confidence, str):
            token = confidence.strip()
            if token:
                try:
                    if token.endswith("%"):
                        numeric = float(token.rstrip("% ")) / 100.0
                    else:
                        numeric = float(token)
                except (TypeError, ValueError):
                    numeric = None
                else:
                    plan["confidence"] = clamp(float(numeric), 0.0, 1.0)

        entry_px = (
            parsed.get("entry_price")
            or parsed.get("entry")
            or parsed.get("entry_px")
            or parsed.get("entryPrice")
        )
        if isinstance(entry_px, (int, float)) and entry_px > 0:
            plan["entry_price"] = float(entry_px)
        stop_px = (
            parsed.get("stop_loss")
            or parsed.get("stop")
            or parsed.get("stopPrice")
            or parsed.get("sl")
        )
        if isinstance(stop_px, (int, float)) and stop_px > 0:
            plan["stop_loss"] = float(stop_px)
        tp_px = (
            parsed.get("take_profit")
            or parsed.get("tp")
            or parsed.get("target")
            or parsed.get("target_price")
        )
        if isinstance(tp_px, (int, float)) and tp_px > 0:
            plan["take_profit"] = float(tp_px)
        return plan

    def plan_trade(
        self,
        symbol: str,
        side: str,
        price: float,
        base_sl: float,
        base_tp: float,
        ctx: Dict[str, Any],
        sentinel: Dict[str, Any],
        atr_abs: float,
        *,
        async_mode: bool = True,
    ) -> Dict[str, Any]:
        fallback = self._fallback_plan(symbol, side, price, base_sl, base_tp, ctx, sentinel, atr_abs)
        symbol_key = self._normalize_symbol(symbol)
        side_key = self._normalize_side(side)
        plan_key = f"plan::{symbol_key}::{side_key}"
        if not self.enabled:
            self._recent_plan_store(plan_key, fallback)
            return fallback

        sentinel_label = str((sentinel or {}).get("label", "")).lower()
        size_factor = 1.0
        if isinstance(sentinel, dict):
            try:
                size_factor = float(sentinel.get("actions", {}).get("size_factor", 1.0) or 1.0)
            except (TypeError, ValueError):
                size_factor = 1.0

        if sentinel_label == "red" or size_factor <= 0:
            fallback.update(
                {
                    "take": False,
                    "decision": "skip",
                    "decision_reason": "sentinel_block",
                    "decision_note": "Sentinel flagged hard risk; skipped without AI call.",
                    "explanation": self._ensure_bounds(
                        "Sentinel reported a red risk state so the trade was skipped immediately.",
                        fallback.get("explanation", ""),
                    ),
                }
            )
            self._recent_plan_store(plan_key, fallback)
            return fallback

        if self.budget_learner and not self.budget_learner.should_allocate(symbol, "plan"):
            fallback.update(
                {
                    "take": False,
                    "decision": "skip",
                    "decision_reason": "budget_bias",
                    "decision_note": "Budget learner deprioritized this symbol after weak ROI.",
                    "explanation": "",
                }
            )
            self._recent_plan_store(plan_key, fallback)
            return fallback

        throttle_key = plan_key
        now = time.time()
        interval_meta = self._compute_ai_intervals(symbol, sentinel, ctx)
        min_interval = float(interval_meta.get("symbol_interval", self._base_min_interval))
        if min_interval < 0:
            min_interval = 0.0
        global_cooldown = float(interval_meta.get("global_interval", self._base_global_cooldown))
        if global_cooldown < 0:
            global_cooldown = 0.0
        if isinstance(ctx, dict):
            try:
                ctx["ai_cooldown_symbol_interval"] = float(min_interval)
                ctx["ai_cooldown_global_interval"] = float(global_cooldown)
                ctx["ai_cooldown_event_risk"] = float(interval_meta.get("event_risk", 0.0))
                ctx["ai_cooldown_confidence"] = float(interval_meta.get("confidence", 0.0))
                ctx["ai_cooldown_budget_ratio"] = float(interval_meta.get("budget_ratio", 1.0))
                ctx["ai_cooldown_regime_heat"] = float(interval_meta.get("regime_heat", 0.0))
            except Exception:
                pass
        status, payload = self._process_pending_request(
            throttle_key,
            fallback,
            now,
            min_interval=min_interval,
            global_cooldown=global_cooldown,
        )
        if status in {"pending", "timeout"}:
            return payload  # type: ignore[return-value]
        if status == "fallback":
            return payload  # type: ignore[return-value]
        if status == "response":
            bundle = payload or {}
            response_text = bundle.get("response") if isinstance(bundle, dict) else None
            meta = bundle.get("info") if isinstance(bundle, dict) else {}
            return self._finalize_response(throttle_key, fallback, meta, response_text, now)

        recent_plan = self._recent_plan_lookup(throttle_key, now, min_interval)
        if recent_plan is not None:
            return recent_plan

        if not self._has_pending_capacity(throttle_key):
            self._recent_plan_store(
                throttle_key,
                fallback,
                now,
                min_interval=min_interval,
            )
            return self._pending_stub(
                fallback,
                "plan_queue_full",
                "AI queue saturated; using fallback heuristics.",
                throttle_key=throttle_key,
                pending=False,
            )

        system_prompt = (
            "You are an automated crypto futures planning assistant for a trading bot. "
            "Analyze the provided indicator stats and sentinel hints to decide if the bot should execute the trade. "
            "Respond ONLY with a single minified JSON object (no prose or markdown). The object must include the keys: "
            "take (bool), decision, decision_reason, decision_note, size_multiplier, sl_multiplier, tp_multiplier, leverage, "
            "risk_note, explanation, confidence (0-1), fasttp_overrides (object with enabled,min_r,ret1,ret3,snap_atr). "
            "If take is true, also include numeric levels entry_price, stop_loss, take_profit. When declining, set take=false, "
            "decision=\"skip\", leave explanation as an empty string, and still populate the remaining required fields."
        )
        stats_block = self._extract_stat_block(ctx)
        sentinel_payload = self._summarize_sentinel(sentinel)
        cap = fallback.get("max_leverage_cap")
        if cap is None:
            cap = self._resolve_leverage_cap(symbol)
        constraints: Dict[str, Any] = {}
        if MAX_NOTIONAL_USDT > 0:
            constraints["max_notional"] = MAX_NOTIONAL_USDT
        if cap is not None:
            constraints["max_leverage"] = cap
        user_payload: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "price": price,
            "base_stop": base_sl,
            "base_target": base_tp,
            "atr_abs": atr_abs,
        }
        extra_context: Dict[str, Any] = {}
        for key in (
            "policy_bucket",
            "policy_size_multiplier",
            "sentinel_factor",
            "alpha_prob",
            "alpha_conf",
            "budget_remaining",
            "budget_spent",
            "open_positions",
            "active_positions",
        ):
            if key not in ctx:
                continue
            value = ctx.get(key)
            if isinstance(value, (int, float, str, bool)):
                extra_context[key] = value
            elif key in {"open_positions", "active_positions"} and isinstance(value, dict):
                trimmed: Dict[str, float] = {}
                for idx, (sym_name, qty_val) in enumerate(value.items()):
                    if idx >= 6:
                        break
                    try:
                        trimmed[sym_name] = float(qty_val)
                    except Exception:
                        continue
                if trimmed:
                    extra_context[key] = trimmed
        if extra_context:
            user_payload["context"] = extra_context
        if stats_block:
            user_payload["stats"] = stats_block
        if sentinel_payload:
            user_payload["sentinel"] = sentinel_payload
        if constraints:
            user_payload["constraints"] = constraints
        base_prompt = json.dumps(user_payload, sort_keys=True, separators=(",", ":"))
        cache_key = self._cache_key("plan", system_prompt, user_payload)
        cached_plan = self._cache_lookup(cache_key)
        if cached_plan is not None:
            self._recent_plan_store(
                throttle_key,
                cached_plan,
                now,
                min_interval=min_interval,
            )
            return cached_plan
        estimate = self._estimate_prospective_cost(system_prompt, base_prompt)
        if not async_mode or not self._client:
            request_id = self._new_request_id("plan", throttle_key)
            payload_with_id = dict(user_payload)
            payload_with_id["request_id"] = request_id
            try:
                user_prompt = json.dumps(payload_with_id, sort_keys=True, separators=(",", ":"))
            except Exception:
                self._recent_plan_store(
                    throttle_key,
                    fallback,
                    now,
                    min_interval=min_interval,
                )
                return fallback
            fallback["request_id"] = request_id
            meta = {"symbol": symbol, "context": "plan", "request_id": request_id}
            response = self._chat(
                system_prompt,
                user_prompt,
                kind="plan",
                budget_estimate=estimate,
                request_meta=meta,
            )
            if not response:
                self._recent_plan_store(
                    throttle_key,
                    fallback,
                    now,
                    min_interval=min_interval,
                )
                return fallback
            parsed = self._parse_structured(response)
            if not isinstance(parsed, dict):
                self._recent_plan_store(
                    throttle_key,
                    fallback,
                    now,
                    min_interval=min_interval,
                )
                return fallback
            parsed.setdefault("request_id", request_id)
            plan = self._apply_plan_overrides(
                fallback,
                parsed,
                request_payload=payload_with_id,
            )
            plan.setdefault("request_id", request_id)
            self._cache_store(cache_key, plan)
            self._recent_plan_store(
                throttle_key,
                plan,
                now,
                min_interval=min_interval,
            )
            return plan

        if not self.budget.can_spend(estimate, kind="plan", model=self.model):
            self._log_budget_block("plan", estimate)
            self._recent_plan_store(
                throttle_key,
                fallback,
                now,
                min_interval=min_interval,
            )
            return fallback

        request_id = self._new_request_id("plan", throttle_key)
        payload_with_id = dict(user_payload)
        payload_with_id["request_id"] = request_id
        try:
            user_prompt = json.dumps(payload_with_id, sort_keys=True, separators=(",", ":"))
        except Exception:
            self._recent_plan_store(
                throttle_key,
                fallback,
                now,
                min_interval=min_interval,
            )
            return fallback
        meta = {"symbol": symbol, "context": "plan", "request_id": request_id}
        fallback["request_id"] = request_id

        cooldown_blocked = global_cooldown > 0 and (now - self._last_global_request) < global_cooldown
        if cooldown_blocked or self._active_pending() >= AI_CONCURRENCY:
            if not self._has_pending_capacity(throttle_key):
                self._recent_plan_store(
                    throttle_key,
                    fallback,
                    now,
                    min_interval=min_interval,
                )
                return self._pending_stub(
                    fallback,
                    "plan_queue_full",
                    "AI queue saturated; using fallback heuristics.",
                    throttle_key=throttle_key,
                    pending=False,
                )
            pending_info = {
                "future": None,
                "fallback": fallback,
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "user_payload": payload_with_id,
                "cache_key": cache_key,
                "kind": "plan",
                "estimate": estimate,
                "queued_at": now,
                "ready_after": now + max(0.5, global_cooldown or 0.5),
                "note": "Queued for AI planning",
                "notified": False,
                "request_meta": meta,
            }
            stub = self._pending_stub(
                fallback,
                "plan_pending",
                "Queued for AI planning",
                throttle_key=throttle_key,
                request_id=request_id,
            )
            pending_info["request_id"] = request_id
            pending_info["min_interval"] = float(min_interval)
            pending_info["global_cooldown"] = float(global_cooldown)
            self._pending_requests[throttle_key] = pending_info
            self._register_pending_key(throttle_key)
            return stub

        if not self._has_pending_capacity(throttle_key):
            self._recent_plan_store(
                throttle_key,
                fallback,
                now,
                min_interval=min_interval,
            )
            return self._pending_stub(
                fallback,
                "plan_queue_full",
                "AI queue saturated; using fallback heuristics.",
                throttle_key=throttle_key,
                pending=False,
            )

        future = self._dispatch_request(
            system_prompt,
            user_prompt,
            kind="plan",
            budget_estimate=estimate,
            request_meta=meta,
        )
        if not future:
            self._recent_plan_store(
                throttle_key,
                fallback,
                now,
                min_interval=min_interval,
            )
            return fallback
        self._pending_requests[throttle_key] = {
            "future": future,
            "fallback": fallback,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "user_payload": payload_with_id,
            "cache_key": cache_key,
            "kind": "plan",
            "estimate": estimate,
            "queued_at": now,
            "dispatched_at": now,
            "notified": False,
            "request_meta": meta,
            "request_id": request_id,
            "min_interval": float(min_interval),
            "global_cooldown": float(global_cooldown),
        }
        self._register_pending_key(throttle_key)
        self._last_global_request = now
        self._last_global_interval = global_cooldown
        self._attach_future_callback(throttle_key, future)
        stub = self._pending_stub(
            fallback,
            "plan_pending",
            "Waiting for AI plan response",
            throttle_key=throttle_key,
            request_id=request_id,
        )
        return stub

    def plan_trend_trade(
        self,
        symbol: str,
        price: float,
        base_sl: float,
        base_tp: float,
        ctx: Dict[str, Any],
        sentinel: Dict[str, Any],
        atr_abs: float,
        *,
        async_mode: bool = True,
    ) -> Dict[str, Any]:
        symbol_key = self._normalize_symbol(symbol)
        trend_key = f"trend::{symbol_key}"
        cap = self._resolve_leverage_cap(symbol)
        baseline_leverage = cap
        if baseline_leverage is None:
            if math.isfinite(LEVERAGE) and LEVERAGE > 0:
                baseline_leverage = LEVERAGE
            else:
                baseline_leverage = 10.0
        fallback = {
            "symbol": symbol,
            "take": False,
            "decision": "skip",
            "decision_reason": "no_signal",
            "decision_note": "Autonomous scan did not detect a safe opportunity.",
            "size_multiplier": 1.0,
            "sl_multiplier": 1.0,
            "tp_multiplier": 1.0,
            "leverage": self._clamp_leverage_value(
                symbol,
                float(baseline_leverage),
                fallback=baseline_leverage,
            ),
            "risk_note": sentinel.get("label", "green") if sentinel else "green",
            "explanation": "",
            "fasttp_overrides": None,
            "event_risk": float(sentinel.get("event_risk", 0.0) if sentinel else 0.0),
            "hype_score": float(sentinel.get("hype_score", 0.0) if sentinel else 0.0),
            "side": None,
            "confidence": 0.0,
            "entry_price": float(price),
            "max_leverage_cap": cap,
        }
        if not self.enabled:
            self._recent_plan_store(trend_key, fallback)
            return fallback

        sentinel_label = str((sentinel or {}).get("label", "")).lower()
        size_factor = 1.0
        if isinstance(sentinel, dict):
            try:
                size_factor = float(sentinel.get("actions", {}).get("size_factor", 1.0) or 1.0)
            except (TypeError, ValueError):
                size_factor = 1.0

        if sentinel_label == "red" or size_factor <= 0:
            fallback.update(
                {
                    "take": False,
                    "decision": "skip",
                    "decision_reason": "sentinel_block",
                    "decision_note": "Sentinel blocked autonomous scan; skipped without AI call.",
                    "explanation": "",
                }
            )
            self._recent_plan_store(trend_key, fallback)
            return fallback

        if self.budget_learner and not self.budget_learner.should_allocate(symbol, "trend"):
            fallback.update(
                {
                    "take": False,
                    "decision": "skip",
                    "decision_reason": "budget_bias",
                    "decision_note": "Budget learner suppressed the autonomous scan for this symbol.",
                }
            )
            self._recent_plan_store(trend_key, fallback)
            return fallback

        throttle_key = trend_key
        now = time.time()
        interval_meta = self._compute_ai_intervals(symbol, sentinel, ctx)
        min_interval = float(interval_meta.get("symbol_interval", self._base_min_interval))
        if min_interval < 0:
            min_interval = 0.0
        global_cooldown = float(interval_meta.get("global_interval", self._base_global_cooldown))
        if global_cooldown < 0:
            global_cooldown = 0.0
        if isinstance(ctx, dict):
            try:
                ctx["ai_cooldown_symbol_interval"] = float(min_interval)
                ctx["ai_cooldown_global_interval"] = float(global_cooldown)
                ctx["ai_cooldown_event_risk"] = float(interval_meta.get("event_risk", 0.0))
                ctx["ai_cooldown_confidence"] = float(interval_meta.get("confidence", 0.0))
                ctx["ai_cooldown_budget_ratio"] = float(interval_meta.get("budget_ratio", 1.0))
                ctx["ai_cooldown_regime_heat"] = float(interval_meta.get("regime_heat", 0.0))
            except Exception:
                pass
        status, payload = self._process_pending_request(
            throttle_key,
            fallback,
            now,
            min_interval=min_interval,
            global_cooldown=global_cooldown,
        )
        if status in {"pending", "timeout"}:
            return payload  # type: ignore[return-value]
        if status == "fallback":
            return payload  # type: ignore[return-value]
        if status == "response":
            bundle = payload or {}
            response_text = bundle.get("response") if isinstance(bundle, dict) else None
            meta = bundle.get("info") if isinstance(bundle, dict) else {}
            return self._finalize_response(throttle_key, fallback, meta, response_text, now)

        recent_plan = self._recent_plan_lookup(throttle_key, now, min_interval)
        if recent_plan is not None:
            return recent_plan

        if not self._has_pending_capacity(throttle_key):
            self._recent_plan_store(
                throttle_key,
                fallback,
                now,
                min_interval=min_interval,
            )
            return self._pending_stub(
                fallback,
                "plan_queue_full",
                "AI queue saturated; falling back to autonomous scan heuristics.",
                throttle_key=throttle_key,
                pending=False,
            )

        system_prompt = (
            "You scout autonomous trends for a futures bot. Weigh indicator stats and sentinel risk to decide on a trade. "
            "Return JSON with take (bool), decision, decision_reason, decision_note, side (BUY/SELL), size_multiplier, "
            "sl_multiplier, tp_multiplier, leverage, risk_note, explanation, fasttp_overrides (enabled,min_r,ret1,ret3,snap_atr), "
            "confidence (0-1) and optional levels entry_price, stop_loss, take_profit. Declines should leave explanation empty."
        )
        stats_block = self._extract_stat_block(ctx)
        sentinel_payload = self._summarize_sentinel(sentinel)
        constraints: Dict[str, Any] = {}
        if MAX_NOTIONAL_USDT > 0:
            constraints["max_notional"] = MAX_NOTIONAL_USDT
        if cap is not None:
            constraints["max_leverage"] = cap
        user_payload: Dict[str, Any] = {
            "symbol": symbol,
            "price": price,
            "atr_abs": atr_abs,
            "distance": {"stop": base_sl, "target": base_tp},
        }
        extra_context: Dict[str, Any] = {}
        for key in (
            "policy_bucket",
            "policy_size_multiplier",
            "sentinel_factor",
            "alpha_prob",
            "alpha_conf",
            "budget_remaining",
            "budget_spent",
            "open_positions",
            "active_positions",
        ):
            if key not in ctx:
                continue
            value = ctx.get(key)
            if isinstance(value, (int, float, str, bool)):
                extra_context[key] = value
            elif key in {"open_positions", "active_positions"} and isinstance(value, dict):
                trimmed: Dict[str, float] = {}
                for idx, (sym_name, qty_val) in enumerate(value.items()):
                    if idx >= 6:
                        break
                    try:
                        trimmed[sym_name] = float(qty_val)
                    except Exception:
                        continue
                if trimmed:
                    extra_context[key] = trimmed
        if extra_context:
            user_payload["context"] = extra_context
        if stats_block:
            user_payload["stats"] = stats_block
        if sentinel_payload:
            user_payload["sentinel"] = sentinel_payload
        if constraints:
            user_payload["constraints"] = constraints
        base_prompt = json.dumps(user_payload, sort_keys=True, separators=(",", ":"))
        cache_key = self._cache_key("trend", system_prompt, user_payload)
        cached_plan = self._cache_lookup(cache_key)
        if cached_plan is not None:
            self._recent_plan_store(
                throttle_key,
                cached_plan,
                now,
                min_interval=min_interval,
            )
            return cached_plan
        estimate = self._estimate_prospective_cost(system_prompt, base_prompt)
        if not async_mode or not self._client:
            request_id = self._new_request_id("trend", throttle_key)
            payload_with_id = dict(user_payload)
            payload_with_id["request_id"] = request_id
            try:
                user_prompt = json.dumps(payload_with_id, sort_keys=True, separators=(",", ":"))
            except Exception:
                self._recent_plan_store(
                    throttle_key,
                    fallback,
                    now,
                    min_interval=min_interval,
                )
                return fallback
            fallback["request_id"] = request_id
            meta = {"symbol": symbol, "context": "trend", "request_id": request_id}
            response = self._chat(
                system_prompt,
                user_prompt,
                kind="trend",
                budget_estimate=estimate,
                request_meta=meta,
            )
            if not response:
                self._recent_plan_store(
                    throttle_key,
                    fallback,
                    now,
                    min_interval=min_interval,
                )
                return fallback
            parsed = self._parse_structured(response)
            if not isinstance(parsed, dict):
                self._recent_plan_store(
                    throttle_key,
                    fallback,
                    now,
                    min_interval=min_interval,
                )
                return fallback
            parsed.setdefault("request_id", request_id)
            plan = self._apply_trend_plan_overrides(
                fallback,
                parsed,
                request_payload=payload_with_id,
            )
            plan.setdefault("request_id", request_id)
            self._cache_store(cache_key, plan)
            self._recent_plan_store(
                throttle_key,
                plan,
                now,
                min_interval=min_interval,
            )
            return plan

        if not self.budget.can_spend(estimate, kind="trend", model=self.model):
            self._log_budget_block("trend", estimate)
            self._recent_plan_store(
                throttle_key,
                fallback,
                now,
                min_interval=min_interval,
            )
            return fallback

        request_id = self._new_request_id("trend", throttle_key)
        payload_with_id = dict(user_payload)
        payload_with_id["request_id"] = request_id
        try:
            user_prompt = json.dumps(payload_with_id, sort_keys=True, separators=(",", ":"))
        except Exception:
            self._recent_plan_store(
                throttle_key,
                fallback,
                now,
                min_interval=min_interval,
            )
            return fallback
        meta = {"symbol": symbol, "context": "trend", "request_id": request_id}
        fallback["request_id"] = request_id

        cooldown_blocked = global_cooldown > 0 and (now - self._last_global_request) < global_cooldown
        if cooldown_blocked or self._active_pending() >= AI_CONCURRENCY:
            if not self._has_pending_capacity(throttle_key):
                self._recent_plan_store(
                    throttle_key,
                    fallback,
                    now,
                    min_interval=min_interval,
                )
                return self._pending_stub(
                    fallback,
                    "plan_queue_full",
                    "AI queue saturated; falling back to autonomous scan heuristics.",
                    throttle_key=throttle_key,
                    pending=False,
                )
            pending_info = {
                "future": None,
                "fallback": fallback,
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "user_payload": payload_with_id,
                "cache_key": cache_key,
                "kind": "trend",
                "estimate": estimate,
                "queued_at": now,
                "ready_after": now + max(0.5, global_cooldown or 0.5),
                "note": "Queued for AI planning",
                "notified": False,
                "request_meta": meta,
            }
            stub = self._pending_stub(
                fallback,
                "trend_pending",
                "Queued for AI planning",
                throttle_key=throttle_key,
                request_id=request_id,
            )
            pending_info["request_id"] = request_id
            pending_info["min_interval"] = float(min_interval)
            pending_info["global_cooldown"] = float(global_cooldown)
            self._pending_requests[throttle_key] = pending_info
            self._register_pending_key(throttle_key)
            return stub

        if not self._has_pending_capacity(throttle_key):
            self._recent_plan_store(
                throttle_key,
                fallback,
                now,
                min_interval=min_interval,
            )
            return self._pending_stub(
                fallback,
                "plan_queue_full",
                "AI queue saturated; falling back to autonomous scan heuristics.",
                throttle_key=throttle_key,
                pending=False,
            )

        future = self._dispatch_request(
            system_prompt,
            user_prompt,
            kind="trend",
            budget_estimate=estimate,
            request_meta=meta,
        )
        if not future:
            self._recent_plan_store(
                throttle_key,
                fallback,
                now,
                min_interval=min_interval,
            )
            return fallback
        self._pending_requests[throttle_key] = {
            "future": future,
            "fallback": fallback,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "user_payload": payload_with_id,
            "cache_key": cache_key,
            "kind": "trend",
            "estimate": estimate,
            "queued_at": now,
            "dispatched_at": now,
            "notified": False,
            "request_meta": meta,
            "request_id": request_id,
            "min_interval": float(min_interval),
            "global_cooldown": float(global_cooldown),
        }
        self._register_pending_key(throttle_key)
        self._last_global_request = now
        self._last_global_interval = global_cooldown
        self._attach_future_callback(throttle_key, future)
        stub = self._pending_stub(
            fallback,
            "trend_pending",
            "Waiting for AI plan response",
            throttle_key=throttle_key,
            request_id=request_id,
        )
        return stub

    def generate_postmortem(self, trade: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        opened = float(trade.get("opened_at", time.time()) or time.time())
        closed = float(trade.get("closed_at", time.time()) or time.time())
        duration = max(0.0, closed - opened)
        pnl = float(trade.get("pnl", 0.0) or 0.0)
        pnl_r = float(trade.get("pnl_r", 0.0) or 0.0)
        symbol = trade.get("symbol", "")
        side = trade.get("side", "")
        bucket = trade.get("bucket")
        fallback_text = (
            f"Closed {symbol} {side.lower()} after {max(duration/60.0, 0.1):.1f} minutes with {pnl:.2f} USDT ({pnl_r:.2f}R). "
            "Review entry timing, size bucket, and sentinel label to refine the policy."
        )
        fallback = {
            "analysis": self._ensure_bounds(fallback_text, fallback_text),
            "pnl": pnl,
            "pnl_r": pnl_r,
            "duration_s": duration,
            "bucket": bucket,
        }
        if not self.enabled:
            return fallback

        system_prompt = (
            "You are a trading coach. Analyse the trade JSON and respond strictly with compact JSON containing request_id, "
            "analysis (40-70 words), feature_scores (floats between -1 and 1), optional labels, volatility descriptor, "
            "execution descriptor, liquidity descriptor, and optional note. Use short descriptors like spike, compression, "
            "thin_liquidity and prefer numeric feature weights for consistent tuning."
        )
        request_id = self._new_request_id("postmortem", str(symbol or ""))
        payload_with_id = dict(trade)
        payload_with_id["request_id"] = request_id
        fallback["request_id"] = request_id
        user_prompt = json.dumps(payload_with_id, sort_keys=True, separators=(",", ":"))
        meta = {"symbol": symbol, "context": "postmortem", "request_id": request_id}
        response = self._chat(
            system_prompt,
            user_prompt,
            kind="postmortem",
            request_meta=meta,
        )
        labels: List[str] = []
        feature_scores: Dict[str, float] = {}
        if response:
            structured = self._parse_structured(response)
            if isinstance(structured, dict):
                structured.setdefault("request_id", request_id)
                analysis = structured.get("analysis") or structured.get("summary")
                if isinstance(analysis, str) and analysis.strip():
                    fallback["analysis"] = self._ensure_bounds(analysis, fallback_text)
                feats = structured.get("feature_scores") or structured.get("features")
                if isinstance(feats, dict):
                    feature_scores = {
                        str(k): float(v)
                        for k, v in feats.items()
                        if isinstance(v, (int, float))
                    }
                def _first_descriptor(*keys: str) -> Optional[str]:
                    for key in keys:
                        value = structured.get(key)
                        if isinstance(value, str) and value.strip():
                            return value.strip()
                        if isinstance(value, (list, tuple)):
                            for item in value:
                                if isinstance(item, str) and item.strip():
                                    return item.strip()
                    return None

                volatility_label = _first_descriptor(
                    "volatility", "volatility_type", "volatility_descriptor"
                )
                execution_label = _first_descriptor(
                    "execution", "execution_type", "execution_descriptor", "execution_quality"
                )
                liquidity_label = _first_descriptor(
                    "liquidity", "liquidity_type", "liquidity_descriptor"
                )
                if volatility_label:
                    score = _score_category(volatility_label, POSTMORTEM_VOLATILITY_SCORES)
                    if score is not None:
                        feature_scores["pm_volatility_bias"] = score
                    fallback["volatility"] = volatility_label
                if execution_label:
                    score = _score_category(execution_label, POSTMORTEM_EXECUTION_SCORES)
                    if score is not None:
                        feature_scores["pm_execution_quality"] = score
                    fallback["execution"] = execution_label
                if liquidity_label:
                    score = _score_category(liquidity_label, POSTMORTEM_LIQUIDITY_SCORES)
                    if score is not None:
                        feature_scores["pm_liquidity_profile"] = score
                    fallback["liquidity"] = liquidity_label
                labels_raw = structured.get("labels") or structured.get("tags")
                if isinstance(labels_raw, list):
                    labels = [str(item) for item in labels_raw if isinstance(item, (str, int, float))]
                note = structured.get("note") or structured.get("insight")
                if isinstance(note, str) and note.strip():
                    fallback["note"] = self._ensure_bounds(note, note)
            else:
                fallback["analysis"] = self._ensure_bounds(response, fallback_text)
        if not feature_scores:
            feature_scores = {}
        try:
            if self.postmortem_learning:
                self.postmortem_learning.register(symbol or "*", feature_scores, pnl_r=pnl_r)
        except Exception:
            pass
        try:
            if self.parameter_tuner:
                self.parameter_tuner.observe(trade, feature_scores)
        except Exception:
            pass
        try:
            if self.budget_learner:
                self.budget_learner.record_trade(trade)
        except Exception:
            pass
        if feature_scores:
            fallback["feature_scores"] = feature_scores
        if labels:
            fallback["labels"] = labels
        return fallback

    def budget_snapshot(self) -> Dict[str, Any]:
        return self.budget.snapshot()

# ========= Exchange =========
class PaperBroker:
    """Local futures simulator used when ``ASTER_PAPER`` is enabled.

    The implementation keeps track of positions, attached stop-loss /
    take-profit brackets and realized trade history. It is intentionally
    lightweight but provides deterministic fills so strategy experiments can
    be validated without hitting the live matching engine.
    """

    def __init__(self, exchange: "Exchange") -> None:
        self.exchange = exchange
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.closed: List[Dict[str, Any]] = []
        self.realized_pnl: float = 0.0
        self._order_seq = 1
        self._trade_seq = 1
        self.trades: List[Dict[str, Any]] = []

    def _next_order_id(self) -> int:
        oid = self._order_seq
        self._order_seq += 1
        return oid

    def _next_trade_id(self) -> int:
        tid = self._trade_seq
        self._trade_seq += 1
        return tid

    def _record_trade(
        self,
        *,
        symbol: str,
        side: str,
        qty: float,
        price: float,
        order_id: Optional[int] = None,
        realized_pnl: float = 0.0,
        commission: float = 0.0,
        timestamp: Optional[float] = None,
    ) -> Dict[str, Any]:
        trade_id = self._next_trade_id()
        ts = timestamp if timestamp is not None else time.time()
        payload = {
            "symbol": symbol,
            "id": trade_id,
            "tradeId": trade_id,
            "orderId": order_id or trade_id,
            "price": f"{float(price):.10f}",
            "qty": f"{float(qty):.10f}",
            "realizedPnl": f"{float(realized_pnl):.10f}",
            "commission": f"{float(commission):.10f}",
            "commissionAsset": QUOTE,
            "buyer": side.upper() == "BUY",
            "maker": False,
            "time": int(ts * 1000),
        }
        self.trades.append(payload)
        return payload

    @staticmethod
    def _decode_bracket_price(payload: Any) -> Optional[float]:
        if not payload:
            return None
        data: Any = payload
        if isinstance(payload, str):
            try:
                data = json.loads(payload)
            except (TypeError, ValueError):
                return None
        if not isinstance(data, dict):
            return None
        trigger = data.get("trigger") if isinstance(data.get("trigger"), dict) else {}
        price = trigger.get("price")
        try:
            return float(price)
        except (TypeError, ValueError):
            return None

    def _position(self, symbol: str) -> Dict[str, Any]:
        return self.positions.setdefault(
            symbol,
            {
                "qty": 0.0,
                "entry_price": 0.0,
                "side": "",
                "opened_at": 0.0,
                "stop_loss": None,
                "take_profit": None,
                "last_price": 0.0,
                "unrealized": 0.0,
            },
        )

    def _update_unrealized(self, pos: Dict[str, Any], mid: float) -> None:
        qty = float(pos.get("qty", 0.0) or 0.0)
        if abs(qty) <= 1e-12:
            pos["unrealized"] = 0.0
            pos["last_price"] = float(mid)
            return
        entry = float(pos.get("entry_price", 0.0) or 0.0)
        side = str(pos.get("side") or "").upper()
        pnl = (mid - entry) * qty if side == "BUY" else (entry - mid) * abs(qty)
        pos["unrealized"] = float(pnl)
        pos["last_price"] = float(mid)

    def update_quote(self, symbol: str, bid: float, ask: float) -> None:
        pos = self.positions.get(symbol)
        if not pos:
            return
        bid = float(bid or 0.0)
        ask = float(ask or 0.0)
        mid = 0.0
        if bid > 0 and ask > 0:
            mid = (bid + ask) / 2.0
        elif bid > 0:
            mid = bid
        elif ask > 0:
            mid = ask
        self._update_unrealized(pos, mid)
        side = str(pos.get("side") or "").upper()
        if not side:
            return
        stop_loss = pos.get("stop_loss")
        take_profit = pos.get("take_profit")
        triggered: Optional[Tuple[str, float]] = None
        if side == "BUY":
            if take_profit is not None and bid > 0 and bid >= take_profit:
                triggered = ("take_profit", float(take_profit))
            elif stop_loss is not None and bid > 0 and bid <= stop_loss:
                triggered = ("stop_loss", float(stop_loss))
        else:
            if take_profit is not None and ask > 0 and ask <= take_profit:
                triggered = ("take_profit", float(take_profit))
            elif stop_loss is not None and ask > 0 and ask >= stop_loss:
                triggered = ("stop_loss", float(stop_loss))
        if triggered:
            reason, exit_price = triggered
            self._close(symbol, exit_price, reason)

    def _close(self, symbol: str, exit_price: float, reason: str) -> None:
        pos = self.positions.get(symbol)
        if not pos:
            return
        qty = float(pos.get("qty", 0.0) or 0.0)
        if abs(qty) <= 1e-12:
            self.positions.pop(symbol, None)
            return
        entry = float(pos.get("entry_price", 0.0) or 0.0)
        side = str(pos.get("side") or "").upper() or ("BUY" if qty > 0 else "SELL")
        now = time.time()
        base_qty = abs(qty)
        if side == "BUY":
            pnl = (exit_price - entry) * base_qty
            risk_ref = pos.get("stop_loss", entry)
            risk = max(1e-9, abs(entry - float(risk_ref)) * base_qty)
        else:
            pnl = (entry - exit_price) * base_qty
            risk_ref = pos.get("stop_loss", entry)
            risk = max(1e-9, abs(entry - float(risk_ref)) * base_qty)
        r_mult = pnl / risk if risk > 0 else 0.0
        record = {
            "symbol": symbol,
            "side": side,
            "qty": base_qty,
            "entry": entry,
            "exit": float(exit_price),
            "pnl": float(pnl),
            "pnl_r": float(r_mult),
            "opened_at": float(pos.get("opened_at", now) or now),
            "closed_at": now,
            "bucket": pos.get("bucket"),
            "context": pos.get("ctx", {}),
            "reason": reason,
            "stop_loss": pos.get("stop_loss"),
            "take_profit": pos.get("take_profit"),
        }
        ai_meta = pos.get("ai")
        if ai_meta:
            record["ai"] = ai_meta
        self.realized_pnl += float(pnl)
        self.closed.append(record)
        exit_side = "SELL" if side == "BUY" else "BUY"
        self._record_trade(
            symbol=symbol,
            side=exit_side,
            qty=base_qty,
            price=float(exit_price),
            realized_pnl=float(pnl),
        )
        self.positions.pop(symbol, None)

    def _same_direction(self, existing_qty: float, delta: float) -> bool:
        return existing_qty * delta > 0

    def market_order(self, params: Dict[str, Any]) -> Dict[str, Any]:
        symbol = str(params.get("symbol") or "").upper()
        side = str(params.get("side") or "").upper()
        if not symbol or side not in {"BUY", "SELL"}:
            raise ValueError("paper mode requires symbol and side")
        try:
            qty = float(params.get("quantity") or params.get("origQty") or 0.0)
        except (TypeError, ValueError):
            qty = 0.0
        if qty <= 0:
            raise ValueError("quantity must be positive in paper mode")
        stop_loss = self._decode_bracket_price(params.get("stopLoss"))
        take_profit = self._decode_bracket_price(params.get("takeProfit"))
        raw = self.exchange._raw_get_book_ticker(symbol)
        bid = 0.0
        ask = 0.0
        if isinstance(raw, dict):
            try:
                bid = float(raw.get("bidPrice", 0.0) or 0.0)
            except (TypeError, ValueError):
                bid = 0.0
            try:
                ask = float(raw.get("askPrice", 0.0) or 0.0)
            except (TypeError, ValueError):
                ask = 0.0
        if side == "BUY":
            fill_price = ask if ask > 0 else (bid if bid > 0 else 0.0)
        else:
            fill_price = bid if bid > 0 else (ask if ask > 0 else 0.0)
        if fill_price <= 0:
            raise RuntimeError(f"No market data available for {symbol} in paper mode")
        signed_qty = qty if side == "BUY" else -qty
        pos = self._position(symbol)
        existing_qty = float(pos.get("qty", 0.0) or 0.0)
        now = time.time()
        if abs(existing_qty) <= 1e-12:
            pos.update(
                {
                    "qty": signed_qty,
                    "entry_price": float(fill_price),
                    "side": side,
                    "opened_at": now,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                }
            )
        elif self._same_direction(existing_qty, signed_qty):
            new_qty = existing_qty + signed_qty
            weight_old = abs(existing_qty)
            weight_new = abs(signed_qty)
            avg = 0.0
            if weight_old + weight_new > 0:
                avg = (
                    pos.get("entry_price", 0.0) * weight_old + fill_price * weight_new
                ) / (weight_old + weight_new)
            pos.update(
                {
                    "qty": new_qty,
                    "entry_price": float(avg),
                    "side": "BUY" if new_qty > 0 else "SELL",
                    "stop_loss": stop_loss if stop_loss is not None else pos.get("stop_loss"),
                    "take_profit": take_profit if take_profit is not None else pos.get("take_profit"),
                }
            )
        else:
            remaining = existing_qty + signed_qty
            closed_qty = min(abs(existing_qty), abs(signed_qty))
            flipped = abs(signed_qty) > abs(existing_qty)
            if closed_qty > 0:
                exit_reason = "manual_exit"
                self._close_partial(symbol, float(fill_price), closed_qty, exit_reason)
            if abs(remaining) > 1e-12:
                if flipped:
                    pos = self._position(symbol)
                    pos.update(
                        {
                            "qty": remaining,
                            "entry_price": float(fill_price),
                            "side": "BUY" if remaining > 0 else "SELL",
                            "opened_at": now,
                            "stop_loss": stop_loss,
                            "take_profit": take_profit,
                        }
                    )
                else:
                    pos = self.positions.get(symbol)
                    if pos:
                        pos["qty"] = remaining
                        pos["side"] = "BUY" if remaining > 0 else "SELL"
                        if stop_loss is not None:
                            pos["stop_loss"] = float(stop_loss)
                        if take_profit is not None:
                            pos["take_profit"] = float(take_profit)
            else:
                self.positions.pop(symbol, None)
        pos = self.positions.get(symbol)
        if pos:
            pos.setdefault("bucket", None)
            pos.setdefault("ctx", {})
        self._update_unrealized(self.positions.get(symbol, {}), fill_price)
        order_id = self._next_order_id()
        self._record_trade(
            symbol=symbol,
            side=side,
            qty=abs(signed_qty),
            price=float(fill_price),
            order_id=order_id,
        )
        return {
            "paper": True,
            "symbol": symbol,
            "orderId": order_id,
            "status": "FILLED",
            "avgPrice": float(fill_price),
            "executedQty": qty,
            "clientOrderId": f"paper-{order_id}",
            "side": side,
        }

    def _close_partial(self, symbol: str, fill_price: float, qty_closed: float, reason: str) -> None:
        pos = self.positions.get(symbol)
        if not pos:
            return
        qty = float(pos.get("qty", 0.0) or 0.0)
        if abs(qty) <= 1e-12:
            self.positions.pop(symbol, None)
            return
        entry = float(pos.get("entry_price", 0.0) or 0.0)
        side = str(pos.get("side") or "").upper() or ("BUY" if qty > 0 else "SELL")
        qty_left = abs(qty) - qty_closed
        if qty_left < -1e-12:
            qty_left = 0.0
        multiplier = 1.0 if side == "BUY" else -1.0
        pnl = (fill_price - entry) * qty_closed * multiplier
        risk_ref = pos.get("stop_loss", entry)
        risk = max(1e-9, abs(entry - float(risk_ref)) * qty_closed)
        r_mult = pnl / risk if risk > 0 else 0.0
        now = time.time()
        record = {
            "symbol": symbol,
            "side": side,
            "qty": qty_closed,
            "entry": entry,
            "exit": float(fill_price),
            "pnl": float(pnl),
            "pnl_r": float(r_mult),
            "opened_at": float(pos.get("opened_at", now) or now),
            "closed_at": now,
            "bucket": pos.get("bucket"),
            "context": pos.get("ctx", {}),
            "reason": reason,
            "stop_loss": pos.get("stop_loss"),
            "take_profit": pos.get("take_profit"),
        }
        ai_meta = pos.get("ai")
        if ai_meta:
            record["ai"] = ai_meta
        self.closed.append(record)
        self.realized_pnl += float(pnl)
        exit_side = "SELL" if side == "BUY" else "BUY"
        self._record_trade(
            symbol=symbol,
            side=exit_side,
            qty=float(qty_closed),
            price=float(fill_price),
            realized_pnl=float(pnl),
        )
        remaining_qty = multiplier * qty_left
        if qty_left <= 1e-12:
            self.positions.pop(symbol, None)
        else:
            pos["qty"] = remaining_qty
            pos["side"] = "BUY" if remaining_qty > 0 else "SELL"

    def cancel_brackets(self, symbol: str) -> None:
        pos = self.positions.get(symbol)
        if not pos:
            return
        pos["stop_loss"] = None
        pos["take_profit"] = None

    def register_brackets(
        self,
        symbol: str,
        side: str,
        qty: float,
        entry: float,
        stop: float,
        take: float,
        bucket: Optional[str] = None,
        ctx: Optional[Dict[str, Any]] = None,
        ai_meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        pos = self.positions.get(symbol)
        if not pos:
            return
        pos["stop_loss"] = float(stop)
        pos["take_profit"] = float(take)
        if bucket is not None:
            pos["bucket"] = bucket
        if ctx:
            pos["ctx"] = dict(ctx)
        if ai_meta:
            pos["ai"] = dict(ai_meta)

    def replace_take_profit(self, symbol: str, price: float) -> bool:
        pos = self.positions.get(symbol)
        if not pos:
            return False
        pos["take_profit"] = float(price)
        return True

    def position_risk(self) -> List[Dict[str, str]]:
        snapshot: List[Dict[str, str]] = []
        for symbol, pos in list(self.positions.items()):
            qty = float(pos.get("qty", 0.0) or 0.0)
            if abs(qty) <= 1e-12:
                continue
            entry = float(pos.get("entry_price", 0.0) or 0.0)
            unrealized = float(pos.get("unrealized", 0.0) or 0.0)
            snapshot.append(
                {
                    "symbol": symbol,
                    "positionAmt": f"{qty:.10f}",
                    "entryPrice": f"{entry:.10f}",
                    "unRealizedProfit": f"{unrealized:.10f}",
                }
            )
        return snapshot

    def consume_closed(self) -> List[Dict[str, Any]]:
        if not self.closed:
            return []
        records = list(self.closed)
        self.closed.clear()
        return records

    def user_trades(
        self,
        symbol: str,
        *,
        order_id: Optional[int] = None,
        from_id: Optional[int] = None,
        start_time: Optional[int] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        trades = [t for t in self.trades if t.get("symbol") == symbol]
        if order_id is not None:
            trades = [t for t in trades if int(t.get("orderId", 0)) == int(order_id)]
        if from_id is not None:
            trades = [t for t in trades if int(t.get("id", 0)) >= int(from_id)]
        if start_time is not None:
            trades = [t for t in trades if int(t.get("time", 0)) >= int(start_time)]
        trades.sort(key=lambda item: int(item.get("id", 0)))
        capped = max(1, min(int(limit), 1000))
        return trades[:capped]


class Exchange:
    def __init__(self, base: str, api_key: str, api_secret: str, recv_window: int = 10000):
        self.base = base.rstrip("/")
        self.api_key = api_key
        self.api_secret = api_secret
        self.recv_window = recv_window
        self.s = requests.Session()
        self._ts_skew_ms = 0
        self.timeout = HTTP_TIMEOUT
        self._max_retries = HTTP_RETRIES
        self._backoff = HTTP_BACKOFF
        self._paper: Optional[PaperBroker] = PaperBroker(self) if PAPER else None
        ws_env = os.getenv("ASTER_WS_BASE", "").strip()
        if ws_env:
            self.ws_base = ws_env.rstrip("/")
        elif self.base.startswith("https://"):
            self.ws_base = "wss://" + self.base[len("https://") :]
        elif self.base.startswith("http://"):
            self.ws_base = "ws://" + self.base[len("http://") :]
        else:
            self.ws_base = self.base

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/x-www-form-urlencoded"}
        if self.api_key:
            h["X-MBX-APIKEY"] = self.api_key
        return h

    def _sign(self, qs: str) -> str:
        return hmac.new(self.api_secret.encode(), qs.encode(), hashlib.sha256).hexdigest()

    def _ts(self) -> int:
        return int(time.time() * 1000 + self._ts_skew_ms)

    def _request_with_retry(self, func, *args, **kwargs):
        attempt = 0
        delay = self._backoff
        while True:
            try:
                kwargs.setdefault("timeout", self.timeout)
                return func(*args, **kwargs)
            except RequestException as exc:
                attempt += 1
                if attempt > max(0, self._max_retries):
                    raise
                sleep_for = delay if delay > 0 else 0.5 * attempt
                try:
                    log.debug(f"HTTP retry {attempt} for {args[0] if args else func}: {exc}")
                except Exception:
                    pass
                try:
                    time.sleep(sleep_for)
                except Exception:
                    pass
                if delay > 0:
                    delay *= 2.0

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base}{path}"
        r = self._request_with_retry(self.s.get, url, params=params or {})
        r.raise_for_status()
        return r.json()

    def signed(self, method: str, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        if not self.api_key or not self.api_secret:
            raise RuntimeError("API credentials missing for signed request")
        p = dict(params or {})
        p["timestamp"] = self._ts()
        p["recvWindow"] = self.recv_window
        ordered = [(k, p[k]) for k in sorted(p)]
        qs = urlencode(ordered, doseq=True)
        sig = self._sign(qs)
        url = f"{self.base}{path}?{qs}&signature={sig}"
        req = {"get": self.s.get, "post": self.s.post, "delete": self.s.delete}[method.lower()]
        r = self._request_with_retry(req, url, headers=self._headers())
        r.raise_for_status()
        return r.json()

    # Convenience
    def get_exchange_info(self) -> Any:
        return self.get("/fapi/v1/exchangeInfo")

    def get_ticker_24hr(self, symbol: Optional[str] = None) -> Any:
        if symbol:
            return self.get("/fapi/v1/ticker/24hr", {"symbol": symbol})
        return self.get("/fapi/v1/ticker/24hr")

    def get_klines(self, symbol: str, interval: str, limit: int) -> List[List[float]]:
        ks = self.get("/fapi/v1/klines", {"symbol": symbol, "interval": interval, "limit": limit})
        out = []
        for k in ks:
            out.append([float(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5]), float(k[7])])
        return out

    def _raw_get_book_ticker(self, symbol: str) -> Any:
        return self.get("/fapi/v1/ticker/bookTicker", {"symbol": symbol})

    def get_book_ticker(self, symbol: Optional[str] = None) -> Any:
        if symbol:
            data = self._raw_get_book_ticker(symbol)
            if PAPER and self._paper and isinstance(data, dict):
                try:
                    bid = float(data.get("bidPrice", 0.0) or 0.0)
                except (TypeError, ValueError):
                    bid = 0.0
                try:
                    ask = float(data.get("askPrice", 0.0) or 0.0)
                except (TypeError, ValueError):
                    ask = 0.0
                self._paper.update_quote(symbol, bid, ask)
            return data
        payload = self.get("/fapi/v1/ticker/bookTicker")
        if PAPER and self._paper and isinstance(payload, list):
            for entry in payload:
                if not isinstance(entry, dict):
                    continue
                sym = entry.get("symbol")
                if not sym:
                    continue
                try:
                    bid = float(entry.get("bidPrice", 0.0) or 0.0)
                except (TypeError, ValueError):
                    bid = 0.0
                try:
                    ask = float(entry.get("askPrice", 0.0) or 0.0)
                except (TypeError, ValueError):
                    ask = 0.0
                self._paper.update_quote(str(sym), bid, ask)
        return payload

    def get_order_book(self, symbol: str, *, limit: Optional[int] = None) -> Any:
        payload = {"symbol": symbol}
        if limit:
            payload["limit"] = max(5, min(int(limit), 1000))
        return self.get("/fapi/v1/depth", payload)

    def get_premium_index(self, symbol: Optional[str] = None) -> Any:
        params = {"symbol": symbol} if symbol else None
        if params:
            return self.get("/fapi/v1/premiumIndex", params)
        return self.get("/fapi/v1/premiumIndex")

    def get_position_risk(self) -> Any:
        if PAPER and self._paper:
            return self._paper.position_risk()
        return self.signed("get", "/fapi/v2/positionRisk", {})

    def get_open_orders(self, symbol: str) -> Any:
        if PAPER and self._paper:
            pos = self._paper.positions.get(symbol)
            if not pos:
                return []
            orders = []
            sl = pos.get("stop_loss")
            tp = pos.get("take_profit")
            if sl is not None:
                orders.append({"symbol": symbol, "type": "STOP_MARKET", "triggerPrice": sl})
            if tp is not None:
                orders.append({"symbol": symbol, "type": "TAKE_PROFIT_MARKET", "triggerPrice": tp})
            return orders
        return self.signed("get", "/fapi/v1/openOrders", {"symbol": symbol})

    def query_order(
        self,
        symbol: str,
        *,
        order_id: Optional[int] = None,
        client_order_id: Optional[str] = None,
    ) -> Any:
        payload: Dict[str, Any] = {"symbol": symbol}
        if order_id is not None:
            payload["orderId"] = str(int(order_id))
        elif client_order_id:
            payload["origClientOrderId"] = client_order_id
        else:
            raise ValueError("order_id or client_order_id required")
        if PAPER and self._paper:
            # Paper mode orders are executed immediately – synthesize status.
            trades = self._paper.user_trades(symbol, order_id=payload.get("orderId"))
            qty = 0.0
            price = 0.0
            if trades:
                for trade in trades:
                    q = _coerce_float(trade.get("qty")) or 0.0
                    p = _coerce_float(trade.get("price")) or 0.0
                    qty += q
                    price += p * q
            avg = price / qty if qty > 0 else 0.0
            return {
                "symbol": symbol,
                "orderId": payload.get("orderId"),
                "status": "FILLED" if qty > 0 else "NEW",
                "executedQty": f"{qty:.10f}",
                "avgPrice": f"{avg:.10f}",
                "updateTime": int(time.time() * 1000),
            }
        return self.signed("get", "/fapi/v1/order", payload)

    def cancel_order(self, symbol: str, order_id: int) -> Any:
        if PAPER and self._paper:
            self._paper.cancel_brackets(symbol)
            return {"paper": True, "symbol": symbol, "orderId": int(order_id)}
        payload = {"symbol": symbol, "orderId": str(int(order_id))}
        return self.signed("delete", "/fapi/v1/order", payload)

    def post_order(self, params: Dict[str, Any]) -> Any:
        if PAPER and self._paper:
            return self._paper.market_order(params)
        try:
            return self.signed("post", "/fapi/v1/order", params)
        except requests.HTTPError as exc:
            if any(k in params for k in ("stopLoss", "takeProfit")):
                context_text = ""
                if exc.response is not None:
                    try:
                        payload = exc.response.json()
                        context_text = json.dumps(payload)[:160]
                    except ValueError:
                        context_text = (exc.response.text or "")[:160]
                context_lower = context_text.lower()
                if context_lower and not any(
                    hint in context_lower for hint in ("stoploss", "takeprofit", "trigger", "closeposition")
                ):
                    raise
                log.debug(
                    "Entry order rejected with bracket payloads (will retry without them): %s",
                    context_text,
                )
                stripped = {k: v for k, v in params.items() if k not in {"stopLoss", "takeProfit"}}
                if stripped != params:
                    return self.signed("post", "/fapi/v1/order", stripped)
            raise

    def cancel_all(self, symbol: str) -> Any:
        if PAPER and self._paper:
            self._paper.cancel_brackets(symbol)
            return {"paper": True, "cancel": symbol}
        return self.signed("delete", "/fapi/v1/allOpenOrders", {"symbol": symbol})

    def set_leverage(self, symbol: str, leverage: float) -> Any:
        if leverage <= 0:
            raise ValueError("leverage must be positive")
        if PAPER and self._paper:
            return {"paper": True, "symbol": symbol, "leverage": leverage}
        payload = {"symbol": symbol, "leverage": int(max(1, round(leverage)))}
        return self.signed("post", "/fapi/v1/leverage", payload)

    def paper_register_brackets(
        self,
        symbol: str,
        side: str,
        qty: float,
        entry: float,
        stop: float,
        take: float,
        *,
        bucket: Optional[str] = None,
        ctx: Optional[Dict[str, Any]] = None,
        ai_meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not (PAPER and self._paper):
            return
        self._paper.register_brackets(symbol, side, qty, entry, stop, take, bucket=bucket, ctx=ctx, ai_meta=ai_meta)

    def paper_consume_closed(self) -> List[Dict[str, Any]]:
        if not (PAPER and self._paper):
            return []
        return self._paper.consume_closed()

    def paper_replace_take_profit(self, symbol: str, price: float) -> bool:
        if not (PAPER and self._paper):
            return False
        return self._paper.replace_take_profit(symbol, price)

    def get_user_trades(
        self,
        symbol: str,
        *,
        order_id: Optional[int] = None,
        from_id: Optional[int] = None,
        start_time: Optional[int] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        if PAPER and self._paper:
            return self._paper.user_trades(
                symbol,
                order_id=order_id,
                from_id=from_id,
                start_time=start_time,
                limit=limit,
            )
        payload: Dict[str, Any] = {"symbol": symbol, "limit": max(1, min(int(limit), 1000))}
        if order_id is not None:
            payload["orderId"] = int(order_id)
        if from_id is not None:
            payload["fromId"] = int(from_id)
        if start_time is not None:
            payload["startTime"] = int(start_time)
        return self.signed("get", "/fapi/v1/userTrades", payload)

    def create_listen_key(self) -> Optional[str]:
        if PAPER and self._paper:
            return f"paper-{uuid.uuid4().hex}"
        url = f"{self.base}/fapi/v1/listenKey"
        r = self._request_with_retry(self.s.post, url, headers=self._headers())
        r.raise_for_status()
        data = r.json()
        return data.get("listenKey")

    def keepalive_listen_key(self, listen_key: str) -> None:
        if PAPER and self._paper:
            return
        url = f"{self.base}/fapi/v1/listenKey"
        self._request_with_retry(
            self.s.put,
            url,
            headers=self._headers(),
            data={"listenKey": listen_key},
        )

    def close_listen_key(self, listen_key: str) -> None:
        if PAPER and self._paper:
            return
        url = f"{self.base}/fapi/v1/listenKey"
        self._request_with_retry(
            self.s.delete,
            url,
            headers=self._headers(),
            data={"listenKey": listen_key},
        )

    def await_order_fill(
        self,
        symbol: str,
        order_info: Optional[Dict[str, Any]],
        *,
        timeout: float = 6.0,
        poll_interval: float = 0.25,
    ) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        if not order_info:
            return None, []
        order_id = _coerce_int(order_info.get("orderId"))
        client_order_id = order_info.get("clientOrderId")
        if PAPER and self._paper:
            trades = self._paper.user_trades(symbol, order_id=order_id)
            return order_info, trades
        deadline = time.time() + max(0.5, timeout)
        latest = dict(order_info)
        while time.time() < deadline:
            status = str(latest.get("status") or "").upper()
            executed = _coerce_float(latest.get("executedQty")) or 0.0
            if status in {"FILLED", "PARTIALLY_FILLED"} and executed > 0:
                break
            try:
                latest = self.query_order(
                    symbol,
                    order_id=order_id,
                    client_order_id=client_order_id,
                )
            except Exception as exc:
                log.debug(f"order status poll failed for {symbol}: {exc}")
            time.sleep(poll_interval)
        trades: List[Dict[str, Any]] = []
        try:
            trades = self.get_user_trades(symbol, order_id=order_id)
        except Exception as exc:
            log.debug(f"userTrades fetch failed for {symbol}: {exc}")
        return latest, trades


class UserDataStream:
    def __init__(
        self,
        exchange: Exchange,
        *,
        on_execution: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_account: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        self.exchange = exchange
        self._on_execution = on_execution
        self._on_account = on_account
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._ws_thread: Optional[threading.Thread] = None
        self._ws_app: Any = None
        self._listen_key: Optional[str] = None
        self._last_keepalive = 0.0
        self._keepalive_interval = float(os.getenv("ASTER_WS_KEEPALIVE", "1200") or 1200)
        self._reconnect_delay = 5.0
        path = os.getenv("ASTER_WS_USER_PATH", "/ws/")
        self._ws_path = path if path.startswith("/") else f"/{path}"

    def start(self) -> None:
        if websocket is None:
            log.debug("websocket-client package not available; user stream disabled")
            return
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="user-data-stream", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._ws_app is not None:
            try:
                self._ws_app.close()
            except Exception:
                pass
        if self._ws_thread and self._ws_thread.is_alive():
            self._ws_thread.join(timeout=2.0)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        if self._listen_key:
            try:
                self.exchange.close_listen_key(self._listen_key)
            except Exception:
                pass
        self._listen_key = None

    def _build_url(self, listen_key: str) -> str:
        base = self.exchange.ws_base.rstrip("/")
        path = self._ws_path
        if not path.endswith("/"):
            path = f"{path}/"
        return f"{base}{path}{listen_key}"

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                if not self._listen_key:
                    self._listen_key = self.exchange.create_listen_key()
                    self._last_keepalive = time.time()
                if not self._listen_key:
                    time.sleep(self._reconnect_delay)
                    continue
                url = self._build_url(self._listen_key)
                self._run_socket(url)
            except Exception as exc:
                log.debug(f"user stream failure: {exc}")
            if self._stop.is_set():
                break
            time.sleep(self._reconnect_delay)

    def _run_socket(self, url: str) -> None:
        if websocket is None:
            return

        def _on_message(_ws, message: str) -> None:
            if self._stop.is_set():
                return
            try:
                payload = json.loads(message)
            except ValueError:
                return
            self._handle_payload(payload)

        def _on_error(_ws, error: Any) -> None:
            log.debug(f"user stream error: {error}")

        def _on_close(_ws, *_args) -> None:
            log.debug("user stream closed")

        self._ws_app = websocket.WebSocketApp(
            url,
            on_message=_on_message,
            on_error=_on_error,
            on_close=_on_close,
        )

        self._ws_thread = threading.Thread(
            target=lambda: self._ws_app.run_forever(ping_interval=30, ping_timeout=10),
            name="user-data-ws",
            daemon=True,
        )
        self._ws_thread.start()

        while not self._stop.is_set():
            if self._ws_thread and not self._ws_thread.is_alive():
                break
            now = time.time()
            if self._listen_key and (now - self._last_keepalive) > max(60.0, self._keepalive_interval):
                try:
                    self.exchange.keepalive_listen_key(self._listen_key)
                    self._last_keepalive = now
                except Exception as exc:
                    log.debug(f"user stream keepalive failed: {exc}")
            time.sleep(5.0)

    def _handle_payload(self, payload: Dict[str, Any]) -> None:
        event_type = str(payload.get("e") or "").upper()
        event_time = payload.get("E")
        if event_type == "ORDER_TRADE_UPDATE":
            order = payload.get("o") or {}
            data = {
                "symbol": order.get("s"),
                "status": order.get("X"),
                "side": order.get("S"),
                "orderId": order.get("i"),
                "clientOrderId": order.get("c"),
                "executedQty": order.get("z"),
                "avgPrice": order.get("ap"),
                "lastQty": order.get("l"),
                "lastPrice": order.get("L"),
                "commission": order.get("n"),
                "realizedPnl": order.get("rp"),
                "tradeId": order.get("t"),
                "tradeTime": order.get("T"),
                "event_time": event_time,
            }
            if self._on_execution:
                try:
                    self._on_execution(data)
                except Exception as exc:
                    log.debug(f"execution callback failed: {exc}")
        elif event_type == "ACCOUNT_UPDATE":
            account = payload.get("a") or {}
            data = {
                "positions": account.get("P") or [],
                "balances": account.get("B") or [],
                "event_time": event_time,
            }
            if self._on_account:
                try:
                    self._on_account(data)
                except Exception as exc:
                    log.debug(f"account callback failed: {exc}")
# ========= Universe =========
class SymbolUniverse:
    def __init__(
        self,
        exchange: Exchange,
        quote: str,
        max_n: int,
        exclude: set,
        rotate: bool,
        include: Optional[List[str]] = None,
    ):
        self.exchange = exchange
        self.quote = quote
        self.max_n = int(max_n)
        self.rotate = bool(rotate)
        self.include = [str(sym).upper() for sym in include] if include else []
        # exclude kann später noch erweitert werden (siehe Bot.setup)
        self.exclude: Set[str] = {str(sym).upper() for sym in (exclude or set())}
        self._cursor = 0
        self._universe_snapshot: List[str] = []

    def _normalize_symbols(self, symbols: Sequence[Dict[str, Any]]) -> List[str]:
        normalized: List[str] = []
        for entry in symbols:
            try:
                if entry.get("quoteAsset") != self.quote:
                    continue
                symbol = str(entry.get("symbol") or "").upper()
                if symbol:
                    normalized.append(symbol)
            except Exception:
                continue
        return normalized

    def refresh(self) -> List[str]:
        try:
            info = self.exchange.get_exchange_info()
            syms = self._normalize_symbols(info.get("symbols", [])) if isinstance(info, dict) else []
        except Exception:
            syms = []

        if not syms:
            return []

        include_index: Dict[str, int] = {}
        if self.include:
            include_index = {sym: idx for idx, sym in enumerate(self.include)}
            syms = [s for s in syms if s in include_index]
            syms.sort(key=lambda s: include_index.get(s, len(include_index)))
        else:
            syms.sort()

        if self.exclude:
            exclude_normalized = {str(sym).upper() for sym in self.exclude}
            syms = [s for s in syms if s not in exclude_normalized]

        if syms != self._universe_snapshot:
            self._universe_snapshot = list(syms)
            self._cursor = 0

        if self.max_n <= 0 or len(syms) <= self.max_n:
            if not self.rotate:
                self._cursor = 0
            return list(syms)

        if not self.rotate:
            return list(syms[: self.max_n])

        start = self._cursor % len(syms)
        take = min(self.max_n, len(syms))
        selected: List[str] = []
        idx = start
        for _ in range(take):
            selected.append(syms[idx])
            idx = (idx + 1) % len(syms)
        self._cursor = (start + take) % len(syms)
        return selected

# ========= Risk =========
class RiskManager:
    def __init__(
        self,
        exchange: Exchange,
        default_notional: float = DEFAULT_NOTIONAL,
        *,
        state: Optional[Dict[str, Any]] = None,
    ):
        self.exchange = exchange
        self.default_notional = default_notional
        self.symbol_filters: Dict[str, Dict[str, Any]] = {}
        # /balance Cache
        self._equity: Optional[float] = None
        self._equity_ts: float = 0.0
        self._equity_ttl = 10  # s
        self.state = state if isinstance(state, dict) else None

    def load_filters(self) -> None:
        try:
            info = self.exchange.get_exchange_info()
            filt: Dict[str, Dict[str, Any]] = {}
            bracket_caps: Dict[str, float] = {}
            if getattr(self.exchange, "api_key", None) and getattr(self.exchange, "api_secret", None):
                try:
                    brackets = self.exchange.signed("get", "/fapi/v1/leverageBracket", {})
                except Exception as exc:
                    log.debug(f"leverage bracket fetch failed: {exc}")
                else:
                    if isinstance(brackets, list):
                        for entry in brackets:
                            symbol_key = str(
                                entry.get("symbol")
                                or entry.get("pair")
                                or entry.get("symbolPair")
                                or ""
                            ).upper()
                            if not symbol_key:
                                continue
                            ladder = entry.get("brackets") or entry.get("leverageBrackets")
                            if not isinstance(ladder, list) or not ladder:
                                continue
                            try:
                                top = ladder[0]
                            except Exception:
                                continue
                            cap = _coerce_positive_float(
                                top.get("initialLeverage")
                                or top.get("maxLeverage")
                                or top.get("leverage")
                            )
                            if cap > 0:
                                bracket_caps[symbol_key] = cap
            for s in info.get("symbols", []):
                sym = s.get("symbol", "")
                fdict = {f.get("filterType"): f for f in s.get("filters", [])}
                lot = fdict.get("LOT_SIZE", {})
                price = fdict.get("PRICE_FILTER", {})
                max_leverage = _coerce_positive_float(s.get("maxLeverage"))
                if max_leverage <= 0:
                    lev_filter = fdict.get("LEVERAGE") or fdict.get("LEVERAGE_FILTER")
                    if isinstance(lev_filter, dict):
                        max_leverage = _coerce_positive_float(lev_filter.get("maxLeverage"))
                if max_leverage <= 0 and sym and sym in bracket_caps:
                    max_leverage = bracket_caps.get(sym, 0.0)
                filt[sym] = {
                    "minQty": float(lot.get("minQty", "0") or 0),
                    "maxQty": float(lot.get("maxQty", "0") or 0),
                    "stepSize": float(lot.get("stepSize", "0.0001") or 0.0001),
                    "minPrice": float(price.get("minPrice", "0") or 0),
                    "maxPrice": float(price.get("maxPrice", "0") or 0),
                    "tickSize": float(price.get("tickSize", "0.0001") or 0.0001),
                    "maxLeverage": max_leverage,
                    "defaultLeverage": _coerce_positive_float(s.get("defaultLeverage")),
                }
            if bracket_caps:
                for sym, cap in bracket_caps.items():
                    bucket = filt.setdefault(sym, {})
                    stored = _coerce_positive_float(bucket.get("maxLeverage"))
                    if cap > stored:
                        bucket["maxLeverage"] = cap
            self.symbol_filters = filt
        except Exception as e:
            log.warning(f"load_filters failed: {e}")

    def _equity_cached(self) -> float:
        now = time.time()
        if self._equity is not None and (now - self._equity_ts) < self._equity_ttl:
            return float(self._equity)
        try:
            bal = self.exchange.signed("get", "/fapi/v2/balance", {})
            eq = 0.0
            for b in bal:
                if b.get("asset") == QUOTE:
                    eq = float(b.get("balance", 0.0) or 0.0)
                    break
            self._equity = eq; self._equity_ts = now
            return float(eq)
        except Exception:
            return 0.0

    def attach_state(self, state: Optional[Dict[str, Any]]) -> None:
        self.state = state if isinstance(state, dict) else None

    def _drawdown_factor(self) -> float:
        if not self.state:
            return 1.0
        history = self.state.get("trade_history")
        if not isinstance(history, list) or not history:
            return 1.0
        running = 0.0
        peak = 0.0
        trough = 0.0
        for trade in history[-120:]:
            try:
                pnl = float(trade.get("pnl", 0.0) or 0.0)
            except Exception:
                pnl = 0.0
            running += pnl
            if running > peak:
                peak = running
            if running < trough:
                trough = running
        drawdown = peak - trough
        if peak <= 0:
            return 1.0
        ratio = max(0.0, min(1.0, drawdown / max(abs(peak), 1e-9)))
        return max(0.45, 1.0 - ratio * 0.55)

    def max_leverage_for(self, symbol: str) -> float:
        filters = self.symbol_filters.get(symbol, {}) if isinstance(self.symbol_filters, dict) else {}
        cap = _coerce_positive_float(filters.get("maxLeverage"))
        if cap <= 0:
            cap = _coerce_positive_float(filters.get("defaultLeverage"))
        if cap <= 0:
            cap = _coerce_positive_float(filters.get("initialLeverage"))
        if cap <= 0:
            cap = _coerce_positive_float(filters.get("leverageCap"))
        if cap <= 0:
            cap = _coerce_positive_float(filters.get("maxBracketLeverage"))
        if cap <= 0 and math.isfinite(LEVERAGE) and LEVERAGE > 0:
            cap = LEVERAGE
        if cap <= 0:
            cap = 20.0
        if math.isfinite(LEVERAGE) and LEVERAGE > 0:
            return max(1.0, min(LEVERAGE, cap))
        return max(1.0, cap)

    def compute_qty(self, symbol: str, entry: float, sl: float, size_mult: float) -> float:
        step = float(self.symbol_filters.get(symbol, {}).get("stepSize", 0.0001) or 0.0001)
        # a) Basiskapital
        notional_base = self.default_notional * max(0.0, size_mult)
        # b) risiko-konsistent (1R = Entry–SL)
        risk_notional = 0.0
        try:
            stop_dist = abs(entry - sl)
            if stop_dist > 0:
                equity = self._equity_cached()
                target_loss = RISK_PER_TRADE * max(1.0, equity)
                risk_notional = target_loss / max(stop_dist / max(entry, 1e-9), 1e-9)
        except Exception:
            risk_notional = 0.0
        if risk_notional > 0:
            notional = risk_notional
            if notional_base > 0:
                lower = notional_base * 0.4
                upper = notional_base * 2.2
                notional = max(notional, lower)
                notional = min(notional, upper)
                notional = (notional * 0.7) + (notional_base * 0.3)
        else:
            notional = notional_base
        notional = max(MIN_NOTIONAL_ENV, notional)
        notional *= self._drawdown_factor()
        notional = max(MIN_NOTIONAL_ENV, notional)
        # c) Cap via Leverage & Equity-Fraction
        equity = self._equity_cached()
        leverage_cap = self.max_leverage_for(symbol)
        dyn_cap = float("inf")
        if equity > 0 and math.isfinite(leverage_cap) and leverage_cap > 0:
            dyn_cap = equity * leverage_cap * EQUITY_FRACTION
        if MAX_NOTIONAL_USDT > 0:
            dyn_cap = min(dyn_cap, MAX_NOTIONAL_USDT)
        notional = min(notional, dyn_cap)
        qty = notional / max(entry, 1e-9)
        # d) Runden auf stepSize
        qty = max(0.0, math.floor(qty / step) * step)
        # e) minNotional
        if entry * qty < MIN_NOTIONAL_ENV:
            return 0.0
        # f) maxQty, falls vorhanden
        maxQty = float(self.symbol_filters.get(symbol, {}).get("maxQty", 0.0) or 0.0)
        if maxQty and qty > maxQty:
            qty = maxQty
            qty = max(0.0, math.floor(qty / step) * step)
        return qty

# ========= Strategy =========
class Strategy:
    def __init__(
        self,
        exchange: Exchange,
        decision_tracker: Optional["DecisionTracker"] = None,
        state: Optional[Dict[str, Any]] = None,
    ):
        self.exchange = exchange
        self.decision_tracker = decision_tracker
        self.min_quote_vol = MIN_QUOTE_VOL
        self.spread_bps_max = SPREAD_BPS_MAX
        self.wickiness_max = WICKINESS_MAX
        self.state = state if isinstance(state, dict) else None
        self._tech_snapshot_dirty = False
        # 24h Ticker Cache
        self._t24_cache: Dict[str, dict] = {}
        self._t24_ts = 0.0
        self._t24_ttl = 120
        self._premium_cache: Dict[str, dict] = {}
        self._premium_ts = 0.0
        self._premium_ttl = 60
        self._kl_cache: Dict[Tuple[str, str, int], Tuple[float, Tuple[Tuple[float, ...], ...]]] = {}
        self._kl_cache_ttl = KLINE_CACHE_SEC
        self._kl_cache_hits = 0
        self._kl_cache_miss = 0
        self._symbol_score_cache: Dict[str, Dict[str, float]] = {}
        self.orderbook_limit = ORDERBOOK_DEPTH_LIMIT
        self._orderbook_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
        self._orderbook_budget_max = ORDERBOOK_ON_DEMAND
        self._orderbook_budget = 0
        self._orderbook_ttl = ORDERBOOK_TTL
        if self.state:
            scores = self.state.get("universe_scores")
            if isinstance(scores, dict):
                hydrated: Dict[str, Dict[str, float]] = {}
                for sym, record in scores.items():
                    if not isinstance(sym, str) or not sym:
                        continue
                    if not isinstance(record, dict):
                        continue
                    try:
                        hydrated[sym] = {
                            "score": float(record.get("score", 0.0) or 0.0),
                            "qv_score": float(record.get("qv", record.get("qv_score", 0.0)) or 0.0),
                            "perf_bias": float(record.get("perf_bias", 1.0) or 1.0),
                            "budget_bias": float(record.get("budget_bias", 1.0) or 1.0),
                        }
                    except Exception:
                        continue
                if hydrated:
                    self._symbol_score_cache = hydrated

    @property
    def tech_snapshot_dirty(self) -> bool:
        return bool(self._tech_snapshot_dirty)

    def clear_tech_snapshot_dirty(self) -> None:
        self._tech_snapshot_dirty = False

    @staticmethod
    def _playbook_timestamp(value: Any) -> float:
        if isinstance(value, (int, float)):
            try:
                return float(value)
            except (TypeError, ValueError):
                return 0.0
        if isinstance(value, str):
            try:
                cleaned = value.replace("Z", "+00:00") if value.endswith("Z") else value
                return datetime.fromisoformat(cleaned).timestamp()
            except Exception:
                return 0.0
        return 0.0

    def _playbook_sentinel_sample(
        self, sentinel_state: Any, *, limit: int = 8
    ) -> Dict[str, Any]:
        if not isinstance(sentinel_state, dict):
            return {}
        entries: List[Tuple[float, str, Dict[str, Any]]] = []
        for sym, payload in sentinel_state.items():
            if not sym or not isinstance(payload, dict):
                continue
            ts = self._playbook_timestamp(payload.get("updated"))
            entries.append((ts, sym, payload))
        if not entries:
            return {}
        entries.sort(key=lambda item: item[0], reverse=True)
        trimmed: Dict[str, Any] = {}
        for _, sym, payload in entries[: max(limit, 1)]:
            item: Dict[str, Any] = {}
            try:
                item["event_risk"] = float(payload.get("event_risk", 0.0) or 0.0)
            except Exception:
                pass
            try:
                item["hype_score"] = float(payload.get("hype_score", 0.0) or 0.0)
            except Exception:
                pass
            label = payload.get("label")
            if isinstance(label, str):
                item["label"] = label
            updated = payload.get("updated")
            if isinstance(updated, (int, float, str)):
                item["updated"] = updated
            actions = payload.get("actions")
            if isinstance(actions, dict):
                reduced: Dict[str, Any] = {}
                if "size_factor" in actions:
                    try:
                        reduced["size_factor"] = float(actions.get("size_factor", 0.0) or 0.0)
                    except Exception:
                        pass
                if "hard_block" in actions:
                    reduced["hard_block"] = bool(actions.get("hard_block"))
                if reduced:
                    item["actions"] = reduced
            signals = payload.get("signals")
            if isinstance(signals, dict):
                for key in (
                    "sentinel_onchain_pressure",
                    "sentinel_social_sentiment",
                    "sentinel_options_skew",
                ):
                    try:
                        value = float(signals.get(key, 0.0) or 0.0)
                    except Exception:
                        continue
                    if abs(value) > 1e-4:
                        item[key] = value
            events = payload.get("events")
            if isinstance(events, list):
                reduced_events: List[Dict[str, Any]] = []
                for event in events[:2]:
                    if not isinstance(event, dict):
                        continue
                    reduced_event: Dict[str, Any] = {}
                    title = (
                        event.get("title")
                        or event.get("name")
                        or event.get("event")
                        or event.get("headline")
                    )
                    if isinstance(title, str):
                        reduced_event["title"] = title
                    severity = event.get("severity")
                    if severity is not None:
                        reduced_event["severity"] = severity
                    when = event.get("time") or event.get("ts") or event.get("timestamp")
                    if isinstance(when, (int, float, str)):
                        reduced_event["time"] = when
                    if reduced_event:
                        reduced_events.append(reduced_event)
                if reduced_events:
                    item["events"] = reduced_events
            if item:
                trimmed[sym] = item
        return trimmed

    def _playbook_regime_indicators(
        self,
        sentinel_state: Any,
        budget_snapshot: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, float]:
        if not isinstance(sentinel_state, dict) or not sentinel_state:
            sentinel_state = {}
        agg_event: List[float] = []
        agg_hype: List[float] = []
        agg_onchain: List[float] = []
        agg_social: List[float] = []
        agg_options: List[float] = []
        for payload in sentinel_state.values():
            if not isinstance(payload, dict):
                continue
            try:
                agg_event.append(float(payload.get("event_risk", 0.0) or 0.0))
            except Exception:
                pass
            try:
                agg_hype.append(float(payload.get("hype_score", 0.0) or 0.0))
            except Exception:
                pass
            signals = payload.get("signals")
            if isinstance(signals, dict):
                for collection, key in (
                    (agg_onchain, "sentinel_onchain_pressure"),
                    (agg_social, "sentinel_social_sentiment"),
                    (agg_options, "sentinel_options_skew"),
                ):
                    try:
                        value = float(signals.get(key, 0.0) or 0.0)
                    except Exception:
                        continue
                    collection.append(value)
        regime: Dict[str, float] = {}
        if agg_event:
            regime["playbook_regime_volatility"] = clamp(sum(agg_event) / len(agg_event), 0.0, 1.0)
        if agg_hype:
            regime["playbook_regime_activity"] = clamp(sum(agg_hype) / len(agg_hype), 0.0, 1.0)
        if agg_onchain:
            regime["playbook_regime_liquidity"] = clamp(sum(agg_onchain) / len(agg_onchain), -1.0, 1.0)
        if agg_social:
            regime["playbook_regime_sentiment"] = clamp(sum(agg_social) / len(agg_social), -1.0, 1.0)
        if agg_options:
            regime["playbook_regime_skew"] = clamp(sum(agg_options) / len(agg_options), -1.0, 1.0)
        if isinstance(budget_snapshot, dict) and budget_snapshot:
            try:
                limit = float(budget_snapshot.get("limit", 0.0) or 0.0)
                remaining = float(budget_snapshot.get("remaining", 0.0) or 0.0)
            except (TypeError, ValueError):
                limit = 0.0
                remaining = 0.0
            if limit > 0:
                utilization = clamp(1.0 - remaining / max(limit, 1e-9), 0.0, 1.0)
                regime["playbook_regime_budget_util"] = utilization
        return regime

    def _playbook_snapshot(self) -> Dict[str, Any]:
        tech_state = self.state.get("technical_snapshot") if self.state else None
        if isinstance(tech_state, dict):
            sample_items = list(
                sorted(
                    tech_state.items(),
                    key=lambda item: float(item[1].get("ts", 0.0))
                    if isinstance(item[1], dict)
                    else 0.0,
                )
            )
            technical_sample = {
                key: value for key, value in sample_items[-6:]
            }
        else:
            technical_sample = {}

        sentinel_state = self.state.get("sentinel", {}) if self.state else {}
        sentinel_sample = self._playbook_sentinel_sample(sentinel_state)

        budget_snapshot: Dict[str, Any] = {}
        tracker = getattr(self, "budget_tracker", None)
        if tracker is not None:
            try:
                budget_snapshot = tracker.snapshot()
            except Exception:
                budget_snapshot = {}

        recent_trades: List[Any] = []
        if self.state:
            trades = self.state.get("trade_history")
            if isinstance(trades, list):
                recent_trades = trades[-6:]

        regime = self._playbook_regime_indicators(sentinel_state, budget_snapshot)

        snapshot = {
            "timestamp": time.time(),
            "technical": technical_sample,
            "sentinel": sentinel_sample,
            "budget": budget_snapshot,
            "recent_trades": recent_trades,
        }
        if regime:
            snapshot["regime"] = regime
        if self.playbook_manager:
            try:
                active_playbook = self.playbook_manager.active()
            except Exception:
                active_playbook = {}
            if isinstance(active_playbook, dict) and active_playbook:
                playbook_summary: Dict[str, Any] = {
                    "mode": active_playbook.get("mode"),
                    "bias": active_playbook.get("bias"),
                    "sl_bias": active_playbook.get("sl_bias"),
                    "tp_bias": active_playbook.get("tp_bias"),
                    "size_bias": active_playbook.get("size_bias"),
                    "reason": active_playbook.get("reason"),
                    "confidence": active_playbook.get("confidence"),
                }
                strategy_blob = active_playbook.get("strategy")
                if isinstance(strategy_blob, dict) and strategy_blob:
                    playbook_summary["strategy"] = strategy_blob
                snapshot["playbook"] = playbook_summary
        return snapshot

    def _klines_cached(self, symbol: str, interval: str, limit: int) -> Sequence[Sequence[float]]:
        key = (symbol, interval, int(limit))
        now = time.time()
        entry = self._kl_cache.get(key)
        if entry and (now - entry[0]) < self._kl_cache_ttl:
            self._kl_cache_hits += 1
            return entry[1]
        try:
            fresh = self.exchange.get_klines(symbol, interval, limit)
        except Exception:
            if entry:
                self._kl_cache_hits += 1
                log.debug(f"kl-cache fallback {symbol} {interval}")
                return entry[1]
            raise
        self._kl_cache_miss += 1
        clone = tuple(tuple(row) for row in fresh) if fresh else tuple()
        if clone:
            self._kl_cache[key] = (now, clone)
        elif entry:
            self._kl_cache.pop(key, None)
        if self._kl_cache_miss % 50 == 0 and len(self._kl_cache) > 200:
            stale = [k for k, (ts, _) in self._kl_cache.items() if (now - ts) >= self._kl_cache_ttl]
            for k in stale:
                self._kl_cache.pop(k, None)
        return clone

    def prime_ticker_cache(
        self, payload: Dict[str, Dict[str, Any]], *, timestamp: Optional[float] = None
    ) -> None:
        if not payload:
            return
        now = float(timestamp or time.time())
        sanitized: Dict[str, Dict[str, Any]] = {}
        for sym, rec in payload.items():
            if not sym:
                continue
            if not isinstance(rec, dict):
                continue
            sanitized[sym] = dict(rec)
        if not sanitized:
            return
        if not self._t24_cache:
            self._t24_cache = sanitized
        else:
            self._t24_cache.update(sanitized)
        self._t24_ts = now

    def _ticker_24(self, symbol: str) -> Optional[Dict[str, Any]]:
        now = time.time()
        try:
            if (now - self._t24_ts) > self._t24_ttl or not self._t24_cache:
                data = self.exchange.get_ticker_24hr()
                if isinstance(data, list):
                    mapping = {
                        d.get("symbol"): d for d in data if isinstance(d, dict) and d.get("symbol")
                    }
                    self.prime_ticker_cache(mapping, timestamp=now)
                elif isinstance(data, dict) and data.get("symbol"):
                    self.prime_ticker_cache({data.get("symbol"): data}, timestamp=now)
        except Exception:
            self._t24_cache = {}
            self._t24_ts = now
        rec = self._t24_cache.get(symbol)
        if rec is None:
            try:
                single = self.exchange.get_ticker_24hr(symbol)
                if isinstance(single, dict):
                    self._t24_cache[symbol] = single
                    rec = single
            except Exception:
                rec = None
        return rec

    def prime_premium_cache(
        self, payload: Dict[str, Dict[str, Any]], *, timestamp: Optional[float] = None
    ) -> None:
        if not payload:
            return
        now = float(timestamp or time.time())
        sanitized: Dict[str, Dict[str, Any]] = {}
        for sym, rec in payload.items():
            if not sym or not isinstance(rec, dict):
                continue
            sanitized[sym] = dict(rec)
        if not sanitized:
            return
        if not self._premium_cache:
            self._premium_cache = sanitized
        else:
            self._premium_cache.update(sanitized)
        self._premium_ts = now

    def _premium_index(self, symbol: str) -> Optional[Dict[str, Any]]:
        now = time.time()
        try:
            if (now - self._premium_ts) > self._premium_ttl or not self._premium_cache:
                data = self.exchange.get_premium_index()
                if isinstance(data, list):
                    mapping = {
                        d.get("symbol"): d for d in data if isinstance(d, dict) and d.get("symbol")
                    }
                    self.prime_premium_cache(mapping, timestamp=now)
                elif isinstance(data, dict) and data.get("symbol"):
                    self.prime_premium_cache({data.get("symbol"): data}, timestamp=now)
        except Exception:
            self._premium_cache = {}
            self._premium_ts = now
        rec = self._premium_cache.get(symbol)
        if rec is None:
            try:
                single = self.exchange.get_premium_index(symbol)
                if isinstance(single, dict):
                    self._premium_cache[symbol] = single
                    rec = single
            except Exception:
                rec = None
        return rec

    def _get_qv_score(self, symbol: str) -> Tuple[float, Optional[Dict[str, Any]], float]:
        rec = self._ticker_24(symbol)
        try:
            qvol = float(rec.get("quoteVolume", 0.0) or 0.0) if rec else 0.0
        except Exception:
            qvol = 0.0
        score = min(2.5, qvol / max(self.min_quote_vol, 1e-9)) if qvol > 0 else 0.0
        return score, rec, float(qvol)

    def reset_orderbook_budget(self, on_demand: Optional[int] = None) -> None:
        budget = self._orderbook_budget_max if on_demand is None else int(on_demand)
        self._orderbook_budget = max(0, budget)

    def plan_orderbook_prefetch(
        self,
        symbols: Sequence[str],
        book_ticker_map: Dict[str, Dict[str, Any]],
        *,
        manual_symbols: Optional[Sequence[str]] = None,
        priority_symbols: Optional[Sequence[str]] = None,
    ) -> List[str]:
        if ORDERBOOK_PREFETCH <= 0 and not manual_symbols and not priority_symbols:
            return []
        ranked: List[Tuple[float, str]] = []
        forced_order: List[str] = []

        def _normalize_set(items: Optional[Sequence[str]]) -> Set[str]:
            result: Set[str] = set()
            if not items:
                return result
            for token in items:
                if not token:
                    continue
                result.add(str(token).strip().upper())
            return result

        manual_set = _normalize_set(manual_symbols)
        priority_set = _normalize_set(priority_symbols)

        def _maybe_force(sym: str) -> None:
            if sym and sym not in forced_order:
                forced_order.append(sym)

        for sym in symbols:
            token = str(sym or "").strip().upper()
            if not token:
                continue
            if token in manual_set or token in priority_set:
                _maybe_force(token)
            bt = book_ticker_map.get(token)
            if not isinstance(bt, dict):
                continue
            try:
                ask = float(bt.get("askPrice", 0.0) or 0.0)
                bid = float(bt.get("bidPrice", 0.0) or 0.0)
                ask_qty = float(bt.get("askQty", 0.0) or 0.0)
                bid_qty = float(bt.get("bidQty", 0.0) or 0.0)
            except Exception:
                continue
            if ask <= 0 or bid <= 0:
                continue
            mid = (ask + bid) / 2.0
            spread = (ask - bid) / max(mid, 1e-9)
            total_qty = max(ask_qty + bid_qty, 1e-9)
            imbalance = (bid_qty - ask_qty) / total_qty
            liquidity_penalty = 0.0
            if min(ask_qty, bid_qty) > 0:
                liquidity_penalty = clamp(1.0 / math.sqrt(max(min(ask_qty, bid_qty), 1e-9)), 0.0, 2.5)
            score = abs(imbalance) * 2.2 + clamp(spread * 220.0, 0.0, 3.0) + liquidity_penalty
            ranked.append((score, token))

        ranked.sort(key=lambda item: item[0], reverse=True)
        plan: List[str] = []
        for token in forced_order:
            if token not in plan:
                plan.append(token)
        if ORDERBOOK_PREFETCH > 0:
            for score, token in ranked:
                if token in plan:
                    continue
                if score <= 0 and len(plan) >= len(forced_order):
                    continue
                plan.append(token)
                if len(plan) >= ORDERBOOK_PREFETCH:
                    break
        return plan

    def _normalize_order_book(self, payload: Any) -> Optional[Dict[str, Any]]:
        if not isinstance(payload, dict):
            return None
        bids_raw = payload.get("bids", [])
        asks_raw = payload.get("asks", [])
        bids: List[Tuple[float, float]] = []
        asks: List[Tuple[float, float]] = []
        for entry in bids_raw:
            if not entry:
                continue
            try:
                price = float(entry[0])
                qty = float(entry[1])
            except Exception:
                continue
            if price <= 0 or qty <= 0:
                continue
            bids.append((price, qty))
            if len(bids) >= self.orderbook_limit:
                break
        for entry in asks_raw:
            if not entry:
                continue
            try:
                price = float(entry[0])
                qty = float(entry[1])
            except Exception:
                continue
            if price <= 0 or qty <= 0:
                continue
            asks.append((price, qty))
            if len(asks) >= self.orderbook_limit:
                break
        if not bids or not asks:
            return None
        bids.sort(key=lambda item: item[0], reverse=True)
        asks.sort(key=lambda item: item[0])
        normalized: Dict[str, Any] = {
            "bids": tuple(bids),
            "asks": tuple(asks),
            "lastUpdateId": payload.get("lastUpdateId"),
        }
        return normalized

    def prefetch_order_books(self, symbols: Sequence[str]) -> Dict[str, Dict[str, Any]]:
        fetched: Dict[str, Dict[str, Any]] = {}
        if not symbols:
            return fetched
        now = time.time()
        for sym in symbols:
            token = str(sym or "").strip().upper()
            if not token:
                continue
            cached = self._orderbook_cache.get(token)
            if cached and (now - cached[0]) <= self._orderbook_ttl:
                fetched[token] = cached[1]
                continue
            try:
                raw = self.exchange.get_order_book(token, limit=self.orderbook_limit)
            except Exception as exc:
                log.debug(f"orderbook fetch failed for {token}: {exc}")
                continue
            normalized = self._normalize_order_book(raw)
            if not normalized:
                continue
            snapshot = dict(normalized)
            snapshot["captured_at"] = time.time()
            self._orderbook_cache[token] = (snapshot["captured_at"], snapshot)
            fetched[token] = snapshot
        return fetched

    def get_cached_order_book(self, symbol: str, *, stale_ok: bool = False) -> Optional[Dict[str, Any]]:
        token = str(symbol or "").strip().upper()
        if not token:
            return None
        cached = self._orderbook_cache.get(token)
        if not cached:
            return None
        ts, snapshot = cached
        if (time.time() - ts) <= self._orderbook_ttl:
            return snapshot
        if stale_ok:
            return snapshot
        return None

    def ensure_order_book(self, symbol: str) -> Optional[Dict[str, Any]]:
        snapshot = self.get_cached_order_book(symbol)
        if snapshot:
            return snapshot
        if self._orderbook_budget <= 0:
            return None
        self._orderbook_budget -= 1
        fetched = self.prefetch_order_books([symbol])
        return fetched.get(str(symbol or "").strip().upper())

    def _order_book_features(
        self,
        symbol: str,
        book_ticker: Optional[Dict[str, Any]] = None,
        order_book: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, float]:
        snapshot = order_book or self.ensure_order_book(symbol)
        if not snapshot:
            return {}
        bids: Sequence[Tuple[float, float]] = snapshot.get("bids", ())  # type: ignore[assignment]
        asks: Sequence[Tuple[float, float]] = snapshot.get("asks", ())  # type: ignore[assignment]
        if not bids or not asks:
            return {}

        def _sum_qty(levels: Sequence[Tuple[float, float]], depth: int) -> float:
            return sum(level[1] for level in levels[: depth if depth > 0 else len(levels)])

        def _sum_notional(levels: Sequence[Tuple[float, float]], depth: int) -> float:
            return sum(level[0] * level[1] for level in levels[: depth if depth > 0 else len(levels)])

        def _gap_score(levels: Sequence[Tuple[float, float]], side: str) -> float:
            if len(levels) < 3:
                return 0.0
            diffs: List[float] = []
            limit = min(len(levels), 12)
            for idx in range(1, limit):
                prev_price = levels[idx - 1][0]
                curr_price = levels[idx][0]
                gap = prev_price - curr_price if side == "bid" else curr_price - prev_price
                if gap > 0:
                    diffs.append(gap)
            if not diffs:
                return 0.0
            avg = sum(diffs) / len(diffs)
            if avg <= 0:
                return 0.0
            return clamp(max(diffs) / avg - 1.0, 0.0, 5.0)

        def _wall_score(levels: Sequence[Tuple[float, float]]) -> float:
            qtys = [level[1] for level in levels[:10] if level[1] > 0]
            if len(qtys) < 3:
                return 0.0
            qtys_sorted = sorted(qtys)
            try:
                median_val = statistics.median(qtys_sorted)
            except statistics.StatisticsError:
                median_val = 0.0
            if median_val <= 0:
                return 0.0
            return clamp(max(qtys_sorted) / median_val - 1.0, 0.0, 5.0)

        bid_qty_5 = _sum_qty(bids, 5)
        ask_qty_5 = _sum_qty(asks, 5)
        total_5 = max(bid_qty_5 + ask_qty_5, 1e-9)
        bid_qty_10 = _sum_qty(bids, 10)
        ask_qty_10 = _sum_qty(asks, 10)
        total_10 = max(bid_qty_10 + ask_qty_10, 1e-9)
        bid_notional_10 = _sum_notional(bids, 10)
        ask_notional_10 = _sum_notional(asks, 10)
        ratio = bid_notional_10 / max(ask_notional_10, 1e-9)
        gap_bid = _gap_score(bids, "bid")
        gap_ask = _gap_score(asks, "ask")
        wall_bid = _wall_score(bids)
        wall_ask = _wall_score(asks)

        features: Dict[str, float] = {
            "lob_imbalance_5": clamp((bid_qty_5 - ask_qty_5) / total_5, -1.0, 1.0),
            "lob_imbalance_10": clamp((bid_qty_10 - ask_qty_10) / total_10, -1.0, 1.0),
            "lob_depth_ratio": clamp(ratio, 0.0, 5.0),
            "lob_gap_score": max(gap_bid, gap_ask),
            "lob_gap_bid": gap_bid,
            "lob_gap_ask": gap_ask,
            "lob_wall_score": max(wall_bid, wall_ask),
            "lob_wall_bid": wall_bid,
            "lob_wall_ask": wall_ask,
            "lob_bid_notional_10": float(bid_notional_10),
            "lob_ask_notional_10": float(ask_notional_10),
            "lob_levels": float(min(len(bids), len(asks))),
        }
        features["lob_bias"] = features["lob_imbalance_10"]
        captured_at = snapshot.get("captured_at")
        if captured_at:
            try:
                age = max(0.0, time.time() - float(captured_at))
            except Exception:
                age = 0.0
            features["lob_snapshot_age"] = float(age)
        if isinstance(book_ticker, dict):
            try:
                ask_px = float(book_ticker.get("askPrice", 0.0) or 0.0)
                bid_px = float(book_ticker.get("bidPrice", 0.0) or 0.0)
                if ask_px > 0 and bid_px > 0:
                    mid_px = (ask_px + bid_px) / 2.0
                    if mid_px > 0:
                        features["lob_bid_support"] = float(bid_notional_10 / max(mid_px, 1e-9))
                        features["lob_ask_pressure"] = float(ask_notional_10 / max(mid_px, 1e-9))
            except Exception:
                pass
        return features

    def _skip(
        self,
        reason: str,
        symbol: str,
        extra: Optional[Dict[str, Any]] = None,
        *,
        ctx: Optional[Dict[str, Any]] = None,
        price: Optional[float] = None,
        atr: Optional[float] = None,
    ):
        if extra:
            log.debug(f"SKIP {symbol}: {reason} {extra}")
        else:
            log.debug(f"SKIP {symbol}: {reason}")
        if self.decision_tracker:
            self.decision_tracker.record_rejection(reason)
        payload: Dict[str, Any] = {}
        if ctx:
            try:
                sanitized = self._sanitize_for_json(ctx)
                if isinstance(sanitized, dict):
                    payload = sanitized
                else:
                    payload = dict(ctx)
            except Exception:
                payload = dict(ctx)
        payload.setdefault("skip_reason", reason)
        if extra:
            payload.setdefault("skip_meta", extra)
        return (
            "NONE",
            float(atr or payload.get("atr_abs") or 0.0),
            payload,
            float(price or payload.get("mid_price") or payload.get("last_price") or 0.0),
        )

    def compute_signal(
        self,
        symbol: str,
        book_ticker: Optional[Dict[str, Any]] = None,
        order_book: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, float, Dict[str, float], float]:
        try:
            kl = self._klines_cached(symbol, INTERVAL, KLINES)
            if not kl or len(kl) < 60:
                return self._skip("few_klines", symbol, {"k": len(kl) if kl else 0})
            htf = self._klines_cached(symbol, HTF_INTERVAL, 120)
        except Exception as e:
            return self._skip("klines_err", symbol, {"err": str(e)[:80]})

        closes = [x[4] for x in kl]; highs = [x[2] for x in kl]; lows = [x[3] for x in kl]
        last = closes[-1]
        ctx_base: Dict[str, Any] = {
            "last_price": float(last),
        }

        score_info = self._symbol_score_cache.get(symbol, {})
        if score_info:
            try:
                ctx_base["universe_score"] = float(score_info.get("score", 0.0) or 0.0)
            except Exception:
                pass
            try:
                ctx_base["universe_qv_score"] = float(score_info.get("qv_score", 0.0) or 0.0)
            except Exception:
                pass
            try:
                ctx_base["universe_perf_bias"] = float(score_info.get("perf_bias", 1.0) or 1.0)
            except Exception:
                pass
            try:
                ctx_base["universe_budget_bias"] = float(score_info.get("budget_bias", 1.0) or 1.0)
            except Exception:
                pass

        # Spread (adaptiv an ATR%)
        mid = last
        spread_bps = 0.0
        bt = book_ticker
        if bt is None:
            try:
                bt = self.exchange.get_book_ticker(symbol)
            except Exception:
                bt = None
        if isinstance(bt, dict):
            try:
                ask = float(bt.get("askPrice", 0.0) or 0.0)
                bid = float(bt.get("bidPrice", 0.0) or 0.0)
                if ask > 0 and bid > 0:
                    mid = (ask + bid) / 2.0
                    spread_bps = (ask - bid) / max(mid, 1e-9)
            except Exception:
                mid = last
                spread_bps = 0.0
        ctx_base.update(
            {
                "mid_price": float(mid),
                "spread_bps": float(spread_bps),
            }
        )

        atr = atr_abs_from_klines(kl, 14)
        atrp = atr / max(1e-9, last)
        dyn_spread_max = max(self.spread_bps_max, 0.5 * atrp)
        if spread_bps > dyn_spread_max:
            ctx_base["atr_abs"] = float(atr)
            ctx_base["atr_pct"] = float(atrp)
            return self._skip(
                "spread",
                symbol,
                {"spread": f"{spread_bps:.5f}", "max": f"{dyn_spread_max:.5f}"},
                ctx=ctx_base,
                price=mid,
                atr=atr,
            )
        ctx_base["atr_abs"] = float(atr)
        ctx_base["atr_pct"] = float(atrp)

        order_features = self._order_book_features(symbol, book_ticker=bt, order_book=order_book)
        if order_features:
            ctx_base.update(order_features)
            lob_bias = order_features.get("lob_bias")
            if isinstance(lob_bias, (int, float)):
                ctx_base["orderbook_bias"] = float(lob_bias)
            ctx_base["orderbook_levels"] = float(order_features.get("lob_levels", 0.0) or 0.0)
        else:
            ctx_base["orderbook_levels"] = 0.0

        # Wickiness
        try:
            wick_hi = highs[-1] - max(closes[-1], float(kl[-1][1]))
            wick_lo = min(closes[-1], float(kl[-1][1])) - lows[-1]
            wickiness = max(wick_hi, wick_lo) / max(1e-9, highs[-1] - lows[-1])
            if wickiness > self.wickiness_max:
                ctx_base["wickiness"] = float(wickiness)
                return self._skip(
                    "wicky",
                    symbol,
                    {"w": f"{wickiness:.2f}"},
                    ctx=ctx_base,
                    price=mid,
                    atr=atr,
                )
            ctx_base["wickiness"] = float(wickiness)
        except Exception:
            pass

        htf_close = [x[4] for x in htf]
        ema_fast = ema(closes, 21)
        ema_slow = ema(closes, 55)
        ema_htf = ema(htf_close, 55)
        cross_up = ema_fast[-2] < ema_slow[-2] and ema_fast[-1] > ema_slow[-1]
        cross_dn = ema_fast[-2] > ema_slow[-2] and ema_fast[-1] < ema_slow[-1]
        rsi14 = rsi(closes, 14)
        bb_upper, bb_middle, bb_lower, bb_width = bollinger_bands(closes, 20, 2.0)
        stoch_k, stoch_d = stoch_rsi(closes, 14, 3, 3)
        stoch_k_last = float(stoch_k[-1]) if stoch_k else 50.0
        stoch_d_last = float(stoch_d[-1]) if stoch_d else 50.0
        supertrend_line, supertrend_dir = supertrend_indicator(kl, 10, 3.0)
        supertrend_last = float(supertrend_line[-1]) if supertrend_line else float(last)
        supertrend_dir_last = float(supertrend_dir[-1]) if supertrend_dir else 0.0
        bb_upper_last = float(bb_upper[-1]) if bb_upper else float(last)
        bb_lower_last = float(bb_lower[-1]) if bb_lower else float(last)
        bb_middle_last = float(bb_middle[-1]) if bb_middle else float(last)
        bb_width_last = float(bb_width[-1]) if bb_width else max(bb_upper_last - bb_lower_last, 0.0)
        bb_denom = max(bb_upper_last - bb_lower_last, 1e-9)
        bb_position = float(max(0.0, min(1.0, (last - bb_lower_last) / bb_denom)))
        ctx_base.update(
            {
                "ema_fast": float(ema_fast[-1]),
                "ema_slow": float(ema_slow[-1]),
                "ema_fast_delta": float(ema_fast[-1] - ema_slow[-1]),
                "ema_htf": float(ema_htf[-1]),
                "cross_up": float(1.0 if cross_up else 0.0),
                "cross_down": float(1.0 if cross_dn else 0.0),
                "rsi": float(rsi14[-1]),
                "bb_upper": float(bb_upper_last),
                "bb_lower": float(bb_lower_last),
                "bb_middle": float(bb_middle_last),
                "bb_width": float(bb_width_last),
                "bb_position": float(bb_position),
                "stoch_rsi_k": float(stoch_k_last),
                "stoch_rsi_d": float(stoch_d_last),
                "supertrend": float(supertrend_last),
                "supertrend_dir": float(supertrend_dir_last),
            }
        )

        adx_val, adx_delta = adx_latest(kl, 14)
        slope_fast = (ema_fast[-1] - ema_fast[-5]) / max(abs(ema_fast[-5]), 1e-9)
        ctx_base.update(
            {
                "adx": float(adx_val),
                "adx_delta": float(adx_delta),
                "slope_fast": float(slope_fast),
            }
        )

        htf_trend_up = ema_htf[-1] > ema_htf[-5]
        htf_trend_down = ema_htf[-1] < ema_htf[-5]
        ctx_base.update(
            {
                "htf_trend_up": float(1.0 if htf_trend_up else 0.0),
                "htf_trend_down": float(1.0 if htf_trend_down else 0.0),
            }
        )

        sig = "NONE"
        if cross_up and rsi14[-1] > RSI_BUY_MIN and htf_trend_up:
            sig = "BUY"
        elif cross_dn and rsi14[-1] < RSI_SELL_MAX and htf_trend_down:
            sig = "SELL"
        elif ALLOW_ALIGN:
            # Fallback: Trend-Align (ohne frischen Cross), leicht entspannte RSI-Schwellen
            if ema_fast[-1] > ema_slow[-1] and htf_trend_up and rsi14[-1] > (RSI_BUY_MIN - ALIGN_RSI_PAD):
                sig = "BUY"
            elif ema_fast[-1] < ema_slow[-1] and htf_trend_down and rsi14[-1] < (RSI_SELL_MAX + ALIGN_RSI_PAD):
                sig = "SELL"
            else:
                return self._skip("no_cross", symbol, ctx=ctx_base, price=mid, atr=atr)
        else:
            return self._skip("no_cross", symbol, ctx=ctx_base, price=mid, atr=atr)

        supertrend_gate_enabled = True
        if CONTRARIAN:
            if sig == "BUY":
                sig = "SELL"
            elif sig == "SELL":
                sig = "BUY"
            supertrend_gate_enabled = False

        slope_htf = (ema_htf[-1] - ema_htf[-5]) / max(1e-9, ema_htf[-5])
        trend_strength = 0.5 + max(adx_val - 20.0, 0.0) / 50.0
        expected_R = abs(slope_htf) * 20.0 * trend_strength
        if expected_R < MIN_EDGE_R:
            ctx_base.update({"slope_htf": float(slope_htf), "expected_r": float(expected_R)})
            return self._skip(
                "edge_r",
                symbol,
                {"expR": f"{expected_R:.3f}", "minR": f"{MIN_EDGE_R:.3f}"},
                ctx=ctx_base,
                price=mid,
                atr=atr,
            )
        ctx_base.update({"slope_htf": float(slope_htf), "expected_r": float(expected_R)})

        filtered_signal = sig

        lob_bias = ctx_base.get("orderbook_bias")
        if isinstance(lob_bias, (int, float)):
            if sig == "BUY" and lob_bias < -0.35:
                ctx_base["lob_conflict"] = float(lob_bias)
                sig = "NONE"
            elif sig == "SELL" and lob_bias > 0.35:
                ctx_base["lob_conflict"] = float(lob_bias)
                sig = "NONE"
        lob_gap_score = ctx_base.get("lob_gap_score")
        if isinstance(lob_gap_score, (int, float)) and lob_gap_score > 3.0:
            ctx_base["lob_gap_alert"] = float(lob_gap_score)
            sig = "NONE"
        lob_levels = ctx_base.get("orderbook_levels")
        if isinstance(lob_levels, (int, float)) and lob_levels < 3:
            ctx_base["lob_depth_issue"] = float(lob_levels)
            sig = "NONE"

        if sig == "BUY":
            if supertrend_gate_enabled and supertrend_dir_last < 0.0:
                ctx_base["supertrend_conflict"] = float(supertrend_dir_last)
                sig = "NONE"
            elif stoch_d_last >= 85.0:
                ctx_base["stoch_rsi_overbought"] = float(stoch_d_last)
                sig = "NONE"
            elif bb_position >= 0.98:
                ctx_base["bb_overextended"] = float(bb_position)
                sig = "NONE"
        elif sig == "SELL":
            if supertrend_gate_enabled and supertrend_dir_last > 0.0:
                ctx_base["supertrend_conflict"] = float(supertrend_dir_last)
                sig = "NONE"
            elif stoch_d_last <= 15.0:
                ctx_base["stoch_rsi_oversold"] = float(stoch_d_last)
                sig = "NONE"
            elif bb_position <= 0.02:
                ctx_base["bb_overextended"] = float(bb_position)
                sig = "NONE"

        if isinstance(self.state, dict):
            try:
                tech_state = self.state.setdefault("technical_snapshot", {})
                if isinstance(tech_state, dict):
                    snapshot = {
                        "ts": time.time(),
                        "price": float(last),
                        "ema_fast": float(ema_fast[-1]),
                        "ema_slow": float(ema_slow[-1]),
                        "ema_htf": float(ema_htf[-1]),
                        "rsi": float(rsi14[-1]),
                        "stoch_rsi_k": float(stoch_k_last),
                        "stoch_rsi_d": float(stoch_d_last),
                        "bb_upper": float(bb_upper_last),
                        "bb_lower": float(bb_lower_last),
                        "bb_width": float(bb_width_last),
                        "bb_pos": float(bb_position),
                        "supertrend": float(supertrend_last),
                        "supertrend_dir": float(supertrend_dir_last),
                        "atr_pct": float(atrp),
                        "adx": float(adx_val),
                        "htf_trend": 1.0 if htf_trend_up else (-1.0 if htf_trend_down else 0.0),
                    }
                    tech_state[symbol] = snapshot
                    if len(tech_state) > 200:
                        stale = sorted(
                            tech_state.items(),
                            key=lambda item: float(item[1].get("ts", 0.0) if isinstance(item[1], dict) else 0.0),
                        )
                        for old_sym, _ in stale[:-200]:
                            tech_state.pop(old_sym, None)
                    self.state["technical_snapshot"] = tech_state
                    self._tech_snapshot_dirty = True
            except Exception:
                pass

        if sig == "NONE":
            filter_meta: Dict[str, str] = {}

            st_conflict = ctx_base.get("supertrend_conflict")
            if isinstance(st_conflict, (int, float)):
                direction = "bearish" if st_conflict < 0 else "bullish"
                filter_meta["supertrend_gate"] = f"{direction} ({st_conflict:+.2f})"

            stoch_over = ctx_base.get("stoch_rsi_overbought")
            if isinstance(stoch_over, (int, float)):
                filter_meta["stoch_rsi"] = f"{float(stoch_over):.1f} (too high)"

            stoch_under = ctx_base.get("stoch_rsi_oversold")
            if isinstance(stoch_under, (int, float)):
                filter_meta["stoch_rsi"] = f"{float(stoch_under):.1f} (too low)"

            bb_ext = ctx_base.get("bb_overextended")
            if isinstance(bb_ext, (int, float)):
                position = float(bb_ext)
                side = "top" if position >= 0.5 else "bottom"
                filter_meta["bollinger_pos"] = f"{position:.2f} (near {side})"

            extra_detail: Optional[Dict[str, str]] = None
            if filter_meta:
                extra_detail = {f"filtered_{k}": v for k, v in filter_meta.items()}
            if filtered_signal in ("BUY", "SELL"):
                extra_detail = extra_detail or {}
                extra_detail["filtered_signal"] = filtered_signal

            return self._skip(
                "filtered",
                symbol,
                extra_detail,
                ctx=ctx_base,
                price=mid,
                atr=atr,
            )

        qv_score, t24, quote_volume = self._get_qv_score(symbol)
        funding = 0.0
        if isinstance(t24, dict):
            try:
                funding = float(t24.get("lastFundingRate", 0.0) or 0.0)
            except Exception:
                funding = 0.0
        premium_index = None
        try:
            premium_index = self._premium_index(symbol)
        except Exception:
            premium_index = None
        ctx_base["qv_score"] = float(qv_score)
        ctx_base["quote_volume"] = float(quote_volume)
        ctx_base["min_quote_volume"] = float(self.min_quote_vol)
        if self.min_quote_vol > 0 and quote_volume < self.min_quote_vol:
            return self._skip(
                "min_qvol",
                symbol,
                {"qvol": f"{quote_volume:.2f}", "min": f"{self.min_quote_vol:.2f}"},
                ctx=ctx_base,
                price=mid,
                atr=atr,
            )

        mark_price = None
        oracle_price = None
        oracle_gap = None
        oracle_gap_clamped = None
        funding_edge = None
        non_arb_region = 0.0
        if isinstance(premium_index, dict):
            try:
                if funding == 0.0:
                    funding = float(premium_index.get("lastFundingRate", funding) or funding)
            except Exception:
                pass
            try:
                mark_price = float(premium_index.get("markPrice", 0.0) or 0.0)
            except Exception:
                mark_price = None
            try:
                oracle_price = float(premium_index.get("indexPrice", 0.0) or 0.0)
            except Exception:
                oracle_price = None
            if mark_price and oracle_price:
                try:
                    oracle_gap = (mark_price - oracle_price) / max(oracle_price, 1e-9)
                except Exception:
                    oracle_gap = None
                if oracle_gap is not None:
                    oracle_gap_clamped = clamp(
                        oracle_gap,
                        -NON_ARB_CLAMP_BPS,
                        NON_ARB_CLAMP_BPS,
                    )
                    funding_edge = funding - oracle_gap_clamped
                    if oracle_gap < -NON_ARB_CLAMP_BPS:
                        non_arb_region = -1.0
                    elif oracle_gap > NON_ARB_CLAMP_BPS:
                        non_arb_region = 1.0
                    ctx_base.update(
                        {
                            "mark_price": float(mark_price),
                            "oracle_price": float(oracle_price),
                            "oracle_gap": float(oracle_gap),
                            "oracle_gap_clamped": float(oracle_gap_clamped),
                            "funding_edge": float(funding_edge),
                            "non_arb_region": float(non_arb_region),
                        }
                    )
                    if NON_ARB_FILTER_ENABLED and sig in ("BUY", "SELL"):
                        if NON_ARB_SKIP_GAP > 0 and abs(oracle_gap) > NON_ARB_SKIP_GAP:
                            return self._skip(
                                "oracle_gap",
                                symbol,
                                {
                                    "gap_pct": f"{oracle_gap * 100:.3f}%",
                                    "limit_pct": f"{NON_ARB_SKIP_GAP * 100:.3f}%",
                                },
                                ctx=ctx_base,
                                price=mid,
                                atr=atr,
                            )
                        if (
                            NON_ARB_EDGE_THRESHOLD > 0
                            and funding_edge is not None
                            and sig == "BUY"
                            and funding_edge > NON_ARB_EDGE_THRESHOLD
                        ):
                            ctx_base["non_arb_bias"] = float(funding_edge)
                            return self._skip(
                                "non_arb_bias_long",
                                symbol,
                                {
                                    "edge": f"{funding_edge:.6f}",
                                    "max": f"{NON_ARB_EDGE_THRESHOLD:.6f}",
                                },
                                ctx=ctx_base,
                                price=mid,
                                atr=atr,
                            )
                        if (
                            NON_ARB_EDGE_THRESHOLD > 0
                            and funding_edge is not None
                            and sig == "SELL"
                            and funding_edge < -NON_ARB_EDGE_THRESHOLD
                        ):
                            ctx_base["non_arb_bias"] = float(funding_edge)
                            return self._skip(
                                "non_arb_bias_short",
                                symbol,
                                {
                                    "edge": f"{funding_edge:.6f}",
                                    "max": f"{-NON_ARB_EDGE_THRESHOLD:.6f}",
                                },
                                ctx=ctx_base,
                                price=mid,
                                atr=atr,
                            )

        ctx_base["funding"] = float(funding)

        if FUNDING_FILTER_ENABLED and sig in ("BUY", "SELL"):
            if sig == "BUY" and funding > FUNDING_MAX_LONG:
                return self._skip(
                    "funding_long",
                    symbol,
                    {"funding": f"{funding:.6f}", "max": f"{FUNDING_MAX_LONG:.6f}"},
                    ctx=ctx_base,
                    price=mid,
                    atr=atr,
                )
            if sig == "SELL" and funding < -FUNDING_MAX_SHORT:
                return self._skip(
                    "funding_short",
                    symbol,
                    {"funding": f"{funding:.6f}", "max": f"{-FUNDING_MAX_SHORT:.6f}"},
                    ctx=ctx_base,
                    price=mid,
                    atr=atr,
                )

        ctx: Dict[str, float] = {
            **ctx_base,
            "trend": 1.0 if sig == "BUY" else -1.0,
            "regime_adx": float(max(min(adx_delta / 100.0, 2.0), -2.0)),
            "regime_slope": float(max(min(slope_fast, 2.0), -2.0)),
        }
        return sig, float(atr), ctx, float(mid or last)

# ========= Trade Manager =========
class TradeManager:
    def __init__(self, exchange: Exchange, policy: Optional[BanditPolicy], state: Dict[str, Any]):
        self.exchange = exchange
        self.policy = policy
        self.state = state
        self.state.setdefault("live_trades", {})
        self.state.setdefault("fast_tp_cooldown", {})
        self.state.setdefault("fail_skip_until", {})
        self.state.setdefault("trade_history", [])
        self._ensure_cumulative_metrics()
        try:
            self.history_max = int(os.getenv("ASTER_HISTORY_MAX", "250"))
        except Exception:
            self.history_max = 250

    @staticmethod
    def _boolish(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        if isinstance(value, (int, float)):
            return value != 0
        text = str(value).strip().lower()
        if not text:
            return False
        return text in {"1", "true", "yes", "on"}

    def _cancel_stale_exit_orders(self, symbol: str) -> None:
        try:
            orders = self.exchange.get_open_orders(symbol) or []
        except Exception as exc:
            log.debug(f"cleanup open orders fail {symbol}: {exc}")
            return

        cancelled = 0
        for order in orders:
            order_type = str(order.get("type") or "").upper()
            if "STOP" not in order_type and "TAKE_PROFIT" not in order_type:
                continue

            close_position = self._boolish(order.get("closePosition"))
            reduce_only = self._boolish(order.get("reduceOnly"))
            if not close_position and not reduce_only:
                continue

            order_id = order.get("orderId") or order.get("id") or order.get("order_id")
            if order_id is None:
                continue

            order_id_int: Optional[int]
            try:
                order_id_int = int(str(order_id).strip())
            except Exception:
                try:
                    order_id_int = int(float(order_id))
                except Exception:
                    order_id_int = None

            if order_id_int is None:
                continue

            try:
                self.exchange.cancel_order(symbol, order_id_int)
                cancelled += 1
            except Exception as exc:
                log.debug(f"cleanup cancel fail {symbol}: {exc}")

        if cancelled:
            log.debug(f"cleanup removed {cancelled} exit orders for {symbol}")

    def _sanitize_meta(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return json.loads(json.dumps(meta, default=lambda o: str(o)))
        except Exception:
            return {}

    def _rebuild_cumulative_metrics(self) -> Dict[str, Any]:
        metrics = {
            "total_trades": 0,
            "total_pnl": 0.0,
            "wins": 0,
            "losses": 0,
            "draws": 0,
        }
        history = self.state.get("trade_history", []) or []
        tolerance = 1e-9
        for trade in history:
            try:
                pnl = float(trade.get("pnl", 0.0) or 0.0)
            except Exception:
                pnl = 0.0
            metrics["total_trades"] += 1
            metrics["total_pnl"] += pnl
            if pnl > tolerance:
                metrics["wins"] += 1
            elif pnl < -tolerance:
                metrics["losses"] += 1
            else:
                metrics["draws"] += 1
        return metrics

    def _ensure_cumulative_metrics(self) -> Dict[str, Any]:
        raw_metrics = self.state.get("cumulative_metrics")
        if isinstance(raw_metrics, dict):
            metrics = {
                "total_trades": int(raw_metrics.get("total_trades", 0) or 0),
                "total_pnl": float(raw_metrics.get("total_pnl", 0.0) or 0.0),
                "wins": int(raw_metrics.get("wins", 0) or 0),
                "losses": int(raw_metrics.get("losses", 0) or 0),
                "draws": int(raw_metrics.get("draws", 0) or 0),
            }
            if "updated_at" in raw_metrics:
                metrics["updated_at"] = raw_metrics.get("updated_at")
        else:
            metrics = self._rebuild_cumulative_metrics()
        self.state["cumulative_metrics"] = metrics
        return metrics

    def _record_cumulative_metrics(self, trade: Dict[str, Any]) -> None:
        metrics = self._ensure_cumulative_metrics()
        try:
            pnl = float(trade.get("pnl", 0.0) or 0.0)
        except Exception:
            pnl = 0.0
        metrics["total_trades"] += 1
        metrics["total_pnl"] += pnl
        tolerance = 1e-9
        if pnl > tolerance:
            metrics["wins"] += 1
        elif pnl < -tolerance:
            metrics["losses"] += 1
        else:
            metrics["draws"] += 1
        metrics["updated_at"] = time.time()

    def save(self) -> None:
        if self.policy and BANDIT_ENABLED:
            try:
                self.state["policy"] = self.policy.to_dict()
            except Exception as e:
                log.debug(f"policy serialize fail: {e}")
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r") as fh:
                    disk_state = json.load(fh)
            except Exception:
                disk_state = {}
            if isinstance(disk_state, dict):
                disk_queue = disk_state.get("manual_trade_requests")
                if isinstance(disk_queue, list):
                    mem_queue = self.state.setdefault("manual_trade_requests", [])
                    existing_ids = {
                        item.get("id") for item in mem_queue if isinstance(item, dict) and item.get("id")
                    }
                    for item in disk_queue:
                        if not isinstance(item, dict):
                            continue
                        item_id = item.get("id")
                        if item_id and item_id not in existing_ids:
                            mem_queue.append(item)
                self._merge_ai_trade_proposals(disk_state)
        try:
            with open(STATE_FILE, "w") as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            log.warning(f"state save failed: {e}")

    def _merge_ai_trade_proposals(self, disk_state: Dict[str, Any]) -> None:
        queue_disk = disk_state.get("ai_trade_proposals")
        if not isinstance(queue_disk, list):
            return
        mem_queue = self.state.get("ai_trade_proposals")
        if not isinstance(mem_queue, list):
            mem_queue = []
        merged: List[Any] = []
        seen_ids: Set[str] = set()
        for item in queue_disk:
            if isinstance(item, dict):
                item_id = item.get("id")
                if isinstance(item_id, str) and item_id:
                    seen_ids.add(item_id)
                merged.append(item)
            else:
                merged.append(item)
        if mem_queue:
            for item in mem_queue:
                if isinstance(item, dict):
                    item_id = item.get("id")
                    if isinstance(item_id, str) and item_id in seen_ids:
                        continue
                    merged.append(item)
                else:
                    merged.append(item)
        self.state["ai_trade_proposals"] = merged

    def note_entry(
        self,
        symbol: str,
        entry: float,
        sl: float,
        tp: float,
        side: str,
        qty: float,
        ctx: Dict[str, float],
        bucket: str,
        atr_abs: float,
        meta: Optional[Dict[str, Any]] = None,
    ):
        record: Dict[str, Any] = {
            "entry": float(entry),
            "expected_entry": float(entry),
            "sl": float(sl),
            "tp": float(tp),
            "side": side,
            "qty": float(qty),
            "ctx": dict(ctx),
            "bucket": bucket,
            "atr_abs": float(atr_abs),
            "opened_at": time.time(),
            "filled_qty": 0.0,
        }
        if meta:
            sanitized = self._sanitize_meta(meta)
            if sanitized:
                record["ai"] = sanitized
                if "fasttp_overrides" in sanitized:
                    record["fasttp_overrides"] = sanitized["fasttp_overrides"]
        self.state["live_trades"][symbol] = record
        self.save()
        if self.policy and BANDIT_ENABLED:
            try:
                self.policy.note_entry(symbol, ctx=ctx, size_bucket=bucket)
            except Exception as e:
                log.debug(f"policy note_entry fail: {e}")

    def register_entry_fill(
        self,
        symbol: str,
        order_info: Optional[Dict[str, Any]],
        trades: Sequence[Dict[str, Any]],
    ) -> None:
        rec = self.state.get("live_trades", {}).get(symbol)
        if not isinstance(rec, dict):
            return
        avg_price = _coerce_float((order_info or {}).get("avgPrice"))
        executed_qty = _coerce_float((order_info or {}).get("executedQty"))
        status = str((order_info or {}).get("status") or "").upper()
        entry_order_id = _coerce_int((order_info or {}).get("orderId"))
        client_order_id = (order_info or {}).get("clientOrderId")
        if trades:
            total_qty = 0.0
            total_cost = 0.0
            commission = rec.get("entry_commission", 0.0) or 0.0
            trade_ids: List[int] = []
            for trade in trades:
                qty = _coerce_float(trade.get("qty")) or 0.0
                price = _coerce_float(trade.get("price")) or 0.0
                total_qty += qty
                total_cost += qty * price
                commission += _coerce_float(trade.get("commission")) or 0.0
                tid = _coerce_int(trade.get("id") or trade.get("tradeId"))
                if tid is not None:
                    trade_ids.append(tid)
            if total_qty > 0 and total_cost > 0:
                avg_price = total_cost / total_qty
                executed_qty = total_qty
            if trade_ids:
                rec["last_trade_id"] = max(trade_ids)
            rec["entry_commission"] = float(commission)
        if avg_price is not None and avg_price > 0:
            rec["entry"] = float(avg_price)
        if executed_qty is not None and executed_qty > 0:
            rec["qty"] = float(executed_qty)
            rec["filled_qty"] = float(executed_qty)
        if entry_order_id is not None:
            rec["entry_order_id"] = int(entry_order_id)
        if client_order_id:
            rec["client_order_id"] = client_order_id
        if status:
            rec["order_status"] = status
        ts = _coerce_float((order_info or {}).get("updateTime"))
        if ts is not None:
            rec["last_update"] = float(ts) / (1000.0 if ts > 1e6 else 1.0)
        rec.setdefault("fills", []).append(
            {
                "avg": float(avg_price or rec.get("entry", 0.0)),
                "qty": float(executed_qty or rec.get("qty", 0.0)),
                "order_id": entry_order_id,
                "client_order_id": client_order_id,
                "status": status,
                "ts": time.time(),
            }
        )
        self.save()

    def handle_order_update(self, payload: Dict[str, Any]) -> None:
        symbol = str(payload.get("symbol") or "").upper()
        if not symbol:
            return
        rec = self.state.get("live_trades", {}).get(symbol)
        if not isinstance(rec, dict):
            return
        side = str(payload.get("side") or "").upper()
        if side and rec.get("side") and side != rec.get("side"):
            return
        status = str(payload.get("status") or "").upper()
        if status not in {"FILLED", "PARTIALLY_FILLED", "TRADE"}:
            return
        order_info = {
            "symbol": symbol,
            "orderId": payload.get("orderId"),
            "clientOrderId": payload.get("clientOrderId"),
            "status": payload.get("status"),
            "executedQty": payload.get("executedQty") or payload.get("cumulativeQty"),
            "avgPrice": payload.get("avgPrice") or payload.get("priceAvg"),
            "updateTime": payload.get("event_time"),
        }
        trade_stub: List[Dict[str, Any]] = []
        last_qty = payload.get("lastQty") or payload.get("tradeQty")
        last_price = payload.get("lastPrice") or payload.get("tradePrice")
        if last_qty:
            trade_stub.append(
                {
                    "qty": last_qty,
                    "price": last_price,
                    "commission": payload.get("commission"),
                    "realizedPnl": payload.get("realizedPnl"),
                    "buyer": side == "BUY",
                    "tradeId": payload.get("tradeId"),
                    "id": payload.get("tradeId"),
                    "time": payload.get("tradeTime") or payload.get("event_time"),
                }
            )
        try:
            self.register_entry_fill(symbol, order_info, trade_stub)
        except Exception as exc:
            log.debug(f"order update registration failed for {symbol}: {exc}")

    def handle_account_update(self, payload: Dict[str, Any]) -> None:
        live = self.state.get("live_trades", {})
        if not isinstance(live, dict) or not live:
            return
        positions = payload.get("positions") or payload.get("P") or []
        for entry in positions:
            symbol = str(entry.get("symbol") or entry.get("s") or "").upper()
            if not symbol or symbol not in live:
                continue
            rec = live.get(symbol)
            if not isinstance(rec, dict):
                continue
            amt = _coerce_float(entry.get("positionAmt") or entry.get("pa"))
            if amt is not None:
                rec["position_amt"] = float(amt)
            entry_price = _coerce_float(entry.get("entryPrice") or entry.get("ep"))
            if entry_price is not None and entry_price > 0:
                rec.setdefault("entry", float(entry_price))
            realized = _coerce_float(entry.get("realizedPnl") or entry.get("rp"))
            if realized is not None:
                rec["realized_snapshot"] = float(realized)
        self.save()

    def remove_closed_trades(
        self,
        postmortem_cb: Optional[Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]] = None,
    ):
        live = self.state.get("live_trades", {})
        if not isinstance(live, dict):
            live = {}
            self.state["live_trades"] = live

        processed_syms: Set[str] = set()
        history_added = False

        paper_closed: List[Dict[str, Any]] = []
        if PAPER:
            try:
                paper_closed = self.exchange.paper_consume_closed()
            except Exception as exc:
                log.debug(f"paper consume closed failed: {exc}")
                paper_closed = []
        if paper_closed:
            hist = self.state.setdefault("trade_history", [])
            for closed in paper_closed:
                sym = str(closed.get("symbol") or "").upper()
                if not sym:
                    continue
                rec = live.get(sym, {})
                entry = float(closed.get("entry", rec.get("entry", 0.0)) or 0.0)
                exit_px = float(closed.get("exit", entry) or entry)
                qty = float(closed.get("qty", rec.get("qty", 0.0)) or 0.0)
                side = str(closed.get("side") or rec.get("side") or ("BUY" if qty >= 0 else "SELL"))
                pnl = float(closed.get("pnl", 0.0) or 0.0)
                pnl_r = float(closed.get("pnl_r", 0.0) or 0.0)
                opened_at = float(closed.get("opened_at", rec.get("opened_at", time.time())) or time.time())
                closed_at = float(closed.get("closed_at", time.time()) or time.time())
                bucket = rec.get("bucket") if rec else closed.get("bucket")
                ctx = rec.get("ctx", {}) if rec else closed.get("context", {})
                ai_meta = rec.get("ai") if isinstance(rec, dict) else closed.get("ai")
                record = {
                    "symbol": sym,
                    "side": side,
                    "qty": float(qty),
                    "entry": float(entry),
                    "exit": float(exit_px),
                    "pnl": float(pnl),
                    "pnl_r": float(pnl_r),
                    "opened_at": opened_at,
                    "closed_at": closed_at,
                    "bucket": bucket,
                    "context": ctx or {},
                }
                if ai_meta:
                    record["ai"] = ai_meta
                reason = closed.get("reason")
                if reason:
                    record["paper_reason"] = reason
                if self.policy and BANDIT_ENABLED:
                    try:
                        self.policy.note_exit(sym, pnl_r=float(pnl_r), ctx=ctx, size_bucket=bucket)
                    except Exception as e:
                        log.debug(f"policy note_exit fail: {e}")
                postmortem = None
                if postmortem_cb:
                    try:
                        postmortem = postmortem_cb({**record})
                    except Exception as exc:
                        log.debug(f"postmortem fail {sym}: {exc}")
                        postmortem = None
                if postmortem:
                    record["postmortem"] = postmortem
                hist.append(record)
                self._record_cumulative_metrics(record)
                if len(hist) > max(10, self.history_max):
                    del hist[: len(hist) - self.history_max]
                log.info(
                    f"EXIT {sym} {side} qty={qty:.6f} exit≈{exit_px:.6f} PNL={pnl:.2f}USDT R={pnl_r:.2f}"
                )
                history_added = True
                processed_syms.add(sym)
            for sym in processed_syms:
                live.pop(sym, None)

        try:
            pos = self.exchange.get_position_risk()
            pos_map = {p.get("symbol"): float(p.get("positionAmt", "0") or 0.0) for p in pos}
        except Exception as e:
            log.debug(f"positionRisk fail: {e}")
            pos_map = {}

        to_del: List[str] = []
        for sym, rec in live.items():
            if sym in processed_syms:
                continue
            amt = pos_map.get(sym, 0.0)
            if abs(amt) > 1e-12:
                continue  # noch offen

            self._cancel_stale_exit_orders(sym)
            entry = float(rec.get("entry"))
            sl = float(rec.get("sl"))
            side = rec.get("side")
            qty = float(rec.get("qty"))
            last_trade_id = rec.get("last_trade_id")
            start_time = None
            opened_at = rec.get("opened_at")
            if isinstance(opened_at, (int, float)) and opened_at > 0:
                start_time = int(max(0, opened_at - 5) * 1000)
            try:
                trades = self.exchange.get_user_trades(
                    sym,
                    from_id=(int(last_trade_id) + 1) if isinstance(last_trade_id, (int, float)) else None,
                    start_time=start_time,
                )
            except Exception as exc:
                log.debug(f"userTrades closing fetch failed for {sym}: {exc}")
                trades = []
            closing_qty = 0.0
            closing_cost = 0.0
            closing_commission = 0.0
            realized_pnl = 0.0
            latest_trade_id = last_trade_id
            for trade in trades or []:
                buyer_flag = bool(trade.get("buyer"))
                is_exit = (side == "BUY" and not buyer_flag) or (side == "SELL" and buyer_flag)
                tid = _coerce_int(trade.get("id") or trade.get("tradeId"))
                if tid is not None:
                    latest_trade_id = tid if latest_trade_id is None else max(latest_trade_id, tid)
                if not is_exit:
                    continue
                qty_tr = _coerce_float(trade.get("qty")) or 0.0
                px_tr = _coerce_float(trade.get("price")) or 0.0
                pnl_tr = _coerce_float(trade.get("realizedPnl")) or 0.0
                fee_tr = _coerce_float(trade.get("commission")) or 0.0
                closing_qty += qty_tr
                closing_cost += qty_tr * px_tr
                realized_pnl += pnl_tr
                closing_commission += fee_tr
            if latest_trade_id is not None:
                rec["last_trade_id"] = latest_trade_id
            if closing_qty <= 0:
                # fallback: Mid-price estimate
                try:
                    bt = self.exchange.get_book_ticker(sym)
                    ask = float(bt.get("askPrice", 0.0) or 0.0)
                    bid = float(bt.get("bidPrice", 0.0) or 0.0)
                    exit_px = (ask + bid) / 2.0 if ask > 0 and bid > 0 else entry
                except Exception:
                    exit_px = entry
                prof = (exit_px - entry) * qty if side == "BUY" else (entry - exit_px) * qty
                risk = max(1e-9, abs(entry - sl) * qty)
                r_mult = float(prof / risk)
                gross_pnl = prof
                exit_commission = 0.0
                rec["exit_price"] = float(exit_px)
                rec["pnl"] = float(prof)
            else:
                exit_px = closing_cost / max(closing_qty, 1e-9)
                entry_commission = rec.get("entry_commission", 0.0) or 0.0
                total_commission = entry_commission + closing_commission
                gross_pnl = float(realized_pnl)
                net_pnl = gross_pnl - total_commission
                if abs(total_commission) <= 1e-9:
                    prof = gross_pnl
                else:
                    prof = net_pnl
                risk = max(1e-9, abs(entry - sl) * qty)
                r_mult = float(prof / risk)
                rec["exit_commission"] = float(closing_commission)
                rec["entry_commission"] = float(entry_commission)
                rec["fees_total"] = float(total_commission)
                rec["gross_pnl"] = float(gross_pnl)
                rec["exit_price"] = float(exit_px)
                rec["exit_qty"] = float(closing_qty)
                rec["pnl"] = float(prof)
                exit_commission = closing_commission
            if self.policy and BANDIT_ENABLED:
                try:
                    self.policy.note_exit(symbol, pnl_r=r_mult, ctx=rec.get("ctx"), size_bucket=rec.get("bucket"))
                except Exception as e:
                    log.debug(f"policy note_exit fail: {e}")
            hist = self.state.setdefault("trade_history", [])
            closed_at = time.time()
            opened_at = float(rec.get("opened_at", closed_at) or closed_at)
            entry_commission = rec.get("entry_commission", 0.0) or 0.0
            total_fees = entry_commission + (rec.get("exit_commission", 0.0) or 0.0)
            pnl_value = rec.get("pnl", prof)
            record = {
                "symbol": sym,
                "side": side,
                "qty": float(qty),
                "entry": float(entry),
                "exit": float(rec.get("exit_price", exit_px if 'exit_px' in locals() else entry)),
                "pnl": float(pnl_value),
                "pnl_r": float(r_mult),
                "opened_at": float(opened_at),
                "closed_at": float(closed_at),
                "bucket": rec.get("bucket"),
                "context": rec.get("ctx", {}),
            }
            if abs(total_fees) > 0:
                record["fees"] = float(total_fees)
            if "gross_pnl" in rec:
                record["pnl_gross"] = float(rec["gross_pnl"])
            ai_meta = rec.get("ai")
            if ai_meta:
                record["ai"] = ai_meta
            postmortem = None
            if postmortem_cb:
                try:
                    postmortem = postmortem_cb({**record})
                except Exception as exc:
                    log.debug(f"postmortem fail {sym}: {exc}")
                    postmortem = None
            if postmortem:
                record["postmortem"] = postmortem
            hist.append(record)
            self._record_cumulative_metrics(record)
            if len(hist) > max(10, self.history_max):
                del hist[: len(hist) - self.history_max]
            log.info(
                f"EXIT {sym} {side} qty={qty:.6f} exit≈{exit_px:.6f} PNL={prof:.2f}USDT R={r_mult:.2f}"
            )
            history_added = True
            to_del.append(sym)

        for sym in to_del:
            self.state["live_trades"].pop(sym, None)
        if to_del or history_added or processed_syms:
            self.save()

# ========= Decisions =========
class DecisionTracker:
    def __init__(self, state: Dict[str, Any], save_cb: Optional[Callable[[], None]] = None):
        self.state = state
        self._save_cb = save_cb
        self._last_persist = 0.0
        self._persist_interval = 15.0

    def _ensure(self) -> Dict[str, Any]:
        stats = self.state.setdefault("decision_stats", {})
        stats.setdefault("taken", 0)
        stats.setdefault("rejected_total", 0)
        stats.setdefault("taken_by_bucket", {})
        stats.setdefault("rejected", {})
        return stats

    def _persist(self, force: bool = False) -> None:
        if not self._save_cb:
            return
        now = time.time()
        if not force and (now - self._last_persist) < self._persist_interval:
            return
        self._last_persist = now
        try:
            self._save_cb()
        except Exception as exc:
            log.debug(f"decision stats save failed: {exc}")

    def record_acceptance(
        self, bucket: Optional[str] = None, persist: bool = True, force: bool = False
    ) -> None:
        stats = self._ensure()
        stats["taken"] = int(stats.get("taken", 0) or 0) + 1
        if bucket:
            bucket_key = str(bucket)
            bucket_map = stats.setdefault("taken_by_bucket", {})
            bucket_map[bucket_key] = int(bucket_map.get(bucket_key, 0) or 0) + 1
        stats["last_updated"] = time.time()
        self.state["decision_stats"] = stats
        if persist:
            self._persist(force=force)

    def record_rejection(self, reason: str, persist: bool = True, force: bool = False) -> None:
        stats = self._ensure()
        reason_key = str(reason or "unknown")
        rejected = stats.setdefault("rejected", {})
        rejected[reason_key] = int(rejected.get(reason_key, 0) or 0) + 1
        stats["rejected_total"] = int(stats.get("rejected_total", 0) or 0) + 1
        stats["last_updated"] = time.time()
        self.state["decision_stats"] = stats
        if persist:
            self._persist(force=force)

# ========= FastTP =========
class FastTP:
    def __init__(self, exchange: Exchange, guard: BracketGuard, state: Dict[str, Any]):
        self.exchange = exchange
        self.guard = guard
        self.state = state
        self.buf: Dict[str, List[Tuple[float, float]]] = {}

    def track(self, symbol: str, price: float):
        buf = self.buf.setdefault(symbol, [])
        now = time.time()
        buf.append((now, float(price)))
        # halte ~5 min Daten
        cutoff = now - 300
        while len(buf) > 2 and buf[0][0] < cutoff:
            buf.pop(0)

    def _ret(self, symbol: str, seconds: int) -> float:
        buf = self.buf.get(symbol, [])
        if len(buf) < 2:
            return 0.0
        latest_ts, latest_px = buf[-1]
        threshold = latest_ts - seconds
        ref_px = None
        for ts, px in reversed(buf):
            if ts <= threshold:
                ref_px = px
                break
        if ref_px is None:
            if latest_ts - buf[0][0] < seconds:
                return 0.0
            ref_px = buf[0][1]
        return (latest_px - ref_px) / max(ref_px, 1e-9)

    def maybe_apply(self, symbol: str, pos_amt: float, entry_px: float, sl_px: float, last_px: float, atr_abs: float) -> bool:
        rec = self.state.get("live_trades", {}).get(symbol, {})
        overrides = rec.get("fasttp_overrides") or (rec.get("ai") or {}).get("fasttp_overrides")
        enabled = FAST_TP_ENABLED if overrides is None else bool(overrides.get("enabled", True))
        if not enabled or abs(pos_amt) < 1e-12 or atr_abs <= 0.0:
            return False
        cd_until = self.state.setdefault("fast_tp_cooldown", {}).get(symbol, 0.0)
        if time.time() < cd_until:
            return False

        side_open = "BUY" if pos_amt > 0 else "SELL"
        risk = max(abs(entry_px - sl_px), 1e-9)
        r_now = (last_px - entry_px) / risk if side_open == "BUY" else (entry_px - last_px) / risk
        min_r = overrides.get("min_r") if overrides else None
        if min_r is None:
            min_r = FASTTP_MIN_R
        if r_now < min_r:
            return False

        ret1 = self._ret(symbol, 60)
        ret3 = self._ret(symbol, 180)
        ret1_cut = overrides.get("ret1") if overrides else FAST_TP_RET1
        ret3_cut = overrides.get("ret3") if overrides else FAST_TP_RET3
        reversal = (
            (ret1 <= ret1_cut or ret3 <= ret3_cut)
            if pos_amt > 0
            else (ret1 >= -ret1_cut or ret3 >= -ret3_cut)
        )
        if not reversal:
            return False

        snap_mult = overrides.get("snap_atr") if overrides else FASTTP_SNAP_ATR
        snap = snap_mult * max(atr_abs, 1e-12)
        new_exit = (max(entry_px + 0.05 * risk, last_px - snap)
                    if pos_amt > 0 else
                    min(entry_px - 0.05 * risk, last_px + snap))

        qty_abs = abs(pos_amt)
        try:
            if PAPER:
                ok = self.exchange.paper_replace_take_profit(
                    symbol,
                    new_exit,
                )
            else:
                _bg_replace_tp(
                    self.guard,
                    symbol,
                    qty_abs,
                    new_exit,
                    side=("BUY" if pos_amt > 0 else "SELL"),
                )
                ok = True
        except Exception as e:
            log.debug(f"FASTTP {symbol} replace error: {e}")
            ok = False

        if ok:
            self.state.setdefault("fast_tp_cooldown", {})[symbol] = time.time() + FASTTP_COOLDOWN_S
            try:
                with open(STATE_FILE, "w") as f:
                    json.dump(self.state, f, indent=2)
            except Exception:
                pass
            log.debug(f"FASTTP {symbol} r={r_now:.2f} ret1={ret1:.4f} ret3={ret3:.4f} → exit {new_exit:.6f}")
            return True
        return False

# ========= Bot =========
class Bot:
    def __init__(self):
        if not API_KEY:
            log.warning(
                "ASTER_API_KEY is not set—live trades cannot be executed without credentials."
            )
        if AI_MODE_ENABLED and not OPENAI_API_KEY:
            log.warning(
                "AI mode is enabled, but ASTER_OPENAI_API_KEY is missing—AI features remain disabled."
            )
        self.exchange = Exchange(BASE, API_KEY, API_SECRET, RECV_WINDOW)
        self.universe = SymbolUniverse(self.exchange, QUOTE, UNIVERSE_MAX, EXCLUDE, UNIVERSE_ROTATE, include=INCLUDE)
        self.risk = RiskManager(self.exchange, DEFAULT_NOTIONAL)
        self.risk.load_filters()
        self.state = {}
        try:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, "r") as fh:
                    self.state = json.load(fh)
        except Exception:
            self.state = {}
        if not isinstance(self.state, dict):
            self.state = {}
        self.state.setdefault("ai_activity", [])
        self.state.setdefault("ai_trade_proposals", [])
        self.state.setdefault("manual_trade_requests", [])
        self.state.setdefault("manual_trade_history", [])
        try:
            self.risk.attach_state(self.state)
        except Exception:
            pass
        self._ensure_banned_state()
        cooldown_map = self.state.get("quote_volume_cooldown")
        if not isinstance(cooldown_map, dict):
            cooldown_map = {}
        self.state["quote_volume_cooldown"] = cooldown_map
        try:
            self.state["cycle_index"] = int(self.state.get("cycle_index", 0) or 0)
        except Exception:
            self.state["cycle_index"] = 0
        self._current_cycle = int(self.state.get("cycle_index", 0) or 0)
        self._last_ai_activity_persist = 0.0
        self._manual_state_dirty = False
        self._quote_volume_cooldown_dirty = False
        self._universe_state_dirty = False
        self._ai_wakeup_event = threading.Event()
        self._ai_priority_lock = threading.Lock()
        self._ai_priority_queue: deque[Tuple[str, Optional[str]]] = deque()
        self._ai_priority_keys: Set[Tuple[str, Optional[str]]] = set()
        self._ai_priority_hint: Dict[str, Optional[str]] = {}
        self._ai_feed_pending_requests: Set[str] = set()
        self._symbol_score_cache: Dict[str, Dict[str, float]] = {}
        self._orderbook_activity_signature: Tuple[str, ...] = tuple()
        self.policy: Optional[BanditPolicy] = None
        if BANDIT_ENABLED:
            pol_state = self.state.get("policy") if isinstance(self.state, dict) else None
            try:
                if pol_state:
                    self.policy = BanditPolicy.from_dict(
                        pol_state,
                        alpha_enabled=ALPHA_ENABLED,
                        alpha_threshold=ALPHA_THRESHOLD,
                        alpha_warmup=ALPHA_WARMUP,
                        alpha_lr=ALPHA_LR,
                        alpha_l2=ALPHA_L2,
                        alpha_min_conf=ALPHA_MIN_CONF,
                        alpha_promote_delta=ALPHA_PROMOTE_DELTA,
                        alpha_reward_margin=ALPHA_REWARD_MARGIN,
                    )
                else:
                    self.policy = BanditPolicy(
                        alpha_enabled=ALPHA_ENABLED,
                        alpha_threshold=ALPHA_THRESHOLD,
                        alpha_warmup=ALPHA_WARMUP,
                        alpha_lr=ALPHA_LR,
                        alpha_l2=ALPHA_L2,
                        alpha_min_conf=ALPHA_MIN_CONF,
                        alpha_promote_delta=ALPHA_PROMOTE_DELTA,
                        alpha_reward_margin=ALPHA_REWARD_MARGIN,
                    )
            except Exception as e:
                log.debug(f"ML policy init failed: {e}")
                self.policy = None
        self.guard = BracketGuard(
            base_url=BASE,
            api_key=API_KEY,
            api_secret=API_SECRET,
            working_type=WORKING_TYPE,
            recv_window=RECV_WINDOW,
        )
        self.trade_mgr = TradeManager(self.exchange, self.policy, self.state)
        self.user_stream: Optional[UserDataStream] = None
        if USER_STREAM_ENABLED:
            try:
                self.user_stream = UserDataStream(
                    self.exchange,
                    on_execution=self._handle_stream_execution,
                    on_account=self._handle_stream_account,
                )
                self.user_stream.start()
            except Exception as exc:
                log.debug(f"user stream initialization failed: {exc}")
        self._reset_decision_stats()
        self.fasttp = FastTP(self.exchange, self.guard, self.state)
        self.decision_tracker = DecisionTracker(self.state, self.trade_mgr.save)
        self._strategy = Strategy(
            self.exchange,
            decision_tracker=self.decision_tracker,
            state=self.state,
        )
        self.state.setdefault("symbol_leverage", {})
        self.budget_tracker = DailyBudgetTracker(self.state, AI_DAILY_BUDGET, AI_STRICT_BUDGET)
        try:
            self._strategy.budget_tracker = self.budget_tracker
        except Exception:
            pass
        remaining_budget = self.budget_tracker.remaining()
        if self.budget_tracker.limit > 0 and remaining_budget is not None and remaining_budget <= 0:
            log.warning(
                "Daily AI budget of %.2f USD is already exhausted—blocking new AI requests.",
                self.budget_tracker.limit,
            )
        sentinel_active = SENTINEL_ENABLED or AI_MODE_ENABLED
        self.sentinel = NewsTrendSentinel(
            self.exchange,
            self.state,
            enabled=sentinel_active,
            ai_client=_shared_openai_client(),
        )
        self.ai_advisor: Optional[AITradeAdvisor] = None
        if AI_MODE_ENABLED:
            self.ai_advisor = AITradeAdvisor(
                OPENAI_API_KEY,
                AI_MODEL,
                self.budget_tracker,
                self.state,
                enabled=AI_MODE_ENABLED,
                wakeup_cb=self._on_ai_future_ready,
                activity_logger=self._emit_ai_budget_alert,
                leverage_lookup=self._symbol_leverage_cap,
            )
            if self.sentinel and getattr(self.ai_advisor, "_client", None):
                try:
                    self.sentinel.set_ai_client(self.ai_advisor._client)
                except Exception:
                    pass

    @property
    def strategy(self) -> Strategy:
        return self._strategy

    def _handle_stream_execution(self, payload: Dict[str, Any]) -> None:
        if not isinstance(payload, dict):
            return
        try:
            self.trade_mgr.handle_order_update(payload)
        except Exception as exc:
            log.debug(f"stream execution dispatch failed: {exc}")

    def _handle_stream_account(self, payload: Dict[str, Any]) -> None:
        if not isinstance(payload, dict):
            return
        try:
            self.trade_mgr.handle_account_update(payload)
        except Exception as exc:
            log.debug(f"stream account dispatch failed: {exc}")

    def _ensure_banned_state(self) -> None:
        banned = self.state.get("banned_symbols")
        if not isinstance(banned, dict):
            banned = {}
        self.state["banned_symbols"] = banned
        try:
            self.universe.exclude = set(self.universe.exclude)
            if banned:
                self.universe.exclude.update(banned.keys())
        except Exception:
            pass

    def _symbol_leverage_cap(self, symbol: str) -> float:
        try:
            cap = self.risk.max_leverage_for(symbol)
        except Exception:
            cap = 0.0
        if cap <= 0:
            if math.isfinite(LEVERAGE) and LEVERAGE > 0:
                cap = LEVERAGE
            else:
                cap = 20.0
        return max(1.0, float(cap))

    def _clamp_leverage(self, symbol: str, leverage: Any) -> float:
        try:
            numeric = float(leverage)
        except (TypeError, ValueError):
            numeric = 0.0
        if numeric <= 0:
            numeric = 1.0
        cap = self._symbol_leverage_cap(symbol)
        return clamp(numeric, 1.0, cap if math.isfinite(cap) else numeric)

    def _banned_map(self) -> Dict[str, Dict[str, Any]]:
        banned = self.state.get("banned_symbols")
        if not isinstance(banned, dict):
            banned = {}
            self.state["banned_symbols"] = banned
        return banned

    def _ban_symbol(self, symbol: str, reason: str, details: Optional[str] = None) -> None:
        banned = self._banned_map()
        if symbol in banned:
            return
        banned[symbol] = {
            "reason": reason,
            "banned_at": time.time(),
        }
        if details:
            banned[symbol]["details"] = details
        try:
            self.universe.exclude.add(symbol)
        except Exception:
            pass
        log.warning(
            "Banning symbol %s due to %s%s",
            symbol,
            reason,
            f" ({details})" if details else "",
        )
        if getattr(self, "trade_mgr", None):
            try:
                self.trade_mgr.save()
            except Exception as exc:
                log.debug(f"ban persist failed {symbol}: {exc}")

    def _price_filter_limits(self, symbol: str) -> Tuple[float, float]:
        limits = self.risk.symbol_filters.get(symbol, {}) if hasattr(self, "risk") else {}
        if not isinstance(limits, dict):
            return 0.0, 0.0
        try:
            min_price = float(limits.get("minPrice", 0.0) or 0.0)
        except (TypeError, ValueError):
            min_price = 0.0
        try:
            max_price = float(limits.get("maxPrice", 0.0) or 0.0)
        except (TypeError, ValueError):
            max_price = 0.0
        return min_price, max_price

    def _clamp_to_price_band(self, symbol: str, price: float) -> float:
        try:
            value = float(price)
        except (TypeError, ValueError):
            try:
                return float(price or 0.0)
            except Exception:
                return 0.0
        if not math.isfinite(value):
            return value
        min_price, max_price = self._price_filter_limits(symbol)
        if max_price > 0 and value > max_price:
            value = max_price
        if min_price > 0 and value < min_price:
            value = min_price
        return value

    def _handle_price_filter_rejection(
        self,
        symbol: str,
        side: str,
        entry: float,
        stop: float,
        target: float,
        *,
        detail: Optional[str] = None,
        manual_override: bool = False,
        manual_req: Optional[Dict[str, Any]] = None,
    ) -> None:
        fail_map = self.state.setdefault("fail_skip_until", {})
        cooldown = time.time() + max(30, LOOP_SLEEP * 2)
        fail_map[symbol] = cooldown
        reason_note = (detail or "Exchange rejected the order due to price limits.").strip()
        log.warning(
            "Price filter rejected %s (%s): %s",
            symbol,
            side,
            reason_note,
        )
        if self.decision_tracker:
            try:
                self.decision_tracker.record_rejection("price_filter", persist=False)
            except Exception:
                pass
        activity_payload = {
            "symbol": symbol,
            "side": side,
            "entry": float(entry),
            "stop": float(stop),
            "target": float(target),
            "cooldown_until": float(cooldown),
        }
        self._log_ai_activity(
            "decision",
            f"Price filter blocked {symbol}",
            body=reason_note,
            data=activity_payload,
            force=True,
        )
        if manual_override:
            if manual_req:
                self._complete_manual_request(
                    manual_req,
                    "failed",
                    error="Exchange rejected price band",
                    result={
                        "entry": float(entry),
                        "stop": float(stop),
                        "target": float(target),
                    },
                )
            else:
                self._manual_state_dirty = True

    def _refresh_manual_requests(self):
        try:
            if not os.path.exists(STATE_FILE):
                return
            with open(STATE_FILE, "r") as fh:
                disk_state = json.load(fh)
        except Exception:
            return
        if not isinstance(disk_state, dict):
            return
        self._merge_ai_trade_proposals(disk_state)
        queue_disk = disk_state.get("manual_trade_requests")
        if not isinstance(queue_disk, list):
            return
        queue_mem = self.state.setdefault("manual_trade_requests", [])
        seen_ids = {item.get("id") for item in queue_mem if isinstance(item, dict)}
        updated = False
        for item in queue_disk:
            if not isinstance(item, dict):
                continue
            item_id = item.get("id")
            if item_id in seen_ids:
                continue
            queue_mem.append(item)
            updated = True
        if updated:
            self.state["manual_trade_requests"] = queue_mem

    def _merge_ai_trade_proposals(self, disk_state: Dict[str, Any]) -> None:
        queue_disk = disk_state.get("ai_trade_proposals")
        if not isinstance(queue_disk, list):
            return
        mem_queue = self.state.get("ai_trade_proposals")
        if not isinstance(mem_queue, list):
            mem_queue = []
        merged: List[Any] = []
        seen_ids: Set[str] = set()
        for item in queue_disk:
            if isinstance(item, dict):
                item_id = item.get("id")
                if isinstance(item_id, str) and item_id:
                    seen_ids.add(item_id)
                merged.append(item)
            else:
                merged.append(item)
        if mem_queue:
            for item in mem_queue:
                if isinstance(item, dict):
                    item_id = item.get("id")
                    if isinstance(item_id, str) and item_id in seen_ids:
                        continue
                    merged.append(item)
                else:
                    merged.append(item)
        self.state["ai_trade_proposals"] = merged

    def _resume_ai_pending_manual_requests(self) -> None:
        if not self.ai_advisor:
            return
        queue = self.state.get("manual_trade_requests")
        if not isinstance(queue, list):
            return
        dirty = False
        for item in queue:
            if not isinstance(item, dict):
                continue
            status = str(item.get("status") or "").lower()
            if status != "ai_pending":
                continue
            key = item.get("ai_pending_key")
            if not isinstance(key, str) or not key:
                continue
            plan = self.ai_advisor.consume_recent_plan(key)
            if not plan:
                continue
            item["status"] = "pending"
            item.pop("ai_pending_key", None)
            item.pop("ai_request_id", None)
            item["ai_ready_plan"] = plan
            item["ai_ready_at"] = time.time()
            dirty = True
        if dirty:
            self._manual_state_dirty = True

    def _on_ai_future_ready(self, _throttle_key: str) -> None:
        self._ai_wakeup_event.set()

    def _emit_ai_budget_alert(
        self,
        kind: str,
        headline: str,
        data: Optional[Dict[str, Any]],
        body: Optional[str] = None,
    ) -> None:
        payload = data or {}
        if body is None:
            limit = float(payload.get("budget_limit", self.budget_tracker.limit))
            spent = float(payload.get("budget_spent", self.budget_tracker.spent()))
            body = (
                f"Spent {spent:.2f} / {limit:.2f} USD of the daily AI budget. "
                "Autonomous requests are paused until the next reset."
            )
        self._log_ai_activity(kind, headline, body=body, data=payload, force=True)

    def _enqueue_ai_priority(self, symbol: str, side: Optional[str]) -> None:
        sym = str(symbol or "").upper()
        if not sym:
            return
        side_token = side.upper() if isinstance(side, str) and side else None
        key = (sym, side_token)
        with self._ai_priority_lock:
            if key in self._ai_priority_keys:
                return
            self._ai_priority_queue.append((sym, side_token))
            self._ai_priority_keys.add(key)
            if side_token is not None:
                self._ai_priority_hint[sym] = side_token
            elif sym not in self._ai_priority_hint:
                self._ai_priority_hint[sym] = None
        self._ai_wakeup_event.set()

    def _consume_ai_priority_symbols(self) -> List[Tuple[str, Optional[str]]]:
        with self._ai_priority_lock:
            items = list(self._ai_priority_queue)
            self._ai_priority_queue.clear()
            self._ai_priority_keys.clear()
        return items

    def _rank_symbols(
        self,
        symbols: Sequence[str],
        ticker_map: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> List[str]:
        unique_syms = [str(sym).upper() for sym in symbols if sym]
        if not unique_syms:
            self._symbol_score_cache = {}
            if getattr(self, "_strategy", None):
                self._strategy._symbol_score_cache = {}
            return []
        base_index = {sym: idx for idx, sym in enumerate(unique_syms)}
        ticker_map = ticker_map or {}
        history = []
        if isinstance(self.state.get("trade_history"), list):
            history = list(self.state.get("trade_history", []))[-120:]
        perf_samples: Dict[str, List[float]] = {}
        if history:
            for trade in history:
                sym = str(trade.get("symbol") or "").upper()
                if sym not in base_index:
                    continue
                try:
                    pnl_r = float(trade.get("pnl_r", 0.0) or 0.0)
                except Exception:
                    pnl_r = 0.0
                perf_samples.setdefault(sym, []).append(max(min(pnl_r, 5.0), -5.0))
        budget_bias_map: Dict[str, float] = {}
        learner = None
        if self.ai_advisor and getattr(self.ai_advisor, "budget_learner", None):
            learner = self.ai_advisor.budget_learner
        if learner:
            for sym in unique_syms:
                try:
                    budget_bias_map[sym] = float(learner.context_bias(sym))
                except Exception:
                    budget_bias_map[sym] = 1.0
        cooldown_map = self.state.get("quote_volume_cooldown")
        if not isinstance(cooldown_map, dict):
            cooldown_map = {}

        score_cache: Dict[str, Dict[str, float]] = {}
        for sym in unique_syms:
            perf_list = perf_samples.get(sym, [])
            if perf_list:
                avg_r = sum(perf_list[-12:]) / max(len(perf_list[-12:]), 1)
            else:
                avg_r = 0.0
            perf_bias = max(0.55, min(1.5, 1.0 + avg_r * 0.28))
            record = ticker_map.get(sym)
            if record and isinstance(record, dict):
                try:
                    qvol = float(record.get("quoteVolume", 0.0) or 0.0)
                except Exception:
                    qvol = 0.0
                qv_score = min(2.5, qvol / max(self.strategy.min_quote_vol, 1e-9)) if qvol > 0 else 0.0
            else:
                try:
                    qv_score, _, qvol = self.strategy._get_qv_score(sym)
                except Exception:
                    qv_score, qvol = 0.0, 0.0
            budget_bias = budget_bias_map.get(sym, 1.0)
            score = qv_score * perf_bias * (0.7 + 0.3 * max(0.1, budget_bias))
            resume_cycle = cooldown_map.get(sym)
            if resume_cycle is not None:
                try:
                    if int(resume_cycle) > getattr(self, "_current_cycle", 0):
                        score *= 0.25
                except Exception:
                    pass
            score_cache[sym] = {
                "score": float(score),
                "qv_score": float(qv_score),
                "perf_bias": float(perf_bias),
                "budget_bias": float(budget_bias),
            }
        ranked = sorted(
            unique_syms,
            key=lambda sym: (
                score_cache.get(sym, {}).get("score", 0.0),
                -base_index.get(sym, 0),
            ),
            reverse=True,
        )
        self._symbol_score_cache = score_cache
        if getattr(self, "_strategy", None):
            self._strategy._symbol_score_cache = score_cache
        universe_state = {
            sym: {
                "score": round(score_cache.get(sym, {}).get("score", 0.0), 6),
                "qv": round(score_cache.get(sym, {}).get("qv_score", 0.0), 4),
                "perf_bias": round(score_cache.get(sym, {}).get("perf_bias", 0.0), 4),
                "budget_bias": round(score_cache.get(sym, {}).get("budget_bias", 0.0), 4),
            }
            for sym in ranked
        }
        prev_state = self.state.get("universe_scores")
        if prev_state != universe_state:
            self.state["universe_scores"] = universe_state
            self._universe_state_dirty = True
        preferred_cut = max(5, min(len(ranked), (self.universe.max_n or 0) * 2 or 20))
        preferred = ranked[:preferred_cut]
        ignored = [sym for sym in ranked if score_cache.get(sym, {}).get("score", 0.0) < 0.1]
        dynamic_state = self.state.setdefault("dynamic_universe", {})
        if dynamic_state.get("preferred") != preferred or dynamic_state.get("ignored") != ignored:
            dynamic_state["preferred"] = preferred
            dynamic_state["ignored"] = ignored
            self._universe_state_dirty = True
        return ranked

    def _drain_ai_ready_queue(self, *, clear_event: bool = False) -> None:
        if clear_event:
            self._ai_wakeup_event.clear()
        if not self.ai_advisor:
            return

        ready_plans: List[Tuple[str, Dict[str, Any]]] = []
        try:
            ready_plans = self.ai_advisor.flush_pending()
        except Exception as exc:
            log.debug(f"pending flush failed: {exc}")
            ready_plans = []

        manual_dirty_before = self._manual_state_dirty
        try:
            self._resume_ai_pending_manual_requests()
        except Exception as exc:
            log.debug(f"manual resume failed: {exc}")

        if ready_plans:
            for throttle_key, plan in ready_plans:
                try:
                    self._handle_ai_ready_plan(throttle_key, plan)
                except Exception as exc:
                    log.debug(f"handle ready plan fail {throttle_key}: {exc}")
        elif not manual_dirty_before and self._manual_state_dirty:
            # ensure we propagate manual state updates triggered by resume even
            # when no explicit plan bundle was returned from flush_pending()
            log.debug("manual queue resumed from AI cache")

    def _handle_ai_ready_plan(self, throttle_key: str, plan: Dict[str, Any]) -> None:
        if not isinstance(throttle_key, str) or not throttle_key:
            return
        if not isinstance(plan, dict):
            return
        parts = throttle_key.split("::")
        if not parts:
            return
        category = parts[0]
        symbol: Optional[str] = None
        side_hint: Optional[str] = None
        if category == "plan" and len(parts) >= 3:
            symbol = parts[1].upper()
            side_hint = parts[2].upper()
        elif category == "trend" and len(parts) >= 2:
            symbol = parts[1].upper()
            side_val = plan.get("side")
            if isinstance(side_val, str) and side_val.strip():
                side_hint = side_val.strip().upper()
        else:
            return
        if not symbol:
            return
        plan_side = str(plan.get("side") or "").strip().upper()
        display_side = plan_side or side_hint or ""

        def _safe_float(value: Any) -> Optional[float]:
            if value is None:
                return None
            try:
                num = float(value)
            except (TypeError, ValueError):
                return None
            if not math.isfinite(num):
                return None
            return num

        decision_raw = plan.get("decision")
        decision_label = str(decision_raw or "").strip().upper()
        take_flag = bool(plan.get("take", False))
        if not decision_label:
            decision_label = "TAKE" if take_flag else "SKIP"

        confidence_val = _safe_float(plan.get("confidence"))
        size_mult_val = _safe_float(plan.get("size_multiplier"))
        sl_mult_val = _safe_float(plan.get("sl_multiplier"))
        tp_mult_val = _safe_float(plan.get("tp_multiplier"))

        body_parts: List[str] = []
        decision_action = "enter trade" if take_flag else "skip trade"
        if decision_label:
            body_parts.append(f"Decision: {decision_label} ({decision_action})")
        if confidence_val is not None:
            body_parts.append(f"Confidence {confidence_val:.2f}")
        mult_parts: List[str] = []
        if size_mult_val is not None:
            mult_parts.append(f"Size ×{size_mult_val:.2f}")
        if sl_mult_val is not None:
            mult_parts.append(f"SL ×{sl_mult_val:.2f}")
        if tp_mult_val is not None:
            mult_parts.append(f"TP ×{tp_mult_val:.2f}")
        if mult_parts:
            body_parts.append(", ".join(mult_parts))

        note_sources: List[str] = []
        decision_reason_val = plan.get("decision_reason")
        decision_note_val = plan.get("decision_note")
        risk_note_val = plan.get("risk_note")
        for raw_note in (
            decision_note_val,
            decision_reason_val,
            risk_note_val,
        ):
            if isinstance(raw_note, str):
                cleaned = " ".join(raw_note.split())
                if cleaned:
                    note_sources.append(cleaned)
        explanation = plan.get("explanation")
        if isinstance(explanation, str):
            cleaned_expl = " ".join(explanation.split())
            if cleaned_expl:
                note_sources.append(cleaned_expl)
        if note_sources:
            note_preview = textwrap.shorten(" | ".join(note_sources), width=240, placeholder="…")
            body_parts.append(note_preview)

        body_text = " | ".join(body_parts) if body_parts else "AI response received."
        side_suffix = f" {display_side}" if display_side else ""
        headline = f"AI response for {symbol}{side_suffix}".strip()

        activity_data: Dict[str, Any] = {
            "symbol": symbol,
            "side": display_side or None,
            "decision": decision_label,
            "take": take_flag,
            "request_id": plan.get("request_id"),
            "throttle_key": throttle_key,
        }
        if confidence_val is not None:
            activity_data["confidence"] = confidence_val
        if size_mult_val is not None:
            activity_data["size_multiplier"] = size_mult_val
        if sl_mult_val is not None:
            activity_data["sl_multiplier"] = sl_mult_val
        if tp_mult_val is not None:
            activity_data["tp_multiplier"] = tp_mult_val
        if note_sources:
            activity_data["notes"] = note_sources
        if isinstance(decision_reason_val, str):
            cleaned_reason = " ".join(decision_reason_val.split())
            if cleaned_reason:
                activity_data["decision_reason"] = cleaned_reason
        if isinstance(decision_note_val, str):
            cleaned_note = " ".join(decision_note_val.split())
            if cleaned_note:
                activity_data["decision_note"] = cleaned_note
        if isinstance(risk_note_val, str):
            cleaned_risk = " ".join(risk_note_val.split())
            if cleaned_risk:
                activity_data["risk_note"] = cleaned_risk
        if isinstance(explanation, str):
            cleaned_explanation = " ".join(explanation.split())
            if cleaned_explanation:
                activity_data["explanation"] = cleaned_explanation

        log.info(
            "AI response for %s%s: %s",
            symbol,
            f" {display_side}" if display_side else "",
            body_text,
        )
        self._log_ai_activity(
            "response",
            headline,
            body=body_text,
            data=activity_data,
            force=True,
        )
        self._enqueue_ai_priority(symbol, side_hint)

    def _pop_manual_request(self, symbol: str) -> Optional[Dict[str, Any]]:
        queue = self.state.get("manual_trade_requests")
        if not isinstance(queue, list):
            return None
        for item in queue:
            if not isinstance(item, dict):
                continue
            if str(item.get("symbol") or "").upper() != symbol.upper():
                continue
            if str(item.get("status") or "pending").lower() != "pending":
                continue
            item["status"] = "processing"
            item["started_at"] = time.time()
            self._manual_state_dirty = True
            proposal_id = self._proposal_id_from_request(item)
            if proposal_id:
                self._update_trade_proposal_status(proposal_id, "processing")
            return item
        return None

    def _proposal_id_from_request(self, request: Optional[Dict[str, Any]]) -> Optional[str]:
        if not request or not isinstance(request, dict):
            return None
        raw_id = request.get("proposal_id")
        if isinstance(raw_id, str):
            proposal_id = raw_id.strip()
            if proposal_id:
                return proposal_id
        payload = request.get("payload")
        if isinstance(payload, dict):
            inner_id = payload.get("proposal_id")
            if isinstance(inner_id, str):
                proposal_id = inner_id.strip()
                if proposal_id:
                    return proposal_id
            nested = payload.get("payload")
            if isinstance(nested, dict):
                nested_id = nested.get("proposal_id")
                if isinstance(nested_id, str):
                    proposal_id = nested_id.strip()
                    if proposal_id:
                        return proposal_id
        return None

    def _update_trade_proposal_status(
        self,
        proposal_id: Optional[str],
        status: str,
        *,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        if not proposal_id:
            return
        queue = self.state.get("ai_trade_proposals")
        if not isinstance(queue, list):
            return
        updated = False
        for entry in queue:
            if not isinstance(entry, dict):
                continue
            if str(entry.get("id") or "") != proposal_id:
                continue
            entry["status"] = status
            entry["updated_at"] = time.time()
            if result is not None:
                try:
                    entry["result"] = json.loads(json.dumps(result, default=lambda o: float(o)))
                except Exception:
                    entry["result"] = result
            elif "result" in entry:
                entry.pop("result", None)
            if error:
                entry["error"] = str(error)
            else:
                entry.pop("error", None)
            updated = True
            break
        if updated:
            self.state["ai_trade_proposals"] = queue
            self._manual_state_dirty = True

    def _complete_manual_request(
        self,
        request: Optional[Dict[str, Any]],
        status: str,
        *,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        if not request or not isinstance(request, dict):
            return
        request["status"] = status
        request["processed_at"] = time.time()
        if result is not None:
            request["result"] = result
        if error:
            request["error"] = error
        elif "error" in request:
            request.pop("error", None)
        proposal_id = self._proposal_id_from_request(request)
        if proposal_id:
            mapped_status = status.lower()
            if mapped_status == "filled":
                mapped_status = "executed"
            elif mapped_status == "failed":
                mapped_status = "failed"
            self._update_trade_proposal_status(
                proposal_id,
                mapped_status,
                result=result,
                error=error,
            )
        history = self.state.setdefault("manual_trade_history", [])
        history.append(dict(request))
        if len(history) > 100:
            del history[:-100]
        self.state["manual_trade_history"] = history
        self._manual_state_dirty = True

    def _log_ai_activity(
        self,
        kind: str,
        headline: str,
        *,
        body: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        force: bool = False,
    ) -> None:
        if not AI_MODE_ENABLED:
            return
        if data and data.get("ai_request") is False:
            return
        request_id: Optional[str] = None
        if isinstance(data, dict):
            raw_request_id = data.get("request_id")
            if isinstance(raw_request_id, str):
                request_id = raw_request_id.strip() or None
            elif raw_request_id is not None:
                request_id = str(raw_request_id)
        kind_label = str(kind or "info")
        kind_normalized = kind_label.lower()
        if request_id:
            if kind_normalized == "query":
                if request_id in self._ai_feed_pending_requests:
                    return
                self._ai_feed_pending_requests.add(request_id)
            else:
                self._ai_feed_pending_requests.discard(request_id)
        entry: Dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "kind": kind_label,
            "headline": _mask_sensitive_text(str(headline or "")),
        }
        if body:
            entry["body"] = _mask_sensitive_text(str(body))
        if data:
            sanitized_data = _mask_sensitive_payload(data)
            try:
                entry["data"] = json.loads(json.dumps(sanitized_data, default=lambda o: str(o)))
            except Exception:
                entry["data"] = sanitized_data
        feed = self.state.setdefault("ai_activity", [])
        feed.append(entry)
        if len(feed) > 250:
            del feed[:-250]
        self.state["ai_activity"] = feed
        try:
            log.info("AI_FEED %s | %s", entry["kind"], entry["headline"])
        except Exception:
            log.debug("AI_FEED %s | %s", entry.get("kind"), entry.get("headline"))
        if not getattr(self, "trade_mgr", None):
            return
        now = time.time()
        if force or (now - getattr(self, "_last_ai_activity_persist", 0.0)) >= 2.0:
            self._last_ai_activity_persist = now
            try:
                self.trade_mgr.save()
            except Exception as exc:
                log.debug(f"ai activity persist failed: {exc}")

    def _reset_decision_stats(self) -> None:
        baseline = {
            "taken": 0,
            "taken_by_bucket": {},
            "rejected": {},
            "rejected_total": 0,
            "last_updated": None,
        }
        existing = self.state.get("decision_stats")
        self.state["decision_stats"] = baseline
        if not getattr(self, "trade_mgr", None):
            return
        if existing != baseline:
            try:
                self.trade_mgr.save()
                if existing:
                    log.debug("decision stats reset on startup")
            except Exception as exc:
                log.debug(f"decision stats reset persist failed: {exc}")

    def _size_mult_from_bucket(self, bucket: str) -> float:
        return {"S": SIZE_MULT_S, "M": SIZE_MULT_M, "L": SIZE_MULT_L}.get(bucket, SIZE_MULT_S)

    def handle_symbol(
        self,
        symbol: str,
        pos_map: Dict[str, float],
        book_ticker: Optional[Dict[str, Any]] = None,
        order_book: Optional[Dict[str, Any]] = None,
    ):
        banned_map = self._banned_map()
        if symbol in banned_map:
            if self.decision_tracker:
                self.decision_tracker.record_rejection("banned_symbol")
            return
        fail_until = self.state.setdefault("fail_skip_until", {}).get(symbol)
        if fail_until and time.time() < fail_until:
            return
        elif fail_until and time.time() >= fail_until:
            try:
                self.state["fail_skip_until"].pop(symbol, None)
            except Exception:
                pass
        resume_cycle = 0
        cooldown_map = self.state.get("quote_volume_cooldown")
        if isinstance(cooldown_map, dict):
            raw_resume = cooldown_map.get(symbol)
            try:
                resume_cycle = int(raw_resume)
            except (TypeError, ValueError):
                resume_cycle = 0
        if resume_cycle and resume_cycle > getattr(self, "_current_cycle", 0):
            pending_queue = self.state.get("manual_trade_requests")
            if isinstance(pending_queue, list):
                for item in pending_queue:
                    if not isinstance(item, dict):
                        continue
                    if str(item.get("symbol") or "").upper() != symbol.upper():
                        continue
                    if str(item.get("status") or "pending").lower() != "pending":
                        continue
                    self._complete_manual_request(
                        item,
                        "failed",
                        error="Quote volume cooldown active",
                    )
            if self.decision_tracker:
                self.decision_tracker.record_rejection("quote_volume_cooldown")
            remaining = resume_cycle - getattr(self, "_current_cycle", 0)
            log.info(
                "Skip %s — quote volume cooldown active for %d more cycles.",
                symbol,
                max(remaining, 0),
            )
            return

        priority_side_hint: Optional[str] = None
        with self._ai_priority_lock:
            if symbol in self._ai_priority_hint:
                priority_side_hint = self._ai_priority_hint.pop(symbol, None)

        # bereits offene Position?
        amt = float(pos_map.get(symbol, 0.0) or 0.0)
        symbol_open = abs(amt) > 1e-12
        if MAX_OPEN_PER_SYMBOL > 0 and symbol_open:
            pending_queue = self.state.get("manual_trade_requests")
            if isinstance(pending_queue, list):
                for item in pending_queue:
                    if not isinstance(item, dict):
                        continue
                    if str(item.get("symbol") or "").upper() != symbol.upper():
                        continue
                    if str(item.get("status") or "pending").lower() != "pending":
                        continue
                    self._complete_manual_request(item, "failed", error="Per-symbol cap reached")
            if self.decision_tracker:
                self.decision_tracker.record_rejection("max_open_symbol")
            log.info(
                "Skip %s — per-symbol position cap reached (%d).",
                symbol,
                MAX_OPEN_PER_SYMBOL,
            )
            return

        active_positions_total = sum(
            1 for qty in pos_map.values() if abs(float(qty or 0.0)) > 1e-12
        )
        if (
            MAX_OPEN_GLOBAL > 0
            and not symbol_open
            and active_positions_total >= MAX_OPEN_GLOBAL
        ):
            pending_queue = self.state.get("manual_trade_requests")
            if isinstance(pending_queue, list):
                for item in pending_queue:
                    if not isinstance(item, dict):
                        continue
                    if str(item.get("symbol") or "").upper() != symbol.upper():
                        continue
                    if str(item.get("status") or "pending").lower() != "pending":
                        continue
                    self._complete_manual_request(
                        item,
                        "failed",
                        error="Global position cap reached",
                    )
            if self.decision_tracker:
                self.decision_tracker.record_rejection("max_open_global")
            log.info(
                "Skip %s — global position cap reached (%d/%d).",
                symbol,
                active_positions_total,
                MAX_OPEN_GLOBAL,
            )
            return

        sig, atr_abs, ctx, price = self.strategy.compute_signal(
            symbol, book_ticker=book_ticker, order_book=order_book
        )
        score_info: Dict[str, Any] = {}
        cache = getattr(self, "_symbol_score_cache", None)
        if isinstance(cache, dict):
            try:
                cached_entry = cache.get(symbol)
                if isinstance(cached_entry, dict):
                    score_info = cached_entry
            except Exception:
                score_info = {}
        if not score_info:
            strategy_cache = getattr(self.strategy, "_symbol_score_cache", None)
            if isinstance(strategy_cache, dict):
                try:
                    cached_entry = strategy_cache.get(symbol)
                    if isinstance(cached_entry, dict):
                        score_info = cached_entry
                except Exception:
                    score_info = {}
        if priority_side_hint and isinstance(ctx, dict):
            ctx.setdefault("ai_priority_side_hint", priority_side_hint)
        base_signal = sig

        manual_req = self._pop_manual_request(symbol)
        manual_override = manual_req is not None
        manual_notional = None
        if manual_override:
            requested_side = str(manual_req.get("side") or "").upper()
            if requested_side not in {"BUY", "SELL"}:
                self._complete_manual_request(manual_req, "failed", error="Invalid side")
                return
            sig = requested_side
            ctx["manual_override"] = True
            ctx["manual_request_id"] = manual_req.get("id")
            ctx["manual_source"] = manual_req.get("source")
            note = manual_req.get("note")
            if isinstance(note, str) and note.strip():
                ctx["manual_note"] = note.strip()
            raw_notional = manual_req.get("notional")
            if raw_notional is not None:
                try:
                    manual_notional = float(raw_notional)
                except (TypeError, ValueError):
                    manual_notional = None

        recovered_plan: Optional[Dict[str, Any]] = None
        if self.ai_advisor and not manual_override and base_signal == "NONE":
            resumed = self.ai_advisor.consume_signal_plan(symbol)
            if resumed:
                resumed_side, resumed_plan = resumed
                resumed_side = str(resumed_side or "").upper()
                if resumed_side in {"BUY", "SELL"}:
                    sig = resumed_side
                    recovered_plan = resumed_plan
                    ctx["ai_generated_signal"] = True
                    ctx["ai_recovered_signal_plan"] = True
                else:
                    recovered_plan = None

        if not manual_override and sig == "NONE" and not self.ai_advisor:
            return

        min_qvol = float(ctx.get("min_quote_volume", self.strategy.min_quote_vol))
        quote_volume = float(ctx.get("quote_volume", 0.0) or 0.0)
        if min_qvol > 0 and quote_volume < min_qvol:
            if quote_volume <= 0:
                try:
                    _, _, fresh_qv = self.strategy._get_qv_score(symbol)
                    quote_volume = float(fresh_qv)
                    ctx["quote_volume"] = quote_volume
                except Exception:
                    pass
            if quote_volume < min_qvol:
                log.info(
                    "Skip %s — quote volume %.2f below minimum %.2f",
                    symbol,
                    quote_volume,
                    min_qvol,
                )
                cooldown_map = self.state.get("quote_volume_cooldown")
                if not isinstance(cooldown_map, dict):
                    cooldown_map = {}
                    self.state["quote_volume_cooldown"] = cooldown_map
                resume_after = getattr(self, "_current_cycle", 0) + QUOTE_VOLUME_COOLDOWN_CYCLES + 1
                if cooldown_map.get(symbol) != resume_after:
                    cooldown_map[symbol] = resume_after
                    self._quote_volume_cooldown_dirty = True
                if manual_override:
                    self._complete_manual_request(
                        manual_req,
                        "failed",
                        error="Quote volume below minimum threshold",
                    )
                return

        sentinel_info = {
            "label": "green",
            "event_risk": 0.0,
            "hype_score": 0.0,
            "actions": {"size_factor": 1.0, "hard_block": False},
            "events": [],
        }
        if self.sentinel:
            try:
                sentinel_info = self.sentinel.evaluate(symbol, ctx)
            except Exception as exc:
                log.debug(f"sentinel evaluate fail {symbol}: {exc}")
        actions = sentinel_info.get("actions", {}) or {}
        event_risk = float(sentinel_info.get("event_risk", 0.0) or 0.0)
        hype_score = float(sentinel_info.get("hype_score", 0.0) or 0.0)

        if self.ai_advisor:
            try:
                ctx.setdefault("side", sig)
                self.ai_advisor.inject_context_features(symbol, ctx)
            except Exception as exc:
                log.debug(f"context feature inject failed {symbol}: {exc}")

        # Policy: Gate + Size
        size_mult = SIZE_MULT_S
        bucket = "S"
        alpha_prob = None
        alpha_conf = None
        if manual_override:
            bucket = manual_req.get("bucket") or "MANUAL"
            override_mult = manual_req.get("size_multiplier")
            if override_mult is not None:
                try:
                    size_mult = float(override_mult)
                except (TypeError, ValueError):
                    pass
        elif sig != "NONE" and BANDIT_ENABLED and self.policy:
            try:
                decision, extras = self.policy.decide(ctx)  # "TAKE"/"SKIP" + {"size_bucket": "..."}
                bucket = extras.get("size_bucket", "S")
                size_mult = self._size_mult_from_bucket(bucket)
                alpha_prob = extras.get("alpha_prob")
                alpha_conf = extras.get("alpha_conf")
                if decision != "TAKE":
                    if alpha_prob is not None:
                        log.debug(f"policy skip {symbol}: alpha={alpha_prob:.3f} conf={alpha_conf or 0.0:.2f}")
                    if self.decision_tracker:
                        self.decision_tracker.record_rejection("policy_filter")
                    return
            except Exception as e:
                log.debug(f"policy decide fail: {e}")

        if alpha_prob is not None:
            ctx["alpha_prob"] = float(alpha_prob)
            ctx["alpha_conf"] = float(alpha_conf or 0.0)

        policy_size_mult = float(size_mult)
        ctx["policy_bucket"] = bucket
        ctx["policy_size_multiplier"] = policy_size_mult
        sentinel_factor = float(actions.get("size_factor", 1.0) or 1.0)
        sentinel_factor *= max(0.35, 1.0 - event_risk * 0.65)
        if hype_score > 1.2:
            sentinel_factor *= min(1.4, 1.0 + (hype_score - 1.0) * 0.25)
        elif hype_score < 0.4:
            sentinel_factor *= max(0.55, 0.85 + hype_score * 0.3)
        tuning_bucket_factor = 1.0
        overrides_sl_mult: Optional[float] = None
        overrides_tp_mult: Optional[float] = None
        playbook_size_factor = 1.0
        playbook_sl_factor = 1.0
        playbook_tp_factor = 1.0
        sentinel_soft_block = False
        if actions.get("hard_block") and not manual_override:
            if event_risk >= 0.85:
                veto_target = (
                    sig
                    if sig != "NONE"
                    else base_signal
                    if base_signal != "NONE"
                    else "opportunity"
                )
                log.info(
                    "Sentinel veto %s due to %s risk (event=%.2f, hype=%.2f)",
                    symbol,
                    sentinel_info.get("label", "red"),
                    event_risk,
                    hype_score,
                )
                self._log_ai_activity(
                    "decision",
                    f"Sentinel vetoed {symbol}",
                    body=(
                        f"Risk label {sentinel_info.get('label', 'red')} blocked the {veto_target} setup "
                        "before contacting the strategy AI."
                    ),
                    data={
                        "symbol": symbol,
                        "side": veto_target,
                        "event_risk": event_risk,
                        "hype_score": hype_score,
                        "ai_request": False,
                    },
                    force=True,
                )
                if self.decision_tracker:
                    self.decision_tracker.record_rejection("sentinel_veto")
                return
            sentinel_soft_block = True
            ctx["sentinel_soft_block"] = True
            log.info(
                "Sentinel soft-block for %s — scaling exposure (event=%.2f, hype=%.2f)",
                symbol,
                event_risk,
                hype_score,
            )
            self._log_ai_activity(
                "decision",
                f"Sentinel throttled {symbol}",
                body="Risk spike detected; reducing position size instead of full veto.",
                data={
                    "symbol": symbol,
                    "side": sig if sig != "NONE" else base_signal,
                    "event_risk": event_risk,
                    "hype_score": hype_score,
                    "ai_request": False,
                },
                force=True,
            )
        if not manual_override:
            tuning_overrides = self.state.get("tuning_overrides")
            if isinstance(tuning_overrides, dict):
                raw_size_bias = tuning_overrides.get("size_bias")
                if isinstance(raw_size_bias, dict):
                    bias_value = raw_size_bias.get(bucket)
                    if bias_value is None and sig in {"BUY", "SELL"}:
                        bias_value = raw_size_bias.get(sig.upper())
                    try:
                        if bias_value is not None:
                            tuning_bucket_factor = max(0.4, min(2.5, float(bias_value)))
                    except (TypeError, ValueError):
                        tuning_bucket_factor = 1.0
                try:
                    overrides_sl_mult = float(tuning_overrides.get("sl_atr_mult"))
                except (TypeError, ValueError):
                    overrides_sl_mult = None
                try:
                    overrides_tp_mult = float(tuning_overrides.get("tp_atr_mult"))
                except (TypeError, ValueError):
                    overrides_tp_mult = None
            playbook_state = self.state.get("ai_playbook")
            active_playbook = (
                playbook_state.get("active") if isinstance(playbook_state, dict) else {}
            )
            if isinstance(active_playbook, dict):
                size_bias_map = active_playbook.get("size_bias")
                if isinstance(size_bias_map, dict) and sig in {"BUY", "SELL"}:
                    try:
                        playbook_size_factor = max(
                            0.4,
                            min(2.5, float(size_bias_map.get(sig.upper(), 1.0))),
                        )
                    except (TypeError, ValueError):
                        playbook_size_factor = 1.0
                try:
                    playbook_sl_factor = float(active_playbook.get("sl_bias", 1.0))
                except (TypeError, ValueError):
                    playbook_sl_factor = 1.0
                try:
                    playbook_tp_factor = float(active_playbook.get("tp_bias", 1.0))
                except (TypeError, ValueError):
                    playbook_tp_factor = 1.0
        size_mult = policy_size_mult * sentinel_factor
        if not manual_override:
            size_mult *= tuning_bucket_factor
            size_mult *= playbook_size_factor
            budget_factor = ctx.get("budget_bias")
            try:
                if budget_factor is not None:
                    bias_val = max(0.1, float(budget_factor))
                    applied = max(0.25, min(1.9, bias_val))
                    size_mult *= applied
                    ctx["budget_bias_applied"] = float(applied)
            except (TypeError, ValueError):
                pass
            perf_bias_val = score_info.get("perf_bias") if isinstance(score_info, dict) else None
            if isinstance(perf_bias_val, (int, float)):
                perf_mult = max(0.6, min(1.6, float(perf_bias_val)))
                size_mult *= perf_mult
                ctx["universe_perf_multiplier"] = float(perf_mult)
        if sentinel_soft_block and not manual_override:
            soft_mult = max(0.2, 1.0 - event_risk * 0.8)
            size_mult *= soft_mult
            ctx["sentinel_soft_multiplier"] = float(soft_mult)
        if not manual_override:
            size_mult = max(SIZE_MULT_FLOOR, size_mult)
            ctx["size_multiplier_floor"] = float(SIZE_MULT_FLOOR)
        else:
            size_mult = max(0.0, size_mult)
        ctx["tuning_size_bucket_multiplier"] = float(tuning_bucket_factor)
        ctx["playbook_size_multiplier"] = float(playbook_size_factor)
        ctx["sentinel_factor"] = sentinel_factor
        ctx["sentinel_event_risk"] = event_risk
        ctx["sentinel_hype"] = hype_score
        ctx["sentinel_label"] = sentinel_info.get("label", "green")
        if "budget_bias_applied" not in ctx:
            try:
                ctx["budget_bias_applied"] = float(ctx.get("budget_bias", 1.0) or 1.0)
            except Exception:
                ctx["budget_bias_applied"] = 1.0

        # Entry/SL/TP foundation
        try:
            bt = self.exchange.get_book_ticker(symbol)
            ask_px = float(bt.get("askPrice", 0.0) or 0.0)
            bid_px = float(bt.get("bidPrice", 0.0) or 0.0)
        except Exception:
            ask_px = 0.0
            bid_px = 0.0

        mid_px = (ask_px + bid_px) / 2.0 if ask_px > 0 and bid_px > 0 else price
        if mid_px <= 0:
            mid_px = price
        if ask_px <= 0:
            ask_px = mid_px
        if bid_px <= 0:
            bid_px = mid_px

        ctx.setdefault("mid_price", float(mid_px))
        ctx["book_ask"] = float(ask_px)
        ctx["book_bid"] = float(bid_px)
        ctx["book"] = {"ask": float(ask_px), "bid": float(bid_px), "mid": float(mid_px)}
        ctx["base_signal"] = base_signal
        try:
            ctx["max_leverage_cap"] = float(self._symbol_leverage_cap(symbol))
        except Exception:
            pass

        atr_hint = float(ctx.get("atr_abs") or 0.0)
        if atr_abs <= 0 and atr_hint > 0:
            atr_abs = atr_hint
        if atr_abs <= 0:
            if manual_override:
                self._complete_manual_request(manual_req, "failed", error="ATR unavailable")
            return

        dynamic_sl_mult = SL_ATR_MULT
        dynamic_tp_mult = TP_ATR_MULT
        if overrides_sl_mult is not None:
            dynamic_sl_mult *= max(0.4, min(2.5, float(overrides_sl_mult)))
        if overrides_tp_mult is not None:
            dynamic_tp_mult *= max(0.6, min(3.0, float(overrides_tp_mult)))
        if not manual_override:
            dynamic_sl_mult *= max(0.4, min(2.5, playbook_sl_factor))
            dynamic_tp_mult *= max(0.6, min(3.0, playbook_tp_factor))
        sl_dist = max(1e-9, dynamic_sl_mult * atr_abs)
        tp_dist = max(1e-9, dynamic_tp_mult * atr_abs)
        ctx["sl_atr_multiplier_dynamic"] = float(dynamic_sl_mult)
        ctx["tp_atr_multiplier_dynamic"] = float(dynamic_tp_mult)

        ai_meta: Optional[Dict[str, Any]] = None
        plan: Optional[Dict[str, Any]] = None
        plan_origin: Optional[str] = None
        plan_entry: Optional[float] = None
        plan_stop: Optional[float] = None
        plan_take: Optional[float] = None

        remaining_budget = self.budget_tracker.remaining()
        include_budget_context = False
        if remaining_budget is not None:
            threshold = 0.0
            if self.budget_tracker.limit > 0:
                threshold = 0.25 * float(self.budget_tracker.limit)
            try:
                avg_cost = self.budget_tracker.average_cost(
                    kind="plan", model=AI_MODEL
                )
            except Exception:
                avg_cost = None
            if avg_cost:
                threshold = max(threshold, float(avg_cost) * 3.0)
            threshold = max(0.5, min(5.0, threshold))
            if remaining_budget <= threshold:
                include_budget_context = True
        if include_budget_context and remaining_budget is not None:
            ctx["budget_remaining"] = float(remaining_budget)
            ctx["budget_spent"] = float(self.budget_tracker.spent())
        else:
            ctx.pop("budget_remaining", None)
            ctx.pop("budget_spent", None)
        open_positions_ctx = {k: float(v) for k, v in pos_map.items() if abs(float(v or 0.0)) > 1e-12}
        if open_positions_ctx:
            ctx["open_positions"] = open_positions_ctx
            ctx["active_positions"] = len(open_positions_ctx)
        else:
            ctx.pop("open_positions", None)
            ctx.pop("active_positions", None)

        if self.ai_advisor and not manual_override:
            skip_reason_raw = ctx.get("skip_reason")
            skip_reason = str(skip_reason_raw or "").strip()
            normalized_skip = skip_reason.lower()
            if normalized_skip in {"no_cross"} or (normalized_skip and normalized_skip not in {"none"}):
                log.debug(
                    "Skip %s — base strategy reported %s; avoiding AI trend scan.",
                    symbol,
                    skip_reason,
                )
                return
            if min_qvol > 0 and float(ctx.get("quote_volume", 0.0) or 0.0) < min_qvol:
                return
            price_for_plan = mid_px if mid_px > 0 else price
            if sig == "NONE":
                plan = self.ai_advisor.plan_trend_trade(
                    symbol,
                    price_for_plan,
                    sl_dist,
                    tp_dist,
                    ctx,
                    sentinel_info,
                    atr_abs,
                    async_mode=True,
                )
                plan_origin = "trend"
                decision_summary = {
                    "decision": plan.get("decision"),
                    "take": bool(plan.get("take", False)),
                    "decision_reason": plan.get("decision_reason"),
                    "decision_note": plan.get("decision_note"),
                    "confidence": plan.get("confidence"),
                    "size_multiplier": plan.get("size_multiplier"),
                    "sl_multiplier": plan.get("sl_multiplier"),
                    "tp_multiplier": plan.get("tp_multiplier"),
                    "leverage": plan.get("leverage"),
                    "origin": plan_origin,
                    "event_risk": plan.get("event_risk"),
                    "hype_score": plan.get("hype_score"),
                    "sentinel_label": sentinel_info.get("label"),
                    "request_id": plan.get("request_id"),
                }
                explanation = plan.get("explanation")
                trend_side = plan.get("side")
                if isinstance(trend_side, str) and trend_side.strip():
                    decision_summary["side"] = trend_side.strip().upper()
                if plan.get("_pending"):
                    if self.ai_advisor.should_log_pending(plan):
                        request_id = plan.get("request_id")
                        self._log_ai_activity(
                            "query",
                            f"AI trend scan requested for {symbol}",
                            body="Consulting the strategy AI for an autonomous opportunity.",
                            data={
                                "symbol": symbol,
                                "side": decision_summary.get("side"),
                                "origin": "trend",
                                "sentinel_label": sentinel_info.get("label"),
                                "event_risk": float(sentinel_info.get("event_risk", 0.0) or 0.0),
                                "hype_score": float(sentinel_info.get("hype_score", 0.0) or 0.0),
                                "decision_reason": plan.get("decision_reason"),
                                "decision_note": plan.get("decision_note"),
                                "request_id": request_id,
                            },
                            force=True,
                        )
                    return
                if not bool(plan.get("take", False)):
                    ctx["ai_plan_origin"] = plan_origin
                    reason_token = str(
                        plan.get("decision_reason")
                        or plan.get("decision_note")
                        or ""
                    ).strip().lower()
                    if (
                        self.ai_advisor
                        and getattr(self.ai_advisor, "budget_learner", None)
                        and not plan.get("ai_fallback")
                        and reason_token
                        and not reason_token.startswith("plan_")
                        and reason_token not in {"budget_bias", "sentinel_block"}
                    ):
                        meta_payload = {
                            "origin": plan_origin,
                            "request_id": plan.get("request_id"),
                            "note": plan.get("decision_note"),
                            "reason": plan.get("decision_reason"),
                            "confidence": plan.get("confidence"),
                        }
                        exp_r = None
                        if isinstance(ctx, dict):
                            exp_r = ctx.get("expected_r")
                        if exp_r is None:
                            exp_r = plan.get("expected_r")
                        plan_ctx = plan.get("context") if isinstance(plan.get("context"), dict) else None
                        if exp_r is None and plan_ctx:
                            exp_r = plan_ctx.get("expected_r")
                        try:
                            if exp_r is not None:
                                meta_payload["expected_r"] = float(exp_r)
                        except (TypeError, ValueError):
                            pass
                        try:
                            self.ai_advisor.budget_learner.record_skip(
                                symbol,
                                "trend",
                                plan.get("decision_reason") or plan.get("decision_note"),
                                meta_payload,
                            )
                        except Exception:
                            pass
                    if self.decision_tracker:
                        self.decision_tracker.record_rejection("ai_trend_skip", force=True)
                    if isinstance(explanation, str) and explanation.strip():
                        self._log_ai_activity(
                            "analysis",
                            f"{symbol} trend scan analysed",
                            body=explanation,
                            data={"symbol": symbol, **decision_summary},
                        )
                    note_body = (
                        plan.get("decision_note")
                        or plan.get("decision_reason")
                        or (explanation if isinstance(explanation, str) else None)
                    )
                    self._log_ai_activity(
                        "decision",
                        f"AI declined {symbol}",
                        body=note_body,
                        data={"symbol": symbol, **decision_summary},
                        force=True,
                    )
                    return
                side = str(plan.get("side") or "").upper()
                if side not in {"BUY", "SELL"}:
                    if self.decision_tracker:
                        self.decision_tracker.record_rejection("ai_trend_invalid", force=True)
                    return
                sig = side
                ctx["ai_generated_signal"] = True
                ctx["ai_plan_origin"] = plan_origin
                decision_summary["side"] = sig
                if isinstance(explanation, str) and explanation.strip():
                    self._log_ai_activity(
                        "analysis",
                        f"{symbol} trend scan analysed",
                        body=explanation,
                        data={"symbol": symbol, "side": sig, **decision_summary},
                    )
            else:
                plan_origin = str((recovered_plan or {}).get("origin") or "signal")
                plan: Dict[str, Any]
                ready_plan: Optional[Dict[str, Any]] = recovered_plan
                if manual_override and manual_req:
                    ready_plan = manual_req.pop("ai_ready_plan", None)
                    if ready_plan:
                        manual_req.pop("ai_ready_at", None)
                        manual_req.pop("ai_pending_key", None)
                        manual_req.pop("ai_request_id", None)
                        manual_req.pop("decision_note", None)
                        self._manual_state_dirty = True
                if ready_plan:
                    plan = ready_plan
                else:
                    plan = self.ai_advisor.plan_trade(
                        symbol,
                        sig,
                        price_for_plan,
                        sl_dist,
                        tp_dist,
                        ctx,
                        sentinel_info,
                        atr_abs,
                        async_mode=True,
                    )
                decision_summary = {
                    "decision": plan.get("decision"),
                    "take": bool(plan.get("take", True)),
                    "decision_reason": plan.get("decision_reason"),
                    "decision_note": plan.get("decision_note"),
                    "confidence": plan.get("confidence"),
                    "size_multiplier": plan.get("size_multiplier"),
                    "sl_multiplier": plan.get("sl_multiplier"),
                    "tp_multiplier": plan.get("tp_multiplier"),
                    "leverage": plan.get("leverage"),
                    "origin": plan_origin,
                    "event_risk": plan.get("event_risk"),
                    "hype_score": plan.get("hype_score"),
                    "sentinel_label": sentinel_info.get("label"),
                    "request_id": plan.get("request_id"),
                }
                explanation = plan.get("explanation")
                if plan.get("_pending"):
                    if manual_override and manual_req:
                        manual_req["status"] = "ai_pending"
                        manual_req["ai_pending_key"] = plan.get("_pending_key")
                        manual_req["ai_request_id"] = plan.get("request_id")
                        manual_req["decision_note"] = plan.get("decision_note")
                        manual_req["updated_at"] = time.time()
                        self._manual_state_dirty = True
                    if self.ai_advisor.should_log_pending(plan):
                        request_id = plan.get("request_id")
                        self._log_ai_activity(
                            "query",
                            f"AI review requested for {symbol}",
                            body=f"Consulting the strategy AI for the {sig} signal.",
                            data={
                                "symbol": symbol,
                                "side": sig,
                                "origin": "signal",
                                "sentinel_label": sentinel_info.get("label"),
                                "event_risk": float(sentinel_info.get("event_risk", 0.0) or 0.0),
                                "hype_score": float(sentinel_info.get("hype_score", 0.0) or 0.0),
                                "decision_reason": plan.get("decision_reason"),
                                "decision_note": plan.get("decision_note"),
                                "request_id": request_id,
                            },
                            force=True,
                        )
                    return
                ctx["ai_plan_origin"] = plan_origin
                decision_summary["side"] = sig
                if not bool(plan.get("take", True)):
                    reason_token = str(
                        plan.get("decision_reason")
                        or plan.get("decision_note")
                        or ""
                    ).strip().lower()
                    if (
                        self.ai_advisor
                        and getattr(self.ai_advisor, "budget_learner", None)
                        and not plan.get("ai_fallback")
                        and reason_token
                        and not reason_token.startswith("plan_")
                        and reason_token not in {"budget_bias", "sentinel_block"}
                    ):
                        meta_payload = {
                            "origin": plan_origin,
                            "request_id": plan.get("request_id"),
                            "note": plan.get("decision_note"),
                            "reason": plan.get("decision_reason"),
                            "side": sig,
                            "confidence": plan.get("confidence"),
                        }
                        exp_r = None
                        if isinstance(ctx, dict):
                            exp_r = ctx.get("expected_r")
                        if exp_r is None:
                            exp_r = plan.get("expected_r")
                        plan_ctx = plan.get("context") if isinstance(plan.get("context"), dict) else None
                        if exp_r is None and plan_ctx:
                            exp_r = plan_ctx.get("expected_r")
                        try:
                            if exp_r is not None:
                                meta_payload["expected_r"] = float(exp_r)
                        except (TypeError, ValueError):
                            pass
                        try:
                            self.ai_advisor.budget_learner.record_skip(
                                symbol,
                                "plan",
                                plan.get("decision_reason") or plan.get("decision_note"),
                                meta_payload,
                            )
                        except Exception:
                            pass
                    if self.decision_tracker:
                        self.decision_tracker.record_rejection("ai_decision", force=True)
                    if isinstance(explanation, str) and explanation.strip():
                        self._log_ai_activity(
                            "analysis",
                            f"{symbol} {sig} signal analysed",
                            body=explanation,
                            data={"symbol": symbol, "side": sig, **decision_summary},
                        )
                    note_body = (
                        plan.get("decision_note")
                        or plan.get("decision_reason")
                        or (explanation if isinstance(explanation, str) else None)
                    )
                    self._log_ai_activity(
                        "decision",
                        f"AI rejected {symbol}",
                        body=note_body,
                        data={"symbol": symbol, "side": sig, **decision_summary},
                        force=True,
                    )
                    return
                if isinstance(explanation, str) and explanation.strip():
                    self._log_ai_activity(
                        "analysis",
                        f"{symbol} {sig} signal analysed",
                        body=explanation,
                        data={"symbol": symbol, "side": sig, **decision_summary},
                    )

            plan_size = float(plan.get("size_multiplier", 1.0) or 0.0)
            plan_sl_mult = float(plan.get("sl_multiplier", 1.0) or 1.0)
            plan_tp_mult = float(plan.get("tp_multiplier", 1.0) or 1.0)
            size_mult *= plan_size
            if not manual_override:
                size_mult = max(SIZE_MULT_FLOOR, size_mult)
            sl_dist *= plan_sl_mult
            tp_dist *= plan_tp_mult
            leverage = plan.get("leverage")
            if isinstance(leverage, (int, float)):
                leverage = self._clamp_leverage(symbol, leverage)
                plan["leverage"] = leverage
                ctx["ai_leverage"] = float(leverage)
            plan_entry = plan.get("entry_price")
            plan_stop = plan.get("stop_loss")
            plan_take = plan.get("take_profit")
            ai_meta = {
                "plan": plan,
                "origin": plan_origin,
                "sentinel": sentinel_info,
                "budget": self.ai_advisor.budget_snapshot(),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
            if plan.get("ai_fallback"):
                ai_meta["fallback"] = True
            if isinstance(explanation, str) and explanation.strip():
                ai_meta["explanation"] = explanation.strip()
            if plan.get("decision_reason"):
                ai_meta["decision_reason"] = plan.get("decision_reason")
            if plan.get("decision_note"):
                ai_meta["decision_note"] = plan.get("decision_note")
            risk_note = plan.get("risk_note")
            if isinstance(risk_note, str) and risk_note.strip():
                ai_meta["risk_note"] = risk_note.strip()
            confidence = plan.get("confidence")
            if isinstance(confidence, (int, float)):
                ai_meta["confidence"] = float(confidence)
                ctx["ai_confidence"] = float(confidence)
            if isinstance(plan_entry, (int, float)) and plan_entry > 0:
                ctx["ai_entry_price"] = float(plan_entry)
            if isinstance(plan_stop, (int, float)) and plan_stop > 0:
                ctx["ai_stop_loss"] = float(plan_stop)
            if isinstance(plan_take, (int, float)) and plan_take > 0:
                ctx["ai_take_profit"] = float(plan_take)
            note_body = (
                plan.get("decision_note")
                or plan.get("decision_reason")
                or (explanation if isinstance(explanation, str) else None)
            )
            if not note_body:
                note_parts: List[str] = []
                ema_fast_val = ctx.get("ema_fast")
                ema_slow_val = ctx.get("ema_slow")
                if isinstance(ema_fast_val, (int, float)) and isinstance(ema_slow_val, (int, float)):
                    if ema_fast_val > ema_slow_val:
                        relation = "above"
                    elif ema_fast_val < ema_slow_val:
                        relation = "below"
                    else:
                        relation = "aligned with"
                    note_parts.append(
                        f"EMA fast {ema_fast_val:.4f} {relation} EMA slow {ema_slow_val:.4f}"
                    )
                adx_val = ctx.get("adx")
                if isinstance(adx_val, (int, float)):
                    note_parts.append(f"ADX {adx_val:.1f}")
                rsi_val = ctx.get("rsi")
                if isinstance(rsi_val, (int, float)):
                    note_parts.append(f"RSI {rsi_val:.1f}")
                stoch_d_val = ctx.get("stoch_rsi_d")
                if isinstance(stoch_d_val, (int, float)):
                    note_parts.append(f"StochRSI%D {stoch_d_val:.1f}")
                bb_pos_val = ctx.get("bb_position")
                if isinstance(bb_pos_val, (int, float)):
                    note_parts.append(f"BB% {bb_pos_val * 100.0:.0f}")
                super_dir_val = ctx.get("supertrend_dir")
                super_val = ctx.get("supertrend")
                if isinstance(super_dir_val, (int, float)):
                    if super_dir_val > 0:
                        dir_txt = "bullish"
                    elif super_dir_val < 0:
                        dir_txt = "bearish"
                    else:
                        dir_txt = "neutral"
                    if isinstance(super_val, (int, float)) and super_val > 0:
                        note_parts.append(f"SuperTrend {dir_txt} @{super_val:.4f}")
                    else:
                        note_parts.append(f"SuperTrend {dir_txt}")
                sentinel_label = (sentinel_info or {}).get("label") if sentinel_info else None
                if isinstance(sentinel_label, str) and sentinel_label:
                    note_parts.append(f"Sentinel {sentinel_label}")
                if note_parts:
                    note_body = " · ".join(note_parts)
            decision_headline = f"AI approved {symbol}"
            if plan.get("ai_fallback"):
                decision_headline = f"Fallback engaged for {symbol}"
            self._log_ai_activity(
                "decision",
                decision_headline,
                body=note_body,
                data={"symbol": symbol, "side": sig, **decision_summary},
                force=True,
            )
            if isinstance(leverage, (int, float)):
                leverage = self._clamp_leverage(symbol, leverage)
                plan["leverage"] = leverage
            if isinstance(leverage, (int, float)) and leverage > 0:
                leverage_state = self.state.setdefault("symbol_leverage", {})
                current = float(leverage_state.get(symbol, 0.0) or 0.0)
                if abs(leverage - current) >= 0.5:
                    try:
                        self.exchange.set_leverage(symbol, leverage)
                        leverage_state[symbol] = float(leverage)
                    except Exception as exc:
                        log.debug(f"set leverage fail {symbol}: {exc}")
                        ai_meta.setdefault("warnings", []).append("Leverage update failed")
            fasttp_overrides = plan.get("fasttp_overrides")
            if isinstance(fasttp_overrides, dict):
                ai_meta["fasttp_overrides"] = fasttp_overrides
        elif manual_override:
            ai_meta = {
                "manual_request": True,
                "request_id": manual_req.get("id"),
                "source": manual_req.get("source"),
            }
            raw_note = manual_req.get("note")
            if isinstance(raw_note, str) and raw_note.strip():
                ai_meta["note"] = raw_note.strip()
            payload = manual_req.get("payload")
            if isinstance(payload, dict):
                ai_meta["payload"] = payload
            override_mult = manual_req.get("size_multiplier")
            if override_mult is not None:
                try:
                    ai_meta["size_multiplier"] = float(override_mult)
                except (TypeError, ValueError):
                    pass
            if manual_notional is not None:
                try:
                    ai_meta["notional"] = float(manual_notional)
                except (TypeError, ValueError):
                    pass
        elif sig == "NONE":
            return

        if sig == "NONE":
            return

        is_buy = sig == "BUY"
        px = ask_px if is_buy else bid_px
        if isinstance(plan_entry, (int, float)) and plan_entry > 0:
            px = float(plan_entry)
        elif px <= 0:
            px = mid_px if mid_px > 0 else price

        sl = px - sl_dist if is_buy else px + sl_dist
        if isinstance(plan_stop, (int, float)) and plan_stop > 0:
            stop_val = float(plan_stop)
            valid_stop = stop_val < px if is_buy else stop_val > px
            if valid_stop and abs(px - stop_val) >= 1e-9:
                sl = stop_val
                sl_dist = abs(px - sl)
            else:
                if ai_meta is not None:
                    ai_meta.setdefault("warnings", []).append("Invalid AI stop-loss level ignored")

        tp = px + tp_dist if is_buy else px - tp_dist
        if isinstance(plan_take, (int, float)) and plan_take > 0:
            take_val = float(plan_take)
            valid_tp = take_val > px if is_buy else take_val < px
            if valid_tp and abs(px - take_val) >= 1e-9:
                tp = take_val
                tp_dist = abs(tp - px)
            else:
                if ai_meta is not None:
                    ai_meta.setdefault("warnings", []).append("Invalid AI take-profit level ignored")

        sl = self._clamp_to_price_band(symbol, sl)
        tp = self._clamp_to_price_band(symbol, tp)

        sl_dist = max(sl_dist, abs(px - sl))
        tp_dist = max(tp_dist, abs(tp - px))

        if abs(px - sl) < 1e-8 or abs(tp - px) < 1e-8:
            if ai_meta is not None:
                ai_meta.setdefault("warnings", []).append("Degenerate trade levels cancelled")
            self._log_ai_activity(
                "decision",
                f"Invalid AI levels for {symbol}",
                body="Stop-loss or take-profit collapsed into the entry price; trade aborted.",
                data={
                    "symbol": symbol,
                    "side": sig,
                    "entry": float(px),
                    "stop": float(sl),
                    "target": float(tp),
                    "plan_origin": plan_origin,
                },
                force=True,
            )
            if self.decision_tracker:
                self.decision_tracker.record_rejection("invalid_levels", force=True)
            if manual_override:
                self._complete_manual_request(manual_req, "failed", error="Invalid trade levels")
            return

        if not manual_override:
            size_mult = max(SIZE_MULT_FLOOR, size_mult)
        mult_cap = SIZE_MULT_CAP if SIZE_MULT_CAP > 0 else 5.0
        size_mult = clamp(size_mult, 0.0, mult_cap)
        if size_mult <= 0:
            self._log_ai_activity(
                "decision",
                f"Sized out {symbol}",
                body="Position sizing reduced to zero after risk controls.",
                data={"symbol": symbol, "side": sig, "size_multiplier": size_mult},
                force=True,
            )
            if self.decision_tracker:
                self.decision_tracker.record_rejection("ai_risk_zero")
            if manual_override:
                self._complete_manual_request(manual_req, "failed", error="Position size reduced to zero")
            return

        tick = float(self.risk.symbol_filters.get(symbol, {}).get("tickSize", 0.0001) or 0.0001)
        sl = round_price(symbol, sl, tick)
        tp = round_price(symbol, tp, tick)

        step = float(self.risk.symbol_filters.get(symbol, {}).get("stepSize", 0.0001) or 0.0001)

        qty = self.risk.compute_qty(symbol, px, sl, size_mult)
        if manual_override and manual_notional is not None:
            manual_qty = manual_notional / max(px, 1e-9)
            manual_qty = max(0.0, math.floor(manual_qty / step) * step)
            if manual_qty > 0:
                qty = manual_qty
        if qty <= 0:
            self._log_ai_activity(
                "decision",
                f"No size for {symbol}",
                body="Risk engine returned zero quantity.",
                data={"symbol": symbol, "side": sig, "size_multiplier": size_mult},
                force=True,
            )
            if self.decision_tracker:
                self.decision_tracker.record_rejection("position_size")
            if manual_override:
                self._complete_manual_request(manual_req, "failed", error="Risk engine returned zero quantity")
            return

        q_str = format_qty(qty, step)

        # Entry
        try:
            order_params = {"symbol": symbol, "side": sig, "type": "MARKET", "quantity": q_str}
            order_params["stopLoss"] = build_bracket_payload("SL", sig, sl)
            order_params["takeProfit"] = build_bracket_payload("TP", sig, tp)
            try:
                order_response = self.exchange.post_order(order_params)
            except requests.HTTPError as exc:
                status = getattr(exc.response, "status_code", None)
                detail = ""
                error_code: Optional[int] = None
                error_msg: Optional[str] = None
                if exc.response is not None:
                    try:
                        payload = exc.response.json()
                        detail = json.dumps(payload)[:160]
                        raw_code = payload.get("code")
                        try:
                            error_code = int(raw_code)
                        except (TypeError, ValueError):
                            error_code = None
                        msg_val = payload.get("msg")
                        if isinstance(msg_val, str):
                            error_msg = msg_val
                    except ValueError:
                        detail = (exc.response.text or "")[:160]
                if error_code == -4002:
                    self._handle_price_filter_rejection(
                        symbol,
                        sig,
                        px,
                        sl,
                        tp,
                        detail=error_msg or detail,
                        manual_override=manual_override,
                        manual_req=manual_req,
                    )
                    return
                if status == 400:
                    if not detail and exc.response is not None:
                        try:
                            detail = exc.response.text[:160]
                        except Exception:
                            detail = ""
                    self._ban_symbol(symbol, "order_bad_request", details=detail or None)
                raise
            # Brackets – versuche neue Signatur (qty+entry), fallback auf alte
            if PAPER:
                self.exchange.paper_register_brackets(
                    symbol,
                    sig,
                    float(q_str),
                    px,
                    sl,
                    tp,
                    bucket=bucket,
                    ctx=ctx,
                    ai_meta=ai_meta,
                )
                ok = True
            else:
                try:
                    ok = self.guard.ensure_after_entry(symbol, sig, float(q_str), px, sl, tp)
                except TypeError:
                    ok = self.guard.ensure_after_entry(symbol, sig, sl, tp)
            if not ok:
                log.warning(f"Bracket orders for {symbol} could not be fully created.")
            if self.decision_tracker and not manual_override:
                self.decision_tracker.record_acceptance(bucket, persist=False)
            self.trade_mgr.note_entry(symbol, px, sl, tp, sig, float(q_str), ctx, bucket, atr_abs, meta=ai_meta)
            final_order: Optional[Dict[str, Any]] = None
            order_trades: List[Dict[str, Any]] = []
            try:
                final_order, order_trades = self.exchange.await_order_fill(symbol, order_response)
            except Exception as exc:
                log.debug(f"order fill await failed for {symbol}: {exc}")
            if final_order or order_trades:
                try:
                    self.trade_mgr.register_entry_fill(symbol, final_order, order_trades)
                except Exception as exc:
                    log.debug(f"register entry fill failed for {symbol}: {exc}")
            live_trade = self.state.get("live_trades", {}).get(symbol, {})
            fill_qty = _coerce_float((final_order or {}).get("executedQty"))
            if fill_qty is None or fill_qty <= 0:
                fill_qty = _coerce_float(live_trade.get("qty")) or float(q_str)
            fill_price = _coerce_float((final_order or {}).get("avgPrice"))
            if fill_price is None or fill_price <= 0:
                fill_price = _coerce_float(live_trade.get("entry")) or px
            if manual_override:
                self._complete_manual_request(
                    manual_req,
                    "filled",
                    result={
                        "quantity": float(fill_qty or 0.0),
                        "entry": float(fill_price or px),
                        "stop": float(sl),
                        "target": float(tp),
                    },
                )
            try:
                filled_qty = float(fill_qty or q_str)
            except (TypeError, ValueError):
                filled_qty = float(qty)
            current_amt = float(pos_map.get(symbol, 0.0) or 0.0)
            delta = filled_qty if sig == "BUY" else -filled_qty
            pos_map[symbol] = current_amt + delta
            alpha_msg = ""
            if alpha_prob is not None:
                alpha_msg = f" alpha={alpha_prob:.3f}/{(alpha_conf or 0.0):.2f}"
            live_entry = float(live_trade.get("entry", fill_price or px) or px)
            log.info(
                "ENTRY %s %s qty=%.6f px≈%.6f SL=%.6f TP=%.6f bucket=%s%s",
                symbol,
                sig,
                float(fill_qty or qty),
                live_entry,
                sl,
                tp,
                bucket,
                alpha_msg,
            )
            if ai_meta and ai_meta.get("explanation"):
                log.info("AI plan %s: %s", symbol, ai_meta.get("explanation"))
            activity_kind = "execution"
            activity_headline = f"Executed {symbol} {sig}"
            activity_body = f"qty={q_str} @≈{px:.6f} (SL {sl:.6f} · TP {tp:.6f})"
            activity_data = {
                "symbol": symbol,
                "side": sig,
                "qty": q_str,
                "entry": float(px),
                "sl": float(sl),
                "tp": float(tp),
                "bucket": bucket,
            }
            if plan and isinstance(plan, dict):
                req_id = plan.get("request_id")
                if isinstance(req_id, str):
                    req_id = req_id.strip()
                if req_id:
                    activity_data["request_id"] = req_id
                origin = plan.get("origin") or plan_origin
            else:
                origin = plan_origin
            if not origin:
                origin = ctx.get("ai_plan_origin")
            if isinstance(origin, str) and origin.strip():
                activity_data["origin"] = origin.strip()
            if alpha_prob is not None:
                try:
                    activity_data["alpha_prob"] = float(alpha_prob)
                except Exception:
                    pass
            if alpha_conf is not None:
                try:
                    activity_data["alpha_conf"] = float(alpha_conf)
                except Exception:
                    pass
            if ctx.get("expected_r") is not None:
                try:
                    activity_data["expected_r"] = float(ctx.get("expected_r"))
                except Exception:
                    pass
            indicator_keys = (
                "rsi",
                "bb_position",
                "bb_width",
                "supertrend",
                "supertrend_dir",
                "stoch_rsi_d",
                "stoch_rsi_k",
            )
            indicator_snapshot: Dict[str, float] = {}
            for key in indicator_keys:
                if key not in ctx:
                    continue
                try:
                    indicator_snapshot[key] = float(ctx[key])
                except Exception:
                    continue
            if indicator_snapshot:
                activity_data["indicators"] = indicator_snapshot
            feature_snapshot: Dict[str, float] = {}
            for key in POLICY_FEATURES:
                if key not in ctx:
                    continue
                try:
                    feature_snapshot[key] = float(ctx[key])
                except Exception:
                    continue
            if feature_snapshot:
                activity_data["bandit_features"] = feature_snapshot
            if manual_override:
                activity_kind = "manual"
                activity_headline = f"Manual {sig.lower()} executed for {symbol}"
                activity_body = (
                    f"qty={q_str} @≈{px:.6f} (SL {sl:.6f} · TP {tp:.6f}) — triggered from chat request."
                )
                activity_data["manual_request"] = True
                activity_data["request_id"] = manual_req.get("id")
            self._log_ai_activity(
                activity_kind,
                activity_headline,
                body=activity_body,
                data=activity_data,
                force=True,
            )
        except Exception as e:
            log.debug(f"entry fail {symbol}: {e}")
            if self.decision_tracker and not manual_override:
                self.decision_tracker.record_rejection("order_failed", force=True)
            if manual_override:
                self._complete_manual_request(manual_req, "failed", error=str(e))
            self.state.setdefault("fail_skip_until", {})[symbol] = time.time() + 60

    def run_once(self):
        self._manual_state_dirty = False
        try:
            cycle_index = int(self.state.get("cycle_index", 0) or 0)
        except Exception:
            cycle_index = 0
        cycle_index += 1
        self.state["cycle_index"] = cycle_index
        self._current_cycle = cycle_index
        cooldown_map = self.state.get("quote_volume_cooldown")
        if not isinstance(cooldown_map, dict):
            cooldown_map = {}
            self.state["quote_volume_cooldown"] = cooldown_map
            self._quote_volume_cooldown_dirty = True
        expired_symbols: List[str] = []
        for sym, resume in list(cooldown_map.items()):
            try:
                resume_cycle = int(resume)
            except (TypeError, ValueError):
                resume_cycle = 0
            if resume_cycle <= cycle_index:
                expired_symbols.append(sym)
        if expired_symbols:
            for sym in expired_symbols:
                if cooldown_map.pop(sym, None) is not None:
                    self._quote_volume_cooldown_dirty = True
        self._ai_wakeup_event.clear()
        self._refresh_manual_requests()
        self._drain_ai_ready_queue()
        syms = self.universe.refresh()
        ticker_map: Dict[str, Dict[str, Any]] = {}
        now = time.time()
        need_bulk_ticker = (
            self.sentinel is not None
            or (now - getattr(self.strategy, "_t24_ts", 0.0)) >= self.strategy._t24_ttl
        )
        if need_bulk_ticker and syms:
            try:
                payload = self.exchange.get_ticker_24hr()
            except Exception as exc:
                log.debug(f"bulk 24h ticker fetch failed: {exc}")
                payload = None
            if isinstance(payload, list):
                for item in payload:
                    if not isinstance(item, dict):
                        continue
                    sym = item.get("symbol")
                    if sym:
                        ticker_map[str(sym)] = dict(item)
            elif isinstance(payload, dict) and payload.get("symbol"):
                ticker_map[str(payload.get("symbol"))] = dict(payload)
            if ticker_map:
                self.strategy.prime_ticker_cache(ticker_map, timestamp=now)
        ranked_syms = self._rank_symbols(syms, ticker_map)
        priority_pairs = self._consume_ai_priority_symbols()
        if priority_pairs:
            ordered: List[str] = []
            seen: Set[str] = set()
            for sym, _ in priority_pairs:
                token = str(sym or "").upper()
                if not token or token in seen:
                    continue
                ordered.append(token)
                seen.add(token)
            for sym in ranked_syms:
                if sym not in seen:
                    ordered.append(sym)
                    seen.add(sym)
            syms = ordered
        else:
            syms = ranked_syms

        pending_manual: Set[str] = set()
        queue = self.state.get("manual_trade_requests")
        if isinstance(queue, list):
            pending_manual = {
                str(item.get("symbol") or "").upper().strip()
                for item in queue
                if isinstance(item, dict)
                and str(item.get("status") or "pending").lower() == "pending"
                and str(item.get("symbol") or "").strip()
            }
        if pending_manual:
            existing = set(syms)
            extra = [sym for sym in pending_manual if sym and sym not in existing]
            if extra:
                syms = syms + extra
        preview: List[str] = []
        for sym in syms[:12]:
            info = self._symbol_score_cache.get(sym, {})
            score = info.get("score")
            if isinstance(score, (int, float)) and score > 0:
                preview.append(f"{sym}({score:.2f})")
            else:
                preview.append(sym)
        suffix = ""
        if preview:
            suffix = f": {', '.join(preview)}"
            if len(syms) > 12:
                suffix += "..."
        log.info("Scanning %d symbols%s", len(syms), suffix)

        syms_queue: deque[str] = deque(syms)

        if self.sentinel:
            try:
                self.sentinel.refresh(syms, prefetched=ticker_map if ticker_map else None)
            except Exception as exc:
                log.debug(f"sentinel refresh failed: {exc}")

        if self.ai_advisor:
            try:
                snapshot = self.strategy._playbook_snapshot()
                self.ai_advisor.maybe_refresh_playbook(snapshot)
            except Exception as exc:
                log.debug(f"playbook refresh failed: {exc}")

        # geschlossene Trades aus State räumen + Policy belohnen
        postmortem_cb = None
        if self.ai_advisor:
            postmortem_cb = self.ai_advisor.generate_postmortem
        self.trade_mgr.remove_closed_trades(postmortem_cb=postmortem_cb)

        # einmalig Positionen holen (pos_map), für FastTP & Skip bei offenen Positionen
        try:
            pos = self.exchange.get_position_risk()
            pos_map = {p.get("symbol"): float(p.get("positionAmt", "0") or 0.0) for p in pos}
        except Exception:
            pos_map = {}

        book_ticker_map: Dict[str, Dict[str, Any]] = {}
        try:
            book_payload = self.exchange.get_book_ticker()
        except Exception as exc:
            log.debug(f"bulk bookTicker fetch failed: {exc}")
            book_payload = None
        if isinstance(book_payload, list):
            for entry in book_payload:
                if not isinstance(entry, dict):
                    continue
                sym = entry.get("symbol")
                if sym:
                    book_ticker_map[str(sym)] = dict(entry)
        elif isinstance(book_payload, dict) and book_payload.get("symbol"):
            book_ticker_map[str(book_payload.get("symbol"))] = dict(book_payload)
        bulk_book_available = bool(book_ticker_map)

        self.strategy.reset_orderbook_budget(ORDERBOOK_ON_DEMAND)

        priority_tokens = [
            str(sym or "").strip().upper()
            for sym, _ in priority_pairs
            if sym and str(sym).strip()
        ]
        manual_for_prefetch = sorted(pending_manual) if pending_manual else None
        orderbook_plan = self.strategy.plan_orderbook_prefetch(
            syms,
            book_ticker_map,
            manual_symbols=manual_for_prefetch,
            priority_symbols=priority_tokens,
        )
        prefetched_order_books = self.strategy.prefetch_order_books(orderbook_plan)
        plan_signature = tuple(orderbook_plan[:8])
        if plan_signature and plan_signature != self._orderbook_activity_signature:
            self._orderbook_activity_signature = plan_signature
            preview_plan = orderbook_plan[:6]
            body = f"Prefetching depth for {', '.join(preview_plan)}"
            if len(orderbook_plan) > len(preview_plan):
                body += " …"
            activity_payload = {
                "prefetch": preview_plan,
                "prefetch_count": len(orderbook_plan),
                "on_demand_budget": ORDERBOOK_ON_DEMAND,
                "depth_limit": self.strategy.orderbook_limit,
            }
            self._log_ai_activity(
                "info",
                "Order book scan updated",
                body=body,
                data=activity_payload,
            )
        elif not plan_signature:
            self._orderbook_activity_signature = tuple()

        last_ai_drain = time.time()
        ai_flush_interval = 2.5

        processed_symbols: Set[str] = set()

        while syms_queue:
            sym = syms_queue.popleft()
            processed_symbols.add(sym)
            if self.ai_advisor:
                priority_updated = False
                if self._ai_wakeup_event.is_set():
                    self._drain_ai_ready_queue(clear_event=True)
                    last_ai_drain = time.time()
                    priority_updated = True
                elif (time.time() - last_ai_drain) >= ai_flush_interval:
                    self._drain_ai_ready_queue()
                    last_ai_drain = time.time()
                    priority_updated = True
                if priority_updated:
                    new_priority = self._consume_ai_priority_symbols()
                    if new_priority:
                        for pri_sym, _ in reversed(new_priority):
                            if not pri_sym:
                                continue
                            token = pri_sym.strip().upper()
                            if not token:
                                continue
                            if token in syms_queue and token not in processed_symbols:
                                continue
                            syms_queue.appendleft(token)
            # Preis tracken für FastTP
            mid = 0.0
            bt = book_ticker_map.get(sym)
            if bt is None:
                try:
                    bt = self.exchange.get_book_ticker(sym)
                except Exception:
                    bt = None
                if isinstance(bt, dict) and bt.get("symbol"):
                    book_ticker_map[sym] = dict(bt)
            if isinstance(bt, dict):
                try:
                    ask = float(bt.get("askPrice", 0.0) or 0.0)
                    bid = float(bt.get("bidPrice", 0.0) or 0.0)
                    mid = (ask + bid) / 2.0 if ask > 0 and bid > 0 else 0.0
                    if mid > 0:
                        self.fasttp.track(sym, mid)
                except Exception:
                    mid = 0.0

            amt = pos_map.get(sym, 0.0)
            if abs(amt) > 1e-12:
                rec = self.state.get("live_trades", {}).get(sym)
                if rec and mid > 0:
                    atr_abs = float(rec.get("atr_abs", 0.0))
                    if atr_abs > 0.0:
                        self.fasttp.maybe_apply(sym, amt, float(rec.get("entry")), float(rec.get("sl")), mid, atr_abs)
                continue

            try:
                order_book_snapshot = (
                    prefetched_order_books.get(sym)
                    or prefetched_order_books.get(sym.upper())
                    or self.strategy.get_cached_order_book(sym)
                    or self.strategy.get_cached_order_book(sym.upper())
                )
                if not order_book_snapshot:
                    order_book_snapshot = self.strategy.ensure_order_book(sym)
                    if not order_book_snapshot and sym.upper() != sym:
                        order_book_snapshot = self.strategy.ensure_order_book(sym.upper())
                    if order_book_snapshot:
                        prefetched_order_books[sym.upper()] = order_book_snapshot
                self.handle_symbol(
                    sym,
                    pos_map,
                    book_ticker=book_ticker_map.get(sym),
                    order_book=order_book_snapshot,
                )
            except Exception as e:
                log.debug(f"signal handling fail {sym}: {e}")
            # dynamisches Throttling: nur bremsen, falls keine Bulk-Daten vorhanden waren
            if not bulk_book_available:
                time.sleep(0.02)

        if getattr(self.strategy, "tech_snapshot_dirty", False):
            try:
                self.trade_mgr.save()
            except Exception as exc:
                log.debug(f"technical snapshot persist failed: {exc}")
            try:
                self.strategy.clear_tech_snapshot_dirty()
            except Exception:
                self.strategy._tech_snapshot_dirty = False  # type: ignore[attr-defined]

        if (
            self._manual_state_dirty
            or self._quote_volume_cooldown_dirty
            or self._universe_state_dirty
        ):
            self.trade_mgr.save()
            self._manual_state_dirty = False
            self._quote_volume_cooldown_dirty = False
            self._universe_state_dirty = False

    def run(self, loop: bool = True):
        log.info("Starting bot (mode=%s, loop=%s)", "PAPER" if PAPER else "LIVE", loop)
        running = True
        def _stop(*_):
            nonlocal running
            running = False
            log.info("Shutdown signal received — finishing the current cycle.")
        signal.signal(signal.SIGINT, _stop)
        signal.signal(signal.SIGTERM, _stop)

        if not loop:
            self.run_once()
            log.info("Done (single run).")
            if self.user_stream:
                try:
                    self.user_stream.stop()
                except Exception as exc:
                    log.debug(f"user stream shutdown failed: {exc}")
            return

        while running:
            t0 = time.time()
            self.run_once()
            dt = time.time() - t0
            log.info("Cycle finished in %.2fs.", dt)
            if not running:
                break
            wait_time = max(1, LOOP_SLEEP)
            triggered = self._ai_wakeup_event.wait(timeout=wait_time)
            if triggered:
                continue
        if self.user_stream:
            try:
                self.user_stream.stop()
            except Exception as exc:
                log.debug(f"user stream shutdown failed: {exc}")
        log.info("Bot stopped. Safe to exit.")

# ========= main =========
if __name__ == "__main__":
    run_once = os.getenv("ASTER_RUN_ONCE", "").lower() in ("1", "true", "yes", "on")
    Bot().run(loop=not run_once)
