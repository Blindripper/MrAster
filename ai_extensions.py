"""AI-driven learning helpers for MrAster bot."""
from __future__ import annotations

import os
from datetime import datetime
import re
import time
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple

_ACTION_FOCUS_STOPWORDS: Set[str] = {
    "and",
    "are",
    "both",
    "but",
    "either",
    "for",
    "from",
    "into",
    "just",
    "keep",
    "like",
    "make",
    "must",
    "need",
    "not",
    "only",
    "our",
    "out",
    "should",
    "such",
    "than",
    "that",
    "the",
    "their",
    "them",
    "then",
    "there",
    "these",
    "they",
    "this",
    "those",
    "through",
    "to",
    "too",
    "toward",
    "towards",
    "very",
    "was",
    "were",
    "while",
    "with",
}

_ACTION_FOCUS_PRIORITY_TERMS: Set[str] = {
    "adjust",
    "avoid",
    "bias",
    "breadth",
    "buy",
    "capture",
    "cut",
    "defend",
    "diversify",
    "expand",
    "exposure",
    "focus",
    "hedge",
    "increase",
    "limit",
    "long",
    "monitor",
    "momentum",
    "neutral",
    "overweight",
    "protect",
    "reduce",
    "risk",
    "sell",
    "short",
    "size",
    "sl",
    "tighten",
    "tp",
    "trim",
    "volatility",
    "warning",
}

_ACTION_FOCUS_PATTERN = re.compile(r"[A-Za-z0-9_%]+")

_FOCUS_SIDE_KEYWORDS: Dict[str, float] = {
    "buy": 1.0,
    "long": 0.9,
    "overweight": 0.8,
    "accumulate": 0.7,
    "expand": 0.6,
    "increase": 0.6,
    "add": 0.5,
    "sell": -1.0,
    "short": -1.0,
    "reduce": -0.7,
    "trim": -0.7,
    "cut": -0.7,
    "hedge": -0.5,
    "defend": -0.4,
    "protect": -0.4,
}

_FOCUS_RISK_KEYWORDS: Dict[str, float] = {
    "reduce": 0.7,
    "trim": 0.6,
    "tighten": 0.65,
    "hedge": 0.6,
    "protect": 0.65,
    "defend": 0.55,
    "avoid": 0.75,
    "block": 0.8,
    "warning": 0.7,
    "risk": 0.55,
    "monitor": 0.35,
    "limit": 0.45,
    "cap": 0.45,
    "no": 0.4,
    "halt": 0.85,
    "increase": -0.45,
    "expand": -0.4,
    "add": -0.35,
    "aggressive": -0.5,
}

_RISK_CONTROL_KEYWORDS: Dict[str, float] = {
    "avoid": 0.75,
    "block": 0.8,
    "cap": 0.5,
    "limit": 0.45,
    "reduce": 0.7,
    "trim": 0.6,
    "tighten": 0.6,
    "hedge": 0.55,
    "protect": 0.6,
    "defend": 0.55,
    "monitor": 0.35,
    "warning": 0.7,
    "risk": 0.55,
    "stop": 0.5,
    "suspend": 0.75,
    "halt": 0.85,
    "aggressive": -0.5,
    "increase": -0.45,
    "expand": -0.4,
    "accelerate": -0.45,
    "add": -0.35,
}

_FOCUS_FEATURE_BASE_TERMS: Set[str] = {
    "adx",
    "atr",
    "trend",
    "range",
    "breadth",
    "hype",
    "volatility",
    "momentum",
    "liquidity",
    "event",
    "risk",
    "spread",
    "rsi",
    "stoch",
    "ema",
}


def _extract_action_focus_terms(texts: Iterable[Optional[str]], *, limit: int = 6) -> List[str]:
    """Distill playbook action prose into a compact set of focus tokens."""

    priority: List[str] = []
    special: List[str] = []
    regular: List[str] = []
    seen: Set[str] = set()

    def _append(bucket: List[str], token: str) -> None:
        if token not in seen:
            bucket.append(token)
            seen.add(token)

    for text in texts:
        if not isinstance(text, str):
            continue
        for raw_token in _ACTION_FOCUS_PATTERN.findall(text.lower()):
            if len(raw_token) < 3:
                continue
            if raw_token in _ACTION_FOCUS_STOPWORDS:
                continue
            if raw_token.endswith("ly") and raw_token not in {"only", "early"}:
                base = raw_token[:-2]
                if len(base) >= 3:
                    raw_token = base
            bucket = regular
            if raw_token in _ACTION_FOCUS_PRIORITY_TERMS:
                bucket = priority
            elif any(ch.isdigit() for ch in raw_token) or "_" in raw_token:
                bucket = special
            _append(bucket, raw_token)

    combined = priority + special + regular
    return combined[:limit]


