import os
import sys
import time

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from aster_multi_bot import Strategy


class _DummyExchange:
    def __init__(self) -> None:
        self.calls = []


def _sample_technical_state(now: float) -> dict:
    return {
        "BTCUSDT": {
            "ts": now - 30,
            "rsi": 45.0,
            "adx": 18.0,
            "atr_pct": 0.011,
            "bb_width": 0.0018,
            "supertrend_dir": 1,
        },
        "ETHUSDT": {
            "ts": now - 20,
            "rsi": 58.0,
            "adx": 22.0,
            "atr_pct": 0.016,
            "bb_width": 0.0024,
            "supertrend_dir": -1,
        },
        "XRPUSDT": {
            "ts": now - 10,
            "rsi": 35.0,
            "adx": 15.0,
            "atr_pct": 0.008,
            "bb_width": 0.0012,
            "supertrend_dir": -1,
        },
        "SOLUSDT": {
            "ts": now - 5,
            "rsi": 62.0,
            "adx": 28.0,
            "atr_pct": 0.02,
            "bb_width": 0.0031,
            "supertrend_dir": 1,
        },
    }


def _sample_sentinel_state(now: float) -> dict:
    return {
        "BTCUSDT": {
            "event_risk": 0.32,
            "hype_score": 0.48,
            "label": "watch",
            "updated": now - 60,
            "actions": {"hard_block": False},
        },
        "ETHUSDT": {
            "event_risk": 0.12,
            "hype_score": 0.3,
            "label": "ok",
            "updated": now - 50,
        },
        "SOLUSDT": {
            "event_risk": 0.45,
            "hype_score": 0.7,
            "label": "alert",
            "updated": now - 40,
            "actions": {"hard_block": True},
        },
    }


def test_playbook_snapshot_includes_filter_state_and_rejections():
    now = time.time()
    state = {
        "technical_snapshot": _sample_technical_state(now),
        "sentinel": _sample_sentinel_state(now),
        "decision_stats": {
            "rejected_history": [
                [now - 5, "edge_r"],
                [now - 4, "edge_r"],
                [now - 3, "spread_tight"],
            ]
        },
    }
    strategy = Strategy(exchange=_DummyExchange(), state=state)
    strategy._skip_relief_snapshot = {"total": 3, "edge_r_pct": 50.0}

    snapshot = strategy._playbook_snapshot()
    filter_state = snapshot.get("filter_state")
    assert filter_state is not None
    assert filter_state["thresholds"]["edge_r"]["min_edge_r"] == pytest.approx(
        strategy.min_edge_r
    )
    assert filter_state["skip_relief"]["total"] == 3
    recent = filter_state.get("recent_rejections")
    assert recent and recent["total"] == 3
    reasons = recent.get("reasons")
    assert reasons and reasons[0]["reason"] == "edge_r"


def test_playbook_market_overview_emits_percentiles():
    now = time.time()
    state: dict = {}
    strategy = Strategy(exchange=_DummyExchange(), state=state)
    overview = strategy._playbook_market_overview(
        _sample_technical_state(now), _sample_sentinel_state(now)
    )
    tech = overview.get("technical")
    assert tech is not None
    assert "rsi_p25" in tech and "atr_pct_p75" in tech
    sentinel = overview.get("sentinel")
    assert sentinel is not None
    assert "event_risk_p90" in sentinel and "hype_score_p50" in sentinel
