import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from aster_multi_bot import Strategy


class _DummyBudgetTracker:
    def __init__(self, snapshot):
        self._snapshot = snapshot

    def snapshot(self):
        return dict(self._snapshot)


class _DummyPlaybookManager:
    def __init__(self, active_payload):
        self._active = active_payload

    def active(self):
        return dict(self._active)


def _sentinel_entry(event_risk, hype_score, *, label, updated, hard_block=None, size_factor=None, events=None):
    payload = {
        "event_risk": event_risk,
        "hype_score": hype_score,
        "label": label,
        "updated": updated,
    }
    actions = {}
    if size_factor is not None:
        actions["size_factor"] = size_factor
    if hard_block is not None:
        actions["hard_block"] = bool(hard_block)
    if actions:
        payload["actions"] = actions
    if events:
        payload["events"] = events
    return payload


def test_playbook_snapshot_includes_overview_budget_and_playbook():
    technical_state = {
        f"SYM{i}USDT": {
            "ts": float(i),
            "rsi": rsi,
            "adx": adx,
            "atr_pct": atr,
            "bb_width": bb,
            "supertrend_dir": st,
            "htf_trend": htf,
        }
        for i, (rsi, adx, atr, bb, st, htf) in enumerate(
            [
                (62, 18, 0.015, 0.05, 1, 0),
                (44, 22, 0.03, 0.06, -1, 0),
                (55, 25, 0.028, 0.055, 0, 1),
                (41, 19, 0.018, 0.052, 0, -1),
                (58, 17, 0.032, 0.058, 1, 0),
                (50, 21, 0.026, 0.057, 0, 0),
                (43, 23, 0.022, 0.054, -1, 0),
            ],
            start=1,
        )
    }

    sentinel_state = {
        f"S{i}USDT": _sentinel_entry(
            event_risk,
            hype_score,
            label=label,
            updated=1_000 + i,
            hard_block=hard_block,
            size_factor=size_factor,
            events=[
                {"title": "Event one", "severity": "info", "time": 1700000000},
                {"title": "Second", "severity": "warning", "time": 1700003600},
                {"title": "Third", "severity": "warning", "time": 1700007200},
            ],
        )
        for i, (event_risk, hype_score, label, hard_block, size_factor) in enumerate(
            [
                (0.10, 0.50, "green", False, 1.00),
                (0.30, 0.60, "yellow", False, 0.95),
                (0.20, 0.40, "green", False, None),
                (0.50, 0.80, "red", True, 0.80),
                (0.05, 0.20, "green", False, 1.10),
                (0.28, 0.70, "green", False, 0.90),
                (0.12, 0.33, "yellow", False, None),
                (0.40, 0.90, "red", True, 1.20),
                (0.18, 0.45, "green", False, 1.05),
            ],
            start=1,
        )
    }

    budget_snapshot = {
        "date": "2025-11-11",
        "spent": 0.0,
        "limit": 20.0,
        "remaining": 20.0,
        "history": [],
        "strict": True,
        "stats": {},
        "count": 0,
    }

    active_playbook = {
        "mode": "adaptive",
        "bias": "slightly bullish",
        "sl_bias": 1.1,
        "tp_bias": 1.3,
        "size_bias": {"BUY": 1.2, "SELL": 0.85},
        "reason": "Breadth strong",
        "confidence": 0.65,
        "strategy": {
            "name": "Momentum",
            "objective": "Capture upside",
            "why_active": "Momentum favourable",
            "market_signals": ["Breadth improving"],
            "actions": [
                {
                    "title": "Add exposure",
                    "detail": "Increase BUY allocations",
                }
            ],
            "risk_controls": ["Respect hard blocks"],
        },
    }

    state = {
        "technical_snapshot": technical_state,
        "sentinel": sentinel_state,
    }

    strategy = Strategy(exchange=None, state=state)
    strategy.budget_tracker = _DummyBudgetTracker(budget_snapshot)
    strategy.playbook_manager = _DummyPlaybookManager(active_playbook)

    snapshot = strategy._playbook_snapshot()

    assert snapshot["timestamp"] > 0
    assert snapshot["budget"] == budget_snapshot

    # Technical snapshot should keep the most recent six entries
    assert len(snapshot["technical"]) == 6
    assert "SYM1USDT" not in snapshot["technical"]

    # Sentinel sample is trimmed to the most recent eight entries
    assert len(snapshot["sentinel"]) == 8
    assert "S1USDT" not in snapshot["sentinel"]

    latest_entry = snapshot["sentinel"]["S9USDT"]
    assert latest_entry["actions"]["size_factor"] == pytest.approx(1.05)
    assert latest_entry["actions"]["hard_block"] is False
    assert len(latest_entry["events"]) == 2

    overview = snapshot["market_overview"]
    assert overview["technical"]["count"] == 7
    assert overview["sentinel"]["count"] == 9
    assert overview["sentinel"]["warning_symbols"] == 4
    assert overview["sentinel"]["hard_blocks"] == 2
    assert overview["sentinel"]["label_counts"] == {"green": 5, "yellow": 2, "red": 2}
    assert overview["sentinel"]["max_event_risk"]["symbol"] == "S4USDT"
    assert overview["sentinel"]["max_hype_score"]["symbol"] == "S8USDT"

    assert overview["sentinel"]["avg_event_risk"] == pytest.approx(0.237, rel=1e-3)
    assert overview["sentinel"]["avg_hype_score"] == pytest.approx(0.542, rel=1e-3)

    tech_overview = overview["technical"]
    assert tech_overview["avg_rsi"] == pytest.approx(50.43, rel=1e-3)
    assert tech_overview["avg_adx"] == pytest.approx(20.71, rel=1e-3)
    assert tech_overview["avg_atr_pct"] == pytest.approx(0.0244, rel=1e-3)
    assert tech_overview["avg_bb_width"] == pytest.approx(0.055143, rel=1e-3)
    rounded_ratio = round(3 / 7, 3)
    assert tech_overview["trend_up_ratio"] == pytest.approx(rounded_ratio, rel=1e-6)
    assert tech_overview["trend_down_ratio"] == pytest.approx(rounded_ratio, rel=1e-6)
    assert tech_overview["rsi_bullish_ratio"] == pytest.approx(rounded_ratio, rel=1e-6)
    assert tech_overview["rsi_bearish_ratio"] == pytest.approx(rounded_ratio, rel=1e-6)
    assert tech_overview["high_volatility_ratio"] == pytest.approx(round(4 / 7, 3), rel=1e-6)
    assert tech_overview["max_atr_pct"] == {"symbol": "SYM5USDT", "value": pytest.approx(0.032, rel=1e-6)}

    playbook_summary = snapshot["playbook"]
    assert playbook_summary["mode"] == "adaptive"
    assert playbook_summary["bias"] == "slightly bullish"
    assert playbook_summary["sl_bias"] == 1.1
    assert playbook_summary["tp_bias"] == 1.3
    assert playbook_summary["size_bias"] == {"BUY": 1.2, "SELL": 0.85}
    assert playbook_summary["confidence"] == 0.65
    assert playbook_summary["strategy"]["name"] == "Momentum"

