const envContainer = document.getElementById('env-settings');
const btnSaveConfig = document.getElementById('btn-save-config');
const btnSaveCredentials = document.getElementById('btn-save-credentials');
const btnStart = document.getElementById('btn-start');
const btnStop = document.getElementById('btn-stop');
const btnProMode = document.getElementById('btn-pro-mode');
const statusIndicator = document.getElementById('status-indicator');
const statusPid = document.getElementById('status-pid');
const statusStarted = document.getElementById('status-started');
const statusUptime = document.getElementById('status-uptime');
const logStream = document.getElementById('log-stream');
const compactLogStream = document.getElementById('log-brief');
const autoScrollToggle = document.getElementById('autoscroll');
const tradeBody = document.getElementById('trade-body');
const tradeSummary = document.getElementById('trade-summary');
const aiHint = document.getElementById('ai-hint');
const pnlChartCanvas = document.getElementById('pnl-chart');
const pnlEmptyState = document.getElementById('pnl-empty');
const presetButtons = document.querySelectorAll('.preset[data-preset]');
const presetDescription = document.getElementById('preset-description');
const riskSlider = document.getElementById('risk-slider');
const leverageSlider = document.getElementById('leverage-slider');
const riskValue = document.getElementById('risk-value');
const leverageValue = document.getElementById('leverage-value');
const inputApiKey = document.getElementById('input-api-key');
const inputApiSecret = document.getElementById('input-api-secret');

let currentConfig = {};
let reconnectTimer = null;
let pnlChart = null;
let proMode = false;
let selectedPreset = 'mid';

const PRESETS = {
  low: {
    label: 'Low',
    summary: 'Capital preservation first: slower signal intake, narrower exposure, and conservative scaling.',
    risk: 0.5,
    leverage: 1,
  },
  mid: {
    label: 'Mid',
    summary: 'Balanced cadence with moderate risk and leverage designed for steady account growth.',
    risk: 1.0,
    leverage: 2,
  },
  high: {
    label: 'High',
    summary: 'High-frequency execution with wider risk budgets and leverage up to the aggressive limit.',
    risk: 2.0,
    leverage: 4,
  },
};

function configureChartDefaults() {
  if (typeof Chart === 'undefined') return;
  const styles = getComputedStyle(document.documentElement);
  const muted = styles.getPropertyValue('--text-muted').trim();
  const border = styles.getPropertyValue('--border').trim();
  const font = styles.getPropertyValue('--font-sans')?.trim() || '"Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';

  Chart.defaults.color = muted || '#a09889';
  Chart.defaults.font.family = font;
  Chart.defaults.borderColor = border || 'rgba(255, 232, 168, 0.08)';
  Chart.defaults.plugins.legend.labels.usePointStyle = true;
  Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(10, 10, 14, 0.92)';
  Chart.defaults.plugins.tooltip.borderColor = border || 'rgba(255, 232, 168, 0.12)';
  Chart.defaults.plugins.tooltip.borderWidth = 1;
}

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

function renderCredentials(env) {
  if (inputApiKey) {
    inputApiKey.value = env?.ASTER_API_KEY ?? '';
  }
  if (inputApiSecret) {
    inputApiSecret.value = env?.ASTER_API_SECRET ?? '';
  }
}

async function loadConfig() {
  const res = await fetch('/api/config');
  if (!res.ok) throw new Error('Unable to load configuration');
  currentConfig = await res.json();
  renderConfig(currentConfig.env);
  renderCredentials(currentConfig.env);
}

function gatherConfigPayload() {
  const payload = {};
  envContainer.querySelectorAll('input[data-key]').forEach((input) => {
    payload[input.dataset.key] = input.value.trim();
  });
  return payload;
}

