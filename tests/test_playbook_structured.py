import time

from ai_extensions import PlaybookManager


def _noop_request(kind, payload):
    return None


def _base_active_state():
    return {
        "mode": "baseline",
        "bias": "neutral",
        "size_bias": {"BUY": 1.0, "SELL": 1.0},
        "sl_bias": 1.0,
        "tp_bias": 1.0,
        "features": {},
        "refreshed": time.time(),
    }


def test_playbook_structured_hard_block_trigger():
    state = {}
    mgr = PlaybookManager(state, request_fn=_noop_request)
    active = _base_active_state()
    active["structured_risk_controls"] = [
        {
            "id": "event_risk_block",
            "effect": "hard_block",
            "condition": {"metric": "event_risk", "operator": ">", "value": 0.8},
            "note": "Event risk extreme",
        }
    ]
    mgr._state["active"] = active  # pylint: disable=protected-access

    ctx = {"side": "BUY", "sentinel_event_risk": 0.91}
    mgr.inject_context(ctx)

    assert ctx["playbook_structured_hard_block"] is True
    assert "Event risk" in ctx["playbook_structured_block_reason"]


def test_playbook_structured_size_and_sl_tp_adjustments():
    state = {}
    mgr = PlaybookManager(state, request_fn=_noop_request)
    active = _base_active_state()
    active["structured_actions"] = [
        {
            "id": "hype_reduce_size",
            "effect": "size_multiplier",
            "multiplier": 0.75,
            "condition": {"metric": "hype", "operator": ">=", "value": 0.7},
            "note": "High hype reduce size",
        },
        {
            "id": "volatility_tighten_sl",
            "effect": "sl_multiplier",
            "multiplier": 0.9,
            "condition": {"metric": "volatility", "operator": ">", "value": 0.4},
        },
        {
            "id": "trend_extend_tp",
            "effect": "tp_multiplier",
            "multiplier": 1.2,
            "condition": {"metric": "trend_strength", "operator": ">", "value": 0.1},
        },
    ]
    active["structured_risk_controls"] = [
        {"id": "cap_size", "effect": "size_cap", "multiplier": 1.3}
    ]
    mgr._state["active"] = active  # pylint: disable=protected-access

    ctx = {
        "side": "SELL",
        "sentinel_hype": 0.78,
        "atr_pct": 0.55,
        "trend": 0.18,
        "sentinel_event_risk": 0.2,
    }
    mgr.inject_context(ctx)

    assert abs(ctx["playbook_structured_size_multiplier"] - 0.75) < 1e-6
    assert abs(ctx["playbook_structured_sl_multiplier"] - 0.9) < 1e-6
    assert abs(ctx["playbook_structured_tp_multiplier"] - 1.2) < 1e-6
    assert abs(ctx["playbook_structured_size_cap"] - 1.3) < 1e-6
    assert "size×0.75" in " ".join(ctx.get("playbook_structured_notes", []))


def test_high_preset_softens_marginal_hard_block(monkeypatch):
    monkeypatch.setenv("ASTER_PRESET_MODE", "high")
    state = {}
    mgr = PlaybookManager(state, request_fn=_noop_request)
    active = _base_active_state()
    active["structured_risk_controls"] = [
        {
            "id": "event_risk_block",
            "effect": "hard_block",
            "condition": {"metric": "event_risk", "operator": ">", "value": 0.8},
            "note": "Event risk elevated",
        }
    ]
    mgr._state["active"] = active  # pylint: disable=protected-access

    ctx = {"side": "BUY", "sentinel_event_risk": 0.82}
    mgr.inject_context(ctx)

    assert ctx.get("playbook_structured_hard_block") is not True
    assert ctx.get("playbook_structured_soft_block") is True
    assert ctx.get("playbook_structured_size_multiplier", 1.0) < 1.0
    assert "soft×" in " ".join(ctx.get("playbook_structured_notes", []))
    assert "Event risk" in ctx.get("playbook_structured_soft_reason", "")


def test_high_preset_retains_block_when_risk_extreme(monkeypatch):
    monkeypatch.setenv("ASTER_PRESET_MODE", "high")
    state = {}
    mgr = PlaybookManager(state, request_fn=_noop_request)
    active = _base_active_state()
    active["structured_risk_controls"] = [
        {
            "id": "event_risk_block",
            "effect": "hard_block",
            "condition": {"metric": "event_risk", "operator": ">", "value": 0.8},
            "note": "Event risk extreme",
        }
    ]
    mgr._state["active"] = active  # pylint: disable=protected-access

    ctx = {"side": "BUY", "sentinel_event_risk": 0.97}
    mgr.inject_context(ctx)

    assert ctx["playbook_structured_hard_block"] is True
    assert ctx.get("playbook_structured_soft_block") is not True
