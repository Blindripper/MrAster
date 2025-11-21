import importlib
import sys
from pathlib import Path

import pytest


class _DummyExchange:
    pass


def _reload_with_env(monkeypatch, env=None):
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        monkeypatch.syspath_prepend(str(project_root))

    env = env or {}
    for key, value in env.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, str(value))

    sys.modules.pop("aster_multi_bot", None)
    return importlib.import_module("aster_multi_bot")


@pytest.mark.parametrize("mode", ["standard", "ai"])
@pytest.mark.parametrize("preset", ["low", "mid", "high", "att"])
def test_min_quote_volume_respects_env(monkeypatch, mode, preset):
    expected = 123_456.0
    bot = _reload_with_env(
        monkeypatch,
        {
            "ASTER_MODE": mode,
            "ASTER_PRESET_MODE": preset,
            "ASTER_MIN_QUOTE_VOL_USDT": expected,
        },
    )

    assert bot.MIN_QUOTE_VOL == pytest.approx(expected)

    strategy = bot.Strategy(exchange=_DummyExchange())
    assert strategy.min_quote_vol == pytest.approx(expected)
