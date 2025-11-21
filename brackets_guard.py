# brackets_guard.py
# Robuster Bracket-Manager (kompatibel zu Binance Futures / Aster DEX)
# - ensure_after_entry(...) setzt/repariert STOP + TAKE_PROFIT (reduceOnly/closePosition)
# - replace_tp_for_open_position(...) ersetzt TP (oder SL, wenn Preis jenseits von Entry liegt)
# - toleriert alte & neue Bot-Signaturen (mit/ohne qty+entry)
# - nutzt working_type (MARK_PRICE/CONTRACT_PRICE), recv_window & sauberes Runden

from __future__ import annotations
import os, time, math, json, logging, hmac, hashlib
from typing import Dict, Optional, Tuple, List
from pathlib import Path
from urllib.parse import urlencode

import requests

_ROOT_DIR = Path(__file__).resolve().parent

def _resolve_path(env_key: str, default_name: str) -> str:
    raw = os.getenv(env_key, default_name) or default_name
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = _ROOT_DIR / candidate
    return str(candidate)

ASTER_STATE_FILE = _resolve_path("ASTER_STATE_FILE", "aster_state.json")
ASTER_QUEUE_FILE = _resolve_path("ASTER_BRACKETS_QUEUE_FILE", "brackets_queue.json")

def _envf(k: str, default: float) -> float:
    try:
        return float(os.getenv(k, str(default)))
    except Exception:
        return default

