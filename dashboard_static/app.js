const envContainer = document.getElementById('env-settings');
const btnSaveConfig = document.getElementById('btn-save-config');
const btnStart = document.getElementById('btn-start');
const btnStop = document.getElementById('btn-stop');
const statusIndicator = document.getElementById('status-indicator');
const statusPid = document.getElementById('status-pid');
const statusStarted = document.getElementById('status-started');
const statusUptime = document.getElementById('status-uptime');
const logStream = document.getElementById('log-stream');
const autoScrollToggle = document.getElementById('autoscroll');
const tradeBody = document.getElementById('trade-body');
const tradeSummary = document.getElementById('trade-summary');
const aiHint = document.getElementById('ai-hint');

let currentConfig = {};
let reconnectTimer = null;

function renderConfig(env) {
  envContainer.innerHTML = '';
  const entries = Object.entries(env || {}).sort(([a], [b]) => a.localeCompare(b));
  for (const [key, value] of entries) {
    const label = document.createElement('label');
    label.dataset.key = key;
    const span = document.createElement('span');
    span.textContent = key;
    const input = document.createElement('input');
    input.value = value ?? '';
    input.dataset.key = key;
    input.placeholder = key;
    label.append(span, input);
    envContainer.append(label);
  }
}

async function loadConfig() {
  const res = await fetch('/api/config');
  if (!res.ok) throw new Error('Unable to load configuration');
  currentConfig = await res.json();
  renderConfig(currentConfig.env);
}

function gatherConfigPayload() {
  const payload = {};
  envContainer.querySelectorAll('input[data-key]').forEach((input) => {
    payload[input.dataset.key] = input.value.trim();
  });
  return payload;
}

async function saveConfig() {
  const payload = gatherConfigPayload();
  btnSaveConfig.disabled = true;
  btnSaveConfig.textContent = 'Saving…';
  try {
    const res = await fetch('/api/config', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ env: payload }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || 'Saving configuration failed');
    }
    currentConfig = await res.json();
    btnSaveConfig.textContent = 'Saved ✓';
    setTimeout(() => (btnSaveConfig.textContent = 'Save'), 1500);
  } catch (err) {
    btnSaveConfig.textContent = 'Error';
    alert(err.message);
    setTimeout(() => (btnSaveConfig.textContent = 'Save'), 2000);
  } finally {
    btnSaveConfig.disabled = false;
  }
}

function formatDuration(seconds) {
  if (seconds == null) return '–';
  const s = Math.floor(seconds % 60).toString().padStart(2, '0');
  const m = Math.floor((seconds / 60) % 60).toString().padStart(2, '0');
  const h = Math.floor(seconds / 3600).toString().padStart(2, '0');
  return `${h}:${m}:${s}`;
}

function formatNumber(num, digits = 2) {
  if (num === undefined || num === null || Number.isNaN(num)) return '–';
  return Number(num).toFixed(digits);
}

