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
    lo_rsi_bounds = manager._relaxed_filter_bounds(45.0, 75.0)
    assert pytest.approx(filters["long_overextended"]["rsi_cap"]) == lo_rsi_bounds[1]
    lo_atr_bounds = manager._relaxed_filter_bounds(0.002, 0.02)
    assert pytest.approx(filters["long_overextended"]["atr_pct_cap"], rel=1e-3) == lo_atr_bounds[1]
    assert filters["trend_extension"]["bars_hard"] > filters["trend_extension"]["bars_soft"]
    edge_bounds = manager._relaxed_filter_bounds(0.03, 0.4)
    assert filters["edge_r"]["min_edge_r"] == pytest.approx(edge_bounds[1])
    wicky_bounds = manager._relaxed_filter_bounds(0.94, 0.9995)
    assert filters["wicky"]["wickiness_max"] == pytest.approx(wicky_bounds[1])
    sent_gate_bounds = manager._relaxed_filter_bounds(0.3, 0.9)
    assert filters["sentinel_veto"]["event_risk_gate"] == pytest.approx(sent_gate_bounds[0])
    block_risk_bounds = manager._relaxed_filter_bounds(0.45, 0.98)
    assert filters["sentinel_veto"]["block_risk"] == pytest.approx(block_risk_bounds[1])
    struct_event_bounds = manager._relaxed_filter_bounds(0.2, 0.9)
    assert filters["playbook_structured_block"]["event_risk_max"] == pytest.approx(
        struct_event_bounds[1]
    )
    struct_soft_bounds = manager._relaxed_filter_bounds(0.25, 1.0)
    assert filters["playbook_structured_block"]["soft_multiplier"] == pytest.approx(
        struct_soft_bounds[1]
    )


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


def test_strategy_softens_overly_strict_filters():
    state: dict = {}
    strategy = Strategy(exchange=_DummyExchange(), state=state)
    defaults = dict(strategy._filter_defaults)
    overrides = {
        "filters": {
            "edge_r": {"min_edge_r": defaults["min_edge_r"] * 3},
            "spread_tight": {"spread_bps_max": defaults["spread_bps_max"] * 0.1},
            "no_cross": {
                "rsi_buy_min": defaults["rsi_buy_min"] + 30,
                "rsi_sell_max": defaults["rsi_sell_max"] - 30,
            },
        }
    }
    strategy.playbook_manager = _DummyManager(overrides)
    strategy.apply_playbook_filters()
    guarded = strategy._guarded_filter_value("min_edge_r", defaults["min_edge_r"] * 3)
    expected_edge = max(EXPECTED_R_MIN_FLOOR, min(0.05, guarded))
    assert strategy.min_edge_r == pytest.approx(expected_edge)
    expected_spread = max(
        1e-5,
        strategy._guarded_filter_value(
            "spread_bps_max", defaults["spread_bps_max"] * 0.1
        ),
    )
    assert strategy.spread_bps_max == pytest.approx(expected_spread)
    expected_buy = max(
        30.0,
        min(
            70.0,
            strategy._guarded_filter_value(
                "rsi_buy_min", defaults["rsi_buy_min"] + 30
            ),
        ),
    )
    assert strategy.rsi_buy_min == pytest.approx(expected_buy)
    expected_sell = max(
        30.0,
        min(
            70.0,
            strategy._guarded_filter_value(
                "rsi_sell_max", defaults["rsi_sell_max"] - 30
            ),
        ),
    )
    assert strategy.rsi_sell_max == pytest.approx(expected_sell)


def test_strategy_caps_min_edge_override_to_point_zero_five():
    state: dict = {}
    strategy = Strategy(exchange=_DummyExchange(), state=state)
    overrides = {"filters": {"edge_r": {"min_edge_r": 0.25}}}
    strategy.playbook_manager = _DummyManager(overrides)
    strategy.apply_playbook_filters()
    assert strategy.min_edge_r == pytest.approx(0.05, rel=1e-3)
    assert strategy.min_edge_r >= EXPECTED_R_MIN_FLOOR
