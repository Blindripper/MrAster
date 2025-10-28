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

import os
import time
import math
import json
import uuid
import hmac
import hashlib
import logging
import signal
import textwrap
import re
import copy
from datetime import datetime, timezone
from urllib.parse import urlencode
from typing import Dict, List, Tuple, Optional, Any, Callable, Sequence, Set

from collections import OrderedDict, deque
from concurrent.futures import Future, ThreadPoolExecutor

import requests

from requests.exceptions import RequestException

try:
    import numpy as np  # noqa: F401
except Exception:
    raise RuntimeError("Dieses Modul benötigt numpy. Bitte: pip install numpy")

from ml_policy import BanditPolicy, FEATURES as POLICY_FEATURES
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
AI_MODE_ENABLED = MODE == "ai" or os.getenv("ASTER_AI_MODE", "").lower() in ("1", "true", "yes", "on")
OPENAI_API_KEY = os.getenv("ASTER_OPENAI_API_KEY", "").strip()
AI_MODEL = os.getenv("ASTER_AI_MODEL", "gpt-4o").strip() or "gpt-4o"
AI_DAILY_BUDGET = float(os.getenv("ASTER_AI_DAILY_BUDGET_USD", "20") or 0)
AI_STRICT_BUDGET = os.getenv("ASTER_AI_STRICT_BUDGET", "true").lower() in ("1", "true", "yes", "on")
SENTINEL_ENABLED = os.getenv("ASTER_AI_SENTINEL_ENABLED", "true").lower() in ("1", "true", "yes", "on")
SENTINEL_DECAY_MINUTES = float(os.getenv("ASTER_AI_SENTINEL_DECAY_MINUTES", "90") or 90)
SENTINEL_NEWS_ENDPOINT = os.getenv("ASTER_AI_NEWS_ENDPOINT", "").strip()
SENTINEL_NEWS_TOKEN = os.getenv("ASTER_AI_NEWS_API_KEY", "").strip()
AI_MIN_INTERVAL_SECONDS = float(os.getenv("ASTER_AI_MIN_INTERVAL_SECONDS", "8") or 0.0)
AI_CONCURRENCY = max(1, int(os.getenv("ASTER_AI_CONCURRENCY", "3") or 1))
AI_GLOBAL_COOLDOWN = max(0.0, float(os.getenv("ASTER_AI_GLOBAL_COOLDOWN_SECONDS", "2.0") or 0.0))
AI_PLAN_TIMEOUT = max(10.0, float(os.getenv("ASTER_AI_PLAN_TIMEOUT_SECONDS", "45") or 0.0))
AI_PENDING_LIMIT = max(AI_CONCURRENCY, int(os.getenv("ASTER_AI_PENDING_LIMIT", str(AI_CONCURRENCY * 2)) or AI_CONCURRENCY))

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
UNIVERSE_MAX = int(os.getenv("ASTER_UNIVERSE_MAX", "120"))
UNIVERSE_ROTATE = os.getenv("ASTER_UNIVERSE_ROTATE", "true").lower() in ("1", "true", "yes", "on")

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
LEVERAGE = float(os.getenv("ASTER_LEVERAGE", "5"))
EQUITY_FRACTION = float(os.getenv("ASTER_EQUITY_FRACTION", "0.33"))
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

HTTP_RETRIES = max(0, int(os.getenv("ASTER_HTTP_RETRIES", "2")))
HTTP_BACKOFF = max(0.0, float(os.getenv("ASTER_HTTP_BACKOFF", "0.6")))
HTTP_TIMEOUT = max(5.0, float(os.getenv("ASTER_HTTP_TIMEOUT", "20")))
KLINE_CACHE_SEC = max(5.0, float(os.getenv("ASTER_KLINE_CACHE_SEC", "45")))

MAX_OPEN_GLOBAL = int(os.getenv("ASTER_MAX_OPEN_GLOBAL", "4"))
MAX_OPEN_PER_SYMBOL = int(os.getenv("ASTER_MAX_OPEN_PER_SYMBOL", "1"))

STATE_FILE = os.getenv("ASTER_STATE_FILE", "aster_state.json")
PAPER = os.getenv("ASTER_PAPER", "false").lower() in ("1", "true", "yes", "on")

