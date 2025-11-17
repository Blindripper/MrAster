import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from aster_multi_bot import Bot


class _RecorderGuard:
    def __init__(self, behavior):
        self._behavior = behavior
        self.calls = []

    def ensure_after_entry(self, symbol, side, *args):
        self.calls.append((symbol, side, args))
        result = self._behavior(len(args))
        if isinstance(result, BaseException):
            raise result
        return result


def _bot_with_guard(guard):
    bot = object.__new__(Bot)
    bot.state = {"execution_telemetry": []}
    bot.guard = guard
    bot.trade_mgr = None
    bot._execution_telemetry_limit = 10
    return bot


def test_guard_prefers_modern_signature():
    guard = _RecorderGuard(lambda count: True if count == 4 else False)
    bot = _bot_with_guard(guard)

    assert bot._ensure_guard_after_entry("BTCUSDT", "BUY", 1.0, 100.0, 99.0, 101.0)
    assert len(guard.calls) == 1
    symbol, side, args = guard.calls[0]
    assert symbol == "BTCUSDT"
    assert side == "BUY"
    assert len(args) == 4
    assert bot.state["execution_telemetry"] == []


def test_guard_fallback_records_telemetry():
    def behavior(arg_count):
        if arg_count == 4:
            return TypeError("legacy path")
        return True

    guard = _RecorderGuard(behavior)
    bot = _bot_with_guard(guard)

    assert bot._ensure_guard_after_entry("ETHUSDT", "SELL", 2.0, 50.0, 49.5, 52.0)
    assert len(guard.calls) == 2
    first_call = guard.calls[0]
    second_call = guard.calls[1]
    assert len(first_call[2]) == 4
    assert len(second_call[2]) == 2
    telemetry = bot.state["execution_telemetry"]
    assert telemetry and telemetry[-1]["event"] == "bracket_guard_legacy_fallback"
    assert telemetry[-1]["symbol"] == "ETHUSDT"


def test_guard_failure_propagates_exception_and_logs():
    guard = _RecorderGuard(lambda _: RuntimeError("guard boom"))
    bot = _bot_with_guard(guard)

    with pytest.raises(RuntimeError):
        bot._ensure_guard_after_entry("BNBUSDT", "BUY", 0.1, 300.0, 295.0, 330.0)

    telemetry = bot.state["execution_telemetry"]
    assert telemetry[-1]["event"] == "bracket_guard_failure"
    assert telemetry[-1]["detail"] == "modern_signature_failed"
