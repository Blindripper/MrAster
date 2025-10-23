# ml_policy.py — LinUCB Bandit für Gate (TAKE/SKIP) + Größenbucket (S/M/L)
from __future__ import annotations
import math, time, random
from typing import Dict, Optional, Tuple, Any

try:
    import numpy as np
except Exception:
    raise RuntimeError("ml_policy.py benötigt numpy. Bitte im venv: pip install numpy")

# Feature-Vektor (muss zum Bot passen)
FEATURES = ("adx","atr_pct","slope_htf","rsi","funding","qv_score","trend","regime_adx","regime_slope","spread_bps")

def _vec_from_ctx(ctx: Dict[str, float]) -> "np.ndarray":
    return np.array([float(ctx.get(k, 0.0) or 0.0) for k in FEATURES], dtype=float).reshape(-1, 1)  # d×1

# ------------------------------ LinUCB ---------------------------------------
class LinUCB:
    def __init__(self, alpha: float = 1.0, l2: float = 1e-3, d: Optional[int] = None):
        self.alpha = float(alpha)
        self.l2 = float(l2)
        self.d = int(d or len(FEATURES))
        self.A = np.eye(self.d) * self.l2  # d×d
        self.b = np.zeros((self.d, 1))     # d×1

    def predict_ucb(self, x: "np.ndarray") -> float:
        # x: d×1
        A_inv = np.linalg.inv(self.A)
        theta = A_inv @ self.b  # d×1
        mu = float((theta.T @ x)[0, 0])
        s = float(math.sqrt((x.T @ A_inv @ x)[0, 0]))
        return mu + self.alpha * s

    def learn(self, x: "np.ndarray", reward: float) -> None:
        self.A += x @ x.T
        self.b += float(reward) * x

    def to_dict(self) -> Dict[str, Any]:
        return {"alpha": self.alpha, "l2": self.l2, "d": self.d, "A": self.A.tolist(), "b": self.b.tolist()}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LinUCB":
        obj = cls(alpha=float(d.get("alpha", 1.0)), l2=float(d.get("l2", 1e-3)), d=int(d.get("d", len(FEATURES))))
        obj.A = np.array(d.get("A", np.eye(obj.d).tolist()), dtype=float)
        obj.b = np.array(d.get("b", np.zeros((obj.d, 1)).tolist()), dtype=float)
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
    ) -> None:
        self.gate = LinUCB(alpha=gate_alpha, l2=l2, d=d)
        self.size = LinUCB(alpha=size_alpha, l2=l2, d=d)
        self.enable_size = bool(enable_size)
        self.size_multipliers = dict(size_multipliers or {"S":1.0,"M":1.4,"L":1.9})
        self.warmup_trades = int(warmup_trades)

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
    def decide(self, ctx: Dict[str, float]) -> Tuple[str, Dict[str, str]]:
        x = _vec_from_ctx(ctx)

        # Gate-Score: wir vergleichen TAKE vs. SKIP=0 baseline
        take_ucb = self.gate.predict_ucb(x) - self.skip_push
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

        return decision, {"size_bucket": size_bucket}

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
        return {
            "gate": self.gate.to_dict(),
            "size": self.size.to_dict(),
            "gate_alpha": self.gate.alpha,
            "size_alpha": self.size.alpha,
            "l2": self.gate.l2,
            "n_trades": self.n_trades,
            "last_trade_ts": self.last_trade_ts,
            "eps_gate": self.eps_gate,
            "gate_margin": self.gate_margin,
            "anti_stall_min": self.anti_stall_min,
            "skip_push": self.skip_push,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "BanditPolicy":
        gate_alpha = float(d.get("gate_alpha", 1.2))
        size_alpha = float(d.get("size_alpha", 0.8))
        l2 = float(d.get("l2", 1e-3))
        obj = cls(gate_alpha=gate_alpha, size_alpha=size_alpha, l2=l2)
        try: obj.gate = LinUCB.from_dict(d["gate"])
        except Exception: pass
        try: obj.size = LinUCB.from_dict(d["size"])
        except Exception: pass

        # Tunables / Stats
        obj.n_trades = int(d.get("n_trades", 0))
        obj.last_trade_ts = float(d.get("last_trade_ts", 0.0))
        obj.eps_gate = float(d.get("eps_gate", 0.0))
        obj.gate_margin = float(d.get("gate_margin", 0.0))
        obj.anti_stall_min = int(d.get("anti_stall_min", 60))
        obj.skip_push = float(d.get("skip_push", 0.0))
        return obj
