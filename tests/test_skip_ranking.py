import time
import unittest

from dashboard_server import _build_skip_ranking


class SkipRankingTests(unittest.TestCase):
    def test_skip_ranking_orders_by_score(self):
        now = time.time()
        state = {
            "ai_recent_plans": [
                {
                    "key": "plan::BTCUSDT::LONG",
                    "ts": now,
                    "plan": {
                        "symbol": "BTCUSDT",
                        "side": "LONG",
                        "take": False,
                        "confidence": 0.82,
                        "size_multiplier": 1.4,
                        "expected_r": 1.1,
                        "event_risk": 0.2,
                        "hype_score": 0.1,
                        "sentinel_factor": 0.15,
                        "budget_ratio": 0.85,
                        "decision_note": "Budget guard tripped",
                    },
                },
                {
                    "key": "plan::ETHUSDT::SHORT",
                    "ts": now - 90,
                    "plan": {
                        "symbol": "ETHUSDT",
                        "side": "SHORT",
                        "take": False,
                        "confidence": 0.35,
                        "size_multiplier": 0.0,
                        "expected_r": 0.4,
                        "event_risk": 0.65,
                        "hype_score": 0.55,
                        "sentinel_factor": 0.7,
                        "budget_ratio": 1.25,
                        "decision_reason": "sentinel_block",
                        "sentinel_label": "RED",
                    },
                },
            ]
        }

        ranking = _build_skip_ranking(state)
        self.assertEqual(len(ranking), 2)
        top, second = ranking
        self.assertEqual(top["symbol"], "BTCUSDT")
        self.assertGreater(top["score"], second["score"])
        self.assertGreater(top["score"], 0)
        self.assertGreaterEqual(second["score"], 0)
        self.assertIsInstance(top.get("score_components"), list)
        self.assertTrue(any(component.get("label") for component in top["score_components"]))
        self.assertEqual(second.get("reason_label"), "Sentinel guardrail")
        self.assertIsNotNone(top.get("ts_iso"))
        self.assertIn("plan", top)
        self.assertIn("context", top)

    def test_skip_ranking_filters_taken_plans(self):
        state = {
            "ai_recent_plans": [
                {
                    "key": "plan::FILUSDT::LONG",
                    "ts": time.time(),
                    "plan": {
                        "symbol": "FILUSDT",
                        "side": "LONG",
                        "take": True,
                        "confidence": 0.9,
                    },
                },
                {
                    "key": "plan::OPUSDT::SHORT",
                    "ts": time.time(),
                    "plan": {
                        "symbol": "OPUSDT",
                        "side": "SHORT",
                        "take": False,
                        "confidence": 0.5,
                        "event_risk": 0.3,
                        "expected_r": 0.7,
                    },
                },
            ]
        }

        ranking = _build_skip_ranking(state)
        self.assertEqual(len(ranking), 1)
        self.assertEqual(ranking[0]["symbol"], "OPUSDT")
        self.assertGreater(ranking[0]["score"], 0)


if __name__ == "__main__":
    unittest.main()
