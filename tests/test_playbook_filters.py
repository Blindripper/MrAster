import os
import sys
import time

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ai_extensions import PlaybookManager
from aster_multi_bot import EXPECTED_R_MIN_FLOOR, Strategy


class _DummyExchange:
    def __init__(self) -> None:
        self.calls = []


class _DummyManager:
    def __init__(self, active):
        self._active = active

    def active(self):
        return self._active


def _noop_request(kind, payload):
    return None


def test_playbook_manager_normalizes_filters():
    state: dict = {}
    manager = PlaybookManager(state, request_fn=_noop_request)
    payload = {
        "mode": "baseline",
        "bias": "neutral",
        "filters": {
            "long_overextended": {"rsi_cap": 120, "atr_pct_cap": 0.5},
            "trend_extension": {"bars_soft": 2, "bars_hard": 5, "adx_min": 80},
            "continuation_pullback": {
                "stoch_warn": 30,
                "stoch_max": 40,
                "stoch_min": 50,
                "adx_delta_min": 25,
            },
            "edge_r": {"min_edge_r": 0.5},
            "wicky": {"wickiness_max": 1.5},
            "sentinel_veto": {
                "event_risk_gate": 0.15,
                "block_risk": 2.0,
                "min_multiplier": 0.05,
                "weight": 5.0,
            },
            "playbook_structured_block": {
                "event_risk_max": 1.5,
                "soft_multiplier": 5.0,
            },
        },
    }
    normalized = manager._normalize_playbook(payload, now=time.time())
    filters = normalized.get("filters")
    assert filters is not None
    assert pytest.approx(filters["long_overextended"]["rsi_cap"]) == 75.0
    assert pytest.approx(filters["long_overextended"]["atr_pct_cap"], rel=1e-3) == 0.02
    assert filters["trend_extension"]["bars_hard"] > filters["trend_extension"]["bars_soft"]
    assert filters["edge_r"]["min_edge_r"] <= 0.4
    assert filters["wicky"]["wickiness_max"] < 1.0
    assert filters["sentinel_veto"]["event_risk_gate"] >= 0.3
    assert filters["sentinel_veto"]["block_risk"] <= 0.98
    assert filters["playbook_structured_block"]["event_risk_max"] <= 0.9
    assert filters["playbook_structured_block"]["soft_multiplier"] <= 1.0


def test_strategy_applies_playbook_filters():
    state: dict = {}
    strategy = Strategy(exchange=_DummyExchange(), state=state)
    defaults = dict(strategy._filter_defaults)
    overrides = {
        "filters": {
            "edge_r": {"min_edge_r": defaults["min_edge_r"] * 0.6},
            "long_overextended": {"rsi_cap": defaults["long_overextended_rsi_cap"] + 4},
            "sentinel_veto": {
                "event_risk_gate": defaults["sentinel_gate_event_risk"] + 0.1,
                "block_risk": defaults["sentinel_gate_block_risk"] - 0.1,
                "min_multiplier": defaults["sentinel_gate_min_mult"] + 0.05,
                "weight": defaults["sentinel_gate_weight"] - 0.1,
            },
            "playbook_structured_block": {
                "event_risk_max": 0.55,
                "soft_multiplier": 0.65,
            },
        }
    }
    strategy.playbook_manager = _DummyManager(overrides)
    strategy.apply_playbook_filters()
    expected_edge = max(EXPECTED_R_MIN_FLOOR, defaults["min_edge_r"] * 0.6)
    assert strategy.min_edge_r == pytest.approx(expected_edge)
    assert strategy.long_overextended_rsi_cap == pytest.approx(
        defaults["long_overextended_rsi_cap"] + 4
    )
    assert strategy.sentinel_gate_event_risk == pytest.approx(
        max(0.2, min(0.95, defaults["sentinel_gate_event_risk"] + 0.1))
    )
    assert strategy.sentinel_gate_block_risk == pytest.approx(
        max(0.35, min(0.99, defaults["sentinel_gate_block_risk"] - 0.1))
    )
    assert strategy.sentinel_gate_min_mult == pytest.approx(
        max(0.1, min(0.9, defaults["sentinel_gate_min_mult"] + 0.05))
    )
    assert strategy.sentinel_gate_weight == pytest.approx(
        max(0.4, min(1.25, defaults["sentinel_gate_weight"] - 0.1))
    )
    assert strategy.structured_block_event_risk_cap == pytest.approx(0.55)
    assert strategy.structured_block_soft_multiplier == pytest.approx(0.65)
    strategy.playbook_manager = _DummyManager({"filters": {}})
    strategy.apply_playbook_filters()
    assert strategy.min_edge_r == pytest.approx(defaults["min_edge_r"])
    assert strategy.long_overextended_rsi_cap == pytest.approx(
        defaults["long_overextended_rsi_cap"]
    )
    assert strategy.sentinel_gate_event_risk == pytest.approx(
        defaults["sentinel_gate_event_risk"]
    )
    assert strategy.structured_block_event_risk_cap == pytest.approx(
        defaults["structured_block_event_risk_cap"]
    )
