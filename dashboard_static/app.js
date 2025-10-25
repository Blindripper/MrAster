const envContainer = document.getElementById('env-settings');
const envPanel = document.getElementById('env-config-panel');
const btnToggleEnv = document.getElementById('btn-toggle-env');
const btnSaveConfig = document.getElementById('btn-save-config');
const btnSaveCredentials = document.getElementById('btn-save-credentials');
const btnStart = document.getElementById('btn-start');
const btnStop = document.getElementById('btn-stop');
const btnSaveAi = document.getElementById('btn-save-ai');
const statusIndicator = document.getElementById('status-indicator');
const statusPid = document.getElementById('status-pid');
const statusStarted = document.getElementById('status-started');
const statusUptime = document.getElementById('status-uptime');
const logStream = document.getElementById('log-stream');
const compactLogStream = document.getElementById('log-brief');
const autoScrollToggles = document.querySelectorAll('input[data-autoscroll]');
const tradeList = document.getElementById('trade-list');
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
const inputOpenAiKey = document.getElementById('input-openai-key');
const inputAiBudget = document.getElementById('input-ai-budget');
const inputAiModel = document.getElementById('input-ai-model');
const decisionSummary = document.getElementById('decision-summary');
const decisionReasons = document.getElementById('decision-reasons');
const btnApplyPreset = document.getElementById('btn-apply-preset');
const tickerContainer = document.getElementById('market-ticker');
const tickerTrack = document.getElementById('ticker-track');
const tickerEmpty = document.getElementById('ticker-empty');
const aiBudgetCard = document.getElementById('ai-budget');
const aiBudgetModeLabel = document.getElementById('ai-budget-mode');
const aiBudgetMeta = document.getElementById('ai-budget-meta');
const aiBudgetFill = document.getElementById('ai-budget-fill');
const aiActivityFeed = document.getElementById('ai-activity');
const aiChatMessages = document.getElementById('ai-chat-messages');
const aiChatForm = document.getElementById('ai-chat-form');
const aiChatInput = document.getElementById('ai-chat-input');
const aiChatStatus = document.getElementById('ai-chat-status');
const activePositionsCard = document.getElementById('active-positions-card');
const activePositionsModeLabel = document.getElementById('active-positions-mode');
const activePositionsWrapper = document.getElementById('active-positions-wrapper');
const activePositionsEmpty = document.getElementById('active-positions-empty');
const activePositionsRows = document.getElementById('active-positions-rows');
const modeButtons = document.querySelectorAll('[data-mode-select]');
const btnHeroDownload = document.getElementById('btn-hero-download');

const DEFAULT_BOT_STATUS = { running: false, pid: null, started_at: null, uptime_s: null };

let currentConfig = {};
let reconnectTimer = null;
let pnlChart = null;
let proMode = false;
let aiMode = false;
let selectedPreset = 'mid';
let autoScrollEnabled = true;
let quickConfigPristine = true;
let envCollapsed = true;
let mostTradedTimer = null;
let lastAiBudget = null;
let lastMostTradedAssets = [];
let latestTradesSnapshot = null;
let lastBotStatus = { ...DEFAULT_BOT_STATUS };
let aiChatHistory = [];
let aiChatPending = false;
let activePositions = [];
let tradesRefreshTimer = null;
let tradeViewportSyncHandle = null;
const aiChatSubmit = aiChatForm ? aiChatForm.querySelector('button[type="submit"]') : null;

function buildAsterPositionUrl(symbol) {
  if (!symbol) return null;
  const trimmed = symbol.toString().trim();
  if (!trimmed) return null;
  return `https://www.asterdex.com/en/futures/v1/${trimmed.toUpperCase()}`;
}

function openAsterPositionUrl(url) {
  if (!url) return;
  window.open(url, '_blank', 'noopener');
}

function getCurrentMode() {
  if (aiMode) return 'ai';
  if (proMode) return 'pro';
  return 'standard';
}

function updateModeButtons() {
  const active = getCurrentMode();
  modeButtons.forEach((button) => {
    const isActive = button.dataset.modeSelect === active;
    button.classList.toggle('active', isActive);
    button.setAttribute('aria-pressed', isActive ? 'true' : 'false');
  });
}

function updateAiBudgetModeLabel() {
  if (!aiBudgetModeLabel) return;
  const active = getCurrentMode();
  if (active === 'ai') {
    aiBudgetModeLabel.textContent = 'AI-Mode';
  } else if (active === 'pro') {
    aiBudgetModeLabel.textContent = 'Pro-Mode';
  } else {
    aiBudgetModeLabel.textContent = 'Standard';
  }
}

function syncModeUi() {
  updateModeButtons();
  updateAiBudgetModeLabel();
}

function syncCollapseToggle(button, collapsed) {
  if (!button) return;
  const expandLabel = button.dataset.labelExpand || 'Expand';
  const collapseLabel = button.dataset.labelCollapse || 'Collapse';
  const ariaExpand = button.dataset.ariaExpand || expandLabel;
  const ariaCollapse = button.dataset.ariaCollapse || collapseLabel;
  const labelTarget = button.querySelector('[data-collapse-label]');
  if (labelTarget) {
    labelTarget.textContent = collapsed ? expandLabel : collapseLabel;
  } else {
    button.textContent = collapsed ? expandLabel : collapseLabel;
  }
  button.setAttribute('aria-expanded', (!collapsed).toString());
  button.setAttribute('aria-label', collapsed ? ariaExpand : ariaCollapse);
  button.classList.toggle('is-expanded', !collapsed);
}

function setEnvCollapsed(collapsed) {
  envCollapsed = Boolean(collapsed);
  if (envPanel) {
    envPanel.classList.toggle('collapsed', envCollapsed);
  }
  if (btnToggleEnv) {
    syncCollapseToggle(btnToggleEnv, envCollapsed);
  }
}

function toggleEnvPanel() {
  setEnvCollapsed(!envCollapsed);
}

setEnvCollapsed(true);

const PRESETS = {
  low: {
    label: 'Low',
    summary: 'Capital preservation first: slower signal intake, narrower exposure, and conservative scaling.',
    risk: 0.5,
    leverage: 1,
    edgeMinR: 0.08,
    slAtr: 1.1,
    tpAtr: 1.8,
    fasttp: {
      minR: 0.18,
      ret1: -0.0007,
      ret3: -0.0014,
      snapAtr: 0.2,
      cooldown: 60,
    },
    sizeMult: {
      base: 0.9,
      s: 0.9,
      m: 1.15,
      l: 1.35,
    },
    alpha: {
      threshold: 0.6,
      minConf: 0.28,
      promoteDelta: 0.18,
      rewardMargin: 0.06,
    },
    equityFraction: 0.22,
    maxOpenGlobal: 1,
    trendBias: 'with',
  },
  mid: {
    label: 'Mid',
    summary: 'Balanced cadence with moderate risk and leverage designed for steady account growth.',
    risk: 1.0,
    leverage: 2,
    edgeMinR: 0.06,
    slAtr: 1.3,
    tpAtr: 2.0,
    fasttp: {
      minR: 0.25,
      ret1: -0.001,
      ret3: -0.002,
      snapAtr: 0.25,
      cooldown: 45,
    },
    sizeMult: {
      base: 1.0,
      s: 1.0,
      m: 1.4,
      l: 1.9,
    },
    alpha: {
      threshold: 0.55,
      minConf: 0.22,
      promoteDelta: 0.15,
      rewardMargin: 0.05,
    },
    equityFraction: 0.28,
    maxOpenGlobal: 2,
    trendBias: 'with',
  },
  high: {
    label: 'High',
    summary: 'High-frequency execution with wider risk budgets and leverage up to the aggressive limit.',
    risk: 2.0,
    leverage: 4,
    edgeMinR: 0.04,
    slAtr: 1.7,
    tpAtr: 2.6,
    fasttp: {
      minR: 0.32,
      ret1: -0.0013,
      ret3: -0.0026,
      snapAtr: 0.3,
      cooldown: 30,
    },
    sizeMult: {
      base: 1.2,
      s: 1.2,
      m: 1.6,
      l: 2.2,
    },
    alpha: {
      threshold: 0.52,
      minConf: 0.18,
      promoteDelta: 0.12,
      rewardMargin: 0.04,
    },
    equityFraction: 0.34,
    maxOpenGlobal: 3,
    trendBias: 'with',
  },
  att: {
    label: 'ATT',
    summary: 'Against-the-trend fading: contrarian plays with tighter stops and disciplined sizing.',
    risk: 0.75,
    leverage: 2,
    edgeMinR: 0.07,
    slAtr: 0.9,
    tpAtr: 1.6,
    fasttp: {
      minR: 0.2,
      ret1: -0.0005,
      ret3: -0.0012,
      snapAtr: 0.18,
      cooldown: 40,
    },
    sizeMult: {
      base: 0.85,
      s: 0.85,
      m: 1.1,
      l: 1.3,
    },
    alpha: {
      threshold: 0.6,
      minConf: 0.25,
      promoteDelta: 0.16,
      rewardMargin: 0.05,
    },
    equityFraction: 0.24,
    maxOpenGlobal: 2,
    trendBias: 'against',
  },
};

const CONTEXT_LABELS = {
  adx: 'ADX',
  rsi: 'RSI',
  atr_pct: 'ATR / Price',
  spread_bps: 'Spread',
  funding: 'Funding',
  qv_score: 'Volume score',
  slope_htf: 'HTF slope',
  trend: 'Trend bias',
  alpha_prob: 'Alpha prob.',
  alpha_conf: 'Alpha conf.',
  regime_adx: 'Regime ADX',
  regime_slope: 'Regime slope',
  sentinel_label: 'Sentinel label',
  sentinel_event_risk: 'Event risk',
  sentinel_hype: 'Hype score',
  sentinel_factor: 'Risk sizing',
};

const CONTEXT_KEYS = [
  'adx',
  'rsi',
  'atr_pct',
  'spread_bps',
  'funding',
  'qv_score',
  'slope_htf',
  'trend',
  'alpha_prob',
  'alpha_conf',
  'regime_adx',
  'regime_slope',
  'sentinel_label',
  'sentinel_event_risk',
  'sentinel_hype',
  'sentinel_factor',
];

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
  sentinel_veto: 'Sentinel vetoed trade',
  ai_risk_zero: 'AI sized trade to zero',
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
  if (inputOpenAiKey) {
    inputOpenAiKey.value = env?.ASTER_OPENAI_API_KEY ?? '';
  }
  if (inputAiBudget) {
    inputAiBudget.value = env?.ASTER_AI_DAILY_BUDGET_USD ?? '1000';
  }
  if (inputAiModel) {
    const model = env?.ASTER_AI_MODEL ?? 'gpt-4o';
    const existingOption = Array.from(inputAiModel.options).find((option) => option.value === model);
    if (existingOption) {
      inputAiModel.value = model;
    } else {
      const fallbackOption = new Option(model, model, true, true);
      inputAiModel.add(fallbackOption);
    }
  }
}

