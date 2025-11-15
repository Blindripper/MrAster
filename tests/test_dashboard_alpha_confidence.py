import math


from dashboard_server import _extract_alpha_confidence, CONFIG


def _with_config(env: dict):
    original = {k: (v.copy() if isinstance(v, dict) else v) for k, v in CONFIG.items()}
    CONFIG.clear()
    CONFIG.update({"env": dict(env)})
    return original


def test_confidence_uses_state_min_conf():
    state = {
        "policy": {
            "alpha": {
                "train_count": 0.0,
                "conf_scale": 40.0,
                "min_conf": 0.3,
            }
        }
    }
    confidence = _extract_alpha_confidence(state)
    assert confidence == 0.3


def test_confidence_falls_back_to_env(monkeypatch):
    original = _with_config({"ASTER_ALPHA_MIN_CONF": "0.45"})
    try:
        state = {"policy": {"alpha": {"train_count": 0.0, "conf_scale": 40.0}}}
        confidence = _extract_alpha_confidence(state)
        assert math.isclose(confidence, 0.45)
    finally:
        CONFIG.clear()
        CONFIG.update(original)


def test_confidence_prefers_decision_stats(monkeypatch):
    original = _with_config({"ASTER_AI_CONF_SCALE": "10"})
    try:
        state = {
            "decision_stats": {
                "taken": 10,
                "rejected_total": 5,
                "last_updated": 123.0,
            },
            "policy": {"alpha": {"train_count": 400.0, "conf_scale": 40.0, "min_conf": 0.2}},
        }
        confidence = _extract_alpha_confidence(state)
        expected = (1.0 - math.exp(-(10 + 5) / 10.0)) * (10 / 15.0)
        assert math.isclose(confidence, expected)
    finally:
        CONFIG.clear()
        CONFIG.update(original)


def test_confidence_ignores_stale_decision_stats(monkeypatch):
    state = {
        "decision_stats": {"taken": 4, "rejected_total": 2},
        "policy": {"alpha": {"train_count": 0.0, "conf_scale": 40.0, "min_conf": 0.6}},
    }
    confidence = _extract_alpha_confidence(state)
    assert math.isclose(confidence, 0.6)


def test_confidence_requires_acceptances_for_decision_stats(monkeypatch):
    original = _with_config({})
    try:
        state = {
            "decision_stats": {
                "taken": 0,
                "rejected_total": 7,
                "last_updated": 1_720_000_000.0,
            },
            "policy": {
                "alpha": {
                    "train_count": 12.0,
                    "conf_scale": 40.0,
                    "min_conf": 0.55,
                }
            },
        }
        confidence = _extract_alpha_confidence(state)
        assert math.isclose(confidence, 0.55)
    finally:
        CONFIG.clear()
        CONFIG.update(original)


def test_confidence_falls_back_to_defaults(monkeypatch):
    original = _with_config({})
    try:
        state = {"policy": {"alpha": {"train_count": 0.0, "conf_scale": 40.0}}}
        confidence = _extract_alpha_confidence(state)
        assert math.isclose(confidence, 0.2)
    finally:
        CONFIG.clear()
        CONFIG.update(original)
