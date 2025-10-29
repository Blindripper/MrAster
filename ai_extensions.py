"""AI-driven learning helpers for MrAster bot."""
from __future__ import annotations

import time
from typing import Any, Callable, Dict, Iterable, List, Optional

POSTMORTEM_FEATURE_MAP: Dict[str, str] = {
    "trend_break": "pm_trend_break",
    "news_driver": "pm_news_driver",
    "liquidity_gap": "pm_liquidity_gap",
    "execution_delay": "pm_execution_delay",
    "sentiment_conflict": "pm_sentiment_conflict",
    "macro_event": "pm_macro_event",
}
POSTMORTEM_DEFAULT_WEIGHT = 0.15
POSTMORTEM_DECAY = 0.92


class PostmortemLearning:
    """Track qualitative LLM post-mortem labels and expose them as numeric features."""

    def __init__(self, state: Dict[str, Any]):
        self._root = state
        self._store = self._root.setdefault(
            "postmortem_learning",
            {"symbols": {}, "global": {"features": {}, "updated": 0.0}},
        )

    @property
    def feature_keys(self) -> Iterable[str]:
        return POSTMORTEM_FEATURE_MAP.values()

    def register(
        self,
        symbol: str,
        feature_scores: Dict[str, float],
        *,
        pnl_r: float,
    ) -> None:
        if not symbol:
            symbol = "*"
        now = time.time()
        normalized = self._normalize_scores(feature_scores, pnl_r)
        sym_bucket = self._store.setdefault(
            "symbols", {}).setdefault(symbol, {"features": {}, "updated": 0.0}
        )
        self._blend(sym_bucket.setdefault("features", {}), normalized, now)
        sym_bucket["updated"] = now
        self._blend(self._store.setdefault("global", {"features": {}, "updated": 0.0}).setdefault("features", {}), normalized, now)
        self._store.setdefault("global", {})["updated"] = now

    def context_features(self, symbol: str) -> Dict[str, float]:
        features: Dict[str, float] = {key: 0.0 for key in self.feature_keys}
        if not symbol:
            symbol = "*"
        global_store = self._store.get("global", {})
        global_features = global_store.get("features", {}) if isinstance(global_store, dict) else {}
        for key in features:
            if key in global_features:
                features[key] = float(global_features.get(key, 0.0) or 0.0)
        sym_store = self._store.get("symbols", {})
        sym_features = (
            sym_store.get(symbol, {}).get("features", {}) if isinstance(sym_store, dict) else {}
        )
        if sym_features:
            for key, value in sym_features.items():
                if key in features:
                    features[key] = float(value)
        return features

    def _blend(self, bucket: Dict[str, Any], scores: Dict[str, float], now: float) -> None:
        for key, value in scores.items():
            prev = float(bucket.get(key, 0.0) or 0.0)
            bucket[key] = (prev * POSTMORTEM_DECAY) + (1.0 - POSTMORTEM_DECAY) * float(value)
        stale = [k for k in bucket.keys() if k not in scores and abs(bucket.get(k, 0.0)) < 1e-3]
        for key in stale:
            bucket.pop(key, None)

    def _normalize_scores(self, scores: Dict[str, float], pnl_r: float) -> Dict[str, float]:
        result: Dict[str, float] = {key: 0.0 for key in self.feature_keys}
        if not scores:
            bias = max(min(pnl_r, 3.0), -3.0) / 3.0
            result[POSTMORTEM_FEATURE_MAP["trend_break"]] = bias
            result[POSTMORTEM_FEATURE_MAP["execution_delay"]] = -bias * 0.5
            return result
        for raw_key, mapped_key in POSTMORTEM_FEATURE_MAP.items():
            if mapped_key not in result:
                continue
            value = float(scores.get(mapped_key, scores.get(raw_key, 0.0)) or 0.0)
            value = max(min(value, 1.0), -1.0)
            result[mapped_key] = value
        # fallback weighting if all zeros
        if all(abs(v) < 1e-6 for v in result.values()):
            fallback = max(min(pnl_r, 2.5), -2.5) / 2.5
            for key in result:
                result[key] = fallback * POSTMORTEM_DEFAULT_WEIGHT
        return result


