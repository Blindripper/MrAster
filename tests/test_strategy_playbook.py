import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from aster_multi_bot import Strategy  # noqa: E402


class StrategyPlaybookManagerTests(unittest.TestCase):
    def test_strategy_has_playbook_manager_attribute(self):
        exchange = MagicMock()
        strategy = Strategy(exchange, decision_tracker=None, state={})

        self.assertTrue(hasattr(strategy, "playbook_manager"))
        self.assertIsNone(strategy.playbook_manager)

        snapshot = strategy._playbook_snapshot()
        self.assertIn("timestamp", snapshot)


if __name__ == "__main__":
    unittest.main()
