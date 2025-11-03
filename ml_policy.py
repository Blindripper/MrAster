# ml_policy.py — LinUCB Bandit für Gate (TAKE/SKIP) + Größenbucket (S/M/L)
from __future__ import annotations
import math, time, random
from typing import Dict, Optional, Tuple, Any

try:
    import numpy as np
except Exception:
    raise RuntimeError("ml_policy.py benötigt numpy. Bitte im venv: pip install numpy")

# Feature-Vektor (muss zum Bot passen)
FEATURES = (
    "adx",
    "atr_pct",
    "slope_htf",
    "rsi",
    "funding",
    "funding_edge",
    "oracle_gap",
    "oracle_gap_clamped",
    "qv_score",
    "trend",
    "regime_adx",
    "regime_slope",
    "spread_bps",
    "lob_imbalance_5",
    "lob_imbalance_10",
    "lob_depth_ratio",
    "lob_gap_score",
    "lob_wall_score",
    "orderbook_bias",
    "orderbook_levels",
    "supertrend_dir",
    "supertrend",
    "bb_position",
    "bb_width",
    "stoch_rsi_d",
    "non_arb_region",
    "pm_trend_break",
    "pm_news_driver",
    "pm_liquidity_gap",
    "pm_execution_delay",
    "pm_sentiment_conflict",
    "pm_macro_event",
    "tuning_risk_bias",
    "tuning_size_bias",
    "tuning_confidence",
    "playbook_breakout_bias",
    "playbook_range_bias",
    "playbook_trend_bias",
    "budget_bias",
    "sentinel_event_risk",
    "sentinel_hype",
    "sentinel_onchain_pressure",
    "sentinel_onchain_flow",
    "sentinel_social_sentiment",
    "sentinel_options_skew",
    "expected_r",
    "lob_snapshot_age",
    "lob_bid_support",
    "lob_ask_pressure",
    "lob_gap_bid",
    "lob_gap_ask",
    "playbook_regime_volatility",
    "playbook_regime_activity",
    "playbook_regime_liquidity",
    "playbook_regime_sentiment",
    "playbook_regime_skew",
    "playbook_regime_budget_util",
    "budget_opportunity_cost",
    "budget_slippage_cost",
)

def _vec_from_ctx(ctx: Dict[str, float]) -> "np.ndarray":
    return np.array([float(ctx.get(k, 0.0) or 0.0) for k in FEATURES], dtype=float).reshape(-1, 1)  # d×1

# ------------------------------ LinUCB ---------------------------------------
class LinUCB:
    def __init__(self, alpha: float = 1.0, l2: float = 1e-3, d: Optional[int] = None):
        self.alpha = float(alpha)
        self.l2 = float(l2)
        self.d = int(d or len(FEATURES))
        self.A = np.eye(self.d) * self.l2  # d×d
        self.b = np.zeros((self.d, 1))  # d×1
        self._A_inv: Optional[np.ndarray] = None
        if self.l2 > 0:
            self._A_inv = np.eye(self.d) / self.l2

    def predict_ucb(self, x: "np.ndarray") -> float:
        # x: d×1
        if self._A_inv is None:
            try:
                self._A_inv = np.linalg.pinv(self.A)
            except np.linalg.LinAlgError:
                self._A_inv = np.linalg.pinv(self.A + np.eye(self.d) * 1e-9)
        A_inv = self._A_inv
        theta = A_inv @ self.b  # d×1
        mu = float((theta.T @ x)[0, 0])
        Ax = A_inv @ x
        var = float((x.T @ Ax)[0, 0])
        if var < 0.0:
            var = 0.0
        s = float(math.sqrt(var))
        return mu + self.alpha * s

    def learn(self, x: "np.ndarray", reward: float) -> None:
        self.A += x @ x.T
        self.b += float(reward) * x
        if self._A_inv is not None:
            try:
                Ax = self._A_inv @ x
                denom = 1.0 + float((x.T @ Ax)[0, 0])
                if denom <= 1e-12:
                    self._A_inv = None
                else:
                    update = Ax @ Ax.T / denom
                    self._A_inv = self._A_inv - update
            except Exception:
                self._A_inv = None

    def to_dict(self) -> Dict[str, Any]:
        return {"alpha": self.alpha, "l2": self.l2, "d": self.d, "A": self.A.tolist(), "b": self.b.tolist()}

    @classmethod
    def from_dict(cls, d: Dict[str, Any], *, target_dim: Optional[int] = None) -> "LinUCB":
        target_dim = int(target_dim or len(FEATURES))
        obj = cls(alpha=float(d.get("alpha", 1.0)), l2=float(d.get("l2", 1e-3)), d=target_dim)
        stored_A = np.array(d.get("A", []), dtype=float)
        stored_b = np.array(d.get("b", []), dtype=float)

        if stored_A.size and stored_A.shape == (target_dim, target_dim):
            obj.A = stored_A
        elif stored_A.size:
            obj.A = np.eye(target_dim) * obj.l2
            min_dim = min(stored_A.shape[0], stored_A.shape[1], target_dim)
            obj.A[:min_dim, :min_dim] = stored_A[:min_dim, :min_dim]
        else:
            obj.A = np.eye(target_dim) * obj.l2

        stored_b = stored_b.reshape(-1, 1) if stored_b.ndim <= 2 else stored_b[:, :1]
        if stored_b.size and stored_b.shape == (target_dim, 1):
            obj.b = stored_b
        elif stored_b.size:
            obj.b = np.zeros((target_dim, 1))
            min_dim = min(stored_b.shape[0], target_dim)
            obj.b[:min_dim, 0] = stored_b[:min_dim, 0]
        else:
            obj.b = np.zeros((target_dim, 1))
        obj._A_inv = None
        return obj