async function loadConfig() {
  const res = await fetch('/api/config');
  if (!res.ok) throw new Error('Unable to load configuration');
  currentConfig = await res.json();
  renderConfig(currentConfig.env);
  renderCredentials(currentConfig.env);
  syncQuickSetupFromEnv(currentConfig.env);
  await syncModeFromEnv(currentConfig.env);
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

function gatherAiPayload() {
  const payload = {};
  if (inputOpenAiKey) {
    payload.ASTER_OPENAI_API_KEY = inputOpenAiKey.value.trim();
  }
  if (inputAiBudget) {
    const value = inputAiBudget.value.trim();
    payload.ASTER_AI_DAILY_BUDGET_USD = value === '' ? '0' : value;
  }
  if (inputAiModel) {
    payload.ASTER_AI_MODEL = inputAiModel.value.trim();
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
    syncQuickSetupFromEnv(currentConfig.env);
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
    syncQuickSetupFromEnv(currentConfig.env);
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

async function saveAiConfig() {
  if (!btnSaveAi) return;
  const payload = gatherAiPayload();
  btnSaveAi.disabled = true;
  btnSaveAi.textContent = 'Saving…';
  try {
    const res = await fetch('/api/config', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ env: payload }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || 'Saving AI configuration failed');
    }
    currentConfig = await res.json();
    renderCredentials(currentConfig.env);
    syncQuickSetupFromEnv(currentConfig.env);
    await syncModeFromEnv(currentConfig.env);
    btnSaveAi.textContent = 'Saved ✓';
    setTimeout(() => (btnSaveAi.textContent = 'Save'), 1500);
  } catch (err) {
    btnSaveAi.textContent = 'Error';
    alert(err.message);
    setTimeout(() => (btnSaveAi.textContent = 'Save'), 2000);
  } finally {
    btnSaveAi.disabled = false;
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

function formatPriceDisplay(value, options = {}) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric) || numeric <= 0) return '–';

  const { minimumFractionDigits, maximumFractionDigits } = options;
  const hasCustomDigits =
    (Number.isInteger(minimumFractionDigits) && minimumFractionDigits >= 0) ||
    (Number.isInteger(maximumFractionDigits) && maximumFractionDigits >= 0);

  if (hasCustomDigits) {
    const localeOptions = {};
    if (Number.isInteger(minimumFractionDigits) && minimumFractionDigits >= 0) {
      localeOptions.minimumFractionDigits = minimumFractionDigits;
    }
    if (Number.isInteger(maximumFractionDigits) && maximumFractionDigits >= 0) {
      localeOptions.maximumFractionDigits = maximumFractionDigits;
    }
    if (
      localeOptions.minimumFractionDigits != null &&
      localeOptions.maximumFractionDigits == null
    ) {
      localeOptions.maximumFractionDigits = localeOptions.minimumFractionDigits;
    }
    return numeric.toLocaleString(undefined, localeOptions);
  }

  if (numeric >= 10000) {
    return numeric.toLocaleString(undefined, {
      maximumFractionDigits: 0,
    });
  }
  if (numeric >= 100) {
    return numeric.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }
  if (numeric >= 1) {
    return numeric.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }
  if (numeric >= 0.1) {
    return numeric.toLocaleString(undefined, {
      minimumFractionDigits: 3,
      maximumFractionDigits: 3,
    });
  }
  if (numeric >= 0.01) {
    return numeric.toLocaleString(undefined, {
      minimumFractionDigits: 4,
      maximumFractionDigits: 4,
    });
  }
  return numeric.toLocaleString(undefined, {
    minimumFractionDigits: 6,
    maximumFractionDigits: 6,
  });
}

function formatVolumeDisplay(value, quote = 'USDT') {
  const numeric = Number(value);
  if (!Number.isFinite(numeric) || numeric <= 0) return `24h Vol –`;
  const abs = Math.abs(numeric);
  let scaled = abs;
  let suffix = '';
  if (abs >= 1e12) {
    scaled = abs / 1e12;
    suffix = 'T';
  } else if (abs >= 1e9) {
    scaled = abs / 1e9;
    suffix = 'B';
  } else if (abs >= 1e6) {
    scaled = abs / 1e6;
    suffix = 'M';
  } else if (abs >= 1e3) {
    scaled = abs / 1e3;
    suffix = 'K';
  }
  const digits = scaled >= 100 ? 0 : scaled >= 10 ? 1 : 2;
  return `24h Vol ${scaled.toFixed(digits)}${suffix} ${quote || 'USDT'}`;
}

function handleTickerLogoError(event) {
  const img = event.currentTarget;
  if (!img) return;
  const raw = (img.dataset.fallbacks || '').split('|').filter(Boolean);
  if (raw.length === 0) {
    img.removeEventListener('error', handleTickerLogoError);
    const wrapper = img.parentElement;
    if (wrapper) {
      const symbol = (wrapper.dataset.symbol || '?').toString().slice(0, 3).toUpperCase();
      wrapper.innerHTML = '';
      const placeholder = document.createElement('span');
      placeholder.className = 'ticker-logo-placeholder';
      placeholder.textContent = symbol;
      wrapper.appendChild(placeholder);
    }
    return;
  }
  const [next, ...rest] = raw;
  img.dataset.fallbacks = rest.join('|');
  img.src = next;
}

function buildTickerLogo(asset) {
  const wrapper = document.createElement('span');
  wrapper.className = 'ticker-logo';
  wrapper.dataset.symbol = (asset.base || asset.symbol || '?').toString().toUpperCase();
  const sources = [];
  const seen = new Set();
  [asset.logo, ...(asset.logo_fallbacks || []), ...(asset.logo_candidates || [])].forEach((url) => {
    const normalized = (url || '').toString().trim();
    if (!normalized || seen.has(normalized)) return;
    seen.add(normalized);
    sources.push(normalized);
  });

  if (sources.length === 0) {
    const placeholder = document.createElement('span');
    placeholder.className = 'ticker-logo-placeholder';
    placeholder.textContent = wrapper.dataset.symbol.slice(0, 3);
    wrapper.appendChild(placeholder);
    return wrapper;
  }

  const img = document.createElement('img');
  img.src = sources.shift();
  img.alt = `${asset.base || asset.symbol || ''} logo`;
  img.loading = 'lazy';
  img.decoding = 'async';
  img.referrerPolicy = 'no-referrer';
  img.dataset.fallbacks = sources.join('|');
  img.addEventListener('error', handleTickerLogoError);
  wrapper.appendChild(img);
  return wrapper;
}

function createTickerItem(asset) {
  const item = document.createElement('div');
  item.className = 'ticker-item';
  item.setAttribute('role', 'listitem');

  const logo = buildTickerLogo(asset);

  const meta = document.createElement('div');
  meta.className = 'ticker-meta';

  const symbol = document.createElement('span');
  symbol.className = 'ticker-symbol';
  symbol.textContent = (asset.base || asset.symbol || '').toString().toUpperCase();

  const price = document.createElement('span');
  price.className = 'ticker-price';
  price.textContent = formatPriceDisplay(asset.price);

  meta.append(symbol, price);

  const stats = document.createElement('div');
  stats.className = 'ticker-stats';

  const volume = document.createElement('span');
  volume.className = 'ticker-volume';
  volume.textContent = formatVolumeDisplay(asset.volume_quote, asset.quote);

  const changeValue = Number(asset.change_15m ?? 0);
  const change = document.createElement('span');
  change.className = `ticker-change ${changeValue >= 0 ? 'positive' : 'negative'}`;
  const arrow = document.createElement('span');
  arrow.className = 'arrow';
  arrow.textContent = changeValue >= 0 ? '▲' : '▼';
  const percent = document.createElement('span');
  percent.className = 'value';
  const digits = Math.abs(changeValue) >= 1 ? 1 : 2;
  percent.textContent = `${Math.abs(changeValue).toFixed(digits)}%`;
  change.append(arrow, percent);

  stats.append(volume, change);

  item.append(logo, meta, stats);
  return item;
}

function computeTickerMetrics(assets) {
  if (!tickerTrack || !Array.isArray(assets) || assets.length === 0) return;
  window.requestAnimationFrame(() => {
    window.requestAnimationFrame(() => {
      const baseCount = assets.length;
      const children = Array.from(tickerTrack.children).slice(0, baseCount);
      if (children.length === 0) return;
      const styles = window.getComputedStyle(tickerTrack);
      const gap = parseFloat(styles.columnGap || styles.gap || '0');
      const totalWidth = children.reduce((sum, child) => sum + child.getBoundingClientRect().width, 0);
      const translate = Math.ceil(totalWidth + gap * Math.max(0, children.length - 1));
      tickerTrack.style.setProperty('--ticker-translate', `${translate}px`);
      const duration = Math.max(20, translate / 35);
      tickerTrack.style.setProperty('--ticker-duration', `${duration}s`);
    });
  });
}

function renderMostTradedTicker(assets, { error } = {}) {
  if (!tickerContainer || !tickerTrack) return;
  tickerTrack.innerHTML = '';
  tickerTrack.style.removeProperty('--ticker-translate');
  tickerTrack.style.removeProperty('--ticker-duration');

  const hasAssets = Array.isArray(assets) && assets.length > 0;
  tickerContainer.classList.toggle('has-data', hasAssets);

  if (!hasAssets) {
    if (tickerEmpty) {
      tickerEmpty.textContent = error || 'No market data available right now.';
    }
    return;
  }

  if (tickerEmpty) {
    tickerEmpty.textContent = '';
  }

  const fragment = document.createDocumentFragment();
  const doubled = assets.concat(assets);
  doubled.forEach((asset, index) => {
    const node = createTickerItem(asset);
    if (index >= assets.length) {
      node.classList.add('ticker-item-duplicate');
      node.setAttribute('aria-hidden', 'true');
    }
    fragment.appendChild(node);
  });
  tickerTrack.appendChild(fragment);
  computeTickerMetrics(assets);
}

