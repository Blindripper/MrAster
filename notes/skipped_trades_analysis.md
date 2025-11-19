# Skipped Trade Analysis — 2025-11-19 snapshot

## Dataset Overview

* Total skipped trades: **13,971**, of which **8,578** (61.4%) were quote-volume cooldowns and excluded from filter tuning.
* Remaining filter-related skips: **5,393** across 15 reasons.

| Reason | Count | Share of filter skips |
| --- | ---: | ---: |
| edge_r | 1,852 | 34.34% |
| no_cross | 1,288 | 23.88% |
| trend_extension | 687 | 12.74% |
| short_trend_alignment | 588 | 10.90% |
| spread_tight | 443 | 8.21% |
| long_overextended | 209 | 3.88% |
| stoch_rsi_trend_short | 145 | 2.69% |
| continuation_pullback | 91 | 1.69% |
| wicky | 50 | 0.93% |
| non_arb_bias_long | 10 | 0.19% |
| quality_gate | 10 | 0.19% |
| arb_gate | 9 | 0.17% |
| non_arb_bias_short | 5 | 0.09% |
| min_qvol | 3 | 0.06% |
| stoch_rsi_penalty | 3 | 0.06% |

## Near-miss intensity per filter

The table below summarizes the relative gap between each sample trade and its filter limit (lower = closer to passing).
| Reason | Samples | Closest rel. gap | Median rel. gap | 90th pct. rel. gap |
| --- | ---: | ---: | ---: | ---: |
| edge_r | 40 | 0.041 | 0.143 | 0.980 |
| trend_extension | 40 | 0.227 | 0.864 | 2.636 |
| short_trend_alignment | 40 | 0.075 | 1.000 | 1.000 |
| spread_tight | 40 | 0.015 | 0.200 | 0.923 |
| long_overextended | 40 | 0.008 | 0.475 | 1.100 |
| stoch_rsi_trend_short | 40 | 0.088 | 0.782 | 0.912 |
| continuation_pullback | 40 | 0.000 | 0.107 | 0.111 |
| wicky | 40 | 0.005 | 0.005 | 0.005 |
| non_arb_bias_long | 10 | 0.640 | 4.460 | 12.260 |
| non_arb_bias_short | 5 | 4.400 | 5.640 | 5.660 |
| stoch_rsi_penalty | 3 | 0.091 | 0.109 | 0.164 |
| min_qvol | 3 | 0.323 | 0.832 | 0.995 |

## Top 1% closest failures

The closest 4 trades (top 1% of the 341 parsed samples) were:
| Rank | Reason | Symbol | Detail | Relative gap |
| --- | --- | --- | --- | ---: |
| 1 | continuation_pullback | FARTCOINUSDT | Stoch Rsi K 90.0 • Gate 90.0 | 0.0000 |
| 2 | wicky | BEATUSDT | W 1.00 | 0.0050 |
| 3 | wicky | BEATUSDT | W 1.00 | 0.0050 |
| 4 | wicky | AVAXUSDT | W 1.00 | 0.0050 |

Key observations:
* `continuation_pullback` rejected a trade exactly at the stoch RSI gate (90.0), so making the gate strict `>` would let it pass without loosening the threshold.
* `wicky` accounted for the remaining near-misses; wickiness was only **0.005** above the 0.995 cap, so adding a fixed +0.005 tolerance (effective cap 1.000) lets those trades through while still blocking highly wick-prone candles.