class ParameterTuner:
    """Collect trade outcomes and request AI suggestions for risk overrides."""

    def __init__(
        self,
        state: Dict[str, Any],
        *,
        request_fn: Callable[[str, Dict[str, Any]], Optional[Dict[str, Any]]],
    ) -> None:
        self._root = state
        self._state = self._root.setdefault(
            "param_tuning",
            {
                "history": [],
                "overrides": {},
                "last_ai": 0.0,
                "ai_notes": "",
            },
        )
        self._request_fn = request_fn
        self._min_trades = 12
        self._ai_interval = 20 * 60
        self._history_cap = 240

    def observe(self, trade: Dict[str, Any], features: Dict[str, float]) -> None:
        record = {
            "ts": time.time(),
            "symbol": trade.get("symbol"),
            "side": trade.get("side"),
            "bucket": trade.get("bucket"),
            "pnl_r": float(trade.get("pnl_r", 0.0) or 0.0),
            "features": {k: float(v) for k, v in (features or {}).items()},
        }
        history: List[Dict[str, Any]] = self._state.setdefault("history", [])
        history.append(record)
        if len(history) > self._history_cap:
            del history[: len(history) - self._history_cap]
        self._state["history"] = history
        self._recompute_local_overrides()
        self._maybe_request_ai()

    def overrides(self) -> Dict[str, Any]:
        return dict(self._state.get("overrides", {}))

    def inject_context(self, ctx: Dict[str, Any]) -> None:
        overrides = self.overrides()
        if not overrides:
            return
        ctx["tuning_confidence"] = float(overrides.get("confidence", 0.0))
        ctx["tuning_risk_bias"] = float(overrides.get("sl_atr_mult", 1.0))
        ctx["tuning_size_bias"] = float(overrides.get("size_bias_global", 1.0))

    def _recompute_local_overrides(self) -> None:
        history: List[Dict[str, Any]] = self._state.get("history", [])
        if not history:
            return
        bucket_perf: Dict[str, List[float]] = {"S": [], "M": [], "L": []}
        wins: List[float] = []
        losses: List[float] = []
        for item in history[-120:]:
            pnl_r = float(item.get("pnl_r", 0.0) or 0.0)
            bucket = str(item.get("bucket") or "S").upper()
            bucket_perf.setdefault(bucket, []).append(pnl_r)
            if pnl_r >= 0:
                wins.append(pnl_r)
            else:
                losses.append(pnl_r)
        def _avg(values: List[float]) -> float:
            return sum(values) / len(values) if values else 0.0
        overrides = dict(self._state.get("overrides", {}))
        overrides.setdefault("size_bias", {})
        for bucket, values in bucket_perf.items():
            avg = _avg(values)
            overrides["size_bias"][bucket] = float(max(0.6, min(1.8, 1.0 + avg * 0.15)))
        avg_win = _avg(wins)
        avg_loss = _avg(losses)
        if wins or losses:
            sl_bias = max(0.6, min(1.5, 1.0 + (-avg_loss) * 0.05))
            tp_bias = max(0.8, min(2.4, 1.0 + avg_win * 0.04))
            overrides["sl_atr_mult"] = sl_bias
            overrides["tp_atr_mult"] = tp_bias
        overrides["size_bias_global"] = float(sum(overrides["size_bias"].values()) / max(len(overrides["size_bias"]) or 1, 1))
        overrides.setdefault("confidence", min(1.0, len(history) / 60.0))
        self._state["overrides"] = overrides
        self._root["tuning_overrides"] = overrides

    def _maybe_request_ai(self) -> None:
        history: List[Dict[str, Any]] = self._state.get("history", [])
        if len(history) < self._min_trades:
            return
        now = time.time()
        if now - float(self._state.get("last_ai", 0.0) or 0.0) < self._ai_interval:
            return
        payload = {
            "trades": [
                {
                    "pnl_r": round(float(item.get("pnl_r", 0.0)), 3),
                    "bucket": item.get("bucket"),
                    "features": {
                        k: round(float(v), 3)
                        for k, v in (item.get("features") or {}).items()
                        if abs(float(v)) > 1e-4
                    },
                }
                for item in history[-60:]
            ],
            "overrides": self._state.get("overrides", {}),
        }
        suggestions = self._request_fn("tuning", payload)
        if not suggestions:
            return
        overrides = dict(self._state.get("overrides", {}))
        size_bias = suggestions.get("size_bias") or {}
        if isinstance(size_bias, dict):
            overrides.setdefault("size_bias", {})
            for bucket, value in size_bias.items():
                try:
                    overrides["size_bias"][bucket.upper()] = float(value)
                except (TypeError, ValueError):
                    continue
        for key in ("sl_atr_mult", "tp_atr_mult", "confidence"):
            if key in suggestions:
                try:
                    overrides[key] = float(suggestions[key])
                except (TypeError, ValueError):
                    continue
        overrides["size_bias_global"] = float(
            sum(overrides.get("size_bias", {"S": 1.0}).values())
            / max(len(overrides.get("size_bias", {})) or 1, 1)
        )
        self._state["overrides"] = overrides
        self._root["tuning_overrides"] = overrides
        self._state["last_ai"] = time.time()
        note = suggestions.get("note") if isinstance(suggestions, dict) else None
        if isinstance(note, str):
            self._state["ai_notes"] = note.strip()