POSTMORTEM_FEATURE_MAP: Dict[str, str] = {
    "trend_break": "pm_trend_break",
    "news_driver": "pm_news_driver",
    "liquidity_gap": "pm_liquidity_gap",
    "execution_delay": "pm_execution_delay",
    "sentiment_conflict": "pm_sentiment_conflict",
    "macro_event": "pm_macro_event",
    # Extended quantitative feedback from postmortem summaries
    "trend": "pm_trend_bias",
    "adx": "pm_adx_bias",
    "ema_slope": "pm_ema_slope",
    "volatility": "pm_volatility_bias",
    "event_risk": "pm_event_risk",
    "hype_score": "pm_hype_bias",
    "spread": "pm_spread_bias",
    "liquidity": "pm_liquidity_profile",
    "execution": "pm_execution_quality",
}
POSTMORTEM_EXTRA_FEATURES = (
    "pm_volatility_bias",
    "pm_execution_quality",
    "pm_liquidity_profile",
    "pm_event_risk",
    "pm_hype_bias",
    "pm_trend_bias",
    "pm_adx_bias",
    "pm_ema_slope",
    "pm_spread_bias",
)
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
        for key in POSTMORTEM_FEATURE_MAP.values():
            yield key
        for extra in POSTMORTEM_EXTRA_FEATURES:
            yield extra

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
        for extra_key in POSTMORTEM_EXTRA_FEATURES:
            if extra_key not in scores:
                continue
            try:
                value = float(scores.get(extra_key, 0.0) or 0.0)
            except (TypeError, ValueError):
                continue
            result[extra_key] = max(min(value, 1.0), -1.0)
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
        self._min_trades = 4
        self._ai_interval = 5 * 60
        self._history_cap = 220

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
        if not isinstance(ctx, dict):
            return
        overrides = self.overrides()
        confidence = float(overrides.get("confidence", 0.0)) if overrides else 0.0
        risk_bias = float(overrides.get("sl_atr_mult", 1.0)) if overrides else 1.0
        size_global = float(overrides.get("size_bias_global", 1.0)) if overrides else 1.0
        ctx["tuning_confidence"] = confidence
        ctx["tuning_risk_bias"] = risk_bias
        ctx["tuning_size_bias"] = size_global
        ctx["tuning_size_bias_global"] = size_global
        size_map = overrides.get("size_bias") if isinstance(overrides.get("size_bias"), dict) else {}
        if size_map:
            for bucket, value in size_map.items():
                try:
                    ctx[f"tuning_size_bias_{str(bucket).lower()}"] = float(value)
                except (TypeError, ValueError):
                    continue
        ctx["tuning_active"] = 1.0 if overrides else 0.0

    def _recompute_local_overrides(self) -> None:
        history: List[Dict[str, Any]] = self._state.get("history", [])
        if not history:
            return
        bucket_perf: Dict[str, List[float]] = {"S": [], "M": [], "L": []}
        wins: List[float] = []
        losses: List[float] = []
        recent_history = history[-90:]
        for item in recent_history:
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
        avg_win = _avg(wins)
        avg_loss = _avg(losses)
        loss_mag = abs(avg_loss)
        recent_avg = _avg([float(item.get("pnl_r", 0.0) or 0.0) for item in recent_history])
        risk_throttle = 1.0
        if recent_history:
            if recent_avg < 0:
                risk_throttle = max(0.35, min(0.95, 1.0 + recent_avg * 0.9))
            else:
                gain = min(recent_avg, 1.0)
                risk_throttle = min(1.2, 1.0 + gain * 0.4)
        if losses and wins:
            if loss_mag > 0 and avg_win > 0:
                ratio = avg_win / loss_mag
                if ratio < 1.0:
                    risk_throttle = min(risk_throttle, max(0.45, 0.82 + ratio * 0.08))
        elif losses and not wins:
            risk_throttle = min(risk_throttle, 0.5)
        for bucket, values in bucket_perf.items():
            avg = _avg(values)
            base = float(max(0.6, min(1.8, 1.0 + avg * 0.15)))
            tuned = base * risk_throttle
            overrides["size_bias"][bucket] = float(max(0.4, min(1.8, tuned)))
        if wins or losses:
            sl_bias = 1.0
            if losses:
                sl_bias = 1.0 - max(0.0, loss_mag - 0.7) * 0.18
            sl_bias = max(0.6, min(1.15, sl_bias))
            tp_bias = 1.0
            if wins:
                tp_bias = 1.0 + max(0.0, avg_win - 0.6) * 0.12
            tp_bias = max(0.9, min(2.4, tp_bias))
            if tp_bias < sl_bias * 1.15:
                tp_bias = min(2.4, sl_bias * 1.15)
            overrides["sl_atr_mult"] = sl_bias
            overrides["tp_atr_mult"] = tp_bias
        overrides["size_bias_global"] = float(
            sum(overrides["size_bias"].values()) / max(len(overrides["size_bias"]) or 1, 1)
        )
        if risk_throttle < 1.0:
            overrides["size_bias_global"] = max(
                0.4,
                min(1.5, overrides["size_bias_global"] * risk_throttle),
            )
        overrides.setdefault("confidence", min(1.0, len(history) / 40.0))
        self._state["overrides"] = overrides
        self._root["tuning_overrides"] = overrides

    def _maybe_request_ai(self) -> None:
        history: List[Dict[str, Any]] = self._state.get("history", [])
        if len(history) < self._min_trades:
            return
        now = time.time()
        if now - float(self._state.get("last_ai", 0.0) or 0.0) < self._ai_interval:
            return
        context = self._build_context_snapshot()
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
        if context:
            payload["context"] = context
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

    def _build_context_snapshot(self) -> Dict[str, Any]:
        snapshot: Dict[str, Any] = {}
        root_playbook = (
            self._root.get("ai_playbook", {}) if isinstance(self._root, dict) else {}
        )
        active_playbook = (
            root_playbook.get("active")
            if isinstance(root_playbook, dict)
            else None
        )
        if isinstance(active_playbook, dict) and active_playbook:
            snapshot["playbook_mode"] = active_playbook.get("mode")
            snapshot["playbook_bias"] = active_playbook.get("bias")
            try:
                snapshot["playbook_sl_bias"] = float(
                    active_playbook.get("sl_bias", 1.0) or 1.0
                )
            except (TypeError, ValueError):
                pass
            try:
                snapshot["playbook_tp_bias"] = float(
                    active_playbook.get("tp_bias", 1.0) or 1.0
                )
            except (TypeError, ValueError):
                pass
            try:
                snapshot["playbook_risk_bias"] = float(
                    active_playbook.get("risk_bias", 1.0) or 1.0
                )
            except (TypeError, ValueError):
                pass
            size_bias = active_playbook.get("size_bias")
            if isinstance(size_bias, dict):
                for key, value in size_bias.items():
                    try:
                        snapshot[f"playbook_size_{str(key).lower()}"] = float(value)
                    except (TypeError, ValueError):
                        continue
        sentinel_state = (
            self._root.get("sentinel") if isinstance(self._root, dict) else None
        )
        if isinstance(sentinel_state, dict) and sentinel_state:
            counts: Dict[str, int] = {}
            max_event: float = 0.0
            max_symbol: Optional[str] = None
            avg_hype_total = 0.0
            hype_count = 0
            for symbol, payload in sentinel_state.items():
                if not isinstance(payload, dict):
                    continue
                label = str(payload.get("label", "")).lower()
                counts[label] = counts.get(label, 0) + 1
                try:
                    event_risk = float(payload.get("event_risk", 0.0) or 0.0)
                except (TypeError, ValueError):
                    event_risk = 0.0
                if event_risk > max_event:
                    max_event = event_risk
                    max_symbol = symbol
                try:
                    hype = float(payload.get("hype_score", 0.0) or 0.0)
                except (TypeError, ValueError):
                    hype = None
                if hype is not None:
                    avg_hype_total += hype
                    hype_count += 1
            for label, count in counts.items():
                snapshot[f"sentinel_{label}_count"] = count
            if max_symbol:
                snapshot["sentinel_peak_symbol"] = max_symbol
                snapshot["sentinel_peak_event_risk"] = round(max_event, 3)
            if hype_count:
                snapshot["sentinel_avg_hype"] = round(avg_hype_total / hype_count, 3)
        budget_info = (
            self._root.get("ai_budget") if isinstance(self._root, dict) else None
        )
        if isinstance(budget_info, dict) and budget_info:
            for key in ("spent", "limit", "remaining"):
                try:
                    value = float(budget_info.get(key, 0.0) or 0.0)
                except (TypeError, ValueError):
                    continue
                snapshot[f"budget_{key}"] = value
            try:
                snapshot["budget_count"] = int(budget_info.get("count", 0) or 0)
            except (TypeError, ValueError):
                pass
        recent_notes = self._state.get("ai_notes")
        if isinstance(recent_notes, str) and recent_notes.strip():
            snapshot["latest_note"] = recent_notes.strip()
        overrides = self._state.get("overrides")
        if isinstance(overrides, dict) and overrides:
            snapshot["current_overrides"] = overrides
        return snapshot


