import pytest

import pytest

from dashboard_server import (
    TradeStats,
    _build_hero_metrics,
    _build_history_summary,
    _compute_stats,
)


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


def test_build_history_summary_tracks_avg_and_counts() -> None:
    stats = TradeStats(
        count=3,
        total_pnl=9.0,
        total_r=1.5,
        win_rate=0.5,
        best_trade=None,
        worst_trade=None,
        ai_hint='',
        wins=2,
        losses=1,
        draws=0,
    )

    summary = _build_history_summary(stats)

    assert summary["trades"] == 3
    assert summary["realized_pnl"] == pytest.approx(9.0)
    assert summary["avg_r"] == pytest.approx(0.5)
    assert summary["win_rate"] == pytest.approx(0.5)
    assert summary["wins"] == 2
    assert summary["losses"] == 1


def test_build_hero_metrics_prefers_history_count_for_total_trades() -> None:
    stats = TradeStats(
        count=0,
        total_pnl=0.0,
        total_r=0.0,
        win_rate=0.0,
        best_trade=None,
        worst_trade=None,
        ai_hint='',
        wins=0,
        losses=0,
        draws=0,
    )
    cumulative = {
        "total_trades": 2,
        "total_pnl": 5.0,
        "realized_pnl": 4.5,
        "ai_budget_spent": 1.5,
        "wins": 2,
        "losses": 1,
        "draws": 0,
    }

    hero = _build_hero_metrics(cumulative, stats, history_count=5)

    assert hero["total_trades"] == 5
    assert hero["total_pnl"] == pytest.approx(5.0)
    assert hero["realized_pnl"] == pytest.approx(4.5)
    assert hero["ai_budget_spent"] == pytest.approx(1.5)
    assert hero["win_rate"] == pytest.approx(2 / 3)