class PlaybookManager:
    """Maintain an automatically generated playbook for adaptive strategy modes."""

    def __init__(
        self,
        state: Dict[str, Any],
        *,
        request_fn: Callable[[str, Dict[str, Any]], Optional[Dict[str, Any]]],
    ) -> None:
        self._root = state
        self._state = self._root.setdefault(
            "ai_playbook",
            {
                "active": {
                    "mode": "baseline",
                    "bias": "neutral",
                    "size_bias": {"BUY": 1.0, "SELL": 1.0},
                    "sl_bias": 1.0,
                    "tp_bias": 1.0,
                    "features": {},
                    "refreshed": 0.0,
                }
            },
        )
        self._request_fn = request_fn
        self._refresh_interval = 15 * 60

    def maybe_refresh(self, snapshot: Dict[str, Any]) -> None:
        active = self._state.get("active", {})
        now = time.time()
        last = float(active.get("refreshed", 0.0) or 0.0)
        if now - last < self._refresh_interval:
            return
        suggestions = self._request_fn("playbook", snapshot)
        if not suggestions:
            return
        active = self._normalize_playbook(suggestions, now)
        self._state["active"] = active
        self._root["ai_playbook"] = self._state

    def active(self) -> Dict[str, Any]:
        return dict(self._state.get("active", {}))

    def inject_context(self, ctx: Dict[str, Any]) -> None:
        active = self.active()
        features = active.get("features", {})
        if isinstance(features, dict):
            for key, value in features.items():
                ctx[key] = float(value)
        ctx["playbook_mode"] = active.get("mode", "baseline")
        ctx["playbook_bias"] = active.get("bias", "neutral")
        ctx["playbook_size_bias"] = float(
            (active.get("size_bias", {}) or {}).get(str(ctx.get("side") or "").upper(), 1.0)
        )

    def _normalize_playbook(self, payload: Dict[str, Any], now: float) -> Dict[str, Any]:
        mode = str(payload.get("mode") or payload.get("regime") or "baseline")
        bias = str(payload.get("bias") or "neutral")
        size_bias = payload.get("size_bias") or {}
        if not isinstance(size_bias, dict):
            size_bias = {"BUY": 1.0, "SELL": 1.0}
        normalized_size = {
            "BUY": float(max(0.4, min(2.5, float(size_bias.get("BUY", 1.0) or 1.0)))),
            "SELL": float(max(0.4, min(2.5, float(size_bias.get("SELL", 1.0) or 1.0)))),
        }
        features = payload.get("features") or {}
        normalized_features: Dict[str, float] = {}
        if isinstance(features, dict):
            for key, value in features.items():
                try:
                    normalized_features[str(key)] = float(value)
                except (TypeError, ValueError):
                    continue
        notes = payload.get("note") or payload.get("notes")
        if isinstance(notes, list):
            notes = "; ".join(str(n) for n in notes)
        active = {
            "mode": mode,
            "bias": bias,
            "size_bias": normalized_size,
            "sl_bias": float(max(0.4, min(2.5, float(payload.get("sl_bias", 1.0) or 1.0)))),
            "tp_bias": float(max(0.6, min(3.0, float(payload.get("tp_bias", 1.0) or 1.0)))),
            "features": normalized_features,
            "notes": notes if isinstance(notes, str) else "",
            "refreshed": now,
        }
        return active


class BudgetLearner:
    """Learn per-symbol AI budget biases from realised performance."""

    def __init__(self, state: Dict[str, Any]):
        self._root = state
        self._state = self._root.setdefault(
            "ai_budget_learning",
            {"symbols": {}, "usage": []},
        )
        self._cost_window = 50
        self._min_samples = 4

    def record_cost(self, kind: str, cost: float, meta: Optional[Dict[str, Any]] = None) -> None:
        symbol = None
        if meta:
            symbol = meta.get("symbol")
        entry = {
            "ts": time.time(),
            "kind": kind,
            "cost": float(cost),
            "symbol": symbol,
        }
        usage: List[Dict[str, Any]] = self._state.setdefault("usage", [])
        usage.append(entry)
        if len(usage) > self._cost_window:
            del usage[: len(usage) - self._cost_window]

    def record_trade(self, trade: Dict[str, Any]) -> None:
        symbol = trade.get("symbol") or "*"
        pnl_r = float(trade.get("pnl_r", 0.0) or 0.0)
        sym_state = self._state.setdefault("symbols", {}).setdefault(
            symbol,
            {"count": 0, "reward": 0.0, "cost": 0.0, "bias": 1.0, "updated": 0.0},
        )
        sym_state["count"] = int(sym_state.get("count", 0)) + 1
        sym_state["reward"] = float(sym_state.get("reward", 0.0) or 0.0) + pnl_r
        sym_state["updated"] = time.time()
        sym_state["bias"] = self._compute_bias(sym_state)
        self._state.setdefault("symbols", {})[symbol] = sym_state

    def should_allocate(self, symbol: str, kind: str) -> bool:
        if not symbol:
            return True
        sym_state = self._state.get("symbols", {}).get(symbol)
        if not sym_state or sym_state.get("count", 0) < self._min_samples:
            return True
        bias = float(sym_state.get("bias", 1.0) or 1.0)
        if bias >= 0.5:
            return True
        if kind == "postmortem":
            return bias >= 0.2
        return bias >= 0.35

    def context_bias(self, symbol: str) -> float:
        sym_state = self._state.get("symbols", {}).get(symbol)
        if not sym_state:
            return 1.0
        return float(sym_state.get("bias", 1.0) or 1.0)

    def _compute_bias(self, sym_state: Dict[str, Any]) -> float:
        reward = float(sym_state.get("reward", 0.0) or 0.0)
        count = max(1, int(sym_state.get("count", 0) or 0))
        avg = reward / count
        bias = 1.0 + avg * 0.25
        return max(0.1, min(1.6, bias))
