import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from aster_multi_bot import _trend_sl_bias  # type: ignore  # noqa: E402


def test_trend_sl_bias_rewards_strong_trend() -> None:
    ctx = {
        "trend_strength": 0.9,
        "expected_r": 0.45,
        "min_edge_r_dynamic": 0.2,
        "quality_gate_pass": 1.0,
        "filter_penalty_score": 0.1,
        "filter_bonus_score": 0.6,
        "adx_filter": 32.0,
        "slope_htf": 0.004,
    }

    bias, quality = _trend_sl_bias(ctx, side="BUY")

    assert 0.5 < quality <= 1.0
    assert bias > 1.0


def test_trend_sl_bias_tightens_on_poor_setup() -> None:
    ctx = {
        "trend_strength": 0.1,
        "expected_r": 0.05,
        "min_edge_r_dynamic": 0.3,
        "filter_penalty_score": 2.0,
        "adx_filter": 12.0,
        "slope_htf": 0.003,
    }

    bias, quality = _trend_sl_bias(ctx, side="SELL")

    assert 0.0 <= quality < 0.5
    assert bias < 1.0
