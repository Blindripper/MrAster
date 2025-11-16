import pytest

import aster_multi_bot as bot


def test_atr_adverse_distance_prefers_risk(monkeypatch):
    monkeypatch.setattr(bot, "ATR_ADVERSE_EXIT_MULT", 0.5)
    dist = bot._atr_adverse_distance(2.0, 1.0)
    assert dist == pytest.approx(1.0)


def test_atr_adverse_distance_falls_back_to_atr(monkeypatch):
    monkeypatch.setattr(bot, "ATR_ADVERSE_EXIT_MULT", 0.5)
    dist = bot._atr_adverse_distance(0.0, 3.0)
    assert dist == pytest.approx(1.5)
