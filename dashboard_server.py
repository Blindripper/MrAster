"""Aster Bot Dashboard server providing web UI for configuration, monitoring and history."""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import signal
import sys
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT_DIR = Path(__file__).resolve().parent
STATE_FILE = ROOT_DIR / os.getenv("ASTER_STATE_FILE", "aster_state.json")
STATIC_DIR = ROOT_DIR / "dashboard_static"
CONFIG_FILE = ROOT_DIR / "dashboard_config.json"

ENV_DEFAULTS: Dict[str, str] = {
    "ASTER_EXCHANGE_BASE": "https://fapi.asterdex.com",
    "ASTER_API_KEY": "",
    "ASTER_API_SECRET": "",
    "ASTER_RECV_WINDOW": "10000",
    "ASTER_WORKING_TYPE": "MARK_PRICE",
    "ASTER_LOGLEVEL": "DEBUG",
    "ASTER_PAPER": "false",
    "ASTER_RUN_ONCE": "false",
    "ASTER_QUOTE": "USDT",
    "ASTER_INCLUDE_SYMBOLS": "BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT,DOGEUSDT,ADAUSDT,LINKUSDT,AVAXUSDT,TRXUSDT,MATICUSDT,NEARUSDT,LTCUSDT,BCHUSDT,DOTUSDT,ATOMUSDT,ARBUSDT,APTUSDT,SUIUSDT,OPUSDT,BLUAIUSDT,HEMIUSDT,TURTLEUSDT,APRUSDT",
    "ASTER_EXCLUDE_SYMBOLS": "AMZNUSDT,APRUSDT",
    "ASTER_UNIVERSE_MAX": "40",
    "ASTER_UNIVERSE_ROTATE": "false",
    "ASTER_MIN_QUOTE_VOL_USDT": "75000",
    "ASTER_INTERVAL": "5m",
    "ASTER_HTF_INTERVAL": "30m",
    "ASTER_KLINES": "360",
    "ASTER_RSI_BUY_MIN": "51",
    "ASTER_RSI_SELL_MAX": "49",
    "ASTER_ALLOW_TREND_ALIGN": "true",
    "ASTER_ALIGN_RSI_PAD": "1.5",
    "ASTER_SPREAD_BPS_MAX": "0.009",
    "ASTER_WICKINESS_MAX": "0.985",
    "ASTER_MIN_EDGE_R": "0.08",
    "ASTER_DEFAULT_NOTIONAL": "120",
    "ASTER_RISK_PER_TRADE": "0.007",
    "ASTER_LEVERAGE": "3",
    "ASTER_EQUITY_FRACTION": "0.25",
    "ASTER_MIN_NOTIONAL_USDT": "5",
    "ASTER_MAX_NOTIONAL_USDT": "300",
    "ASTER_SIZE_MULT": "1.0",
    "ASTER_SIZE_MULT_S": "1.0",
    "ASTER_SIZE_MULT_M": "1.4",
    "ASTER_SIZE_MULT_L": "1.9",
    "ASTER_SL_ATR_MULT": "1.3",
    "ASTER_TP_ATR_MULT": "2.0",
    "FAST_TP_ENABLED": "true",
    "FASTTP_MIN_R": "0.25",
    "FAST_TP_RET1": "-0.0010",
    "FAST_TP_RET3": "-0.0020",
    "FASTTP_SNAP_ATR": "0.25",
    "FASTTP_COOLDOWN_S": "45",
    "ASTER_MAX_OPEN_GLOBAL": "2",
    "ASTER_MAX_OPEN_PER_SYMBOL": "1",
    "ASTER_STATE_FILE": "aster_state.json",
    "ASTER_LOOP_SLEEP": "20",
    "ASTER_BANDIT_ENABLED": "true",
    "ASTER_HISTORY_MAX": "250",
    "ASTER_BOT_SCRIPT": "aster_multi_bot.py",
}

ALLOWED_ENV_KEYS = set(ENV_DEFAULTS.keys())


def _load_config() -> Dict[str, Any]:
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text())
            env_cfg = data.get("env", {})
        except Exception:
            env_cfg = {}
    else:
        env_cfg = {}

    merged = {k: os.getenv(k, env_cfg.get(k, v)) for k, v in ENV_DEFAULTS.items()}
    config = {"env": merged}
    CONFIG_FILE.write_text(json.dumps(config, indent=2, sort_keys=True))
    return config


