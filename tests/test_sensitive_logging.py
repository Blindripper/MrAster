import copy

import aster_multi_bot as bot


def test_mask_sensitive_text_replaces_known_tokens(monkeypatch):
    monkeypatch.setattr(bot, "_SENSITIVE_TOKEN_VALUES", ("supersecret",), raising=False)

    original = "prefix supersecret suffix"
    masked = bot._mask_sensitive_text(original)

    assert masked == f"prefix {bot._REDACTED_TOKEN} suffix"


def test_mask_sensitive_payload_masks_nested_values(monkeypatch):
    monkeypatch.setattr(bot, "_SENSITIVE_TOKEN_VALUES", ("shh-key",), raising=False)

    payload = {
        "plain": "value",
        "string_secret": "header shh-key footer",
        "nested": {
            "ASTER_API_KEY": "should hide",
            "details": [
                "shh-key",
                {"ASTER_OPENAI_API_KEY": "also hide", "other": "ok"},
            ],
        },
    }

    snapshot = copy.deepcopy(payload)
    masked = bot._mask_sensitive_payload(payload)

    # Original payload remains untouched
    assert payload == snapshot

    # String replacement uses the redaction token
    assert masked["string_secret"] == f"header {bot._REDACTED_TOKEN} footer"

    # Fields that match sensitive names are redacted entirely
    assert masked["nested"]["ASTER_API_KEY"] == bot._REDACTED_TOKEN
    assert masked["nested"]["details"][0] == bot._REDACTED_TOKEN
    assert masked["nested"]["details"][1]["ASTER_OPENAI_API_KEY"] == bot._REDACTED_TOKEN
    # Unrelated values stay intact
    assert masked["nested"]["details"][1]["other"] == "ok"
