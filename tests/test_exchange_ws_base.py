import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import aster_multi_bot as bot


@pytest.fixture(autouse=True)
def _reset_ws_env(monkeypatch):
    monkeypatch.delenv("ASTER_WS_BASE", raising=False)
    # Ensure we do not accidentally enable paper trading for these unit tests.
    monkeypatch.setenv("ASTER_PAPER", "false")


def _make_exchange(base: str) -> bot.Exchange:
    return bot.Exchange(base, api_key="", api_secret="")


def test_ws_base_for_futures_domain():
    exchange = _make_exchange("https://fapi.asterdex.com")
    assert exchange.ws_base == "wss://fstream.asterdex.com"


def test_ws_base_for_delivery_domain():
    exchange = _make_exchange("http://dapi.example.com")
    assert exchange.ws_base == "ws://dstream.example.com"


def test_ws_base_preserves_custom_ws_scheme():
    exchange = _make_exchange("wss://custom.example/socket")
    assert exchange.ws_base == "wss://custom.example/socket"
