import pytest

from dashboard_server import _merge_realized_pnl


def _make_trade(pnl: float = 5.0, pnl_r: float = 0.5) -> dict:
    return {
        "symbol": "STABLEUSDT",
        "opened_at": 1_000.0,
        "closed_at": 1_060.0,
        "pnl": pnl,
        "pnl_r": pnl_r,
    }


def _make_income(amount: float) -> dict:
    return {"symbol": "STABLEUSDT", "income": amount, "time": 1_030.0}


def test_merge_realized_pnl_overrides_estimates_and_updates_r() -> None:
    history = [_make_trade()]
    realized = [_make_income(-3.6)]

    merged = _merge_realized_pnl(history, realized)

    assert len(merged) == 1
    record = merged[0]
    assert record["realized_pnl"] == pytest.approx(-3.6)
    assert record["pnl"] == pytest.approx(-3.6)
    assert record["estimated_pnl"] == pytest.approx(5.0)
    assert record["pnl_r"] == pytest.approx(-0.36)


def test_merge_realized_pnl_handles_missing_risk_context() -> None:
    history = [_make_trade(pnl_r=0.0)]
    realized = [_make_income(-7.2)]

    merged = _merge_realized_pnl(history, realized)

    record = merged[0]
    assert record["pnl"] == pytest.approx(-7.2)
    assert record["realized_pnl"] == pytest.approx(-7.2)
    # pnl_r remains unchanged when we cannot infer risk
    assert record["pnl_r"] == 0.0


def test_merge_realized_pnl_synthesizes_records_for_untracked_income() -> None:
    realized = [
        {
            "symbol": "STOPUSDT",
            "income": -0.25,
            "time": 1_500.0,
            "info": "ORDER:42 type=STOP_MARKET side:SELL",
        }
    ]

    merged = _merge_realized_pnl([], realized)

    assert len(merged) == 1
    record = merged[0]
    assert record["symbol"] == "STOPUSDT"
    assert record["pnl"] == pytest.approx(-0.25)
    assert record["synthetic"] is True
    assert record["synthetic_source"] == "realized_income"
    assert record["closed_at"] == pytest.approx(1_500.0)
    assert record["side"] == "SELL"
    assert record["opened_at_iso"] == "1970-01-01T00:25:00+00:00"
    assert record["closed_at_iso"] == "1970-01-01T00:25:00+00:00"
