from typing import Any, Dict

import pytest

from aster_multi_bot import Bot


def _bot_with_state(state: Dict[str, Any]) -> Bot:
    bot = Bot.__new__(Bot)  # type: ignore
    bot.state = state
    bot._hype_history_dirty = False  # type: ignore[attr-defined]
    return bot


def _make_history(values: Dict[str, list]) -> Dict[str, Any]:
    return {symbol: list(entries) for symbol, entries in values.items()}


def test_hype_correlation_blocks_without_strong_breadth(monkeypatch: pytest.MonkeyPatch) -> None:
    base_time = 1_000_000.0
    history = _make_history(
        {
            "ETHUSDT": [
                {"ts": base_time - 9, "value": 0.1},
                {"ts": base_time - 6, "value": 0.4},
                {"ts": base_time - 3, "value": 0.7},
                {"ts": base_time - 1, "value": 0.9},
            ],
            "BTCUSDT": [
                {"ts": base_time - 9, "value": 0.05},
                {"ts": base_time - 6, "value": 0.35},
                {"ts": base_time - 3, "value": 0.65},
                {"ts": base_time - 1, "value": 0.85},
            ],
        }
    )
    bot = _bot_with_state({Bot.HYPE_HISTORY_KEY: history})
    monkeypatch.setattr("aster_multi_bot.time.time", lambda: base_time)

    ctx: Dict[str, Any] = {}
    result = bot._check_correlated_hype("BTCUSDT", "BUY", {"ETHUSDT": 1.0}, ctx)

    assert result["blocked"] is True
    assert result["penalty"] == pytest.approx(1.0)
    assert result["conflicts"]
    assert result["breadth"] is None


def test_hype_correlation_penalises_when_breadth_strong(monkeypatch: pytest.MonkeyPatch) -> None:
    base_time = 2_000_000.0
    history = _make_history(
        {
            "ETHUSDT": [
                {"ts": base_time - 12, "value": 0.15},
                {"ts": base_time - 8, "value": 0.45},
                {"ts": base_time - 4, "value": 0.75},
                {"ts": base_time - 1, "value": 0.95},
            ],
            "BTCUSDT": [
                {"ts": base_time - 12, "value": 0.12},
                {"ts": base_time - 8, "value": 0.42},
                {"ts": base_time - 4, "value": 0.72},
                {"ts": base_time - 1, "value": 0.92},
            ],
        }
    )
    bot = _bot_with_state({Bot.HYPE_HISTORY_KEY: history})
    monkeypatch.setattr("aster_multi_bot.time.time", lambda: base_time)

    ctx: Dict[str, Any] = {"breadth": 0.96}
    result = bot._check_correlated_hype("BTCUSDT", "BUY", {"ETHUSDT": 2.5}, ctx)

    assert result["blocked"] is False
    assert result["penalty"] == pytest.approx(0.5)
    assert result["conflicts"]
    assert result["breadth"] == pytest.approx(0.96)


def test_hype_correlation_ignores_non_long_positions(monkeypatch: pytest.MonkeyPatch) -> None:
    base_time = 3_000_000.0
    history = _make_history(
        {
            "ETHUSDT": [
                {"ts": base_time - 6, "value": 0.2},
                {"ts": base_time - 3, "value": 0.4},
                {"ts": base_time - 1, "value": 0.6},
                {"ts": base_time - 0.2, "value": 0.8},
            ],
        }
    )
    bot = _bot_with_state({Bot.HYPE_HISTORY_KEY: history})
    monkeypatch.setattr("aster_multi_bot.time.time", lambda: base_time)

    ctx: Dict[str, Any] = {"breadth": 0.5}
    result = bot._check_correlated_hype("BTCUSDT", "SELL", {"ETHUSDT": -1.0}, ctx)

    assert result["blocked"] is False
    assert result["penalty"] == pytest.approx(1.0)
    assert not result["conflicts"]


def test_record_hype_score_trims_history(monkeypatch: pytest.MonkeyPatch) -> None:
    bot = _bot_with_state({})
    now = 4_000_000.0
    monkeypatch.setattr("aster_multi_bot.time.time", lambda: now)

    bot._record_hype_score("BTCUSDT", 0.4)
    assert bot.state[Bot.HYPE_HISTORY_KEY]["BTCUSDT"]
    assert bot._hype_history_dirty is True  # type: ignore[attr-defined]

    monkeypatch.setattr("aster_multi_bot.time.time", lambda: now + Bot.HYPE_HISTORY_WINDOW_SEC + 5)
    bot._record_hype_score("BTCUSDT", 0.6)

    history = bot.state[Bot.HYPE_HISTORY_KEY]["BTCUSDT"]
    assert all(
        (now + Bot.HYPE_HISTORY_WINDOW_SEC + 5) - entry["ts"] <= Bot.HYPE_HISTORY_WINDOW_SEC
        for entry in history
    )
    assert len(history) <= Bot.HYPE_HISTORY_LIMIT
