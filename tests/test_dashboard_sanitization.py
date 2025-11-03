import asyncio
import json

import dashboard_server as server


def test_loghub_masks_sensitive_tokens(monkeypatch):
    hub = server.LogHub()
    monkeypatch.setattr(server, "_SENSITIVE_TOKEN_VALUES", ("super-secret",))

    asyncio.run(hub.push("prefix super-secret suffix"))

    assert hub.buffer[-1]["line"] == f"prefix {server._REDACTED_TOKEN} suffix"


def test_mask_sensitive_payload_masks_fields(monkeypatch):
    monkeypatch.setattr(server, "_SENSITIVE_TOKEN_VALUES", ("hide-me",))

    payload = {
        "ASTER_API_KEY": "hide-me",
        "nested": {
            "OPENAI_API_KEY": "hide-me",
            "other": "keep",
        },
        "list_values": ["hide-me", {"ASTER_CHAT_OPENAI_API_KEY": "hide-me"}],
    }

    masked = server._mask_sensitive_payload(payload)

    assert masked["ASTER_API_KEY"] == server._REDACTED_TOKEN
    assert masked["nested"]["OPENAI_API_KEY"] == server._REDACTED_TOKEN
    assert masked["nested"]["other"] == "keep"
    assert masked["list_values"][0] == server._REDACTED_TOKEN
    assert masked["list_values"][1]["ASTER_CHAT_OPENAI_API_KEY"] == server._REDACTED_TOKEN


def test_append_ai_activity_entry_masks_state(monkeypatch, tmp_path):
    monkeypatch.setattr(server, "_SENSITIVE_TOKEN_VALUES", ("12345",))
    temp_state = tmp_path / "state.json"
    monkeypatch.setattr(server, "STATE_FILE", temp_state)

    server._append_ai_activity_entry(
        "info",
        "Headline 12345",
        body="Body 12345",
        data={"ASTER_API_SECRET": "12345", "details": ["12345"]},
    )

    state = json.loads(temp_state.read_text())
    entry = state["ai_activity"][-1]

    assert server._REDACTED_TOKEN in entry["headline"]
    assert server._REDACTED_TOKEN in entry["body"]
    assert entry["data"]["ASTER_API_SECRET"] == server._REDACTED_TOKEN
    assert entry["data"]["details"][0] == server._REDACTED_TOKEN
