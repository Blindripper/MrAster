from dashboard_server import _prepare_display_history


def test_prepare_display_history_keeps_synthetic_trades():
    history = [
        {
            "symbol": "BTCUSDT",
            "pnl": 12.5,
            "opened_at": 1_700_000_000.0,
            "closed_at": 1_700_000_120.0,
        },
        {
            "symbol": "SYNTHUSDT",
            "pnl": -4.2,
            "synthetic": True,
            "synthetic_source": "realized_income",
            "opened_at": 1_700_000_200.0,
            "closed_at": 1_700_000_200.0,
        },
    ]

    display = _prepare_display_history(history)

    assert len(display) == 2
    synth = display[1]
    assert synth["symbol"] == "SYNTHUSDT"
    assert synth["synthetic"] is True
    assert synth["closed_at_iso"] is not None
    assert "T" in synth["closed_at_iso"]
    assert display[0]["opened_at_iso"].startswith("2023")
