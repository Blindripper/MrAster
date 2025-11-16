import pytest

from dashboard_server import _compute_stats


def _trade(symbol: str, pnl: float, *, pnl_r: float = 0.0) -> dict:
    return {
        "symbol": symbol,
        "pnl": pnl,
        "pnl_r": pnl_r,
    }


def _synthetic_income(symbol: str, pnl: float) -> dict:
    return {
        "symbol": symbol,
        "pnl": pnl,
        "synthetic": True,
        "synthetic_source": "realized_income",
    }


def test_compute_stats_ignores_realized_income_rows() -> None:
    history = [
        _trade("BTCUSDT", 12.5, pnl_r=1.2),
        _synthetic_income("BTCUSDT", -3.0),
        _synthetic_income("ETHUSDT", 5.0),
    ]

    stats = _compute_stats(history)

    assert stats.count == 1
    assert stats.total_pnl == pytest.approx(12.5)
    assert stats.total_r == pytest.approx(1.2)
    assert stats.wins == 1
    assert stats.losses == 0
    assert stats.draws == 0


def test_compute_stats_returns_empty_when_only_income_rows() -> None:
    history = [
        _synthetic_income("BTCUSDT", 4.2),
        _synthetic_income("ETHUSDT", -1.5),
    ]

    stats = _compute_stats(history)

    assert stats.count == 0
    assert stats.total_pnl == 0.0
    assert stats.total_r == 0.0
    assert stats.wins == 0
    assert stats.losses == 0
    assert stats.draws == 0
