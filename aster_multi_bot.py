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
import hmac
import hashlib
import logging
import signal
from typing import Dict, List, Tuple, Optional, Any

import requests

try:
    import numpy as np  # noqa: F401
except Exception:
    raise RuntimeError("Dieses Modul benötigt numpy. Bitte: pip install numpy")

from ml_policy import BanditPolicy
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

QUOTE = os.getenv("ASTER_QUOTE", "USDT")
INTERVAL = os.getenv("ASTER_INTERVAL", "5m")
HTF_INTERVAL = os.getenv("ASTER_HTF_INTERVAL", "30m")
KLINES = int(os.getenv("ASTER_KLINES", "360"))

INCLUDE = [s for s in (os.getenv("ASTER_INCLUDE_SYMBOLS", "") or "").split(",") if s]
EXCLUDE = set([s for s in (os.getenv("ASTER_EXCLUDE_SYMBOLS", "") or "").split(",") if s])
UNIVERSE_MAX = int(os.getenv("ASTER_UNIVERSE_MAX", "120"))
UNIVERSE_ROTATE = os.getenv("ASTER_UNIVERSE_ROTATE", "true").lower() in ("1", "true", "yes", "on")

MIN_QUOTE_VOL = float(os.getenv("ASTER_MIN_QUOTE_VOL_USDT", "75000"))
SPREAD_BPS_MAX = float(os.getenv("ASTER_SPREAD_BPS_MAX", "0.0030"))  # 0.30 %
WICKINESS_MAX = float(os.getenv("ASTER_WICKINESS_MAX", "0.97"))
MIN_EDGE_R = float(os.getenv("ASTER_MIN_EDGE_R", "0.30"))

BANDIT_ENABLED = os.getenv("ASTER_BANDIT_ENABLED", "true").lower() in ("1", "true", "yes", "on")
SIZE_MULT_BASE = float(os.getenv("ASTER_SIZE_MULT", "1.00"))
SIZE_MULT_S = float(os.getenv("ASTER_SIZE_MULT_S", str(SIZE_MULT_BASE)))
SIZE_MULT_M = float(os.getenv("ASTER_SIZE_MULT_M", str(1.4 * SIZE_MULT_BASE)))
SIZE_MULT_L = float(os.getenv("ASTER_SIZE_MULT_L", str(1.9 * SIZE_MULT_BASE)))

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

# ========= Utils =========
def ema(data: List[float], period: int) -> List[float]:
    if not data:
        return []
    k = 2.0 / (period + 1.0)
    out = [data[0]]
    for x in data[1:]:
        out.append(out[-1] + k * (x - out[-1]))
    return out

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

def round_price(symbol: str, price: float, tick: float) -> float:
    if tick <= 0:
        return float(price)
    steps = math.floor(price / tick + 1e-12)
    return float(steps * tick)

def format_qty(qty: float, step: float) -> str:
    q = max(0.0, math.floor(qty / step) * step)
    s = f"{q:.12f}".rstrip("0").rstrip(".")
    return s or "0"

