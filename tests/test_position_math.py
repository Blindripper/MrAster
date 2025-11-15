import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_node(script: str) -> list:
    result = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout.strip())


def test_derive_position_mark_price_variants():
    script = """
import { derivePositionMarkPrice } from './dashboard_static/position_math.js';

const outputs = [];
outputs.push(derivePositionMarkPrice({ mark: 123.45, entry: 100, quantity: 2, pnl: 20 }));
outputs.push(derivePositionMarkPrice({ mark: null, entry: 100, quantity: 2, pnl: 20 }));
outputs.push(derivePositionMarkPrice({ mark: null, entry: 100, quantity: -2, pnl: 20 }));
outputs.push(derivePositionMarkPrice({ mark: null, entry: 100, quantity: null, notional: 500, pnl: 50, side: 'BUY' }));
outputs.push(derivePositionMarkPrice({ mark: null, entry: 100, quantity: null, notional: 500, pnl: 50, side: 'SELL' }));
outputs.push(derivePositionMarkPrice({ mark: null, entry: 100, quantity: null, notional: null, pnl: 50 }));
console.log(JSON.stringify(outputs));
"""
    values = _run_node(script)
    assert values[0] == pytest.approx(123.45)
    assert values[1] == pytest.approx(110.0)
    assert values[2] == pytest.approx(90.0)
    assert values[3] == pytest.approx(110.0)
    assert values[4] == pytest.approx(90.0)
    assert values[5] is None
