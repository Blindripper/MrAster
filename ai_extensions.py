"""AI-driven learning helpers for MrAster bot."""
from __future__ import annotations

from datetime import datetime
import math
import time
from collections import deque
from typing import Any, Callable, Deque, Dict, Iterable, List, Optional, Tuple

POSTMORTEM_FEATURE_MAP: Dict[str, str] = {
    "trend_break": "pm_trend_break",
    "news_driver": "pm_news_driver",
    "liquidity_gap": "pm_liquidity_gap",
    "execution_delay": "pm_execution_delay",
    "sentiment_conflict": "pm_sentiment_conflict",
    "macro_event": "pm_macro_event",
}
POSTMORTEM_EXTRA_FEATURES = (
    "pm_volatility_bias",
    "pm_execution_quality",
    "pm_liquidity_profile",
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
                "last_anomaly": {},
            },
        )
        self._request_fn = request_fn
        self._min_trades = 4
        self._ai_interval = 5 * 60
        self._history_cap = 220
        existing_history = self._state.get("history")
        if isinstance(existing_history, list):
            self._history: Deque[Dict[str, Any]] = deque(existing_history, maxlen=self._history_cap)
        else:
            self._history = deque(maxlen=self._history_cap)
            if isinstance(existing_history, deque):
                for item in list(existing_history)[-self._history_cap:]:
                    self._history.append(item)
        self._state["history"] = list(self._history)

    def observe(self, trade: Dict[str, Any], features: Dict[str, float]) -> None:
        record = {
            "ts": time.time(),
            "symbol": trade.get("symbol"),
            "side": trade.get("side"),
            "bucket": trade.get("bucket"),
            "pnl_r": float(trade.get("pnl_r", 0.0) or 0.0),
            "features": {k: float(v) for k, v in (features or {}).items()},
        }
        self._history.append(record)
        self._state["history"] = list(self._history)
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
        history: List[Dict[str, Any]] = list(self._history)
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

    def _detect_anomaly(self, history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if len(history) < self._min_trades:
            return None
        recent = history[-40:]
        if len(recent) < self._min_trades:
            return None
        pnl_values: List[float] = [float(item.get("pnl_r", 0.0) or 0.0) for item in recent]
        mean = sum(pnl_values) / max(len(pnl_values), 1)
        variance = sum((value - mean) ** 2 for value in pnl_values) / max(len(pnl_values), 1)
        std = math.sqrt(max(variance, 1e-9))
        top_outlier: Optional[Tuple[float, Dict[str, Any], float]] = None
        if std > 1e-4:
            for entry in recent:
                value = float(entry.get("pnl_r", 0.0) or 0.0)
                z_score = (value - mean) / std
                if abs(z_score) >= 1.45:
                    if not top_outlier or abs(z_score) > top_outlier[0]:
                        top_outlier = (abs(z_score), entry, z_score)
        bucket_map: Dict[str, List[float]] = {}
        symbol_map: Dict[str, List[float]] = {}
        for entry in recent:
            bucket = str(entry.get("bucket") or "S").upper()
            symbol = str(entry.get("symbol") or "*").upper()
            pnl = float(entry.get("pnl_r", 0.0) or 0.0)
            bucket_map.setdefault(bucket, []).append(pnl)
            symbol_map.setdefault(symbol, []).append(pnl)
        bucket_signal: Optional[Tuple[str, float]] = None
        for bucket, values in bucket_map.items():
            if len(values) < max(2, self._min_trades // 2):
                continue
            avg_bucket = sum(values) / len(values)
            if avg_bucket < mean - 0.35:
                bucket_signal = (bucket, avg_bucket)
                break
        symbol_signal: Optional[Tuple[str, float]] = None
        for symbol, values in symbol_map.items():
            if len(values) < max(2, self._min_trades // 2):
                continue
            avg_symbol = sum(values) / len(values)
            if avg_symbol < mean - 0.4:
                symbol_signal = (symbol, avg_symbol)
                break
        regime_flags: List[str] = []
        def _feature_avg(feature: str) -> Optional[float]:
            vals: List[float] = []
            for entry in recent:
                features = entry.get("features") or {}
                if not isinstance(features, dict):
                    continue
                raw = features.get(feature)
                if raw is None:
                    continue
                try:
                    vals.append(float(raw))
                except (TypeError, ValueError):
                    continue
            if not vals:
                return None
            return sum(vals) / len(vals)

        avg_event_risk = _feature_avg("sentinel_event_risk")
        if avg_event_risk is not None and avg_event_risk > 0.6:
            regime_flags.append("high_event_risk")
        avg_onchain = _feature_avg("sentinel_onchain_pressure")
        if avg_onchain is not None:
            if avg_onchain > 0.35:
                regime_flags.append("onchain_pressure")
            elif avg_onchain < -0.35:
                regime_flags.append("onchain_outflow")
        avg_social = _feature_avg("sentinel_social_sentiment")
        if avg_social is not None:
            if avg_social > 0.35:
                regime_flags.append("bullish_sentiment")
            elif avg_social < -0.35:
                regime_flags.append("bearish_sentiment")

        if top_outlier:
            _, entry, z_val = top_outlier
            anomaly = {
                "trigger": "z_score",
                "z_score": round(float(z_val), 3),
                "symbol": entry.get("symbol"),
                "bucket": entry.get("bucket"),
                "pnl_r": entry.get("pnl_r"),
                "mean": round(mean, 3),
                "std": round(std, 3),
                "sample_size": len(pnl_values),
            }
        elif bucket_signal:
            anomaly = {
                "trigger": "bucket_drawdown",
                "bucket": bucket_signal[0],
                "bucket_mean": round(bucket_signal[1], 3),
                "mean": round(mean, 3),
                "sample_size": len(pnl_values),
            }
        elif symbol_signal:
            anomaly = {
                "trigger": "symbol_drawdown",
                "symbol": symbol_signal[0],
                "symbol_mean": round(symbol_signal[1], 3),
                "mean": round(mean, 3),
                "sample_size": len(pnl_values),
            }
        else:
            return None

        if regime_flags:
            anomaly["regime"] = regime_flags
        features_tail = recent[-1].get("features") if recent else None
        if isinstance(features_tail, dict):
            sentinel_label = features_tail.get("sentinel_label")
            if sentinel_label:
                anomaly.setdefault("meta", {})["sentinel_label"] = sentinel_label
        symbol = anomaly.get("symbol") or (recent[-1].get("symbol") if recent else None)
        bucket = anomaly.get("bucket") or (recent[-1].get("bucket") if recent else None)
        signature = f"{symbol}:{bucket}:{anomaly.get('trigger')}"
        anomaly["signature"] = signature
        return anomaly

    def _maybe_request_ai(self) -> None:
        history: List[Dict[str, Any]] = list(self._history)
        if len(history) < self._min_trades:
            return
        now = time.time()
        if now - float(self._state.get("last_ai", 0.0) or 0.0) < self._ai_interval:
            return
        anomaly = self._detect_anomaly(history)
        if not anomaly:
            return
        last_anomaly = self._state.get("last_anomaly")
        if isinstance(last_anomaly, dict):
            last_sig = last_anomaly.get("signature")
            last_ts = float(last_anomaly.get("ts", 0.0) or 0.0)
            if (
                last_sig
                and last_sig == anomaly.get("signature")
                and now - last_ts < max(self._ai_interval * 0.8, 90.0)
            ):
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
        if anomaly:
            payload["anomaly"] = {
                key: value
                for key, value in anomaly.items()
                if key not in {"signature", "ts"}
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
        anomaly["ts"] = time.time()
        self._state["last_anomaly"] = anomaly

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
        self._refresh_interval = 8 * 60
        self._bootstrap_pending = True
        self._bootstrap_deadline = time.time() + 120.0
        self._bootstrap_retry = 90.0
        self._bootstrap_cooldown_until = 0.0
        self._event_cb = event_cb
        self._state.setdefault("regime_snapshot", {})

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

        return strategy or None

    def maybe_refresh(self, snapshot: Dict[str, Any]) -> None:
        active = self._state.get("active", {})
        now = time.time()
        last_raw = active.get("refreshed", 0.0)
        last = self._parse_timestamp(last_raw)
        if isinstance(snapshot, dict):
            regime_snapshot = snapshot.get("regime")
            if isinstance(regime_snapshot, dict):
                self._state["regime_snapshot"] = regime_snapshot
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
        if snapshot.get("recent_trades"):
            return True
        budget = snapshot.get("budget")
        if isinstance(budget, dict) and budget:
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
        if isinstance(features, dict):
            for key, value in features.items():
                ctx[key] = float(value)
        regime_snapshot = self._state.get("regime_snapshot")
        if isinstance(regime_snapshot, dict):
            for key, value in regime_snapshot.items():
                try:
                    if key not in ctx:
                        ctx[key] = float(value)
                except (TypeError, ValueError):
                    continue
        ctx["playbook_mode"] = active.get("mode", "baseline")
        ctx["playbook_bias"] = active.get("bias", "neutral")
        ctx["playbook_size_bias"] = float(
            (active.get("size_bias", {}) or {}).get(str(ctx.get("side") or "").upper(), 1.0)
        )
        confidence = active.get("confidence")
        try:
            if confidence is not None:
                ctx["playbook_confidence"] = float(confidence)
        except (TypeError, ValueError):
            pass
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
            if isinstance(signals, list):
                for idx, signal in enumerate(signals[:3], start=1):
                    if isinstance(signal, str) and signal.strip():
                        ctx[f"playbook_signal_{idx}"] = signal
            actions = strategy.get("actions")
            if isinstance(actions, list):
                for idx, action in enumerate(actions[:3], start=1):
                    if not isinstance(action, dict):
                        continue
                    title = action.get("title")
                    detail = action.get("detail")
                    trigger = action.get("trigger")
                    base_key = f"playbook_action_{idx}"
                    if isinstance(title, str) and title.strip():
                        ctx[f"{base_key}_title"] = title
                    if isinstance(detail, str) and detail.strip():
                        ctx[f"{base_key}_detail"] = detail
                    if isinstance(trigger, str) and trigger.strip():
                        ctx[f"{base_key}_trigger"] = trigger

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
        if confidence is not None:
            active["confidence"] = confidence
        if reason_text:
            active["reason"] = reason_text
        if strategy:
            active["strategy"] = strategy
            if "reason" not in active and strategy.get("why_active"):
                active["reason"] = strategy["why_active"]
        request_id = payload.get("request_id")
        if isinstance(request_id, str):
            token = request_id.strip()
            if token:
                active["request_id"] = token
        return active


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
                "opportunity_cost": 0.0,
                "slippage_cost": 0.0,
            },
        )
        sym_state["count"] = int(sym_state.get("count", 0)) + 1
        sym_state["reward"] = float(sym_state.get("reward", 0.0) or 0.0) + pnl_r
        # decay extended metrics to keep them responsive
        for key in ("opportunity_cost", "slippage_cost"):
            try:
                current = float(sym_state.get(key, 0.0) or 0.0)
            except (TypeError, ValueError):
                current = 0.0
            sym_state[key] = current * 0.96
        recent = sym_state.setdefault("recent_pnl", [])
        if isinstance(recent, list):
            recent.append(pnl_r)
            if len(recent) > self._reward_window:
                del recent[: len(recent) - self._reward_window]
            sym_state["recent_pnl"] = recent
        context = trade.get("context") if isinstance(trade.get("context"), dict) else {}
        expected_r = None
        if context:
            expected_r = self._safe_float(context.get("expected_r"))
        if expected_r is None:
            expected_r = self._safe_float(trade.get("expected_r"))
        opp_cost = self._safe_float(trade.get("opportunity_cost"))
        slip_cost = self._safe_float(trade.get("slippage"))
        if opp_cost is None and expected_r is not None and expected_r > 0 and pnl_r <= 0:
            opp_cost = expected_r
        if slip_cost is None and expected_r is not None and pnl_r > 0 and expected_r > pnl_r:
            slip_cost = expected_r - pnl_r
        if opp_cost is None and context:
            opp_cost = self._safe_float(context.get("opportunity_cost"))
        if slip_cost is None and context:
            slip_cost = self._safe_float(context.get("slippage_cost"))
        if opp_cost is not None and opp_cost > 0:
            sym_state["opportunity_cost"] = float(sym_state.get("opportunity_cost", 0.0) or 0.0) + float(max(opp_cost, 0.0))
        if slip_cost is not None and slip_cost > 0:
            sym_state["slippage_cost"] = float(sym_state.get("slippage_cost", 0.0) or 0.0) + float(max(slip_cost, 0.0))
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
        try:
            snapshot["opportunity_cost"] = float(sym_state.get("opportunity_cost", 0.0) or 0.0)
            snapshot["slippage_cost"] = float(sym_state.get("slippage_cost", 0.0) or 0.0)
        except (TypeError, ValueError):
            snapshot["opportunity_cost"] = 0.0
            snapshot["slippage_cost"] = 0.0
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
                "opportunity_cost": 0.0,
                "slippage_cost": 0.0,
            },
        )
        for key in ("opportunity_cost", "slippage_cost"):
            try:
                sym_state[key] = float(sym_state.get(key, 0.0) or 0.0) * 0.98
            except (TypeError, ValueError):
                sym_state[key] = 0.0
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
            expected_r = self._safe_float(meta.get("expected_r") or meta.get("expected_return"))
            opp_meta = self._safe_float(meta.get("opportunity_cost"))
            if expected_r is None:
                expected_r = self._safe_float(meta.get("edge"))
            if expected_r and expected_r > 0:
                sym_state["opportunity_cost"] = float(sym_state.get("opportunity_cost", 0.0) or 0.0) + expected_r
            elif opp_meta and opp_meta > 0:
                sym_state["opportunity_cost"] = float(sym_state.get("opportunity_cost", 0.0) or 0.0) + opp_meta
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
        opp_cost = float(sym_state.get("opportunity_cost", 0.0) or 0.0)
        slip_cost = float(sym_state.get("slippage_cost", 0.0) or 0.0)
        bias = 1.0 + avg * 0.4 - skip_penalty * self._skip_penalty_factor
        if opp_cost > 0:
            bias += min(0.5, opp_cost * 0.12)
        if slip_cost > 0:
            bias += min(0.35, slip_cost * 0.1)
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
