"""Tests for helper logic in :mod:`news`."""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from news import _prepare_search_query


def test_prepare_search_query_strips_known_quote_assets():
    assert _prepare_search_query("BTCUSDT") == "BTC"
    assert _prepare_search_query("ethbtc") == "ETH"
    assert _prepare_search_query("DOGEUSD") == "DOGE"


def test_prepare_search_query_falls_back_to_symbol():
    assert _prepare_search_query("FOOBAR") == "FOOBAR"
    assert _prepare_search_query("ABC") == "ABC"
