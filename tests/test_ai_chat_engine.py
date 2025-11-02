import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from dashboard_server import AIChatEngine, CONFIG, _safe_float


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


def test_gpt41_allows_legacy_fallback(engine: AIChatEngine) -> None:
    traits = engine._model_traits("gpt-4.1")
    assert traits["legacy_supported"] is True
    assert traits["reasoning"] is None


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


def test_safe_float_extracts_numeric_fragment() -> None:
    assert _safe_float(" 120 USDT ") == pytest.approx(120.0)
    assert _safe_float("approx. 1,250.50 units") == pytest.approx(1250.5)


def test_normalize_trade_proposal_falls_back_to_default_notional(engine: AIChatEngine) -> None:
    payload = {
        "symbol": "BTCUSDT",
        "direction": "LONG",
        "entry_price": 100.0,
        "stop_loss": 95.0,
        "take_profit": 110.0,
    }
    normalized = engine._normalize_trade_proposal(payload)
    assert normalized is not None
    assert normalized["notional"] == pytest.approx(120.0)


def test_structured_trade_proposals_handle_plain_text_blocks(engine: AIChatEngine) -> None:
    sample = (
        "Market Analysis\n"
        "LONG Idea\n"
        "Symbol: ETHUSDT\n"
        "Timeframe: 4H\n"
        "Thesis: ETHUSDT is consolidating near support at 3,850 USDT with stable volume.\n"
        "Entry Zone: 3,850–3,870 USDT\n"
        "Invalidation: Close below 3,800 USDT\n"
        "Target: 4,050 USDT\n"
        "Catalysts: BTC stabilization, ETH-specific news, or broader risk-on sentiment.\n"
        "Caveats: If BTC breaks down, invalidation may trigger quickly.\n\n"
        "SHORT Idea\n"
        "Symbol: SOLUSDT\n"
        "Timeframe: 4H\n"
        "Thesis: SOLUSDT is showing mild downward momentum at 184.94 USDT with solid volume.\n"
        "Entry Zone: 184–185 USDT\n"
        "Invalidation: Close above 188 USDT\n"
        "Target: 175 USDT\n"
        "Catalysts: Continued bearish sentiment and lack of recovery signals.\n"
        "Data Caveats: Confidence limited if liquidity fades.\n"
    )

    proposals = engine._extract_trade_proposals(sample)
    assert len(proposals) >= 2

    by_symbol = {item["symbol"]: item for item in proposals}
    assert {"ETHUSDT", "SOLUSDT"}.issubset(by_symbol.keys())

    eth = by_symbol["ETHUSDT"]
    assert eth["direction"] == "LONG"
    assert eth["entry_kind"] == "limit"
    assert eth["entry_price"] == pytest.approx(3860.0)
    assert eth["stop_loss"] == pytest.approx(3800.0)
    assert eth["take_profit"] == pytest.approx(4050.0)
    assert eth["notional"] == pytest.approx(120.0)

    sol = by_symbol["SOLUSDT"]
    assert sol["direction"] == "SHORT"
    assert sol["entry_kind"] == "limit"
    assert sol["entry_price"] == pytest.approx(184.5)
    assert sol["stop_loss"] == pytest.approx(188.0)
    assert sol["take_profit"] == pytest.approx(175.0)
    assert sol["notional"] == pytest.approx(120.0)