LOOP_SLEEP = int(os.getenv("ASTER_LOOP_SLEEP", "30"))  # Sekunden
WORKING_TYPE = os.getenv("ASTER_WORKING_TYPE", "MARK_PRICE")  # an Guard weitergeben

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
    window: deque = deque()
    for val in rsi_vals:
        window.append(val)
        if len(window) > period and period > 0:
            window.popleft()
        if len(window) < period or period <= 0:
            stoch.append(50.0)
            continue
        low = min(window)
        high = max(window)
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
        bucket.setdefault("spent", 0.0)
        bucket.setdefault("history", [])
        bucket.setdefault("stats", {})
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
    ):
        self.exchange = exchange
        self.state = state
        self.enabled = bool(enabled)
        self._ticker_cache: Dict[str, Dict[str, Any]] = {}
        self._last_payload: Dict[str, Dict[str, Any]] = {}
        self._decay = max(60.0, float(decay_minutes or 0) * 60.0)

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
        if not self.enabled or not SENTINEL_NEWS_ENDPOINT:
            return []
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
            return []

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

        event_risk = clamp(volatility * 1.4 + trend_factor * 0.6, 0.0, 1.0)
        if price_change < -9.0:
            event_risk = max(event_risk, 0.75)
        hype_score = clamp((volume_factor * 0.6) + (trend_factor * 0.6) + (bias_factor * 0.3), 0.0, 1.0)

        label = "green"
        hard_block = False
        if event_risk >= 0.75:
            label = "red"
            hard_block = True
        elif event_risk >= 0.45:
            label = "yellow"
        elif hype_score >= 0.65 and price_change >= 4.0:
            label = "yellow"

        size_factor = 1.0
        if label == "yellow":
            size_factor = 0.5
        if label == "red":
            size_factor = 0.0
        if label == "green" and hype_score > 0.7 and price_change > 0:
            size_factor = clamp(1.0 + (hype_score - 0.6), 1.0, 1.45)

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
            payload = {
                "event_risk": float(payload.get("event_risk", 0.0) or 0.0),
                "hype_score": float(payload.get("hype_score", 0.0) or 0.0),
                "label": payload.get("label", "green"),
                "actions": payload.get("actions", {"size_factor": 1.0, "hard_block": False}),
                "events": payload.get("events", []),
                "meta": payload.get("meta", {}),
            }
            self._last_payload[symbol] = {"ts": now, "payload": payload}

        sentinel_state = self.state.setdefault("sentinel", {})
        sentinel_state[symbol] = {
            **payload,
            "updated": datetime.now(timezone.utc).isoformat(),
        }
        if ctx is not None:
            ctx["sentinel_event_risk"] = float(payload.get("event_risk", 0.0) or 0.0)
            ctx["sentinel_hype"] = float(payload.get("hype_score", 0.0) or 0.0)
            ctx["sentinel_label"] = payload.get("label", "green")
        if store_only:
            return payload
        return payload


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
    ) -> None:
        self.api_key = (api_key or "").strip()
        self.model = (model or "gpt-4o").strip()
        self.budget = budget
        self.state = state if isinstance(state, dict) else None
        self.enabled = bool(enabled and self.api_key)
        self._temperature_supported = True
        self._temperature_override = self._resolve_temperature()
        self._cache: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
        self._recent_plans: "OrderedDict[str, Tuple[float, Dict[str, Any]]]" = OrderedDict()
        self._pending_requests: Dict[str, Dict[str, Any]] = {}
        self._pending_order: deque[str] = deque()
        self._min_interval = max(0.0, AI_MIN_INTERVAL_SECONDS)
        self._last_global_request = 0.0
        self._plan_timeout = AI_PLAN_TIMEOUT
        self._pending_limit = AI_PENDING_LIMIT
        self._executor: Optional[ThreadPoolExecutor] = None
        if self.enabled and AI_CONCURRENCY > 0:
            self._executor = ThreadPoolExecutor(max_workers=AI_CONCURRENCY)
        self._load_persistent_state()

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
                self._recent_plans[key] = (ts_val, copy.deepcopy(plan))
        while len(self._recent_plans) > self.RECENT_PLAN_LIMIT:
            self._recent_plans.popitem(last=False)

    def _persist_state(self) -> None:
        if not self.state:
            return
        cache_dump: List[Dict[str, Any]] = []
        for key, value in list(self._cache.items())[-self.CACHE_LIMIT:]:
            cache_dump.append({"key": key, "plan": copy.deepcopy(value)})
        recent_dump: List[Dict[str, Any]] = []
        for key, (ts, plan) in list(self._recent_plans.items())[-self.RECENT_PLAN_LIMIT:]:
            recent_dump.append({"key": key, "ts": float(ts), "plan": copy.deepcopy(plan)})
        self.state["ai_plan_cache"] = cache_dump
        self.state["ai_recent_plans"] = recent_dump

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
        if key in self._pending_requests:
            return True
        if self._pending_limit <= 0:
            return True
        self._prune_pending_queue()
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
    ) -> Optional[Future]:
        if not self._executor:
            return None
        return self._executor.submit(
            self._chat,
            system_prompt,
            user_prompt,
            kind=kind,
            budget_estimate=budget_estimate,
        )

    def _process_pending_request(
        self,
        throttle_key: str,
        fallback: Dict[str, Any],
        now: float,
    ) -> Tuple[Optional[str], Optional[Any]]:
        info = self._pending_requests.get(throttle_key)
        if not info:
            return None, None
        kind = str(info.get("kind", "plan"))
        note = info.get("note") or "Waiting for AI plan response"
        future = info.get("future")
        if future is None:
            if not self.enabled or not self._executor:
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
            if ready_after <= now and self._executor:
                cooldown_ok = AI_GLOBAL_COOLDOWN <= 0 or (now - self._last_global_request) >= AI_GLOBAL_COOLDOWN
                concurrency_ok = self._active_pending() < AI_CONCURRENCY
                if cooldown_ok and concurrency_ok:
                    future = self._dispatch_request(
                        info.get("system_prompt", ""),
                        info.get("user_prompt", ""),
                        kind=kind,
                        budget_estimate=float(info.get("estimate", 0.0) or 0.0),
                    )
                    if future:
                        info["future"] = future
                        info["dispatched_at"] = now
                        self._last_global_request = now
                        note = "Waiting for AI plan response"
                    else:
                        self._remove_pending_entry(throttle_key)
                        self._recent_plan_store(throttle_key, fallback, now)
                        return "fallback", fallback
                else:
                    info["ready_after"] = now + max(0.5, AI_GLOBAL_COOLDOWN or 0.5)
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
            self._recent_plan_store(throttle_key, fallback, now)
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
        if not response_text:
            self._recent_plan_store(throttle_key, fallback, now)
            return fallback
        parsed = self._parse_structured(response_text)
        if not isinstance(parsed, dict):
            self._recent_plan_store(throttle_key, fallback, now)
            return fallback
        kind = str(meta.get("kind", "plan")) if isinstance(meta, dict) else "plan"
        if kind == "trend":
            plan_ready = self._apply_trend_plan_overrides(fallback, parsed)
        else:
            plan_ready = self._apply_plan_overrides(fallback, parsed)
        if cache_key_ready:
            self._cache_store(str(cache_key_ready), plan_ready)
        self._recent_plan_store(throttle_key, plan_ready, now)
        return plan_ready

    def flush_pending(self) -> None:
        if not self._pending_requests:
            return
        now = time.time()
        keys = list(self._pending_order) if self._pending_order else list(self._pending_requests.keys())
        for throttle_key in keys:
            info = self._pending_requests.get(throttle_key)
            if not info:
                continue
            fallback = info.get("fallback")
            if not isinstance(fallback, dict):
                continue
            status, payload = self._process_pending_request(throttle_key, fallback, now)
            if status != "response":
                continue
            bundle = payload or {}
            response_text = bundle.get("response") if isinstance(bundle, dict) else None
            meta = bundle.get("info") if isinstance(bundle, dict) else info
            self._finalize_response(throttle_key, fallback, meta, response_text, now)

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
        self._cache[key] = copy.deepcopy(value)
        self._cache.move_to_end(key)
        while len(self._cache) > self.CACHE_LIMIT:
            self._cache.popitem(last=False)
        self._persist_state()

    def _recent_plan_lookup(self, key: str, now: Optional[float] = None) -> Optional[Dict[str, Any]]:
        if self._min_interval <= 0:
            return None
        if key not in self._recent_plans:
            return None
        if now is None:
            now = time.time()
        ts, plan = self._recent_plans[key]
        if now - ts > self._min_interval:
            return None
        self._recent_plans.move_to_end(key)
        return copy.deepcopy(plan)

    def _recent_plan_store(self, key: str, plan: Dict[str, Any], now: Optional[float] = None) -> None:
        if self._min_interval <= 0:
            return
        if now is None:
            now = time.time()
        self._recent_plans[key] = (now, copy.deepcopy(plan))
        self._recent_plans.move_to_end(key)
        while len(self._recent_plans) > self.RECENT_PLAN_LIMIT:
            self._recent_plans.popitem(last=False)
        self._persist_state()

    def consume_recent_plan(self, key: str) -> Optional[Dict[str, Any]]:
        if self._min_interval <= 0 or not key:
            return None
        bundle = self._recent_plans.pop(key, None)
        if not bundle:
            return None
        try:
            self._persist_state()
        except Exception:
            # Persistence issues should not block delivering the plan.
            pass
        _, plan = bundle
        return copy.deepcopy(plan)

    def consume_signal_plan(self, symbol: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        if self._min_interval <= 0:
            return None
        if not symbol:
            return None
        prefix = f"plan::{symbol.upper()}::"
        now = time.time()
        selected_key: Optional[str] = None
        selected_side: Optional[str] = None
        selected_plan: Optional[Dict[str, Any]] = None
        for key, (ts, plan) in list(self._recent_plans.items()):
            if not key.startswith(prefix):
                continue
            if now - ts > self._min_interval:
                self._recent_plans.pop(key, None)
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

    def _chat(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        kind: str,
        budget_estimate: float = 0.0,
    ) -> Optional[str]:
        if not self.enabled:
            return None
        estimate = max(0.0, float(budget_estimate or 0.0))
        if estimate <= 0:
            estimate = self._estimate_prospective_cost(system_prompt, user_prompt)
        if not self.budget.can_spend(estimate, kind=kind, model=self.model):
            log.info("AI daily budget exhausted — skipping %s request.", kind)
            return None
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "response_format": {"type": "text"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        def _send_chat(p: Dict[str, Any]) -> requests.Response:
            return requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=p,
                timeout=30,
            )

        if self._temperature_supported and self._temperature_override is not None:
            payload["temperature"] = self._temperature_override

        try:
            attempt = 0
            while True:
                resp = _send_chat(payload)
                if resp.status_code < 400:
                    data = resp.json()
                    break
                text_preview = (resp.text or "")[:160]
                lower_preview = text_preview.lower()
                if (
                    self._temperature_supported
                    and "temperature" in payload
                    and "temperature" in lower_preview
                    and "default" in lower_preview
                    and attempt == 0
                ):
                    # Retry without temperature for models that only allow the default value.
                    payload.pop("temperature", None)
                    attempt += 1
                    self._temperature_supported = False
                    log.debug("AI model rejected temperature override; retrying without it.")
                    continue
                raise RuntimeError(f"HTTP {resp.status_code}: {text_preview}")
        except Exception as exc:
            log.debug(f"AI request failed ({kind}): {exc}")
            return None

        usage = data.get("usage")
        cost = self._estimate_cost(usage)
        if cost is None:
            cost = 0.0025
        self.budget.record(cost, {"kind": kind, "model": self.model, "usage": usage})

        try:
            choices = data.get("choices") or []
            content = choices[0]["message"]["content"] if choices else ""
            return str(content or "").strip()
        except Exception:
            return None

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
        size_multiplier = clamp(size_factor * risk_bias, 0.0, 1.8)

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

        leverage = clamp(LEVERAGE * (0.5 if event_risk > 0.6 else (1.0 + hype_score * 0.25)), 1.0, max(LEVERAGE * 1.2, 1.0))

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
            "size_multiplier": size_multiplier,
            "sl_multiplier": sl_mult,
            "tp_multiplier": tp_mult,
            "leverage": leverage,
            "fasttp_overrides": fasttp_overrides,
            "risk_note": label,
            "explanation": explanation,
            "event_risk": event_risk,
            "hype_score": hype_score,
            "take": True,
            "decision": "take",
            "decision_reason": "fallback_rules",
            "decision_note": "Signal cleared heuristics. Proceeding with adjusted sizing and risk bounds.",
            "entry_price": float(price),
            "stop_loss": float(price - base_sl if side == "BUY" else price + base_sl),
            "take_profit": float(price + base_tp if side == "BUY" else price - base_tp),
        }

    def _apply_plan_overrides(
        self, fallback: Dict[str, Any], parsed: Dict[str, Any]
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
            plan["size_multiplier"] = clamp(float(size_multiplier), 0.0, 2.0)
        if isinstance(sl_multiplier, (int, float)):
            plan["sl_multiplier"] = clamp(float(sl_multiplier), 0.5, 2.5)
        if isinstance(tp_multiplier, (int, float)):
            plan["tp_multiplier"] = clamp(float(tp_multiplier), 0.5, 3.0)
        if isinstance(leverage, (int, float)):
            plan["leverage"] = clamp(float(leverage), 1.0, max(LEVERAGE * 2.0, 1.0))
        if isinstance(fasttp_overrides, dict):
            overrides = {
                "enabled": bool(fasttp_overrides.get("enabled", True)),
                "min_r": float(
                    fasttp_overrides.get(
                        "min_r", fallback.get("fasttp_overrides", {}).get("min_r", FASTTP_MIN_R)
                    )
                ),
                "ret1": float(fasttp_overrides.get("ret1", FAST_TP_RET1)),
                "ret3": float(fasttp_overrides.get("ret3", FAST_TP_RET3)),
                "snap_atr": float(fasttp_overrides.get("snap_atr", FASTTP_SNAP_ATR)),
            }
            plan["fasttp_overrides"] = overrides
        if isinstance(risk_note, str) and risk_note.strip():
            plan["risk_note"] = risk_note.strip()
        if isinstance(explanation, str) and explanation.strip():
            plan["explanation"] = self._ensure_bounds(explanation, fallback.get("explanation", ""))
        else:
            plan["explanation"] = fallback.get("explanation")

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
        self, fallback: Dict[str, Any], parsed: Dict[str, Any]
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
        if isinstance(side_raw, str):
            side_norm = side_raw.strip().upper()
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

        if isinstance(size_multiplier, (int, float)):
            plan["size_multiplier"] = clamp(float(size_multiplier), 0.0, 2.0)
        if isinstance(sl_multiplier, (int, float)):
            plan["sl_multiplier"] = clamp(float(sl_multiplier), 0.5, 2.5)
        if isinstance(tp_multiplier, (int, float)):
            plan["tp_multiplier"] = clamp(float(tp_multiplier), 0.5, 3.0)
        if isinstance(leverage, (int, float)):
            plan["leverage"] = clamp(float(leverage), 1.0, max(LEVERAGE * 2.0, 1.0))
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
        if not self.enabled:
            self._recent_plan_store(f"plan::{symbol.upper()}::{side.upper()}", fallback)
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
            self._recent_plan_store(f"plan::{symbol.upper()}::{side.upper()}", fallback)
            return fallback

        throttle_key = f"plan::{symbol.upper()}::{side.upper()}"
        now = time.time()
        status, payload = self._process_pending_request(throttle_key, fallback, now)
        if status in {"pending", "timeout"}:
            return payload  # type: ignore[return-value]
        if status == "fallback":
            return payload  # type: ignore[return-value]
        if status == "response":
            bundle = payload or {}
            response_text = bundle.get("response") if isinstance(bundle, dict) else None
            meta = bundle.get("info") if isinstance(bundle, dict) else {}
            return self._finalize_response(throttle_key, fallback, meta, response_text, now)

        recent_plan = self._recent_plan_lookup(throttle_key, now)
        if recent_plan is not None:
            return recent_plan

        if not self._has_pending_capacity(throttle_key):
            self._recent_plan_store(throttle_key, fallback, now)
            return self._pending_stub(
                fallback,
                "plan_queue_full",
                "AI queue saturated; using fallback heuristics.",
                throttle_key=throttle_key,
                pending=False,
            )

        system_prompt = (
            "You advise a futures bot. Use the indicator stats and sentinel hints to decide if the trade should run. "
            "Return compact JSON with: take (bool), decision, decision_reason, decision_note, size_multiplier, sl_multiplier, "
            "tp_multiplier, leverage, risk_note, explanation, fasttp_overrides (enabled,min_r,ret1,ret3,snap_atr) and optional "
            "levels entry_price, stop_loss, take_profit. If you reject set take=false and leave explanation empty."
        )
        stats_block = self._extract_stat_block(ctx)
        sentinel_payload = self._summarize_sentinel(sentinel)
        constraints: Dict[str, Any] = {}
        if MAX_NOTIONAL_USDT > 0:
            constraints["max_notional"] = MAX_NOTIONAL_USDT
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
        user_prompt = json.dumps(user_payload, sort_keys=True, separators=(",", ":"))
        cache_key = self._cache_key("plan", system_prompt, user_payload)
        cached_plan = self._cache_lookup(cache_key)
        if cached_plan is not None:
            self._recent_plan_store(throttle_key, cached_plan, now)
            return cached_plan
        estimate = self._estimate_prospective_cost(system_prompt, user_prompt)
        if not async_mode or not self._executor:
            response = self._chat(system_prompt, user_prompt, kind="plan", budget_estimate=estimate)
            if not response:
                self._recent_plan_store(throttle_key, fallback, now)
                return fallback
            parsed = self._parse_structured(response)
            if not isinstance(parsed, dict):
                self._recent_plan_store(throttle_key, fallback, now)
                return fallback
            plan = self._apply_plan_overrides(fallback, parsed)
            self._cache_store(cache_key, plan)
            self._recent_plan_store(throttle_key, plan, now)
            return plan

        if not self.budget.can_spend(estimate, kind="plan", model=self.model):
            self._recent_plan_store(throttle_key, fallback, now)
            return fallback

        cooldown_blocked = AI_GLOBAL_COOLDOWN > 0 and (now - self._last_global_request) < AI_GLOBAL_COOLDOWN
        if cooldown_blocked or self._active_pending() >= AI_CONCURRENCY:
            if not self._has_pending_capacity(throttle_key):
                self._recent_plan_store(throttle_key, fallback, now)
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
                "cache_key": cache_key,
                "kind": "plan",
                "estimate": estimate,
                "queued_at": now,
                "ready_after": now + max(0.5, AI_GLOBAL_COOLDOWN or 0.5),
                "note": "Queued for AI planning",
                "notified": False,
            }
            stub = self._pending_stub(
                fallback,
                "plan_pending",
                "Queued for AI planning",
                throttle_key=throttle_key,
            )
            pending_info["request_id"] = stub.get("request_id")
            self._pending_requests[throttle_key] = pending_info
            self._register_pending_key(throttle_key)
            return stub

        if not self._has_pending_capacity(throttle_key):
            self._recent_plan_store(throttle_key, fallback, now)
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
        )
        if not future:
            self._recent_plan_store(throttle_key, fallback, now)
            return fallback
        self._pending_requests[throttle_key] = {
            "future": future,
            "fallback": fallback,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "cache_key": cache_key,
            "kind": "plan",
            "estimate": estimate,
            "queued_at": now,
            "dispatched_at": now,
            "notified": False,
        }
        self._register_pending_key(throttle_key)
        self._last_global_request = now
        stub = self._pending_stub(
            fallback,
            "plan_pending",
            "Waiting for AI plan response",
            throttle_key=throttle_key,
        )
        self._pending_requests[throttle_key]["request_id"] = stub.get("request_id")
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
        fallback = {
            "take": False,
            "decision": "skip",
            "decision_reason": "no_signal",
            "decision_note": "Autonomous scan did not detect a safe opportunity.",
            "size_multiplier": 1.0,
            "sl_multiplier": 1.0,
            "tp_multiplier": 1.0,
            "leverage": LEVERAGE,
            "risk_note": sentinel.get("label", "green") if sentinel else "green",
            "explanation": "",
            "fasttp_overrides": None,
            "event_risk": float(sentinel.get("event_risk", 0.0) if sentinel else 0.0),
            "hype_score": float(sentinel.get("hype_score", 0.0) if sentinel else 0.0),
            "side": None,
            "confidence": 0.0,
            "entry_price": float(price),
        }
        if not self.enabled:
            self._recent_plan_store(f"trend::{symbol.upper()}", fallback)
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
            self._recent_plan_store(f"trend::{symbol.upper()}", fallback)
            return fallback

        throttle_key = f"trend::{symbol.upper()}"
        now = time.time()
        status, payload = self._process_pending_request(throttle_key, fallback, now)
        if status in {"pending", "timeout"}:
            return payload  # type: ignore[return-value]
        if status == "fallback":
            return payload  # type: ignore[return-value]
        if status == "response":
            bundle = payload or {}
            response_text = bundle.get("response") if isinstance(bundle, dict) else None
            meta = bundle.get("info") if isinstance(bundle, dict) else {}
            return self._finalize_response(throttle_key, fallback, meta, response_text, now)

        recent_plan = self._recent_plan_lookup(throttle_key, now)
        if recent_plan is not None:
            return recent_plan

        if not self._has_pending_capacity(throttle_key):
            self._recent_plan_store(throttle_key, fallback, now)
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
        user_prompt = json.dumps(user_payload, sort_keys=True, separators=(",", ":"))
        cache_key = self._cache_key("trend", system_prompt, user_payload)
        cached_plan = self._cache_lookup(cache_key)
        if cached_plan is not None:
            self._recent_plan_store(throttle_key, cached_plan, now)
            return cached_plan
        estimate = self._estimate_prospective_cost(system_prompt, user_prompt)
        if not async_mode or not self._executor:
            response = self._chat(system_prompt, user_prompt, kind="trend", budget_estimate=estimate)
            if not response:
                self._recent_plan_store(throttle_key, fallback, now)
                return fallback
            parsed = self._parse_structured(response)
            if not isinstance(parsed, dict):
                self._recent_plan_store(throttle_key, fallback, now)
                return fallback
            plan = self._apply_trend_plan_overrides(fallback, parsed)
            self._cache_store(cache_key, plan)
            self._recent_plan_store(throttle_key, plan, now)
            return plan

        if not self.budget.can_spend(estimate, kind="trend", model=self.model):
            self._recent_plan_store(throttle_key, fallback, now)
            return fallback

        cooldown_blocked = AI_GLOBAL_COOLDOWN > 0 and (now - self._last_global_request) < AI_GLOBAL_COOLDOWN
        if cooldown_blocked or self._active_pending() >= AI_CONCURRENCY:
            if not self._has_pending_capacity(throttle_key):
                self._recent_plan_store(throttle_key, fallback, now)
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
                "cache_key": cache_key,
                "kind": "trend",
                "estimate": estimate,
                "queued_at": now,
                "ready_after": now + max(0.5, AI_GLOBAL_COOLDOWN or 0.5),
                "note": "Queued for AI planning",
                "notified": False,
            }
            stub = self._pending_stub(
                fallback,
                "trend_pending",
                "Queued for AI planning",
                throttle_key=throttle_key,
            )
            pending_info["request_id"] = stub.get("request_id")
            self._pending_requests[throttle_key] = pending_info
            self._register_pending_key(throttle_key)
            return stub

        if not self._has_pending_capacity(throttle_key):
            self._recent_plan_store(throttle_key, fallback, now)
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
        )
        if not future:
            self._recent_plan_store(throttle_key, fallback, now)
            return fallback
        self._pending_requests[throttle_key] = {
            "future": future,
            "fallback": fallback,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "cache_key": cache_key,
            "kind": "trend",
            "estimate": estimate,
            "queued_at": now,
            "dispatched_at": now,
            "notified": False,
        }
        self._register_pending_key(throttle_key)
        self._last_global_request = now
        stub = self._pending_stub(
            fallback,
            "trend_pending",
            "Waiting for AI plan response",
            throttle_key=throttle_key,
        )
        self._pending_requests[throttle_key]["request_id"] = stub.get("request_id")
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
            "You are a trading coach. Analyse the trade JSON and respond with a 40-70 word paragraph summarising what went right, "
            "what could improve, and one actionable tweak."
        )
        user_prompt = json.dumps(trade, sort_keys=True, separators=(",", ":"))
        response = self._chat(system_prompt, user_prompt, kind="postmortem")
        if not response:
            return fallback
        summary = self._ensure_bounds(response, fallback_text)
        fallback["analysis"] = summary
        return fallback

    def budget_snapshot(self) -> Dict[str, Any]:
        return self.budget.snapshot()