async function loadMostTradedCoins() {
  if (!tickerContainer) return;
  try {
    if (tickerEmpty) {
      tickerEmpty.textContent = 'Gathering market leaders…';
    }
    const res = await fetch('/api/markets/most-traded');
    if (!res.ok) {
      const payload = await res.json().catch(() => ({}));
      throw new Error(payload.detail || 'Unable to load market data');
    }
    const data = await res.json();
    const assets = data.assets || [];
    if (assets.length > 0) {
      lastMostTradedAssets = assets;
    }
    renderMostTradedTicker(assets);
  } catch (err) {
    console.warn(err);
    if (lastMostTradedAssets.length > 0) {
      renderMostTradedTicker(lastMostTradedAssets);
    } else {
      renderMostTradedTicker([], { error: 'Unable to load market data.' });
    }
  }
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

function formatTimeShort(value) {
  if (!value) return '–';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '–';
  return date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
}

function computeDurationSeconds(openedIso, closedIso) {
  if (!openedIso || !closedIso) return NaN;
  const opened = new Date(openedIso).getTime();
  const closed = new Date(closedIso).getTime();
  if (Number.isNaN(opened) || Number.isNaN(closed)) return NaN;
  return Math.max(0, Math.round((closed - opened) / 1000));
}

function formatSideLabel(side) {
  if (!side) return '–';
  const normalized = side.toString().toUpperCase();
  if (normalized === 'BUY') return 'LONG';
  if (normalized === 'SELL') return 'SHORT';
  return normalized;
}

const ACTIVE_POSITION_ALIASES = {
  symbol: ['symbol', 'sym', 'ticker', 'pair'],
  size: ['size', 'qty', 'quantity', 'positionAmt', 'position_amt', 'position_amount'],
  entry: ['entry', 'entry_price', 'entryPrice'],
  mark: ['mark', 'mark_price', 'markPrice', 'lastPrice', 'price'],
  roe: ['roe', 'roe_percent', 'roe_pct', 'roePercent', 'pnl_percent', 'pnl_pct'],
  pnl: ['pnl', 'unrealized', 'unrealized_pnl', 'pnl_unrealized', 'unrealizedProfit', 'pnl_usd'],
  nextTp: ['next_tp', 'tp_next', 'nextTarget', 'next_tp_price', 'tp', 'take_profit_next'],
  stop: [
    'stop',
    'stop_loss',
    'stopLoss',
    'stop_price',
    'stopPrice',
    'stopLossPrice',
    'stop_loss_price',
    'sl',
    'stop_next',
    'next_stop',
    'stopTarget',
    'stop_loss_next',
  ],
  side: ['side', 'positionSide', 'direction'],
};

const ACTIVE_POSITION_TIMESTAMP_NUMERIC_KEYS = [
  'opened_at',
  'openedAt',
  'opened_ts',
  'opened_at_ts',
  'open_time',
  'openTime',
  'timestamp',
  'ts',
];

const ACTIVE_POSITION_TIMESTAMP_ISO_KEYS = [
  'opened_at_iso',
  'open_time_iso',
  'openTimeIso',
  'opened_iso',
  'created_at',
  'openedAtIso',
];

const POSITION_CLOSED_FLAG_KEYS = [
  'closed',
  'is_closed',
  'isClosed',
  'closed_out',
  'closedOut',
  'has_closed',
  'hasClosed',
  'settled',
  'isSettled',
  'done',
  'isDone',
  'completed',
  'isCompleted',
];

const POSITION_OPEN_FLAG_KEYS = [
  'open',
  'is_open',
  'isOpen',
  'active',
  'isActive',
  'running',
];

const POSITION_STATUS_KEYS = [
  'status',
  'state',
  'lifecycle',
  'stage',
  'positionStatus',
  'tradeStatus',
];

const POSITION_CLOSED_STATUS_TOKENS = [
  'closed',
  'closing',
  'settled',
  'settlement',
  'exit',
  'exited',
  'inactive',
  'cancelled',
  'canceled',
  'finished',
  'complete',
  'completed',
  'filled',
  'stopped',
  'liquidated',
];

const POSITION_OPEN_STATUS_TOKENS = ['open', 'opening', 'active', 'running', 'live', 'entered'];

const CLOSED_FLAG_POSITIVE_TOKENS = [
  '1',
  'true',
  'yes',
  'y',
  'on',
  'closed',
  'closing',
  'done',
  'complete',
  'completed',
  'finished',
  'exit',
  'exited',
  'inactive',
  'settled',
  'settlement',
  'filled',
  'liquidated',
  'cancelled',
  'canceled',
];

const CLOSED_FLAG_NEGATIVE_TOKENS = ['0', 'false', 'no', 'off', 'open', 'opening', 'active', 'running', 'pending'];

const OPEN_FLAG_POSITIVE_TOKENS = ['1', 'true', 'yes', 'y', 'on', 'open', 'opening', 'active', 'running', 'live'];

const OPEN_FLAG_NEGATIVE_TOKENS = [
  '0',
  'false',
  'no',
  'off',
  'closed',
  'closing',
  'inactive',
  'disabled',
  'done',
  'complete',
  'completed',
  'exit',
  'exited',
  'settled',
  'liquidated',
  'cancelled',
  'canceled',
];

const POSITION_CLOSED_TIMESTAMP_KEYS = [
  'closed_at',
  'closedAt',
  'closed_ts',
  'closedTs',
  'closed_time',
  'closedTime',
  'close_time',
  'closeTime',
  'closed_at_iso',
  'closedAtIso',
  'closed_iso',
  'close_iso',
  'exit_at',
  'exitAt',
  'exited_at',
  'exitedAt',
  'closeTimeIso',
];

function unwrapPositionValue(raw) {
  if (raw === undefined || raw === null) return undefined;
  if (Array.isArray(raw)) {
    return raw.length ? unwrapPositionValue(raw[0]) : undefined;
  }
  if (typeof raw === 'object') {
    if ('value' in raw) return unwrapPositionValue(raw.value);
    if ('price' in raw) return unwrapPositionValue(raw.price);
    if ('amount' in raw) return unwrapPositionValue(raw.amount);
    if ('qty' in raw) return unwrapPositionValue(raw.qty);
    return undefined;
  }
  return raw;
}

function toNumeric(value) {
  if (value === undefined || value === null || value === '') return NaN;
  if (typeof value === 'number') return Number(value);
  if (typeof value === 'string') {
    const normalized = value.replace(/[^0-9+-.eE]/g, '');
    if (!normalized || normalized === '+' || normalized === '-') {
      return NaN;
    }
    return Number(normalized);
  }
  return Number(value);
}

function normalisePositionRecord(record, fallbackSymbol) {
  if (!record || typeof record !== 'object') {
    return { symbol: fallbackSymbol };
  }
  const normalized = { ...record };
  const symbolCandidate =
    unwrapPositionValue(record.symbol) ??
    unwrapPositionValue(record.sym) ??
    unwrapPositionValue(record.ticker) ??
    unwrapPositionValue(record.pair) ??
    fallbackSymbol;
  if (symbolCandidate && !normalized.symbol) {
    normalized.symbol = symbolCandidate;
  }
  return normalized;
}

function mapPositionCollection(collection) {
  if (!collection) return [];
  if (Array.isArray(collection)) {
    return collection.map((item) => normalisePositionRecord(item));
  }
  if (collection instanceof Map) {
    return Array.from(collection.entries()).map(([key, value]) => normalisePositionRecord(value, key));
  }
  if (typeof collection === 'object') {
    return Object.entries(collection).map(([key, value]) => normalisePositionRecord(value, key));
  }
  return [];
}

function normaliseActivePositions(raw) {
  if (!raw || (typeof raw !== 'object' && !Array.isArray(raw))) {
    return [];
  }

  const collected = [];

  const appendCollection = (collection) => {
    const mapped = mapPositionCollection(collection).filter((item) => !isPositionLikelyClosed(item));
    if (mapped.length) {
      collected.push(...mapped);
    }
  };

  const hasModeBuckets =
    typeof raw === 'object' && ['standard', 'pro', 'ai'].some((mode) => raw && raw[mode] !== undefined);

  if (hasModeBuckets) {
    ['standard', 'pro', 'ai'].forEach((mode) => {
      appendCollection(raw[mode]);
    });
    if (collected.length === 0) {
      appendCollection(raw.all || raw.shared);
    }
    return collected;
  }

  appendCollection(raw);

  return collected;
}

function tokeniseTextValue(value) {
  if (value === undefined || value === null) return [];
  return value
    .toString()
    .trim()
    .toLowerCase()
    .split(/[^a-z0-9]+/g)
    .filter(Boolean);
}

function parseFlagValue(value, positiveTokens, negativeTokens) {
  if (value === undefined || value === null) return null;
  if (typeof value === 'boolean') return value;
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) return null;
    if (value === 0) return false;
    return true;
  }
  const tokens = tokeniseTextValue(value);
  if (!tokens.length) return null;
  if (tokens.some((token) => negativeTokens.includes(token))) return false;
  if (tokens.some((token) => positiveTokens.includes(token))) return true;
  return null;
}

function hasClosedTimestamp(position) {
  for (const key of POSITION_CLOSED_TIMESTAMP_KEYS) {
    if (!(key in position)) continue;
    const value = unwrapPositionValue(position[key]);
    if (value === undefined || value === null || value === '') {
      continue;
    }
    const numeric = toNumeric(value);
    if (Number.isFinite(numeric) && numeric > 0) {
      return true;
    }
    const parsed = Date.parse(value);
    if (Number.isFinite(parsed)) {
      return true;
    }
  }
  return false;
}

function sizeLooksClosed(position) {
  const sizeKeys = ACTIVE_POSITION_ALIASES.size || [];
  for (const key of sizeKeys) {
    if (!(key in position)) continue;
    const direct = unwrapPositionValue(position[key]);
    const numeric = toNumeric(direct);
    if (Number.isFinite(numeric)) {
      if (Math.abs(numeric) < 1e-9) {
        return true;
      }
      return false;
    }
    const raw = position[key];
    if (Array.isArray(raw) && raw.length > 0) {
      for (const candidate of raw) {
        const numericCandidate = toNumeric(unwrapPositionValue(candidate));
        if (Number.isFinite(numericCandidate)) {
          if (Math.abs(numericCandidate) < 1e-9) {
            return true;
          }
          return false;
        }
      }
    }
  }
  return false;
}

