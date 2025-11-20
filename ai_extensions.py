"""AI-driven learning helpers for MrAster bot."""
from __future__ import annotations

import math
import os
from datetime import datetime
import re
import time
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple


def _parse_env_float(key: str) -> Optional[float]:
    raw = os.getenv(key)
    if raw is None:
        return None
    token = str(raw).strip()
    if not token:
        return None
    try:
        value = float(token)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(value):
        return None
    return value


def _playbook_refresh_interval_seconds() -> float:
    """Resolve the desired refresh interval for AI playbook updates."""

    default_seconds = 3 * 60 * 60.0
    seconds = _parse_env_float("ASTER_PLAYBOOK_REFRESH_INTERVAL_SECONDS")
    if seconds is None:
        seconds = _parse_env_float("ASTER_PLAYBOOK_REFRESH_SECONDS")
    if seconds is None:
        minutes = _parse_env_float("ASTER_PLAYBOOK_REFRESH_INTERVAL_MINUTES")
        if minutes is None:
            minutes = _parse_env_float("ASTER_PLAYBOOK_REFRESH_MINUTES")
        if minutes is not None:
            seconds = minutes * 60.0
    if seconds is None:
        seconds = default_seconds
    seconds = max(3 * 60 * 60.0, float(seconds))
    return seconds


_PLAYBOOK_REFRESH_INTERVAL_SECONDS = _playbook_refresh_interval_seconds()

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

_ADVISOR_PERSONA_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "trend_follower": {
        "label": "Trendfolger",
        "prompt": (
            "You are operating as the Trendfolger persona. Prioritise breakout and trend-"
            "continuation checklists: validate higher timeframe alignment, momentum breadth,"
            " and progressive stop management before approving entries."
        ),
        "focus_keywords": [
            "trend",
            "momentum",
            "breakout",
            "pullback",
        ],
        "confidence_bias": 0.05,
        "priority": 1,
    },
    "mean_reversion": {
        "label": "Mean-Reversion",
        "prompt": (
            "You are operating as the Mean-Reversion persona. Emphasise range-bound checklists:"
            " confirm support/resistance, oscillator extremes, liquidity pockets, and plan quick risk release."
        ),
        "focus_keywords": [
            "range",
            "oscillator",
            "support",
            "fade",
        ],
        "confidence_bias": -0.02,
        "priority": 1,
    },
    "event_risk": {
        "label": "Event-Risk",
        "prompt": (
            "You are operating as the Event-Risk guardian persona. Focus on catalyst-driven checklists:"
            " audit news drivers, tighten sizing, prefer hedges, and decline trades lacking mitigation."
        ),
        "focus_keywords": [
            "event_risk",
            "hedge",
            "reduce",
            "news",
        ],
        "confidence_bias": -0.08,
        "priority": 5,
    },
}


def _advisor_persona_store(root: Dict[str, Any]) -> Dict[str, Any]:
    store = root.setdefault("advisor_persona", {}) if isinstance(root, dict) else {}
    sources = store.get("sources")
    if not isinstance(sources, dict):
        sources = {}
    store["sources"] = sources
    return store


def _advisor_persona_definition(key: str) -> Optional[Dict[str, Any]]:
    if not isinstance(key, str):
        return None
    token = key.strip().lower()
    if not token:
        return None
    return _ADVISOR_PERSONA_DEFINITIONS.get(token)


def _advisor_persona_refresh(store: Dict[str, Any], now: Optional[float] = None) -> None:
    if not isinstance(store, dict):
        return
    sources = store.get("sources")
    if not isinstance(sources, dict):
        sources = {}
        store["sources"] = sources
    ts = time.time() if now is None else float(now)
    changed = False
    for source, entry in list(sources.items()):
        if not isinstance(entry, dict):
            sources.pop(source, None)
            changed = True
            continue
        expires = entry.get("expires")
        if expires is not None:
            try:
                expiry_ts = float(expires)
            except (TypeError, ValueError):
                expiry_ts = ts
            if expiry_ts <= ts:
                sources.pop(source, None)
                changed = True
    active: Optional[Dict[str, Any]] = None
    for entry in sources.values():
        if not isinstance(entry, dict):
            continue
        candidate = dict(entry)
        if active is None:
            active = candidate
            continue
        priority = int(candidate.get("priority", 0))
        active_priority = int(active.get("priority", 0))
        if priority > active_priority:
            active = candidate
            continue
        if priority == active_priority:
            updated = float(candidate.get("updated", 0.0) or 0.0)
            active_updated = float(active.get("updated", 0.0) or 0.0)
            if updated > active_updated:
                active = candidate
    if active is not None:
        store["active"] = dict(active)
    elif "active" in store:
        store.pop("active", None)
    if changed:
        store["sources"] = sources


