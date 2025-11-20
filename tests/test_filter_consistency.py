import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from aster_multi_bot import EXPECTED_R_MIN_FLOOR, STOCHRSI_OVERSOLD, Strategy


class _DummyExchange:
    def __init__(self) -> None:
        self.calls = []


def test_long_overextended_window_allows_buys():
    strategy = Strategy(exchange=_DummyExchange())
    # The RSI buy gate must be below the overextension cap so longs can proceed.
    assert strategy.rsi_buy_min < strategy.long_overextended_rsi_cap
    # ATR cap should be positive to avoid blocking everything.
    assert strategy.long_overextended_atr_cap > 0


def test_trend_extension_has_soft_and_hard_gates():
    strategy = Strategy(exchange=_DummyExchange())
    # Hard stop must be stricter than soft stop to avoid duplicate blocking.
    assert strategy.trend_extension_bars < strategy.trend_extension_bars_hard
    # ADX guard should stay within a realistic 0-100 oscillator band.
    assert 0 < strategy.trend_extension_adx_min < 100


def test_expected_edge_floor_has_headroom():
    strategy = Strategy(exchange=_DummyExchange())
    assert strategy.min_edge_r >= EXPECTED_R_MIN_FLOOR
    assert strategy.min_edge_r < 1


def test_short_trend_stoch_filter_is_reachable():
    strategy = Strategy(exchange=_DummyExchange())
    # Short Stoch RSI guard should sit above the oversold line but below max oscillator value.
    assert STOCHRSI_OVERSOLD < strategy.trend_short_stochrsi_min < 100
