import asyncio

import pytest

from dashboard_server import (
    _merge_realized_pnl,
    _resolve_history_with_realized,
    _strip_realized_income_trades,
)


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


def test_strip_realized_income_trades_removes_synthetic_records() -> None:
    history = [
        _make_trade(),
        {
            "symbol": "STOPUSDT",
            "pnl": -0.25,
            "synthetic": True,
            "synthetic_source": "realized_income",
        },
    ]

    filtered = _strip_realized_income_trades(history)

    assert len(filtered) == 1
    assert filtered[0]["symbol"] == "STABLEUSDT"


def test_strip_realized_income_trades_preserves_real_records() -> None:
    history = [
        {
            "symbol": "BTCUSDT",
            "pnl": 1.0,
            "context": {"source": "manual_import"},
        },
        {
            "symbol": "ETHUSDT",
            "pnl": -1.0,
        },
    ]

    filtered = _strip_realized_income_trades(history)

    symbols = {entry["symbol"] for entry in filtered}
    assert symbols == {"BTCUSDT", "ETHUSDT"}


def test_strip_realized_income_trades_keeps_real_records_with_income_context() -> None:
    history = [
        {
            "symbol": "BTCUSDT",
            "pnl": 2.0,
            "context": {"source": "realized_income"},
        },
        {
            "symbol": "SYNTHUSDT",
            "pnl": -0.4,
            "synthetic": True,
            "context": {"source": "realized_income"},
        },
    ]

    filtered = _strip_realized_income_trades(history)

    symbols = {entry["symbol"] for entry in filtered}
    assert symbols == {"BTCUSDT"}


def test_resolve_history_with_realized_enriches_when_enabled(monkeypatch):
    history = [_make_trade(pnl=1.0, pnl_r=0.25)]
    env_cfg = {"ASTER_DASHBOARD_REALIZED_ENRICH": "true"}
    realized = [_make_income(4.0)]

    def fake_fetch(env: dict, limit: int = 400):
        assert env is env_cfg
        assert limit == 400
        return realized

    async def fake_to_thread(func, *args, **kwargs):
        return func(*args, **kwargs)

    import dashboard_server

    monkeypatch.setattr(dashboard_server, "_fetch_realized_pnl_entries", fake_fetch)
    monkeypatch.setattr(dashboard_server.asyncio, "to_thread", fake_to_thread)

    async def run() -> None:
        enriched = await _resolve_history_with_realized({"trade_history": history}, env_cfg)
        assert len(enriched) == 1
        record = enriched[0]
        assert record["pnl"] == pytest.approx(4.0)
        assert record["realized_pnl"] == pytest.approx(4.0)
        assert record.get("estimated_pnl") == pytest.approx(1.0)

    asyncio.run(run())


def test_resolve_history_with_realized_skips_when_disabled(monkeypatch):
    history = [_make_trade(pnl=2.5)]
    env_cfg = {"ASTER_DASHBOARD_REALIZED_ENRICH": "false"}

    def fake_fetch(_env: dict, limit: int = 400):
        raise AssertionError("fetch should not run when enrich flag is disabled")

    import dashboard_server

    monkeypatch.setattr(dashboard_server, "_fetch_realized_pnl_entries", fake_fetch)

    async def run() -> None:
        enriched = await _resolve_history_with_realized({"trade_history": history}, env_cfg)
        assert enriched == history

    asyncio.run(run())