def advisor_register_persona(
    root: Dict[str, Any],
    source: str,
    key: str,
    *,
    reason: Optional[str] = None,
    focus: Optional[Iterable[str]] = None,
    ttl: Optional[float] = None,
    confidence_bias: Optional[float] = None,
    priority: Optional[int] = None,
    now: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    definition = _advisor_persona_definition(key)
    if not definition:
        return None
    store = _advisor_persona_store(root)
    ts = time.time() if now is None else float(now)
    focus_terms: List[str] = []
    base_focus = definition.get("focus_keywords", [])
    if isinstance(base_focus, (list, tuple)):
        for term in base_focus:
            if isinstance(term, str) and term and term not in focus_terms:
                focus_terms.append(term)
    if focus:
        for term in focus:
            if isinstance(term, str):
                token = term.strip()
                if token and token not in focus_terms:
                    focus_terms.append(token)
    entry = {
        "key": key,
        "label": definition.get("label", key.title()),
        "prompt": definition.get("prompt", ""),
        "focus_keywords": focus_terms[:12],
        "confidence_bias": float(
            confidence_bias
            if confidence_bias is not None
            else definition.get("confidence_bias", 0.0)
        ),
        "priority": int(priority if priority is not None else definition.get("priority", 0)),
        "source": str(source or "unknown"),
        "updated": ts,
    }
    if reason:
        entry["reason"] = str(reason)
    if ttl is not None:
        try:
            ttl_value = float(ttl)
        except (TypeError, ValueError):
            ttl_value = 0.0
        if ttl_value > 0:
            entry["expires"] = ts + ttl_value
    store.setdefault("sources", {})[entry["source"]] = entry
    _advisor_persona_refresh(store, ts)
    return dict(entry)


def advisor_clear_persona(root: Dict[str, Any], source: str) -> None:
    store = _advisor_persona_store(root)
    sources = store.get("sources", {})
    if source in sources:
        sources.pop(source, None)
        _advisor_persona_refresh(store)


def advisor_active_persona(root: Dict[str, Any], now: Optional[float] = None) -> Optional[Dict[str, Any]]:
    store = _advisor_persona_store(root)
    _advisor_persona_refresh(store, now)
    active = store.get("active")
    return dict(active) if isinstance(active, dict) else None


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
    "pm_volatility_compression_flag",
)
POSTMORTEM_DEFAULT_WEIGHT = 0.15
POSTMORTEM_DECAY = 0.92


ADVISOR_MEMORY_TEMPLATES: Dict[str, str] = {
    "funding": "Funding regime kept catching us off guard. Add a dedicated funding skew check before sizing new trades.",
    "funding_edge": "Funding divergence kept hurting outcomes. Review perp vs. spot funding before taking the next setup.",
    "oracle_gap": "Oracle vs. spot gaps repeated. Validate cross-venue pricing before committing risk.",
    "pm_liquidity_gap": "Liquidity gaps were ignored. Demand confirmation of resting depth and slippage before re-entering.",
    "pm_execution_delay": "Execution delays eroded performance. Pre-plan order routing to avoid hesitation on entries/exits.",
    "pm_trend_break": "Trend breaks surprised the plan. Require HTF confirmation when structure fractures.",
    "pm_macro_event": "Macro catalysts blindsided trades. Check the macro/event calendar before deploying capital.",
    "pm_news_driver": "News-driven moves were missed. Monitor catalyst feeds before acting on signals.",
    "pm_sentiment_conflict": "Sentiment conflicts kept biting. Align positioning with sentiment data or size down.",
    "pm_volatility_bias": "Volatility regime misread. Respect current vol profile when sizing risk.",
    "pm_spread_bias": "Spreads chewed through edge. Re-evaluate liquidity costs and avoid thin books.",
    "pm_liquidity_profile": "Liquidity quality disappointed. Verify venue depth before scaling.",
    "pm_execution_quality": "Execution quality lagged. Tighten broker/venue routing before next wave.",
    "pm_event_risk": "Event risk was underestimated. Gate trades when event risk spikes.",
    "pm_hype_bias": "Hype-driven froth hurt trades. Fade hype or reduce exposure when crowding builds.",
    "pm_trend_bias": "Trend bias misalignment repeated. Sync entries with prevailing regime.",
    "pm_adx_bias": "Trend strength filter slipped. Re-calibrate ADX thresholds before entries.",
    "pm_ema_slope": "EMA slope context misread. Validate slope/stack alignment in the checklist.",
}