class PlaybookManager:
    """Maintain an automatically generated playbook for adaptive strategy modes."""

    _SYMBOL_PATTERN = re.compile(r"\b[A-Z0-9]{3,}(?:USDT|USDC|USD|EUR|GBP|BTC|ETH|TRY|JPY|PERP)?\b")
    _FEATURE_SLUG_PATTERN = re.compile(r"[^a-z0-9_]+")
    _BLOCK_KEYWORDS = (
        "halt",
        "suspend",
        "block",
        "forbid",
        "prohibit",
        "do not trade",
        "no trade",
        "stop trading",
    )
    _AVOID_KEYWORDS = (
        "avoid",
        "stay away",
        "no exposure",
        "skip",
        "stand aside",
    )
    _WARNING_KEYWORDS = (
        "warning",
        "caution",
        "risk",
        "drawdown",
        "selloff",
        "sell-off",
        "drop",
        "decline",
        "volatility",
        "pressure",
        "elevated",
        "fragile",
        "stress",
    )
    _POSITIVE_KEYWORDS = (
        "focus",
        "favour",
        "favor",
        "opportunity",
        "support",
        "bullish",
        "strong",
        "momentum",
        "accumulate",
    )
    _DIRECTIVE_LEVEL = {
        "block": 3.0,
        "avoid": 2.6,
        "warning": 1.8,
        "caution": 1.6,
        "monitor": 1.2,
        "focus": -0.8,
        "positive": -0.6,
        "mention": 0.2,
        "neutral": 0.0,
    }
    _STRUCTURED_EFFECTS = {
        "size_multiplier",
        "size_cap",
        "size_floor",
        "sl_multiplier",
        "tp_multiplier",
        "hard_block",
    }
    _STRUCTURED_SCOPE = {"BUY", "SELL", "ANY"}
    _STRUCTURED_METRIC_KEYS = {
        "event_risk": ("sentinel_event_risk", "playbook_feature_event_risk", "event_risk", "pm_event_risk"),
        "hype": ("sentinel_hype", "playbook_feature_hype", "hype", "pm_hype_bias"),
        "volatility": ("atr_pct", "playbook_feature_volatility", "pm_volatility_bias"),
        "breadth": ("breadth", "playbook_feature_breadth"),
        "trend_strength": ("trend", "regime_slope", "playbook_feature_trend", "pm_trend_bias"),
    }

    STRUCTURED_EVENT_BLOCK_MIN = float(
        os.getenv("ASTER_STRUCTURED_EVENT_BLOCK_MIN", "0.4") or 0.0
    )
    _RISK_KEYWORD_TILTS = {
        "cautious": -0.25,
        "defensive": -0.3,
        "protective": -0.24,
        "conservative": -0.28,
        "shielded": -0.22,
        "balanced": 0.0,
        "neutral": 0.0,
        "calm": -0.12,
        "guarded": -0.2,
        "risk_off": -0.34,
        "risk-off": -0.34,
        "riskoff": -0.34,
        "defensive_bias": -0.28,
        "opportunistic": 0.14,
        "constructive": 0.08,
        "expansionary": 0.18,
        "aggressive": 0.3,
        "offensive": 0.24,
        "risk_on": 0.26,
        "risk-on": 0.26,
        "riskon": 0.26,
        "bullish": 0.22,
        "bearish": -0.22,
        "proactive": 0.12,
    }

    def __init__(
        self,
        state: Dict[str, Any],
        *,
        request_fn: Callable[[str, Dict[str, Any]], Optional[Dict[str, Any]]],
        event_cb: Optional[
            Callable[[str, Dict[str, Any], Optional[Dict[str, Any]]], None]
        ] = None,
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
        self._refresh_interval = 60 * 60
        self._bootstrap_pending = True
        self._bootstrap_deadline = time.time() + 120.0
        self._bootstrap_retry = 90.0
        self._bootstrap_cooldown_until = 0.0
        self._event_cb = event_cb

    @staticmethod
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

    @classmethod
    def _normalize_feature_key(cls, key: Any) -> Optional[str]:
        if key is None:
            return None
        if isinstance(key, str):
            token = key.strip().lower()
        else:
            token = str(key).strip().lower()
        if not token:
            return None
        token = token.replace("/", " ").replace("-", " ")
        slug = cls._FEATURE_SLUG_PATTERN.sub("_", token)
        slug = slug.strip("_")
        if not slug:
            return None
        while "__" in slug:
            slug = slug.replace("__", "_")
        return slug

    @classmethod
    def _normalize_string_list(
        cls, raw: Any, *, limit: int = 6
    ) -> List[str]:
        values: List[str] = []
        if isinstance(raw, list):
            for item in raw:
                text = cls._clean_string(item)
                if text:
                    values.append(text)
                if len(values) >= limit:
                    break
        else:
            text = cls._clean_string(raw)
            if text:
                values.append(text)
        return values

    @classmethod
    def _normalize_structured_condition(cls, raw: Any) -> Optional[Dict[str, Any]]:
        if not isinstance(raw, dict):
            return None
        metric = cls._clean_string(raw.get("metric"))
        if not metric:
            return None
        metric_key = metric.lower().replace(" ", "_")
        if metric_key not in cls._STRUCTURED_METRIC_KEYS:
            return None
        operator = cls._clean_string(raw.get("operator")) or ">"
        operator = operator.lower()
        if operator not in {">", ">=", "<", "<=", "between"}:
            return None
        value = raw.get("value")
        try:
            if value is None and operator == "between":
                value = raw.get("min")
            numeric = float(value)
        except (TypeError, ValueError):
            return None
        condition: Dict[str, Any] = {"metric": metric_key, "operator": operator, "value": float(numeric)}
        if operator == "between":
            upper = raw.get("value2", raw.get("max"))
            try:
                if upper is not None:
                    condition["value2"] = float(upper)
            except (TypeError, ValueError):
                return None
        return condition

    @classmethod
    def _normalize_structured_entry(cls, raw: Any) -> Optional[Dict[str, Any]]:
        if not isinstance(raw, dict):
            return None
        effect = cls._clean_string(raw.get("effect"))
        if not effect:
            return None
        effect_key = effect.lower().replace(" ", "_")
        if effect_key not in cls._STRUCTURED_EFFECTS:
            return None
        entry: Dict[str, Any] = {"effect": effect_key}
        identifier = cls._clean_string(raw.get("id") or raw.get("name") or effect_key)
        if identifier:
            entry["id"] = identifier
        multiplier = raw.get("multiplier") or raw.get("value")
        if multiplier is not None:
            try:
                entry["multiplier"] = float(multiplier)
            except (TypeError, ValueError):
                pass
        scope = cls._clean_string(raw.get("scope") or raw.get("side") or "ANY")
        if scope:
            scope_token = scope.upper()
            if scope_token in cls._STRUCTURED_SCOPE:
                entry["scope"] = scope_token
        condition = cls._normalize_structured_condition(raw.get("condition"))
        if condition:
            entry["condition"] = condition
        note = cls._clean_string(raw.get("note") or raw.get("detail"))
        if note:
            entry["note"] = note
        return entry

    @classmethod
    def _parse_structured_entries(
        cls, raw: Any, *, limit: int = 8
    ) -> List[Dict[str, Any]]:
        entries: List[Dict[str, Any]] = []
        if not isinstance(raw, list):
            return entries
        for item in raw:
            entry = cls._normalize_structured_entry(item)
            if entry:
                entries.append(entry)
            if len(entries) >= limit:
                break
        return entries

    @classmethod
    def _risk_adjustments_from_text(cls, raw: Any) -> List[float]:
        text = cls._clean_string(raw)
        if not text:
            return []
        lowered = text.lower()
        adjustments: List[float] = []
        for key, tilt in cls._RISK_KEYWORD_TILTS.items():
            if key and key in lowered:
                adjustments.append(float(tilt))
        return adjustments

    @classmethod
    def _derive_focus_hints(
        cls,
        focus_terms: Iterable[str],
        risk_controls: Iterable[str],
    ) -> Tuple[float, float, Dict[str, float]]:
        side_samples: List[float] = []
        risk_samples: List[float] = []
        feature_bias: Dict[str, float] = {}

        def _maybe_record_feature(token: str, weight: float) -> None:
            slug = cls._normalize_feature_key(token)
            if not slug or slug in feature_bias:
                return
            include = False
            if "_" in token or any(ch.isdigit() for ch in token):
                include = True
            else:
                base = slug.split("_", 1)[0]
                if base in _FOCUS_FEATURE_BASE_TERMS:
                    include = True
            if not include:
                return
            feature_bias[slug] = float(max(-1.0, min(1.0, weight if weight else 1.0)))

        def _ingest(token: str, *, from_risk: bool = False) -> None:
            if not token:
                return
            if token in _ACTION_FOCUS_STOPWORDS:
                return
            side_weight = _FOCUS_SIDE_KEYWORDS.get(token)
            if side_weight is not None:
                side_samples.append(float(side_weight))
            risk_weight = _FOCUS_RISK_KEYWORDS.get(token)
            if risk_weight is not None:
                risk_samples.append(float(risk_weight))
            rc_weight = None
            if from_risk:
                rc_weight = _RISK_CONTROL_KEYWORDS.get(token)
                if rc_weight is not None:
                    risk_samples.append(float(rc_weight))
            weight = 0.0
            if risk_weight is not None:
                weight = float(risk_weight)
            elif side_weight is not None:
                weight = float(side_weight)
            elif rc_weight is not None:
                weight = float(rc_weight)
            _maybe_record_feature(token, weight)

        for term in focus_terms or ():
            if not isinstance(term, str):
                continue
            token = term.strip().lower()
            if not token:
                continue
            _ingest(token)

        for entry in risk_controls or ():
            if not isinstance(entry, str):
                continue
            for raw in _ACTION_FOCUS_PATTERN.findall(entry.lower()):
                if len(raw) < 3:
                    continue
                _ingest(raw, from_risk=True)

        if side_samples:
            side_bias = float(max(-1.0, min(1.0, sum(side_samples) / len(side_samples))))
        else:
            side_bias = 0.0
        if risk_samples:
            risk_bias = float(max(-1.0, min(1.0, sum(risk_samples) / len(risk_samples))))
        else:
            risk_bias = 0.0
        return side_bias, risk_bias, feature_bias

    @classmethod
    def _derive_risk_bias(
        cls, payload: Dict[str, Any], *, default: float = 1.0
    ) -> float:
        adjustments: List[float] = []
        adjustments.extend(
            cls._risk_adjustments_from_text(
                payload.get("mode") or payload.get("regime")
            )
        )
        adjustments.extend(cls._risk_adjustments_from_text(payload.get("bias")))
        if adjustments:
            base_tilt = sum(adjustments) / max(len(adjustments), 1)
        else:
            base_tilt = 0.0
        conf_adjust = 0.0
        try:
            confidence = payload.get("confidence")
            if confidence is not None:
                conf = max(0.0, min(1.0, float(confidence)))
                conf_adjust = (conf - 0.5) * 0.4
        except (TypeError, ValueError):
            conf_adjust = 0.0
        total_tilt = base_tilt + conf_adjust
        return float(max(0.55, min(1.45, default + total_tilt)))

    @classmethod
    def _normalize_strategy(cls, payload: Any) -> Optional[Dict[str, Any]]:
        if not isinstance(payload, dict):
            return None

        strategy: Dict[str, Any] = {}
        name = cls._clean_string(payload.get("name"))
        if name:
            strategy["name"] = name

        objective = cls._clean_string(payload.get("objective") or payload.get("goal"))
        if objective:
            strategy["objective"] = objective

        why_active = cls._clean_string(
            payload.get("why_active")
            or payload.get("rationale")
            or payload.get("justification")
        )
        if why_active:
            strategy["why_active"] = why_active

        signals = cls._normalize_string_list(
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
                    title = cls._clean_string(
                        item.get("title")
                        or item.get("name")
                        or item.get("step")
                    )
                    detail = cls._clean_string(
                        item.get("detail")
                        or item.get("instruction")
                        or item.get("action")
                    )
                    trigger = cls._clean_string(
                        item.get("trigger") or item.get("condition")
                    )
                else:
                    detail = cls._clean_string(item)
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
                detail = cls._clean_string(value)
                if not detail:
                    continue
                action_entry = {
                    "title": cls._clean_string(key) or f"Step {len(actions) + 1}",
                    "detail": detail,
                }
                actions.append(action_entry)
                if len(actions) >= 6:
                    break
        if actions:
            strategy["actions"] = actions

        risk_controls = cls._normalize_string_list(
            payload.get("risk_controls") or payload.get("risk_management")
        )
        if risk_controls:
            strategy["risk_controls"] = risk_controls[:6]

        structured_actions = cls._parse_structured_entries(
            payload.get("actions_structured") or []
        )
        if structured_actions:
            strategy["actions_structured"] = structured_actions

        structured_risk = cls._parse_structured_entries(
            payload.get("risk_controls_structured") or []
        )
        if structured_risk:
            strategy["risk_controls_structured"] = structured_risk

        return strategy or None

    def maybe_refresh(self, snapshot: Dict[str, Any]) -> None:
        active = self._state.get("active", {})
        now = time.time()
        last_raw = active.get("refreshed", 0.0)
        last = self._parse_timestamp(last_raw)
        if isinstance(active, dict) and last == 0.0 and last_raw not in (0, 0.0, None):
            active["refreshed"] = 0.0
        bootstrap_triggered = False
        if self._bootstrap_pending:
            if now < self._bootstrap_cooldown_until:
                return
            ready = self._snapshot_ready(snapshot)
            if not ready and last <= 0.0 and isinstance(snapshot, dict) and snapshot:
                # brand-new state: accept any non-empty snapshot payload to avoid stalling
                ready = True
            if ready or now >= self._bootstrap_deadline:
                bootstrap_triggered = True
            else:
                return
        if not bootstrap_triggered and now - last < self._refresh_interval:
            return
        suggestions = self._request_fn("playbook", snapshot)
        if not suggestions:
            if bootstrap_triggered:
                # retry once we either have data or hit the next deadline
                self._bootstrap_cooldown_until = time.time() + self._bootstrap_retry
                if self._bootstrap_deadline < self._bootstrap_cooldown_until:
                    self._bootstrap_deadline = self._bootstrap_cooldown_until
            return
        active = self._normalize_playbook(suggestions, now)
        self._state["active"] = active
        self._root["ai_playbook"] = self._state
        if bootstrap_triggered:
            self._bootstrap_pending = False
            self._bootstrap_cooldown_until = 0.0
        if self._event_cb:
            try:
                context = {"raw": suggestions, "snapshot": snapshot}
                self._event_cb("applied", dict(active), context)
            except Exception:
                pass

    def _snapshot_ready(self, snapshot: Dict[str, Any]) -> bool:
        if not isinstance(snapshot, dict):
            return False
        if snapshot.get("technical"):
            return True
        if snapshot.get("sentinel"):
            return True
        budget = snapshot.get("budget")
        if isinstance(budget, dict) and budget:
            return True
        overview = snapshot.get("market_overview")
        if isinstance(overview, dict) and overview:
            return True
        return False

    def active(self) -> Dict[str, Any]:
        return dict(self._state.get("active", {}))

    @staticmethod
    def _parse_timestamp(value: Any) -> float:
        if isinstance(value, (int, float)):
            try:
                return float(value)
            except (TypeError, ValueError):
                return 0.0
        if isinstance(value, str):
            token = value.strip()
            if not token:
                return 0.0
            try:
                cleaned = token.replace("Z", "+00:00") if token.endswith("Z") else token
                return datetime.fromisoformat(cleaned).timestamp()
            except Exception:
                try:
                    return float(token)
                except (TypeError, ValueError):
                    return 0.0
        return 0.0

    def inject_context(self, ctx: Dict[str, Any]) -> None:
        active = self.active()
        features = active.get("features", {})
        feature_aliases = active.get("feature_aliases", {})
        raw_features: Dict[str, float] = {}
        slugged_features: Dict[str, float] = {}
        if isinstance(features, dict):
            for key, value in features.items():
                try:
                    numeric = float(value)
                except (TypeError, ValueError):
                    continue
                key_str = str(key)
                raw_features[key_str] = numeric
                ctx[key_str] = numeric
                alias = self._normalize_feature_key(key_str)
                if alias:
                    slugged_features[alias] = numeric
        if isinstance(feature_aliases, dict):
            for alias, value in feature_aliases.items():
                try:
                    numeric = float(value)
                except (TypeError, ValueError):
                    continue
                slug = self._normalize_feature_key(alias)
                if not slug:
                    continue
                slugged_features[slug] = numeric
        if raw_features:
            ctx["playbook_features_raw"] = dict(raw_features)
        if slugged_features:
            ctx["playbook_features"] = dict(slugged_features)
            for slug, numeric in slugged_features.items():
                pref_key = f"playbook_feature_{slug}"
                if pref_key not in ctx:
                    ctx[pref_key] = numeric
        ctx["playbook_mode"] = active.get("mode", "baseline")
        ctx["playbook_bias"] = active.get("bias", "neutral")
        size_bias_data = active.get("size_bias", {})
        size_bias = size_bias_data if isinstance(size_bias_data, dict) else {}
        try:
            buy_bias = float((size_bias or {}).get("BUY", 1.0) or 1.0)
        except (TypeError, ValueError):
            buy_bias = 1.0
        try:
            sell_bias = float((size_bias or {}).get("SELL", 1.0) or 1.0)
        except (TypeError, ValueError):
            sell_bias = 1.0
        ctx["playbook_size_bias_buy"] = buy_bias
        ctx["playbook_size_bias_sell"] = sell_bias
        ctx["playbook_size_bias_map"] = {"BUY": buy_bias, "SELL": sell_bias}
        side_token = str(ctx.get("side") or "").upper()
        side_bias = buy_bias if side_token == "BUY" else sell_bias if side_token == "SELL" else buy_bias
        ctx["playbook_size_bias"] = float((size_bias or {}).get(side_token, side_bias))
        try:
            ctx["playbook_sl_bias"] = float(active.get("sl_bias", 1.0) or 1.0)
        except (TypeError, ValueError):
            ctx["playbook_sl_bias"] = 1.0
        try:
            ctx["playbook_tp_bias"] = float(active.get("tp_bias", 1.0) or 1.0)
        except (TypeError, ValueError):
            ctx["playbook_tp_bias"] = 1.0
        try:
            ctx["playbook_risk_bias"] = float(active.get("risk_bias", 1.0) or 1.0)
        except (TypeError, ValueError):
            ctx["playbook_risk_bias"] = 1.0
        confidence = active.get("confidence")
        try:
            if confidence is not None:
                ctx["playbook_confidence"] = float(confidence)
        except (TypeError, ValueError):
            pass
        notes = active.get("notes")
        if isinstance(notes, str) and notes.strip():
            ctx["playbook_notes"] = notes.strip()
        request_id = active.get("request_id")
        if isinstance(request_id, str) and request_id.strip():
            ctx["playbook_request_id"] = request_id.strip()
        strategy = active.get("strategy")
        if isinstance(strategy, dict):
            name = strategy.get("name")
            objective = strategy.get("objective")
            reason = strategy.get("why_active")
            if name:
                ctx["playbook_strategy_name"] = str(name)
            if objective:
                ctx["playbook_strategy_objective"] = str(objective)
            if reason:
                ctx["playbook_strategy_reason"] = str(reason)
            signals = strategy.get("market_signals")
            sanitized_signals: List[str] = []
            if isinstance(signals, list):
                for signal in signals:
                    if isinstance(signal, str) and signal.strip():
                        sanitized_signals.append(signal.strip())
                for idx, signal in enumerate(sanitized_signals[:3], start=1):
                    ctx[f"playbook_signal_{idx}"] = signal
            if sanitized_signals:
                ctx["playbook_strategy_signals"] = sanitized_signals[:6]
            actions = strategy.get("actions")
            sanitized_actions: List[Dict[str, Any]] = []
            aggregated_terms: List[str] = []
            if isinstance(actions, list):
                for action in actions:
                    if not isinstance(action, dict):
                        continue
                    clean_action: Dict[str, Any] = {}
                    title = action.get("title")
                    detail = action.get("detail")
                    trigger = action.get("trigger")
                    if isinstance(title, str) and title.strip():
                        clean_action["title"] = title.strip()
                    if isinstance(detail, str) and detail.strip():
                        clean_action["detail"] = detail.strip()
                    if isinstance(trigger, str) and trigger.strip():
                        clean_action["trigger"] = trigger.strip()
                    focus_terms = _extract_action_focus_terms(
                        (title, detail, trigger)
                    )
                    if focus_terms:
                        clean_action["focus_terms"] = focus_terms
                    if clean_action:
                        sanitized_actions.append(clean_action)
                    if len(sanitized_actions) >= 6:
                        break
            if sanitized_actions:
                ctx["playbook_strategy_actions"] = sanitized_actions
                aggregated_seen: Set[str] = set()
                for idx, action in enumerate(sanitized_actions[:3], start=1):
                    base_key = f"playbook_action_{idx}"
                    title = action.get("title")
                    detail = action.get("detail")
                    trigger = action.get("trigger")
                    focus_terms = action.get("focus_terms")
                    if title:
                        ctx[f"{base_key}_title"] = title
                    if detail:
                        ctx[f"{base_key}_detail"] = detail
                    if trigger:
                        ctx[f"{base_key}_trigger"] = trigger
                    if focus_terms:
                        ctx[f"{base_key}_focus_terms"] = focus_terms
                for action in sanitized_actions:
                    for term in action.get("focus_terms", []):
                        if term not in aggregated_seen:
                            aggregated_terms.append(term)
                            aggregated_seen.add(term)
                if aggregated_terms:
                    ctx["playbook_action_focus_terms"] = aggregated_terms
            risk_controls = strategy.get("risk_controls") or strategy.get("risk_management")
            sanitized_rc: List[str] = []
            if isinstance(risk_controls, list):
                for entry in risk_controls:
                    if isinstance(entry, str) and entry.strip():
                        sanitized_rc.append(entry.strip())
                    if len(sanitized_rc) >= 6:
                        break
            if sanitized_rc:
                ctx["playbook_strategy_risk_controls"] = sanitized_rc
            focus_side_bias, focus_risk_bias, focus_features = self._derive_focus_hints(
                aggregated_terms,
                sanitized_rc,
            )
            if abs(focus_side_bias) >= 1e-6:
                ctx["playbook_focus_side_bias"] = focus_side_bias
            if abs(focus_risk_bias) >= 1e-6:
                ctx["playbook_focus_risk_bias"] = focus_risk_bias
            if focus_features:
                ctx["playbook_focus_features"] = dict(focus_features)
                for slug, weight in focus_features.items():
                    ctx.setdefault(f"playbook_focus_feature_{slug}", weight)
        structured_directives: List[Dict[str, Any]] = []
        actions_structured = active.get("structured_actions")
        if isinstance(actions_structured, list):
            structured_directives.extend(actions_structured)
        risk_structured = active.get("structured_risk_controls")
        if isinstance(risk_structured, list):
            structured_directives.extend(risk_structured)
        self._apply_structured_directives(ctx, structured_directives)
        symbol = str(ctx.get("symbol") or "").strip().upper()
        if symbol:
            directive = self.symbol_directive(symbol)
            if directive:
                ctx["playbook_symbol_directive"] = directive.get("label", "neutral")
                level = directive.get("level", directive.get("score", 0.0))
                try:
                    ctx["playbook_symbol_directive_level"] = float(level)
                except (TypeError, ValueError):
                    ctx["playbook_symbol_directive_level"] = 0.0
                drop_pct = directive.get("drop_pct")
                if isinstance(drop_pct, (int, float)):
                    ctx["playbook_symbol_drop_pct"] = float(drop_pct)
                note = directive.get("text") or directive.get("note")
                if isinstance(note, str) and note.strip():
                    ctx["playbook_symbol_note"] = note
                source = directive.get("source")
                if isinstance(source, str) and source.strip():
                    ctx["playbook_symbol_directive_source"] = source
                updated = directive.get("updated")
                if isinstance(updated, (int, float)):
                    ctx["playbook_symbol_directive_updated"] = float(updated)

    @classmethod
    def _resolve_metric_value(cls, ctx: Dict[str, Any], metric: str) -> Optional[float]:
        keys = cls._STRUCTURED_METRIC_KEYS.get(metric)
        if not keys:
            return None
        for key in keys:
            if key not in ctx:
                continue
            value = ctx.get(key)
            try:
                if value is None:
                    continue
                numeric = float(value)
            except (TypeError, ValueError):
                continue
            return numeric
        return None

    @classmethod
    def _condition_matches(
        cls, ctx: Dict[str, Any], condition: Optional[Dict[str, Any]]
    ) -> bool:
        if not condition:
            return True
        metric = condition.get("metric")
        if not metric:
            return False
        metric_value = cls._resolve_metric_value(ctx, metric)
        if metric_value is None:
            return False
        try:
            threshold = float(condition.get("value", 0.0))
        except (TypeError, ValueError):
            return False
        op = condition.get("operator") or ">"
        if op == ">":
            return metric_value > threshold
        if op == ">=":
            return metric_value >= threshold
        if op == "<":
            return metric_value < threshold
        if op == "<=":
            return metric_value <= threshold
        if op == "between":
            try:
                upper = float(condition.get("value2"))
            except (TypeError, ValueError):
                return False
            low = min(threshold, upper)
            high = max(threshold, upper)
            return low <= metric_value <= high
        return False

    def _apply_structured_directives(
        self, ctx: Dict[str, Any], directives: List[Dict[str, Any]]
    ) -> None:
        keys_to_reset = [
            "playbook_structured_size_multiplier",
            "playbook_structured_size_cap",
            "playbook_structured_size_floor",
            "playbook_structured_sl_multiplier",
            "playbook_structured_tp_multiplier",
            "playbook_structured_hard_block",
            "playbook_structured_block_reason",
            "playbook_structured_notes",
        ]
        if not directives:
            for key in keys_to_reset:
                ctx.pop(key, None)
            return

        size_mult = 1.0
        sl_mult = 1.0
        tp_mult = 1.0
        size_cap: Optional[float] = None
        size_floor: Optional[float] = None
        hard_block = False
        block_reason: Optional[str] = None
        notes: List[str] = []
        side = str(ctx.get("side") or "").upper() or "ANY"

        for entry in directives:
            effect = entry.get("effect")
            if effect not in self._STRUCTURED_EFFECTS:
                continue
            scope = entry.get("scope") or "ANY"
            if scope != "ANY" and scope != side:
                continue
            if not self._condition_matches(ctx, entry.get("condition")):
                continue
            note = entry.get("note") or entry.get("id")
            multiplier_raw = entry.get("multiplier")
            try:
                multiplier = float(multiplier_raw) if multiplier_raw is not None else 1.0
            except (TypeError, ValueError):
                multiplier = 1.0
            multiplier = float(max(0.05, min(4.0, multiplier)))
            if effect == "hard_block":
                condition = entry.get("condition")
                if (
                    self.STRUCTURED_EVENT_BLOCK_MIN > 0
                    and isinstance(condition, dict)
                ):
                    metric = condition.get("metric")
                    if metric == "event_risk":
                        current_event = self._resolve_metric_value(ctx, metric)
                        if (
                            current_event is not None
                            and current_event < self.STRUCTURED_EVENT_BLOCK_MIN
                        ):
                            if note:
                                notes.append(
                                    f"ignored block {note}: event_risk {current_event:.2f} < {self.STRUCTURED_EVENT_BLOCK_MIN:.2f}"
                                )
                            continue
                hard_block = True
                block_reason = note or block_reason or entry.get("effect")
                if note:
                    notes.append(note)
                continue
            if effect == "size_multiplier":
                size_mult *= multiplier
                if note:
                    notes.append(f"size×{multiplier:.2f}: {note}")
            elif effect == "size_cap":
                size_cap = multiplier if size_cap is None else min(size_cap, multiplier)
                if note:
                    notes.append(f"size≤{size_cap:.2f}: {note}")
            elif effect == "size_floor":
                size_floor = multiplier if size_floor is None else max(size_floor, multiplier)
                if note:
                    notes.append(f"size≥{size_floor:.2f}: {note}")
            elif effect == "sl_multiplier":
                sl_mult *= multiplier
                if note:
                    notes.append(f"SL×{multiplier:.2f}: {note}")
            elif effect == "tp_multiplier":
                tp_mult *= multiplier
                if note:
                    notes.append(f"TP×{multiplier:.2f}: {note}")

        if hard_block:
            ctx["playbook_structured_hard_block"] = True
            if block_reason or notes:
                reason = block_reason or "; ".join(notes)
                ctx["playbook_structured_block_reason"] = reason
        else:
            ctx.pop("playbook_structured_hard_block", None)
            ctx.pop("playbook_structured_block_reason", None)

        size_mult = float(max(0.1, min(3.5, size_mult)))
        sl_mult = float(max(0.3, min(3.5, sl_mult)))
        tp_mult = float(max(0.3, min(3.5, tp_mult)))

        if abs(size_mult - 1.0) > 1e-4:
            ctx["playbook_structured_size_multiplier"] = size_mult
        else:
            ctx.pop("playbook_structured_size_multiplier", None)
        if size_cap is not None:
            ctx["playbook_structured_size_cap"] = float(max(0.1, min(3.5, size_cap)))
        else:
            ctx.pop("playbook_structured_size_cap", None)
        if size_floor is not None:
            ctx["playbook_structured_size_floor"] = float(max(0.1, min(3.5, size_floor)))
        else:
            ctx.pop("playbook_structured_size_floor", None)
        if abs(sl_mult - 1.0) > 1e-4:
            ctx["playbook_structured_sl_multiplier"] = sl_mult
        else:
            ctx.pop("playbook_structured_sl_multiplier", None)
        if abs(tp_mult - 1.0) > 1e-4:
            ctx["playbook_structured_tp_multiplier"] = tp_mult
        else:
            ctx.pop("playbook_structured_tp_multiplier", None)
        if notes:
            ctx["playbook_structured_notes"] = notes[:8]
        else:
            ctx.pop("playbook_structured_notes", None)

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
        feature_aliases: Dict[str, float] = {}
        if isinstance(features, dict):
            for key, value in features.items():
                try:
                    numeric = float(value)
                except (TypeError, ValueError):
                    continue
                key_str = str(key)
                normalized_features[key_str] = numeric
                alias = self._normalize_feature_key(key_str)
                if alias:
                    feature_aliases[alias] = numeric
        notes = payload.get("note") or payload.get("notes")
        if isinstance(notes, list):
            notes = "; ".join(str(n) for n in notes)
        confidence = None
        try:
            if payload.get("confidence") is not None:
                confidence = max(0.0, min(1.0, float(payload.get("confidence"))))
        except (TypeError, ValueError):
            confidence = None

        strategy = self._normalize_strategy(payload.get("strategy"))
        reason_text = self._clean_string(
            payload.get("reason") or payload.get("rationale")
        )

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
        if feature_aliases:
            active["feature_aliases"] = feature_aliases
        active["risk_bias"] = self._derive_risk_bias(payload)
        if confidence is not None:
            active["confidence"] = confidence
        if reason_text:
            active["reason"] = reason_text
        if strategy:
            active["strategy"] = strategy
            if "reason" not in active and strategy.get("why_active"):
                active["reason"] = strategy["why_active"]
            structured_actions = strategy.get("actions_structured")
            if structured_actions:
                active["structured_actions"] = structured_actions
            structured_risk = strategy.get("risk_controls_structured")
            if structured_risk:
                active["structured_risk_controls"] = structured_risk
        request_id = payload.get("request_id")
        if isinstance(request_id, str):
            token = request_id.strip()
            if token:
                active["request_id"] = token
        symbol_directives = self._collect_symbol_directives(payload, now)
        if symbol_directives:
            active["symbol_directives"] = symbol_directives
        return active

    def _collect_symbol_directives(self, payload: Dict[str, Any], now: float) -> Dict[str, Any]:
        directives: Dict[str, Dict[str, Any]] = {}

        def register(text: Optional[str], source: str) -> None:
            cleaned = self._clean_string(text)
            if not cleaned:
                return
            matches = self._SYMBOL_PATTERN.findall(cleaned)
            if not matches:
                return
            lowered = cleaned.lower()
            label = "neutral"
            score = 0.0
            if any(keyword in lowered for keyword in self._BLOCK_KEYWORDS):
                label = "block"
                score = self._DIRECTIVE_LEVEL["block"]
            elif any(keyword in lowered for keyword in self._AVOID_KEYWORDS):
                label = "avoid"
                score = self._DIRECTIVE_LEVEL["avoid"]
            elif any(keyword in lowered for keyword in self._WARNING_KEYWORDS):
                label = "warning"
                score = self._DIRECTIVE_LEVEL["warning"]
            elif any(keyword in lowered for keyword in self._POSITIVE_KEYWORDS):
                label = "focus"
                score = self._DIRECTIVE_LEVEL["focus"]
            else:
                label = "mention"
                score = self._DIRECTIVE_LEVEL["mention"]
            drop_pct = None
            drop_match = re.search(r"(-?\d+(?:\.\d+)?)%\s*(?:drop|decline|sell[- ]?off|drawdown)", cleaned, flags=re.IGNORECASE)
            if drop_match:
                try:
                    drop_pct = abs(float(drop_match.group(1)))
                except (TypeError, ValueError):
                    drop_pct = None
                else:
                    if label == "mention" and drop_pct >= 4.0:
                        label = "warning"
                        score = max(score, self._DIRECTIVE_LEVEL["warning"])
            monitor_match = re.search(r"monitor|watch|observe", lowered)
            if label == "mention" and monitor_match:
                label = "monitor"
                score = self._DIRECTIVE_LEVEL["monitor"]
            level = self._DIRECTIVE_LEVEL.get(label, score)
            for raw_symbol in matches:
                symbol = raw_symbol.upper()
                entry = {
                    "label": label,
                    "level": level,
                    "score": score,
                    "text": cleaned,
                    "source": source,
                    "updated": float(now),
                }
                if drop_pct is not None:
                    entry["drop_pct"] = float(drop_pct)
                prev = directives.get(symbol)
                if prev:
                    prev_drop = prev.get("drop_pct")
                    if prev_drop is not None and "drop_pct" not in entry:
                        try:
                            entry["drop_pct"] = float(prev_drop)
                        except (TypeError, ValueError):
                            pass
                if not prev:
                    directives[symbol] = entry
                    continue
                prev_level = float(prev.get("level", prev.get("score", 0.0)) or 0.0)
                prev_abs = abs(prev_level)
                curr_abs = abs(level)
                if curr_abs > prev_abs or (curr_abs == prev_abs and level > prev_level):
                    prev_text = prev.get("text")
                    if isinstance(prev_text, str) and prev_text.strip() and prev_text.strip() not in entry["text"]:
                        entry["text"] = f"{prev_text.strip()} | {entry['text']}"
                    directives[symbol] = entry
                    continue
                if drop_pct is not None:
                    old_drop = prev.get("drop_pct")
                    if not isinstance(old_drop, (int, float)) or float(old_drop) < drop_pct:
                        prev["drop_pct"] = float(drop_pct)
                if cleaned and cleaned not in prev.get("text", ""):
                    prev_text = prev.get("text")
                    if isinstance(prev_text, str) and prev_text.strip():
                        prev["text"] = f"{prev_text} | {cleaned}"
                    else:
                        prev["text"] = cleaned

        strategy = payload.get("strategy")
        if isinstance(strategy, dict):
            register(strategy.get("why_active"), "strategy")
            signals = strategy.get("market_signals")
            if isinstance(signals, list):
                for item in signals:
                    register(item if isinstance(item, str) else None, "market_signal")
            actions = strategy.get("actions")
            if isinstance(actions, list):
                for entry in actions:
                    if isinstance(entry, dict):
                        register(entry.get("detail") or entry.get("title"), "strategy_action")
                    else:
                        register(str(entry), "strategy_action")
        risk_controls = payload.get("risk_controls")
        if isinstance(risk_controls, list):
            for item in risk_controls:
                register(item if isinstance(item, str) else None, "risk_control")
        top_signals = payload.get("market_signals")
        if isinstance(top_signals, list):
            for item in top_signals:
                register(item if isinstance(item, str) else None, "top_market_signal")
        notes = payload.get("notes")
        if isinstance(notes, list):
            for item in notes:
                register(item if isinstance(item, str) else None, "note")
        else:
            register(notes if isinstance(notes, str) else None, "note")
        actions = payload.get("actions")
        if isinstance(actions, list):
            for entry in actions:
                if isinstance(entry, dict):
                    register(entry.get("detail") or entry.get("title"), "action")
                else:
                    register(str(entry), "action")
        return directives

    def symbol_directive(self, symbol: str) -> Optional[Dict[str, Any]]:
        active = self.active()
        directives = active.get("symbol_directives")
        if not isinstance(directives, dict):
            return None
        key = str(symbol or "").strip().upper()
        if not key:
            return None
        entry = directives.get(key)
        if entry:
            return dict(entry)
        return None


class BudgetLearner:
    """Learn per-symbol AI budget biases from realised performance."""

    def __init__(self, state: Dict[str, Any]):
        self._root = state
        self._state = self._root.setdefault(
            "ai_budget_learning",
            {"symbols": {}, "usage": []},
        )
        self._cost_window = 40
        self._min_samples = 2
        self._skip_half_life = 90 * 60  # decay faster after roughly 90 minutes
        self._skip_penalty_cap = 5.0
        self._skip_reason_cap = 6
        self._skip_penalty_factor = 0.22
        self._skip_penalty_increment = {
            "plan": 0.55,
            "trend": 0.45,
            "postmortem": 0.2,
        }
        self._skip_limit_plan = 1.65
        self._skip_limit_trend = 1.1
        self._skip_limit_any = 2.35
        self._skip_limit_soft = 0.45
        self._reward_window = 60

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
            {
                "count": 0,
                "reward": 0.0,
                "cost": 0.0,
                "bias": 1.0,
                "updated": 0.0,
                "skip_weight": 0.0,
                "skip_updated": 0.0,
                "skip_reasons": {},
                "skip_meta": [],
                "recent_pnl": [],
            },
        )
        sym_state["count"] = int(sym_state.get("count", 0)) + 1
        sym_state["reward"] = float(sym_state.get("reward", 0.0) or 0.0) + pnl_r
        recent = sym_state.setdefault("recent_pnl", [])
        if isinstance(recent, list):
            recent.append(pnl_r)
            if len(recent) > self._reward_window:
                del recent[: len(recent) - self._reward_window]
            sym_state["recent_pnl"] = recent
        skip_penalty = self._decayed_skip_penalty(sym_state, update=True)
        if pnl_r > 0 and skip_penalty > 0:
            # Successful trades reduce the severity of prior AI skips.
            reduced = max(0.0, skip_penalty * 0.5)
            if reduced <= 1e-4:
                sym_state["skip_weight"] = 0.0
                sym_state["skip_updated"] = 0.0
            else:
                sym_state["skip_weight"] = reduced
                sym_state["skip_updated"] = time.time()
        sym_state["updated"] = time.time()
        sym_state["bias"] = self._compute_bias(sym_state)
        self._state.setdefault("symbols", {})[symbol] = sym_state

    def should_allocate(self, symbol: str, kind: str) -> bool:
        if not symbol:
            return True
        sym_state = self._state.get("symbols", {}).get(symbol)
        if not sym_state:
            return True
        if sym_state.get("count", 0) < self._min_samples:
            skip_penalty = self._decayed_skip_penalty(sym_state, update=True)
            if skip_penalty >= self._skip_limit_any:
                return False
            if kind == "trend" and skip_penalty >= self._skip_limit_trend:
                return False
            if kind != "trend" and skip_penalty >= self._skip_limit_plan:
                return False
            if skip_penalty < self._skip_limit_soft:
                return True
        skip_penalty = self._decayed_skip_penalty(sym_state, update=True)
        if skip_penalty >= self._skip_limit_any:
            return False
        if kind == "trend" and skip_penalty >= self._skip_limit_trend:
            return False
        if kind != "trend" and skip_penalty >= self._skip_limit_plan:
            return False
        bias = float(self._compute_bias(sym_state) or sym_state.get("bias", 1.0) or 1.0)
        sym_state["bias"] = bias
        if kind == "postmortem":
            return bias >= 0.25
        if bias < 0.45:
            return False
        if kind == "trend" and bias < 0.6:
            return False
        return bias >= 0.7 if kind != "trend" else True

    def context_bias(self, symbol: str) -> float:
        sym_state = self._state.get("symbols", {}).get(symbol)
        if not sym_state:
            return 1.0
        bias = self._compute_bias(sym_state)
        sym_state["bias"] = bias
        return float(bias or 1.0)

    def context_snapshot(self, symbol: str) -> Dict[str, Any]:
        sym_key = symbol if symbol in (self._state.get("symbols", {}) or {}) else symbol or "*"
        sym_state = self._state.get("symbols", {}).get(sym_key)
        if not isinstance(sym_state, dict):
            sym_state = self._state.get("symbols", {}).get("*")
        snapshot: Dict[str, Any] = {}
        if not isinstance(sym_state, dict):
            return snapshot
        bias = self._compute_bias(sym_state)
        sym_state["bias"] = bias
        snapshot["bias"] = float(bias)
        skip_penalty = self._decayed_skip_penalty(sym_state, update=False)
        snapshot["skip_weight"] = float(skip_penalty)
        recent = sym_state.get("recent_pnl")
        if isinstance(recent, list) and recent:
            tail = recent[-min(len(recent), 12) :]
            if tail:
                avg = sum(tail) / len(tail)
                snapshot["recent_avg_pnl"] = float(avg)
                snapshot["recent_last_pnl"] = float(tail[-1])
        skip_reasons = sym_state.get("skip_reasons")
        if isinstance(skip_reasons, dict) and skip_reasons:
            ranked = sorted(
                (
                    (str(reason), int((meta or {}).get("count", 0)))
                    for reason, meta in skip_reasons.items()
                ),
                key=lambda item: item[1],
                reverse=True,
            )
            if ranked:
                snapshot["skip_top_reason"] = ranked[0][0]
                snapshot["skip_top_reason_count"] = float(ranked[0][1])
        skip_meta = sym_state.get("skip_meta")
        if isinstance(skip_meta, list) and skip_meta:
            last_entry = skip_meta[-1]
            if isinstance(last_entry, dict):
                reason = last_entry.get("reason")
                if isinstance(reason, str) and reason.strip():
                    snapshot.setdefault("skip_latest_reason", reason.strip())
                ts = last_entry.get("ts")
                try:
                    snapshot["skip_latest_ts"] = float(ts)
                except (TypeError, ValueError):
                    pass
        return snapshot

    def record_skip(
        self,
        symbol: Optional[str],
        kind: str,
        reason: Optional[str],
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        sym_key = symbol or "*"
        sym_state = self._state.setdefault("symbols", {}).setdefault(
            sym_key,
            {
                "count": 0,
                "reward": 0.0,
                "cost": 0.0,
                "bias": 1.0,
                "updated": 0.0,
                "skip_weight": 0.0,
                "skip_updated": 0.0,
                "skip_reasons": {},
                "skip_meta": [],
                "recent_pnl": [],
            },
        )
        now = time.time()
        current = self._decayed_skip_penalty(sym_state, now=now, update=True)
        increment = float(self._skip_penalty_increment.get(kind, 0.5))
        new_weight = min(self._skip_penalty_cap, current + increment)
        sym_state["skip_weight"] = new_weight
        sym_state["skip_updated"] = now
        reason_token = str(reason or "unknown").strip()
        if reason_token:
            reasons: Dict[str, Dict[str, Any]] = sym_state.setdefault("skip_reasons", {})
            reason_entry = reasons.get(reason_token)
            if not isinstance(reason_entry, dict):
                reason_entry = {"count": 0, "last": 0.0}
            reason_entry["count"] = int(reason_entry.get("count", 0)) + 1
            reason_entry["last"] = now
            reasons[reason_token] = reason_entry
            if len(reasons) > self._skip_reason_cap:
                oldest = min(reasons.items(), key=lambda item: item[1].get("last", now))[0]
                reasons.pop(oldest, None)
        if meta:
            sanitized: Dict[str, Any] = {}
            for key, value in meta.items():
                if isinstance(value, (str, int, float, bool)):
                    sanitized[str(key)] = value
            if reason_token:
                sanitized.setdefault("reason", reason_token)
            if sanitized:
                sanitized["ts"] = now
                history: List[Dict[str, Any]] = sym_state.setdefault("skip_meta", [])
                history.append(sanitized)
                if len(history) > 8:
                    del history[: len(history) - 8]
        sym_state["updated"] = now
        sym_state["bias"] = self._compute_bias(sym_state, now=now)
        self._state.setdefault("symbols", {})[sym_key] = sym_state

    def _compute_bias(self, sym_state: Dict[str, Any], now: Optional[float] = None) -> float:
        reward = float(sym_state.get("reward", 0.0) or 0.0)
        count = max(1, int(sym_state.get("count", 0) or 0))
        avg = reward / count
        recent = sym_state.get("recent_pnl")
        if isinstance(recent, list) and recent:
            window = recent[-min(len(recent), 20) :]
            if window:
                recent_avg = sum(window) / len(window)
                avg = (recent_avg * 0.7) + (avg * 0.3)
        skip_penalty = self._decayed_skip_penalty(sym_state, now=now, update=True)
        bias = 1.0 + avg * 0.4 - skip_penalty * self._skip_penalty_factor
        return max(0.15, min(1.8, bias))

    def _decayed_skip_penalty(
        self,
        sym_state: Dict[str, Any],
        *,
        now: Optional[float] = None,
        update: bool = False,
    ) -> float:
        weight = float(sym_state.get("skip_weight", 0.0) or 0.0)
        if weight <= 1e-6:
            if update and weight:
                sym_state["skip_weight"] = 0.0
                sym_state["skip_updated"] = 0.0
            return 0.0
        last = float(sym_state.get("skip_updated", 0.0) or 0.0)
        now_val = float(now if now is not None else time.time())
        elapsed = max(0.0, now_val - last) if last else 0.0
        if elapsed <= 0 or self._skip_half_life <= 0:
            decayed = weight
        else:
            decay_factor = pow(0.5, elapsed / float(self._skip_half_life))
            decayed = weight * decay_factor
        if update:
            if decayed <= 1e-4:
                sym_state["skip_weight"] = 0.0
                sym_state["skip_updated"] = 0.0
            else:
                sym_state["skip_weight"] = decayed
                sym_state["skip_updated"] = now_val
        return decayed
