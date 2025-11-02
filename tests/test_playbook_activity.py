import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from dashboard_server import (
    _build_playbook_process,
    _collect_playbook_activity,
    _normalize_playbook_state,
)


class PlaybookActivityTests(unittest.TestCase):
    def test_detects_entries_with_request_kind(self):
        payload = [
            {
                "kind": "alert",
                "headline": "AI budget exhausted",
                "ts": "2024-07-01T10:00:00Z",
                "data": {
                    "request_kind": "playbook",
                    "request_id": "req-1",
                    "reason": "budget_exhausted",
                },
            }
        ]
        result = _collect_playbook_activity(payload)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["request_id"], "req-1")
        self.assertEqual(result[0]["request_kind"], "playbook")

    def test_detects_entries_with_playbook_payload(self):
        payload = [
            {
                "kind": "info",
                "headline": "Momentum regime update",
                "ts": "2024-07-01T10:05:00Z",
                "data": {
                    "mode": "momentum",
                    "bias": "bullish",
                    "size_bias": {"BUY": 1.2, "SELL": 0.9},
                    "sl_bias": 1.1,
                },
            }
        ]
        result = _collect_playbook_activity(payload)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["mode"], "momentum")
        self.assertEqual(result[0]["bias"], "bullish")

    def test_ignores_unrelated_entries(self):
        payload = [
            {
                "kind": "response",
                "headline": "AI response for BTCUSDT",
                "ts": "2024-07-01T10:10:00Z",
                "data": {
                    "symbol": "BTCUSDT",
                    "notes": ["some insight"],
                },
            }
        ]
        result = _collect_playbook_activity(payload)
        self.assertEqual(result, [])


class PlaybookProcessTests(unittest.TestCase):
    def test_process_groups_successful_flow(self):
        raw = [
            {
                "kind": "query",
                "headline": "Playbook refresh requested",
                "ts": "2024-07-01T10:00:00Z",
                "data": {"request_id": "req-1", "snapshot_meta": {"technical": 42}},
            },
            {
                "kind": "playbook",
                "headline": "Playbook updated: momentum",
                "ts": "2024-07-01T10:05:00Z",
                "data": {
                    "request_id": "req-1",
                    "mode": "momentum",
                    "bias": "bullish",
                    "size_bias": {"BUY": 1.1, "SELL": 0.9},
                },
            },
        ]
        activity = _collect_playbook_activity(raw)
        process = _build_playbook_process(activity)
        self.assertEqual(len(process), 1)
        entry = process[0]
        self.assertEqual(entry["request_id"], "req-1")
        self.assertEqual(entry["status"], "applied")
        stages = [step["stage"] for step in entry["steps"]]
        self.assertEqual(stages, ["requested", "applied"])

    def test_process_marks_failures(self):
        raw = [
            {
                "kind": "query",
                "headline": "Playbook refresh requested",
                "ts": "2024-07-01T10:00:00Z",
                "data": {"request_id": "req-2"},
            },
            {
                "kind": "error",
                "headline": "Playbook refresh failed",
                "ts": "2024-07-01T10:01:30Z",
                "data": {"request_id": "req-2", "reason": "timeout"},
            },
        ]
        activity = _collect_playbook_activity(raw)
        process = _build_playbook_process(activity)
        self.assertEqual(len(process), 1)
        entry = process[0]
        self.assertEqual(entry["status"], "failed")
        stages = [step["stage"] for step in entry["steps"]]
        self.assertEqual(stages[-1], "failed")


class PlaybookStateTests(unittest.TestCase):
    def test_collects_atr_keys_and_confidence(self):
        payload = [
            {
                "kind": "playbook",
                "headline": "Playbook tuning update",
                "ts": "2024-07-01T10:15:00Z",
                "data": {
                    "request_id": "req-3",
                    "size_bias": {"S": 0.55, "M": 0.63, "L": 0.63},
                    "sl_atr_mult": 1.15,
                    "tp_atr_mult": 1.05,
                    "confidence": 0.05,
                    "note": "Testing new schema",
                },
            }
        ]

        result = _collect_playbook_activity(payload)
        self.assertEqual(len(result), 1)
        entry = result[0]
        self.assertEqual(entry["request_id"], "req-3")
        self.assertAlmostEqual(entry["sl_bias"], 1.15)
        self.assertAlmostEqual(entry["tp_bias"], 1.05)
        self.assertAlmostEqual(entry["confidence"], 0.05)
        self.assertIn("S", entry["size_bias"])
        self.assertIn("M", entry["size_bias"])
        self.assertIn("L", entry["size_bias"])
        self.assertEqual(entry["notes"], "Testing new schema")

    def test_normalize_state_supports_new_schema(self):
        raw = {
            "active": {
                "mode": "tuning",
                "bias": "bearish",
                "size_bias": {"S": 0.55, "M": 0.63},
                "sl_atr_mult": 1.2,
                "tp_atr_mult": 0.9,
                "confidence": 0.12,
                "note": "Example note",
            }
        }

        state = _normalize_playbook_state(raw)
        self.assertIsNotNone(state)
        self.assertAlmostEqual(state["sl_bias"], 1.2)
        self.assertAlmostEqual(state["tp_bias"], 0.9)
        self.assertIn("S", state["size_bias"])
        self.assertIn("M", state["size_bias"])
        self.assertAlmostEqual(state["confidence"], 0.12)
        self.assertEqual(state["notes"], "Example note")


if __name__ == "__main__":
    unittest.main()
