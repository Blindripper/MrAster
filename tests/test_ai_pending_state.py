import os
import sys
from concurrent.futures import Future

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from aster_multi_bot import AITradeAdvisor, DailyBudgetTracker  # noqa: E402


def _make_advisor() -> tuple[AITradeAdvisor, dict]:
    state: dict = {}
    budget = DailyBudgetTracker(state, limit=5.0, strict=True)
    advisor = AITradeAdvisor("key", "gpt-4.1", budget, state, enabled=False)
    advisor._pending_order.clear()
    advisor._pending_requests.clear()
    advisor._sync_pending_state()
    return advisor, state


def test_sync_pending_state_serializes_queue() -> None:
    advisor, state = _make_advisor()
    throttle_key = "plan::BTCUSDT"
    advisor._pending_order.append(throttle_key)
    advisor._pending_requests[throttle_key] = {
        "future": None,
        "kind": "plan",
        "queued_at": 12.5,
        "note": "Queued for AI planning",
        "request_id": "req-plan",
        "request_meta": {"symbol": "BTCUSDT"},
    }

    advisor._sync_pending_state()

    snapshot = state.get("ai_pending_requests")
    assert isinstance(snapshot, list)
    assert len(snapshot) == 1
    entry = snapshot[0]
    assert entry["key"] == throttle_key
    assert entry["status"] == "queued"
    assert entry["request_id"] == "req-plan"
    assert entry["symbol"] == "BTCUSDT"
    assert entry["kind"] == "plan"


def test_sync_pending_state_marks_inflight_and_clears() -> None:
    advisor, state = _make_advisor()
    throttle_key = "trend::ETHUSDT"
    advisor._pending_order.append(throttle_key)
    advisor._pending_requests[throttle_key] = {
        "future": None,
        "kind": "trend",
        "queued_at": 33.0,
        "note": "Queued",
        "request_id": "req-trend",
        "request_meta": {"symbol": "ETHUSDT"},
    }
    advisor._sync_pending_state()

    fut = Future()
    advisor._pending_requests[throttle_key]["future"] = fut
    advisor._pending_requests[throttle_key]["dispatched_at"] = 34.0
    advisor._sync_pending_state()

    snapshot = state.get("ai_pending_requests")
    assert isinstance(snapshot, list)
    assert snapshot and snapshot[0]["status"] == "inflight"

    advisor._remove_pending_entry(throttle_key)
    assert state.get("ai_pending_requests") == []
