import sys
import os
import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from aster_multi_bot import (
    NO_CROSS_RELIEF_MAX,
    NO_CROSS_RELIEF_STEP,
    RSI_BUY_MIN,
    RSI_SELL_MAX,
    SKIP_RELIEF_STEP_SIZE,
    Strategy,
    DecisionTracker,
)


class _DummyExchange:
    def __init__(self) -> None:
        self.calls = []


def test_skip_relief_steps_every_hundred_skips():
    state: dict = {}
    tracker = DecisionTracker(state)
    strategy = Strategy(exchange=_DummyExchange(), decision_tracker=tracker, state=state)

    for _ in range(SKIP_RELIEF_STEP_SIZE - 1):
        strategy._skip("no_cross", "BTCUSDT")

    assert strategy.rsi_buy_min == pytest.approx(RSI_BUY_MIN)
    assert strategy.rsi_sell_max == pytest.approx(RSI_SELL_MAX)

    strategy._skip("no_cross", "BTCUSDT")

    first_step_pad = min(NO_CROSS_RELIEF_MAX, NO_CROSS_RELIEF_STEP)
    assert strategy.rsi_buy_min == pytest.approx(max(35.0, RSI_BUY_MIN - first_step_pad))
    assert strategy.rsi_sell_max == pytest.approx(min(65.0, RSI_SELL_MAX + first_step_pad))
    assert strategy._skip_relief_snapshot.get("steps") == 1

    for _ in range(SKIP_RELIEF_STEP_SIZE):
        strategy._skip("no_cross", "BTCUSDT")

    second_step_pad = min(NO_CROSS_RELIEF_MAX, 2 * NO_CROSS_RELIEF_STEP)
    assert strategy.rsi_buy_min == pytest.approx(max(35.0, RSI_BUY_MIN - second_step_pad))
    assert strategy.rsi_sell_max == pytest.approx(min(65.0, RSI_SELL_MAX + second_step_pad))
    assert strategy._skip_relief_snapshot.get("steps") == 2


def test_skip_relief_respects_tightened_rsi_before_first_step():
    state: dict = {}
    tracker = DecisionTracker(state)
    strategy = Strategy(exchange=_DummyExchange(), decision_tracker=tracker, state=state)

    strategy.rsi_buy_min = RSI_BUY_MIN + 3.0
    strategy.rsi_sell_max = RSI_SELL_MAX - 3.0
    strategy._refresh_filter_defaults()

    tightened_buy = strategy.rsi_buy_min
    tightened_sell = strategy.rsi_sell_max

    strategy._skip("no_cross", "BTCUSDT")

    assert strategy.rsi_buy_min == pytest.approx(tightened_buy)
    assert strategy.rsi_sell_max == pytest.approx(tightened_sell)

    for _ in range(SKIP_RELIEF_STEP_SIZE - 1):
        strategy._skip("no_cross", "BTCUSDT")

    first_step_pad = min(NO_CROSS_RELIEF_MAX, NO_CROSS_RELIEF_STEP)
    assert strategy.rsi_buy_min == pytest.approx(max(35.0, tightened_buy - first_step_pad))
    assert strategy.rsi_sell_max == pytest.approx(min(65.0, tightened_sell + first_step_pad))


def test_skip_relief_resets_after_trade():
    state: dict = {}
    tracker = DecisionTracker(state)
    strategy = Strategy(exchange=_DummyExchange(), decision_tracker=tracker, state=state)

    for _ in range(2 * SKIP_RELIEF_STEP_SIZE):
        strategy._skip("no_cross", "ETHUSDT")

    assert strategy._skip_relief_snapshot.get("steps") >= 2
    assert strategy.rsi_buy_min < RSI_BUY_MIN
    assert strategy.rsi_sell_max > RSI_SELL_MAX

    strategy._reset_skip_relief_after_trade()

    assert strategy._skip_relief_snapshot.get("steps") == 0
    assert strategy._skip_relief_snapshot.get("skips_since_trade") == 0
    assert strategy.rsi_buy_min == pytest.approx(RSI_BUY_MIN)
    assert strategy.rsi_sell_max == pytest.approx(RSI_SELL_MAX)
