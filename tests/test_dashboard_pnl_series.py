import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from dashboard_server import _build_pnl_series


def test_build_pnl_series_accumulates_sorted_history():
    history = [
        {"pnl": 5.0, "closed_at": 1_700_000_300.0},
        {"pnl": -2.0, "closed_at": 1_700_000_100.0},
        {"pnl": 1.5, "closed_at": 1_700_000_200.0},
    ]

    series = _build_pnl_series(history)

    assert series["values"] == [ -2.0, -0.5, 4.5 ]
    assert len(series["labels"]) == 3
    assert series["labels"][0].startswith("20") or series["labels"][0].startswith("Trade")


def test_build_pnl_series_respects_limit():
    history = []
    for idx in range(5):
        history.append({"pnl": 1.0, "closed_at": 1_700_000_000.0 + idx})

    series = _build_pnl_series(history, limit=3)

    assert series["values"] == [3.0, 4.0, 5.0]
    assert len(series["labels"]) == 3