# --------------------------- Minimal internal Exchange -----------------------
class _LiteExchange:
    def __init__(self, base: str, key: str, sec: str, recv_window: int = 10000, timeout_sec: int = 10):
        self.base, self.k, self.s = base.rstrip("/"), key, sec
        self.recv_window, self.timeout = int(recv_window), int(timeout_sec)

    def _sign(self, params: Dict[str, str]) -> Dict[str, str]:
        params = dict(params)
        params["timestamp"] = str(int(time.time() * 1000))
        params["recvWindow"] = str(self.recv_window)
        qs = urlencode(params)
        sig = hmac.new(self.s.encode(), qs.encode(), hashlib.sha256).hexdigest()
        params["signature"] = sig
        return params

    def _headers(self) -> Dict[str, str]:
        return {"X-MBX-APIKEY": self.k} if self.k else {}

    def _req(self, method: str, path: str, params: Dict[str, str], signed: bool) -> dict:
        url = f"{self.base}{path}"
        if signed:
            params = self._sign(params)
            r = requests.request(method, url, params=params, headers=self._headers(), timeout=self.timeout)
        else:
            r = requests.request(method, url, params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    # Unsigned
    def get_book_ticker(self, symbol: str) -> dict:
        return self._req("GET", "/fapi/v1/ticker/bookTicker", {"symbol": symbol}, signed=False)

    def get_exchange_info(self) -> dict:
        return self._req("GET", "/fapi/v1/exchangeInfo", {}, signed=False)

    def get_mark_price(self, symbol: str) -> float:
        # Binance Futures endpoint (public)
        data = self._req("GET", "/fapi/v1/premiumIndex", {"symbol": symbol}, signed=False)
        try:
            return float(data.get("markPrice", 0.0) or 0.0)
        except Exception:
            return 0.0

    def get_open_orders(self, symbol: str) -> List[dict]:
        return self._req("GET", "/fapi/v1/openOrders", {"symbol": symbol}, signed=True)

    def cancel_order(self, symbol: str, order_id: int) -> dict:
        return self._req("DELETE", "/fapi/v1/order", {"symbol": symbol, "orderId": str(order_id)}, signed=True)

    def place_order(self, **params) -> dict:
        return self._req("POST", "/fapi/v1/order", params, signed=True)

    def get_position_risk(self) -> List[dict]:
        return self._req("GET", "/fapi/v2/positionRisk", {}, signed=True)

# ------------------------------- Guard ---------------------------------------
class BracketGuard:
    def __init__(
        self,
        exchange: Optional[_LiteExchange] = None,
        state_file: Optional[str] = None,
        queue_file: Optional[str] = None,
        working_type: str = "MARK_PRICE",
        recv_window: int = 10000,
        log: Optional[logging.Logger] = None,
        repair_interval_sec: int = 5,
        timeout_sec: int = 10,
        # „leichte“ Variante – falls kein Exchange übergeben wird:
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        **_,
    ) -> None:
        self.log = log or logging.getLogger("brackets")
        self.working_type = str(working_type or "MARK_PRICE")
        self.recv_window = int(recv_window)
        self.repair_interval_sec = int(repair_interval_sec)
        self.timeout_sec = int(timeout_sec)

        self.state_file = state_file or ASTER_STATE_FILE
        self.queue_file = queue_file or ASTER_QUEUE_FILE

        if exchange is not None:
            self.ex = exchange
        else:
            base = base_url or os.getenv("ASTER_EXCHANGE_BASE", "https://fapi.asterdex.com")
            key = api_key or os.getenv("ASTER_API_KEY", "")
            sec = api_secret or os.getenv("ASTER_API_SECRET", "")
            self.ex = _LiteExchange(base, key, sec, recv_window=self.recv_window, timeout_sec=self.timeout_sec)

        # Meta aus exchangeInfo (tickSize)
        self._tick_cache: Dict[str, float] = {}
        try:
            info = self.ex.get_exchange_info()
            for s in info.get("symbols", []):
                sym = s.get("symbol")
                fdict = {f.get("filterType"): f for f in s.get("filters", [])}
                tick = float(fdict.get("PRICE_FILTER", {}).get("tickSize", "0.0001") or 0.0001)
                self._tick_cache[sym] = tick
        except Exception:
            pass

    # ------------------------------- Rounding --------------------------------
    def _tick(self, symbol: str) -> float:
        return float(self._tick_cache.get(symbol, 0.0001) or 0.0001)

    @staticmethod
    def _floor_to(x: float, step: float) -> float:
        return math.floor(float(x) / step) * step

    @staticmethod
    def _ceil_to(x: float, step: float) -> float:
        return math.ceil(float(x) / step) * step

    def _ref_price(self, symbol: str) -> float:
        try:
            m = self.ex.get_mark_price(symbol)
            if m > 0:
                return m
        except Exception:
            pass
        try:
            bt = self.ex.get_book_ticker(symbol)
            a = float(bt.get("askPrice", 0) or 0); b = float(bt.get("bidPrice", 0) or 0)
            if a > 0 and b > 0:
                return (a + b) / 2.0
        except Exception:
            pass
        return 0.0

    @staticmethod
    def _format_decimal(value: float) -> str:
        s = f"{float(value):.12f}".rstrip("0").rstrip(".")
        return s or "0"

    def _build_bracket_payload(
        self,
        kind: str,
        side: str,
        price: float,
        position_side: Optional[str] = None,
    ) -> str:
        payload = {
            "type": "STOP_MARKET" if kind.upper() == "STOP" else "TAKE_PROFIT_MARKET",
            "trigger": {
                "type": self.working_type,
                "price": self._format_decimal(price),
            },
            "closePosition": True,
        }
        if position_side:
            payload["positionSide"] = position_side
        return json.dumps(payload, separators=(",", ":"))

    def _round_trigger(self, symbol: str, side: str, kind: str, price: float, ref: Optional[float], safety_ticks: int = 1) -> float:
        """
        kind: "STOP" oder "TP"; side: "BUY" (long) / "SELL" (short)
        Runden + Sicherheitsabstand relativ zu ref (entry/mark/mid).
        """
        step = self._tick(symbol)
        px = float(price)
        if ref is None or ref <= 0:
            return self._floor_to(px, step)

        gap = max(1, int(safety_ticks)) * step
        if side == "BUY":  # long
            if kind == "STOP":
                px = min(px, ref - gap)
                px = self._floor_to(px, step)
            else:  # TP
                px = max(px, ref + gap)
                px = self._ceil_to(px, step)
        else:  # short
            if kind == "STOP":
                px = max(px, ref + gap)
                px = self._ceil_to(px, step)
            else:  # TP
                px = min(px, ref - gap)
                px = self._floor_to(px, step)
        return px

    # ------------------------------- Low-level Place --------------------------
    def place_sl(
        self,
        symbol: str,
        side: str,
        qty: float,
        stop_price: float,
        ref: Optional[float] = None,
        safety_ticks: int = 1,
        position_side: Optional[str] = None,
    ) -> dict:
        """
        SL für eine bestehende Position platzieren (closePosition=True).
        Für Long (BUY) → SL ist SELL STOP_MARKET; für Short → BUY STOP_MARKET.
        """
        ref = self._ref_price(symbol) if ref is None else ref
        px = self._round_trigger(symbol, side, "STOP", stop_price, ref, safety_ticks=safety_ticks)
        opp_side = "SELL" if side == "BUY" else "BUY"
        params = {
            "symbol": symbol,
            "side": opp_side,
            "type": "STOP_MARKET",
            "workingType": self.working_type,
            "closePosition": True,
            "stopPrice": self._format_decimal(px),
        }
        params["stopLoss"] = self._build_bracket_payload("STOP", side, px, position_side=position_side)
        if position_side:
            params["positionSide"] = position_side
        return self.ex.place_order(**params)

    def place_tp(
        self,
        symbol: str,
        side: str,
        qty: float,
        take_profit_price: float,
        ref: Optional[float] = None,
        safety_ticks: int = 1,
        position_side: Optional[str] = None,
    ) -> dict:
        """
        TP für eine bestehende Position platzieren (closePosition=True).
        Für Long (BUY) → TP ist SELL TAKE_PROFIT_MARKET; für Short → BUY TAKE_PROFIT_MARKET.
        """
        ref = self._ref_price(symbol) if ref is None else ref
        px = self._round_trigger(symbol, side, "TP", take_profit_price, ref, safety_ticks=safety_ticks)
        opp_side = "SELL" if side == "BUY" else "BUY"
        params = {
            "symbol": symbol,
            "side": opp_side,
            "type": "TAKE_PROFIT_MARKET",
            "workingType": self.working_type,
            "closePosition": True,
            "stopPrice": self._format_decimal(px),
        }
        params["takeProfit"] = self._build_bracket_payload("TP", side, px, position_side=position_side)
        if position_side:
            params["positionSide"] = position_side
        return self.ex.place_order(**params)

    # ------------------------------- Helpers ---------------------------------
    def get_open_orders(self, symbol: str) -> List[dict]:
        try:
            return self.ex.get_open_orders(symbol) or []
        except Exception:
            return []

    def cancel_order(self, symbol: str, order_id: int) -> None:
        try:
            self.ex.cancel_order(symbol, int(order_id))
        except Exception:
            pass

    def _is_immediate_trigger_error(self, e: Exception) -> bool:
        try:
            if hasattr(e, "response") and e.response is not None:
                msg = (e.response.json() or {}).get("msg", "")
                return "immediately" in msg.lower()
        except Exception:
            pass
        return False

    def _log_http_fail(self, kind: str, symbol: str, e: Exception) -> None:
        try:
            if hasattr(e, "response") and e.response is not None:
                msg = e.response.json().get("msg", str(e))
            else:
                msg = str(e)
        except Exception:
            msg = str(e)
        self.log.debug(f"BRACKET {kind} place fail {symbol}: {msg}")

    def _place_with_retry(
        self,
        fn,
        symbol: str,
        side: str,
        qty: float,
        price: float,
        ref: Optional[float],
        kind: str,
        position_side: Optional[str] = None,
    ):
        try:
            fn(symbol, side, abs(qty), price, ref=ref, safety_ticks=1, position_side=position_side)
            return
        except requests.HTTPError as e:
            if self._is_immediate_trigger_error(e):
                try:
                    fn(
                        symbol,
                        side,
                        abs(qty),
                        price,
                        ref=ref,
                        safety_ticks=4,
                        position_side=position_side,
                    )  # +4 Ticks
                    return
                except Exception as e2:
                    self._log_http_fail(kind, symbol, e2)
            else:
                self._log_http_fail(kind, symbol, e)
        except Exception as e:
            self.log.debug(f"BRACKET {kind} place fail {symbol}: {e}")

    # ----------------------------- Core logic --------------------------------
    def _classify_orders(self, orders: List[dict]) -> Tuple[Optional[dict], Optional[dict]]:
        stop, tp = None, None
        for o in orders or []:
            ty = str(o.get("type", "")).upper()
            if "STOP" in ty and "TAKE" not in ty:
                stop = o
            elif "TAKE_PROFIT" in ty:
                tp = o
        return stop, tp

    def _position_snapshot(self, symbol: str) -> List[Tuple[str, float]]:
        try:
            pos = self.ex.get_position_risk()
            out: List[Tuple[str, float]] = []
            for p in pos or []:
                if p.get("symbol") != symbol:
                    continue
                pos_side = str(p.get("positionSide", "") or "BOTH").upper()
                amt = float(p.get("positionAmt", "0") or 0.0)
                out.append((pos_side, amt))
            return out
        except Exception:
            return []

    def _position_side_amt(self, symbol: str) -> Tuple[str, float, str]:
        try:
            pos = self._position_snapshot(symbol)
            fallback: Tuple[str, float, str] = ("BUY", 0.0, "BOTH")
            for pos_side, amt in pos:
                if pos_side == "BOTH":
                    if amt > 0:
                        return "BUY", amt, "BOTH"
                    if amt < 0:
                        return "SELL", amt, "BOTH"
                    fallback = ("BUY", 0.0, "BOTH")
                elif pos_side == "LONG":
                    if amt != 0:
                        return "BUY", amt, "LONG"
                    fallback = ("BUY", 0.0, "LONG")
                elif pos_side == "SHORT":
                    if amt != 0:
                        return "SELL", amt, "SHORT"
                    fallback = ("SELL", 0.0, "SHORT")
            return fallback
        except Exception:
            pass
        return "BUY", 0.0, "BOTH"

    def _position_side_param(self, symbol: str, side: str) -> Optional[str]:
        desired = "LONG" if side == "BUY" else "SHORT"
        try:
            pos = self._position_snapshot(symbol)
            fallback = None
            for pos_side, _ in pos:
                if pos_side == desired:
                    return desired
                if pos_side == "BOTH":
                    fallback = "BOTH"
            return fallback
        except Exception:
            return None

    def _decide_exit_kind(self, symbol: str, new_price: float, side: Optional[str] = None) -> str:
        """
        Grobe Heuristik: wenn neuer Preis auf der SL-Seite vom Referenzpreis liegt → STOP, sonst TP.
        """
        ref = self._ref_price(symbol)
        if not ref or ref <= 0:
            return "TP"
        if side is None:
            side, _, _ = self._position_side_amt(symbol)
        if side == "BUY":
            return "STOP" if new_price < ref else "TP"
        else:
            return "STOP" if new_price > ref else "TP"

    def replace_exit(self, symbol: str, quantity: float, new_price: float, side: Optional[str] = None) -> None:
        side_inferred, amt, pos_side = self._position_side_amt(symbol)
        if abs(amt) <= 0.0:
            return
        side = side or side_inferred
        ref = self._ref_price(symbol)
        kind = self._decide_exit_kind(symbol, new_price, side)
        orders = self.get_open_orders(symbol)
        stop, tp = self._classify_orders(orders)
        try:
            if kind == "STOP":
                if stop is not None:
                    try: self.cancel_order(symbol, int(stop.get("orderId")))
                    except Exception: pass
                self._place_with_retry(
                    self.place_sl,
                    symbol,
                    side,
                    abs(amt),
                    new_price,
                    ref,
                    "STOP",
                    position_side=pos_side,
                )
            else:
                if tp is not None:
                    try: self.cancel_order(symbol, int(tp.get("orderId")))
                    except Exception: pass
                self._place_with_retry(
                    self.place_tp,
                    symbol,
                    side,
                    abs(amt),
                    new_price,
                    ref,
                    "TP",
                    position_side=pos_side,
                )
        except Exception as e:
            self.log.debug(f"BRACKET replace_exit fail {symbol}: {e}")

    # API erwartet häufig diese Convenience-Funktionen:
    def replace_tp_for_open_position(self, symbol: str, quantity: float, new_price: float, side: Optional[str] = None) -> None:
        self.replace_exit(symbol, quantity, new_price, side=side)

    # Backward/forward compatible: beide Signaturen akzeptieren
    def ensure_after_entry(self, symbol: str, side: str, *args) -> bool:
        """
        neue Signatur: ensure_after_entry(symbol, side, quantity, entry_price, stop_price, take_profit)
        alte Signatur: ensure_after_entry(symbol, side, stop_price, take_profit)
        """
        try:
            if len(args) == 4:
                quantity, entry_price, sl_price, tp_price = args
            elif len(args) == 2:
                sl_price, tp_price = args
                quantity, entry_price = None, None
            else:
                raise TypeError("ensure_after_entry expects 4 or 2 extra args")
        except Exception:
            return False

        orders = self.get_open_orders(symbol)
        stop, tp = self._classify_orders(orders)
        ref = entry_price if entry_price is not None else self._ref_price(symbol)

        def _is_invalid_against_ref(kind: str, price: Optional[float]) -> bool:
            if price is None or ref is None or ref <= 0:
                return False
            if side == "BUY":
                return price >= ref if kind == "STOP" else price <= ref
            return price <= ref if kind == "STOP" else price >= ref

        # Falls SL/TP fehlen → heuristisch ergänzen
        if (sl_price is None or tp_price is None) and entry_price is not None:
            tp_mult = _envf("ASTER_TP_ATR_MULT", 1.6)
            sl_mult = _envf("ASTER_SL_ATR_MULT", 1.0)
            ratio = (tp_mult / sl_mult) if sl_mult > 0 else 1.6
            risk_abs = abs(entry_price - (entry_price - 1e-9)) + 1e-6  # dummy > 0
            if sl_price is None:
                sl_price = entry_price - risk_abs if side == "BUY" else entry_price + risk_abs
            if tp_price is None:
                tp_price = entry_price + risk_abs * ratio if side == "BUY" else entry_price - risk_abs * ratio

        raw_sl_price, raw_tp_price = sl_price, tp_price

        # Runden & Sicherheitsabstand
        if sl_price is not None:
            sl_price = self._round_trigger(symbol, side, "STOP", float(sl_price), ref, safety_ticks=3)
        if tp_price is not None:
            tp_price = self._round_trigger(symbol, side, "TP", float(tp_price), ref, safety_ticks=3)

        position_side = self._position_side_param(symbol, side)

        ok = True
        if _is_invalid_against_ref("STOP", raw_sl_price):
            self.log.debug(
                "ensure_after_entry STOP skipped %s: price %s not on %s side of ref %s",
                symbol,
                raw_sl_price,
                side,
                ref,
            )
            sl_price = None
            ok = False
        if _is_invalid_against_ref("TP", raw_tp_price):
            self.log.debug(
                "ensure_after_entry TP skipped %s: price %s not on %s side of ref %s",
                symbol,
                raw_tp_price,
                side,
                ref,
            )
            tp_price = None
            ok = False
        try:
            if not stop and sl_price is not None:
                self._place_with_retry(
                    self.place_sl,
                    symbol,
                    side,
                    abs(quantity or 0.0),
                    sl_price,
                    ref,
                    "STOP",
                    position_side=position_side,
                )
        except Exception as e:
            self.log.debug(f"ensure_after_entry STOP fail {symbol}: {e}")
            ok = False
        try:
            if not tp and tp_price is not None:
                self._place_with_retry(
                    self.place_tp,
                    symbol,
                    side,
                    abs(quantity or 0.0),
                    tp_price,
                    ref,
                    "TP",
                    position_side=position_side,
                )
        except Exception as e:
            self.log.debug(f"ensure_after_entry TP fail {symbol}: {e}")
            ok = False
        return ok

# -------- module-level alias (der Bot importiert/ruft diesen Namen) ---------
def replace_tp_for_open_position(guard: BracketGuard, symbol: str, quantity: float, new_price: float, side: Optional[str] = None) -> None:
    guard.replace_tp_for_open_position(symbol, quantity, new_price, side=side)