# ---------------------------- Alpha Model ------------------------------------
class AlphaModel:
    def __init__(
        self,
        lr: float = 0.05,
        l2: float = 5e-4,
        min_conf: float = 0.1,
        reward_margin: float = 0.05,
        conf_scale: float = 40.0,
    ) -> None:
        self.lr = float(lr)
        self.l2 = float(l2)
        self.min_conf = float(min_conf)
        self.reward_margin = float(abs(reward_margin))
        self.conf_scale = max(1.0, float(conf_scale))
        self.weights: Optional[np.ndarray] = None
        self.mean: Optional[np.ndarray] = None
        self.m2: Optional[np.ndarray] = None
        self.norm_count: float = 0.0
        self.train_count: float = 0.0
        self.last_prob: float = 0.5

    def _ensure_stats(self) -> None:
        target = len(FEATURES)
        if self.mean is None or len(self.mean) != target:
            if self.mean is None:
                self.mean = np.zeros(target, dtype=float)
                self.m2 = np.zeros(target, dtype=float)
            else:
                new_mean = np.zeros(target, dtype=float)
                new_m2 = np.zeros(target, dtype=float)
                upto = min(len(self.mean), target)
                if upto:
                    new_mean[:upto] = self.mean[:upto]
                    new_m2[:upto] = self.m2[:upto]
                self.mean = new_mean
                self.m2 = new_m2
                if self.norm_count < 0:
                    self.norm_count = 0.0

    def _norm(self, x_raw: np.ndarray, update: bool) -> np.ndarray:
        self._ensure_stats()
        if update:
            self.norm_count += 1.0
            delta = x_raw - self.mean
            self.mean += delta / self.norm_count
            self.m2 += delta * (x_raw - self.mean)
        if self.norm_count > 1:
            var = self.m2 / max(self.norm_count - 1.0, 1.0)
            std = np.sqrt(np.maximum(var, 1e-6))
        else:
            std = np.ones_like(x_raw)
        return (x_raw - self.mean) / std

    def _vec(self, ctx: Dict[str, float]) -> np.ndarray:
        return np.array([float(ctx.get(k, 0.0) or 0.0) for k in FEATURES], dtype=float)

    def _ensure_weight_shape(self, size: int) -> None:
        if self.weights is None:
            return
        if self.weights.shape[0] != size:
            new_weights = np.zeros(size, dtype=float)
            upto = min(self.weights.shape[0], size)
            if upto:
                new_weights[:upto] = self.weights[:upto]
            self.weights = new_weights

    def predict(self, ctx: Dict[str, float]) -> Tuple[float, float]:
        x_raw = self._vec(ctx)
        x_norm = self._norm(x_raw, update=False)
        x = np.append(x_norm, 1.0)
        self._ensure_weight_shape(len(x))
        if self.weights is None:
            prob = 0.5
        else:
            z = float(np.dot(self.weights, x))
            prob = 1.0 / (1.0 + math.exp(-z))
        prob = float(np.clip(prob, 1e-4, 1.0 - 1e-4))
        self.last_prob = prob
        conf = max(self.min_conf, 1.0 - math.exp(-self.train_count / self.conf_scale))
        return prob, conf

    def learn(self, ctx: Dict[str, float], reward: float) -> None:
        if ctx is None:
            return
        if reward > self.reward_margin:
            target = 1.0
        elif reward < -self.reward_margin:
            target = 0.0
        else:
            return
        weight = min(1.0, max(0.1, abs(reward)))
        x_raw = self._vec(ctx)
        x_norm = self._norm(x_raw, update=True)
        x = np.append(x_norm, 1.0)
        if self.weights is None:
            self.weights = np.zeros_like(x)
        else:
            self._ensure_weight_shape(len(x))
        z = float(np.dot(self.weights, x))
        prob = 1.0 / (1.0 + math.exp(-z))
        error = (prob - target) * weight
        grad = error * x + self.l2 * self.weights
        self.weights = self.weights - self.lr * grad
        self.train_count += weight
        self.last_prob = float(prob)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "weights": self.weights.tolist() if self.weights is not None else None,
            "mean": self.mean.tolist() if self.mean is not None else None,
            "m2": self.m2.tolist() if self.m2 is not None else None,
            "norm_count": self.norm_count,
            "train_count": self.train_count,
            "lr": self.lr,
            "l2": self.l2,
            "min_conf": self.min_conf,
            "reward_margin": self.reward_margin,
            "conf_scale": self.conf_scale,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlphaModel":
        obj = cls(
            lr=float(data.get("lr", 0.05)),
            l2=float(data.get("l2", 5e-4)),
            min_conf=float(data.get("min_conf", 0.1)),
            reward_margin=float(data.get("reward_margin", 0.05)),
            conf_scale=float(data.get("conf_scale", 40.0)),
        )
        target = len(FEATURES)
        bias_size = target + 1
        if data.get("weights") is not None:
            weights = np.array(data.get("weights"), dtype=float)
            weights = weights.flatten()
            if weights.shape[0] != bias_size:
                new_weights = np.zeros(bias_size, dtype=float)
                upto = min(weights.shape[0], bias_size)
                if upto:
                    new_weights[:upto] = weights[:upto]
                weights = new_weights
            obj.weights = weights
        if data.get("mean") is not None:
            mean = np.array(data.get("mean"), dtype=float).flatten()
            if mean.shape[0] != target:
                new_mean = np.zeros(target, dtype=float)
                upto = min(mean.shape[0], target)
                if upto:
                    new_mean[:upto] = mean[:upto]
                mean = new_mean
            obj.mean = mean
        if data.get("m2") is not None:
            m2 = np.array(data.get("m2"), dtype=float).flatten()
            if m2.shape[0] != target:
                new_m2 = np.zeros(target, dtype=float)
                upto = min(m2.shape[0], target)
                if upto:
                    new_m2[:upto] = m2[:upto]
                m2 = new_m2
            obj.m2 = m2
        obj.norm_count = float(data.get("norm_count", 0.0))
        obj.train_count = float(data.get("train_count", 0.0))
        return obj