function gatherCredentialPayload() {
  const payload = {};
  if (inputApiKey) {
    payload.ASTER_API_KEY = inputApiKey.value.trim();
  }
  if (inputApiSecret) {
    payload.ASTER_API_SECRET = inputApiSecret.value.trim();
  }
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
    renderCredentials(currentConfig.env);
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

async function saveCredentials() {
  const payload = gatherCredentialPayload();
  if (!btnSaveCredentials) return;
  btnSaveCredentials.disabled = true;
  btnSaveCredentials.textContent = 'Saving…';
  try {
    const res = await fetch('/api/config', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ env: payload }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || 'Saving credentials failed');
    }
    currentConfig = await res.json();
    renderCredentials(currentConfig.env);
    renderConfig(currentConfig.env);
    btnSaveCredentials.textContent = 'Saved ✓';
    setTimeout(() => (btnSaveCredentials.textContent = 'Save'), 1500);
  } catch (err) {
    btnSaveCredentials.textContent = 'Error';
    alert(err.message);
    setTimeout(() => (btnSaveCredentials.textContent = 'Save'), 2000);
  } finally {
    btnSaveCredentials.disabled = false;
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
  if (!autoScrollToggle || autoScrollToggle.checked) {
    logStream.scrollTop = logStream.scrollHeight;
  }

  appendCompactLog({ line, level: normalizedLevel, ts });
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

function createTradeCell(label, { text, node, className }) {
  const cell = document.createElement('td');
  cell.dataset.label = label;
  if (className) {
    className
      .split(' ')
      .filter(Boolean)
      .forEach((cls) => cell.classList.add(cls));
  }
  if (node) {
    cell.append(node);
  } else {
    cell.textContent = text ?? '–';
  }
  return cell;
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
    const pnlClass = pnl > 0 ? 'profit' : pnl < 0 ? 'loss' : '';
    const pnlValue = `${pnl > 0 ? '+' : ''}${formatNumber(pnl, 2)}`;
    const pnlR = Number(trade.pnl_r ?? 0);
    const pnlRClass = pnlR > 0 ? 'profit' : pnlR < 0 ? 'loss' : '';
    const side = (trade.side || '').toString().toLowerCase();
    const sideLabel = trade.side ? trade.side.toUpperCase() : '–';
    const sideBadge = document.createElement('span');
    sideBadge.className = `side-badge ${side}`.trim();
    sideBadge.textContent = sideLabel;

    row.append(
      createTradeCell('Symbol', { text: trade.symbol || '–', className: 'symbol' }),
      createTradeCell('Side', { node: sideBadge }),
      createTradeCell('Size', { text: formatNumber(trade.qty, 4), className: 'numeric' }),
      createTradeCell('Entry', { text: formatNumber(trade.entry, 4), className: 'numeric' }),
      createTradeCell('Exit', { text: formatNumber(trade.exit, 4), className: 'numeric' }),
      createTradeCell('PNL (USDT)', {
        text: pnlValue,
        className: ['numeric', pnlClass].filter(Boolean).join(' '),
      }),
      createTradeCell('R', {
        text: formatNumber(pnlR, 2),
        className: ['numeric', pnlRClass].filter(Boolean).join(' '),
      }),
      createTradeCell('Opened', { text: formatTimestamp(trade.opened_at_iso) }),
      createTradeCell('Closed', { text: formatTimestamp(trade.closed_at_iso) })
    );
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

function renderPnlChart(history) {
  if (!pnlChartCanvas || typeof Chart === 'undefined') return;

  const entries = Array.isArray(history) ? history.slice() : [];
  const sorted = entries
    .filter((trade) => trade && trade.pnl !== undefined && trade.pnl !== null)
    .sort((a, b) => {
      const aDate = new Date(a.closed_at_iso || a.opened_at_iso || 0).getTime();
      const bDate = new Date(b.closed_at_iso || b.opened_at_iso || 0).getTime();
      return aDate - bDate;
    });

  if (sorted.length === 0) {
    if (pnlChart) {
      pnlChart.destroy();
      pnlChart = null;
    }
    pnlChartCanvas.style.display = 'none';
    if (pnlEmptyState) {
      pnlEmptyState.style.display = 'flex';
    }
    return;
  }

  if (pnlEmptyState) {
    pnlEmptyState.style.display = 'none';
  }
  pnlChartCanvas.style.display = 'block';

  const labels = [];
  const values = [];
  let cumulative = 0;
  for (const trade of sorted) {
    const pnl = Number(trade.pnl ?? 0);
    if (Number.isNaN(pnl)) continue;
    cumulative += pnl;
    const timestamp = trade.closed_at_iso || trade.opened_at_iso;
    if (timestamp) {
      const date = new Date(timestamp);
      if (!Number.isNaN(date.getTime())) {
        labels.push(
          date.toLocaleString(undefined, {
            month: 'short',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
          })
        );
      } else {
        labels.push(`Trade ${labels.length + 1}`);
      }
    } else {
      labels.push(`Trade ${labels.length + 1}`);
    }
    values.push(Number(cumulative.toFixed(2)));
  }

  const styles = getComputedStyle(document.documentElement);
  const accent = styles.getPropertyValue('--accent-strong').trim() || '#f0a94b';
  const accentSoft = styles.getPropertyValue('--accent-soft').trim() || 'rgba(240, 169, 75, 0.18)';

  const data = {
    labels,
    datasets: [
      {
        label: 'Cumulative PNL (USDT)',
        data: values,
        borderColor: accent,
        backgroundColor: accentSoft,
        tension: 0.35,
        pointRadius: 2.5,
        pointHoverRadius: 4,
        pointBackgroundColor: '#0c0d12',
        fill: true,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        ticks: {
          maxRotation: 0,
          autoSkip: true,
          color: styles.getPropertyValue('--text-muted').trim() || '#a09889',
        },
        grid: {
          display: false,
        },
      },
      y: {
        ticks: {
          callback: (value) => `${Number(value).toFixed ? Number(value).toFixed(2) : value}`,
          color: styles.getPropertyValue('--text-muted').trim() || '#a09889',
        },
        grid: {
          color: styles.getPropertyValue('--grid-line').trim() || 'rgba(255, 232, 168, 0.08)',
        },
      },
    },
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const value = context.parsed.y;
            return ` ${value >= 0 ? '+' : ''}${value.toFixed(2)} USDT`;
          },
        },
      },
    },
  };

  if (pnlChart) {
    pnlChart.data = data;
    pnlChart.options = options;
    pnlChart.update();
  } else {
    const ctx = pnlChartCanvas.getContext('2d');
    pnlChart = new Chart(ctx, {
      type: 'line',
      data,
      options,
    });
  }
}

