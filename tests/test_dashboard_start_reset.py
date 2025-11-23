import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import dashboard_server


def test_clear_live_state_resets_decision_stats(monkeypatch, tmp_path):
    state_file = tmp_path / "state.json"
    state = {
        "decision_stats": {"taken": 3, "rejected_total": 1, "rejected": {"foo": 1}},
        "live_trades": {"BTCUSDT": {"order": "123"}},
        "other": "keep",
    }
    state_file.write_text(json.dumps(state))
    monkeypatch.setattr(dashboard_server, "STATE_FILE", state_file)

    dashboard_server._clear_live_state()

    saved = json.loads(state_file.read_text())
    assert saved["decision_stats"] == {
        "taken": 0,
        "taken_by_bucket": {},
        "rejected": {},
        "rejected_total": 0,
        "last_updated": None,
    }
    assert "live_trades" not in saved
    assert saved["other"] == "keep"
