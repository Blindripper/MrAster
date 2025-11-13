import os
import sys
import unittest
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from dashboard_server import (
    _build_playbook_process,
    _collect_playbook_activity,
    _derive_playbook_state_from_activity,
    _normalize_playbook_state,
    _resolve_playbook_state,
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

    def test_collects_strategy_payload(self):
        payload = [
            {
                "kind": "playbook",
                "headline": "Playbook updated",
                "ts": "2024-07-01T10:07:00Z",
                "data": {
                    "request_id": "req-strategy",
                    "strategy": {
                        "name": "Range Fade",
                        "why_active": "Range-bound session with capped volatility",
                        "actions": [
                            {
                                "title": "Fade extremes",
                                "detail": "Sell near resistance and buy near support when volume stays muted.",
                            }
                        ],
                    },
                },
            }
        ]

        result = _collect_playbook_activity(payload)
        self.assertEqual(len(result), 1)
        entry = result[0]
        self.assertEqual(entry["request_id"], "req-strategy")
        self.assertIn("strategy", entry)
        self.assertEqual(entry["strategy"]["name"], "Range Fade")
        self.assertEqual(entry["reason"], "Range-bound session with capped volatility")

    def test_detects_tuning_entries(self):
        payload = [
            {
                "kind": "tuning",
                "headline": "Risk tuning update",
                "ts": "2024-07-01T10:06:00Z",
                "data": {
                    "request_kind": "tuning",
                    "request_id": "tuning::alpha:1234",
                    "sl_atr_mult": 1.15,
                    "tp_atr_mult": 1.05,
                    "size_bias": {"S": 0.55, "M": 0.63, "L": 0.63},
                    "confidence": 0.05,
                    "note": "Testing",
                },
            }
        ]
        result = _collect_playbook_activity(payload)
        self.assertEqual(len(result), 1)
        entry = result[0]
        self.assertEqual(entry["request_id"], "tuning::alpha:1234")
        self.assertAlmostEqual(entry["sl_bias"], 1.15)
        self.assertAlmostEqual(entry["tp_bias"], 1.05)
        self.assertAlmostEqual(entry["confidence"], 0.05)

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

    def test_ignores_entries_with_other_request_kind(self):
        payload = [
            {
                "kind": "info",
                "headline": "Strategy copilot insight",
                "ts": "2024-07-01T10:20:00Z",
                "data": {
                    "request_kind": "strategy",
                    "request_id": "strategy::insight:abcd",
                    "size_bias": {"S": 1.1},
                    "features": {"example": 0.5},
                },
            }
        ]
        result = _collect_playbook_activity(payload)
        self.assertEqual(result, [])

    def test_ignores_entries_with_analysis_mode(self):
        payload = [
            {
                "kind": "info",
                "headline": "Manual market analysis requested",
                "ts": "2024-07-01T10:25:00Z",
                "data": {
                    "mode": "analysis",
                    "bias": "neutral",
                    "size_bias": {"BUY": 1.0, "SELL": 1.0},
                },
            }
        ]

        result = _collect_playbook_activity(payload)
        self.assertEqual(result, [])

    def test_ignores_entries_with_analysis_request_id(self):
        payload = [
            {
                "kind": "info",
                "headline": "Analysis refresh pipeline",
                "ts": "2024-07-01T10:26:00Z",
                "data": {
                    "request_id": "analysis::analysis:5163801eddb4",
                    "size_bias": {"S": 0.9},
                    "tp_atr_mult": 1.05,
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

    def test_process_skips_anonymous_cycle_markers(self):
        raw = [
            {
                "kind": "info",
                "headline": "Playbook refresh cycle started",
                "ts": "2024-07-01T09:00:00Z",
            },
            {
                "kind": "info",
                "headline": "Playbook refresh cycle finished",
                "ts": "2024-07-01T09:00:10Z",
            },
        ]

        activity = _collect_playbook_activity(raw)
        self.assertEqual(len(activity), 2)

        process = _build_playbook_process(activity)
        self.assertEqual(process, [])

    def test_process_ignores_pending_cycles_without_request_id(self):
        raw = [
            {
                "kind": "query",
                "headline": "Playbook refresh requested",
                "ts": "2024-07-01T09:05:00Z",
            },
            {
                "kind": "query",
                "headline": "Playbook refresh requested",
                "ts": "2024-07-01T09:06:00Z",
            },
        ]

        activity = _collect_playbook_activity(raw)
        self.assertEqual(len(activity), 2)

        process = _build_playbook_process(activity)
        self.assertEqual(process, [])

    def test_process_skips_signal_entries_without_request_id(self):
        raw = [
            {
                "kind": "playbook",
                "headline": "Event regime snapshot",
                "ts": "2024-07-01T11:00:00Z",
                "data": {
                    "mode": "event_hype",
                    "bias": "neutral",
                    "size_bias": {"BUY": 1.05, "SELL": 0.95},
                    "sl_atr_mult": 1.1,
                },
            },
            {
                "kind": "playbook",
                "headline": "Event regime snapshot",
                "ts": "2024-07-01T12:00:00Z",
                "data": {
                    "mode": "event_hype",
                    "bias": "neutral",
                    "size_bias": {"BUY": 1.02, "SELL": 0.98},
                    "tp_atr_mult": 0.95,
                },
            },
        ]

        activity = _collect_playbook_activity(raw)
        self.assertEqual(len(activity), 2)

        process = _build_playbook_process(activity)
        self.assertEqual(process, [])


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

    def test_normalize_state_includes_strategy(self):
        raw = {
            "active": {
                "mode": "breakout",
                "bias": "bullish",
                "strategy": {
                    "name": "Breakout Momentum",
                    "objective": "Capitalize on strong breakout moves",
                    "why_active": "Trend and breadth both show sustained expansion",
                    "market_signals": ["ADX rising", "Volume acceleration"],
                    "actions": [
                        {
                            "title": "Confirm breakout",
                            "detail": "Wait for candle close above resistance with volume > 1.5× baseline.",
                            "trigger": "Price closes above resistance",
                        }
                    ],
                    "risk_controls": ["Cut exposure if sentinel turns yellow", "Disable leverage on event spikes"],
                },
            }
        }

        state = _normalize_playbook_state(raw)
        self.assertIsNotNone(state)
        self.assertIn("strategy", state)
        strategy = state["strategy"]
        self.assertEqual(strategy["name"], "Breakout Momentum")
        self.assertIn("market_signals", strategy)
        self.assertIn("actions", strategy)
        self.assertEqual(state["reason"], "Trend and breadth both show sustained expansion")

    def test_derive_state_from_activity(self):
        raw_activity = [
            {
                "kind": "playbook",
                "headline": "Playbook updated: momentum",
                "ts": "2024-07-01T10:05:00Z",
                "data": {
                    "mode": "momentum squeeze",
                    "bias": "bullish",
                    "size_bias": {"BUY": 1.2, "SELL": 0.8},
                    "sl_bias": 1.15,
                    "tp_bias": 0.95,
                    "confidence": 0.33,
                    "notes": "Rotation favouring majors",
                },
            }
        ]

        activity = _collect_playbook_activity(raw_activity)
        state = _derive_playbook_state_from_activity(activity)
        self.assertIsNotNone(state)
        self.assertEqual(state["mode"], "momentum squeeze")
        self.assertEqual(state["bias"], "bullish")
        self.assertAlmostEqual(state["size_bias"]["BUY"], 1.2)
        self.assertAlmostEqual(state["sl_bias"], 1.15)
        self.assertAlmostEqual(state["confidence"], 0.33)
        self.assertIn("refreshed", state)

    def test_resolve_state_prefers_activity_when_placeholder(self):
        placeholder = {
            "active": {
                "mode": "baseline",
                "bias": "neutral",
                "size_bias": {"BUY": 1.0, "SELL": 1.0},
                "sl_bias": 1.0,
                "tp_bias": 1.0,
                "features": {},
                "refreshed": 0,
            }
        }

        raw_activity = [
            {
                "kind": "playbook",
                "headline": "Playbook updated: breakout",
                "ts": "2024-07-01T11:00:00Z",
                "data": {
                    "mode": "breakout",
                    "bias": "bullish",
                    "size_bias": {"BUY": 1.3, "SELL": 0.7},
                    "sl_bias": 1.25,
                },
            }
        ]

        activity = _collect_playbook_activity(raw_activity)
        resolved = _resolve_playbook_state(placeholder, activity)
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved["mode"], "breakout")
        self.assertAlmostEqual(resolved["size_bias"]["BUY"], 1.3)
        self.assertIn("refreshed_ts", resolved)

    def test_resolve_state_keeps_existing_when_fresh(self):
        raw_state = {
            "active": {
                "mode": "range",
                "bias": "bearish",
                "size_bias": {"BUY": 0.8, "SELL": 1.2},
                "sl_bias": 1.05,
                "tp_bias": 1.4,
                "features": {"breadth": -0.4},
                "refreshed": datetime(2024, 7, 1, 12, 0, 0, tzinfo=timezone.utc).timestamp(),
            }
        }

        raw_activity = [
            {
                "kind": "playbook",
                "headline": "Playbook updated: breakout",
                "ts": "2024-07-01T13:00:00Z",
                "data": {
                    "mode": "breakout",
                    "bias": "bullish",
                },
            }
        ]

        activity = _collect_playbook_activity(raw_activity)
        resolved = _resolve_playbook_state(raw_state, activity)
        self.assertEqual(resolved["mode"], "range")
        self.assertEqual(resolved["bias"], "bearish")
        self.assertAlmostEqual(resolved["size_bias"]["SELL"], 1.2)

    def test_tuning_entries_default_to_baseline_neutral(self):
        raw_activity = [
            {
                "kind": "tuning",
                "headline": "Parameter tuning update",
                "ts": "2024-07-01T14:00:00Z",
                "data": {
                    "request_kind": "tuning",
                    "sl_atr_mult": 1.1,
                    "tp_atr_mult": 1.25,
                    "size_bias": {"S": 1.2, "M": 1.05},
                    "confidence": 0.22,
                },
            }
        ]

        activity = _collect_playbook_activity(raw_activity)
        state = _derive_playbook_state_from_activity(activity)
        self.assertIsNotNone(state)
        self.assertEqual(state["mode"], "baseline")
        self.assertEqual(state["bias"], "neutral")
        self.assertAlmostEqual(state["sl_bias"], 1.1)
        self.assertAlmostEqual(state["tp_bias"], 1.25)
        self.assertAlmostEqual(state["size_bias"]["S"], 1.2)


if __name__ == "__main__":
    unittest.main()
