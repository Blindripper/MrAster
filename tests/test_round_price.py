import math
import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from aster_multi_bot import round_price


def test_round_price_respects_bias_up_and_down() -> None:
    tick = 0.1
    price = 100.04
    assert round_price("BTCUSDT", price, tick, bias="down") == pytest.approx(100.0)
    assert round_price("BTCUSDT", price, tick, bias="up") == pytest.approx(100.1)


def test_round_price_prevents_short_stop_collapse() -> None:
    tick = 0.1
    entry = 68000.0
    tight_stop = entry + 0.03  # closer than one tick
    rounded = round_price("BTCUSDT", tight_stop, tick, bias="up")
    assert rounded >= entry + tick


def test_round_price_default_matches_floor() -> None:
    tick = 0.5
    price = 123.74
    assert round_price("ETHUSDT", price, tick) == math.floor(price / tick + 1e-12) * tick
