import json
import os
import sys
from typing import Any, Dict

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from aster_multi_bot import AITradeAdvisor, DailyBudgetTracker  # noqa: E402


def _make_advisor() -> AITradeAdvisor:
    state: Dict[str, Any] = {}
    budget = DailyBudgetTracker(state, limit=5.0, strict=True)
    advisor = AITradeAdvisor("key", "gpt-4o", budget, state, enabled=False)
    return advisor


def _sample_trade() -> Dict[str, Any]:
    context: Dict[str, Any] = {
        "adx": 74.4,
        "ema_fast": 0.2481,
        "ema_slow": 0.2523,
        "policy_bucket": "S",
        "policy_size_multiplier": 1.5,
        "ai_plan_origin": "signal",
        "ai_priority_side_hint": "SELL",
        "ai_confidence": 0.83,
        "sentinel_label": "yellow",
        "sentinel_event_risk": 0.78,
        "sentinel_hype": 1.0,
        "sentinel_factor": 0.9,
        "budget_skip_top_reason": "Sentinel event risk is high.",
        "budget_skip_latest_reason": "Active positions count is high.",
        "open_positions": {
            "BTCUSDT": -12.0,
            "ETHUSDT": -5.0,
            "SOLUSDT": 2.5,
            "BNBUSDT": 1.0,
            "ADAUSDT": -3.0,
            "DOGEUSDT": 4.0,
        },
        "ai_take_profit": 0.24156,
    }
    return {
        "symbol": "SAPIENUSDT",
        "side": "SELL",
        "qty": 812.0,
        "entry": 0.24552,
        "exit": 0.24228,
        "pnl": 2.63,
        "pnl_r": 6.64,
        "opened_at": 1762815061.45,
        "closed_at": 1762815896.26,
        "bucket": "S",
        "context": context,
        "ai": {
            "decision": "take",
            "decision_reason": "strong_trend",
            "decision_note": "trend confirmed",
            "take": True,
            "confidence": 0.83,
            "size_multiplier": 2.3,
            "sl_multiplier": 1.2,
            "tp_multiplier": 1.0,
            "leverage": 4.5,
            "entry_price": 0.24629,
            "stop_loss": 0.24949,
            "take_profit": 0.24156,
            "fasttp_overrides": {
                "enabled": True,
                "min_r": 0.14,
                "ret1": 0.002,
                "ret3": 0.0035,
                "snap_atr": 0.7,
            },
            "extra_blob": {"ignored": "value"},
        },
    }


def test_postmortem_payload_trims_context() -> None:
    advisor = _make_advisor()
    trade = _sample_trade()

    payload = advisor._postmortem_request_payload(trade)

    assert payload["symbol"] == "SAPIENUSDT"
    assert payload["side"] == "SELL"
    assert payload["pnl"] == pytest.approx(2.63)
    assert payload["pnl_r"] == pytest.approx(6.64)
    assert payload["duration_s"] > 0

    stats = payload.get("stats")
    assert isinstance(stats, dict)
    assert stats.get("adx") == pytest.approx(74.4, rel=1e-3)
    assert "ai_take_profit" not in stats

    sentinel = payload.get("sentinel")
    assert sentinel == {"label": "yellow", "event_risk": pytest.approx(0.78), "hype_score": pytest.approx(1.0), "factor": pytest.approx(0.9)}

    context_meta = payload.get("context")
    assert isinstance(context_meta, dict)
    assert "ai_take_profit" not in context_meta
    assert context_meta.get("policy_bucket") == "S"
    assert len(context_meta.get("open_positions", {})) <= 5

    ai_decision = payload.get("ai_decision")
    assert isinstance(ai_decision, dict)
    assert ai_decision.get("take") is True
    assert ai_decision.get("size_multiplier") == pytest.approx(2.3)
    assert ai_decision.get("fasttp_overrides", {}).get("enabled") is True


def test_generate_postmortem_uses_compact_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    advisor = _make_advisor()
    advisor.enabled = True
    trade = _sample_trade()

    captured: Dict[str, Any] = {}

    def fake_chat(system_prompt: str, user_prompt: str, **kwargs: Any) -> str:
        captured["system_prompt"] = system_prompt
        captured["user_prompt"] = user_prompt
        req_id = kwargs.get("request_meta", {}).get("request_id", "req")
        analysis = (
            "Strong short captured trend continuation. Entry aligned with EMA stack, ADX above 70 and "
            "bearish slopes signalled durable downside momentum despite yellow sentinel volatility backdrop. "
            "Execution avoided slippage and liquidity stayed balanced, so performance outpaced plan."
        )
        return json.dumps(
            {
                "request_id": req_id,
                "analysis": analysis,
                "feature_scores": {"adx": 0.8},
                "volatility_descriptor": "spike",
                "execution_descriptor": "efficient",
                "liquidity_descriptor": "sufficient",
            }
        )

    monkeypatch.setattr(advisor, "_chat", fake_chat)

    result = advisor.generate_postmortem(trade)

    assert result is not None
    assert "request_id" in result
    assert result.get("analysis", "").startswith("Strong short")
    assert "_ai_request" in result
    assert "_ai_response" in result

    payload = json.loads(captured["user_prompt"])
    assert payload["request_id"] == result["request_id"]
    assert "context" in payload
    assert "sentinel" in payload
    assert "ai_take_profit" not in json.dumps(payload)

