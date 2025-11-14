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
