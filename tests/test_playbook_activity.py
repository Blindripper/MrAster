import unittest

from dashboard_server import _collect_playbook_activity


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


if __name__ == "__main__":
    unittest.main()
