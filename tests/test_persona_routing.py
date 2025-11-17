import math
import os
import sys
from typing import Optional

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ai_extensions import advisor_active_persona
from aster_multi_bot import AITradeAdvisor, DailyBudgetTracker, NewsTrendSentinel


class _DummyExchange:
    def __init__(self, price_change: float, high: float, low: float, last: float) -> None:
        self.price_change = price_change
        self.high = high
        self.low = low
        self.last = last

    def get_ticker_24hr(self, symbol: Optional[str] = None) -> dict:
        return {
            "symbol": symbol or "BTCUSDT",
            "priceChangePercent": str(self.price_change),
            "quoteVolume": "2500000",
            "takerBuyQuoteVolume": "800000",
            "lastPrice": str(self.last),
            "highPrice": str(self.high),
            "lowPrice": str(self.low),
        }


def test_sentinel_registers_event_persona():
    state: dict = {}
    exchange = _DummyExchange(price_change=12.5, high=132.0, low=78.0, last=100.0)
    sentinel = NewsTrendSentinel(exchange, state, enabled=True)
    sentinel.evaluate("BTCUSDT")
    persona = advisor_active_persona(state)
    assert persona is not None
    assert persona.get("key") == "event_risk"
    assert persona.get("source") == "sentinel"
    focus_terms = persona.get("focus_keywords") or []
    assert any("event" in term for term in focus_terms)


def test_plan_overrides_apply_persona_bias():
    state: dict = {}
    budget = DailyBudgetTracker(state, limit=100.0, strict=False)
    advisor = AITradeAdvisor(
        api_key="dummy",
        model="gpt-4o-mini",
        budget=budget,
        state=state,
        enabled=False,
    )
    fallback = {
        "symbol": "BTCUSDT",
        "take": True,
        "decision": "take",
        "size_multiplier": 1.0,
        "sl_multiplier": 1.0,
        "tp_multiplier": 1.0,
        "leverage": 5.0,
    }
    parsed = {"confidence": 0.42}
    request_payload = {
        "symbol": "BTCUSDT",
        "persona": {
            "key": "mean_reversion",
            "label": "Mean-Reversion",
            "confidence_bias": -0.1,
            "focus": ["range", "fade"],
            "source": "playbook",
        },
    }
    plan = advisor._apply_plan_overrides(fallback, parsed, request_payload=request_payload)
    assert plan["advisor_persona"] == "mean_reversion"
    assert plan["advisor_persona_label"] == "Mean-Reversion"
    assert math.isclose(plan["confidence"], 0.32, rel_tol=1e-6)
    assert plan.get("advisor_persona_confidence_bias_applied") == pytest.approx(-0.1)
    assert "range" in plan.get("advisor_persona_focus", [])


def test_mean_reversion_bias_strengthens_in_range_env():
    state: dict = {}
    budget = DailyBudgetTracker(state, limit=100.0, strict=False)
    advisor = AITradeAdvisor("key", "gpt-4.1", budget, state, enabled=False)
    fallback = {"symbol": "BTCUSDT", "take": True}
    parsed = {"confidence": 0.5}
    request_payload = {
        "persona": {"key": "mean_reversion", "confidence_bias": -0.02},
        "stats": {
            "atr_pct": 0.007,
            "htf_trend_up": 0.0,
            "htf_trend_down": 0.0,
            "rsi": 49.5,
        },
    }
    plan = advisor._apply_plan_overrides(fallback, parsed, request_payload=request_payload)
    assert plan["advisor_persona_confidence_bias_applied"] == pytest.approx(-0.077, rel=1e-6)
    assert plan["confidence"] == pytest.approx(0.423, rel=1e-6)


def test_mean_reversion_bias_softens_in_trend_env():
    state: dict = {}
    budget = DailyBudgetTracker(state, limit=100.0, strict=False)
    advisor = AITradeAdvisor("key", "gpt-4.1", budget, state, enabled=False)
    fallback = {"symbol": "BTCUSDT", "take": True}
    parsed = {"confidence": 0.5}
    request_payload = {
        "persona": {"key": "mean_reversion", "confidence_bias": -0.02},
        "stats": {
            "atr_pct": 0.036,
            "htf_trend_up": 1.0,
            "rsi": 69.0,
        },
    }
    plan = advisor._apply_plan_overrides(fallback, parsed, request_payload=request_payload)
    assert plan["advisor_persona_confidence_bias_applied"] == pytest.approx(0.04, rel=1e-6)
    assert plan["confidence"] == pytest.approx(0.54, rel=1e-6)


def test_sentinel_clears_persona_when_risk_drops():
    state: dict = {}
    exchange = _DummyExchange(price_change=10.0, high=140.0, low=70.0, last=100.0)
    sentinel = NewsTrendSentinel(exchange, state, enabled=True)
    sentinel.evaluate("BTCUSDT")
    persona = advisor_active_persona(state)
    assert persona and persona.get("key") == "event_risk"

    exchange.price_change = 1.2
    exchange.high = 101.0
    exchange.low = 99.0
    exchange.last = 100.0
    sentinel._last_payload.clear()  # type: ignore[attr-defined]  # reset cache for fresh evaluation
    sentinel._ticker_cache.clear()  # type: ignore[attr-defined]  # reset cached ticker snapshot
    payload_low = sentinel.evaluate("BTCUSDT")
    assert float(payload_low.get("event_risk", 0.0)) < 0.6

    persona_after = advisor_active_persona(state)
    sources = state.get("advisor_persona", {}).get("sources", {})
    assert "sentinel" not in sources or sources["sentinel"].get("key") != "event_risk"
    assert persona_after is None or persona_after.get("source") != "sentinel"


def test_tokenize_focus_term_handles_compound_terms():
    tokens = AITradeAdvisor._tokenize_focus_term(
        "Mean Reversion bounce near VWAP and oversold Bollinger bands std dev break"
    )
    assert {"mean", "reversion", "bounce", "vwap", "oversold"}.issubset(tokens)
    assert {"meanreversion", "mean_reversion", "stddev", "bollinger"}.issubset(tokens)


def test_playbook_focus_terms_trigger_range_persona_feature():
    state: dict = {}
    budget = DailyBudgetTracker(state, limit=50.0, strict=False)
    advisor = AITradeAdvisor(
        api_key="dummy",
        model="gpt-4o-mini",
        budget=budget,
        state=state,
        enabled=False,
    )
    ctx = {
        "playbook_action_focus_terms": [
            "mean reversion bounce reverting to VWAP while oversold on std dev"
        ]
    }
    advisor._inject_persona_focus_features(ctx)
    assert ctx.get("persona_focus_range", 0.0) == pytest.approx(1.0)
