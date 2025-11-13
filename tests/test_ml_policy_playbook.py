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


def test_eps_gate_introduces_random_take_probability():
    random.seed(42)
    policy = BanditPolicy()
    policy.eps_gate = 0.3
    policy.gate.predict_ucb = lambda x: -0.4
    takes = sum(1 for _ in range(200) if policy.decide({})[0] == "TAKE")
    assert takes >= 40


def test_bandit_policy_warmup_grace_period_expires():
    policy = BanditPolicy(warmup_trades=2)
    policy.eps_gate = 0.0
    policy.skip_push = 0.0
    policy.gate_margin = 0.0
    policy.gate.predict_ucb = lambda x: -0.02
    policy.size.predict_ucb = lambda x: 0.0

    ctx = {}

    decision1, extras1 = policy.decide(ctx)
    assert decision1 == "TAKE"
    policy.note_entry("sym", ctx=ctx, size_bucket=extras1["size_bucket"])
    policy.note_exit("sym", ctx=ctx, size_bucket=extras1["size_bucket"], pnl_r=0.0)

    decision2, extras2 = policy.decide(ctx)
    assert decision2 == "TAKE"
    policy.note_entry("sym", ctx=ctx, size_bucket=extras2["size_bucket"])
    policy.note_exit("sym", ctx=ctx, size_bucket=extras2["size_bucket"], pnl_r=0.0)

    decision3, extras3 = policy.decide(ctx)
    assert decision3 == "SKIP"
    assert "alpha_prob" not in extras3  # alpha disabled by default


def test_alpha_policy_blocks_trades_after_warmup():
    policy = BanditPolicy(
        alpha_enabled=True,
        alpha_threshold=0.55,
        alpha_warmup=2,
        alpha_min_conf=0.2,
    )
    policy.eps_gate = 0.0
    policy.skip_push = 0.0
    policy.gate_margin = 0.0
    policy.gate.predict_ucb = lambda x: 0.2
    policy.size.predict_ucb = lambda x: 0.0
    policy.gate.learn = lambda x, r: None
    policy.size.learn = lambda x, r: None

    ctx = {}

    for _ in range(2):
        decision, extras = policy.decide(ctx)
        assert decision == "TAKE"
        policy.note_entry("sym", ctx=ctx, size_bucket=extras["size_bucket"])
        policy.note_exit("sym", ctx=ctx, size_bucket=extras["size_bucket"], pnl_r=-0.5)

    decision_final, extras_final = policy.decide(ctx)
    assert extras_final["alpha_ready"] is True
    assert extras_final["alpha_prob"] < policy.alpha_threshold
    assert decision_final == "SKIP"