function formatTimestamp(value) {
  if (!value) return '–';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '–';
  return date.toLocaleString(undefined, {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

async function updateStatus() {
  try {
    const res = await fetch('/api/bot/status');
    if (!res.ok) throw new Error();
    const data = await res.json();
    const running = data.running;
    statusIndicator.textContent = running ? 'Running' : 'Stopped';
    statusIndicator.className = `pill ${running ? 'running' : 'stopped'}`;
    statusPid.textContent = data.pid ?? '–';
    statusStarted.textContent = data.started_at ? new Date(data.started_at * 1000).toLocaleString() : '–';
    statusUptime.textContent = running ? formatDuration(data.uptime_s) : '–';
    btnStart.disabled = running;
    btnStop.disabled = !running;
  } catch {
    statusIndicator.textContent = 'Offline';
    statusIndicator.className = 'pill stopped';
    statusPid.textContent = '–';
    statusStarted.textContent = '–';
    statusUptime.textContent = '–';
  }
}

function appendLogLine({ line, level, ts }) {
  const normalizedLevel = (level || 'info').toLowerCase();
  const el = document.createElement('div');
  el.className = `log-line ${normalizedLevel}`.trim();

  const meta = document.createElement('div');
  meta.className = 'log-meta';

  if (ts) {
    const time = document.createElement('span');
    time.className = 'log-time';
    time.textContent = new Date(ts * 1000).toLocaleTimeString();
    meta.append(time);
  }

  const label = document.createElement('span');
  label.className = 'log-level';
  const labelMap = {
    error: 'Error',
    warning: 'Warning',
    system: 'System',
    debug: 'Debug',
    info: 'Info',
  };
  label.textContent = labelMap[normalizedLevel] || normalizedLevel.toUpperCase();
  meta.append(label);

  const message = document.createElement('div');
  message.className = 'log-message';
  message.textContent = line;

  el.append(meta, message);
  logStream.append(el);
  while (logStream.children.length > 500) {
    logStream.removeChild(logStream.firstChild);
  }
  if (autoScrollToggle.checked) {
    logStream.scrollTop = logStream.scrollHeight;
  }
}

function connectLogs() {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
  const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
  const socket = new WebSocket(`${protocol}://${location.host}/ws/logs`);
  socket.addEventListener('message', (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.type === 'log') {
        appendLogLine(data);
      }
    } catch (err) {
      console.error('WebSocket parse error', err);
    }
  });
  socket.addEventListener('close', () => {
    reconnectTimer = setTimeout(connectLogs, 2000);
  });
  socket.addEventListener('error', () => {
    socket.close();
  });
}

function renderTradeHistory(history) {
  tradeBody.innerHTML = '';
  if (!history || history.length === 0) {
    const row = document.createElement('tr');
    const cell = document.createElement('td');
    cell.colSpan = 9;
    cell.textContent = 'No trades yet.';
    cell.className = 'empty';
    row.append(cell);
    tradeBody.append(row);
    return;
  }
  for (const trade of history) {
    const row = document.createElement('tr');
    const pnl = Number(trade.pnl ?? 0);
    const pnlClass = pnl > 0 ? 'profit' : pnl < 0 ? 'loss' : 'neutral';
    const pnlValue = `${pnl > 0 ? '+' : ''}${formatNumber(pnl, 2)}`;
    const pnlR = Number(trade.pnl_r ?? 0);
    const pnlRClass = pnlR > 0 ? 'profit' : pnlR < 0 ? 'loss' : 'neutral';
    const side = (trade.side || '').toString().toLowerCase();
    const sideLabel = trade.side ? trade.side.toUpperCase() : '–';
    row.innerHTML = `
      <td class="symbol">${trade.symbol || '–'}</td>
      <td><span class="side-badge ${side}">${sideLabel}</span></td>
      <td class="numeric">${formatNumber(trade.qty, 4)}</td>
      <td class="numeric">${formatNumber(trade.entry, 4)}</td>
      <td class="numeric">${formatNumber(trade.exit, 4)}</td>
      <td class="numeric ${pnlClass}">${pnlValue}</td>
      <td class="numeric ${pnlRClass}">${formatNumber(pnlR, 2)}</td>
      <td>${formatTimestamp(trade.opened_at_iso)}</td>
      <td>${formatTimestamp(trade.closed_at_iso)}</td>
    `;
    tradeBody.append(row);
  }
}

function renderTradeSummary(stats) {
  tradeSummary.innerHTML = '';
  if (!stats) {
    const placeholder = document.createElement('div');
    placeholder.className = 'trade-metric muted';
    placeholder.innerHTML = `<span class="metric-label">Performance</span><span class="metric-value">No data yet</span>`;
    tradeSummary.append(placeholder);
    aiHint.textContent = 'No data available.';
    return;
  }
  const avgR = stats.count ? stats.total_r / stats.count : 0;
  const metrics = [
    {
      label: 'Trades',
      value: stats.count ?? 0,
      tone: 'neutral',
    },
    {
      label: 'Total PNL',
      value: `${stats.total_pnl > 0 ? '+' : ''}${formatNumber(stats.total_pnl, 2)} USDT`,
      tone: stats.total_pnl > 0 ? 'profit' : stats.total_pnl < 0 ? 'loss' : 'neutral',
    },
    {
      label: 'Win rate',
      value: `${((stats.win_rate ?? 0) * 100).toFixed(1)}%`,
      tone: 'neutral',
    },
    {
      label: 'Avg R',
      value: formatNumber(avgR, 2),
      tone: avgR > 0 ? 'profit' : avgR < 0 ? 'loss' : 'neutral',
    },
  ];
  for (const metric of metrics) {
    const el = document.createElement('div');
    el.className = `trade-metric ${metric.tone}`;
    el.innerHTML = `
      <span class="metric-label">${metric.label}</span>
      <span class="metric-value">${metric.value}</span>
    `;
    tradeSummary.append(el);
  }
  aiHint.textContent = stats.ai_hint;
}

async function loadTrades() {
  try {
    const res = await fetch('/api/trades');
    if (!res.ok) throw new Error('Unable to load trades');
    const data = await res.json();
    renderTradeHistory(data.history);
    renderTradeSummary(data.stats);
  } catch (err) {
    console.warn(err);
  }
}

async function startBot() {
  btnStart.disabled = true;
  try {
    const res = await fetch('/api/bot/start', { method: 'POST' });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || 'Unable to start bot');
    }
  } catch (err) {
    alert(err.message);
  } finally {
    await updateStatus();
  }
}

async function stopBot() {
  btnStop.disabled = true;
  try {
    await fetch('/api/bot/stop', { method: 'POST' });
  } finally {
    await updateStatus();
  }
}

btnSaveConfig.addEventListener('click', saveConfig);
btnStart.addEventListener('click', startBot);
btnStop.addEventListener('click', stopBot);

document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible') {
    updateStatus();
    loadTrades();
  }
});

async function init() {
  await loadConfig();
  await updateStatus();
  await loadTrades();
  connectLogs();
  setInterval(updateStatus, 5000);
  setInterval(loadTrades, 8000);
}

init().catch((err) => console.error(err));
