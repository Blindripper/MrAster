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


def test_confidence_falls_back_to_defaults(monkeypatch):
    original = _with_config({})
    try:
        state = {"policy": {"alpha": {"train_count": 0.0, "conf_scale": 40.0}}}
        confidence = _extract_alpha_confidence(state)
        assert math.isclose(confidence, 0.2)
    finally:
        CONFIG.clear()
        CONFIG.update(original)
