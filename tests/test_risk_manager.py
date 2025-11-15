import time

import pytest

from aster_multi_bot import RiskManager, DEFAULT_NOTIONAL, QUOTE


class DummyExchange:
    def __init__(self, responses, *, fail_after=None):
        self._responses = list(responses)
        self._fail_after = fail_after
        self.calls = 0

    def signed(self, method, path, params):
        self.calls += 1
        if self._fail_after is not None and self.calls > self._fail_after:
            raise RuntimeError("boom")
        idx = min(self.calls, len(self._responses)) - 1
        return self._responses[idx]


def test_equity_cached_prefers_richest_wallet_entry():
    exchange = DummyExchange(
        [
            [
                {
                    "asset": QUOTE,
                    "balance": "32.5",
                    "availableBalance": "45.0",
                    "crossWalletBalance": "155.75",
                    "maxWithdrawAmount": "120.0",
                }
            ]
        ]
    )
    risk = RiskManager(exchange, DEFAULT_NOTIONAL)

    equity = risk._equity_cached()

    assert equity == pytest.approx(155.75)
    assert exchange.calls == 1

    # cached result should be reused without triggering another API call
    assert risk._equity_cached() == pytest.approx(equity)
    assert exchange.calls == 1


def test_equity_cached_falls_back_to_cached_value_on_error():
    exchange = DummyExchange(
        [
            [
                {
                    "asset": QUOTE,
                    "balance": "80",
                }
            ]
        ],
        fail_after=1,
    )
    risk = RiskManager(exchange, DEFAULT_NOTIONAL)

    first = risk._equity_cached()
    assert first == pytest.approx(80.0)

    # force cache expiry and verify we return the cached value if the API fails
    risk._equity_ts -= risk._equity_ttl + 1
    assert risk._equity_cached() == pytest.approx(first)
    assert exchange.calls == 2


def test_compute_qty_limits_position_to_ten_percent_equity():
    exchange = DummyExchange([[]])
    risk = RiskManager(exchange, DEFAULT_NOTIONAL)

    # prime the equity cache so no API call is attempted
    risk._equity = 1000.0
    risk._equity_ts = time.time()
    risk._equity_ttl = 3600

    risk.symbol_filters = {"BTCUSDT": {"stepSize": 0.001}}
    risk._preset_min_notional = 0.0
    risk._preset_max_notional = float("inf")

    risk._drawdown_factor = lambda: 1.0  # type: ignore
    risk._adaptive_size_multiplier = lambda *args, **kwargs: 1.0  # type: ignore
    risk._ai_notional_tier = lambda *args, **kwargs: ("tier", 10000.0, 0.0, float("inf"))  # type: ignore
    risk.max_leverage_for = lambda symbol: 50.0  # type: ignore
    state = {"symbol_leverage": {"BTCUSDT": 5.0}}
    risk.attach_state(state)

    qty = risk.compute_qty("BTCUSDT", entry=100.0, sl=95.0, size_mult=3.0)

    notional = qty * 100.0
    margin = notional / 5.0

    assert margin == pytest.approx(100.0)
