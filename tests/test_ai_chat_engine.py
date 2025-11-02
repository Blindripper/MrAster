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


def test_responses_payload_normalises_text(monkeypatch: pytest.MonkeyPatch, engine: AIChatEngine) -> None:
    captured: dict = {}

    class DummyResponse:
        status_code = 200

        @staticmethod
        def json() -> dict:
            return {
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {"type": "output_text", "text": "ok"},
                        ],
                    }
                ]
            }

    def fake_post(url: str, headers: dict, json: dict, timeout: int) -> DummyResponse:
        captured["url"] = url
        captured["payload"] = json
        return DummyResponse()

    monkeypatch.setattr("dashboard_server.requests.post", fake_post)

    messages = [
        {"role": "system", "content": " system "},
        {"role": "user", "content": [{"type": "input_text", "text": " hello "}]},
        {"role": "assistant", "content": " ack "},
        {"role": "user", "content": [" next "]},
    ]

    reply, usage = engine._call_openai_responses({}, "gpt-4.1-mini", messages, temperature=0.2)

    assert reply == "ok"
    assert usage is None
    assert captured["url"].endswith("/responses")
    payload = captured["payload"]
    assert payload["model"] == "gpt-4.1-mini"
    system_entry = payload["input"][0]
    assert system_entry["role"] == "system"
    assert system_entry["content"][0]["type"] == "text"
    # Ensure all user/assistant entries normalise to "text" segments
    for entry in payload["input"][1:]:
        for chunk in entry["content"]:
            assert chunk["type"] == "text"
