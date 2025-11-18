import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from aster_multi_bot import AITradeAdvisor, DailyBudgetTracker
from ai_extensions import advisor_register_persona


def _advisor():
    state: dict = {}
    budget = DailyBudgetTracker(state, limit=100.0, strict=False)
    advisor = AITradeAdvisor(
        api_key="dummy",
        model="gpt-4o-mini",
        budget=budget,
        state=state,
        enabled=False,
    )
    return advisor, state


def test_inject_context_adds_persona_focus_features():
    advisor, state = _advisor()
    advisor_register_persona(
        state,
        "playbook",
        "trend_follower",
        focus=["Breakout bias", "momentum"],
    )
    ctx: dict = {"symbol": "BTCUSDT"}
    advisor.inject_context_features("BTCUSDT", ctx)
    assert ctx.get("persona_focus_trend", 0.0) > 0.0
    assert "persona_focus_range" not in ctx or ctx["persona_focus_range"] >= 0.0


def test_inject_context_adds_guardrail_reason_features():
    advisor, state = _advisor()
    active = {
        "mode": "defensive",
        "bias": "cautious",
        "size_bias": {"BUY": 0.9, "SELL": 0.85},
        "sl_bias": 0.9,
        "tp_bias": 1.05,
        "features": {},
        "refreshed": time.time(),
        "structured_actions": [
            {
                "id": "spread_guardrail",
                "effect": "size_multiplier",
                "multiplier": 0.75,
                "note": "Spread widening guardrail",
            },
            {
                "id": "tighten_sl",
                "effect": "sl_multiplier",
                "multiplier": 0.8,
                "note": "Volatility spike tighten stop-loss",
            },
            {
                "id": "trim_tp",
                "effect": "tp_multiplier",
                "multiplier": 0.9,
                "note": "Take profit early on event risk",
            },
        ],
    }
    advisor.playbook_manager._state["active"] = active  # pylint: disable=protected-access
    ctx = {
        "symbol": "BTCUSDT",
        "side": "BUY",
        "sentinel_event_risk": 0.65,
        "atr_pct": 0.55,
    }
    advisor.inject_context_features("BTCUSDT", ctx)
    assert ctx.get("playbook_guardrail_reason_spread", 0.0) > 0.0
    assert ctx.get("playbook_guardrail_reason_sl", 0.0) > 0.0
    assert ctx.get("playbook_guardrail_reason_tp", 0.0) > 0.0
    assert ctx.get("playbook_guardrail_reason_event", 0.0) >= 0.6
    assert ctx.get("playbook_guardrail_reason_volatility", 0.0) >= 0.5