def _save_config(config: Dict[str, Any]) -> None:
    CONFIG_FILE.write_text(json.dumps(config, indent=2, sort_keys=True))


CONFIG: Dict[str, Any] = _load_config()


class ConfigUpdate(BaseModel):
    env: Dict[str, str] = Field(default_factory=dict)


class BotStatus(BaseModel):
    running: bool
    pid: Optional[int]
    started_at: Optional[float]
    uptime_s: Optional[float]


class TradeStats(BaseModel):
    count: int
    total_pnl: float
    total_r: float
    win_rate: float
    best_trade: Optional[Dict[str, Any]]
    worst_trade: Optional[Dict[str, Any]]
    ai_hint: str


def _ensure_static_dir() -> None:
    if not STATIC_DIR.exists():
        STATIC_DIR.mkdir(parents=True, exist_ok=True)


_ensure_static_dir()


class LogHub:
    def __init__(self) -> None:
        self.buffer: deque = deque(maxlen=500)
        self.clients: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def register(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            history = list(self.buffer)
            self.clients.add(ws)
        for item in history:
            await self._safe_send(ws, item)

    async def unregister(self, ws: WebSocket) -> None:
        async with self._lock:
            self.clients.discard(ws)

    async def push(self, line: str, level: str = "info") -> None:
        payload = {
            "ts": time.time(),
            "line": line,
            "level": level,
        }
        async with self._lock:
            self.buffer.append(payload)
            clients = list(self.clients)
        for client in clients:
            await self._safe_send(client, payload)

    async def _safe_send(self, ws: WebSocket, payload: Dict[str, Any]) -> None:
        try:
            await ws.send_json({"type": "log", **payload})
        except Exception:
            await self.unregister(ws)


def _resolve_python() -> str:
    """Return an executable python interpreter for subprocesses."""

    exe = sys.executable
    if exe:
        path = Path(exe)
        if path.exists():
            return str(path)

    candidate = shutil.which("python3") or shutil.which("python")
    if not candidate:
        raise FileNotFoundError("Python interpreter not found for bot execution")
    return candidate


def _resolve_bot_script(env_cfg: Dict[str, str]) -> Path:
    script_value = env_cfg.get("ASTER_BOT_SCRIPT", "aster_multi_bot.py")
    script_path = Path(script_value)
    if not script_path.is_absolute():
        script_path = ROOT_DIR / script_path
    script_path = script_path.resolve()
    if not script_path.exists():
        raise FileNotFoundError(f"Bot script not found: {script_path}")
    return script_path


class BotRunner:
    def __init__(self, loghub: LogHub) -> None:
        self.loghub = loghub
        self.process: Optional[asyncio.subprocess.Process] = None
        self._lock = asyncio.Lock()
        self._reader_task: Optional[asyncio.Task] = None
        self.started_at: Optional[float] = None

    async def status(self) -> BotStatus:
        running = self.process is not None and self.process.returncode is None
        uptime = time.time() - self.started_at if running and self.started_at else None
        pid = self.process.pid if running and self.process else None
        return BotStatus(running=running, pid=pid, started_at=self.started_at, uptime_s=uptime)

    async def start(self) -> None:
        async with self._lock:
            if self.process and self.process.returncode is None:
                raise RuntimeError("Bot is already running")
            env = os.environ.copy()
            env_cfg = CONFIG.get("env", {})
            env.update(env_cfg)
            python_cmd = _resolve_python()
            bot_script = _resolve_bot_script(env_cfg)
            env.setdefault("ASTER_LOGLEVEL", "DEBUG")
            try:
                self.process = await asyncio.create_subprocess_exec(
                    python_cmd,
                    str(bot_script),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    env=env,
                    cwd=str(ROOT_DIR),
                )
            except FileNotFoundError as exc:
                await self.loghub.push(str(exc), level="error")
                raise
            self.started_at = time.time()
            await self.loghub.push("Bot process started", level="system")
            self._reader_task = asyncio.create_task(self._pump_stdout())

    async def stop(self) -> None:
        async with self._lock:
            if not self.process:
                return
            proc = self.process
            if proc.returncode is None:
                try:
                    proc.send_signal(signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    await asyncio.wait_for(proc.wait(), timeout=10)
                except asyncio.TimeoutError:
                    proc.kill()
            self.process = None
            self.started_at = None
            await self.loghub.push("Bot process stopped", level="system")
        if self._reader_task:
            task = self._reader_task
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception as exc:  # pragma: no cover - best effort cleanup
                await self.loghub.push(
                    f"Log reader stopped with error: {exc}", level="error"
                )
            self._reader_task = None

    async def _pump_stdout(self) -> None:
        if not self.process or not self.process.stdout:
            return
        proc = self.process
        try:
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                text = line.decode("utf-8", errors="ignore").rstrip()
                await self.loghub.push(text)
        finally:
            if proc.returncode is None:
                await proc.wait()
            await self.loghub.push("Bot process finished", level="system")
            self.process = None
            self.started_at = None


loghub = LogHub()
runner = BotRunner(loghub)

app = FastAPI(title="Aster Bot Control Center")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def index() -> FileResponse:
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Dashboard build not found")
    return FileResponse(index_file)


@app.get("/api/config")
async def get_config() -> Dict[str, Any]:
    return CONFIG


@app.put("/api/config")
async def update_config(update: ConfigUpdate) -> Dict[str, Any]:
    env_cfg = CONFIG.setdefault("env", {})
    for key, value in update.env.items():
        if key not in ALLOWED_ENV_KEYS:
            raise HTTPException(status_code=400, detail=f"Unknown key: {key}")
        env_cfg[key] = str(value)
    _save_config(CONFIG)
    await loghub.push("Configuration updated", level="system")
    return CONFIG


@app.post("/api/bot/start")
async def start_bot() -> Dict[str, Any]:
    try:
        await runner.start()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"status": "started"}


@app.post("/api/bot/stop")
async def stop_bot() -> Dict[str, Any]:
    await runner.stop()
    return {"status": "stopped"}


@app.get("/api/bot/status", response_model=BotStatus)
async def bot_status() -> BotStatus:
    return await runner.status()


def _read_state() -> Dict[str, Any]:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            return {}
    return {}


def _format_ts(ts: Optional[float]) -> Optional[str]:
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(ts).isoformat()
    except Exception:
        return None


def _compute_stats(history: List[Dict[str, Any]]) -> TradeStats:
    if not history:
        return TradeStats(
            count=0,
            total_pnl=0.0,
            total_r=0.0,
            win_rate=0.0,
            best_trade=None,
            worst_trade=None,
            ai_hint="No trades yet — start the bot to collect more data.",
        )
    total_pnl = sum(float(h.get("pnl", 0.0) or 0.0) for h in history)
    total_r = sum(float(h.get("pnl_r", 0.0) or 0.0) for h in history)
    wins = [h for h in history if (h.get("pnl", 0.0) or 0.0) > 0]
    losses = [h for h in history if (h.get("pnl", 0.0) or 0.0) < 0]
    count = len(history)
    win_rate = (len(wins) / count) if count else 0.0
    best = max(history, key=lambda h: h.get("pnl", 0.0))
    worst = min(history, key=lambda h: h.get("pnl", 0.0))

    hint: str
    if count < 10:
        hint = "Limited data so far — observe a few more trades before tweaking parameters."
    elif win_rate > 0.6 and total_r > 0:
        hint = "Strong performance! Consider nudging the size multiplier slightly higher."
    elif win_rate < 0.4 and total_r < 0:
        hint = "Caution: performance is lagging. Review spread/RSI filters or switch to PAPER mode for fine-tuning."
    else:
        hint = "Steady progress. Keep watching PnL and refine the RSI/ATR multipliers gradually."

    return TradeStats(
        count=count,
        total_pnl=total_pnl,
        total_r=total_r,
        win_rate=win_rate,
        best_trade=best,
        worst_trade=worst,
        ai_hint=hint,
    )


@app.get("/api/trades")
async def trades() -> Dict[str, Any]:
    state = _read_state()
    history: List[Dict[str, Any]] = state.get("trade_history", [])[-200:]
    for item in history:
        item["opened_at_iso"] = _format_ts(item.get("opened_at"))
        item["closed_at_iso"] = _format_ts(item.get("closed_at"))
    open_trades = state.get("live_trades", {})
    stats = _compute_stats(history)
    return {
        "open": open_trades,
        "history": history[::-1],
        "stats": stats.dict(),
    }


@app.websocket("/ws/logs")
async def ws_logs(ws: WebSocket) -> None:
    await loghub.register(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        await loghub.unregister(ws)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("dashboard_server:app", host="0.0.0.0", port=8000, reload=False)
