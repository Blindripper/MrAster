import time

import pytest

from ai_extensions import PlaybookManager


def _manager():
    state = {}
    return PlaybookManager(state, request_fn=lambda kind, payload: None)


def test_playbook_collects_symbol_directives_from_text_sources():
    mgr = _manager()
    now = time.time()
    payload = {
        "mode": "baseline",
        "bias": "neutral",
        "size_bias": {"BUY": 1.0, "SELL": 1.0},
        "sl_bias": 1.0,
        "tp_bias": 1.0,
        "features": {},
        "strategy": {
            "market_signals": [
                "CUDISUSDT has a warning due to an 8.1% drop in 24h, but overall event risk is manageable.",
            ],
        },
        "risk_controls": [
            "Avoid assets with recent sharp drawdowns (e.g., CUDISUSDT) unless recovery signals appear.",
        ],
    }
    active = mgr._normalize_playbook(payload, now)  # pylint: disable=protected-access
    directives = active.get("symbol_directives")
    assert isinstance(directives, dict)
    entry = directives.get("CUDISUSDT")
    assert entry is not None
    assert entry.get("label") == "avoid"
    assert entry.get("level", 0.0) >= 2.0
    assert abs(entry.get("drop_pct", 0.0) - 8.1) < 1e-6


def test_playbook_injects_symbol_directive_into_context():
    mgr = _manager()
    now = time.time()
    payload = {
        "mode": "baseline",
        "bias": "neutral",
        "size_bias": {"BUY": 1.0, "SELL": 1.0},
        "sl_bias": 1.0,
        "tp_bias": 1.0,
        "features": {},
        "risk_controls": [
            "Avoid assets with recent sharp drawdowns (e.g., CUDISUSDT) unless recovery signals appear.",
        ],
    }
    active = mgr._normalize_playbook(payload, now)  # pylint: disable=protected-access
    mgr._state["active"] = active  # pylint: disable=protected-access
    ctx = {"side": "BUY", "symbol": "CUDISUSDT"}
    mgr.inject_context(ctx)
    assert ctx["playbook_symbol_directive"] == "avoid"
    assert ctx["playbook_symbol_directive_level"] >= 2.0
    assert "playbook_symbol_note" in ctx or "playbook_symbol_directive_source" in ctx


def test_playbook_risk_bias_tracks_mode_bias_and_confidence():
    mgr = _manager()
    now = time.time()
    payload = {
        "mode": "defensive posture",
        "bias": "risk_off",
        "size_bias": {"BUY": 0.9, "SELL": 0.9},
        "sl_bias": 0.9,
        "tp_bias": 0.9,
        "features": {},
        "confidence": 0.2,
    }
    active = mgr._normalize_playbook(payload, now)  # pylint: disable=protected-access
    assert pytest.approx(active["risk_bias"], rel=0.01) == 0.56
    mgr._state["active"] = active  # pylint: disable=protected-access
    ctx = {"side": "BUY", "symbol": "BTCUSDT"}
    mgr.inject_context(ctx)
    assert pytest.approx(ctx["playbook_risk_bias"], rel=0.01) == active["risk_bias"]
    assert pytest.approx(ctx["playbook_confidence"], rel=0.01) == 0.2