# ========= Exchange =========
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

    def get_book_ticker(self, symbol: Optional[str] = None) -> Any:
        params = {"symbol": symbol} if symbol else None
        if params:
            return self.get("/fapi/v1/ticker/bookTicker", params)
        return self.get("/fapi/v1/ticker/bookTicker")

    def get_position_risk(self) -> Any:
        return self.signed("get", "/fapi/v2/positionRisk", {})

    def get_open_orders(self, symbol: str) -> Any:
        if PAPER:
            return []
        return self.signed("get", "/fapi/v1/openOrders", {"symbol": symbol})

    def cancel_order(self, symbol: str, order_id: int) -> Any:
        if PAPER:
            return {"paper": True, "symbol": symbol, "orderId": int(order_id)}
        payload = {"symbol": symbol, "orderId": str(int(order_id))}
        return self.signed("delete", "/fapi/v1/order", payload)

    def post_order(self, params: Dict[str, Any]) -> Any:
        if PAPER:
            return {"paper": True, "params": params}
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
        if PAPER:
            return {"paper": True, "cancel": symbol}
        return self.signed("delete", "/fapi/v1/allOpenOrders", {"symbol": symbol})

    def set_leverage(self, symbol: str, leverage: float) -> Any:
        if leverage <= 0:
            raise ValueError("leverage must be positive")
        if PAPER:
            return {"paper": True, "symbol": symbol, "leverage": leverage}
        payload = {"symbol": symbol, "leverage": int(max(1, round(leverage)))}
        return self.signed("post", "/fapi/v1/leverage", payload)

