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


def test_mask_sensitive_payload_redacts_change_entries(monkeypatch):
    # Ensure runtime key rotations are masked even when the value was not seen at import time
    monkeypatch.setattr(bot, "_SENSITIVE_TOKEN_VALUES", tuple(), raising=False)

    payload = {
        "changes": [
            {
                "key": "ASTER_OPENAI_API_KEY",
                "old": "sk-old-123",
                "new": "sk-new-456",
            },
            {
                "key": "ASTER_AI_NEWS_API_KEY",
                "old": "news-old-token",
                "new": "news-new-token",
            },
            {
                "key": "UNRELATED_KEY",
                "old": "before",
                "new": "after",
            },
        ]
    }

    masked = bot._mask_sensitive_payload(payload)

    sensitive_change, sentinel_change, other_change = masked["changes"]

    assert sensitive_change["old"] == bot._REDACTED_TOKEN
    assert sensitive_change["new"] == bot._REDACTED_TOKEN
    assert sentinel_change["old"] == bot._REDACTED_TOKEN
    assert sentinel_change["new"] == bot._REDACTED_TOKEN

    assert other_change["old"] == "before"
    assert other_change["new"] == "after"


def test_collect_sensitive_tokens_includes_sentinel_tokens(monkeypatch):
    monkeypatch.setattr(bot, "SENTINEL_NEWS_TOKEN", "news-secret", raising=False)
    monkeypatch.setattr(bot, "SENTINEL_ONCHAIN_TOKEN", "onchain-secret", raising=False)
    monkeypatch.setattr(bot, "SENTINEL_SOCIAL_TOKEN", "social-secret", raising=False)
    monkeypatch.setattr(bot, "SENTINEL_OPTIONS_TOKEN", "options-secret", raising=False)

    monkeypatch.setenv("ASTER_AI_NEWS_API_KEY", "news-secret")
    monkeypatch.setenv("ASTER_AI_ONCHAIN_API_KEY", "onchain-secret")
    monkeypatch.setenv("ASTER_AI_SOCIAL_API_KEY", "social-secret")
    monkeypatch.setenv("ASTER_AI_OPTIONS_API_KEY", "options-secret")

    tokens = bot._collect_sensitive_tokens()

    for expected in (
        "news-secret",
        "onchain-secret",
        "social-secret",
        "options-secret",
    ):
        assert expected in tokens
