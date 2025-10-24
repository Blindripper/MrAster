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
const autoScrollToggles = document.querySelectorAll('input[data-autoscroll]');
const tradeBodyPosition = document.getElementById('trade-body-position');
const tradeBodyPricing = document.getElementById('trade-body-pricing');
const tradeBodyPerformance = document.getElementById('trade-body-performance');
const tradeBodyTiming = document.getElementById('trade-body-timing');
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
const decisionSummary = document.getElementById('decision-summary');
const decisionReasons = document.getElementById('decision-reasons');

let currentConfig = {};
let reconnectTimer = null;
let pnlChart = null;
let proMode = false;
let selectedPreset = 'mid';
let autoScrollEnabled = true;

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

const DECISION_REASON_LABELS = {
  spread: 'Spread too wide',
  wicky: 'Wicks too volatile',
  no_cross: 'Signal not confirmed',
  few_klines: 'Not enough recent candles',
  edge_r: 'Expected edge too small',
  klines_err: 'Market data unavailable',
  funding_long: 'Funding too expensive for longs',
  funding_short: 'Funding too expensive for shorts',
  policy_filter: 'AI filter rejected the setup',
  position_size: 'Position size below minimum',
  order_failed: 'Order could not be placed',
};

const FRIENDLY_LEVEL_LABELS = {
  success: 'Trade',
  info: 'Update',
  warning: 'Heads-up',
  error: 'Issue',
  system: 'System',
  debug: 'Detail',
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

function friendlyReason(reason) {
  if (!reason) return 'Other';
  const key = reason.toString().toLowerCase();
  if (DECISION_REASON_LABELS[key]) {
    return DECISION_REASON_LABELS[key];
  }
  return key
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
    .trim()
    || 'Other';
}

function parseStructuredLog(line, fallbackLevel = 'info') {
  const raw = (line ?? '').toString();
  const trimmed = raw.trim();
  const match = trimmed.match(
    /^(\d{4}-\d{2}-\d{2}[^│]*?)\s*│\s*([A-Z]+)\s*│\s*([^│]+)\s*│\s*(.*)$/,
  );
  if (match) {
    return {
      raw: trimmed,
      timestamp: match[1]?.trim() || null,
      level: match[2]?.trim().toLowerCase() || fallbackLevel,
      logger: match[3]?.trim() || null,
      message: match[4]?.trim() || '',
    };
  }
  return {
    raw: trimmed,
    level: (fallbackLevel || 'info').toLowerCase(),
    message: trimmed,
  };
}

function toTitleWords(value) {
  return (value || '')
    .toString()
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
    .trim();
}

function formatExtraDetails(raw) {
  if (!raw) return '';
  const normalized = raw.replace(/[{}]/g, '').trim();
  const pairs = [];
  const quotedPairs = normalized.matchAll(/'([^']+)'\s*:\s*'([^']+)'/g);
  for (const match of quotedPairs) {
    const [, key, value] = match;
    pairs.push([key, value]);
  }
  if (!pairs.length) {
    const simplePairs = normalized.matchAll(/([A-Za-z_]+)=([\d.+-]+)/g);
    for (const match of simplePairs) {
      const [, key, value] = match;
      pairs.push([key, value]);
    }
  }
  if (!pairs.length) return '';
  return pairs
    .map(([key, value]) => `${toTitleWords(key)} ${value}`)
    .join(' • ');
}

function humanizeLogLine(line, fallbackLevel = 'info') {
  const parsed = parseStructuredLog(line, fallbackLevel);
  const baseLevel = (parsed.level || fallbackLevel || 'info').toLowerCase();
  let severity = baseLevel;
  let label = FRIENDLY_LEVEL_LABELS[severity] || severity.toUpperCase();
  let relevant = severity !== 'debug';
  let text = parsed.message || parsed.raw;

  const bucketLabels = { S: 'small', M: 'medium', L: 'large' };
  const entryMatch = parsed.message?.match(
    /^ENTRY (\S+) (BUY|SELL) qty=([\d.]+) px≈([\d.]+) SL=([\d.]+) TP=([\d.]+) bucket=([A-Z])(?:\s+alpha=([\d.]+)\/([\d.]+))?/,
  );
  if (entryMatch) {
    const [, symbol, side, qtyStr, pxStr, slStr, tpStr, bucket, alphaProb, alphaConf] = entryMatch;
    const qtyNum = Number(qtyStr);
    const qty = Number.isFinite(qtyNum)
      ? qtyNum.toFixed(qtyNum >= 1 ? 2 : 4)
      : qtyStr;
    const price = formatNumber(pxStr, 4);
    const sl = formatNumber(slStr, 4);
    const tp = formatNumber(tpStr, 4);
    const direction = side === 'BUY' ? 'long' : 'short';
    const bucketLabel = bucketLabels[bucket] || bucket;
    const extras = [`SL ${sl}`, `TP ${tp}`, `Size ${bucketLabel}`];
    if (alphaProb) {
      const prob = formatNumber(alphaProb, 2);
      if (prob !== '–') {
        extras.push(`AI ${prob} prob`);
      }
      const conf = formatNumber(alphaConf, 2);
      if (conf !== '–') {
        extras.push(`conf ${conf}`);
      }
    }
    text = `Opened ${direction} on ${symbol} at ~${price} (${qty} units). ${extras.join(', ')}.`;
    label = 'Trade placed';
    severity = 'success';
    relevant = true;
    return { text, label, severity, relevant, parsed };
  }

  const exitMatch = parsed.message?.match(
    /^EXIT (\S+) (BUY|SELL) qty=([\d.]+) exit≈([\d.]+) PNL=([\-\d.]+)USDT R=([\-\d.]+)/,
  );
  if (exitMatch) {
    const [, symbol, side, qtyStr, exitStr, pnlStr, rStr] = exitMatch;
    const exitPrice = formatNumber(exitStr, 4);
    const pnl = Number(pnlStr);
    const pnlText = Number.isFinite(pnl) ? `${pnl >= 0 ? '+' : ''}${pnl.toFixed(2)} USDT` : `${pnlStr} USDT`;
    const r = Number(rStr);
    const rText = Number.isFinite(r) ? r.toFixed(2) : rStr;
    const direction = side === 'BUY' ? 'long' : 'short';
    text = `Closed ${direction} on ${symbol} at ~${exitPrice} for ${pnlText} (${rText} R).`;
    label = pnl >= 0 ? 'Trade win' : 'Trade loss';
    severity = pnl >= 0 ? 'success' : 'warning';
    relevant = true;
    return { text, label, severity, relevant, parsed };
  }

  const skipMatch = parsed.message?.match(/^SKIP (\S+): ([\w_]+)(.*)$/);
  if (skipMatch) {
    const [, symbol, reason, extraRaw] = skipMatch;
    const detail = formatExtraDetails(extraRaw);
    const reasonLabel = friendlyReason(reason);
    text = `Skipped ${symbol} — ${reasonLabel}${detail ? ` (${detail})` : ''}.`;
    label = 'Skipped trade';
    severity = 'warning';
    relevant = true;
    return { text, label, severity, relevant, parsed, reason };
  }

  const policyMatch = parsed.message?.match(/^policy skip (\S+):\s*alpha=([\d.]+)\s+conf=([\d.]+)/i);
  if (policyMatch) {
    const [, symbol, alpha, conf] = policyMatch;
    const alphaText = Number.isFinite(Number(alpha)) ? Number(alpha).toFixed(2) : alpha;
    const confText = Number.isFinite(Number(conf)) ? Number(conf).toFixed(2) : conf;
    text = `AI filter skipped ${symbol} (alpha ${alphaText}, confidence ${confText}).`;
    label = 'AI filter';
    severity = 'warning';
    relevant = true;
    return { text, label, severity, relevant, parsed, reason: 'policy_filter' };
  }

  const entryFailMatch = parsed.message?.match(/^entry fail (\S+):\s*(.*)$/i);
  if (entryFailMatch) {
    const [, symbol, detail] = entryFailMatch;
    text = `Order for ${symbol} failed${detail ? `: ${detail}` : '.'}`;
    label = 'Order issue';
    severity = 'error';
    relevant = true;
    return { text, label, severity, relevant, parsed, reason: 'order_failed' };
  }

  const fasttpOkMatch = parsed.message?.match(/^FASTTP (\S+) .*→ exit ([\d.]+)/);
  if (fasttpOkMatch) {
    const [, symbol] = fasttpOkMatch;
    text = `Fast take-profit tightened for ${symbol} after a quick move.`;
    label = 'Fast TP';
    severity = 'info';
    relevant = true;
    return { text, label, severity, relevant, parsed };
  }

  const fasttpErrMatch = parsed.message?.match(/^FASTTP (\S+) replace error: (.*)$/);
  if (fasttpErrMatch) {
    const [, symbol, detail] = fasttpErrMatch;
    text = `Fast TP adjustment failed for ${symbol}: ${detail}`;
    label = 'Fast TP';
    severity = 'warning';
    relevant = true;
    return { text, label, severity, relevant, parsed };
  }

  const startMatch = parsed.message?.match(/^Starting bot \(mode=(\w+), loop=(\w+)\)/);
  if (startMatch) {
    const [, mode, loop] = startMatch;
    const modeLabel = mode === 'PAPER' ? 'paper' : mode?.toLowerCase() || 'live';
    const loopLabel = loop?.toLowerCase() === 'true' ? 'continuous' : 'single-run';
    text = `Bot starting in ${modeLabel} mode (${loopLabel}).`;
    label = 'Bot status';
    severity = 'system';
    relevant = true;
    return { text, label, severity, relevant, parsed };
  }

  const stopMatch = parsed.message?.match(/^Bot stopped\. Safe to exit\.?$/);
  if (stopMatch) {
    text = 'Bot stopped safely. You can close the session.';
    label = 'Bot status';
    severity = 'system';
    relevant = true;
    return { text, label, severity, relevant, parsed };
  }

  const launchMatch = parsed.message?.match(/^Launching bot:/);
  if (launchMatch) {
    text = 'Launching the trading bot with your current settings.';
    label = 'Bot status';
    severity = 'system';
    relevant = true;
    return { text, label, severity, relevant, parsed };
  }

  const configMatch = parsed.message?.match(/^Configuration updated$/);
  if (configMatch) {
    text = 'Configuration saved successfully.';
    label = 'Settings';
    severity = 'system';
    relevant = true;
    return { text, label, severity, relevant, parsed };
  }

  const cycleMatch = parsed.message?.match(/^Cycle finished in ([\d.]+)s\./);
  if (cycleMatch) {
    const [, seconds] = cycleMatch;
    const duration = Number(seconds);
    const durationText = Number.isFinite(duration) ? `${duration.toFixed(1)}s` : `${seconds}s`;
    text = `Scan finished in ${durationText}.`;
    label = 'Scan complete';
    severity = 'info';
    relevant = false;
    return { text, label, severity, relevant, parsed };
  }

  const scanningMatch = parsed.message?.match(/^Scanning (\d+) symbols?(?::\s*(.*))?/);
  if (scanningMatch) {
    const [, count, list] = scanningMatch;
    const preview = list ? list.split(',').slice(0, 3).join(', ').trim() : '';
    text = `Reviewing ${count} markets${preview ? ` (e.g. ${preview})` : ''}.`;
    label = 'Scan';
    severity = 'info';
    relevant = false;
    return { text, label, severity, relevant, parsed };
  }

  const shutdownMatch = parsed.message?.match(/^Shutdown signal received/);
  if (shutdownMatch) {
    text = 'Shutdown signal received — finishing the current cycle.';
    label = 'Bot status';
    severity = 'system';
    relevant = true;
    return { text, label, severity, relevant, parsed };
  }

  if (!text) {
    text = parsed.raw || '';
  }

  if (parsed.level === 'error') {
    relevant = true;
  }

  return { text, label, severity, relevant, parsed };
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
  const parsed = parseStructuredLog(line, normalizedLevel);
  const derivedLevel = (parsed.level || normalizedLevel).toLowerCase();
  const el = document.createElement('div');
  el.className = `log-line ${derivedLevel}`.trim();

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
  label.textContent = labelMap[derivedLevel] || derivedLevel.toUpperCase();
  meta.append(label);

  const message = document.createElement('div');
  message.className = 'log-message';
  message.textContent = parsed.raw ?? line;

  el.append(meta, message);
  logStream.append(el);
  while (logStream.children.length > 500) {
    logStream.removeChild(logStream.firstChild);
  }
  if (autoScrollEnabled) {
    logStream.scrollTop = logStream.scrollHeight;
  }

  appendCompactLog({ line: parsed.raw ?? line, level: derivedLevel, ts });
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
  const groups = [
    {
      body: tradeBodyPosition,
      columns: ['symbol', 'side', 'size'],
    },
    {
      body: tradeBodyPricing,
      columns: ['entry', 'exit'],
    },
    {
      body: tradeBodyPerformance,
      columns: ['pnl', 'r'],
    },
    {
      body: tradeBodyTiming,
      columns: ['opened', 'closed'],
    },
  ];

  groups.forEach((group) => {
    if (group.body) {
      group.body.innerHTML = '';
    }
  });

  if (!history || history.length === 0) {
    const placeholder = document.createElement('tr');
    const cell = document.createElement('td');
    cell.colSpan = 3;
    cell.textContent = 'No trades yet.';
    cell.className = 'empty';
    placeholder.append(cell);
    if (tradeBodyPosition) {
      tradeBodyPosition.append(placeholder);
    }
    groups
      .filter((group) => group.body && group.body !== tradeBodyPosition)
      .forEach((group) => {
        const row = document.createElement('tr');
        const filler = document.createElement('td');
        filler.colSpan = group.columns.length;
        filler.className = 'empty';
        filler.textContent = 'Awaiting trade data…';
        row.append(filler);
        group.body.append(row);
      });
    return;
  }

  for (const trade of history) {
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

    const columnRenderers = {
      symbol: () => createTradeCell('Symbol', { text: trade.symbol || '–', className: 'symbol' }),
      side: () => createTradeCell('Side', { node: sideBadge }),
      size: () => createTradeCell('Size', { text: formatNumber(trade.qty, 4), className: 'numeric' }),
      entry: () => createTradeCell('Entry', { text: formatNumber(trade.entry, 4), className: 'numeric' }),
      exit: () => createTradeCell('Exit', { text: formatNumber(trade.exit, 4), className: 'numeric' }),
      pnl: () =>
        createTradeCell('PNL (USDT)', {
          text: pnlValue,
          className: ['numeric', pnlClass].filter(Boolean).join(' '),
        }),
      r: () =>
        createTradeCell('R', {
          text: formatNumber(pnlR, 2),
          className: ['numeric', pnlRClass].filter(Boolean).join(' '),
        }),
      opened: () => createTradeCell('Opened', { text: formatTimestamp(trade.opened_at_iso) }),
      closed: () => createTradeCell('Closed', { text: formatTimestamp(trade.closed_at_iso) }),
    };

    groups.forEach((group) => {
      if (!group.body) return;
      const row = document.createElement('tr');
      group.columns.forEach((key) => {
        const renderer = columnRenderers[key];
        if (renderer) {
          row.append(renderer());
        }
      });
      group.body.append(row);
    });
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

function renderDecisionStats(stats) {
  if (!decisionSummary || !decisionReasons) return;
  const takenMetric = decisionSummary.querySelector('[data-metric="taken"] strong');
  const skippedMetric = decisionSummary.querySelector('[data-metric="skipped"] strong');
  const taken = Number(stats?.taken ?? 0);
  const rejectedCounts = stats?.rejected && typeof stats.rejected === 'object' ? stats.rejected : {};
  const rejectedTotalRaw = Number(stats?.rejected_total ?? 0);
  const rejectedTotal = Number.isFinite(rejectedTotalRaw) && rejectedTotalRaw > 0
    ? rejectedTotalRaw
    : Object.values(rejectedCounts).reduce((acc, value) => acc + Number(value ?? 0), 0);

  if (takenMetric) {
    takenMetric.textContent = taken.toString();
  }
  if (skippedMetric) {
    skippedMetric.textContent = rejectedTotal.toString();
  }

  decisionReasons.innerHTML = '';

  const items = Object.entries(rejectedCounts)
    .map(([reason, count]) => ({
      reason,
      count: Number(count ?? 0),
      label: friendlyReason(reason),
    }))
    .filter((item) => item.count > 0);

  if (!items.length) {
    const li = document.createElement('li');
    li.className = 'empty';
    li.textContent = taken > 0 ? 'No skipped trades recorded.' : 'No trade decisions yet.';
    decisionReasons.append(li);
    return;
  }

  items.sort((a, b) => {
    if (b.count !== a.count) return b.count - a.count;
    return a.label.localeCompare(b.label);
  });

  for (const item of items) {
    const li = document.createElement('li');
    li.dataset.reason = item.reason;
    const labelEl = document.createElement('span');
    labelEl.className = 'reason-label';
    labelEl.textContent = item.label;
    const countEl = document.createElement('span');
    countEl.className = 'reason-count';
    countEl.textContent = item.count.toString();
    li.append(labelEl, countEl);
    decisionReasons.append(li);
  }
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
  const friendly = humanizeLogLine(line, level);
  if (!friendly || !friendly.relevant) return;

  const severity = (friendly.severity || level || 'info').toLowerCase();
  const el = document.createElement('div');
  el.className = `log-line ${severity}`.trim();

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
  label.textContent = friendly.label || FRIENDLY_LEVEL_LABELS[severity] || severity.toUpperCase();
  meta.append(label);

  const message = document.createElement('div');
  message.className = 'log-message';
  message.textContent = friendly.text || line;

  el.append(meta, message);
  compactLogStream.append(el);

  while (compactLogStream.children.length > 150) {
    compactLogStream.removeChild(compactLogStream.firstChild);
  }
  if (autoScrollEnabled) {
    compactLogStream.scrollTop = compactLogStream.scrollHeight;
  }
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
    renderDecisionStats(data.decision_stats);
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

if (autoScrollToggles.length > 0) {
  const initial = autoScrollToggles[0].checked;
  autoScrollEnabled = initial;
  autoScrollToggles.forEach((toggle) => {
    toggle.checked = initial;
    toggle.addEventListener('change', () => {
      autoScrollEnabled = toggle.checked;
      autoScrollToggles.forEach((peer) => {
        if (peer !== toggle) {
          peer.checked = autoScrollEnabled;
        }
      });
    });
  });
} else {
  autoScrollEnabled = true;
}

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
