import time

from dashboard_server import _filter_history_for_run, _merge_realized_pnl


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


def test_filter_history_for_run_falls_back_to_history_when_no_recent_trades():
    run_started_at = time.time()
    history = [
        {"symbol": "BNBUSDT", "closed_at": run_started_at - 500},
        {"symbol": "XRPUSDT", "closed_at": run_started_at - 400},
    ]

    filtered = _filter_history_for_run(history, run_started_at)

    assert filtered == history


def test_filter_history_drops_synthetic_realized_entries_before_run():
    run_started_at = time.time()
    history = [
        {
            "symbol": "ETHUSDT",
            "opened_at": run_started_at + 5,
            "closed_at": run_started_at + 15,
            "pnl": 10.0,
            "pnl_r": 1.0,
        }
    ]
    realized_entries = [
        {"symbol": "ETHUSDT", "income": 10.0, "time": run_started_at + 16},
        {"symbol": "BTCUSDT", "income": 5.0, "time": run_started_at - 60},
    ]

    merged = _merge_realized_pnl(history, realized_entries)
    filtered = _filter_history_for_run(merged, run_started_at)

    assert len(filtered) == 1
    assert filtered[0]["symbol"] == "ETHUSDT"
