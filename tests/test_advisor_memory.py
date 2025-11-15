import os
from typing import Any, Dict, Tuple

import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from aster_multi_bot import AITradeAdvisor, DailyBudgetTracker  # noqa: E402


def _make_advisor() -> Tuple[AITradeAdvisor, Dict[str, Any]]:
    state: Dict[str, Any] = {}
    budget = DailyBudgetTracker(state, limit=10.0, strict=True)
    advisor = AITradeAdvisor("key", "gpt-4.1", budget, state, enabled=False)
    return advisor, state


def test_parameter_tuner_distils_postmortem_lessons() -> None:
    advisor, state = _make_advisor()
    tuner = advisor.parameter_tuner
    assert tuner is not None

    trade = {"symbol": "BTCUSDT", "side": "BUY", "bucket": "M", "pnl_r": -1.2}
    features = {"funding_edge": 0.9, "pm_trend_break": 0.2}

    for _ in range(3):
        tuner.observe(dict(trade), dict(features))

    memory = state.get("advisor_memory", {})
    lessons = memory.get("lessons", {}) if isinstance(memory, dict) else {}
    assert "funding_edge" in lessons
    assert lessons["funding_edge"].get("snippet")

    ctx: Dict[str, Any] = {"funding_edge": 0.8}
    tuner.inject_context(ctx)

    snippets = ctx.get("advisor_memory_snippets")
    assert ctx.get("advisor_memory_active") == 1.0
    assert isinstance(snippets, list) and snippets
    assert any("funding" in str(snippet).lower() for snippet in snippets)
    focus = ctx.get("advisor_memory_focus", [])
    assert any(str(item).startswith("funding") for item in focus)