# ========= Universe =========
class SymbolUniverse:
    def __init__(self, exchange: Exchange, quote: str, max_n: int, exclude: set, rotate: bool, include: Optional[List[str]] = None):
        self.exchange = exchange
        self.quote = quote
        self.max_n = max_n
        self.exclude = exclude
        self.rotate = rotate
        self.include = include or []

    def refresh(self) -> List[str]:
        try:
            info = self.exchange.get_exchange_info()
            syms = [s["symbol"] for s in info.get("symbols", []) if s.get("quoteAsset") == self.quote]
        except Exception:
            syms = []
        if self.include:
            syms = [s for s in syms if s in self.include]
        if self.exclude:
            syms = [s for s in syms if s not in self.exclude]
        return sorted(syms)[: self.max_n]

# ========= Risk =========
class RiskManager:
    def __init__(self, exchange: Exchange, default_notional: float = DEFAULT_NOTIONAL):
        self.exchange = exchange
        self.default_notional = default_notional
        self.symbol_filters: Dict[str, Dict[str, Any]] = {}
        # /balance Cache
        self._equity: Optional[float] = None
        self._equity_ts: float = 0.0
        self._equity_ttl = 10  # s

    def load_filters(self) -> None:
        try:
            info = self.exchange.get_exchange_info()
            filt: Dict[str, Dict[str, Any]] = {}
            for s in info.get("symbols", []):
                sym = s.get("symbol", "")
                fdict = {f.get("filterType"): f for f in s.get("filters", [])}
                lot = fdict.get("LOT_SIZE", {})
                price = fdict.get("PRICE_FILTER", {})
                filt[sym] = {
                    "minQty": float(lot.get("minQty", "0") or 0),
                    "maxQty": float(lot.get("maxQty", "0") or 0),
                    "stepSize": float(lot.get("stepSize", "0.0001") or 0.0001),
                    "tickSize": float(price.get("tickSize", "0.0001") or 0.0001),
                }
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

    def compute_qty(self, symbol: str, entry: float, sl: float, size_mult: float) -> float:
        step = float(self.symbol_filters.get(symbol, {}).get("stepSize", 0.0001) or 0.0001)
        # a) Basiskapital
        notional_base = DEFAULT_NOTIONAL * max(0.0, size_mult)
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
        notional = max(MIN_NOTIONAL_ENV, notional_base, risk_notional)
        # c) Cap via Leverage & Equity-Fraction
        equity = self._equity_cached()
        dyn_cap = equity * LEVERAGE * EQUITY_FRACTION if equity > 0 else float("inf")
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
        self._kl_cache: Dict[Tuple[str, str, int], Tuple[float, Tuple[Tuple[float, ...], ...]]] = {}
        self._kl_cache_ttl = KLINE_CACHE_SEC
        self._kl_cache_hits = 0
        self._kl_cache_miss = 0

    @property
    def tech_snapshot_dirty(self) -> bool:
        return bool(self._tech_snapshot_dirty)

    def clear_tech_snapshot_dirty(self) -> None:
        self._tech_snapshot_dirty = False

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

    def _get_qv_score(self, symbol: str) -> Tuple[float, Optional[Dict[str, Any]], float]:
        rec = self._ticker_24(symbol)
        try:
            qvol = float(rec.get("quoteVolume", 0.0) or 0.0) if rec else 0.0
        except Exception:
            qvol = 0.0
        score = min(2.5, qvol / max(self.min_quote_vol, 1e-9)) if qvol > 0 else 0.0
        return score, rec, float(qvol)

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
                payload = json.loads(json.dumps(ctx, default=lambda o: float(o)))
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
        self, symbol: str, book_ticker: Optional[Dict[str, Any]] = None
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
        try:
            with open(STATE_FILE, "w") as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            log.warning(f"state save failed: {e}")

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
            "sl": float(sl),
            "tp": float(tp),
            "side": side,
            "qty": float(qty),
            "ctx": dict(ctx),
            "bucket": bucket,
            "atr_abs": float(atr_abs),
            "opened_at": time.time(),
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

    def remove_closed_trades(
        self,
        postmortem_cb: Optional[Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]] = None,
    ):
        live = self.state.get("live_trades", {})
        if not live:
            return
        try:
            pos = self.exchange.get_position_risk()
            pos_map = {p.get("symbol"): float(p.get("positionAmt", "0") or 0.0) for p in pos}
        except Exception as e:
            log.debug(f"positionRisk fail: {e}")
            pos_map = {}

        to_del: List[str] = []
        history_added = False
        for sym, rec in live.items():
            amt = pos_map.get(sym, 0.0)
            if abs(amt) > 1e-12:
                continue  # noch offen

            self._cancel_stale_exit_orders(sym)
            entry = float(rec.get("entry")); sl = float(rec.get("sl"))
            side = rec.get("side"); qty = float(rec.get("qty"))
            # Exit-Preis näherungsweise aus Mid
            try:
                bt = self.exchange.get_book_ticker(sym)
                ask = float(bt.get("askPrice", 0.0) or 0.0); bid = float(bt.get("bidPrice", 0.0) or 0.0)
                exit_px = (ask + bid) / 2.0 if ask > 0 and bid > 0 else entry
            except Exception:
                exit_px = entry
            prof = (exit_px - entry) * qty if side == "BUY" else (entry - exit_px) * qty
            risk = max(1e-9, abs(entry - sl) * qty)
            r_mult = float(prof / risk)
            if self.policy and BANDIT_ENABLED:
                try:
                    self.policy.note_exit(symbol, pnl_r=r_mult, ctx=rec.get("ctx"), size_bucket=rec.get("bucket"))
                except Exception as e:
                    log.debug(f"policy note_exit fail: {e}")
            hist = self.state.setdefault("trade_history", [])
            closed_at = time.time()
            opened_at = float(rec.get("opened_at", closed_at) or closed_at)
            record = {
                "symbol": sym,
                "side": side,
                "qty": float(qty),
                "entry": float(entry),
                "exit": float(exit_px),
                "pnl": float(prof),
                "pnl_r": float(r_mult),
                "opened_at": float(opened_at),
                "closed_at": float(closed_at),
                "bucket": rec.get("bucket"),
                "context": rec.get("ctx", {}),
            }
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
        if to_del or history_added:
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
            _bg_replace_tp(
                self.guard,
                symbol,
                qty_abs,
                new_exit,
                side=("BUY" if pos_amt > 0 else "SELL")
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
        self.state.setdefault("manual_trade_requests", [])
        self.state.setdefault("manual_trade_history", [])
        self._ensure_banned_state()
        self._last_ai_activity_persist = 0.0
        self._manual_state_dirty = False
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
        sentinel_active = SENTINEL_ENABLED or AI_MODE_ENABLED
        self.sentinel = NewsTrendSentinel(self.exchange, self.state, enabled=sentinel_active)
        self.ai_advisor: Optional[AITradeAdvisor] = None
        if AI_MODE_ENABLED:
            self.ai_advisor = AITradeAdvisor(
                OPENAI_API_KEY,
                AI_MODEL,
                self.budget_tracker,
                self.state,
                enabled=AI_MODE_ENABLED,
            )

    @property
    def strategy(self) -> Strategy:
        return self._strategy

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
            return item
        return None

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
        entry: Dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "kind": str(kind or "info"),
            "headline": str(headline or ""),
        }
        if body:
            entry["body"] = str(body)
        if data:
            try:
                entry["data"] = json.loads(json.dumps(data, default=lambda o: str(o)))
            except Exception:
                entry["data"] = data
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
        self, symbol: str, pos_map: Dict[str, float], book_ticker: Optional[Dict[str, Any]] = None
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

        # bereits offene Position?
        amt = float(pos_map.get(symbol, 0.0) or 0.0)
        if abs(amt) > 1e-12:
            pending_queue = self.state.get("manual_trade_requests")
            if isinstance(pending_queue, list):
                for item in pending_queue:
                    if not isinstance(item, dict):
                        continue
                    if str(item.get("symbol") or "").upper() != symbol.upper():
                        continue
                    if str(item.get("status") or "pending").lower() != "pending":
                        continue
                    self._complete_manual_request(item, "failed", error="Position already open")
            return

        sig, atr_abs, ctx, price = self.strategy.compute_signal(symbol, book_ticker=book_ticker)
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
        size_mult = policy_size_mult * sentinel_factor
        ctx["sentinel_factor"] = sentinel_factor
        ctx["sentinel_event_risk"] = float(sentinel_info.get("event_risk", 0.0) or 0.0)
        ctx["sentinel_hype"] = float(sentinel_info.get("hype_score", 0.0) or 0.0)
        ctx["sentinel_label"] = sentinel_info.get("label", "green")

        if actions.get("hard_block") and not manual_override:
            veto_target = sig if sig != "NONE" else base_signal if base_signal != "NONE" else "opportunity"
            log.info(
                "Sentinel veto %s due to %s risk (event=%.2f, hype=%.2f)",
                symbol,
                sentinel_info.get("label", "red"),
                float(sentinel_info.get("event_risk", 0.0) or 0.0),
                float(sentinel_info.get("hype_score", 0.0) or 0.0),
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
                    "event_risk": float(sentinel_info.get("event_risk", 0.0) or 0.0),
                    "hype_score": float(sentinel_info.get("hype_score", 0.0) or 0.0),
                    "ai_request": False,
                },
                force=True,
            )
            if self.decision_tracker:
                self.decision_tracker.record_rejection("sentinel_veto")
            return

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

        atr_hint = float(ctx.get("atr_abs") or 0.0)
        if atr_abs <= 0 and atr_hint > 0:
            atr_abs = atr_hint
        if atr_abs <= 0:
            if manual_override:
                self._complete_manual_request(manual_req, "failed", error="ATR unavailable")
            return

        sl_dist = max(1e-9, SL_ATR_MULT * atr_abs)
        tp_dist = max(1e-9, TP_ATR_MULT * atr_abs)

        ai_meta: Optional[Dict[str, Any]] = None
        plan: Optional[Dict[str, Any]] = None
        plan_origin: Optional[str] = None
        plan_entry: Optional[float] = None
        plan_stop: Optional[float] = None
        plan_take: Optional[float] = None

        remaining_budget = self.budget_tracker.remaining()
        if remaining_budget is not None:
            ctx["budget_remaining"] = float(remaining_budget)
        ctx["budget_spent"] = float(self.budget_tracker.spent())
        open_positions_ctx = {k: float(v) for k, v in pos_map.items() if abs(float(v or 0.0)) > 1e-12}
        if open_positions_ctx:
            ctx["open_positions"] = open_positions_ctx
            ctx["active_positions"] = len(open_positions_ctx)
        else:
            ctx.pop("open_positions", None)
            ctx.pop("active_positions", None)

        if self.ai_advisor and not manual_override:
            skip_reason = str(ctx.get("skip_reason") or "").strip().lower()
            if skip_reason in {"no_cross"} and sig == "NONE" and not recovered_plan:
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
            sl_dist *= plan_sl_mult
            tp_dist *= plan_tp_mult
            leverage = plan.get("leverage")
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

        size_mult = clamp(size_mult, 0.0, 5.0)
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
                self.exchange.post_order(order_params)
            except requests.HTTPError as exc:
                status = getattr(exc.response, "status_code", None)
                if status == 400:
                    detail = ""
                    if exc.response is not None:
                        try:
                            payload = exc.response.json()
                            detail = json.dumps(payload)[:160]
                        except ValueError:
                            detail = (exc.response.text or "")[:160]
                    self._ban_symbol(symbol, "order_bad_request", details=detail or None)
                raise
            # Brackets – versuche neue Signatur (qty+entry), fallback auf alte
            try:
                ok = self.guard.ensure_after_entry(symbol, sig, float(q_str), px, sl, tp)
            except TypeError:
                ok = self.guard.ensure_after_entry(symbol, sig, sl, tp)
            if not ok:
                log.warning(f"Bracket orders for {symbol} could not be fully created.")
            if self.decision_tracker and not manual_override:
                self.decision_tracker.record_acceptance(bucket, persist=False)
            self.trade_mgr.note_entry(symbol, px, sl, tp, sig, float(q_str), ctx, bucket, atr_abs, meta=ai_meta)
            if manual_override:
                self._complete_manual_request(
                    manual_req,
                    "filled",
                    result={
                        "quantity": float(q_str),
                        "entry": float(px),
                        "stop": float(sl),
                        "target": float(tp),
                    },
                )
            alpha_msg = ""
            if alpha_prob is not None:
                alpha_msg = f" alpha={alpha_prob:.3f}/{(alpha_conf or 0.0):.2f}"
            log.info(
                "ENTRY %s %s qty=%s px≈%.6f SL=%.6f TP=%.6f bucket=%s%s",
                symbol,
                sig,
                q_str,
                px,
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
        self._refresh_manual_requests()
        if self.ai_advisor:
            try:
                self.ai_advisor.flush_pending()
            except Exception as exc:
                log.debug(f"pending flush failed: {exc}")
            try:
                self._resume_ai_pending_manual_requests()
            except Exception as exc:
                log.debug(f"manual resume failed: {exc}")
        syms = self.universe.refresh()

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

        log.info(
            "Scanning %d symbols%s",
            len(syms),
            f": {', '.join(syms[:12])}{'...' if len(syms)>12 else ''}",
        )

        ticker_map: Dict[str, Dict[str, Any]] = {}
        now = time.time()
        need_bulk_ticker = self.sentinel is not None or (now - getattr(self.strategy, "_t24_ts", 0.0)) >= self.strategy._t24_ttl
        if need_bulk_ticker:
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

        if self.sentinel:
            try:
                self.sentinel.refresh(syms, prefetched=ticker_map if ticker_map else None)
            except Exception as exc:
                log.debug(f"sentinel refresh failed: {exc}")

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

        for sym in syms:
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
                self.handle_symbol(sym, pos_map, book_ticker=book_ticker_map.get(sym))
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

        if self._manual_state_dirty:
            self.trade_mgr.save()
            self._manual_state_dirty = False

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
            return

        while running:
            t0 = time.time()
            self.run_once()
            dt = time.time() - t0
            log.info("Cycle finished in %.2fs.", dt)
            if not running:
                break
            time.sleep(max(1, LOOP_SLEEP))
        log.info("Bot stopped. Safe to exit.")

# ========= main =========
if __name__ == "__main__":
    run_once = os.getenv("ASTER_RUN_ONCE", "").lower() in ("1", "true", "yes", "on")
    Bot().run(loop=not run_once)
