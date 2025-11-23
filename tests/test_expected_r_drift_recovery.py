import os
import sys
import time

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import aster_multi_bot
from aster_multi_bot import TradeManager


def _make_manager() -> TradeManager:
    return TradeManager(exchange=object(), policy=None, state={})


def test_expected_r_drift_probation_after_cooldown(monkeypatch: pytest.MonkeyPatch) -> None:
    manager = _make_manager()
    monkeypatch.setattr(aster_multi_bot, "EXPECTED_R_DRIFT_RECOVERY_MINUTES", 0.001)
    monkeypatch.setattr(aster_multi_bot, "EXPECTED_R_DRIFT_RECOVERY_MULT", 0.3)

    ctx = {"expected_r_signal_drift": aster_multi_bot.EXPECTED_R_DRIFT_HALT * 2}

    mult, blocked = manager._expected_r_drift_multiplier(ctx)
    assert blocked is True
    assert mult == 0.0

    time.sleep(0.1)

    mult, blocked = manager._expected_r_drift_multiplier(ctx)
    assert blocked is False
    assert 0.0 < mult <= aster_multi_bot.EXPECTED_R_DRIFT_RECOVERY_MULT
    status = manager.state.get("expected_r_drift_status")
    assert isinstance(status, dict) and status.get("recovering") is True


def test_expected_r_drift_recovers_when_drift_improves(monkeypatch: pytest.MonkeyPatch) -> None:
    manager = _make_manager()
    monkeypatch.setattr(aster_multi_bot, "EXPECTED_R_DRIFT_RECOVERY_MINUTES", 0.001)
    monkeypatch.setattr(aster_multi_bot, "EXPECTED_R_DRIFT_RECOVERY_MULT", 0.25)

    hard_ctx = {"expected_r_signal_drift": aster_multi_bot.EXPECTED_R_DRIFT_HALT * 1.2}
    soft_ctx = {"expected_r_signal_drift": aster_multi_bot.EXPECTED_R_DRIFT_SOFT * 0.6}

    mult, blocked = manager._expected_r_drift_multiplier(hard_ctx)
    assert blocked is True
    assert mult == 0.0

    time.sleep(0.1)
    mult, blocked = manager._expected_r_drift_multiplier(hard_ctx)
    assert blocked is False
    assert mult == pytest.approx(aster_multi_bot.EXPECTED_R_DRIFT_RECOVERY_MULT, rel=1e-6)

    mult, blocked = manager._expected_r_drift_multiplier(soft_ctx)
    assert blocked is False
    assert mult == 1.0
    assert manager.state.get("expected_r_drift_status") == {}


def test_expected_r_drift_recovery_ramps_up(monkeypatch: pytest.MonkeyPatch) -> None:
    manager = _make_manager()
    monkeypatch.setattr(aster_multi_bot, "EXPECTED_R_DRIFT_RECOVERY_MINUTES", 0.001)
    monkeypatch.setattr(aster_multi_bot, "EXPECTED_R_DRIFT_RECOVERY_MULT", 0.2)

    ctx = {"expected_r_signal_drift": aster_multi_bot.EXPECTED_R_DRIFT_HALT * 1.1}
    manager._expected_r_drift_multiplier(ctx)
    time.sleep(0.1)

    ctx_medium = {"expected_r_signal_drift": (aster_multi_bot.EXPECTED_R_DRIFT_SOFT + aster_multi_bot.EXPECTED_R_DRIFT_HALT) / 2}
    mult, blocked = manager._expected_r_drift_multiplier(ctx_medium)

    assert blocked is False
    assert mult >= aster_multi_bot.EXPECTED_R_DRIFT_MIN_MULT
    assert mult <= 1.0
