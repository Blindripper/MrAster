import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from dashboard_server import AIChatEngine, CONFIG


@pytest.fixture
def engine() -> AIChatEngine:
    return AIChatEngine(CONFIG)


def test_beta_header_includes_reasoning_for_o1_models(engine: AIChatEngine) -> None:
    assert engine._beta_header_for_model("o1") == "reasoning"
    assert engine._beta_header_for_model("o1-mini") == "reasoning"


def test_o1_marked_as_responses_only(engine: AIChatEngine) -> None:
    traits = engine._model_traits("o1")
    assert traits["legacy_supported"] is False
    assert traits["reasoning"] == {"effort": "medium"}
