import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import dashboard_server


class _DummyResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception("http error")

    def json(self):
        return self._payload


def test_fetch_position_brackets_accepts_take_profit_with_hyphen(monkeypatch):
    def fake_get(url, headers, timeout):
        payload = [
            {
                "type": "Take-Profit-Market",
                "price": "0.333",
                "side": "SELL",
                "positionSide": "LONG",
                "reduceOnly": True,
            }
        ]
        return _DummyResponse(payload)

    monkeypatch.setattr(dashboard_server.requests, "get", fake_get)

    env = {
        "ASTER_EXCHANGE_BASE": "https://example.invalid",
        "ASTER_API_KEY": "k",
        "ASTER_API_SECRET": "s",
    }

    result = dashboard_server._fetch_position_brackets(env, ["DOGEUSDT"], 5000)

    assert "DOGEUSDT" in result
    bucket = result["DOGEUSDT"].get("BUY")
    assert bucket is not None
    take_entry = bucket.get("take")
    assert isinstance(take_entry, dict)
    assert take_entry.get("price") == pytest.approx(0.333)
    assert take_entry.get("type") == "TAKE-PROFIT-MARKET"

