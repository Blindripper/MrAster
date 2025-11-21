import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import dashboard_server


def test_trade_export_payload_preserves_exit_reason():
    history_entry = {
        "symbol": "COAIUSDT",
        "opened_at": 1732230000.0,
        "closed_at": 1732233600.0,
        "management": {"last_exit_reason": "trail"},
    }

    payload = dashboard_server._build_trade_export_payload({"history": [history_entry]})

    assert payload["history"], "history should not be empty"
    record = payload["history"][0]
    assert record.get("exit_reason") == "trail"
    assert record.get("management_exit_reason") == "trail"
    assert record.get("opened_at_iso")
    assert record.get("closed_at_iso")