ADVISOR_MEMORY_ALIAS_MAP: Dict[str, Set[str]] = {
    "funding": {"funding", "funding_edge"},
    "funding_edge": {"funding_edge", "funding"},
    "oracle_gap": {"oracle_gap", "oracle_gap_clamped"},
    "pm_liquidity_gap": {"pm_liquidity_gap", "liquidity_gap"},
    "pm_execution_delay": {"pm_execution_delay", "execution_delay"},
    "pm_trend_break": {"pm_trend_break", "trend_break", "pm_trend_bias", "trend"},
    "pm_macro_event": {"pm_macro_event", "macro_event"},
    "pm_news_driver": {"pm_news_driver", "news_driver"},
    "pm_sentiment_conflict": {"pm_sentiment_conflict", "sentiment_conflict"},
    "pm_volatility_bias": {"pm_volatility_bias", "volatility", "atr_pct"},
    "pm_spread_bias": {"pm_spread_bias", "spread", "spread_bps"},
    "pm_liquidity_profile": {"pm_liquidity_profile", "liquidity_profile"},
    "pm_execution_quality": {"pm_execution_quality", "execution_quality"},
    "pm_event_risk": {"pm_event_risk", "event_risk", "sentinel_event_risk"},
    "pm_hype_bias": {"pm_hype_bias", "hype", "sentinel_hype"},
    "pm_trend_bias": {"pm_trend_bias", "trend", "regime_slope"},
    "pm_adx_bias": {"pm_adx_bias", "adx"},
    "pm_ema_slope": {"pm_ema_slope", "ema_slope"},
}


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
        self._lesson_threshold = 0.35
        self._lesson_min_severity = 0.4
        self._lesson_min_count = 2
        self._lesson_retention = 3 * 24 * 60 * 60
        memory_bucket = self._root.setdefault(
            "advisor_memory", {"lessons": {}, "updated": 0.0}
        )
        if not isinstance(memory_bucket, dict):
            memory_bucket = {"lessons": {}, "updated": 0.0}
            self._root["advisor_memory"] = memory_bucket
        memory_bucket.setdefault("lessons", {})
        memory_bucket.setdefault("updated", 0.0)
        self._memory = memory_bucket

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
        self._update_advisor_memory()

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
        self._apply_advisor_memory(ctx)

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


    def advisor_memory(self) -> Dict[str, Any]:
        lessons = {
            key: dict(value)
            for key, value in (self._memory.get("lessons", {}) or {}).items()
        }
        return {"lessons": lessons, "updated": self._memory.get("updated", 0.0)}

    def _canonical_feature_key(self, key: Any) -> Optional[str]:
        if key is None:
            return None
        if isinstance(key, str):
            token = key.strip().lower()
        else:
            token = str(key).strip().lower()
        if not token:
            return None
        if token in POSTMORTEM_FEATURE_MAP:
            token = POSTMORTEM_FEATURE_MAP[token]
        return token

    def _collect_issue_stats(self) -> Dict[str, Dict[str, float]]:
        history: List[Dict[str, Any]] = self._state.get("history", [])
        if not history:
            return {}
        stats: Dict[str, Dict[str, float]] = {}
        now = time.time()
        window = history[-120:]
        for record in window:
            pnl_r = float(record.get("pnl_r", 0.0) or 0.0)
            if pnl_r >= -0.1:
                continue
            features = record.get("features")
            if not isinstance(features, dict):
                continue
            ts = float(record.get("ts", now) or now)
            weight = min(abs(pnl_r), 3.0)
            for raw_key, raw_value in features.items():
                canonical = self._canonical_feature_key(raw_key)
                if not canonical:
                    continue
                try:
                    value = float(raw_value)
                except (TypeError, ValueError):
                    continue
                if abs(value) < self._lesson_threshold:
                    continue
                bucket = stats.setdefault(
                    canonical,
                    {"score": 0.0, "weight": 0.0, "count": 0, "last_ts": ts},
                )
                bucket["score"] += value * weight
                bucket["weight"] += weight
                bucket["count"] += 1
                if ts > bucket.get("last_ts", 0.0):
                    bucket["last_ts"] = ts
        for detail in stats.values():
            weight = detail.get("weight", 0.0)
            detail["avg"] = detail["score"] / weight if weight else 0.0
            detail["avg_abs"] = abs(detail.get("avg", 0.0))
        return stats

    def _lesson_aliases(self, feature: str) -> Set[str]:
        aliases = set(ADVISOR_MEMORY_ALIAS_MAP.get(feature, set()))
        aliases.add(feature)
        for raw_key, mapped in POSTMORTEM_FEATURE_MAP.items():
            if mapped == feature:
                aliases.add(raw_key)
        return aliases

    @staticmethod
    def _lesson_label(feature: str) -> str:
        label = feature
        if label.startswith("pm_"):
            label = label[3:]
        label = label.replace("_", " ")
        return label.strip().lower()

    def _lesson_snippet(self, feature: str, avg: float) -> str:
        template = ADVISOR_MEMORY_TEMPLATES.get(feature)
        if template:
            return template
        label = self._lesson_label(feature)
        return (
            f"Postmortems keep flagging {label} issues. "
            "Add this check to the pre-trade routine."
        )

    def _update_advisor_memory(self) -> None:
        stats = self._collect_issue_stats()
        lessons = self._memory.get("lessons")
        if not isinstance(lessons, dict):
            lessons = {}
            self._memory["lessons"] = lessons
        now = time.time()
        changed = False
        for feature, detail in stats.items():
            if detail.get("count", 0) < self._lesson_min_count:
                continue
            if detail.get("avg_abs", 0.0) < self._lesson_min_severity:
                continue
            snippet = self._lesson_snippet(feature, detail.get("avg", 0.0))
            entry = lessons.get(feature, {})
            match_keys = sorted(self._lesson_aliases(feature))
            payload = {
                "feature": feature,
                "snippet": snippet,
                "avg_score": detail.get("avg", 0.0),
                "severity": detail.get("avg_abs", 0.0),
                "count": detail.get("count", 0),
                "weight": detail.get("weight", 0.0),
                "last_triggered": detail.get("last_ts", now),
                "threshold": self._lesson_threshold,
                "match_keys": match_keys,
                "source": "postmortem",
                "updated": now,
            }
            if entry != payload:
                lessons[feature] = payload
                changed = True
        for feature in list(lessons.keys()):
            if feature in stats:
                continue
            entry = lessons.get(feature, {})
            last_ts = float(entry.get("last_triggered", 0.0) or 0.0)
            if now - last_ts > self._lesson_retention:
                del lessons[feature]
                changed = True
        if changed:
            self._memory["updated"] = now
            self._root["advisor_memory"] = self._memory

    def _apply_advisor_memory(self, ctx: Dict[str, Any]) -> None:
        lessons = self._memory.get("lessons")
        if not isinstance(lessons, dict) or not lessons:
            return
        matches: List[Dict[str, Any]] = []
        snippets: List[str] = []
        for feature, entry in lessons.items():
            snippet = entry.get("snippet")
            if not snippet:
                continue
            threshold = float(entry.get("threshold", self._lesson_threshold) or 0.0)
            keys = entry.get("match_keys") or [feature]
            matched = False
            peak = 0.0
            for key in keys:
                if key not in ctx:
                    continue
                try:
                    value = float(ctx.get(key, 0.0) or 0.0)
                except (TypeError, ValueError):
                    continue
                if abs(value) >= threshold:
                    matched = True
                    peak = max(peak, abs(value))
            if not matched:
                continue
            if snippet not in snippets:
                snippets.append(snippet)
            matches.append(
                {
                    "feature": feature,
                    "snippet": snippet,
                    "match_keys": list(keys),
                    "peak": peak,
                }
            )
        if not snippets:
            return
        existing = ctx.get("advisor_memory_snippets")
        if isinstance(existing, list):
            for snippet in snippets:
                if snippet not in existing:
                    existing.append(snippet)
        else:
            ctx["advisor_memory_snippets"] = list(snippets)
        ctx["advisor_memory_active"] = 1.0
        ctx.setdefault("advisor_memory_matches", []).extend(matches)
        focus_list = ctx.setdefault("advisor_memory_focus", [])
        for item in matches:
            feature_name = item.get("feature")
            if feature_name and feature_name not in focus_list:
                focus_list.append(feature_name)
        ctx["advisor_memory_updated"] = float(self._memory.get("updated", 0.0) or 0.0)


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
        # Event risk guardrails must be evaluated on the active symbol, so we only
        # consider symbol-level metrics instead of global features.
        "event_risk": ("sentinel_event_risk", "event_risk"),
        "hype": ("sentinel_hype", "playbook_feature_hype", "hype", "pm_hype_bias"),
        "volatility": ("atr_pct", "playbook_feature_volatility", "pm_volatility_bias"),
        "breadth": ("breadth", "playbook_feature_breadth"),
        "trend_strength": ("trend", "regime_slope", "playbook_feature_trend", "pm_trend_bias"),
    }

    _AGGRESSIVE_PRESETS = {"high", "att"}
    _STRUCTURED_SOFTEN_SLACK = {
        "event_risk": 0.12,
        "hype": 0.08,
        "volatility": 0.1,
        "breadth": 0.08,
        "trend_strength": 0.08,
    }
    _STRUCTURED_STRICT_TERMS = (
        "halt",
        "suspend",
        "freeze",
        "blackout",
        "do not trade",
        "forbid",
        "stop trading",
        "no trading",
    )
    _FILTER_FIELD_SPECS: Dict[str, Dict[str, Tuple[float, float]]] = {
        "long_overextended": {
            "rsi_cap": (45.0, 75.0),
            "atr_pct_cap": (0.002, 0.02),
        },
        "trend_extension": {
            "bars_soft": (6.0, 60.0),
            "bars_hard": (10.0, 90.0),
            "adx_min": (20.0, 80.0),
        },
        "continuation_pullback": {
            "stoch_warn": (40.0, 92.0),
            "stoch_max": (55.0, 98.0),
            "stoch_min": (5.0, 45.0),
            "adx_delta_min": (0.0, 15.0),
        },
        "spread_tight": {"spread_bps_max": (0.0003, 0.004)},
        "short_trend_alignment": {
            "slope_min": (0.0002, 0.0035),
            "supertrend_tol": (-0.6, 0.85),
        },
        "edge_r": {"min_edge_r": (0.03, 0.4)},
        "no_cross": {
            "rsi_buy_min": (38.0, 65.0),
            "rsi_sell_max": (35.0, 65.0),
        },
        "wicky": {"wickiness_max": (0.94, 1.0)},
        "stoch_rsi_trend_short": {"stoch_min": (5.0, 75.0)},
        "sentinel_veto": {
            "event_risk_gate": (0.3, 0.9),
            "block_risk": (0.45, 0.98),
            "min_multiplier": (0.1, 0.8),
            "weight": (0.5, 1.25),
        },
        "playbook_structured_block": {
            "event_risk_max": (0.2, 0.9),
            "soft_multiplier": (0.25, 1.0),
        },
    }

    _SIZE_BIAS_DELTA = {"low": -0.08, "mid": 0.0, "high": 0.12, "att": 0.18}
    _RISK_BIAS_DELTA = {"low": -0.08, "mid": 0.0, "high": 0.12, "att": 0.18}
    _CONFIDENCE_DELTA = {"low": -0.05, "mid": 0.0, "high": 0.05, "att": 0.08}
    _FILTER_RANGE_RELAXATION = {"low": 0.0, "mid": 0.06, "high": 0.12, "att": 0.16}

    _SELL_DELTA_RATIO = 0.65

    _SOFT_BLOCK_FACTOR = 0.45

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
        self._refresh_interval = _PLAYBOOK_REFRESH_INTERVAL_SECONDS
        self._bootstrap_pending = True
        self._bootstrap_deadline = time.time() + 120.0
        self._bootstrap_retry = 90.0
        self._bootstrap_cooldown_until = 0.0
        self._event_cb = event_cb
        preset = os.getenv("ASTER_PRESET_MODE", "mid").strip().lower() or "mid"
        self._preset_mode = preset if preset in {"low", "mid", "high", "att"} else "mid"
        self._aggressive_mode = self._preset_mode in self._AGGRESSIVE_PRESETS
        self._size_bias_delta = self._SIZE_BIAS_DELTA.get(self._preset_mode, 0.0)
        self._sell_bias_delta = self._size_bias_delta * self._SELL_DELTA_RATIO
        self._risk_bias_delta = self._RISK_BIAS_DELTA.get(self._preset_mode, 0.0)
        self._confidence_delta = self._CONFIDENCE_DELTA.get(self._preset_mode, 0.0)
        self._filter_relaxation = self._FILTER_RANGE_RELAXATION.get(
            self._preset_mode, 0.0
        )
        if not advisor_active_persona(self._root):
            advisor_register_persona(
                self._root,
                "playbook",
                "trend_follower",
                reason="bootstrap",
                focus=["trend", "momentum", "breakout"],
                confidence_bias=self._persona_confidence_override(
                    "trend_follower", self._state.get("active", {})
                ),
                now=time.time(),
            )

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

    def _relaxed_filter_bounds(self, lower: float, upper: float) -> Tuple[float, float]:
        if self._filter_relaxation <= 0.0:
            return lower, upper
        if not math.isfinite(lower) or not math.isfinite(upper):
            return lower, upper
        span = upper - lower
        if span <= 0.0:
            return lower, upper
        slack = span * self._filter_relaxation
        relaxed_lower = lower - (slack * 0.5)
        relaxed_upper = upper + slack
        if lower >= 0.0 and relaxed_lower < 0.0:
            relaxed_lower = 0.0
        if relaxed_upper <= relaxed_lower:
            relaxed_upper = relaxed_lower + max(1e-6, span * 0.1)
        return relaxed_lower, relaxed_upper

    def _normalize_filters(self, payload: Any) -> Optional[Dict[str, Dict[str, float]]]:
        if not isinstance(payload, dict):
            return None
        normalized: Dict[str, Dict[str, float]] = {}
        for reason, spec in self._FILTER_FIELD_SPECS.items():
            fields = payload.get(reason)
            if not isinstance(fields, dict):
                continue
            cleaned: Dict[str, float] = {}
            for field, bounds in spec.items():
                if field not in fields:
                    continue
                value = fields.get(field)
                try:
                    numeric = float(value)
                except (TypeError, ValueError):
                    continue
                lower, upper = self._relaxed_filter_bounds(*bounds)
                cleaned[field] = float(max(lower, min(upper, numeric)))
            if not cleaned:
                continue
            if reason == "trend_extension":
                soft = cleaned.get("bars_soft")
                hard = cleaned.get("bars_hard")
                if soft is not None and hard is not None and hard <= soft:
                    cleaned["bars_hard"] = float(soft + 1.0)
            if reason == "continuation_pullback":
                warn = cleaned.get("stoch_warn")
                maxi = cleaned.get("stoch_max")
                mini = cleaned.get("stoch_min")
                if warn is not None and maxi is not None and maxi < warn:
                    cleaned["stoch_max"] = warn
                if mini is not None and warn is not None and warn < mini:
                    cleaned["stoch_warn"] = mini
                if mini is not None and maxi is not None and maxi < mini:
                    cleaned["stoch_max"] = mini
            normalized[reason] = cleaned
        return normalized or None

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
        persona_active = advisor_active_persona(self._root)
        if persona_active:
            ctx["advisor_persona"] = persona_active.get("key")
            ctx["advisor_persona_label"] = persona_active.get("label")
            ctx["advisor_persona_source"] = persona_active.get("source")
            focus_terms = persona_active.get("focus_keywords")
            if isinstance(focus_terms, list) and focus_terms:
                ctx["advisor_persona_focus_terms"] = list(focus_terms)
            try:
                ctx["advisor_persona_confidence_bias"] = float(
                    persona_active.get("confidence_bias", 0.0) or 0.0
                )
            except (TypeError, ValueError):
                pass
        hint = active.get("persona_hint")
        if isinstance(hint, dict):
            ctx["playbook_persona"] = hint.get("key")
            if hint.get("focus_keywords"):
                ctx["playbook_persona_focus"] = hint.get("focus_keywords")
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
        structured_directives: List[Dict[str, Any]] = []
        actions_structured = active.get("structured_actions")
        if isinstance(actions_structured, list):
            structured_directives.extend(actions_structured)
        risk_structured = active.get("structured_risk_controls")
        if isinstance(risk_structured, list):
            structured_directives.extend(risk_structured)
        self._apply_structured_directives(ctx, structured_directives)

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
            "playbook_structured_soft_block",
            "playbook_structured_soft_factor",
            "playbook_structured_soft_reason",
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
        soft_block = False
        soft_reasons: List[str] = []
        soft_factor = 1.0
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
                if not isinstance(condition, dict):
                    directive_label = str(
                        ctx.get("playbook_symbol_directive") or ""
                    ).strip().lower()
                    try:
                        directive_level = float(
                            ctx.get("playbook_symbol_directive_level", 0.0) or 0.0
                        )
                    except (TypeError, ValueError):
                        directive_level = 0.0
                    block_threshold = float(
                        self._DIRECTIVE_LEVEL.get("block", 2.6)
                    )
                    if directive_label != "block" and directive_level < block_threshold:
                        if note:
                            notes.append(
                                f"ignored block {note}: no symbol hard-block context"
                            )
                        continue
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
                if self._aggressive_mode:
                    softened, soften_reason = self._should_soften_hard_block(ctx, entry)
                    if softened:
                        soft_block = True
                        soft_factor *= self._SOFT_BLOCK_FACTOR
                        size_mult *= self._SOFT_BLOCK_FACTOR
                        resolved_reason = soften_reason or note or entry.get("effect")
                        if resolved_reason:
                            notes.append(
                                f"soft×{self._SOFT_BLOCK_FACTOR:.2f}: {resolved_reason}"
                            )
                            soft_reasons.append(resolved_reason)
                        else:
                            notes.append(
                                f"soft×{self._SOFT_BLOCK_FACTOR:.2f}: playbook hard block throttled"
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

        if soft_block:
            ctx["playbook_structured_soft_block"] = True
            ctx["playbook_structured_soft_factor"] = float(max(0.1, min(3.5, soft_factor)))
            if soft_reasons:
                ctx["playbook_structured_soft_reason"] = "; ".join(
                    reason for reason in soft_reasons if reason
                )
        else:
            ctx.pop("playbook_structured_soft_block", None)
            ctx.pop("playbook_structured_soft_factor", None)
            ctx.pop("playbook_structured_soft_reason", None)

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
        if self._size_bias_delta:
            normalized_size["BUY"] = float(
                max(0.4, min(2.5, normalized_size["BUY"] + self._size_bias_delta))
            )
            normalized_size["SELL"] = float(
                max(0.4, min(2.5, normalized_size["SELL"] + self._sell_bias_delta))
            )
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
        risk_bias = self._derive_risk_bias(payload)
        if self._risk_bias_delta:
            risk_bias = float(max(0.5, min(1.6, risk_bias + self._risk_bias_delta)))
        active["risk_bias"] = risk_bias
        if confidence is not None:
            adjusted_conf = confidence + self._confidence_delta
            active["confidence"] = max(0.0, min(1.0, adjusted_conf))
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
        self._apply_persona_hint(active, now)
        return active

    def _feature_keyword_score(
        self, features: Dict[str, Any], keywords: Sequence[str]
    ) -> float:
        total = 0.0
        for name, raw_value in features.items():
            lowered = str(name).lower()
            if not any(term in lowered for term in keywords):
                continue
            try:
                numeric = abs(float(raw_value))
            except (TypeError, ValueError):
                continue
            total += numeric
        return float(total)

    def _persona_focus_terms(self, active: Dict[str, Any]) -> List[str]:
        focus_terms: List[str] = []
        features = active.get("features", {})
        if isinstance(features, dict):
            try:
                ordered = sorted(
                    (
                        (key, abs(float(value)))
                        for key, value in features.items()
                    ),
                    key=lambda item: item[1],
                    reverse=True,
                )
            except Exception:
                ordered = []
            for key, weight in ordered[:6]:
                if weight < 0.08:
                    continue
                slug = self._normalize_feature_key(key) or str(key)
                if slug and slug not in focus_terms:
                    focus_terms.append(slug)
        strategy = active.get("strategy")
        if isinstance(strategy, dict):
            actions = strategy.get("actions")
            if isinstance(actions, list):
                for action in actions:
                    if not isinstance(action, dict):
                        continue
                    tokens = _extract_action_focus_terms(
                        (
                            action.get("title"),
                            action.get("detail"),
                            action.get("trigger"),
                        )
                    )
                    for token in tokens:
                        if token not in focus_terms:
                            focus_terms.append(token)
                        if len(focus_terms) >= 10:
                            break
        return focus_terms[:10]

    def _select_persona_key(
        self, active: Dict[str, Any]
    ) -> Tuple[str, str, List[str]]:
        features = active.get("features", {}) if isinstance(active.get("features"), dict) else {}
        mode_text = str(active.get("mode", "")).lower()
        bias_text = str(active.get("bias", "")).lower()
        notes_text = str(active.get("notes", "")).lower()
        reason_text = str(active.get("reason", "")).lower()
        strategy = active.get("strategy")
        strategy_bits: List[str] = []
        if isinstance(strategy, dict):
            for key in ("name", "objective", "why_active"):
                value = strategy.get(key)
                if isinstance(value, str):
                    strategy_bits.append(value.lower())
        combined_text = " ".join(
            bit for bit in [mode_text, bias_text, notes_text, reason_text] + strategy_bits if bit
        )
        event_score = self._feature_keyword_score(features, ("event", "risk", "news"))
        range_score = self._feature_keyword_score(
            features, ("range", "mean", "oscillator", "stoch", "rsi")
        )
        trend_score = self._feature_keyword_score(
            features, ("trend", "momentum", "adx", "breakout")
        )

        persona_key = "trend_follower"
        persona_reason = mode_text or "trend"
        event_terms = ("event", "risk", "catalyst", "shock", "news", "volatility")
        range_terms = (
            "range",
            "mean reversion",
            "range-bound",
            "oscillation",
            "balance",
            "consolidation",
            "chop",
            "sideways",
        )
        trend_terms = ("trend", "impulse", "breakout", "momentum", "swing")

        if event_score >= 0.35 or any(term in combined_text for term in event_terms):
            persona_key = "event_risk"
            persona_reason = "event risk bias"
        elif range_score >= max(trend_score, 0.18) or any(
            term in combined_text for term in range_terms
        ):
            persona_key = "mean_reversion"
            persona_reason = "range bias"
        elif trend_score >= 0.12 or any(term in combined_text for term in trend_terms):
            persona_key = "trend_follower"
            persona_reason = "trend bias"
        focus_terms = self._persona_focus_terms(active)
        return persona_key, persona_reason, focus_terms

    def _persona_confidence_override(
        self, persona_key: str, active: Dict[str, Any]
    ) -> Optional[float]:
        if not persona_key:
            return None
        persona_norm = persona_key.strip().lower()
        if not persona_norm:
            return None

        combined_features: Dict[str, float] = {}
        for source in (active.get("feature_aliases"), active.get("features")):
            if not isinstance(source, dict):
                continue
            for key, value in source.items():
                try:
                    combined_features[str(key).lower()] = float(value)
                except (TypeError, ValueError):
                    continue

        def _feature_value(tokens: Sequence[str]) -> Optional[float]:
            for token in tokens:
                normalized = token.strip().lower()
                if normalized in combined_features:
                    return combined_features[normalized]
            for key, value in combined_features.items():
                if any(term in key for term in tokens):
                    return value
            return None

        if persona_norm != "mean_reversion":
            return None

        trend_strength = _feature_value(("trend_strength", "trend_bias", "trend"))
        rsi_bandwidth = _feature_value(
            (
                "rsi_bandwidth",
                "rsi_band",
                "rsi_range",
                "rsi_balance",
                "rsi_neutral",
                "range_signal",
            )
        )
        if trend_strength is None and rsi_bandwidth is None:
            return None
        trend_strength = max(0.0, min(abs(trend_strength or 0.0), 1.5))
        rsi_bandwidth = max(0.0, min(abs(rsi_bandwidth or 0.0), 1.5))
        range_signal = (rsi_bandwidth * 0.7) - (trend_strength * 0.5)
        if range_signal >= 0.35:
            return -0.07
        if range_signal >= 0.18:
            return -0.045
        if range_signal <= -0.45:
            return 0.01
        if range_signal <= -0.25:
            return -0.005
        return None

    def _apply_persona_hint(self, active: Dict[str, Any], now: float) -> None:
        persona_key, reason, focus_terms = self._select_persona_key(active)
        bias_override = self._persona_confidence_override(persona_key, active)
        entry = advisor_register_persona(
            self._root,
            "playbook",
            persona_key,
            reason=reason,
            focus=focus_terms,
            confidence_bias=bias_override,
            now=now,
        )
        if not entry:
            return
        hint: Dict[str, Any] = {
            "key": entry.get("key"),
            "label": entry.get("label"),
            "focus_keywords": entry.get("focus_keywords", []),
            "confidence_bias": entry.get("confidence_bias", 0.0),
        }
        if entry.get("reason"):
            hint["reason"] = entry.get("reason")
        active["persona_hint"] = hint
        active_persona = advisor_active_persona(self._root, now)
        if active_persona:
            active["persona_active"] = {
                "key": active_persona.get("key"),
                "label": active_persona.get("label"),
                "source": active_persona.get("source"),
                "focus_keywords": active_persona.get("focus_keywords", []),
                "confidence_bias": active_persona.get("confidence_bias", 0.0),
            }

    def _aggressive_condition_slack(self, metric: Optional[str]) -> float:
        if not metric:
            return 0.1
        return float(self._STRUCTURED_SOFTEN_SLACK.get(metric, 0.08))

    def _should_soften_hard_block(
        self, ctx: Dict[str, Any], entry: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        if not self._aggressive_mode:
            return False, None
        note = self._clean_string(entry.get("note") or entry.get("id"))
        if note:
            lowered = note.lower()
            if any(term in lowered for term in self._STRUCTURED_STRICT_TERMS):
                return False, None
        condition = entry.get("condition")
        if not isinstance(condition, dict):
            return True, note
        metric = condition.get("metric")
        if not metric:
            return True, note
        metric_value = self._resolve_metric_value(ctx, metric)
        if metric_value is None:
            return True, note or f"{metric} unavailable"
        try:
            threshold = float(condition.get("value"))
        except (TypeError, ValueError):
            return True, note
        op = condition.get("operator") or ">"
        slack = self._aggressive_condition_slack(metric)
        if op in (">", ">="):
            if metric_value <= threshold + slack:
                reason = note or f"{metric} {metric_value:.2f} ≈ {threshold:.2f}"
                return True, reason
            return False, None
        if op in ("<", "<="):
            if metric_value >= threshold - slack:
                reason = note or f"{metric} {metric_value:.2f} ≈ {threshold:.2f}"
                return True, reason
            return False, None
        if op == "between":
            try:
                upper = float(condition.get("value2"))
            except (TypeError, ValueError):
                return True, note
            low = min(threshold, upper)
            high = max(threshold, upper)
            if not (low <= metric_value <= high):
                return False, None
            distance = min(metric_value - low, high - metric_value)
            if distance <= slack:
                reason = note or f"{metric} near boundary"
                return True, reason
            return False, None
        return True, note

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
            "plan": 0.45,
            "trend": 0.45,
            "postmortem": 0.2,
        }
        self._skip_limit_plan = 1.85
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
