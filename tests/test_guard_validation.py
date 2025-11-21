import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from brackets_guard import BracketGuard


class _DummyExchange:
    def __init__(self):
        self.orders = []

    def get_exchange_info(self):
        return {
            "symbols": [
                {
                    "symbol": "KITEUSDT",
                    "filters": [{"filterType": "PRICE_FILTER", "tickSize": "0.0001"}],
                }
            ]
        }

    def get_open_orders(self, symbol):
        return []

    def get_position_risk(self):
        return [{"symbol": "KITEUSDT", "positionSide": "BOTH", "positionAmt": "0"}]

    # Unused in these tests but required by BracketGuard
    def get_mark_price(self, symbol):
        return 0.0

    def get_book_ticker(self, symbol):
        return {"askPrice": 0.0, "bidPrice": 0.0}

    def cancel_order(self, symbol, order_id):
        self.orders.append(("cancel", symbol, order_id))

    def place_order(self, **params):
        self.orders.append(("place", params))
        return params


def _guard_with_recorder():
    guard = BracketGuard(exchange=_DummyExchange(), log=logging.getLogger("test_guard"))
    calls = []

    def _record_call(fn, symbol, side, qty, price, ref, kind, position_side=None):
        calls.append(
            {
                "fn": fn.__name__,
                "symbol": symbol,
                "side": side,
                "qty": qty,
                "price": price,
                "ref": ref,
                "kind": kind,
                "position_side": position_side,
            }
        )

    guard._place_with_retry = _record_call
    return guard, calls


def test_invalid_long_stop_is_skipped():
    guard, calls = _guard_with_recorder()

    ok = guard.ensure_after_entry("KITEUSDT", "BUY", 1.0, 1.0, 1.01, 1.1)

    assert ok is False
    assert [call["fn"] for call in calls] == ["place_tp"]


def test_invalid_short_take_profit_is_skipped():
    guard, calls = _guard_with_recorder()

    ok = guard.ensure_after_entry("KITEUSDT", "SELL", 1.0, 2.0, 2.2, 2.1)

    assert ok is False
    assert [call["fn"] for call in calls] == ["place_sl"]
