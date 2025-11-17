import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import dashboard_server


def test_enrich_open_positions_preserves_management_payload(monkeypatch):
    sample_open = {
        "standard": {
            "DEXEUSDT": {
                "symbol": "DEXEUSDT",
                "side": "SELL",
                "management_exit_reason": "expected_r_stop",
                "management_events": [
                    {
                        "ts": 1713371234.0,
                        "action": "expected_r_stop",
                        "stop": 5.12,
                    }
                ],
            }
        }
    }

    snapshot_payload = {
        "DEXEUSDT": {
            "entryPrice": 5.48,
            "markPrice": 5.45,
            "side": "SELL",
        }
    }

    monkeypatch.setattr(
        dashboard_server,
        "_fetch_position_snapshot",
        lambda env: snapshot_payload,
    )
    monkeypatch.setattr(
        dashboard_server,
        "_fetch_position_brackets",
        lambda env, symbols, recv_window: {},
    )

    enriched = dashboard_server.enrich_open_positions(sample_open, {})

    assert isinstance(enriched, list)
    assert len(enriched) == 1
    record = enriched[0]

    assert record["symbol"] == "DEXEUSDT"
    assert record["entry"] == snapshot_payload["DEXEUSDT"]["entryPrice"]
    assert record["mark_price"] == snapshot_payload["DEXEUSDT"]["markPrice"]
    assert record["management_exit_reason"] == "expected_r_stop"
    events = record.get("management_events")
    assert isinstance(events, list)
    assert events and events[0]["action"] == "expected_r_stop"
