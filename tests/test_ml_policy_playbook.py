import random

from ml_policy import BanditPolicy


def _policy():
    policy = BanditPolicy()
    policy.eps_gate = 0.0
    policy.gate.predict_ucb = lambda x: 0.2
    policy.size.predict_ucb = lambda x: 0.1
    return policy


def test_bandit_policy_penalizes_low_playbook_risk_bias():
    random.seed(0)
    policy = _policy()
    ctx = {"playbook_risk_bias": 0.6}
    decision, extras = policy.decide(ctx)
    assert decision == "SKIP"
    assert extras["playbook_risk_bias"] == ctx["playbook_risk_bias"]
    assert extras["playbook_risk_penalty"] > 0


def test_bandit_policy_rewards_high_playbook_risk_bias():
    random.seed(0)
    policy = _policy()
    policy.gate.predict_ucb = lambda x: -0.05
    ctx = {"playbook_risk_bias": 1.3}
    decision, extras = policy.decide(ctx)
    assert decision == "TAKE"
    assert extras["playbook_risk_bonus"] > 0
