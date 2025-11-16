import time

from dashboard_server import _filter_history_for_run


def test_filter_history_for_run_excludes_previous_entries():
    run_started_at = time.time()
    history = [
        {"symbol": "BTCUSDT", "closed_at": run_started_at - 120},
        {"symbol": "ETHUSDT", "closed_at": run_started_at + 5},
    ]

    filtered = _filter_history_for_run(history, run_started_at)

    assert len(filtered) == 1
    assert filtered[0]["symbol"] == "ETHUSDT"


def test_filter_history_for_run_uses_opened_timestamp_when_needed():
    run_started_at = time.time()
    history = [
        {"symbol": "ADAUSDT", "opened_at": run_started_at + 10},
        {"symbol": "SOLUSDT", "opened_at": run_started_at - 10},
    ]

    filtered = _filter_history_for_run(history, run_started_at)

    assert len(filtered) == 1
    assert filtered[0]["symbol"] == "ADAUSDT"


def test_filter_history_for_run_returns_all_when_no_cutoff():
    history = [
        {"symbol": "BNBUSDT", "closed_at": 10},
        {"symbol": "XRPUSDT", "closed_at": 20},
    ]

    filtered = _filter_history_for_run(history, None)

    assert filtered == history
