import os
import sys
import time
from typing import Any, Dict, List, Optional

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from aster_multi_bot import (
    TradeManager,
    _compute_r_multiple,
    _compute_trade_performance_summary,
)


def _make_trade(symbol: str, pnl: float, pnl_r: float, bucket: str = "S") -> Dict[str, Any]:
    return {"symbol": symbol, "pnl": pnl, "pnl_r": pnl_r, "bucket": bucket}


def test_compute_trade_performance_summary_highlights_extremes() -> None:
    history: List[Dict[str, Any]] = [
        _make_trade("BTCUSDT", 12.0, 1.2, "L"),
        _make_trade("ETHUSDT", -6.0, -0.7, "S"),
        _make_trade("BTCUSDT", -2.5, -0.3, "M"),
        _make_trade("BNBUSDT", 4.5, 0.5, "S"),
    ]

    summary = _compute_trade_performance_summary(history)

    assert summary["sample"] == 4
    assert summary["win_rate"] == pytest.approx(0.5, rel=1e-2)
    assert summary["profit_factor"] > 1.0
    assert summary["best_symbol"]["symbol"] == "BTCUSDT"
    assert summary["worst_symbol"]["symbol"] == "ETHUSDT"
    assert "bucket_stats" in summary


def test_trade_manager_derives_bias_and_cooldown() -> None:
    losing_streak = [
        _make_trade("BTCUSDT", -8.0, -0.8, "L"),
        _make_trade("ETHUSDT", -6.5, -0.7, "M"),
        _make_trade("SOLUSDT", -5.0, -0.6, "S"),
        _make_trade("XRPUSDT", -4.2, -0.5, "S"),
        _make_trade("ADAUSDT", -3.8, -0.4, "S"),
    ]
    state: Dict[str, Any] = {"trade_history": losing_streak.copy()}

    manager = TradeManager(exchange=object(), policy=None, state=state)

    profile = state.get("performance_profile")
    assert profile is not None
    assert profile["sample"] == len(losing_streak)

    bias = state.get("performance_bias")
    assert bias is not None
    assert bias["size_factor"] <= 0.6
    assert bias.get("cooldown") is True
    assert bias["loss_streak"] >= 4
    assert bias.get("cooldown_expires_at") > time.time()
    assert bias.get("cooldown_started_at") <= bias["cooldown_expires_at"]


def test_symbol_specific_performance_bias_isolated() -> None:
    history = [
        _make_trade("BTCUSDT", -4.0, -0.5, "S"),
        _make_trade("BTCUSDT", -5.0, -0.6, "S"),
        _make_trade("ETHUSDT", 3.5, 0.4, "S"),
    ]
    state: Dict[str, Any] = {"trade_history": history.copy()}

    TradeManager(exchange=object(), policy=None, state=state)

    symbol_bias = state.get("symbol_performance_bias")
    assert isinstance(symbol_bias, dict)
    assert "BTCUSDT" in symbol_bias
    btc_bias = symbol_bias["BTCUSDT"]
    assert btc_bias.get("loss_streak") >= 2
    symbol_profiles = state.get("symbol_performance_profile")
    assert isinstance(symbol_profiles, dict)
    assert symbol_profiles.get("BTCUSDT", {}).get("sample") == 2


def test_performance_bias_rewards_positive_expectancy() -> None:
    state: Dict[str, Any] = {"trade_history": []}
    manager = TradeManager(exchange=object(), policy=None, state=state)

    metrics = {
        "sample": 18,
        "expectancy_r": 0.8,
        "profit_factor": 1.9,
        "win_rate": 0.68,
        "drawdown_ratio": 0.15,
        "current_loss_streak": 0,
    }

    bias = manager._derive_performance_bias(metrics)
    assert bias["size_factor"] > 1.0
    assert bias.get("cooldown") is None


def test_cooldown_reuses_previous_window() -> None:
    state: Dict[str, Any] = {"trade_history": []}
    manager = TradeManager(exchange=object(), policy=None, state=state)

    metrics = {
        "sample": 6,
        "expectancy_r": -0.7,
        "profit_factor": 0.6,
        "win_rate": 0.2,
        "drawdown_ratio": 0.55,
        "current_loss_streak": 4,
    }

    initial = manager._derive_performance_bias(metrics)
    state["performance_bias"] = initial
    time.sleep(0.01)
    follow_up = manager._derive_performance_bias(metrics)

    assert follow_up.get("cooldown") is True
    assert follow_up.get("cooldown_started_at") == pytest.approx(
        initial.get("cooldown_started_at"),
        rel=0.01,
    )
    assert follow_up.get("cooldown_expires_at") >= initial.get("cooldown_expires_at")


def test_compute_r_multiple_ignores_missing_stop_loss() -> None:
    assert _compute_r_multiple(0.2871, None, 3027.0, -2.70) == 0.0


def test_compute_r_multiple_handles_negligible_risk() -> None:
    entry = 0.2871
    qty = 3027.0
    pnl = -2.70
    assert _compute_r_multiple(entry, entry, qty, pnl) == 0.0


def test_compute_r_multiple_with_valid_stop() -> None:
    entry = 100.0
    stop = 95.0
    qty = 2.0
    pnl = -8.0
    expected = pnl / ((entry - stop) * qty)
    assert _compute_r_multiple(entry, stop, qty, pnl) == pytest.approx(expected, rel=1e-9)


def test_note_management_exit_marks_trade() -> None:
    symbol = "ALLOUSDT"
    state: Dict[str, Any] = {"trade_history": [], "live_trades": {symbol: {"management": {}}}}
    manager = TradeManager(exchange=object(), policy=None, state=state)

    manager.note_management_exit(symbol, "atr_adverse_stop", quantity=5.0)

    rec = state["live_trades"][symbol]
    assert rec.get("management_exit_reason") == "atr_adverse_stop"
    mgmt = rec.get("management")
    assert isinstance(mgmt, dict)
    assert mgmt.get("last_exit_reason") == "atr_adverse_stop"
    assert mgmt.get("last_exit_qty") == pytest.approx(5.0)


def test_management_exit_reason_propagates_to_history() -> None:
    symbol = "ALLOUSDT"
    entry = 100.0
    qty = 10.0

    class DummyExchange:
        def paper_consume_closed(self) -> List[Dict[str, Any]]:
            return []

        def get_position_risk(self) -> List[Dict[str, Any]]:
            return []

        def get_user_trades(self, _symbol: str, *, from_id: Optional[int] = None, start_time: Optional[int] = None) -> List[Dict[str, Any]]:
            return [
                {
                    "buyer": False,
                    "qty": str(qty),
                    "price": "99.5",
                    "id": 12345,
                    "realizedPnl": "-5.0",
                    "commission": "0.02",
                }
            ]

    state: Dict[str, Any] = {
        "trade_history": [],
        "live_trades": {
            symbol: {
                "entry": entry,
                "initial_sl": 99.0,
                "sl": 99.0,
                "qty": qty,
                "side": "BUY",
                "opened_at": time.time() - 60.0,
                "management": {"atr_adverse_stop": True},
            }
        },
    }

    manager = TradeManager(exchange=DummyExchange(), policy=None, state=state)
    manager.note_management_exit(symbol, "atr_adverse_stop", quantity=qty)
    manager.remove_closed_trades()

    history = state.get("trade_history", [])
    assert history, "trade history should contain the management stop exit"
    record = history[-1]
    assert record.get("management_exit_reason") == "atr_adverse_stop"