function appendCompactLog({ line, level, ts }) {
  if (!compactLogStream) return;
  const allowed = new Set(['error', 'warning', 'system', 'info']);
  if (!allowed.has(level)) return;

  const el = document.createElement('div');
  el.className = `log-line ${level}`.trim();

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
  label.textContent = level.toUpperCase();
  meta.append(label);

  const message = document.createElement('div');
  message.className = 'log-message';
  message.textContent = line;

  el.append(meta, message);
  compactLogStream.append(el);

  while (compactLogStream.children.length > 150) {
    compactLogStream.removeChild(compactLogStream.firstChild);
  }
  compactLogStream.scrollTop = compactLogStream.scrollHeight;
}

function setRangeBackground(slider) {
  if (!slider) return;
  const min = Number(slider.min);
  const max = Number(slider.max);
  const value = Number(slider.value);
  if (Number.isNaN(min) || Number.isNaN(max) || Number.isNaN(value)) return;
  const percent = ((value - min) / (max - min)) * 100;
  slider.style.background = `linear-gradient(90deg, var(--accent-strong) ${percent}%, rgba(22, 24, 34, 0.85) ${percent}%)`;
}

function formatRisk(value) {
  const numeric = Number(value);
  if (Number.isNaN(numeric)) return '–';
  if (numeric >= 1) return `${numeric.toFixed(1)}%`;
  return `${numeric.toFixed(2)}%`;
}

function updateRiskValue() {
  if (!riskSlider || !riskValue) return;
  riskValue.textContent = formatRisk(riskSlider.value);
  setRangeBackground(riskSlider);
}

function updateLeverageValue() {
  if (!leverageSlider || !leverageValue) return;
  const numeric = Number(leverageSlider.value);
  leverageValue.textContent = `${numeric.toFixed(0)}×`;
  setRangeBackground(leverageSlider);
}

function applyPreset(key) {
  const preset = PRESETS[key];
  if (!preset) return;
  selectedPreset = key;
  presetButtons.forEach((button) => {
    const active = button.dataset.preset === key;
    button.classList.toggle('active', active);
    if (active) {
      button.setAttribute('aria-pressed', 'true');
    } else {
      button.setAttribute('aria-pressed', 'false');
    }
  });
  if (presetDescription) {
    presetDescription.textContent = `${preset.label} preset: ${preset.summary}`;
  }
  if (riskSlider) {
    riskSlider.value = preset.risk.toString();
  }
  if (leverageSlider) {
    leverageSlider.value = preset.leverage.toString();
  }
  updateRiskValue();
  updateLeverageValue();
}

function setProMode(state) {
  proMode = state;
  document.body.classList.toggle('pro-mode', proMode);
  if (btnProMode) {
    btnProMode.textContent = proMode ? 'Exit Pro-Mode' : 'Pro-Mode';
    btnProMode.classList.toggle('active', proMode);
    btnProMode.setAttribute('aria-pressed', proMode ? 'true' : 'false');
  }
}

async function loadTrades() {
  try {
    const res = await fetch('/api/trades');
    if (!res.ok) throw new Error('Unable to load trades');
    const data = await res.json();
    renderTradeHistory(data.history);
    renderTradeSummary(data.stats);
    renderPnlChart(data.history);
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
btnSaveCredentials?.addEventListener('click', saveCredentials);
btnStart.addEventListener('click', startBot);
btnStop.addEventListener('click', stopBot);
btnProMode?.addEventListener('click', () => setProMode(!proMode));

presetButtons.forEach((button) => {
  button.addEventListener('click', () => applyPreset(button.dataset.preset));
  button.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      applyPreset(button.dataset.preset);
    }
  });
});

riskSlider?.addEventListener('input', updateRiskValue);
riskSlider?.addEventListener('change', updateRiskValue);
leverageSlider?.addEventListener('input', updateLeverageValue);
leverageSlider?.addEventListener('change', updateLeverageValue);

document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible') {
    updateStatus();
    loadTrades();
  }
});

async function init() {
  configureChartDefaults();
  await loadConfig();
  await updateStatus();
  await loadTrades();
  applyPreset(selectedPreset);
  setProMode(false);
  connectLogs();
  setInterval(updateStatus, 5000);
  setInterval(loadTrades, 8000);
}

init().catch((err) => console.error(err));