# --------------------------- BanditPolicy ------------------------------------
class BanditPolicy:
    """
    Entscheidung:
      - Gate: TAKE oder SKIP
      - Größe: S/M/L

    Hooks:
      - decide(ctx) -> ("TAKE"/"SKIP", {"size_bucket": "S|M|L"})
      - note_entry(symbol, ctx=..., size_bucket=...)
      - note_exit(symbol, pnl_r=...)  # Reward in R-Multiple
    """

    def __init__(
        self,
        gate_alpha: float = 1.2,
        size_alpha: float = 0.8,
        l2: float = 1e-3,
        warmup_trades: int = 30,
        enable_size: bool = True,
        size_multipliers: Optional[Dict[str, float]] = None,
        d: Optional[int] = None,
        *,
        alpha_enabled: bool = False,
        alpha_threshold: float = 0.55,
        alpha_warmup: int = 40,
        alpha_lr: float = 0.05,
        alpha_l2: float = 5e-4,
        alpha_min_conf: float = 0.2,
        alpha_promote_delta: float = 0.15,
        alpha_reward_margin: float = 0.05,
    ) -> None:
        self.gate = LinUCB(alpha=gate_alpha, l2=l2, d=d)
        self.size = LinUCB(alpha=size_alpha, l2=l2, d=d)
        self.enable_size = bool(enable_size)
        self.size_multipliers = dict(size_multipliers or {"S":1.0,"M":1.4,"L":1.9})
        self.warmup_trades = int(warmup_trades)

        self.feature_names = tuple(FEATURES)

        self.alpha_threshold = float(alpha_threshold)
        self.alpha_warmup = int(alpha_warmup)
        self.alpha_min_conf = float(alpha_min_conf)
        self.alpha_promote_delta = float(alpha_promote_delta)
        self.alpha_reward_margin = float(alpha_reward_margin)
        self.alpha_lr = float(alpha_lr)
        self.alpha_l2 = float(alpha_l2)
        self.alpha_enabled = bool(alpha_enabled)
        self.alpha: Optional[AlphaModel] = None
        if self.alpha_enabled:
            self.alpha = AlphaModel(
                lr=self.alpha_lr,
                l2=self.alpha_l2,
                min_conf=alpha_min_conf,
                reward_margin=alpha_reward_margin,
            )

        # Tunables (können später per ENV übergeben/gesetzt werden)
        self.eps_gate: float = 0.0          # ε-greedy Chance auf TAKE
        self.gate_margin: float = 0.0       # Margin-Anforderung auf UCB>0
        self.anti_stall_min: int = 60       # Mindestsekunden zwischen Trades (Anti-Stall aus)
        self.skip_push: float = 0.0         # Bonus auf SKIP (positiv = konservativer)

        # Laufzeit-Stats
        self.n_trades: int = 0
        self.last_trade_ts: float = 0.0

        # Puffer falls Bot Einhänge nicht jedes Mal übergibt
        self._last_ctx: Optional[Dict[str, float]] = None
        self._last_size_bucket: Optional[str] = None

    # ---------- API ----------
    def decide(self, ctx: Dict[str, float]) -> Tuple[str, Dict[str, Any]]:
        x = _vec_from_ctx(ctx)

        # Gate-Score: wir vergleichen TAKE vs. SKIP=0 baseline
        take_ucb = self.gate.predict_ucb(x) - self.skip_push
        event_risk = float(ctx.get("sentinel_event_risk", 0.0) or 0.0)
        hype_score = float(ctx.get("sentinel_hype", 0.0) or 0.0)
        risk_penalty = 0.0
        if event_risk > 0.32:
            risk_penalty += (event_risk - 0.32) * 1.2
            if event_risk > 0.55:
                risk_penalty += 0.05
        if hype_score > 0.86:
            risk_penalty += (hype_score - 0.86) * 0.6
        if risk_penalty > 0.0:
            take_ucb -= risk_penalty
        # Warmup: am Anfang eher großzügig
        if self.n_trades < self.warmup_trades:
            take_ucb += 0.05

        # ε-greedy
        if random.random() < self.eps_gate:
            decision = "TAKE"
        else:
            decision = "TAKE" if (take_ucb - self.gate_margin) > 0.0 else "SKIP"

        # Größe: UCB-Argmax über Buckets
        if not self.enable_size:
            size_bucket = "S"
        else:
            scores = {}
            for b in ("S","M","L"):
                # simple trick: unterschiedliche „Arme“ simulieren mit skaliertem Feature
                xb = x * self.size_multipliers[b]
                scores[b] = self.size.predict_ucb(xb)
            size_bucket = max(scores.items(), key=lambda kv: kv[1])[0]
        extras: Dict[str, Any] = {"size_bucket": size_bucket}
        if risk_penalty > 0.0:
            extras["risk_penalty"] = risk_penalty
            extras["risk_event"] = event_risk
            extras["risk_hype"] = hype_score

        if self.alpha:
            try:
                prob, conf = self.alpha.predict(ctx)
            except Exception:
                prob, conf = 0.5, self.alpha_min_conf
            extras["alpha_prob"] = prob
            extras["alpha_conf"] = conf
            ready = conf >= self.alpha_min_conf and self.n_trades >= self.alpha_warmup
            extras["alpha_ready"] = ready
            if ready and prob < self.alpha_threshold:
                decision = "SKIP"
            elif ready and prob > min(0.99, self.alpha_threshold + self.alpha_promote_delta):
                size_bucket = self._promote_bucket(size_bucket)
                extras["size_bucket"] = size_bucket
                # kein direkter Eingriff in LinUCB; Bucket-Anpassung reicht

        if decision == "TAKE" and self.enable_size and (event_risk > 0.45 or risk_penalty >= 0.2):
            demote_steps = 1
            if event_risk > 0.65 or risk_penalty >= 0.35:
                demote_steps = 2
            size_bucket = self._demote_bucket(size_bucket, demote_steps)
            extras["size_bucket"] = size_bucket
            extras["risk_demotion"] = demote_steps

        return decision, extras

    @staticmethod
    def _promote_bucket(bucket: str) -> str:
        order = ("S", "M", "L")
        try:
            idx = order.index(bucket)
        except ValueError:
            idx = 0
        return order[min(idx + 1, len(order) - 1)]

    @staticmethod
    def _demote_bucket(bucket: str, steps: int = 1) -> str:
        order = ("S", "M", "L")
        try:
            idx = order.index(bucket)
        except ValueError:
            idx = 0
        return order[max(0, idx - max(1, steps))]

    def note_entry(self, *args, **kwargs) -> None:
        """
        Schluckt alle Parameter, speichert (falls vorhanden) ctx/size_bucket,
        löst aber KEIN learn() aus (Reward gibt es erst am Exit).
        """
        ctx = kwargs.get("ctx") or kwargs.get("context")
        if isinstance(ctx, dict):
            self._last_ctx = dict(ctx)
        sb = kwargs.get("size_bucket") or kwargs.get("bucket")
        if isinstance(sb, str):
            self._last_size_bucket = sb
        self.last_trade_ts = time.time()
        self.n_trades += 1

    def _extract_reward(self, kwargs: dict) -> Optional[float]:
        for k in ("reward_r", "pnl_r", "r", "reward", "pnl_r_multiple"):
            if k in kwargs:
                try:
                    return float(kwargs.get(k))
                except Exception:
                    pass
        return None

    def note_exit(self, *args, **kwargs) -> None:
        """
        Optionaler Hook für Exit (TP/SL/Manuell). Erwartet idealerweise:
          - ctx=..., size_bucket=..., pnl_r=...
        Fällt zurück auf _last_ctx/_last_size_bucket, wenn nichts mitgegeben wird.
        """
        reward = self._extract_reward(kwargs)
        if reward is None:
            return  # kein Reward -> kein Lernen

        ctx = kwargs.get("ctx") or self._last_ctx
        if not isinstance(ctx, dict):
            return
        if self.alpha:
            try:
                self.alpha.learn(ctx, reward)
            except Exception:
                pass
        x = _vec_from_ctx(ctx)

        # Gate lernt mit tatsächlichem Reward
        try:
            self.gate.learn(x, reward)
        except Exception:
            pass

        # Size lernt nur, wenn size_bucket bekannt
        b = kwargs.get("size_bucket") or self._last_size_bucket
        if isinstance(b, str) and b in ("S","M","L"):
            try:
                xb = x * self.size_multipliers[b]
                self.size.learn(xb, reward)
            except Exception:
                pass

    # ---------- Persistence (optional) ----------
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "gate": self.gate.to_dict(),
            "size": self.size.to_dict(),
            "features": list(self.feature_names),
            "gate_alpha": self.gate.alpha,
            "size_alpha": self.size.alpha,
            "l2": self.gate.l2,
            "n_trades": self.n_trades,
            "last_trade_ts": self.last_trade_ts,
            "eps_gate": self.eps_gate,
            "gate_margin": self.gate_margin,
            "anti_stall_min": self.anti_stall_min,
            "skip_push": self.skip_push,
            "warmup_trades": self.warmup_trades,
            "enable_size": self.enable_size,
            "size_multipliers": dict(self.size_multipliers),
            "alpha_enabled": bool(self.alpha is not None),
            "alpha_threshold": self.alpha_threshold,
            "alpha_warmup": self.alpha_warmup,
            "alpha_min_conf": self.alpha_min_conf,
            "alpha_promote_delta": self.alpha_promote_delta,
            "alpha_reward_margin": self.alpha_reward_margin,
            "alpha_lr": self.alpha_lr,
            "alpha_l2": self.alpha_l2,
        }
        if self.alpha:
            try:
                data["alpha"] = self.alpha.to_dict()
            except Exception:
                pass
        return data

    @classmethod
    def from_dict(cls, d: Dict[str, Any], **overrides) -> "BanditPolicy":
        gate_alpha = float(overrides.get("gate_alpha", d.get("gate_alpha", 1.2)))
        size_alpha = float(overrides.get("size_alpha", d.get("size_alpha", 0.8)))
        l2 = float(overrides.get("l2", d.get("l2", 1e-3)))
        warmup_trades = int(overrides.get("warmup_trades", d.get("warmup_trades", 30)))
        enable_size = overrides.get("enable_size", d.get("enable_size", True))
        size_multipliers = overrides.get("size_multipliers", d.get("size_multipliers"))
        alpha_enabled = overrides.get("alpha_enabled", d.get("alpha_enabled", False))
        alpha_threshold = float(overrides.get("alpha_threshold", d.get("alpha_threshold", 0.55)))
        alpha_warmup = int(overrides.get("alpha_warmup", d.get("alpha_warmup", 40)))
        alpha_lr = float(overrides.get("alpha_lr", d.get("alpha_lr", 0.05)))
        alpha_l2 = float(overrides.get("alpha_l2", d.get("alpha_l2", 5e-4)))
        alpha_min_conf = float(overrides.get("alpha_min_conf", d.get("alpha_min_conf", 0.2)))
        alpha_promote_delta = float(overrides.get("alpha_promote_delta", d.get("alpha_promote_delta", 0.15)))
        alpha_reward_margin = float(overrides.get("alpha_reward_margin", d.get("alpha_reward_margin", 0.05)))
        obj = cls(
            gate_alpha=gate_alpha,
            size_alpha=size_alpha,
            l2=l2,
            warmup_trades=warmup_trades,
            enable_size=enable_size,
            size_multipliers=size_multipliers,
            alpha_enabled=alpha_enabled,
            alpha_threshold=alpha_threshold,
            alpha_warmup=alpha_warmup,
            alpha_lr=alpha_lr,
            alpha_l2=alpha_l2,
            alpha_min_conf=alpha_min_conf,
            alpha_promote_delta=alpha_promote_delta,
            alpha_reward_margin=alpha_reward_margin,
        )
        try:
            obj.gate = LinUCB.from_dict(d["gate"], target_dim=len(FEATURES))
        except Exception:
            pass
        try:
            obj.size = LinUCB.from_dict(d["size"], target_dim=len(FEATURES))
        except Exception: pass

        if isinstance(d.get("features"), (list, tuple)):
            obj.feature_names = tuple(d.get("features"))

        # Tunables / Stats
        obj.n_trades = int(d.get("n_trades", 0))
        obj.last_trade_ts = float(d.get("last_trade_ts", 0.0))
        obj.eps_gate = float(d.get("eps_gate", 0.0))
        obj.gate_margin = float(d.get("gate_margin", 0.0))
        obj.anti_stall_min = int(d.get("anti_stall_min", 60))
        obj.skip_push = float(d.get("skip_push", 0.0))
        if obj.alpha and isinstance(d.get("alpha"), dict):
            try:
                obj.alpha = AlphaModel.from_dict(d["alpha"])
                obj.alpha_lr = obj.alpha.lr
                obj.alpha_l2 = obj.alpha.l2
                obj.alpha_reward_margin = obj.alpha.reward_margin
            except Exception:
                pass
        return obj