function isPositionLikelyClosed(position) {
  if (!position || typeof position !== 'object') {
    return false;
  }

  for (const key of POSITION_CLOSED_FLAG_KEYS) {
    if (!(key in position)) continue;
    const flag = parseFlagValue(position[key], CLOSED_FLAG_POSITIVE_TOKENS, CLOSED_FLAG_NEGATIVE_TOKENS);
    if (flag === true) {
      return true;
    }
    if (flag === false) {
      continue;
    }
  }

  for (const key of POSITION_OPEN_FLAG_KEYS) {
    if (!(key in position)) continue;
    const flag = parseFlagValue(position[key], OPEN_FLAG_POSITIVE_TOKENS, OPEN_FLAG_NEGATIVE_TOKENS);
    if (flag === true) {
      return false;
    }
    if (flag === false) {
      return true;
    }
  }

  for (const key of POSITION_STATUS_KEYS) {
    if (!(key in position)) continue;
    const tokens = tokeniseTextValue(position[key]);
    if (!tokens.length) continue;
    if (tokens.some((token) => POSITION_CLOSED_STATUS_TOKENS.includes(token))) {
      return true;
    }
    if (tokens.some((token) => POSITION_OPEN_STATUS_TOKENS.includes(token))) {
      return false;
    }
  }

  if (hasClosedTimestamp(position)) {
    return true;
  }

  if (sizeLooksClosed(position)) {
    return true;
  }

  return false;
}

function pickFieldValue(position, candidates) {
  if (!position || typeof position !== 'object') {
    return { value: undefined, raw: undefined, key: null };
  }
  for (const key of candidates) {
    if (key in position) {
      const raw = position[key];
      const value = unwrapPositionValue(raw);
      if (value !== undefined && value !== null && value !== '') {
        return { value, raw, key };
      }
      if (Array.isArray(raw) || (raw && typeof raw === 'object')) {
        return { value, raw, key };
      }
    }
  }
  return { value: undefined, raw: undefined, key: null };
}

function pickNumericField(position, candidates) {
  const result = pickFieldValue(position, candidates);
  let numeric = toNumeric(result.value);
  if (Number.isFinite(numeric)) {
    return { ...result, numeric };
  }
  if (Array.isArray(result.raw) && result.raw.length > 0) {
    numeric = toNumeric(result.raw[0]);
    if (Number.isFinite(numeric)) {
      return { ...result, numeric };
    }
  }
  return { ...result, numeric: null };
}

function formatBracketLevel(field) {
  if (!field) return '–';

  const valueCandidates = [];

  if (field.value !== undefined && field.value !== null && field.value !== '') {
    valueCandidates.push(field.value);
  }

  if (Array.isArray(field.raw) && field.raw.length > 0) {
    valueCandidates.push(unwrapPositionValue(field.raw[0]));
  }

  for (const candidate of valueCandidates) {
    if (candidate === undefined || candidate === null || candidate === '') {
      continue;
    }
    const numeric = toNumeric(candidate);
    if (Number.isFinite(numeric)) {
      const formatted = formatPriceDisplay(numeric);
      if (formatted !== '–') {
        return formatted;
      }
    }
    if (typeof candidate === 'string' || typeof candidate === 'number') {
      return candidate.toString();
    }
  }

  return '–';
}

function formatSignedNumber(value, digits = 2) {
  if (!Number.isFinite(value)) return null;
  const abs = Math.abs(value).toFixed(digits);
  if (value > 0) return `+${abs}`;
  if (value < 0) return `-${abs}`;
  return abs;
}

function formatPercentField(field, digits = 2) {
  if (!field || !Number.isFinite(field.numeric)) {
    return null;
  }
  let numeric = field.numeric;
  const key = (field.key || '').toString();
  const keyHintsPercent = /percent|pct/i.test(key);
  if (!keyHintsPercent && Math.abs(numeric) <= 10) {
    numeric *= 100;
  }
  const abs = Math.abs(numeric).toFixed(digits);
  const sign = numeric > 0 ? '+' : numeric < 0 ? '-' : '';
  return { text: `${sign}${abs}%`, numeric };
}

function formatPositionSize(value) {
  if (!Number.isFinite(value)) return '–';
  const abs = Math.abs(value);
  if (abs >= 1000) {
    return abs.toLocaleString(undefined, { maximumFractionDigits: 0 });
  }
  if (abs >= 100) {
    return abs.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  }
  if (abs >= 10) {
    return abs.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
  if (abs >= 1) {
    return abs.toLocaleString(undefined, { minimumFractionDigits: 3, maximumFractionDigits: 3 });
  }
  if (abs >= 0.1) {
    return abs.toLocaleString(undefined, { minimumFractionDigits: 4, maximumFractionDigits: 4 });
  }
  return abs.toLocaleString(undefined, { minimumFractionDigits: 5, maximumFractionDigits: 5 });
}

function getPositionSymbol(position) {
  const field = pickFieldValue(position, ACTIVE_POSITION_ALIASES.symbol || []);
  const symbol = field.value ?? position.symbol;
  if (!symbol) return '–';
  return symbol.toString().toUpperCase();
}

function buildSideBadge(side) {
  if (!side) return null;
  const badge = document.createElement('span');
  const normalized = side.toString().toLowerCase();
  let tone = '';
  if (normalized === 'buy' || normalized === 'long') tone = 'long';
  else if (normalized === 'sell' || normalized === 'short') tone = 'short';
  badge.className = `side-badge ${tone}`.trim();
  badge.textContent = formatSideLabel(side);
  return badge;
}

function extractPositionSide(position, sizeField) {
  const field = pickFieldValue(position, ACTIVE_POSITION_ALIASES.side || []);
  if (field.value) return field.value;
  if (sizeField && Number.isFinite(sizeField.numeric)) {
    if (sizeField.numeric > 0) return 'BUY';
    if (sizeField.numeric < 0) return 'SELL';
  }
  return null;
}

function getPositionTimestamp(position) {
  const numericField = pickNumericField(position, ACTIVE_POSITION_TIMESTAMP_NUMERIC_KEYS);
  if (Number.isFinite(numericField.numeric)) {
    return numericField.numeric;
  }
  const isoField = pickFieldValue(position, ACTIVE_POSITION_TIMESTAMP_ISO_KEYS);
  if (isoField.value) {
    const parsed = Date.parse(isoField.value);
    if (Number.isFinite(parsed)) {
      return parsed / 1000;
    }
  }
  return Number.NEGATIVE_INFINITY;
}

function updateActivePositionsView() {
  if (!activePositionsRows) return;
  const positions = Array.isArray(activePositions) ? activePositions : [];
  const sorted = positions.slice().sort((a, b) => getPositionTimestamp(b) - getPositionTimestamp(a));
  activePositionsRows.innerHTML = '';

  const hasRows = sorted.length > 0;

  if (activePositionsModeLabel) {
    activePositionsModeLabel.textContent = 'All modes';
  }
  if (activePositionsEmpty) {
    activePositionsEmpty.textContent = 'No active positions.';
    if (hasRows) {
      activePositionsEmpty.setAttribute('hidden', '');
    } else {
      activePositionsEmpty.removeAttribute('hidden');
    }
  }
  if (activePositionsWrapper) {
    if (hasRows) {
      activePositionsWrapper.removeAttribute('hidden');
    } else {
      activePositionsWrapper.setAttribute('hidden', '');
    }
  }
  if (activePositionsCard) {
    if (hasRows) {
      activePositionsCard.removeAttribute('data-empty');
    } else {
      activePositionsCard.setAttribute('data-empty', 'true');
    }
  }

  if (!hasRows) return;

  sorted.forEach((position) => {
    const row = document.createElement('tr');

    const sizeField = pickNumericField(position, ACTIVE_POSITION_ALIASES.size || []);

    const symbolCell = document.createElement('td');
    const symbolWrapper = document.createElement('div');
    symbolWrapper.className = 'active-positions-symbol-wrapper';
    const symbolLabel = document.createElement('span');
    symbolLabel.className = 'active-positions-symbol';
    const symbolValue = getPositionSymbol(position);
    symbolLabel.textContent = symbolValue;
    symbolWrapper.append(symbolLabel);
    const sideValue = extractPositionSide(position, sizeField);
    const sideBadge = buildSideBadge(sideValue);
    if (sideBadge) {
      symbolWrapper.append(sideBadge);
    }
    symbolCell.append(symbolWrapper);
    row.append(symbolCell);

    const asterUrl = buildAsterPositionUrl(symbolValue);
    if (asterUrl) {
      row.dataset.asterUrl = asterUrl;
      row.classList.add('active-positions-row-link');
      row.setAttribute('tabindex', '0');
      row.setAttribute('role', 'link');
      row.setAttribute('aria-label', `Open ${symbolValue} on Asterdex`);
      row.addEventListener('click', () => openAsterPositionUrl(asterUrl));
      row.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          openAsterPositionUrl(asterUrl);
        }
      });
    }

    const sizeCell = document.createElement('td');
    sizeCell.className = 'numeric active-positions-size';
    const sizeNumeric = Number.isFinite(sizeField.numeric) ? Math.abs(sizeField.numeric) : sizeField.numeric;
    sizeCell.textContent = formatPositionSize(sizeNumeric);
    row.append(sizeCell);

    const entryCell = document.createElement('td');
    entryCell.className = 'numeric';
    const entryField = pickNumericField(position, ACTIVE_POSITION_ALIASES.entry || []);
    entryCell.textContent = formatPriceDisplay(entryField.numeric, {
      minimumFractionDigits: 7,
      maximumFractionDigits: 7,
    });
    row.append(entryCell);

    const markCell = document.createElement('td');
    markCell.className = 'numeric';
    const markField = pickNumericField(position, ACTIVE_POSITION_ALIASES.mark || []);
    markCell.textContent = formatPriceDisplay(markField.numeric, {
      minimumFractionDigits: 7,
      maximumFractionDigits: 7,
    });
    row.append(markCell);

    const pnlCell = document.createElement('td');
    pnlCell.className = 'numeric';
    const pnlField = pickNumericField(position, ACTIVE_POSITION_ALIASES.pnl || []);
    const pnlPercentField = formatPercentField(pickNumericField(position, ACTIVE_POSITION_ALIASES.roe || []));
    let pnlDisplay = '–';
    let pnlTone = null;
    if (Number.isFinite(pnlField.numeric)) {
      pnlTone = pnlField.numeric;
      pnlDisplay = `${formatSignedNumber(pnlField.numeric, 2)} USDT`;
      if (pnlPercentField && pnlPercentField.text) {
        pnlDisplay += ` (${pnlPercentField.text})`;
      }
    } else if (pnlPercentField && pnlPercentField.text) {
      pnlTone = pnlPercentField.numeric;
      pnlDisplay = pnlPercentField.text;
    }
    pnlCell.textContent = pnlDisplay;
    if (Number.isFinite(pnlTone)) {
      if (pnlTone > 0) {
        pnlCell.classList.add('tone-profit');
      } else if (pnlTone < 0) {
        pnlCell.classList.add('tone-loss');
      }
    }
    row.append(pnlCell);

    const tpSlCell = document.createElement('td');
    tpSlCell.className = 'numeric active-positions-brackets';
    const nextTpField = pickFieldValue(position, ACTIVE_POSITION_ALIASES.nextTp || []);
    const stopField = pickFieldValue(position, ACTIVE_POSITION_ALIASES.stop || []);
    const tpDisplay = formatBracketLevel(nextTpField);
    const slDisplay = formatBracketLevel(stopField);

    const buildBracketRow = (labelText, valueText) => {
      const bracketRow = document.createElement('div');
      bracketRow.className = 'active-positions-bracket';

      const label = document.createElement('span');
      label.className = 'active-positions-bracket-label';
      label.textContent = labelText;

      const value = document.createElement('span');
      value.className = 'active-positions-bracket-value';
      value.textContent = valueText;

      bracketRow.append(label, value);
      return bracketRow;
    };

    tpSlCell.append(buildBracketRow('TP', tpDisplay));
    tpSlCell.append(buildBracketRow('SL', slDisplay));
    row.append(tpSlCell);

    activePositionsRows.append(row);
  });
}