# ========= Exchange =========
class Exchange:
    def __init__(self, base: str, api_key: str, api_secret: str, recv_window: int = 10000):
        self.base = base.rstrip("/")
        self.api_key = api_key
        self.api_secret = api_secret
        self.recv_window = recv_window
        self.s = requests.Session()
        self._ts_skew_ms = 0

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/x-www-form-urlencoded"}
        if self.api_key:
            h["X-MBX-APIKEY"] = self.api_key
        return h

    def _sign(self, qs: str) -> str:
        return hmac.new(self.api_secret.encode(), qs.encode(), hashlib.sha256).hexdigest()

    def _ts(self) -> int:
        return int(time.time() * 1000 + self._ts_skew_ms)

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base}{path}"
        r = self.s.get(url, params=params or {}, timeout=15)
        r.raise_for_status()
        return r.json()

    def signed(self, method: str, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        if not self.api_key or not self.api_secret:
            raise RuntimeError("API credentials missing for signed request")
        p = dict(params or {})
        p["timestamp"] = self._ts()
        p["recvWindow"] = self.recv_window
        qs = "&".join(f"{k}={p[k]}" for k in sorted(p))
        sig = self._sign(qs)
        url = f"{self.base}{path}?{qs}&signature={sig}"
        req = {"get": self.s.get, "post": self.s.post, "delete": self.s.delete}[method.lower()]
        r = req(url, headers=self._headers(), timeout=20)
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

    def get_book_ticker(self, symbol: str) -> Dict[str, Any]:
        return self.get("/fapi/v1/ticker/bookTicker", {"symbol": symbol})

    def get_position_risk(self) -> Any:
        return self.signed("get", "/fapi/v2/positionRisk", {})

    def post_order(self, params: Dict[str, Any]) -> Any:
        if PAPER:
            return {"paper": True, "params": params}
        return self.signed("post", "/fapi/v1/order", params)

    def cancel_all(self, symbol: str) -> Any:
        if PAPER:
            return {"paper": True, "cancel": symbol}
        return self.signed("delete", "/fapi/v1/allOpenOrders", {"symbol": symbol})

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
    def __init__(self, exchange: Exchange):
        self.exchange = exchange
        self.min_quote_vol = MIN_QUOTE_VOL
        self.spread_bps_max = SPREAD_BPS_MAX
        self.wickiness_max = WICKINESS_MAX
        # 24h Ticker Cache
        self._t24_cache: Dict[str, dict] = {}
        self._t24_ts = 0.0
        self._t24_ttl = 120

    def _get_qv_score(self, symbol: str) -> float:
        now = time.time()
        try:
            if (now - self._t24_ts) > self._t24_ttl or not self._t24_cache:
                data = self.exchange.get_ticker_24hr()
                if isinstance(data, list):
                    self._t24_cache = {d.get("symbol"): d for d in data if isinstance(d, dict)}
                self._t24_ts = now
            rec = self._t24_cache.get(symbol) or self.exchange.get_ticker_24hr(symbol)
            qvol = float(rec.get("quoteVolume", 0.0) or 0.0) if rec else 0.0
            return min(2.0, qvol / max(self.min_quote_vol, 1e-9)) if qvol > 0 else 0.0
        except Exception:
            return 0.0

    def _skip(self, reason: str, symbol: str, extra: Dict[str, Any] = None):
        if extra:
            log.debug(f"SKIP {symbol}: {reason} {extra}")
        else:
            log.debug(f"SKIP {symbol}: {reason}")
        return "NONE", 0.0, {}, 0.0

    def compute_signal(self, symbol: str) -> Tuple[str, float, Dict[str, float], float]:
        try:
            kl = self.exchange.get_klines(symbol, INTERVAL, KLINES)
            if not kl or len(kl) < 60:
                return self._skip("few_klines", symbol, {"k": len(kl) if kl else 0})
            htf = self.exchange.get_klines(symbol, HTF_INTERVAL, 120)
        except Exception as e:
            return self._skip("klines_err", symbol, {"err": str(e)[:80]})

        closes = [x[4] for x in kl]; highs = [x[2] for x in kl]; lows = [x[3] for x in kl]
        last = closes[-1]

        # Spread (adaptiv an ATR%)
        try:
            bt = self.exchange.get_book_ticker(symbol)
            ask = float(bt.get("askPrice", 0.0) or 0.0)
            bid = float(bt.get("bidPrice", 0.0) or 0.0)
            mid = (ask + bid) / 2.0 if ask > 0 and bid > 0 else last
            spread_bps = (ask - bid) / max(mid, 1e-9)
        except Exception:
            mid, spread_bps = last, 0.0

        atr = atr_abs_from_klines(kl, 14)
        atrp = atr / max(1e-9, last)
        dyn_spread_max = max(self.spread_bps_max, 0.5 * atrp)
        if spread_bps > dyn_spread_max:
            return self._skip("spread", symbol, {"spread": f"{spread_bps:.5f}", "max": f"{dyn_spread_max:.5f}"})

        # Wickiness
        try:
            wick_hi = highs[-1] - max(closes[-1], float(kl[-1][1]))
            wick_lo = min(closes[-1], float(kl[-1][1])) - lows[-1]
            wickiness = max(wick_hi, wick_lo) / max(1e-9, highs[-1] - lows[-1])
            if wickiness > self.wickiness_max:
                return self._skip("wicky", symbol, {"w": f"{wickiness:.2f}"})
        except Exception:
            pass

        htf_close = [x[4] for x in htf]
        ema_fast = ema(closes, 21); ema_slow = ema(closes, 55)
        ema_htf = ema(htf_close, 55)
        cross_up = ema_fast[-2] < ema_slow[-2] and ema_fast[-1] > ema_slow[-1]
        cross_dn = ema_fast[-2] > ema_slow[-2] and ema_fast[-1] < ema_slow[-1]
        rsi14 = rsi(closes, 14)

        htf_trend_up = ema_htf[-1] > ema_htf[-5]
        htf_trend_down = ema_htf[-1] < ema_htf[-5]

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
                return self._skip("no_cross", symbol)
        else:
            return self._skip("no_cross", symbol)

        slope_htf = (ema_htf[-1] - ema_htf[-5]) / max(1e-9, ema_htf[-5])
        expected_R = abs(slope_htf) * 20.0
        if expected_R < MIN_EDGE_R:
            return self._skip("edge_r", symbol, {"expR": f"{expected_R:.3f}", "minR": f"{MIN_EDGE_R:.3f}"})

        qv_score = self._get_qv_score(symbol)
        ctx: Dict[str, float] = {
            "adx": 0.0,
            "atr_pct": atrp,
            "slope_htf": slope_htf,
            "rsi": float(rsi14[-1]),
            "funding": 0.0,
            "qv_score": float(qv_score),
            "trend": 1.0 if sig == "BUY" else -1.0,
            "regime_adx": 0.0,
            "regime_slope": 0.0,
            "spread_bps": float(spread_bps),
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
        try:
            self.history_max = int(os.getenv("ASTER_HISTORY_MAX", "250"))
        except Exception:
            self.history_max = 250

    def save(self) -> None:
        try:
            with open(STATE_FILE, "w") as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            log.warning(f"state save failed: {e}")

    def note_entry(self, symbol: str, entry: float, sl: float, tp: float, side: str, qty: float, ctx: Dict[str, float], bucket: str, atr_abs: float):
        self.state["live_trades"][symbol] = {
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
        self.save()
        if self.policy and BANDIT_ENABLED:
            try:
                self.policy.note_entry(symbol, ctx=ctx, size_bucket=bucket)
            except Exception as e:
                log.debug(f"policy note_entry fail: {e}")

    def remove_closed_trades(self):
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
                    self.policy.note_exit(symbol, pnl_r=r_mult)
                except Exception as e:
                    log.debug(f"policy note_exit fail: {e}")
            hist = self.state.setdefault("trade_history", [])
            closed_at = time.time()
            opened_at = float(rec.get("opened_at", closed_at) or closed_at)
            hist.append({
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
            })
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
        if not FAST_TP_ENABLED or abs(pos_amt) < 1e-12 or atr_abs <= 0.0:
            return False
        cd_until = self.state.setdefault("fast_tp_cooldown", {}).get(symbol, 0.0)
        if time.time() < cd_until:
            return False

        side_open = "BUY" if pos_amt > 0 else "SELL"
        risk = max(abs(entry_px - sl_px), 1e-9)
        r_now = (last_px - entry_px) / risk if side_open == "BUY" else (entry_px - last_px) / risk
        if r_now < FASTTP_MIN_R:
            return False

        ret1 = self._ret(symbol, 60)
        ret3 = self._ret(symbol, 180)
        reversal = (ret1 <= FAST_TP_RET1 or ret3 <= FAST_TP_RET3) if pos_amt > 0 else (ret1 >= -FAST_TP_RET1 or ret3 >= -FAST_TP_RET3)
        if not reversal:
            return False

        snap = FASTTP_SNAP_ATR * max(atr_abs, 1e-12)
        new_exit = (max(entry_px + 0.05 * risk, last_px - snap)
                    if pos_amt > 0 else
                    min(entry_px - 0.05 * risk, last_px + snap))

        qty_abs = abs(pos_amt)
        try:
            ok = _bg_replace_tp(
                self.guard,
                symbol,
                qty_abs,
                new_exit,
                side=("BUY" if pos_amt > 0 else "SELL")
            )
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
        self.policy: Optional[BanditPolicy] = None
        if BANDIT_ENABLED:
            try:
                self.policy = BanditPolicy()
            except Exception as e:
                log.debug(f"ML policy init failed: {e}")
        self.state = {}
        try:
            if os.path.exists(STATE_FILE):
                self.state = json.load(open(STATE_FILE, "r"))
        except Exception:
            self.state = {}
        self.guard = BracketGuard(
            base_url=BASE,
            api_key=API_KEY,
            api_secret=API_SECRET,
            working_type=WORKING_TYPE,
            recv_window=RECV_WINDOW,
        )
        self.trade_mgr = TradeManager(self.exchange, self.policy, self.state)
        self.fasttp = FastTP(self.exchange, self.guard, self.state)
        self._strategy = Strategy(self.exchange)

    @property
    def strategy(self) -> Strategy:
        return self._strategy

    def _size_mult_from_bucket(self, bucket: str) -> float:
        return {"S": SIZE_MULT_S, "M": SIZE_MULT_M, "L": SIZE_MULT_L}.get(bucket, SIZE_MULT_S)

    def handle_symbol(self, symbol: str, pos_map: Dict[str, float]):
        # bereits offene Position?
        amt = float(pos_map.get(symbol, 0.0) or 0.0)
        if abs(amt) > 1e-12:
            return

        sig, atr_abs, ctx, price = self.strategy.compute_signal(symbol)
        if sig == "NONE":
            return

        # Policy: Gate + Size
        size_mult = SIZE_MULT_S
        bucket = "S"
        if BANDIT_ENABLED and self.policy:
            try:
                decision, extras = self.policy.decide(ctx)  # "TAKE"/"SKIP" + {"size_bucket": "..."}
                if decision != "TAKE":
                    return
                bucket = extras.get("size_bucket", "S")
                size_mult = self._size_mult_from_bucket(bucket)
            except Exception as e:
                log.debug(f"policy decide fail: {e}")

        # Entry/SL/TP
        try:
            bt = self.exchange.get_book_ticker(symbol)
            px = float(bt.get("askPrice" if sig == "BUY" else "bidPrice", 0.0) or 0.0) or price
        except Exception:
            px = price

        sl_dist = max(1e-9, SL_ATR_MULT * atr_abs)
        tp_dist = max(1e-9, TP_ATR_MULT * atr_abs)
        is_buy = (sig == "BUY")
        sl = px - sl_dist if is_buy else px + sl_dist
        tp = px + tp_dist if is_buy else px - tp_dist

        tick = float(self.risk.symbol_filters.get(symbol, {}).get("tickSize", 0.0001) or 0.0001)
        sl = round_price(symbol, sl, tick)
        tp = round_price(symbol, tp, tick)

        qty = self.risk.compute_qty(symbol, px, sl, size_mult)
        if qty <= 0:
            return

        step = float(self.risk.symbol_filters.get(symbol, {}).get("stepSize", 0.0001) or 0.0001)
        q_str = format_qty(qty, step)

        # Entry
        try:
            self.exchange.post_order({"symbol": symbol, "side": sig, "type": "MARKET", "quantity": q_str})
            # Brackets – versuche neue Signatur (qty+entry), fallback auf alte
            try:
                ok = self.guard.ensure_after_entry(symbol, sig, float(q_str), px, sl, tp)
            except TypeError:
                ok = self.guard.ensure_after_entry(symbol, sig, sl, tp)
            if not ok:
                log.warning(f"Bracket für {symbol} nicht vollständig gesetzt.")
            self.trade_mgr.note_entry(symbol, px, sl, tp, sig, float(q_str), ctx, bucket, atr_abs)
            log.info(f"ENTRY {symbol} {sig} qty={q_str} px≈{px:.6f} SL={sl:.6f} TP={tp:.6f} bucket={bucket}")
        except Exception as e:
            log.debug(f"entry fail {symbol}: {e}")
            self.state.setdefault("fail_skip_until", {})[symbol] = time.time() + 60

    def run_once(self):
        syms = self.universe.refresh()
        log.info("Scan %d Symbole%s", len(syms), f": {', '.join(syms[:12])}{'...' if len(syms)>12 else ''}")

        # geschlossene Trades aus State räumen + Policy belohnen
        self.trade_mgr.remove_closed_trades()

        # einmalig Positionen holen (pos_map), für FastTP & Skip bei offenen Positionen
        try:
            pos = self.exchange.get_position_risk()
            pos_map = {p.get("symbol"): float(p.get("positionAmt", "0") or 0.0) for p in pos}
        except Exception:
            pos_map = {}

        for sym in syms:
            # Preis tracken für FastTP
            mid = 0.0
            try:
                bt = self.exchange.get_book_ticker(sym)
                ask = float(bt.get("askPrice", 0.0) or 0.0)
                bid = float(bt.get("bidPrice", 0.0) or 0.0)
                mid = (ask + bid) / 2.0 if ask > 0 and bid > 0 else 0.0
                if mid > 0:
                    self.fasttp.track(sym, mid)
            except Exception:
                pass

            amt = pos_map.get(sym, 0.0)
            if abs(amt) > 1e-12:
                rec = self.state.get("live_trades", {}).get(sym)
                if rec and mid > 0:
                    atr_abs = float(rec.get("atr_abs", 0.0))
                    if atr_abs > 0.0:
                        self.fasttp.maybe_apply(sym, amt, float(rec.get("entry")), float(rec.get("sl")), mid, atr_abs)
                continue

            try:
                self.handle_symbol(sym, pos_map)
            except Exception as e:
                log.debug(f"signal handling fail {sym}: {e}")
            time.sleep(0.05)

    def run(self, loop: bool = True):
        log.info("Start Bot – Mode=%s, Loop=%s", "PAPER" if PAPER else "LIVE", loop)
        running = True
        def _stop(*_):
            nonlocal running
            running = False
            log.info("Signal empfangen – beende nach Zyklus.")
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
            log.info("Zyklus beendet (%.2fs).", dt)
            if not running:
                break
            time.sleep(max(1, LOOP_SLEEP))
        log.info("Bot gestoppt.")

# ========= main =========
if __name__ == "__main__":
    run_once = os.getenv("ASTER_RUN_ONCE", "").lower() in ("1", "true", "yes", "on")
    Bot().run(loop=not run_once)
