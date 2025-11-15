import os
import sys
from types import SimpleNamespace
from typing import Any, Dict, List, Tuple

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from aster_multi_bot import Bot


def _make_bot(state: Dict[str, Any]) -> Bot:
    bot = Bot.__new__(Bot)  # type: ignore
    bot.state = state
    bot.risk = SimpleNamespace(symbol_filters={})
    bot._management_dirty = False  # type: ignore[attr-defined]
    bot._log_management_event = lambda *args, **kwargs: None  # type: ignore[attr-defined]
    bot._adjust_exit = lambda *args, **kwargs: True  # type: ignore[attr-defined]
    bot.guard = None
    return bot


def test_compression_time_cut_triggers(monkeypatch: pytest.MonkeyPatch) -> None:
    symbol = "BTCUSDT"
    base_time = 1_000_000.0
    state: Dict[str, Any] = {"live_trades": {}}
    bot = _make_bot(state)
    bot.risk.symbol_filters[symbol] = {"stepSize": 0.001, "tickSize": 0.0001}

    calls: List[Tuple[str, str, float, str]] = []

    def fake_submit(symbol_arg: str, side: str, quantity: float, reason: str) -> bool:
        calls.append((symbol_arg, side, quantity, reason))
        return True

    bot._submit_reduce_only = fake_submit  # type: ignore[attr-defined]

    monkeypatch.setattr("aster_multi_bot.time.time", lambda: base_time)
    monkeypatch.setattr("aster_multi_bot.random.uniform", lambda _a, _b: 600.0)

    rec = {
        "entry": 100.0,
        "initial_sl": 99.0,
        "sl": 99.0,
        "side": "BUY",
        "qty": 1.0,
        "ctx": {"pm_volatility_compression_flag": 0.2},
        "atr_abs": 0.008,
        "opened_at": base_time - 601.0,
        "management": {},
    }
    state["live_trades"][symbol] = rec

    bot._manage_open_position(symbol, amount=1.0, mid=100.003, atr_abs=0.008)

    assert calls
    assert calls[0][3] == "compression_time_cut"
    mgmt = rec["management"]
    assert mgmt.get("compression_time_cut_executed") is True
    assert bot._management_dirty is True  # type: ignore[attr-defined]