function renderActivePositions(openPositions) {
  activePositions = normaliseActivePositions(openPositions);
  updateActivePositionsView();
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
    return { text, label, severity, relevant, parsed, refreshTrades: true };
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
    return { text, label, severity, relevant, parsed, refreshTrades: true };
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
    return { text, label, severity, relevant, parsed, refreshTrades: true };
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

function scheduleTradesRefresh(delay = 0) {
  if (tradesRefreshTimer) {
    clearTimeout(tradesRefreshTimer);
  }
  const wait = Math.max(0, Number(delay) || 0);
  tradesRefreshTimer = setTimeout(() => {
    tradesRefreshTimer = null;
    loadTrades().catch((err) => console.warn('Unable to refresh trades', err));
  }, wait);
}

async function updateStatus() {
  try {
    const res = await fetch('/api/bot/status');
    if (!res.ok) throw new Error();
    const data = await res.json();
    lastBotStatus = data;
    const running = data.running;
    statusIndicator.textContent = running ? 'Running' : 'Stopped';
    statusIndicator.className = `pill ${running ? 'running' : 'stopped'}`;
    statusPid.textContent = data.pid ?? '–';
    statusStarted.textContent = data.started_at ? new Date(data.started_at * 1000).toLocaleString() : '–';
    statusUptime.textContent = running ? formatDuration(data.uptime_s) : '–';
    btnStart.disabled = running;
    btnStop.disabled = !running;
  } catch {
    lastBotStatus = { ...DEFAULT_BOT_STATUS };
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

function createMetric(label, value, tone = 'neutral') {
  const metric = document.createElement('div');
  metric.className = `trade-metric${tone && tone !== 'neutral' ? ` ${tone}` : ''}`;
  const labelEl = document.createElement('span');
  labelEl.className = 'metric-label';
  labelEl.textContent = label;
  const valueEl = document.createElement('span');
  valueEl.className = 'metric-value';
  valueEl.textContent = value ?? '–';
  metric.append(labelEl, valueEl);
  return metric;
}

function formatContextValue(key, raw) {
  const numeric = Number(raw);
  if (Number.isFinite(numeric)) {
    switch (key) {
      case 'atr_pct':
        return `${(numeric * 100).toFixed(2)}%`;
      case 'spread_bps':
        return `${(numeric * 100).toFixed(2)}%`;
      case 'funding':
        return `${(numeric * 100).toFixed(3)}%`;
      case 'qv_score':
        return numeric.toFixed(2);
      case 'slope_htf':
      case 'regime_slope':
        return numeric.toFixed(3);
      case 'adx':
      case 'regime_adx':
      case 'rsi':
        return numeric.toFixed(1);
      case 'trend':
        return numeric > 0 ? 'Bullish' : numeric < 0 ? 'Bearish' : 'Neutral';
      case 'alpha_prob':
      case 'alpha_conf':
        return `${(numeric * 100).toFixed(1)}%`;
      case 'sentinel_event_risk':
      case 'sentinel_hype':
        return `${(numeric * 100).toFixed(1)}%`;
      case 'sentinel_factor':
        return `${numeric.toFixed(2)}×`;
      default:
        return numeric.toFixed(3);
    }
  }
  if (key === 'sentinel_label') {
    return (raw || '').toString().replace(/^[a-z]/, (char) => char.toUpperCase());
  }
  if (raw === undefined || raw === null) return '–';
  return raw.toString();
}

function renderTradeHistory(history) {
  if (!tradeList) return;
  tradeList.innerHTML = '';

  if (!history || history.length === 0) {
    tradeList.style.removeProperty('max-height');
    tradeList.removeAttribute('data-viewport-locked');
    return;
  }

  history.forEach((trade, index) => {
    const pnl = Number(trade.pnl ?? 0);
    const pnlTone = pnl > 0 ? 'profit' : pnl < 0 ? 'loss' : 'neutral';
    const pnlDisplay = `${pnl > 0 ? '+' : ''}${formatNumber(pnl, 2)} USDT`;
    const rValue = Number(trade.pnl_r ?? 0);
    const rTone = rValue > 0 ? 'profit' : rValue < 0 ? 'loss' : 'neutral';
    const rDisplay = `${rValue > 0 ? '+' : ''}${formatNumber(rValue, 2)} R`;
    const durationSeconds = computeDurationSeconds(trade.opened_at_iso, trade.closed_at_iso);

    const details = document.createElement('details');
    details.className = 'trade-item';
    if (trade.side) {
      details.dataset.side = trade.side.toString().toLowerCase();
    }
    if (pnlTone && pnlTone !== 'neutral') {
      details.dataset.pnl = pnlTone;
    }

    const summary = document.createElement('summary');
    summary.className = 'trade-item-summary';

    const heading = document.createElement('div');
    heading.className = 'trade-item-heading';
    const symbol = document.createElement('span');
    symbol.className = 'trade-symbol';
    symbol.textContent = trade.symbol || '–';
    heading.append(symbol);

    if (trade.side) {
      const sideBadge = document.createElement('span');
      const normalized = trade.side.toString().toLowerCase();
      const sideClass = normalized === 'buy' ? 'long' : normalized === 'sell' ? 'short' : '';
      sideBadge.className = `side-badge ${sideClass}`.trim();
      sideBadge.textContent = formatSideLabel(trade.side);
      heading.append(sideBadge);
    }

    const summaryMain = document.createElement('div');
    summaryMain.className = 'trade-summary-main';
    summaryMain.append(heading);

    const summaryMeta = document.createElement('div');
    summaryMeta.className = 'trade-summary-meta';
    const tradeDate = document.createElement('span');
    tradeDate.className = 'trade-date';
    tradeDate.textContent = formatTimestamp(trade.closed_at_iso || trade.opened_at_iso);
    const outcomeLabel = pnlTone === 'profit' ? 'Profit' : pnlTone === 'loss' ? 'Loss' : 'Flat';
    const tradeOutcome = document.createElement('span');
    tradeOutcome.className = `trade-outcome ${pnlTone}`.trim();
    tradeOutcome.textContent = `${outcomeLabel} ${pnlDisplay}`;
    summaryMeta.append(tradeOutcome, tradeDate);

    const priceBlock = document.createElement('div');
    priceBlock.className = 'trade-price-block';
    const entryLine = document.createElement('span');
    entryLine.innerHTML = `<strong>Entry</strong> ${formatNumber(trade.entry, 4)}`;
    const exitLine = document.createElement('span');
    exitLine.innerHTML = `<strong>Exit</strong> ${formatNumber(trade.exit, 4)}`;
    priceBlock.append(entryLine, exitLine);

    const resultBlock = document.createElement('div');
    resultBlock.className = 'trade-result-block';
    const pnlSpan = document.createElement('span');
    pnlSpan.className = `trade-pnl ${pnlTone === 'neutral' ? '' : pnlTone}`.trim();
    pnlSpan.textContent = pnlDisplay;
    const rSpan = document.createElement('span');
    rSpan.className = `trade-r ${rTone === 'neutral' ? '' : rTone}`.trim();
    rSpan.textContent = rDisplay;
    resultBlock.append(pnlSpan, rSpan);

    const timeBlock = document.createElement('div');
    timeBlock.className = 'trade-time-block';
    const timeRange = document.createElement('span');
    timeRange.className = 'trade-time-range';
    timeRange.textContent = `${formatTimeShort(trade.opened_at_iso)} → ${formatTimeShort(trade.closed_at_iso)}`;
    timeBlock.append(timeRange);
    if (Number.isFinite(durationSeconds)) {
      const durationLabel = document.createElement('span');
      durationLabel.className = 'trade-duration';
      durationLabel.textContent = `Duration ${formatDuration(durationSeconds)}`;
      timeBlock.append(durationLabel);
    }

    summary.append(summaryMain, summaryMeta);
    details.append(summary);

    const body = document.createElement('div');
    body.className = 'trade-item-body';

    const overview = document.createElement('div');
    overview.className = 'trade-item-overview';
    overview.append(priceBlock, resultBlock, timeBlock);
    body.append(overview);

    const metricGrid = document.createElement('div');
    metricGrid.className = 'trade-metric-grid';
    const metrics = [
      createMetric('PNL (USDT)', pnlDisplay, pnlTone),
      createMetric('R multiple', rDisplay, rTone),
      createMetric('Size', formatNumber(trade.qty, 4)),
      createMetric('Bandit bucket', trade.bucket ? trade.bucket.toString().toUpperCase() : '–'),
      createMetric('Opened', formatTimestamp(trade.opened_at_iso)),
      createMetric('Closed', formatTimestamp(trade.closed_at_iso)),
      createMetric('Entry', formatNumber(trade.entry, 4)),
      createMetric('Exit', formatNumber(trade.exit, 4)),
    ];
    if (Number.isFinite(durationSeconds)) {
      metrics.splice(6, 0, createMetric('Duration', formatDuration(durationSeconds)));
    }
    metrics.forEach((metric) => metricGrid.append(metric));
    body.append(metricGrid);

    const context = trade.context && typeof trade.context === 'object' ? trade.context : null;
    if (context) {
      const keys = CONTEXT_KEYS.filter((key) => context[key] !== undefined && context[key] !== null);
      if (keys.length > 0) {
        const contextWrapper = document.createElement('div');
        contextWrapper.className = 'trade-context-wrapper';
        const title = document.createElement('h4');
        title.textContent = 'Signal context';
        const dl = document.createElement('dl');
        dl.className = 'trade-context';
        keys.forEach((key) => {
          const dt = document.createElement('dt');
          dt.textContent = CONTEXT_LABELS[key] || key;
          const dd = document.createElement('dd');
          dd.textContent = formatContextValue(key, context[key]);
          dl.append(dt, dd);
        });
        contextWrapper.append(title, dl);
        body.append(contextWrapper);
      }
    }

    const aiMeta = trade.ai && typeof trade.ai === 'object' ? trade.ai : null;
    if (aiMeta) {
      const aiSection = document.createElement('div');
      aiSection.className = 'trade-ai-section';

      const header = document.createElement('div');
      header.className = 'trade-ai-header';
      const title = document.createElement('h4');
      title.textContent = 'AI rationale';
      header.append(title);

      const sentinel = aiMeta.sentinel && typeof aiMeta.sentinel === 'object' ? aiMeta.sentinel : null;
      if (sentinel && sentinel.label) {
        const badge = document.createElement('span');
        badge.className = `sentinel-badge sentinel-${sentinel.label}`;
        badge.textContent = sentinel.label.toString().toUpperCase();
        header.append(badge);
      }
      aiSection.append(header);

      if (aiMeta.explanation) {
        const explanation = document.createElement('p');
        explanation.className = 'trade-ai-explanation';
        explanation.textContent = aiMeta.explanation;
        aiSection.append(explanation);
      }

      const plan = aiMeta.plan && typeof aiMeta.plan === 'object' ? aiMeta.plan : null;
      if (plan) {
        const planList = document.createElement('ul');
        planList.className = 'trade-ai-plan';
        const planEntries = [
          ['Size multiplier', plan.size_multiplier, '×'],
          ['SL multiplier', plan.sl_multiplier, '×'],
          ['TP multiplier', plan.tp_multiplier, '×'],
          ['Leverage', plan.leverage, '×'],
        ];
        planEntries.forEach(([label, raw, suffix]) => {
          if (raw === undefined || raw === null) return;
          const value = Number(raw);
          if (!Number.isFinite(value)) return;
          const li = document.createElement('li');
          li.innerHTML = `<span>${label}</span><strong>${value.toFixed(2)}${suffix || ''}</strong>`;
          planList.append(li);
        });
        if (planList.children.length > 0) {
          aiSection.append(planList);
        }
      }

      if (sentinel) {
        const sentinelMeta = document.createElement('div');
        sentinelMeta.className = 'trade-sentinel-meta';
        const risk = Number(sentinel.event_risk ?? sentinel.meta?.event_risk ?? 0);
        const hype = Number(sentinel.hype_score ?? sentinel.meta?.hype_score ?? 0);
        sentinelMeta.innerHTML = `Event risk ${(risk * 100).toFixed(1)}% · Hype ${(hype * 100).toFixed(1)}% · Size factor ${Number(sentinel.actions?.size_factor ?? 1).toFixed(2)}×`;
        aiSection.append(sentinelMeta);

        if (Array.isArray(sentinel.events) && sentinel.events.length > 0) {
          const eventList = document.createElement('ul');
          eventList.className = 'trade-sentinel-events';
          sentinel.events.slice(0, 3).forEach((event) => {
            if (!event) return;
            const item = document.createElement('li');
            const severity = (event.severity || '').toString().toLowerCase();
            item.className = severity ? `severity-${severity}` : '';
            item.textContent = `${event.headline || 'Event'} (${event.source || 'news'})`;
            eventList.append(item);
          });
          if (eventList.children.length > 0) {
            aiSection.append(eventList);
          }
        }
      }

      if (Array.isArray(aiMeta.warnings) && aiMeta.warnings.length > 0) {
        const warningList = document.createElement('ul');
        warningList.className = 'trade-ai-warnings';
        aiMeta.warnings.forEach((warning) => {
          const li = document.createElement('li');
          li.textContent = warning;
          warningList.append(li);
        });
        aiSection.append(warningList);
      }

      const budget = aiMeta.budget && typeof aiMeta.budget === 'object' ? aiMeta.budget : null;
      if (budget && budget.limit !== undefined) {
        const budgetMeta = document.createElement('div');
        budgetMeta.className = 'trade-ai-budget';
        const limit = Number(budget.limit ?? 0);
        const spent = Number(budget.spent ?? 0);
        if (Number.isFinite(limit) && limit > 0) {
          const remaining = Math.max(0, limit - spent);
          budgetMeta.textContent = `Daily AI spend ${spent.toFixed(2)} / ${limit.toFixed(2)} USD · remaining ${remaining.toFixed(2)} USD`;
        } else {
          budgetMeta.textContent = `Daily AI spend ${spent.toFixed(2)} USD (no hard cap)`;
        }
        aiSection.append(budgetMeta);
      }

      body.append(aiSection);
    }

    const postmortem = trade.postmortem && typeof trade.postmortem === 'object' ? trade.postmortem : null;
    if (postmortem && postmortem.analysis) {
      const postSection = document.createElement('div');
      postSection.className = 'trade-postmortem';
      const heading = document.createElement('h4');
      heading.textContent = 'Post-mortem coach';
      const summary = document.createElement('p');
      summary.textContent = postmortem.analysis;
      postSection.append(heading, summary);
      body.append(postSection);
    }

    details.append(body);
    tradeList.append(details);
  });

  requestTradeListViewportSync();
}

function renderAiBudget(budget) {
  if (!aiBudgetCard || !aiBudgetModeLabel || !aiBudgetMeta || !aiBudgetFill) return;
  lastAiBudget = budget || null;
  aiBudgetCard.classList.toggle('active', aiMode);
  updateAiBudgetModeLabel();
  if (!aiMode) {
    aiBudgetFill.style.width = '0%';
    aiBudgetMeta.textContent = 'AI-Mode disabled.';
    return;
  }
  const limit = Number((budget && budget.limit) ?? 0);
  const spent = Number((budget && budget.spent) ?? 0);
  if (!Number.isFinite(limit) || limit <= 0) {
    aiBudgetFill.style.width = '0%';
    aiBudgetMeta.textContent = `Spent ${spent.toFixed(2)} USD · unlimited budget`;
    aiBudgetCard.classList.add('unlimited');
    return;
  }
  aiBudgetCard.classList.remove('unlimited');
  const pct = clampValue(limit > 0 ? (spent / limit) * 100 : 0, 0, 100);
  aiBudgetFill.style.width = `${pct.toFixed(1)}%`;
  const remaining = Math.max(0, limit - spent);
  aiBudgetMeta.textContent = `Spent ${spent.toFixed(2)} / ${limit.toFixed(2)} USD · remaining ${remaining.toFixed(2)} USD`;
}

function isScrolledToBottom(element, threshold = 24) {
  if (!element) return true;
  return element.scrollHeight - element.clientHeight - element.scrollTop <= threshold;
}

function scrollToBottom(element, behavior = 'smooth') {
  if (!element) return;
  element.scrollTo({ top: element.scrollHeight, behavior });
}

function parsePxValue(value) {
  if (typeof value !== 'string') return 0;
  const parsed = parseFloat(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function syncTradeListViewport() {
  if (!tradeList || typeof window === 'undefined') return;
  const items = Array.from(tradeList.querySelectorAll('.trade-item'));
  if (items.length <= 3) {
    tradeList.style.removeProperty('max-height');
    tradeList.removeAttribute('data-viewport-locked');
    return;
  }

  const summaries = items
    .slice(0, 3)
    .map((item) => item.querySelector('.trade-item-summary'))
    .filter(Boolean);

  if (summaries.length === 0) {
    tradeList.style.removeProperty('max-height');
    tradeList.removeAttribute('data-viewport-locked');
    return;
  }

  let visibleHeight = 0;
  summaries.forEach((summary) => {
    visibleHeight += summary.getBoundingClientRect().height;
  });

  if (visibleHeight <= 0) {
    tradeList.style.removeProperty('max-height');
    tradeList.removeAttribute('data-viewport-locked');
    return;
  }

  const style = window.getComputedStyle(tradeList);
  const gapValue = parsePxValue(style.rowGap || style.gap || '0');
  const paddingTop = parsePxValue(style.paddingTop);
  const paddingBottom = parsePxValue(style.paddingBottom);
  const visibleCount = summaries.length;
  const totalHeight =
    visibleHeight + gapValue * Math.max(0, visibleCount - 1) + paddingTop + paddingBottom + 4;

  tradeList.style.maxHeight = `${Math.round(Math.max(totalHeight, 0))}px`;
  tradeList.setAttribute('data-viewport-locked', 'true');
}

function requestTradeListViewportSync() {
  if (!tradeList) return;

  if (typeof window === 'undefined' || typeof window.requestAnimationFrame !== 'function') {
    syncTradeListViewport();
    return;
  }

  if (tradeViewportSyncHandle !== null) {
    window.cancelAnimationFrame(tradeViewportSyncHandle);
  }

  tradeViewportSyncHandle = window.requestAnimationFrame(() => {
    tradeViewportSyncHandle = null;
    syncTradeListViewport();
  });
}

if (typeof window !== 'undefined' && tradeList) {
  tradeList.addEventListener('toggle', () => requestTradeListViewportSync());
  window.addEventListener('resize', () => requestTradeListViewportSync());
}

function renderAiActivity(feed) {
  if (!aiActivityFeed) return;
  const shouldAutoScroll = isScrolledToBottom(aiActivityFeed);
  aiActivityFeed.innerHTML = '';
  if (!aiMode) {
    const disabled = document.createElement('div');
    disabled.className = 'ai-feed-empty';
    disabled.textContent = 'Enable AI mode to see the activity feed.';
    aiActivityFeed.append(disabled);
    return;
  }
  const items = Array.isArray(feed) ? feed.slice(0, 80) : [];
  if (!items.length) {
    const empty = document.createElement('p');
    empty.className = 'ai-feed-empty';
    empty.textContent = 'Autonomous decisions appear here in real time as new actions occur.';
    aiActivityFeed.append(empty);
    return;
  }
  items.forEach((raw) => {
    const item = raw || {};
    const wrapper = document.createElement('div');
    wrapper.className = 'ai-activity-item';

    const kind = document.createElement('div');
    kind.className = 'ai-activity-kind';
    const kindText = (item.kind || 'info').toString().toUpperCase();
    kind.textContent = kindText;

    const body = document.createElement('div');
    const headline = document.createElement('h4');
    headline.className = 'ai-activity-headline';
    headline.textContent = item.headline || kindText;
    body.append(headline);

    if (item.body) {
      const bodyText = document.createElement('p');
      bodyText.className = 'ai-activity-body';
      bodyText.textContent = item.body;
      body.append(bodyText);
    }

    const meta = document.createElement('div');
    meta.className = 'ai-activity-meta';
    const timeText = formatRelativeTime(item.ts);
    if (timeText) {
      const timeEl = document.createElement('span');
      timeEl.textContent = timeText;
      meta.append(timeEl);
    }
    const summary = summariseDataRecord(item.data);
    if (summary) {
      const dataEl = document.createElement('span');
      dataEl.textContent = summary;
      meta.append(dataEl);
    }
    if (meta.children.length > 0) {
      body.append(meta);
    }

    wrapper.append(kind, body);
    aiActivityFeed.append(wrapper);
  });
  if (shouldAutoScroll) {
    const behavior = aiActivityFeed.scrollHeight > aiActivityFeed.clientHeight ? 'smooth' : 'auto';
    // Ensure the newest activity remains visible when new entries arrive.
    scrollToBottom(aiActivityFeed, behavior);
  }
}

function setAiHintMessage(message) {
  if (!aiHint) return;
  const text = (message || '').toString().trim();
  if (!text) {
    aiHint.textContent = '';
    aiHint.hidden = true;
    return;
  }
  aiHint.hidden = false;
  aiHint.textContent = text;
}

function appendChatMessage(role, message, meta = {}) {
  if (!aiChatMessages) return;
  const empty = aiChatMessages.querySelector('.ai-chat-empty');
  if (empty) empty.remove();
  const msg = document.createElement('div');
  msg.className = `ai-chat-message ${role === 'user' ? 'user' : 'assistant'}`;
  const roleLabel = document.createElement('div');
  roleLabel.className = 'ai-chat-role';
  roleLabel.textContent = role === 'user' ? 'You' : 'Strategy AI';
  const text = document.createElement('p');
  text.className = 'ai-chat-text';
  text.textContent = message;
  msg.append(roleLabel, text);
  const metaParts = [];
  if (meta.model) metaParts.push(meta.model);
  if (meta.source && meta.source !== 'openai') metaParts.push(meta.source);
  if (metaParts.length > 0) {
    const metaEl = document.createElement('div');
    metaEl.className = 'ai-chat-meta';
    metaEl.textContent = metaParts.join(' • ');
    msg.append(metaEl);
  }
  aiChatMessages.append(msg);
  aiChatMessages.scrollTop = aiChatMessages.scrollHeight;
}

function setChatStatus(message) {
  if (aiChatStatus) {
    aiChatStatus.textContent = message || '';
  }
}

function resetChatPlaceholder(text) {
  if (!aiChatMessages) return;
  aiChatMessages.innerHTML = '';
  const empty = document.createElement('div');
  empty.className = 'ai-chat-empty';
  empty.textContent = text;
  aiChatMessages.append(empty);
}

function syncAiChatAvailability() {
  if (!aiChatInput) return;
  if (!aiMode) {
    aiChatInput.value = '';
    aiChatInput.disabled = true;
    if (aiChatSubmit) aiChatSubmit.disabled = true;
    aiChatHistory = [];
    resetChatPlaceholder('Chat is only available in AI-Mode.');
    setChatStatus('AI-Mode disabled.');
  } else {
    aiChatInput.disabled = false;
    if (aiChatSubmit) aiChatSubmit.disabled = false;
    if (
      aiChatMessages &&
      !aiChatMessages.querySelector('.ai-chat-message') &&
      !aiChatMessages.querySelector('.ai-chat-empty')
    ) {
      resetChatPlaceholder('Chat with the Strategy AI to discuss decisions.');
    }
    setChatStatus('');
  }
}

function renderTradeSummary(stats) {
  tradeSummary.innerHTML = '';
  if (!stats) {
    const placeholder = document.createElement('div');
    placeholder.className = 'trade-metric muted';
    placeholder.innerHTML = `<span class="metric-label">Performance</span><span class="metric-value">No data yet</span>`;
    tradeSummary.append(placeholder);
    setAiHintMessage('AI insight will appear once new telemetry is available.');
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
  setAiHintMessage(stats.ai_hint);
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
  if (friendly?.refreshTrades) {
    scheduleTradesRefresh(250);
  }
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

function clampValue(value, min, max) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return min;
  if (Number.isFinite(min) && numeric < min) return min;
  if (Number.isFinite(max) && numeric > max) return max;
  return numeric;
}

function formatRelativeTime(input) {
  if (!input) return '';
  const ts = typeof input === 'number' ? input * 1000 : Date.parse(input);
  if (!Number.isFinite(ts)) return String(input);
  const now = Date.now();
  const diffMs = now - ts;
  if (Number.isNaN(diffMs)) return String(input);
  const diffSec = Math.floor(diffMs / 1000);
  if (diffSec < 5) return 'just now';
  if (diffSec < 60) return `${diffSec}s ago`;
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.floor(diffHr / 24);
  if (diffDay < 7) return `${diffDay}d ago`;
  return new Date(ts).toLocaleString();
}

function summariseDataRecord(record) {
  if (!record || typeof record !== 'object') return '';
  const entries = Object.entries(record)
    .filter(([key, value]) => value !== null && value !== undefined && typeof value !== 'object')
    .slice(0, 4)
    .map(([key, value]) => `${key}: ${value}`);
  return entries.join(' · ');
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function toFixedString(value, digits) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return Number(0).toFixed(digits);
  }
  return numeric.toFixed(digits);
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

function resetQuickConfigButton() {
  quickConfigPristine = true;
  if (btnApplyPreset && !btnApplyPreset.disabled) {
    btnApplyPreset.textContent = 'Apply preset';
  }
}

function markQuickConfigDirty() {
  quickConfigPristine = false;
  if (btnApplyPreset && !btnApplyPreset.disabled) {
    btnApplyPreset.textContent = 'Apply changes';
  }
}

function buildQuickSetupPayload() {
  const presetKey = PRESETS[selectedPreset] ? selectedPreset : 'mid';
  const preset = PRESETS[presetKey];
  const riskMin = riskSlider ? Number(riskSlider.min) : 0.25;
  const riskMax = riskSlider ? Number(riskSlider.max) : 5;
  const leverageMin = leverageSlider ? Number(leverageSlider.min) : 1;
  const leverageMax = leverageSlider ? Number(leverageSlider.max) : 5;
  const rawRisk = riskSlider ? Number(riskSlider.value) : preset.risk;
  const rawLeverage = leverageSlider ? Number(leverageSlider.value) : preset.leverage;
  const safeRisk = clampValue(rawRisk, riskMin, riskMax);
  const safeLeverage = clampValue(rawLeverage, leverageMin, leverageMax);
  const baselineRisk = Number(preset.risk) || 1;
  const ratio = clampValue(baselineRisk > 0 ? safeRisk / baselineRisk : 1, 0.2, 4);

  const payload = {
    ASTER_PRESET_MODE: presetKey,
    ASTER_RISK_PER_TRADE: toFixedString(safeRisk / 100, 4),
    ASTER_LEVERAGE: toFixedString(safeLeverage, 0),
    ASTER_SL_ATR_MULT: toFixedString(preset.slAtr, 2),
    ASTER_TP_ATR_MULT: toFixedString(preset.tpAtr, 2),
    ASTER_TREND_BIAS: preset.trendBias || 'with',
    FAST_TP_ENABLED: 'true',
    FASTTP_MIN_R: toFixedString(preset.fasttp.minR, 2),
    FAST_TP_RET1: toFixedString(preset.fasttp.ret1, 4),
    FAST_TP_RET3: toFixedString(preset.fasttp.ret3, 4),
    FASTTP_SNAP_ATR: toFixedString(preset.fasttp.snapAtr, 2),
    FASTTP_COOLDOWN_S: toFixedString(preset.fasttp.cooldown, 0),
    ASTER_MIN_EDGE_R: toFixedString(preset.edgeMinR, 2),
    ASTER_SIZE_MULT: toFixedString(preset.sizeMult.base * ratio, 2),
    ASTER_SIZE_MULT_S: toFixedString(preset.sizeMult.s * ratio, 2),
    ASTER_SIZE_MULT_M: toFixedString(preset.sizeMult.m * ratio, 2),
    ASTER_SIZE_MULT_L: toFixedString(preset.sizeMult.l * ratio, 2),
    ASTER_EQUITY_FRACTION: toFixedString(preset.equityFraction, 2),
    ASTER_MAX_OPEN_GLOBAL: toFixedString(preset.maxOpenGlobal, 0),
    ASTER_BANDIT_ENABLED: 'true',
    ASTER_ALPHA_ENABLED: 'true',
    ASTER_ALPHA_THRESHOLD: toFixedString(preset.alpha.threshold, 2),
    ASTER_ALPHA_MIN_CONF: toFixedString(preset.alpha.minConf, 2),
    ASTER_ALPHA_PROMOTE_DELTA: toFixedString(preset.alpha.promoteDelta, 2),
    ASTER_ALPHA_REWARD_MARGIN: toFixedString(preset.alpha.rewardMargin, 2),
  };

  return payload;
}

function syncQuickSetupFromEnv(env) {
  if (!env) return;
  const storedPreset = (env.ASTER_PRESET_MODE || '').toString().toLowerCase();
  const presetKey = PRESETS[storedPreset] ? storedPreset : PRESETS[selectedPreset] ? selectedPreset : 'mid';
  applyPreset(presetKey, { silent: true });

  if (riskSlider && env.ASTER_RISK_PER_TRADE) {
    const percent = clampValue(Number(env.ASTER_RISK_PER_TRADE) * 100, Number(riskSlider.min), Number(riskSlider.max));
    riskSlider.value = percent.toFixed(2).replace(/\.00$/, '');
  }
  if (leverageSlider && env.ASTER_LEVERAGE) {
    const lev = clampValue(Number(env.ASTER_LEVERAGE), Number(leverageSlider.min), Number(leverageSlider.max));
    leverageSlider.value = lev.toString();
  }
  updateRiskValue();
  updateLeverageValue();
  resetQuickConfigButton();
}

async function saveQuickSetup() {
  if (!btnApplyPreset) return;
  const payload = buildQuickSetupPayload();
  btnApplyPreset.disabled = true;
  btnApplyPreset.textContent = 'Applying…';
  try {
    const res = await fetch('/api/config', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ env: payload }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || 'Saving quick setup failed');
    }
    currentConfig = await res.json();
    renderConfig(currentConfig.env);
    renderCredentials(currentConfig.env);
    syncQuickSetupFromEnv(currentConfig.env);
    let restarted = false;
    try {
      restarted = await restartBotIfNeeded();
    } catch (restartErr) {
      throw new Error(`Bot restart failed: ${restartErr.message}`);
    }
    btnApplyPreset.textContent = restarted ? 'Restarted ✓' : 'Applied ✓';
    setTimeout(() => {
      if (btnApplyPreset && !btnApplyPreset.disabled) {
        resetQuickConfigButton();
      }
    }, 1800);
  } catch (err) {
    btnApplyPreset.textContent = 'Error';
    alert(err.message);
    setTimeout(() => {
      if (btnApplyPreset && !btnApplyPreset.disabled) {
        btnApplyPreset.textContent = 'Apply changes';
      }
    }, 2000);
  } finally {
    if (btnApplyPreset) {
      btnApplyPreset.disabled = false;
    }
  }
}

function applyPreset(key, options = {}) {
  const preset = PRESETS[key];
  if (!preset) return;
  const { silent = false } = options;
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
  if (!silent) {
    markQuickConfigDirty();
  }
}

function setAiMode(state) {
  aiMode = Boolean(state);
  document.body.classList.toggle('ai-mode', aiMode);
  renderAiBudget(lastAiBudget);
  renderAiActivity(latestTradesSnapshot?.ai_activity);
  syncAiChatAvailability();
}

async function syncModeFromEnv(env) {
  const raw = (env?.ASTER_MODE || '').toString().toLowerCase();
  if (raw === 'ai') {
    await selectMode('ai', { persist: false });
  } else if (raw === 'pro') {
    await selectMode('pro', { persist: false });
  } else {
    await selectMode('standard', { persist: false });
  }
}

function setProMode(state) {
  proMode = Boolean(state);
  document.body.classList.toggle('pro-mode', proMode);
  if (proMode) {
    setEnvCollapsed(true);
  }
}

function applyModeState(mode) {
  if (mode === 'ai') {
    setAiMode(true);
    setProMode(false);
  } else if (mode === 'pro') {
    setAiMode(false);
    setProMode(true);
  } else {
    setAiMode(false);
    setProMode(false);
  }
  updateActivePositionsView();
  syncModeUi();
}

async function persistMode(mode) {
  const payload = { env: { ASTER_MODE: mode } };
  const res = await fetch('/api/config', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || 'Unable to update mode');
  }
  currentConfig = await res.json();
  renderConfig(currentConfig.env);
  renderCredentials(currentConfig.env);
  syncQuickSetupFromEnv(currentConfig.env);
}

async function selectMode(mode, options = {}) {
  const { persist = false } = options;
  const target = (mode || '').toString().toLowerCase();
  const current = getCurrentMode();
  if (!['standard', 'pro', 'ai'].includes(target) || target === current) {
    return;
  }

  const previous = current;
  applyModeState(target);

  if (!persist) {
    return;
  }

  try {
    await persistMode(target);
  } catch (err) {
    alert(err.message);
    applyModeState(previous);
    throw err;
  }
}

async function downloadTradeHistory() {
  try {
    let snapshot = latestTradesSnapshot;
    if (!snapshot) {
      const res = await fetch('/api/trades');
      if (!res.ok) {
        throw new Error('Unable to fetch trade history');
      }
      snapshot = await res.json();
    }

    const exportPayload = {
      generated_at: new Date().toISOString(),
      history: Array.isArray(snapshot?.history) ? snapshot.history : [],
      stats: snapshot?.stats ?? {},
      decision_stats: snapshot?.decision_stats ?? {},
      ai_budget: snapshot?.ai_budget ?? null,
      open: snapshot?.open ?? {},
    };

    const blob = new Blob([JSON.stringify(exportPayload, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    link.href = url;
    link.download = `mraster-trades-${timestamp}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch (err) {
    console.error(err);
    alert(err?.message || 'Unable to download trade history');
  }
}

async function loadTrades() {
  try {
    const res = await fetch('/api/trades');
    if (!res.ok) throw new Error('Unable to load trades');
    const data = await res.json();
    latestTradesSnapshot = data;
    renderTradeHistory(data.history);
    renderTradeSummary(data.stats);
    renderDecisionStats(data.decision_stats);
    renderPnlChart(data.history);
    renderAiBudget(data.ai_budget);
    renderAiActivity(data.ai_activity);
    renderActivePositions(data.open);
  } catch (err) {
    console.warn(err);
  }
}

async function waitForBotState(targetRunning, options = {}) {
  const { timeout = 15000, interval = 500 } = options;
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    await updateStatus();
    if (lastBotStatus.running === targetRunning) {
      return lastBotStatus;
    }
    await sleep(interval);
  }
  throw new Error(`Timed out waiting for bot to ${targetRunning ? 'start' : 'stop'}`);
}

async function restartBotIfNeeded() {
  if (getCurrentMode() !== 'standard') {
    return false;
  }
  await updateStatus();
  if (!lastBotStatus.running) {
    return false;
  }

  if (btnApplyPreset) {
    btnApplyPreset.textContent = 'Restarting…';
  }

  const stopRes = await fetch('/api/bot/stop', { method: 'POST' });
  if (!stopRes.ok) {
    const data = await stopRes.json().catch(() => ({}));
    throw new Error(data.detail || 'Unable to stop bot');
  }
  await waitForBotState(false);

  const startRes = await fetch('/api/bot/start', { method: 'POST' });
  if (!startRes.ok) {
    const data = await startRes.json().catch(() => ({}));
    throw new Error(data.detail || 'Unable to start bot');
  }
  await waitForBotState(true);
  return true;
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
btnSaveAi?.addEventListener('click', saveAiConfig);
btnApplyPreset?.addEventListener('click', saveQuickSetup);
btnToggleEnv?.addEventListener('click', toggleEnvPanel);
btnHeroDownload?.addEventListener('click', () => {
  downloadTradeHistory();
});

modeButtons.forEach((button) => {
  button.addEventListener('click', () => {
    selectMode(button.dataset.modeSelect, { persist: true }).catch(() => {});
  });
  button.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      selectMode(button.dataset.modeSelect, { persist: true }).catch(() => {});
    }
  });
});

syncModeUi();

presetButtons.forEach((button) => {
  button.addEventListener('click', () => applyPreset(button.dataset.preset));
  button.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      applyPreset(button.dataset.preset);
    }
  });
});

riskSlider?.addEventListener('input', () => {
  updateRiskValue();
  markQuickConfigDirty();
});
riskSlider?.addEventListener('change', () => {
  updateRiskValue();
  markQuickConfigDirty();
});
leverageSlider?.addEventListener('input', () => {
  updateLeverageValue();
  markQuickConfigDirty();
});
leverageSlider?.addEventListener('change', () => {
  updateLeverageValue();
  markQuickConfigDirty();
});

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

if (aiChatForm && aiChatInput) {
  aiChatForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (aiChatPending) {
      return;
    }
    if (!aiMode) {
      setChatStatus('Please enable AI-Mode first.');
      return;
    }
    const message = (aiChatInput.value || '').trim();
    if (!message) {
      setChatStatus('Please enter a message.');
      return;
    }
    aiChatPending = true;
    aiChatInput.disabled = true;
    if (aiChatSubmit) aiChatSubmit.disabled = true;
    setChatStatus('Strategy AI is thinking…');
    const historyPayload = aiChatHistory.slice(-6);
    appendChatMessage('user', message);
    aiChatHistory.push({ role: 'user', content: message });
    if (aiChatHistory.length > 12) {
      aiChatHistory = aiChatHistory.slice(-12);
    }
    aiChatInput.value = '';
    try {
      const res = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, history: historyPayload }),
      });
      const text = await res.text();
      let data = {};
      try {
        data = text ? JSON.parse(text) : {};
      } catch (parseErr) {
        data = {};
      }
      if (!res.ok) {
        const detail = data && typeof data === 'object' ? data.detail : null;
        throw new Error(detail || 'Chat request failed');
      }
      const reply = (data.reply || '').toString() || 'No reply received.';
      appendChatMessage('assistant', reply, { model: data.model, source: data.source });
      aiChatHistory.push({ role: 'assistant', content: reply });
      if (aiChatHistory.length > 12) {
        aiChatHistory = aiChatHistory.slice(-12);
      }
      let statusMessage = '';
      if (data.source === 'fallback') {
        statusMessage = 'Reply (fallback)';
      } else if (data.model) {
        statusMessage = `Reply (${data.model})`;
      } else {
        statusMessage = 'Reply received';
      }
      if (data.queued_action && data.queued_action.symbol && data.queued_action.side) {
        const { symbol, side } = data.queued_action;
        const summary = `${symbol.toUpperCase()} ${side.toUpperCase()}`;
        statusMessage = statusMessage ? `${statusMessage} · Manual trade queued (${summary})` : `Manual trade queued (${summary})`;
      }
      setChatStatus(statusMessage);
    } catch (err) {
      appendChatMessage('assistant', err?.message || 'Chat failed.', { source: 'error' });
      setChatStatus('Chat failed.');
    } finally {
      aiChatPending = false;
      if (aiMode) {
        aiChatInput.disabled = false;
        if (aiChatSubmit) aiChatSubmit.disabled = false;
      }
    }
  });
}

syncAiChatAvailability();

document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible') {
    updateStatus();
    loadTrades();
    loadMostTradedCoins();
  }
});

async function init() {
  configureChartDefaults();
  await loadConfig();
  await updateStatus();
  await loadTrades();
  await loadMostTradedCoins();
  connectLogs();
  setInterval(updateStatus, 5000);
  setInterval(loadTrades, 8000);
  if (tickerContainer) {
    if (mostTradedTimer) {
      clearInterval(mostTradedTimer);
    }
    mostTradedTimer = setInterval(loadMostTradedCoins, 60000);
  }
}

init().catch((err) => console.error(err));
