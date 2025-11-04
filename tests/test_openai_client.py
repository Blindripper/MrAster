import asyncio

import pytest

from openai_client import (
    OpenAIClient,
    OpenAIError,
    is_responses_unsupported_error,
)


def test_is_responses_unsupported_error_detects_common_messages() -> None:
    payload = {
        "error": {
            "message": "The model gpt-4o-mini does not support the responses API. Use the chat.completions endpoint.",
            "code": "model_not_supported",
        }
    }
    assert is_responses_unsupported_error(payload) is True

    assert is_responses_unsupported_error({"error": {"message": "Unexpected"}}) is False


def test_client_disables_responses_after_incompatible_error(monkeypatch: pytest.MonkeyPatch) -> None:
    client = OpenAIClient("test-key", default_model="gpt-4o-mini")

    calls = {"responses": 0, "legacy": 0}

    async def fake_acreate(self, **kwargs):  # type: ignore[override]
        calls["responses"] += 1
        raise OpenAIError(
            400,
            "Unsupported",
            payload={
                "error": {
                    "message": "The model does not support the responses API",
                    "code": "model_not_supported",
                }
            },
        )

    async def fake_legacy(self, **kwargs):  # type: ignore[override]
        calls["legacy"] += 1
        return "ok", None, {"choices": [{"message": {"content": "ok"}}]}

    monkeypatch.setattr(OpenAIClient, "acreate", fake_acreate)
    monkeypatch.setattr(OpenAIClient, "_legacy_chat_completion", fake_legacy)

    async def _run() -> None:
        await client._acreate_with_fallback(messages=[{"role": "user", "content": "hi"}])
        await client._acreate_with_fallback(messages=[{"role": "user", "content": "hi again"}])

    try:
        asyncio.run(_run())
    finally:
        client.close()

    assert calls["responses"] == 1
    assert calls["legacy"] == 2
