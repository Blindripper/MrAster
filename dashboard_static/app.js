import { derivePositionMarkPrice } from './position_math.js';

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
const nearMissList = document.getElementById('near-miss-list');
const nearMissMeta = document.getElementById('near-miss-meta');
const autoScrollToggles = document.querySelectorAll('input[data-autoscroll]');
const tradeList = document.getElementById('trade-list');
const tradeSummary = document.getElementById('trade-summary');
const completedPositionsPanel = document.getElementById('completed-positions-panel');
const completedPositionsList = document.getElementById('completed-positions-list');
const completedPositionsEmpty = document.getElementById('completed-positions-empty');
const aiRequestList = document.getElementById('ai-request-list');
const aiRequestPrev = document.getElementById('ai-requests-prev');
const aiRequestNext = document.getElementById('ai-requests-next');
const aiRequestModal = document.getElementById('ai-request-modal');
const aiRequestModalClose = document.getElementById('ai-request-modal-close');
const aiRequestModalBody = document.getElementById('ai-request-modal-body');
const aiRequestModalTitle = document.getElementById('ai-request-modal-title');
const aiRequestModalSubtitle = document.getElementById('ai-request-modal-subtitle');
const tradeModal = document.getElementById('trade-modal');
const tradeModalClose = document.getElementById('trade-modal-close');
const tradeModalBody = document.getElementById('trade-modal-body');
const tradeModalTitle = document.getElementById('trade-modal-title');
const tradeModalSubtitle = document.getElementById('trade-modal-subtitle');
const decisionModal = document.getElementById('decision-modal');
const decisionModalClose = document.getElementById('decision-modal-close');
const decisionModalBody = document.getElementById('decision-modal-body');
const decisionModalTitle = document.getElementById('decision-modal-title');
const decisionModalSubtitle = document.getElementById('decision-modal-subtitle');
const aiHint = document.getElementById('ai-hint');
const pnlChartCanvas = document.getElementById('pnl-chart');
const pnlChartWrapper = document.querySelector('.pnl-chart-wrapper');
const pnlEmptyState = document.getElementById('pnl-empty');
const pnlChartModal = document.getElementById('pnl-modal');
const pnlChartModalClose = document.getElementById('pnl-modal-close');
const pnlChartModalCanvas = document.getElementById('pnl-chart-expanded');
const presetButtons = document.querySelectorAll('.preset[data-preset]');
const presetDescription = document.getElementById('preset-description');
const presetFundingDetails = document.getElementById('preset-funding-details');
const presetMlDetails = document.getElementById('preset-ml-details');
const presetLeverageDetails = document.getElementById('preset-leverage-details');
const presetNotionalDetails = document.getElementById('preset-notional-details');
const riskSlider = document.getElementById('risk-slider');
const leverageSlider = document.getElementById('leverage-slider');
const riskValue = document.getElementById('risk-value');
const leverageValue = document.getElementById('leverage-value');
const inputApiKey = document.getElementById('input-api-key');
const inputApiSecret = document.getElementById('input-api-secret');
const inputOpenAiKey = document.getElementById('input-openai-key');
const inputChatOpenAiKey = document.getElementById('input-chat-openai-key');
const inputAiBudget = document.getElementById('input-ai-budget');
const inputAiModel = document.getElementById('input-ai-model');
const inputDefaultNotional = document.getElementById('input-default-notional');
const inputAiDefaultNotional = document.getElementById('input-ai-default-notional');
const decisionSummary = document.getElementById('decision-summary');
const decisionReasons = document.getElementById('decision-reasons');
const decisionReasonsContainer = document.getElementById('decision-reasons-container');
const decisionReasonsToggle = document.getElementById('decision-reasons-toggle');
const decisionReasonsToggleLabel = document.getElementById('decision-reasons-toggle-label');
const decisionReasonsDownload = document.getElementById('decision-reasons-download');
const btnApplyPreset = document.getElementById('btn-apply-preset');
const tickerContainer = document.getElementById('market-ticker');
const tickerTrack = document.getElementById('ticker-track');
const tickerEmpty = document.getElementById('ticker-empty');
const aiBudgetCard = document.getElementById('ai-budget');
const aiBudgetModeLabel = document.getElementById('ai-budget-mode');
const aiBudgetMeta = document.getElementById('ai-budget-meta');
const aiBudgetFill = document.getElementById('ai-budget-fill');
const playbookSummaryContainer = document.getElementById('playbook-summary');
const playbookRequestList = document.getElementById('playbook-request-list');
const playbookModal = document.getElementById('playbook-modal');
const playbookModalClose = document.getElementById('playbook-modal-close');
const playbookModalBody = document.getElementById('playbook-modal-body');
const playbookModalTitle = document.getElementById('playbook-modal-title');
const playbookModalSubtitle = document.getElementById('playbook-modal-subtitle');
const playbookRiskIndicator = document.getElementById('playbook-risk-indicator');
const playbookRiskValue = document.getElementById('playbook-risk-value');
const playbookRiskStatus = document.getElementById('playbook-risk-status');
const playbookRiskFill = document.getElementById('playbook-risk-fill');
const aiChatMessages = document.getElementById('ai-chat-messages');
const aiChatForm = document.getElementById('ai-chat-form');
const aiChatInput = document.getElementById('ai-chat-input');
const aiChatStatus = document.getElementById('ai-chat-status');
const chatKeyIndicator = document.getElementById('chat-key-indicator');
const btnAnalyzeMarket = document.getElementById('btn-analyze-market');
const btnTakeTradeProposals = document.getElementById('btn-take-proposals');
const positionUpdatesCard = document.getElementById('active-positions-notifications-panel');
const activePositionsCard = document.getElementById('active-positions-card');
const activePositionsModeLabel = document.getElementById('active-positions-mode');
const activePositionsWrapper = document.getElementById('active-positions-wrapper');
const activePositionsRows = document.getElementById('active-positions-rows');
const activePositionsNotifications = document.getElementById('active-positions-notifications');
const activePositionsNotificationsEmpty = document.getElementById(
  'active-positions-notifications-empty',
);
const statusCard = document.querySelector('.card.status');
const tradesCard = document.getElementById('trades');
const aiRequestsCard = aiRequestList ? aiRequestList.closest('.card') : null;
const pnlCard = pnlChartWrapper ? pnlChartWrapper.closest('.card') : null;
const playbookCard = playbookSummaryContainer
  ? playbookSummaryContainer.closest('.card')
  : document.getElementById('playbook');
const tradeDataCards = [
  tradesCard,
  aiRequestsCard,
  pnlCard,
  playbookCard,
  activePositionsCard,
  positionUpdatesCard,
].filter(
  Boolean,
);
const automationToggle = document.getElementById('automation-toggle');
const automationIntervalInput = document.getElementById('automation-interval');
const automationCountdown = document.getElementById('automation-countdown');
const automationCountdownLabel = document.getElementById('automation-countdown-label');
const automationCountdownValue = document.getElementById('automation-countdown-value');
const modeButtons = document.querySelectorAll('[data-mode-select]');
const btnHeroDownload = document.getElementById('btn-hero-download');
const btnPostX = document.getElementById('btn-post-x');
const paperModeToggle = document.getElementById('paper-mode-toggle');
const heroTotalTrades = document.getElementById('hero-total-trades');
const heroTotalPnl = document.getElementById('hero-total-pnl');
const heroTotalPnlNote = document.getElementById('hero-total-pnl-note');
const heroTotalWinRate = document.getElementById('hero-total-win-rate');
const pnlTradesWonValue = document.getElementById('pnl-trades-won');
const pnlTradesLostValue = document.getElementById('pnl-trades-lost');
const shareFeedback = document.getElementById('share-feedback');
const MEME_COMPOSER_WINDOW_NAME = 'mraster-meme-composer';
const MEME_COMPOSER_WINDOW_FEATURES =
  'width=920,height=1080,menubar=no,toolbar=no,location=no,status=no,resizable=yes,scrollbars=yes';

const languageButtons = document.querySelectorAll('.language-button[data-lang]');
const i18nElements = document.querySelectorAll('[data-i18n]');
const mobileSectionNav = document.querySelector('.mobile-section-nav');
const mobileSectionNavToggle = document.querySelector('.mobile-section-nav__toggle');
const mobileSectionNavMenu = document.getElementById('mobile-section-nav-menu');
const mobileCollapsibleCards = Array.from(document.querySelectorAll('[data-mobile-collapsible]'));

if (mobileSectionNav && mobileSectionNavToggle && mobileSectionNavMenu) {
  const setMobileNavExpanded = (expanded, { restoreFocus = true } = {}) => {
    const isOpen = mobileSectionNav.classList.contains('is-open');
    if (expanded) {
      if (isOpen) return;
      mobileSectionNav.classList.add('is-open');
      mobileSectionNavToggle.setAttribute('aria-expanded', 'true');
    } else {
      if (!isOpen) return;
      mobileSectionNav.classList.remove('is-open');
      mobileSectionNavToggle.setAttribute('aria-expanded', 'false');
      if (restoreFocus && typeof mobileSectionNavToggle.focus === 'function') {
        mobileSectionNavToggle.focus();
      }
    }
  };

  mobileSectionNavToggle.addEventListener('click', () => {
    const expanded = mobileSectionNav.classList.contains('is-open');
    setMobileNavExpanded(!expanded, { restoreFocus: false });
  });

  mobileSectionNavMenu.addEventListener('click', (event) => {
    const link = event.target.closest('.mobile-section-nav__link');
    if (!link) return;
    setMobileNavExpanded(false, { restoreFocus: false });
  });

  document.addEventListener('click', (event) => {
    if (!mobileSectionNav.classList.contains('is-open')) return;
    if (mobileSectionNav.contains(event.target)) return;
    setMobileNavExpanded(false, { restoreFocus: false });
  });

  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') return;
    if (!mobileSectionNav.classList.contains('is-open')) return;
    setMobileNavExpanded(false);
  });

  const desktopQuery = window.matchMedia('(min-width: 769px)');
  const handleDesktopChange = (event) => {
    if (event.matches) {
      setMobileNavExpanded(false, { restoreFocus: false });
    }
  };

  if (typeof desktopQuery.addEventListener === 'function') {
    desktopQuery.addEventListener('change', handleDesktopChange);
  } else if (typeof desktopQuery.addListener === 'function') {
    desktopQuery.addListener(handleDesktopChange);
  }
}

const mobileCollapsibleQuery = window.matchMedia('(max-width: 768px)');
const mobileCollapsibleRegistry = new WeakMap();
let mobileCollapsibleId = 0;

const getCollapsibleLabel = (card, header) => {
  if (card.getAttribute('aria-label')) return card.getAttribute('aria-label');
  const labelledElement = header.querySelector('[data-mobile-title] h2, [data-mobile-title] h3');
  if (labelledElement && labelledElement.textContent) return labelledElement.textContent.trim();
  const heading = header.querySelector('h2, h3');
  if (heading && heading.textContent) return heading.textContent.trim();
  return header.textContent.trim();
};

const setCardCollapsed = (card, collapsed) => {
  const state = mobileCollapsibleRegistry.get(card);
  if (!state) return;
  const isCollapsed = Boolean(collapsed);
  card.dataset.mobileCollapsed = isCollapsed ? 'true' : 'false';
  state.toggle.setAttribute('aria-expanded', isCollapsed ? 'false' : 'true');
  state.body.hidden = isCollapsed;
};

const attachMobileCollapsible = (card) => {
  if (mobileCollapsibleRegistry.has(card)) return;
  const header = card.querySelector('[data-mobile-collapsible-header]');
  const body = card.querySelector('[data-mobile-collapsible-body]');
  if (!header || !body) return;

  if (!body.id) {
    mobileCollapsibleId += 1;
    const generatedId = `${card.id || 'card'}-mobile-body-${mobileCollapsibleId}`;
    body.id = generatedId;
  }

  const toggle = document.createElement('button');
  toggle.type = 'button';
  toggle.className = 'card-collapse-toggle';
  toggle.setAttribute('aria-controls', body.id);
  toggle.setAttribute('aria-expanded', 'false');
  const labelText = getCollapsibleLabel(card, header) || 'section';
  toggle.setAttribute('aria-label', `${labelText} toggle`);

  const icon = document.createElement('span');
  icon.className = 'card-collapse-toggle__icon';
  toggle.appendChild(icon);

  header.appendChild(toggle);

  const collapseState = { toggle, body, header };
  mobileCollapsibleRegistry.set(card, collapseState);

  toggle.addEventListener('click', () => {
    const isCollapsed = card.dataset.mobileCollapsed !== 'false';
    setCardCollapsed(card, !isCollapsed);
  });

  setCardCollapsed(card, true);
};

const detachMobileCollapsible = (card) => {
  const state = mobileCollapsibleRegistry.get(card);
  if (!state) return;
  state.toggle.remove();
  state.body.hidden = false;
  card.removeAttribute('data-mobile-collapsed');
  mobileCollapsibleRegistry.delete(card);
};

const applyMobileCollapsibles = () => {
  mobileCollapsibleCards.forEach((card) => attachMobileCollapsible(card));
};

const teardownMobileCollapsibles = () => {
  mobileCollapsibleCards.forEach((card) => detachMobileCollapsible(card));
};

if (mobileCollapsibleCards.length) {
  if (mobileCollapsibleQuery.matches) {
    applyMobileCollapsibles();
  }

  const handleMobileCollapsibleChange = (event) => {
    if (event.matches) {
      applyMobileCollapsibles();
    } else {
      teardownMobileCollapsibles();
    }
  };

  if (typeof mobileCollapsibleQuery.addEventListener === 'function') {
    mobileCollapsibleQuery.addEventListener('change', handleMobileCollapsibleChange);
  } else if (typeof mobileCollapsibleQuery.addListener === 'function') {
    mobileCollapsibleQuery.addListener(handleMobileCollapsibleChange);
  }
}

if (btnSaveConfig) btnSaveConfig.dataset.state = 'idle';
if (btnSaveCredentials) btnSaveCredentials.dataset.state = 'idle';
if (btnSaveAi) btnSaveAi.dataset.state = 'idle';
if (btnApplyPreset) btnApplyPreset.dataset.state = 'idle';
if (btnTakeTradeProposals) btnTakeTradeProposals.dataset.state = 'idle';

const DEFAULT_BOT_STATUS = { running: false, pid: null, started_at: null, uptime_s: null };

const DEFAULT_LANGUAGE = 'en';
const SUPPORTED_LANGUAGES = ['en', 'ru', 'zh', 'ko', 'de', 'fr', 'es', 'tr'];
const COMPACT_SKIP_AGGREGATION_WINDOW = 600; // seconds
const MAX_MANAGEMENT_EVENTS = 50;
const POSITION_NOTIFICATIONS_REFRESH_INTERVAL_MS = 2_000;
const COMPLETED_POSITIONS_HISTORY_LIMIT = 12;
const COMPLETED_POSITION_IDENTIFIER_BASE_KEYS = [
  'position_id',
  'positionId',
  'hash',
  'uuid',
  'trade_id',
  'tradeId',
  'id',
  'opened_at',
  'openedAt',
  'closed_at',
  'closedAt',
];

const TRADE_POSITION_IDENTIFIER_KEYS = [
  'position_id',
  'positionId',
  'position_uuid',
  'positionUuid',
  'position_hash',
  'positionHash',
  'position_key',
  'positionKey',
  'strategy_position_id',
  'strategyPositionId',
  'hash',
  'uuid',
  'trade_id',
  'tradeId',
  'id',
  'order_id',
  'orderId',
];

const COMPLETED_POSITION_IDENTIFIER_KEYS = Array.from(
  new Set([...COMPLETED_POSITION_IDENTIFIER_BASE_KEYS, ...TRADE_POSITION_IDENTIFIER_KEYS])
);

const TRADE_POSITION_CONTAINER_KEYS = [
  'extra',
  'context',
  'position',
  'position_info',
  'positionInfo',
  'position_meta',
  'positionMeta',
  'position_context',
  'positionContext',
  'position_snapshot',
  'positionSnapshot',
  'position_details',
  'positionDetails',
];

const TRADE_TIMESTAMP_IDENTIFIER_KEYS = [
  'closed_at',
  'closedAt',
  'closed_ts',
  'closedTs',
  'opened_at',
  'openedAt',
  'ts',
  'timestamp',
  'created_at',
  'createdAt',
  'updated_at',
  'updatedAt',
];
const COMPLETED_POSITIONS_STATS_DEFAULTS = Object.freeze({
  trades: 0,
  realizedPnl: 0,
  totalR: 0,
  wins: 0,
  losses: 0,
  draws: 0,
});
let completedPositionsStatsTotals = { ...COMPLETED_POSITIONS_STATS_DEFAULTS };
let tradeSummaryOverride = null;
const activePositionManagementCache = new Map();

const PLAYBOOK_CARD_TIMESTAMP_KEYS = {
  summary: ['requested_ts', 'requested', 'refreshed_ts', 'refreshed', 'applied_ts', 'applied'],
  process: ['requested_ts', 'requested', 'completed_ts', 'completed', 'failed_ts', 'failed', 'ts_epoch', 'ts'],
  activity: ['ts_epoch', 'ts', 'requested_ts', 'completed_ts', 'completed_ts_epoch'],
};

const TRANSLATIONS = {
  ru: {
    'language.english': 'Английский',
    'language.russian': 'Русский',
    'language.chinese': 'Китайский (мандарин)',
    'language.german': 'Немецкий',
    'language.french': 'Французский',
    'language.spanish': 'Испанский',
    'language.turkish': 'Турецкий',
    'language.korean': 'Корейский',
    'language.switcher': 'Выбор языка',
    'nav.menu': 'Разделы',
    'nav.overview': 'Обзор',
    'nav.trades': 'Сделки',
    'nav.playbook': 'Плейбук',
    'nav.config': 'Настройки',
    'nav.logs': 'Логи',
    'ticker.label': 'Самые торгуемые монеты · Топ 20:',
    'ticker.empty': 'Собираем лидеров рынка…',
    'ticker.noData': 'Сейчас нет рыночных данных.',
    'hero.badge': 'MrAster – автономный торговый комплекс',
    'hero.heading': 'Улавливайте каждое движение рынка с автоматизацией на базе ИИ.',
    'hero.description':
      'Запускайте криптоботов за секунды, транслируйте телеметрию в реальном времени и перенастраивайте стратегии с помощью ИИ-ассистентов, которые сохраняют полную прозрачность исполнения в режимах Standard, Pro и AI.',
    'hero.launch': 'Открыть Aster',
    'hero.download': 'Скачать сделки',
    'hero.share': 'Опубликовать в X',
    'hero.metrics.trades': 'Всего сделок',
    'hero.metrics.pnl': 'Совокупный PNL',
    'hero.metrics.winrate': 'Общий винрейт',
    'hero.metrics.volume': 'Совокупный объем',
    'hero.mode.label': 'Режим',
    'hero.mode.standard': 'Стандарт',
    'hero.mode.pro': 'Профессиональный',
    'hero.mode.ai': 'ИИ',
    'hero.mode.paper': 'Активировать бумажный режим',
    'active.title': 'Активные позиции',
    'active.subtitle': 'Текущее покрытие во всех режимах.',
    'active.mode': 'Все режимы',
    'active.mode.paper': 'Бумажный режим',
    'active.mode.unrealized': 'Совокупный нереализованный PNL',
    'active.notifications.title': 'Обновления по позициям',
    'active.notifications.subtitle': 'Оперативные обновления по текущим открытым позициям.',
    'active.notifications.empty': 'Свежих обновлений по управлению пока нет.',
    'active.empty': 'Нет активных позиций.',
    'active.empty.paper': 'Пока нет бумажных сделок.',
    'active.notifications.closed': 'Позиция закрыта',
    'active.table.symbol': 'Символ',
    'active.table.size': 'Размер',
    'active.table.entry': 'Цена входа',
    'active.table.mark': 'Маркет-прайс',
    'active.table.leverage': 'Плечо',
    'active.table.margin': 'Маржа',
    'active.table.pnl': 'PNL (ROE%)',
    'active.management.fasttp': 'Выход FastTP скорректирован',
    'active.management.breakeven': 'Стоп перенесён в безубыток',
    'active.management.trail': 'Трейлинг-стоп подтянут',
    'active.management.autoHalf': 'Автофиксация прибыли сократила позицию',
    'active.management.scaleHalf': 'Постепенное сокращение позиции выполнено',
    'active.management.timeCut': 'Сокращение по таймеру выполнено',
    'active.management.reduceOnly': 'Отправлен reduce-only ордер',
    'active.management.generic': 'Бот скорректировал позицию',
    'active.management.justNow': 'только что',
    'active.management.oneMinuteAgo': '1 мин назад',
    'active.management.minutesAgo': '{{value}} мин назад',
    'active.management.hoursAgo': '{{value}} ч назад',
    'active.management.daysAgo': '{{value}} д назад',
    'status.title': 'Статус',
    'status.state': 'Состояние',
    'status.pid': 'PID',
    'status.started': 'Запущен',
    'status.uptime': 'Время работы',
    'status.indicator.running': 'Работает',
    'status.indicator.stopped': 'Остановлен',
    'status.indicator.offline': 'Оффлайн',
    'status.aiBudget': 'Бюджет ИИ (день)',
    'status.aiBudget.standard': 'Стандарт',
    'status.aiBudget.pro': 'Про-режим',
    'status.aiBudget.paper': 'Бумажный режим',
    'status.aiBudgetMeta': 'Бюджет не настроен.',
    'status.aiBudgetMeta.disabled': 'AI-режим отключён.',
    'status.aiBudgetMeta.unlimited': 'Расход за день {{spent}} USD · лимит отсутствует',
    'status.aiBudgetMeta.limited': 'Расход за день {{spent}} / {{limit}} USD · остаток {{remaining}} USD',
    'status.aiBudgetMeta.paper': 'Бумажный режим не использует бюджет.',
    'status.tradeDecisions': 'Решения по сделкам',
    'status.decisions.accepted': 'Принято:',
    'status.decisions.skipped': 'Пропущено:',
    'status.decisions.empty': 'Решений по сделкам пока нет.',
    'status.decisions.noneSkipped': 'Пропущенных сделок не зафиксировано.',
    'status.decisions.noneYet': 'Решений по сделкам пока нет.',
    'status.decisions.noReason': 'Для этой причины ещё нет сделок. Загляните после следующего решения.',
    'status.decisions.noReasonShort': 'Для этой причины ещё нет сделок.',
    'status.decisions.showDetails': 'Показать детали',
    'status.decisions.hideDetails': 'Скрыть детали',
    'status.decisions.download': 'Скачать',
    'status.decisions.exportError': 'Не удалось выгрузить пропущенные сделки.',
    'credentials.title': 'Биржевые ключи',
    'credentials.apiKey.label': 'ASTER_API_KEY',
    'credentials.apiKey.placeholder': 'Введите API-ключ',
    'credentials.apiSecret.label': 'ASTER_API_SECRET',
    'credentials.apiSecret.placeholder': 'Введите секретный ключ',
    'credentials.start': 'Старт',
    'credentials.stop': 'Стоп',
    'credentials.save': 'Сохранить',
    'credentials.saving': 'Сохранение…',
    'credentials.saved': 'Сохранено ✓',
    'credentials.error': 'Ошибка',
    'trades.title': 'История сделок',
    'trades.subtitle': 'Последние исполнения и результат одним взглядом.',
    'trades.empty': 'Сделок пока нет.',
    'trades.viewDetails': 'Подробнее',
    'trades.summary.placeholder.label': 'Эффективность',
    'trades.summary.placeholder.value': 'Данных пока нет',
    'trades.summary.hint': 'Подсказка ИИ появится, когда поступит новая телеметрия.',
    'trades.metric.trades': 'Сделки',
    'trades.metric.totalPnl': 'Совокупный PNL',
    'trades.metric.winRate': 'Винрейт',
    'trades.metric.avgR': 'Средний R',
    'trades.postmortem.label': 'Постмортем-наставник',
    'trades.modal.noMetadata': 'Дополнительные данные отсутствуют.',
    'trades.synthetic.badge': 'Реализованный PNL',
    'trades.synthetic.note': 'Синхронизировано с биржевым реализованным PnL — данные входа/выхода недоступны.',
    'trades.synthetic.incomeType': 'Тип дохода',
    'trades.synthetic.info': 'Биржевой источник',
    'trades.completed.title': 'Закрытые позиции',
    'trades.completed.subtitle': 'Документируемые выходы менеджера позиций.',
    'trades.completed.empty': 'Закрытые позиции появятся после следующего выхода бота.',
    'trades.completed.pnl': 'Реализованный PNL',
    'trades.completed.reason': 'Причина выхода',
    'trades.completed.noReason': 'Причина не указана.',
    'pnl.title': 'Динамика PNL',
    'pnl.subtitle': 'Отслеживайте рост реализованного PNL с момента запуска бота.',
    'pnl.tradesWon': 'Победные сделки',
    'pnl.tradesLost': 'Убыточные сделки',
    'pnl.metaLabel': 'Реализованный PNL с запуска бота',
    'pnl.legendLabel': 'Совокупный реализованный PNL',
    'pnl.empty': 'Данных PNL пока нет. Выполните сделки, чтобы заполнить график.',
    'pnl.expandAria': 'Открыть расширенный график эффективности',
    'ai.feed.label': 'Автопоток',
    'ai.feed.title': 'Автономный кокпит стратегии',
    'ai.feed.subtitle':
      'Здесь отображается телеметрия стратегии и автономные действия ИИ. Разговоры перенесены в отдельный чат дашборда.',
    'ai.feed.disabled': 'Включите AI-режим, чтобы увидеть ленту активности.',
    'ai.feed.empty': 'Автономные решения появятся здесь в реальном времени по мере событий.',
    'ai.requests.title': 'Решения ИИ',
    'ai.requests.subtitle': 'Свежие проверки и выводы ИИ по торговым запросам.',
    'ai.requests.empty': 'История решений ИИ появится здесь.',
    'ai.requests.status.pending': 'Ожидает ответа',
    'ai.requests.status.responded': 'Ответ получен',
    'ai.requests.status.accepted': 'Вход одобрен',
    'ai.requests.status.rejected': 'Вход отклонён',
    'ai.requests.status.analysed': 'Анализ завершён',
    'ai.requests.status.decided': 'Решение зафиксировано',
    'ai.feed.reasonLabel': 'Причина',
    'ai.feed.responseLabel': 'Последний ответ',
    'ai.feed.awaitingResponse': 'Ожидаем ответ ИИ…',
    'ai.feed.reason.plan_pending': 'Запрошен план ИИ',
    'ai.feed.reason.plan_timeout': 'План ИИ не ответил вовремя',
    'ai.feed.reason.trend_pending': 'Запрошен тренд-скан ИИ',
    'ai.feed.reason.trend_timeout': 'Тренд-скан не ответил вовремя',
    'common.autoScroll': 'Автопрокрутка',
    'common.close': 'Закрыть',
    'common.save': 'Сохранить',
    'common.saving': 'Сохранение…',
    'common.saved': 'Сохранено ✓',
    'common.error': 'Ошибка',
    'common.expand': 'Развернуть',
    'common.collapse': 'Свернуть',
    'common.analyze': 'Анализ рынка',
    'chat.label': 'Чат дашборда',
    'chat.title': 'Стратегический помощник',
    'chat.subtitle':
      'Общайтесь с трейдинг-ассистентом в рабочем пространстве в стиле ChatGPT. Для консоли нужен отдельный API-ключ.',
    'chat.empty': 'Укажите API-ключ чат-дашборда, чтобы начать разговор.',
    'chat.inputLabel': 'Спросите стратегический ИИ',
    'chat.placeholder': 'Отправьте сообщение своему помощнику…',
    'chat.analyze': 'Анализ рынка',
    'chat.analyzing': 'Анализ…',
    'chat.analyze.hint': 'Добавьте ключ OpenAI в настройках AI, чтобы анализировать рынок.',
    'chat.analyze.pending': 'Анализ рынка выполняется…',
    'chat.automation.toggle': 'Автоматизировать',
    'chat.automation.interval': 'Интервал (минуты)',
    'chat.automation.nextRunLabel': 'Следующий запуск через',
    'chat.automation.running': 'Автоматизация выполняется…',
    'chat.automation.scheduled': 'Автоматический цикл запланирован через {{minutes}} мин.',
    'chat.automation.stopped': 'Автоматизация отключена.',
    'chat.automation.rescheduled': 'Интервал автоматизации обновлён: {{minutes}} мин.',
    'chat.send': 'Отправить',
    'chat.sending': 'Отправка…',
    'chat.status.analyzing': 'Анализ рынка…',
    'chat.status.disabled': 'AI-режим отключён.',
    'chat.status.keyRequired': 'Требуется ключ OpenAI.',
    'chat.status.fallback': 'Анализ рынка (резервный режим).',
    'chat.status.ready': 'Анализ рынка готов.',
    'chat.status.failed': 'Не удалось выполнить анализ рынка.',
    'chat.status.enableAi': 'Сначала включите AI-режим.',
    'chat.status.emptyMessage': 'Введите сообщение.',
    'chat.status.thinking': 'Стратегический ИИ размышляет…',
    'chat.status.error': 'Чат недоступен.',
    'chat.placeholder.disabled': 'Включите AI-режим, чтобы использовать чат дашборда.',
    'chat.placeholder.key': 'Добавьте ключ OpenAI в настройках AI, чтобы начать разговор.',
    'chat.placeholder.prompt': 'Спросите стратегического помощника о своих сделках.',
    'chat.analysis.none': 'Анализ не получен.',
    'chat.reply.none': 'Ответ не получен.',
    'chat.key.ready': 'Ключ чата активен.',
    'chat.role.analysis': 'Рыночный анализ',
    'ai.config.title': 'Настройки AI-режима',
    'ai.config.subtitle': 'Укажите ключи OpenAI и ограничения, чтобы бот мог управлять сделками автономно.',
    'ai.config.save': 'Сохранить',
    'ai.config.saving': 'Сохранение…',
    'ai.config.saved': 'Сохранено ✓',
    'ai.config.error': 'Ошибка',
    'ai.config.access.title': 'Доступ',
    'ai.config.access.openai': 'Ключ OpenAI API',
    'ai.config.access.openaiPlaceholder': 'sk-...',
    'ai.config.access.openaiHint': 'Хранится локально. Нужен для автономного исполнения сделок.',
    'ai.config.access.chat': 'Ключ чат-дашборда',
    'ai.config.access.chatPlaceholder': 'sk-...',
    'ai.config.access.chatHint':
      'Этот отдельный ключ OpenAI питает чат и изолирует торговые запросы. Окно чата отключено, пока ключ не сохранён.',
    'ai.config.budget.title': 'Дневной бюджет',
    'ai.config.budget.label': 'Дневной бюджет (USD)',
    'ai.config.budget.placeholder': '20',
    'ai.config.budget.hint': 'Задайте лимит расходов на ИИ, чтобы автономия оставалась в рамках бюджета.',
    'ai.config.model.title': 'Модель',
    'ai.config.model.label': 'Модель',
    'ai.config.model.group.gpt5': 'Семейство GPT-5',
    'ai.config.model.group.gpt41': 'Семейство GPT-4.1',
    'ai.config.model.group.gpt4o': 'Семейство GPT-4o',
    'ai.config.model.group.reasoning': 'Reasoning-модели',
    'ai.config.model.group.legacy': 'Устаревшие модели',
    'ai.config.model.hint': 'Выберите модель OpenAI, которая будет анализировать рынок в реальном времени.',
    'ai.config.baseline.title': 'Базовый объём',
    'ai.config.baseline.label': 'Базовая сумма на сделку (USDT)',
    'ai.config.baseline.placeholder': '250',
    'ai.config.baseline.hint':
      'Определяет <code>ASTER_DEFAULT_NOTIONAL</code>: минимум USDT, на который ИИ ориентируется перед своими множителями и ограничениями по риску.',
    'ai.config.footer':
      'Когда AI-режим активен, движок стратегии постоянно настраивает размер позиций, плечо, стопы и FastTP, соблюдая дневной бюджет.',
    'quick.title': 'Быстрый запуск стратегии',
    'quick.subtitle': 'Выберите пресет и подстройте риск с плечом под свой комфорт.',
    'quick.apply': 'Применить пресет',
    'quick.applyChanges': 'Применить изменения',
    'quick.applyProgress': 'Применение…',
    'quick.applyRestarting': 'Перезапуск…',
    'quick.applySuccess': 'Применено ✓',
    'quick.applyRestarted': 'Перезапущено ✓',
    'quick.applyError': 'Ошибка',
    'quick.presets.low.title': 'Low',
    'quick.presets.low.subtitle': 'Мало сделок · 30% риск на сделку · 33% капитала',
    'quick.presets.mid.title': 'Mid',
    'quick.presets.mid.subtitle': 'Сбалансированная торговля · 50% риск на сделку · 66% капитала',
    'quick.presets.high.title': 'High',
    'quick.presets.high.subtitle': 'Часто · агрессивно · 100% риск на сделку',
    'quick.presets.att.title': 'ATT',
    'quick.presets.att.subtitle': 'Против тренда',
    'quick.leverage.title': 'Плечо',
    'quick.leverage.placeholder': 'Базовое плечо: –',
    'quick.notional.title': 'Диапазон размера',
    'quick.notional.details': 'Адаптивный размер позиции: {{min}} – {{max}} за сделку.',
    'quick.notional.unlimited': 'баланс счёта',
    'quick.description': 'Выберите профиль, чтобы загрузить рекомендованные параметры риска.',
    'quick.risk.label': 'Риск на сделку',
    'quick.risk.aria': 'Риск на сделку (%)',
    'quick.risk.min': '0.25%',
    'quick.risk.max': '100%',
    'quick.leverage.label': 'Плечо',
    'quick.leverage.aria': 'Множитель плеча',
    'quick.leverage.min': '1×',
    'quick.leverage.max': 'Максимум 25×',
    'quick.baseline.label': 'Базовая ставка на сделку (USDT)',
    'quick.baseline.placeholder': '250',
    'quick.baseline.unit': 'USDT',
    'quick.baseline.hint':
      'Задаёт <code>ASTER_DEFAULT_NOTIONAL</code> — базовый объём, который бот выделяет на каждую сделку до ограничений по риску.',
    'quick.funding.title': 'Фильтры по фандингу',
    'quick.funding.details': 'Контроль фандинга зависит от выбранного пресета.',
    'quick.ml.title': 'ML-политика',
    'quick.ml.empty': 'Детали ML-политики появятся после загрузки пресета.',
    'quick.ml.none': 'Для этого пресета нет описания ML-политики.',
    'env.title': 'Конфигурация окружения',
    'env.expand': 'Развернуть',
    'env.collapse': 'Свернуть',
    'env.save': 'Сохранить',
    'env.saving': 'Сохранение…',
    'env.saved': 'Сохранено ✓',
    'env.error': 'Ошибка',
    'env.subtitle': 'Изменяйте любые параметры <code>ASTER_*</code> без перезапуска сервиса. Изменения сохраняются автоматически.',
    'logs.activity.title': 'Лента активности',
    'logs.activity.subtitle': 'Ключевые сделки, предупреждения и события высокого сигнала.',
    'logs.debug.title': 'Отладочные логи в реальном времени',
    'modals.decision.title': 'Причина торгового решения',
    'modals.trade.title': 'Детали сделки',
    'modals.pnl.title': 'Динамика PNL',
    'modals.pnl.subtitle': 'Отслеживайте рост реализованного PNL с момента запуска бота.',
    'footer.note': 'Создано для Aster — адаптивная торговля с полной прозрачностью. Используйте живые логи и подсказки ИИ, чтобы уверенно улучшать стратегию.',
  },
  de: {
    'language.english': 'Englisch',
    'language.russian': 'Russisch',
    'language.chinese': 'Chinesisch (Mandarin)',
    'language.german': 'Deutsch',
    'language.french': 'Französisch',
    'language.spanish': 'Spanisch',
    'language.turkish': 'Türkisch',
    'language.korean': 'Koreanisch',
    'language.switcher': 'Sprache wählen',
    'nav.menu': 'Bereiche',
    'nav.overview': 'Übersicht',
    'nav.trades': 'Trades',
    'nav.playbook': 'Playbook',
    'nav.config': 'Konfiguration',
    'nav.logs': 'Protokolle',
    'ticker.label': 'Meistgehandelte Coins · Top 20:',
    'ticker.empty': 'Marktführer werden geladen…',
    'ticker.noData': 'Zurzeit liegen keine Marktdaten vor.',
    'hero.badge': 'MrAster – Autonomes Handelssystem',
    'hero.heading': 'Nutze jeden Marktimpuls mit KI-gestützter Automatisierung.',
    'hero.description': 'Starte Kryptobots in Sekunden, streame Live-Telemetrie und kalibriere Strategien neu – mit KI-Copiloten, die in den Modi Standard, Pro und AI für volle Transparenz sorgen.',
    'hero.launch': 'Aster öffnen',
    'hero.download': 'Trades herunterladen',
    'hero.share': 'Auf X teilen',
    'hero.metrics.trades': 'Anzahl Trades',
    'hero.metrics.pnl': 'Gesamter PNL',
    'hero.metrics.winrate': 'Gesamte Trefferquote',
    'hero.metrics.volume': 'Gesamtes Volumen',
    'hero.mode.label': 'Modus',
    'hero.mode.standard': 'Standard',
    'hero.mode.pro': 'Profi',
    'hero.mode.ai': 'KI',
    'hero.mode.paper': 'Papiermodus aktivieren',
    'active.title': 'Aktive Positionen',
    'active.subtitle': 'Aktuelle Exponierung in allen Modi.',
    'active.mode': 'Alle Modi',
    'active.mode.paper': 'Papiermodus',
    'active.mode.unrealized': 'Gesamter unrealisierter PNL',
    'active.notifications.title': 'Positions-Updates',
    'active.notifications.subtitle': 'Live-Updates zu den aktuell offenen Positionen.',
    'active.notifications.empty': 'Noch keine aktuellen Verwaltungsereignisse.',
    'active.empty': 'Keine aktiven Positionen.',
    'active.empty.paper': 'Noch keine Papier-Trades.',
    'active.notifications.closed': 'Position geschlossen',
    'active.table.symbol': 'Symbol',
    'active.table.size': 'Positionsgröße',
    'active.table.entry': 'Einstiegspreis',
    'active.table.mark': 'Markpreis',
    'active.table.leverage': 'Hebel',
    'active.table.margin': 'Margin',
    'active.table.pnl': 'PNL (ROE%)',
    'active.management.fasttp': 'FastTP-Ausstieg angepasst',
    'active.management.breakeven': 'Stop auf Break-even gesetzt',
    'active.management.trail': 'Trailing-Stop nachgezogen',
    'active.management.autoHalf': 'Automatischer Teilverkauf ausgelöst',
    'active.management.scaleHalf': 'Positionsabbau eingeleitet',
    'active.management.timeCut': 'Zeitbasierter Exit ausgeführt',
    'active.management.reduceOnly': 'Reduce-Only-Order gesendet',
    'active.management.generic': 'Bot hat die Position angepasst',
    'active.management.justNow': 'gerade eben',
    'active.management.oneMinuteAgo': 'vor 1 Min.',
    'active.management.minutesAgo': 'vor {{value}} Min.',
    'active.management.hoursAgo': 'vor {{value}} Std.',
    'active.management.daysAgo': 'vor {{value}} Tg.',
    'status.title': 'Status',
    'status.state': 'Zustand',
    'status.pid': 'PID',
    'status.started': 'Gestartet',
    'status.uptime': 'Laufzeit',
    'status.indicator.running': 'Läuft',
    'status.indicator.stopped': 'Gestoppt',
    'status.indicator.offline': 'Offline',
    'status.aiBudget': 'KI-Budget (täglich)',
    'status.aiBudget.standard': 'Standard',
    'status.aiBudget.pro': 'Pro-Modus',
    'status.aiBudget.paper': 'Papiermodus',
    'status.aiBudgetMeta': 'Budget nicht konfiguriert.',
    'status.aiBudgetMeta.disabled': 'KI-Modus ist deaktiviert.',
    'status.aiBudgetMeta.unlimited': 'Heutiger Verbrauch {{spent}} USD · kein Limit',
    'status.aiBudgetMeta.limited': 'Heutiger Verbrauch {{spent}} / {{limit}} USD · verbleibend {{remaining}} USD',
    'status.aiBudgetMeta.paper': 'Im Papiermodus wird kein Budget verwendet.',
    'status.tradeDecisions': 'Handelsentscheidungen',
    'status.decisions.accepted': 'Ausgeführt:',
    'status.decisions.skipped': 'Übersprungen:',
    'status.decisions.empty': 'Noch keine Handelsentscheidungen.',
    'status.decisions.noneSkipped': 'Es wurden keine Trades übersprungen.',
    'status.decisions.noneYet': 'Noch keine Handelsentscheidungen.',
    'status.decisions.noReason': 'Für diesen Grund liegen noch keine Trades vor. Schau nach der nächsten Entscheidung wieder vorbei.',
    'status.decisions.noReasonShort': 'Für diesen Grund liegen noch keine Trades vor.',
    'status.decisions.showDetails': 'Details anzeigen',
    'status.decisions.hideDetails': 'Details verbergen',
    'status.decisions.download': 'Download',
    'status.decisions.exportError': 'Download der übersprungenen Trades fehlgeschlagen.',
    'credentials.title': 'Börsen-Zugangsdaten',
    'credentials.apiKey.label': 'ASTER_API_KEY',
    'credentials.apiKey.placeholder': 'API-Key eingeben',
    'credentials.apiSecret.label': 'ASTER_API_SECRET',
    'credentials.apiSecret.placeholder': 'Geheimschlüssel eingeben',
    'credentials.start': 'Start',
    'credentials.stop': 'Stopp',
    'credentials.save': 'Speichern',
    'credentials.saving': 'Speichere…',
    'credentials.saved': 'Gespeichert ✓',
    'credentials.error': 'Fehler',
    'trades.title': 'Trade-Historie',
    'trades.subtitle': 'Neueste Ausführungen und Ergebnis auf einen Blick.',
    'trades.empty': 'Noch keine Trades.',
    'trades.viewDetails': 'Details anzeigen',
    'trades.summary.placeholder.label': 'Performance',
    'trades.summary.placeholder.value': 'Noch keine Daten',
    'trades.summary.hint': 'Ein KI-Hinweis erscheint hier, sobald neue Telemetrie vorliegt.',
    'trades.metric.trades': 'Trades',
    'trades.metric.totalPnl': 'Gesamt-PNL',
    'trades.metric.winRate': 'Trefferquote',
    'trades.metric.avgR': 'Ø R',
    'trades.postmortem.label': 'Post-Mortem-Coach',
    'trades.modal.noMetadata': 'Keine zusätzlichen Daten vorhanden.',
    'trades.synthetic.badge': 'Realisierter PnL',
    'trades.synthetic.note': 'Aus dem Börsen-PnL übernommen – Ein-/Ausstiegskurse fehlen.',
    'trades.synthetic.incomeType': 'Ertragsart',
    'trades.synthetic.info': 'Börsenhinweis',
    'trades.completed.title': 'Abgeschlossene Positionen',
    'trades.completed.subtitle': 'Dokumentierte Exits des Positionsmanagers.',
    'trades.completed.empty': 'Geschlossene Positionen erscheinen nach dem nächsten Exit.',
    'trades.completed.pnl': 'Realisierter PNL',
    'trades.completed.reason': 'Exit-Grund',
    'trades.completed.noReason': 'Kein Grund protokolliert.',
    'pnl.title': 'PNL-Verlauf',
    'pnl.subtitle': 'Visualisiere den kumulierten PNL seit dem Start des Bots.',
    'pnl.tradesWon': 'Gewonnene Trades',
    'pnl.tradesLost': 'Verlorene Trades',
    'pnl.metaLabel': 'Realisierter PNL seit Bot-Start',
    'pnl.legendLabel': 'Kumulierter realisierter PNL',
    'pnl.empty': 'Noch keine PNL-Daten. Führe Trades aus, um das Diagramm zu füllen.',
    'pnl.expandAria': 'Erweiterten Performance-Chart öffnen',
    'ai.feed.label': 'Autopilot',
    'ai.feed.title': 'Autonomes Strategie-Cockpit',
    'ai.feed.subtitle':
      'Hier erscheinen Strategie-Telemetrie und autonome KI-Aktionen. Unterhaltungen findest du im separaten Dashboard-Chat.',
    'ai.feed.disabled': 'Aktiviere den KI-Modus, um den Aktivitätsfeed zu sehen.',
    'ai.feed.empty': 'Autonome Entscheidungen werden hier in Echtzeit angezeigt, sobald Ereignisse eintreten.',
    'ai.requests.title': 'KI-Entscheidungen',
    'ai.requests.subtitle': 'Neueste KI-Prüfungen und Ergebnisse zu Handelssignalen.',
    'ai.requests.empty': 'Noch keine protokollierten KI-Entscheidungen.',
    'ai.requests.status.pending': 'Wartet auf Antwort',
    'ai.requests.status.responded': 'Antwort eingetroffen',
    'ai.requests.status.accepted': 'Einstieg bestätigt',
    'ai.requests.status.rejected': 'Einstieg abgelehnt',
    'ai.requests.status.analysed': 'Analyse abgeschlossen',
    'ai.requests.status.decided': 'Entscheidung vorliegend',
    'ai.feed.reasonLabel': 'Grund',
    'ai.feed.responseLabel': 'Letzte Antwort',
    'ai.feed.awaitingResponse': 'KI-Antwort steht noch aus…',
    'ai.feed.reason.plan_pending': 'KI-Plan angefragt',
    'ai.feed.reason.plan_timeout': 'KI-Plan hat nicht rechtzeitig geantwortet',
    'ai.feed.reason.trend_pending': 'Trend-Scan angefragt',
    'ai.feed.reason.trend_timeout': 'Trend-Scan hat nicht rechtzeitig geantwortet',
    'common.autoScroll': 'Auto-Scroll',
    'common.close': 'Schließen',
    'common.save': 'Speichern',
    'common.saving': 'Speichere…',
    'common.saved': 'Gespeichert ✓',
    'common.error': 'Fehler',
    'common.expand': 'Erweitern',
    'common.collapse': 'Einklappen',
    'common.analyze': 'Markt analysieren',
    'chat.label': 'Dashboard-Chat',
    'chat.title': 'Strategie-Assistent',
    'chat.subtitle':
      'Unterhalte dich mit dem Trading-Assistenten im ChatGPT-ähnlichen Arbeitsbereich. Für die Konsole ist ein eigener API-Schlüssel nötig.',
    'chat.empty': 'Bitte hinterlege einen API-Schlüssel für den Dashboard-Chat, um zu starten.',
    'chat.inputLabel': 'Frag die Strategie-KI',
    'chat.placeholder': 'Sende deinem Assistenten eine Nachricht…',
    'chat.analyze': 'Markt analysieren',
    'chat.analyzing': 'Analysiere…',
    'chat.analyze.hint': 'Füge in den KI-Einstellungen einen OpenAI-Schlüssel hinzu, um die Marktanalyse zu aktivieren.',
    'chat.analyze.pending': 'Marktanalyse läuft…',
    'chat.automation.toggle': 'Automatisieren',
    'chat.automation.interval': 'Intervall (Minuten)',
    'chat.automation.nextRunLabel': 'Nächster Start in',
    'chat.automation.running': 'Automatisierung läuft…',
    'chat.automation.scheduled': 'Automatischer Durchlauf in {{minutes}} Minute(n) geplant.',
    'chat.automation.stopped': 'Automatisierung deaktiviert.',
    'chat.automation.rescheduled': 'Automatisierungsintervall auf {{minutes}} Minute(n) aktualisiert.',
    'chat.send': 'Senden',
    'chat.sending': 'Sende…',
    'chat.status.analyzing': 'Marktanalyse läuft…',
    'chat.status.disabled': 'KI-Modus ist deaktiviert.',
    'chat.status.keyRequired': 'OpenAI-Schlüssel erforderlich.',
    'chat.status.fallback': 'Marktanalyse (Fallback-Modus).',
    'chat.status.ready': 'Marktanalyse bereit.',
    'chat.status.failed': 'Marktanalyse fehlgeschlagen.',
    'chat.status.enableAi': 'Bitte aktiviere zuerst den KI-Modus.',
    'chat.status.emptyMessage': 'Bitte gib eine Nachricht ein.',
    'chat.status.thinking': 'Die Strategie-KI denkt nach…',
    'chat.status.error': 'Chat nicht verfügbar.',
    'chat.placeholder.disabled': 'Aktiviere den KI-Modus, um den Dashboard-Chat zu nutzen.',
    'chat.placeholder.key': 'Füge in den KI-Einstellungen einen OpenAI-Schlüssel hinzu, um loszulegen.',
    'chat.placeholder.prompt': 'Frag den Strategie-Assistenten nach deinen Trades.',
    'chat.analysis.none': 'Keine Analyse empfangen.',
    'chat.reply.none': 'Keine Antwort erhalten.',
    'chat.key.ready': 'Chat-Schlüssel ist aktiv.',
    'chat.role.analysis': 'Marktanalyse',
    'ai.config.title': 'KI-Modus konfigurieren',
    'ai.config.subtitle': 'Hinterlege OpenAI-Schlüssel und Limits, damit der Bot Trades autonom steuert.',
    'ai.config.save': 'Speichern',
    'ai.config.saving': 'Speichere…',
    'ai.config.saved': 'Gespeichert ✓',
    'ai.config.error': 'Fehler',
    'ai.config.access.title': 'Zugriff',
    'ai.config.access.openai': 'OpenAI API-Schlüssel',
    'ai.config.access.openaiPlaceholder': 'sk-...',
    'ai.config.access.openaiHint': 'Wird nur lokal gespeichert. Ermöglicht die autonome Ausführung.',
    'ai.config.access.chat': 'Dashboard-Chat-Schlüssel',
    'ai.config.access.chatPlaceholder': 'sk-...',
    'ai.config.access.chatHint':
      'Dieser separate OpenAI-Schlüssel dient dem Chat und ist von den Trading-Anfragen isoliert. Vor dem Speichern bleibt das Chat-Fenster deaktiviert.',
    'ai.config.budget.title': 'Tagesbudget',
    'ai.config.budget.label': 'Tagesbudget (USD)',
    'ai.config.budget.placeholder': '20',
    'ai.config.budget.hint': 'Setze ein Ausgabenlimit für die KI, damit die Autonomie im Budget bleibt.',
    'ai.config.model.title': 'Modell',
    'ai.config.model.label': 'Modell',
    'ai.config.model.group.gpt5': 'GPT-5-Serie',
    'ai.config.model.group.gpt41': 'GPT-4.1-Serie',
    'ai.config.model.group.gpt4o': 'GPT-4o-Serie',
    'ai.config.model.group.reasoning': 'Reasoning-Modelle',
    'ai.config.model.group.legacy': 'Legacy-Modelle',
    'ai.config.model.hint': 'Wähle das OpenAI-Modell für deine Marktanalysen in Echtzeit.',
    'ai.config.baseline.title': 'Basisposition',
    'ai.config.baseline.label': 'Basisposition pro Trade (USDT)',
    'ai.config.baseline.placeholder': '250',
    'ai.config.baseline.hint':
      'Entspricht <code>ASTER_DEFAULT_NOTIONAL</code>: Mindest-USDT-Betrag, auf den sich die KI vor Risikomultiplikatoren bezieht.',
    'ai.config.footer':
      'Bei aktiviertem KI-Modus passt die Strategie-Engine Positionierung, Hebel, Stop-Loss und FastTP kontinuierlich an – immer im Rahmen des Tagesbudgets.',
    'quick.title': 'Schnellstart der Strategie',
    'quick.subtitle': 'Wähle ein Preset und stimme Risiko sowie Hebel auf deine Präferenzen ab.',
    'quick.apply': 'Preset anwenden',
    'quick.applyChanges': 'Änderungen übernehmen',
    'quick.applyProgress': 'Wird angewendet…',
    'quick.applyRestarting': 'Starte neu…',
    'quick.applySuccess': 'Angewendet ✓',
    'quick.applyRestarted': 'Neu gestartet ✓',
    'quick.applyError': 'Fehler',
    'quick.presets.low.title': 'Low',
    'quick.presets.low.subtitle': 'Niedrige Frequenz · 30 % Risiko pro Trade · 33 % Kapitaleinsatz',
    'quick.presets.mid.title': 'Mid',
    'quick.presets.mid.subtitle': 'Ausgewogenes Trading · 50 % Risiko pro Trade · 66 % Kapitaleinsatz',
    'quick.presets.high.title': 'High',
    'quick.presets.high.subtitle': 'Hohe Frequenz · Aggressiv · 100 % Risiko pro Trade',
    'quick.presets.att.title': 'ATT',
    'quick.presets.att.subtitle': 'Counter-Trend-Setup',
    'quick.leverage.title': 'Hebel',
    'quick.leverage.placeholder': 'Basishebel: –',
    'quick.notional.title': 'Größenbereich',
    'quick.notional.details': 'Adaptive Positionsgröße: {{min}} – {{max}} je Trade.',
    'quick.notional.unlimited': 'Kontoeigenkapital',
    'quick.description': 'Wähle eine Konfiguration, um empfohlene Risiko-Parameter zu laden.',
    'quick.risk.label': 'Risiko pro Trade',
    'quick.risk.aria': 'Risiko pro Trade (%)',
    'quick.risk.min': '0,25%',
    'quick.risk.max': '100%',
    'quick.leverage.label': 'Hebel',
    'quick.leverage.aria': 'Hebel-Multiplikator',
    'quick.leverage.min': '1×',
    'quick.leverage.max': 'Bis zu 25×',
    'quick.baseline.label': 'Basis-Einsatz pro Trade (USDT)',
    'quick.baseline.placeholder': '250',
    'quick.baseline.unit': 'USDT',
    'quick.baseline.hint':
      'Setzt <code>ASTER_DEFAULT_NOTIONAL</code> – die Basisposition, die der Bot vor Risikoregeln für jeden Trade reserviert.',
    'quick.funding.title': 'Funding-Filter',
    'quick.funding.details': 'Die Funding-Filter richten sich nach dem gewählten Preset.',
    'quick.ml.title': 'ML-Strategie',
    'quick.ml.empty': 'Lade ein Preset, um Details zur ML-Strategie zu sehen.',
    'quick.ml.none': 'Dieses Preset enthält keine ML-Strategie.',
    'env.title': 'Umgebungskonfiguration',
    'env.expand': 'Erweitern',
    'env.collapse': 'Einklappen',
    'env.save': 'Speichern',
    'env.saving': 'Speichere…',
    'env.saved': 'Gespeichert ✓',
    'env.error': 'Fehler',
    'env.subtitle':
      'Ändere beliebige <code>ASTER_*</code>-Parameter ohne Neustart des Dienstes. Anpassungen werden automatisch gespeichert.',
    'logs.activity.title': 'Aktivitätsfeed',
    'logs.activity.subtitle': 'Wichtige Trades, Warnungen und Hochsignal-Ereignisse.',
    'logs.debug.title': 'Debug-Logs in Echtzeit',
    'modals.decision.title': 'Grund für die Handelsentscheidung',
    'modals.trade.title': 'Trade-Details',
    'modals.pnl.title': 'PNL-Verlauf',
    'modals.pnl.subtitle': 'Visualisiere den kumulierten PNL seit dem Start des Bots.',
    'footer.note':
      'Entwickelt für Aster – adaptives Trading mit voller Transparenz. Nutze Live-Logs und KI-Hinweise, um deine Strategie mit Vertrauen zu optimieren.',
  },
  ko: {
    'language.english': '영어',
    'language.russian': '러시아어',
    'language.chinese': '중국어(만다린)',
    'language.german': '독일어',
    'language.french': '프랑스어',
    'language.spanish': '스페인어',
    'language.turkish': '터키어',
    'language.korean': '한국어',
    'language.switcher': '언어 선택',
    'nav.menu': '섹션',
    'nav.overview': '개요',
    'nav.trades': '거래',
    'nav.playbook': '플레이북',
    'nav.config': '설정',
    'nav.logs': '로그',
    'ticker.label': '가장 많이 거래되는 코인 · 상위 20개:',
    'ticker.empty': '시장 선도주를 불러오는 중…',
    'ticker.noData': '현재 이용 가능한 시장 데이터가 없습니다.',
    'hero.badge': 'MrAster – 자율형 트레이딩 스위트',
    'hero.heading': 'AI가 다듬은 자동화로 모든 시장 움직임을 포착하세요.',
    'hero.description':
      '몇 초 만에 크립토 봇을 배포하고, 실시간 텔레메트리를 스트리밍하며, Standard·Pro·AI 모드 전반에서 모든 실행을 투명하게 유지하는 AI 코파일럿과 함께 전략을 재조정하세요.',
    'hero.launch': 'Aster 실행하기',
    'hero.download': '거래 내보내기',
    'hero.share': 'X에 공유',
    'hero.metrics.trades': '총 거래 수',
    'hero.metrics.pnl': '누적 PNL',
    'hero.metrics.winrate': '전체 승률',
    'hero.metrics.volume': '총 거래량',
    'hero.mode.label': '모드',
    'hero.mode.standard': '스탠다드',
    'hero.mode.pro': '프로',
    'hero.mode.ai': 'AI',
    'hero.mode.paper': '페이퍼 모드 활성화',
    'active.title': '활성 포지션',
    'active.subtitle': '모든 모드에서의 현재 익스포저.',
    'active.mode': '전체 모드',
    'active.mode.paper': '페이퍼 모드',
    'active.mode.unrealized': '총 미실현 PNL',
    'active.notifications.title': '포지션 업데이트',
    'active.notifications.subtitle': '현재 오픈된 포지션을 위한 실시간 업데이트.',
    'active.notifications.empty': '최근 관리 이벤트가 아직 없습니다.',
    'active.empty': '활성 포지션이 없습니다.',
    'active.empty.paper': '아직 페이퍼 거래가 없습니다.',
    'active.notifications.closed': '포지션이 종료되었습니다',
    'active.table.symbol': '심볼',
    'active.table.size': '포지션 규모',
    'active.table.entry': '진입가',
    'active.table.mark': '마크 가격',
    'active.table.leverage': '레버리지',
    'active.table.margin': '증거금',
    'active.table.pnl': 'PNL (ROE%)',
    'active.management.fasttp': 'FastTP 청산이 조정되었습니다',
    'active.management.breakeven': '스톱이 본전으로 이동했습니다',
    'active.management.trail': '트레일링 스톱이 조여졌습니다',
    'active.management.autoHalf': '자동 익절이 포지션을 축소했습니다',
    'active.management.scaleHalf': '완만한 분할 청산이 실행되었습니다',
    'active.management.timeCut': '시간 기반 축소가 실행되었습니다',
    'active.management.reduceOnly': 'Reduce-only 주문이 전송되었습니다',
    'active.management.generic': '봇이 이 포지션을 조정했습니다',
    'active.management.justNow': '방금 전',
    'active.management.oneMinuteAgo': '1분 전',
    'active.management.minutesAgo': '{{value}}분 전',
    'active.management.hoursAgo': '{{value}}시간 전',
    'active.management.daysAgo': '{{value}}일 전',
    'status.title': '상태',
    'status.state': '상태',
    'status.pid': 'PID',
    'status.started': '시작 시각',
    'status.uptime': '가동 시간',
    'status.indicator.running': '실행 중',
    'status.indicator.stopped': '중지됨',
    'status.indicator.offline': '오프라인',
    'status.aiBudget': 'AI 예산(일일)',
    'status.aiBudget.standard': '스탠다드',
    'status.aiBudget.pro': '프로 모드',
    'status.aiBudget.paper': '페이퍼 모드',
    'status.aiBudgetMeta': '예산이 아직 설정되지 않았습니다.',
    'status.aiBudgetMeta.disabled': 'AI 모드가 비활성화되었습니다.',
    'status.aiBudgetMeta.unlimited': '금일 사용액 {{spent}} USD · 제한 없음',
    'status.aiBudgetMeta.limited': '금일 사용액 {{spent}} / {{limit}} USD · 잔여 {{remaining}} USD',
    'status.aiBudgetMeta.paper': '페이퍼 모드는 예산을 사용하지 않습니다.',
    'status.tradeDecisions': '거래 결정',
    'status.decisions.accepted': '체결:',
    'status.decisions.skipped': '건너뜀:',
    'status.decisions.empty': '아직 거래 결정이 없습니다.',
    'status.decisions.noneSkipped': '건너뛴 거래가 없습니다.',
    'status.decisions.noneYet': '아직 거래 결정이 없습니다.',
    'status.decisions.noReason': '이 사유로 기록된 거래가 아직 없습니다. 다음 결정 이후에 다시 확인하세요.',
    'status.decisions.noReasonShort': '이 사유로 기록된 거래가 아직 없습니다.',
    'status.decisions.showDetails': '상세 보기',
    'status.decisions.hideDetails': '상세 접기',
    'status.decisions.download': '다운로드',
    'status.decisions.exportError': '건너뛴 트레이드를 지금은 다운로드할 수 없습니다.',
    'credentials.title': '거래소 자격 증명',
    'credentials.apiKey.label': 'ASTER_API_KEY',
    'credentials.apiKey.placeholder': 'API 키 입력',
    'credentials.apiSecret.label': 'ASTER_API_SECRET',
    'credentials.apiSecret.placeholder': '시크릿 키 입력',
    'credentials.start': '시작',
    'credentials.stop': '중지',
    'credentials.save': '저장',
    'credentials.saving': '저장 중…',
    'credentials.saved': '저장 완료 ✓',
    'credentials.error': '오류',
    'trades.title': '거래 내역',
    'trades.subtitle': '최신 체결과 결과를 한눈에 확인하세요.',
    'trades.empty': '아직 거래가 없습니다.',
    'trades.viewDetails': '세부 정보 보기',
    'trades.summary.placeholder.label': '성과',
    'trades.summary.placeholder.value': '데이터 없음',
    'trades.summary.hint': '새로운 텔레메트리가 수신되면 이곳에 AI 힌트가 표시됩니다.',
    'trades.metric.trades': '거래 수',
    'trades.metric.totalPnl': '누적 PNL',
    'trades.metric.winRate': '승률',
    'trades.metric.avgR': '평균 R',
    'trades.postmortem.label': '포스트모템 코치',
    'trades.modal.noMetadata': '추가 메타데이터가 없습니다.',
    'trades.synthetic.badge': '실현 PnL',
    'trades.synthetic.note': '거래소 실현 PnL에서 동기화되어 진입/청산 가격이 없습니다.',
    'trades.synthetic.incomeType': '수익 유형',
    'trades.synthetic.info': '거래소 정보',
    'trades.completed.title': '종료된 포지션',
    'trades.completed.subtitle': '포지션 매니저가 기록한 청산 내역.',
    'trades.completed.empty': '봇이 포지션을 청산하면 여기에 표시됩니다.',
    'trades.completed.pnl': '실현 PNL',
    'trades.completed.reason': '청산 사유',
    'trades.completed.noReason': '사유가 기록되지 않았습니다.',
    'pnl.title': 'PNL 추세',
    'pnl.subtitle': '봇을 시작한 순간부터 누적된 실현 PNL 흐름을 확인하세요.',
    'pnl.tradesWon': '승리한 트레이드',
    'pnl.tradesLost': '패배한 트레이드',
    'pnl.metaLabel': '봇 시작 이후 실현 PNL',
    'pnl.legendLabel': '누적 실현 PNL',
    'pnl.empty': '아직 PNL 데이터가 없습니다. 거래를 실행하면 차트가 채워집니다.',
    'pnl.expandAria': '성과 차트 확장 보기 열기',
    'ai.feed.label': '오토파일럿',
    'ai.feed.title': '자율 전략 조종실',
    'ai.feed.subtitle':
      '전략 텔레메트리와 AI 자율 작업이 여기에 표시됩니다. 대화는 대시보드 채팅 섹션에서 분리되어 제공됩니다.',
    'ai.feed.disabled': 'AI 모드를 활성화하면 활동 피드를 볼 수 있습니다.',
    'ai.feed.empty': '자율 의사결정이 발생하면 실시간으로 여기에 나타납니다.',
    'ai.requests.title': 'AI 결정 로그',
    'ai.requests.subtitle': '거래 요청에 대한 최신 AI 검토와 결과입니다.',
    'ai.requests.empty': 'AI 결정 기록이 여기에 표시됩니다.',
    'ai.requests.status.pending': '응답 대기 중',
    'ai.requests.status.responded': '응답 수신',
    'ai.requests.status.accepted': '진입 승인',
    'ai.requests.status.rejected': '진입 거부',
    'ai.requests.status.analysed': '분석 완료',
    'ai.requests.status.decided': '결정 확정',
    'ai.feed.reasonLabel': '사유',
    'ai.feed.responseLabel': '최근 응답',
    'ai.feed.awaitingResponse': 'AI 응답 대기 중…',
    'ai.feed.reason.plan_pending': 'AI 계획 요청됨',
    'ai.feed.reason.plan_timeout': 'AI 계획 응답 시간 초과',
    'ai.feed.reason.trend_pending': '추세 스캔 요청됨',
    'ai.feed.reason.trend_timeout': '추세 스캔 응답 시간 초과',
    'common.autoScroll': '자동 스크롤',
    'common.close': '닫기',
    'common.save': '저장',
    'common.saving': '저장 중…',
    'common.saved': '저장 완료 ✓',
    'common.error': '오류',
    'common.expand': '확장',
    'common.collapse': '접기',
    'common.analyze': '시장 분석',
    'chat.label': '대시보드 채팅',
    'chat.title': '전략 어시스턴트',
    'chat.subtitle':
      'ChatGPT 스타일 워크스페이스에서 트레이딩 어시스턴트와 대화하세요. 콘솔에는 별도 API 키가 필요합니다.',
    'chat.empty': '대시보드 채팅용 API 키를 입력하면 대화를 시작할 수 있습니다.',
    'chat.inputLabel': '전략 AI에게 질문하기',
    'chat.placeholder': '어시스턴트에게 메시지를 보내세요…',
    'chat.analyze': '시장 분석',
    'chat.analyzing': '분석 중…',
    'chat.analyze.hint': 'AI 설정에서 OpenAI 키를 추가하면 시장 분석을 사용할 수 있습니다.',
    'chat.analyze.pending': '시장 분석을 실행하는 중…',
    'chat.automation.toggle': '자동화',
    'chat.automation.interval': '간격(분)',
    'chat.automation.nextRunLabel': '다음 실행까지',
    'chat.automation.running': '자동화 실행 중…',
    'chat.automation.scheduled': '자동 실행이 {{minutes}}분 후로 예약되었습니다.',
    'chat.automation.stopped': '자동화가 비활성화되었습니다.',
    'chat.automation.rescheduled': '자동화 간격이 {{minutes}}분으로 업데이트되었습니다.',
    'chat.send': '보내기',
    'chat.sending': '전송 중…',
    'chat.status.analyzing': '시장 분석 중…',
    'chat.status.disabled': 'AI 모드가 비활성화되어 있습니다.',
    'chat.status.keyRequired': 'OpenAI 키가 필요합니다.',
    'chat.status.fallback': '시장 분석(대체 모드).',
    'chat.status.ready': '시장 분석 준비 완료.',
    'chat.status.failed': '시장 분석에 실패했습니다.',
    'chat.status.enableAi': '먼저 AI 모드를 활성화하세요.',
    'chat.status.emptyMessage': '메시지를 입력하세요.',
    'chat.status.thinking': '전략 AI가 생각하는 중…',
    'chat.status.error': '채팅을 사용할 수 없습니다.',
    'chat.placeholder.disabled': 'AI 모드를 활성화하면 대시보드 채팅을 사용할 수 있습니다.',
    'chat.placeholder.key': 'AI 설정에서 OpenAI 키를 추가하면 대화를 시작할 수 있습니다.',
    'chat.placeholder.prompt': '전략 어시스턴트에게 거래 상황을 물어보세요.',
    'chat.analysis.none': '분석을 받지 못했습니다.',
    'chat.reply.none': '응답을 받지 못했습니다.',
    'chat.key.ready': '채팅 키가 활성화되었습니다.',
    'chat.role.analysis': '시장 분석',
    'ai.config.title': 'AI 모드 구성',
    'ai.config.subtitle': 'OpenAI 키와 제한을 설정하여 봇이 거래를 자율적으로 관리하도록 하세요.',
    'ai.config.save': '저장',
    'ai.config.saving': '저장 중…',
    'ai.config.saved': '저장 완료 ✓',
    'ai.config.error': '오류',
    'ai.config.access.title': '액세스',
    'ai.config.access.openai': 'OpenAI API 키',
    'ai.config.access.openaiPlaceholder': 'sk-...',
    'ai.config.access.openaiHint': '로컬에만 저장됩니다. 자율 실행에 사용됩니다.',
    'ai.config.access.chat': '대시보드 채팅 키',
    'ai.config.access.chatPlaceholder': 'sk-...',
    'ai.config.access.chatHint':
      '이 별도의 OpenAI 키는 채팅용이며 트레이딩 요청과 분리됩니다. 저장 전까지 채팅 창은 비활성화됩니다.',
    'ai.config.budget.title': '일일 예산',
    'ai.config.budget.label': '일일 예산 (USD)',
    'ai.config.budget.placeholder': '20',
    'ai.config.budget.hint': 'AI 지출 상한을 설정해 자율 운용이 예산을 넘지 않도록 하세요.',
    'ai.config.model.title': '모델',
    'ai.config.model.label': '모델',
    'ai.config.model.group.gpt5': 'GPT-5 계열',
    'ai.config.model.group.gpt41': 'GPT-4.1 계열',
    'ai.config.model.group.gpt4o': 'GPT-4o 계열',
    'ai.config.model.group.reasoning': '추론 모델',
    'ai.config.model.group.legacy': '레거시 모델',
    'ai.config.model.hint': '실시간 시장 분석에 사용할 OpenAI 모델을 선택하세요.',
    'ai.config.baseline.title': '기본 포지션',
    'ai.config.baseline.label': '거래당 기본 포지션 (USDT)',
    'ai.config.baseline.placeholder': '250',
    'ai.config.baseline.hint':
      '<code>ASTER_DEFAULT_NOTIONAL</code>에 해당합니다. 위험 배수와 제약을 적용하기 전 AI가 기준으로 삼는 최소 USDT 금액입니다.',
    'ai.config.footer':
      'AI 모드가 활성화되면 전략 엔진이 일일 예산을 지키면서 포지션 규모, 레버리지, 스탑, FastTP를 지속적으로 조정합니다.',
    'quick.title': '전략 퀵 스타트',
    'quick.subtitle': '프리셋을 고르고 위험과 레버리지를 취향에 맞게 조정하세요.',
    'quick.apply': '프리셋 적용',
    'quick.applyChanges': '변경 사항 적용',
    'quick.applyProgress': '적용 중…',
    'quick.applyRestarting': '재시작 중…',
    'quick.applySuccess': '적용 완료 ✓',
    'quick.applyRestarted': '재시작 완료 ✓',
    'quick.applyError': '오류',
    'quick.presets.low.title': 'Low',
    'quick.presets.low.subtitle': '거래 적음 · 거래당 위험 30% · 자본 33%',
    'quick.presets.mid.title': 'Mid',
    'quick.presets.mid.subtitle': '균형 트레이딩 · 거래당 위험 50% · 자본 66%',
    'quick.presets.high.title': 'High',
    'quick.presets.high.subtitle': '고빈도 · 공격적 · 거래당 위험 100%',
    'quick.presets.att.title': 'ATT',
    'quick.presets.att.subtitle': '역추세 세팅',
    'quick.leverage.title': '레버리지',
    'quick.leverage.placeholder': '기준 레버리지: –',
    'quick.notional.title': '포지션 범위',
    'quick.notional.details': '적응형 포지션 범위: {{min}} – {{max}} 거래당.',
    'quick.notional.unlimited': '계정 자본',
    'quick.description': '추천 위험 파라미터를 불러오려면 프로파일을 선택하세요.',
    'quick.risk.label': '거래당 위험',
    'quick.risk.aria': '거래당 위험 (%)',
    'quick.risk.min': '0.25%',
    'quick.risk.max': '100%',
    'quick.leverage.label': '레버리지',
    'quick.leverage.aria': '레버리지 배수',
    'quick.leverage.min': '1×',
    'quick.leverage.max': '최대 25×',
    'quick.baseline.label': '거래당 기본 배팅 (USDT)',
    'quick.baseline.placeholder': '250',
    'quick.baseline.unit': 'USDT',
    'quick.baseline.hint':
      '<code>ASTER_DEFAULT_NOTIONAL</code>을 설정합니다 — 봇이 위험 규칙을 적용하기 전 각 거래에 예약하는 기본 포지션입니다.',
    'quick.funding.title': '펀딩 필터',
    'quick.funding.details': '선택한 프리셋에 따라 펀딩 제어가 달라집니다.',
    'quick.ml.title': 'ML 정책',
    'quick.ml.empty': '프리셋을 불러오면 ML 정책 세부 정보가 표시됩니다.',
    'quick.ml.none': '이 프리셋에는 ML 설명이 없습니다.',
    'env.title': '환경 구성',
    'env.expand': '펼치기',
    'env.collapse': '접기',
    'env.save': '저장',
    'env.saving': '저장 중…',
    'env.saved': '저장 완료 ✓',
    'env.error': '오류',
    'env.subtitle':
      '서비스를 재시작하지 않고도 모든 <code>ASTER_*</code> 파라미터를 변경하세요. 변경 사항은 자동으로 저장됩니다.',
    'logs.activity.title': '활동 피드',
    'logs.activity.subtitle': '핵심 거래, 경고, 하이 시그널 이벤트.',
    'logs.debug.title': '실시간 디버그 로그',
    'modals.decision.title': '거래 결정 사유',
    'modals.trade.title': '거래 세부 정보',
    'modals.pnl.title': 'PNL 추세',
    'modals.pnl.subtitle': '봇을 시작한 순간부터 누적된 실현 PNL 흐름을 확인하세요.',
    'footer.note':
      'Aster를 위해 설계된 적응형 트레이딩 — 완전한 투명성과 함께 전략을 개선하세요. 실시간 로그와 AI 힌트를 활용해 자신 있게 전략을 다듬으세요.',
  },
  fr: {
    'language.english': 'Anglais',
    'language.russian': 'Russe',
    'language.chinese': 'Chinois (mandarin)',
    'language.german': 'Allemand',
    'language.french': 'Français',
    'language.spanish': 'Espagnol',
    'language.turkish': 'Turc',
    'language.korean': 'Coréen',
    'language.switcher': 'Choisir la langue',
    'nav.menu': 'Sections',
    'nav.overview': 'Aperçu',
    'nav.trades': 'Transactions',
    'nav.playbook': 'Playbook',
    'nav.config': 'Config',
    'nav.logs': 'Journaux',
    'ticker.label': 'Crypto les plus échangées · Top 20 :',
    'ticker.empty': 'Collecte des leaders du marché…',
    'ticker.noData': 'Aucune donnée de marché disponible pour le moment.',
    'hero.badge': 'MrAster – Suite de trading autonome',
    'hero.heading': 'Profitez de chaque mouvement du marché avec une automatisation réglée par l’IA.',
    'hero.description':
      'Déployez des bots crypto en quelques secondes, diffusez la télémétrie en direct et recalibrez vos stratégies avec des copilotes IA qui garantissent une transparence totale en modes Standard, Pro et AI.',
    'hero.launch': 'Ouvrir Aster',
    'hero.download': 'Télécharger les trades',
    'hero.share': 'Publier sur X',
    'hero.metrics.trades': 'Total des trades',
    'hero.metrics.pnl': 'PNL cumulé',
    'hero.metrics.winrate': 'Taux de réussite global',
    'hero.metrics.volume': 'Volume total',
    'hero.mode.label': 'Mode',
    'hero.mode.standard': 'Standard',
    'hero.mode.pro': 'Pro',
    'hero.mode.ai': 'IA',
    'hero.mode.paper': 'Activer le mode papier',
    'active.title': 'Positions actives',
    'active.subtitle': 'Exposition en temps réel sur tous les modes.',
    'active.mode': 'Tous les modes',
    'active.mode.paper': 'Mode papier',
    'active.mode.unrealized': 'PNL total non réalisé',
    'active.notifications.title': 'Mises à jour des positions',
    'active.notifications.subtitle': 'Mises à jour en temps réel pour les positions ouvertes.',
    'active.notifications.empty': 'Aucune gestion récente pour le moment.',
    'active.empty': 'Aucune position active.',
    'active.empty.paper': 'Aucun trade en mode papier pour l’instant.',
    'active.notifications.closed': 'Position clôturée',
    'active.table.symbol': 'Symbole',
    'active.table.size': 'Taille',
    'active.table.entry': 'Prix d’entrée',
    'active.table.mark': 'Prix de marché',
    'active.table.leverage': 'Effet de levier',
    'active.table.margin': 'Marge',
    'active.table.pnl': 'PNL (ROE %)',
    'active.management.fasttp': 'Sortie FastTP ajustée',
    'active.management.breakeven': 'Stop déplacé au break-even',
    'active.management.trail': 'Trailing stop resserré',
    'active.management.autoHalf': 'Prise de profit automatique partielle exécutée',
    'active.management.scaleHalf': 'Allégement progressif exécuté',
    'active.management.timeCut': 'Réduction déclenchée par le temps exécutée',
    'active.management.reduceOnly': 'Ordre reduce-only envoyé',
    'active.management.generic': 'Le bot a ajusté cette position',
    'active.management.justNow': 'à l’instant',
    'active.management.oneMinuteAgo': 'il y a 1 min',
    'active.management.minutesAgo': 'il y a {{value}} min',
    'active.management.hoursAgo': 'il y a {{value}} h',
    'active.management.daysAgo': 'il y a {{value}} j',
    'status.title': 'Statut',
    'status.state': 'État',
    'status.pid': 'PID',
    'status.started': 'Démarré',
    'status.uptime': 'Durée de fonctionnement',
    'status.indicator.running': 'En cours',
    'status.indicator.stopped': 'Arrêté',
    'status.indicator.offline': 'Hors ligne',
    'status.aiBudget': 'Budget IA (quotidien)',
    'status.aiBudget.standard': 'Standard',
    'status.aiBudget.pro': 'Mode Pro',
    'status.aiBudget.paper': 'Mode papier',
    'status.aiBudgetMeta': 'Budget non configuré.',
    'status.aiBudgetMeta.disabled': 'Le mode IA est désactivé.',
    'status.aiBudgetMeta.unlimited': 'Dépenses du jour {{spent}} USD · aucun plafond',
    'status.aiBudgetMeta.limited': 'Dépenses du jour {{spent}} / {{limit}} USD · reste {{remaining}} USD',
    'status.aiBudgetMeta.paper': 'Le mode papier n’utilise pas de budget.',
    'status.tradeDecisions': 'Décisions de trading',
    'status.decisions.accepted': 'Exécutées :',
    'status.decisions.skipped': 'Ignorées :',
    'status.decisions.empty': 'Aucune décision de trading pour le moment.',
    'status.decisions.noneSkipped': 'Aucun trade ignoré enregistré.',
    'status.decisions.noneYet': 'Pas encore de décisions de trading.',
    'status.decisions.noReason': 'Aucune opération pour ce motif pour l’instant. Revenez après la prochaine décision.',
    'status.decisions.noReasonShort': 'Aucune opération pour ce motif pour l’instant.',
    'status.decisions.showDetails': 'Afficher les détails',
    'status.decisions.hideDetails': 'Masquer les détails',
    'status.decisions.download': 'Télécharger',
    'status.decisions.exportError': 'Impossible de télécharger les trades ignorés pour le moment.',
    'credentials.title': 'Identifiants d’exchange',
    'credentials.apiKey.label': 'ASTER_API_KEY',
    'credentials.apiKey.placeholder': 'Saisir la clé API',
    'credentials.apiSecret.label': 'ASTER_API_SECRET',
    'credentials.apiSecret.placeholder': 'Saisir la clé secrète',
    'credentials.start': 'Démarrer',
    'credentials.stop': 'Arrêter',
    'credentials.save': 'Enregistrer',
    'credentials.saving': 'Enregistrement…',
    'credentials.saved': 'Enregistré ✓',
    'credentials.error': 'Erreur',
    'trades.title': 'Historique des trades',
    'trades.subtitle': 'Dernières exécutions et résultats en un clin d’œil.',
    'trades.empty': 'Aucun trade pour le moment.',
    'trades.viewDetails': 'Voir les détails',
    'trades.summary.placeholder.label': 'Performance',
    'trades.summary.placeholder.value': 'Pas encore de données',
    'trades.summary.hint': 'Un commentaire IA apparaîtra ici dès que de nouvelles données de télémétrie seront disponibles.',
    'trades.metric.trades': 'Trades',
    'trades.metric.totalPnl': 'PNL total',
    'trades.metric.winRate': 'Taux de réussite',
    'trades.metric.avgR': 'R moyen',
    'trades.postmortem.label': 'Coach post-mortem',
    'trades.modal.noMetadata': 'Aucune donnée supplémentaire.',
    'trades.synthetic.badge': 'PnL réalisé',
    'trades.synthetic.note': 'Synchronisé depuis le PnL réalisé de l’exchange – entrées/sorties indisponibles.',
    'trades.synthetic.incomeType': 'Type de revenu',
    'trades.synthetic.info': 'Info bourse',
    'trades.completed.title': 'Positions clôturées',
    'trades.completed.subtitle': 'Sorties documentées par le gestionnaire de positions.',
    'trades.completed.empty': 'Elles apparaîtront après la prochaine clôture du bot.',
    'trades.completed.pnl': 'PNL réalisé',
    'trades.completed.reason': 'Motif de sortie',
    'trades.completed.noReason': 'Aucun motif consigné.',
    'pnl.title': 'Trajectoire du PNL',
    'pnl.subtitle': 'Suivez l’évolution du PNL réalisé depuis le lancement du bot.',
    'pnl.tradesWon': 'Trades gagnants',
    'pnl.tradesLost': 'Trades perdants',
    'pnl.metaLabel': 'PNL réalisé depuis le lancement du bot',
    'pnl.legendLabel': 'PNL réalisé cumulé',
    'pnl.empty': 'Pas encore de données de PNL. Exécutez des trades pour alimenter le graphique.',
    'pnl.expandAria': 'Ouvrir le graphique de performance étendu',
    'ai.feed.label': 'Autopilote',
    'ai.feed.title': 'Cockpit stratégique autonome',
    'ai.feed.subtitle':
      'La télémétrie de stratégie et les actions autonomes de l’IA apparaissent ici. Les conversations se déroulent dans le chat du tableau de bord.',
    'ai.feed.disabled': 'Activez le mode IA pour voir le flux d’activité.',
    'ai.feed.empty': 'Les décisions autonomes apparaîtront ici en temps réel dès qu’elles surviennent.',
    'ai.requests.title': 'Décisions de l’IA',
    'ai.requests.subtitle': 'Dernières revues et décisions de l’IA sur les demandes de trading.',
    'ai.requests.empty': 'Les décisions de l’IA apparaîtront ici.',
    'ai.requests.status.pending': 'En attente de réponse',
    'ai.requests.status.responded': 'Réponse reçue',
    'ai.requests.status.accepted': 'Entrée validée',
    'ai.requests.status.rejected': 'Entrée refusée',
    'ai.requests.status.analysed': 'Analyse terminée',
    'ai.requests.status.decided': 'Décision enregistrée',
    'ai.feed.reasonLabel': 'Raison',
    'ai.feed.responseLabel': 'Dernière réponse',
    'ai.feed.awaitingResponse': 'En attente de la réponse de l’IA…',
    'ai.feed.reason.plan_pending': 'Plan IA en cours',
    'ai.feed.reason.plan_timeout': 'Plan IA expiré',
    'ai.feed.reason.trend_pending': 'Analyse de tendance en cours',
    'ai.feed.reason.trend_timeout': 'Analyse de tendance expirée',
    'common.autoScroll': 'Défilement auto',
    'common.close': 'Fermer',
    'common.save': 'Enregistrer',
    'common.saving': 'Enregistrement…',
    'common.saved': 'Enregistré ✓',
    'common.error': 'Erreur',
    'common.expand': 'Développer',
    'common.collapse': 'Réduire',
    'common.analyze': 'Analyser le marché',
    'chat.label': 'Chat du tableau de bord',
    'chat.title': 'Assistant stratégique',
    'chat.subtitle':
      'Discutez avec l’assistant de trading dans une interface façon ChatGPT. La console nécessite sa propre clé API.',
    'chat.empty': 'Ajoutez une clé API pour le chat du tableau de bord afin de démarrer.',
    'chat.inputLabel': 'Interroger l’IA de stratégie',
    'chat.placeholder': 'Envoyez un message à votre assistant…',
    'chat.analyze': 'Analyser le marché',
    'chat.analyzing': 'Analyse en cours…',
    'chat.analyze.hint': 'Ajoutez une clé OpenAI dans les paramètres IA pour activer l’analyse de marché.',
    'chat.analyze.pending': 'Analyse de marché en cours…',
    'chat.automation.toggle': 'Automatiser',
    'chat.automation.interval': 'Intervalle (minutes)',
    'chat.automation.nextRunLabel': 'Prochaine exécution dans',
    'chat.automation.running': 'Automatisation en cours…',
    'chat.automation.scheduled': 'Cycle automatisé planifié dans {{minutes}} minute(s).',
    'chat.automation.stopped': 'Automatisation désactivée.',
    'chat.automation.rescheduled': 'Intervalle d’automatisation mis à jour à {{minutes}} minute(s).',
    'chat.send': 'Envoyer',
    'chat.sending': 'Envoi…',
    'chat.status.analyzing': 'Analyse de marché en cours…',
    'chat.status.disabled': 'Le mode IA est désactivé.',
    'chat.status.keyRequired': 'Clé OpenAI requise.',
    'chat.status.fallback': 'Analyse de marché (mode secours).',
    'chat.status.ready': 'Analyse de marché prête.',
    'chat.status.failed': 'Échec de l’analyse de marché.',
    'chat.status.enableAi': 'Activez d’abord le mode IA.',
    'chat.status.emptyMessage': 'Veuillez saisir un message.',
    'chat.status.thinking': 'L’IA stratégique réfléchit…',
    'chat.status.error': 'Chat indisponible.',
    'chat.placeholder.disabled': 'Activez le mode IA pour utiliser le chat du tableau de bord.',
    'chat.placeholder.key': 'Ajoutez une clé OpenAI dans les paramètres IA pour commencer.',
    'chat.placeholder.prompt': 'Interrogez l’assistant stratégique sur vos trades.',
    'chat.analysis.none': 'Aucune analyse reçue.',
    'chat.reply.none': 'Aucune réponse reçue.',
    'chat.key.ready': 'La clé de chat est active.',
    'chat.role.analysis': 'Analyse de marché',
    'ai.config.title': 'Configurer le mode IA',
    'ai.config.subtitle': 'Renseignez les clés OpenAI et les limites pour que le bot gère les trades de façon autonome.',
    'ai.config.save': 'Enregistrer',
    'ai.config.saving': 'Enregistrement…',
    'ai.config.saved': 'Enregistré ✓',
    'ai.config.error': 'Erreur',
    'ai.config.access.title': 'Accès',
    'ai.config.access.openai': 'Clé API OpenAI',
    'ai.config.access.openaiPlaceholder': 'sk-...',
    'ai.config.access.openaiHint': 'Stockée uniquement en local. Permet l’exécution autonome.',
    'ai.config.access.chat': 'Clé du chat du tableau de bord',
    'ai.config.access.chatPlaceholder': 'sk-...',
    'ai.config.access.chatHint':
      'Cette clé OpenAI séparée alimente le chat et reste isolée des requêtes de trading. Tant qu’elle n’est pas enregistrée, la fenêtre de chat reste désactivée.',
    'ai.config.budget.title': 'Budget quotidien',
    'ai.config.budget.label': 'Budget quotidien (USD)',
    'ai.config.budget.placeholder': '20',
    'ai.config.budget.hint': 'Fixez une limite de dépenses pour que l’IA reste dans le budget.',
    'ai.config.model.title': 'Modèle',
    'ai.config.model.label': 'Modèle',
    'ai.config.model.group.gpt5': 'Série GPT-5',
    'ai.config.model.group.gpt41': 'Série GPT-4.1',
    'ai.config.model.group.gpt4o': 'Série GPT-4o',
    'ai.config.model.group.reasoning': 'Modèles de raisonnement',
    'ai.config.model.group.legacy': 'Modèles hérités',
    'ai.config.model.hint': 'Choisissez le modèle OpenAI pour votre analyse de marché en temps réel.',
    'ai.config.baseline.title': 'Position de base',
    'ai.config.baseline.label': 'Position de base par trade (USDT)',
    'ai.config.baseline.placeholder': '250',
    'ai.config.baseline.hint':
      'Correspond à <code>ASTER_DEFAULT_NOTIONAL</code> : le montant minimal en USDT que l’IA utilise avant les multiplicateurs de risque.',
    'ai.config.footer':
      'Avec le mode IA activé, le moteur stratégique ajuste en continu taille de position, levier, stop et FastTP tout en respectant le budget quotidien.',
    'quick.title': 'Démarrage rapide de la stratégie',
    'quick.subtitle': 'Choisissez un preset et ajustez risque et levier selon vos préférences.',
    'quick.apply': 'Appliquer le preset',
    'quick.applyChanges': 'Appliquer les modifications',
    'quick.applyProgress': 'Application…',
    'quick.applyRestarting': 'Redémarrage…',
    'quick.applySuccess': 'Appliqué ✓',
    'quick.applyRestarted': 'Redémarré ✓',
    'quick.applyError': 'Erreur',
    'quick.presets.low.title': 'Low',
    'quick.presets.low.subtitle': 'Basse fréquence · Risque 30 % par trade · Capital 33 %',
    'quick.presets.mid.title': 'Mid',
    'quick.presets.mid.subtitle': 'Trading équilibré · Risque 50 % par trade · Capital 66 %',
    'quick.presets.high.title': 'High',
    'quick.presets.high.subtitle': 'Haute fréquence · Agressif · Risque 100 % par trade',
    'quick.presets.att.title': 'ATT',
    'quick.presets.att.subtitle': 'Configuration contrarienne',
    'quick.leverage.title': 'Effet de levier',
    'quick.leverage.placeholder': 'Effet de levier de base : –',
    'quick.notional.title': 'Plage de taille',
    'quick.notional.details': 'Taille adaptative : {{min}} – {{max}} par trade.',
    'quick.notional.unlimited': 'capitaux du compte',
    'quick.description': 'Choisissez une configuration pour charger les paramètres de risque recommandés.',
    'quick.risk.label': 'Risque par trade',
    'quick.risk.aria': 'Risque par trade (%)',
    'quick.risk.min': '0,25 %',
    'quick.risk.max': '100 %',
    'quick.leverage.label': 'Effet de levier',
    'quick.leverage.aria': 'Multiplicateur de levier',
    'quick.leverage.min': '1×',
    'quick.leverage.max': 'Jusqu’à 25×',
    'quick.baseline.label': 'Mise de base par trade (USDT)',
    'quick.baseline.placeholder': '250',
    'quick.baseline.unit': 'USDT',
    'quick.baseline.hint':
      'Définit <code>ASTER_DEFAULT_NOTIONAL</code> : la position de base que le bot réserve avant les règles de risque.',
    'quick.funding.title': 'Filtre de funding',
    'quick.funding.details': 'Les filtres de funding dépendent du preset choisi.',
    'quick.ml.title': 'Stratégie ML',
    'quick.ml.empty': 'Chargez un preset pour afficher les détails de la stratégie ML.',
    'quick.ml.none': 'Ce preset n’inclut pas de stratégie ML.',
    'env.title': 'Configuration de l’environnement',
    'env.expand': 'Développer',
    'env.collapse': 'Réduire',
    'env.save': 'Enregistrer',
    'env.saving': 'Enregistrement…',
    'env.saved': 'Enregistré ✓',
    'env.error': 'Erreur',
    'env.subtitle':
      'Modifiez n’importe quel paramètre <code>ASTER_*</code> sans redémarrer le service. Les changements sont enregistrés automatiquement.',
    'logs.activity.title': 'Flux d’activité',
    'logs.activity.subtitle': 'Trades clés, alertes et événements à fort signal.',
    'logs.debug.title': 'Logs de débogage en temps réel',
    'modals.decision.title': 'Raison de la décision de trading',
    'modals.trade.title': 'Détails du trade',
    'modals.pnl.title': 'Trajectoire du PNL',
    'modals.pnl.subtitle': 'Suivez l’évolution du PNL réalisé depuis le lancement du bot.',
    'footer.note':
      'Conçu pour Aster – un trading adaptable avec une transparence totale. Exploitez les logs en direct et les conseils de l’IA pour optimiser votre stratégie en toute confiance.',
  },
  es: {
    'language.english': 'Inglés',
    'language.russian': 'Ruso',
    'language.chinese': 'Chino (mandarín)',
    'language.german': 'Alemán',
    'language.french': 'Francés',
    'language.spanish': 'Español',
    'language.turkish': 'Turco',
    'language.korean': 'Coreano',
    'language.switcher': 'Seleccionar idioma',
    'nav.menu': 'Secciones',
    'nav.overview': 'Resumen',
    'nav.trades': 'Operaciones',
    'nav.playbook': 'Playbook',
    'nav.config': 'Configuración',
    'nav.logs': 'Registros',
    'ticker.label': 'Monedas más negociadas · Top 20:',
    'ticker.empty': 'Reuniendo líderes del mercado…',
    'ticker.noData': 'No hay datos de mercado disponibles.',
    'hero.badge': 'MrAster – Suite de trading autónoma',
    'hero.heading': 'Aprovecha cada movimiento del mercado con automatización ajustada por IA.',
    'hero.description':
      'Despliega bots cripto en segundos, transmite telemetría en vivo y recalibra estrategias con copilotos de IA que mantienen una transparencia absoluta en los modos Standard, Pro y AI.',
    'hero.launch': 'Abrir Aster',
    'hero.download': 'Descargar operaciones',
    'hero.share': 'Publicar en X',
    'hero.metrics.trades': 'Operaciones totales',
    'hero.metrics.pnl': 'PNL acumulado',
    'hero.metrics.winrate': 'Ratio de aciertos total',
    'hero.metrics.volume': 'Volumen total',
    'hero.mode.label': 'Modo',
    'hero.mode.standard': 'Estándar',
    'hero.mode.pro': 'Pro',
    'hero.mode.ai': 'IA',
    'hero.mode.paper': 'Activar modo simulado',
    'active.title': 'Posiciones activas',
    'active.subtitle': 'Exposición actual en todos los modos.',
    'active.mode': 'Todos los modos',
    'active.mode.paper': 'Modo simulado',
    'active.mode.unrealized': 'PNL total no realizado',
    'active.notifications.title': 'Actualizaciones de posiciones',
    'active.notifications.subtitle': 'Actualizaciones en tiempo real de las posiciones abiertas.',
    'active.notifications.empty': 'Aún no hay eventos recientes de gestión.',
    'active.empty': 'Sin posiciones activas.',
    'active.empty.paper': 'Todavía no hay operaciones simuladas.',
    'active.notifications.closed': 'Posición cerrada',
    'active.table.symbol': 'Símbolo',
    'active.table.size': 'Tamaño',
    'active.table.entry': 'Precio de entrada',
    'active.table.mark': 'Precio de marca',
    'active.table.leverage': 'Apalancamiento',
    'active.table.margin': 'Margen',
    'active.table.pnl': 'PNL (ROE%)',
    'active.management.fasttp': 'Salida FastTP ajustada',
    'active.management.breakeven': 'Stop movido a punto de equilibrio',
    'active.management.trail': 'Trailing stop ajustado',
    'active.management.autoHalf': 'Toma de ganancias automática redujo la posición',
    'active.management.scaleHalf': 'Reducción gradual ejecutada',
    'active.management.timeCut': 'Reducción basada en tiempo ejecutada',
    'active.management.reduceOnly': 'Orden reduce-only enviada',
    'active.management.generic': 'El bot ajustó esta posición',
    'active.management.justNow': 'ahora mismo',
    'active.management.oneMinuteAgo': 'hace 1 min',
    'active.management.minutesAgo': 'hace {{value}} min',
    'active.management.hoursAgo': 'hace {{value}} h',
    'active.management.daysAgo': 'hace {{value}} d',
    'status.title': 'Estado',
    'status.state': 'Estado',
    'status.pid': 'PID',
    'status.started': 'Inicio',
    'status.uptime': 'Tiempo activo',
    'status.indicator.running': 'En ejecución',
    'status.indicator.stopped': 'Detenido',
    'status.indicator.offline': 'Sin conexión',
    'status.aiBudget': 'Presupuesto de IA (diario)',
    'status.aiBudget.standard': 'Estándar',
    'status.aiBudget.pro': 'Modo Pro',
    'status.aiBudget.paper': 'Modo simulado',
    'status.aiBudgetMeta': 'Presupuesto no configurado.',
    'status.aiBudgetMeta.disabled': 'El modo IA está desactivado.',
    'status.aiBudgetMeta.unlimited': 'Gasto del día {{spent}} USD · sin límite',
    'status.aiBudgetMeta.limited': 'Gasto del día {{spent}} / {{limit}} USD · restante {{remaining}} USD',
    'status.aiBudgetMeta.paper': 'El modo simulado no consume presupuesto.',
    'status.tradeDecisions': 'Decisiones de trading',
    'status.decisions.accepted': 'Ejecutadas:',
    'status.decisions.skipped': 'Omitidas:',
    'status.decisions.empty': 'Aún no hay decisiones de trading.',
    'status.decisions.noneSkipped': 'No se han registrado operaciones omitidas.',
    'status.decisions.noneYet': 'Aún no hay decisiones de trading.',
    'status.decisions.noReason': 'Todavía no hay operaciones para este motivo. Vuelve tras la próxima decisión.',
    'status.decisions.noReasonShort': 'Todavía no hay operaciones para este motivo.',
    'status.decisions.showDetails': 'Mostrar detalles',
    'status.decisions.hideDetails': 'Ocultar detalles',
    'status.decisions.download': 'Descargar',
    'status.decisions.exportError': 'No se pudieron descargar los trades omitidos en este momento.',
    'credentials.title': 'Credenciales del exchange',
    'credentials.apiKey.label': 'ASTER_API_KEY',
    'credentials.apiKey.placeholder': 'Introduce la clave API',
    'credentials.apiSecret.label': 'ASTER_API_SECRET',
    'credentials.apiSecret.placeholder': 'Introduce la clave secreta',
    'credentials.start': 'Iniciar',
    'credentials.stop': 'Detener',
    'credentials.save': 'Guardar',
    'credentials.saving': 'Guardando…',
    'credentials.saved': 'Guardado ✓',
    'credentials.error': 'Error',
    'trades.title': 'Historial de operaciones',
    'trades.subtitle': 'Ejecuciones recientes y resultados de un vistazo.',
    'trades.empty': 'Aún no hay operaciones.',
    'trades.viewDetails': 'Ver detalles',
    'trades.summary.placeholder.label': 'Rendimiento',
    'trades.summary.placeholder.value': 'Sin datos todavía',
    'trades.summary.hint': 'Una nota de IA aparecerá aquí cuando llegue nueva telemetría.',
    'trades.metric.trades': 'Operaciones',
    'trades.metric.totalPnl': 'PNL total',
    'trades.metric.winRate': 'Ratio de aciertos',
    'trades.metric.avgR': 'R medio',
    'trades.postmortem.label': 'Coach post-mortem',
    'trades.modal.noMetadata': 'No hay datos adicionales.',
    'trades.synthetic.badge': 'PnL realizado',
    'trades.synthetic.note': 'Sincronizado desde el PnL realizado del exchange; no hay datos de entrada/salida.',
    'trades.synthetic.incomeType': 'Tipo de ingreso',
    'trades.synthetic.info': 'Nota del exchange',
    'trades.completed.title': 'Posiciones cerradas',
    'trades.completed.subtitle': 'Salidas documentadas por el gestor de posiciones.',
    'trades.completed.empty': 'Las posiciones cerradas aparecerán tras el próximo cierre del bot.',
    'trades.completed.pnl': 'PNL realizado',
    'trades.completed.reason': 'Motivo de salida',
    'trades.completed.noReason': 'Sin motivo registrado.',
    'pnl.title': 'Evolución del PNL',
    'pnl.subtitle': 'Sigue el crecimiento del PNL realizado desde el inicio del bot.',
    'pnl.tradesWon': 'Operaciones ganadas',
    'pnl.tradesLost': 'Operaciones perdidas',
    'pnl.metaLabel': 'PNL realizado desde el inicio del bot',
    'pnl.legendLabel': 'PNL realizado acumulado',
    'pnl.empty': 'Sin datos de PNL por ahora. Ejecuta operaciones para poblar el gráfico.',
    'pnl.expandAria': 'Abrir gráfico de rendimiento ampliado',
    'ai.feed.label': 'Autopiloto',
    'ai.feed.title': 'Cabina estratégica autónoma',
    'ai.feed.subtitle':
      'Aquí aparecen la telemetría de la estrategia y las acciones autónomas de la IA. Las conversaciones viven en el chat del dashboard.',
    'ai.feed.disabled': 'Activa el modo IA para ver el feed de actividad.',
    'ai.feed.empty': 'Las decisiones autónomas aparecerán aquí en tiempo real conforme sucedan.',
    'ai.requests.title': 'Decisiones de la IA',
    'ai.requests.subtitle': 'Revisiones y resultados más recientes de la IA para las señales de trading.',
    'ai.requests.empty': 'Aquí aparecerá el historial de decisiones de la IA.',
    'ai.requests.status.pending': 'Esperando respuesta',
    'ai.requests.status.responded': 'Respuesta recibida',
    'ai.requests.status.accepted': 'Entrada aprobada',
    'ai.requests.status.rejected': 'Entrada rechazada',
    'ai.requests.status.analysed': 'Análisis completado',
    'ai.requests.status.decided': 'Decisión registrada',
    'ai.feed.reasonLabel': 'Motivo',
    'ai.feed.responseLabel': 'Última respuesta',
    'ai.feed.awaitingResponse': 'Esperando la respuesta de la IA…',
    'ai.feed.reason.plan_pending': 'Plan de IA solicitado',
    'ai.feed.reason.plan_timeout': 'El plan de IA no respondió a tiempo',
    'ai.feed.reason.trend_pending': 'Exploración de tendencia solicitada',
    'ai.feed.reason.trend_timeout': 'La exploración de tendencia no respondió a tiempo',
    'common.autoScroll': 'Autodesplazamiento',
    'common.close': 'Cerrar',
    'common.save': 'Guardar',
    'common.saving': 'Guardando…',
    'common.saved': 'Guardado ✓',
    'common.error': 'Error',
    'common.expand': 'Expandir',
    'common.collapse': 'Contraer',
    'common.analyze': 'Analizar mercado',
    'chat.label': 'Chat del dashboard',
    'chat.title': 'Asistente estratégico',
    'chat.subtitle':
      'Conversa con el asistente de trading en una interfaz tipo ChatGPT. La consola requiere su propia clave API.',
    'chat.empty': 'Añade una clave API para el chat del dashboard y empieza a usarlo.',
    'chat.inputLabel': 'Pregunta a la IA de estrategia',
    'chat.placeholder': 'Envía un mensaje a tu asistente…',
    'chat.analyze': 'Analizar mercado',
    'chat.analyzing': 'Analizando…',
    'chat.analyze.hint': 'Agrega una clave de OpenAI en los ajustes de IA para activar el análisis de mercado.',
    'chat.analyze.pending': 'Análisis de mercado en curso…',
    'chat.automation.toggle': 'Automatizar',
    'chat.automation.interval': 'Intervalo (minutos)',
    'chat.automation.nextRunLabel': 'Próxima ejecución en',
    'chat.automation.running': 'Automatización en curso…',
    'chat.automation.scheduled': 'Ciclo automatizado programado en {{minutes}} minuto(s).',
    'chat.automation.stopped': 'Automatización desactivada.',
    'chat.automation.rescheduled': 'Intervalo de automatización actualizado a {{minutes}} minuto(s).',
    'chat.send': 'Enviar',
    'chat.sending': 'Enviando…',
    'chat.status.analyzing': 'Análisis de mercado en curso…',
    'chat.status.disabled': 'El modo IA está desactivado.',
    'chat.status.keyRequired': 'Se requiere clave de OpenAI.',
    'chat.status.fallback': 'Análisis de mercado (modo respaldo).',
    'chat.status.ready': 'Análisis de mercado listo.',
    'chat.status.failed': 'Análisis de mercado fallido.',
    'chat.status.enableAi': 'Activa el modo IA primero.',
    'chat.status.emptyMessage': 'Introduce un mensaje.',
    'chat.status.thinking': 'La IA de estrategia está pensando…',
    'chat.status.error': 'El chat no está disponible.',
    'chat.placeholder.disabled': 'Activa el modo IA para usar el chat del dashboard.',
    'chat.placeholder.key': 'Añade una clave de OpenAI en los ajustes de IA para empezar.',
    'chat.placeholder.prompt': 'Pregunta al asistente estratégico sobre tus operaciones.',
    'chat.analysis.none': 'No se recibió análisis.',
    'chat.reply.none': 'No se recibió respuesta.',
    'chat.key.ready': 'La clave del chat está activa.',
    'chat.role.analysis': 'Análisis de mercado',
    'ai.config.title': 'Configurar modo IA',
    'ai.config.subtitle': 'Introduce claves de OpenAI y límites para que el bot gestione las operaciones de forma autónoma.',
    'ai.config.save': 'Guardar',
    'ai.config.saving': 'Guardando…',
    'ai.config.saved': 'Guardado ✓',
    'ai.config.error': 'Error',
    'ai.config.access.title': 'Acceso',
    'ai.config.access.openai': 'Clave API de OpenAI',
    'ai.config.access.openaiPlaceholder': 'sk-...',
    'ai.config.access.openaiHint': 'Solo se guarda localmente. Permite la ejecución autónoma.',
    'ai.config.access.chat': 'Clave para el chat del dashboard',
    'ai.config.access.chatPlaceholder': 'sk-...',
    'ai.config.access.chatHint':
      'Esta clave de OpenAI separada se usa para el chat y está aislada de las solicitudes de trading. El chat permanece deshabilitado hasta guardarla.',
    'ai.config.budget.title': 'Presupuesto diario',
    'ai.config.budget.label': 'Presupuesto diario (USD)',
    'ai.config.budget.placeholder': '20',
    'ai.config.budget.hint': 'Establece un límite de gasto para que la IA permanezca dentro del presupuesto.',
    'ai.config.model.title': 'Modelo',
    'ai.config.model.label': 'Modelo',
    'ai.config.model.group.gpt5': 'Serie GPT-5',
    'ai.config.model.group.gpt41': 'Serie GPT-4.1',
    'ai.config.model.group.gpt4o': 'Serie GPT-4o',
    'ai.config.model.group.reasoning': 'Modelos de razonamiento',
    'ai.config.model.group.legacy': 'Modelos heredados',
    'ai.config.model.hint': 'Elige el modelo de OpenAI para el análisis de mercado en tiempo real.',
    'ai.config.baseline.title': 'Posición base',
    'ai.config.baseline.label': 'Posición base por operación (USDT)',
    'ai.config.baseline.placeholder': '250',
    'ai.config.baseline.hint':
      'Equivale a <code>ASTER_DEFAULT_NOTIONAL</code>: el mínimo en USDT que la IA usa antes de multiplicadores de riesgo.',
    'ai.config.footer':
      'Con el modo IA activo, el motor ajusta continuamente tamaño, apalancamiento, stop-loss y FastTP sin salir del presupuesto diario.',
    'quick.title': 'Inicio rápido de la estrategia',
    'quick.subtitle': 'Selecciona un preset y ajusta riesgo y apalancamiento a tu gusto.',
    'quick.apply': 'Aplicar preset',
    'quick.applyChanges': 'Aplicar cambios',
    'quick.applyProgress': 'Aplicando…',
    'quick.applyRestarting': 'Reiniciando…',
    'quick.applySuccess': 'Aplicado ✓',
    'quick.applyRestarted': 'Reiniciado ✓',
    'quick.applyError': 'Error',
    'quick.presets.low.title': 'Low',
    'quick.presets.low.subtitle': 'Baja frecuencia · 30% de riesgo por operación · 33% capital',
    'quick.presets.mid.title': 'Mid',
    'quick.presets.mid.subtitle': 'Trading equilibrado · 50% de riesgo por operación · 66% capital',
    'quick.presets.high.title': 'High',
    'quick.presets.high.subtitle': 'Alta frecuencia · Agresivo · 100% de riesgo por operación',
    'quick.presets.att.title': 'ATT',
    'quick.presets.att.subtitle': 'Configuración contra tendencia',
    'quick.leverage.title': 'Apalancamiento',
    'quick.leverage.placeholder': 'Apalancamiento base: –',
    'quick.notional.title': 'Rango de tamaño',
    'quick.notional.details': 'Tamaño adaptativo: {{min}} – {{max}} por operación.',
    'quick.notional.unlimited': 'capital de la cuenta',
    'quick.description': 'Elige una configuración para cargar los parámetros de riesgo recomendados.',
    'quick.risk.label': 'Riesgo por operación',
    'quick.risk.aria': 'Riesgo por operación (%)',
    'quick.risk.min': '0,25%',
    'quick.risk.max': '100%',
    'quick.leverage.label': 'Apalancamiento',
    'quick.leverage.aria': 'Multiplicador de apalancamiento',
    'quick.leverage.min': '1×',
    'quick.leverage.max': 'Hasta 25×',
    'quick.baseline.label': 'Apuesta base por operación (USDT)',
    'quick.baseline.placeholder': '250',
    'quick.baseline.unit': 'USDT',
    'quick.baseline.hint':
      'Define <code>ASTER_DEFAULT_NOTIONAL</code>: la posición base que el bot reserva antes de aplicar reglas de riesgo.',
    'quick.funding.title': 'Filtro de funding',
    'quick.funding.details': 'Los filtros de funding dependen del preset seleccionado.',
    'quick.ml.title': 'Estrategia de ML',
    'quick.ml.empty': 'Carga un preset para ver los detalles de la estrategia ML.',
    'quick.ml.none': 'Este preset no incluye estrategia ML.',
    'env.title': 'Configuración del entorno',
    'env.expand': 'Expandir',
    'env.collapse': 'Contraer',
    'env.save': 'Guardar',
    'env.saving': 'Guardando…',
    'env.saved': 'Guardado ✓',
    'env.error': 'Error',
    'env.subtitle':
      'Modifica cualquier parámetro <code>ASTER_*</code> sin reiniciar el servicio. Los cambios se guardan automáticamente.',
    'logs.activity.title': 'Feed de actividad',
    'logs.activity.subtitle': 'Operaciones clave, alertas y eventos de alta señal.',
    'logs.debug.title': 'Logs de depuración en tiempo real',
    'modals.decision.title': 'Motivo de la decisión de trading',
    'modals.trade.title': 'Detalles de la operación',
    'modals.pnl.title': 'Evolución del PNL',
    'modals.pnl.subtitle': 'Sigue el crecimiento del PNL realizado desde el inicio del bot.',
    'footer.note':
      'Diseñado para Aster: trading adaptable con total transparencia. Usa los logs en vivo y las notas de IA para optimizar tu estrategia con confianza.',
  },
  tr: {
    'language.english': 'İngilizce',
    'language.russian': 'Rusça',
    'language.chinese': 'Çince (Mandarin)',
    'language.german': 'Almanca',
    'language.french': 'Fransızca',
    'language.spanish': 'İspanyolca',
    'language.turkish': 'Türkçe',
    'language.korean': 'Korece',
    'language.switcher': 'Dili seç',
    'nav.menu': 'Bölümler',
    'nav.overview': 'Genel bakış',
    'nav.trades': 'İşlemler',
    'nav.playbook': 'Oyun planı',
    'nav.config': 'Yapılandırma',
    'nav.logs': 'Günlükler',
    'ticker.label': 'En çok işlem gören Coinler · İlk 20:',
    'ticker.empty': 'Piyasa liderleri toplanıyor…',
    'ticker.noData': 'Şu anda piyasa verisi yok.',
    'hero.badge': 'MrAster – Otonom trading paketi',
    'hero.heading': 'Yapay zekâ destekli otomasyonla her hareketi yakalayın.',
    'hero.description': 'Saniyeler içinde kripto botları çalıştırın, canlı telemetri yayınlayın ve Standard, Pro ve AI modlarında her işlemi şeffaf tutan yapay zekâ yardımcılarıyla stratejileri yeniden ayarlayın.',
    'hero.launch': 'Aster’ı aç',
    'hero.download': 'İşlemleri indir',
    'hero.share': 'X’te paylaş',
    'hero.metrics.trades': 'Toplam işlem',
    'hero.metrics.pnl': 'Toplam PNL',
    'hero.metrics.winrate': 'Genel kazanma oranı',
    'hero.metrics.volume': 'Toplam hacim',
    'hero.mode.label': 'Mod',
    'hero.mode.standard': 'Standart',
    'hero.mode.pro': 'Pro',
    'hero.mode.ai': 'AI',
    'hero.mode.paper': 'Demo modu etkinleştir',
    'active.title': 'Aktif pozisyonlar',
    'active.subtitle': 'Tüm modlardaki anlık pozisyon büyüklüğü.',
    'active.mode': 'Tüm modlar',
    'active.mode.paper': 'Demo modu',
    'active.mode.unrealized': 'Toplam gerçekleşmemiş PNL',
    'active.notifications.title': 'Pozisyon güncellemeleri',
    'active.notifications.subtitle': 'Anlık olarak açık pozisyonlara dair güncellemeler.',
    'active.notifications.empty': 'Henüz son yönetim olayları yok.',
    'active.empty': 'Aktif pozisyon yok.',
    'active.empty.paper': 'Henüz demo işlemi yok.',
    'active.notifications.closed': 'Pozisyon kapatıldı',
    'active.table.symbol': 'Sembol',
    'active.table.size': 'Büyüklük',
    'active.table.entry': 'Giriş fiyatı',
    'active.table.mark': 'Mark fiyatı',
    'active.table.leverage': 'Kaldıraç',
    'active.table.margin': 'Marj',
    'active.table.pnl': 'PNL (ROE%)',
    'active.management.fasttp': 'FastTP çıkışı ayarlandı',
    'active.management.breakeven': 'Zarar durdurma başabaşa taşındı',
    'active.management.trail': 'İz süren stop sıkılaştırıldı',
    'active.management.autoHalf': 'Otomatik kâr alma pozisyonu küçülttü',
    'active.management.scaleHalf': 'Kademeli azaltım uygulandı',
    'active.management.timeCut': 'Zamana bağlı azaltım uygulandı',
    'active.management.reduceOnly': 'Sadece azalt (reduce-only) emri gönderildi',
    'active.management.generic': 'Bot bu pozisyonu ayarladı',
    'active.management.justNow': 'az önce',
    'active.management.oneMinuteAgo': '1 dk önce',
    'active.management.minutesAgo': '{{value}} dk önce',
    'active.management.hoursAgo': '{{value}} sa önce',
    'active.management.daysAgo': '{{value}} g önce',
    'status.title': 'Durum',
    'status.state': 'Durum',
    'status.pid': 'PID',
    'status.started': 'Başlangıç',
    'status.uptime': 'Çalışma süresi',
    'status.indicator.running': 'Çalışıyor',
    'status.indicator.stopped': 'Durduruldu',
    'status.indicator.offline': 'Çevrimdışı',
    'status.aiBudget': 'AI bütçesi (günlük)',
    'status.aiBudget.standard': 'Standart',
    'status.aiBudget.pro': 'Pro modu',
    'status.aiBudget.paper': 'Demo modu',
    'status.aiBudgetMeta': 'Bütçe ayarlanmadı.',
    'status.aiBudgetMeta.disabled': 'AI modu devre dışı.',
    'status.aiBudgetMeta.unlimited': 'Günlük harcama {{spent}} USD · limit yok',
    'status.aiBudgetMeta.limited': 'Günlük harcama {{spent}} / {{limit}} USD · kalan {{remaining}} USD',
    'status.aiBudgetMeta.paper': 'Demo modu bütçe tüketmez.',
    'status.tradeDecisions': 'İşlem kararları',
    'status.decisions.accepted': 'Uygulanan:',
    'status.decisions.skipped': 'Atlanan:',
    'status.decisions.empty': 'Henüz işlem kararı yok.',
    'status.decisions.noneSkipped': 'Atlanan işlem kaydı yok.',
    'status.decisions.noneYet': 'Henüz işlem kararı yok.',
    'status.decisions.noReason': 'Bu gerekçeye ait işlem yok. Sonraki karardan sonra tekrar bakın.',
    'status.decisions.noReasonShort': 'Bu gerekçeye ait işlem yok.',
    'status.decisions.showDetails': 'Detayları göster',
    'status.decisions.hideDetails': 'Detayları gizle',
    'status.decisions.download': 'İndir',
    'status.decisions.exportError': 'Atlanan işlemler şu anda indirilemedi.',
    'credentials.title': 'Borsa anahtarları',
    'credentials.apiKey.label': 'ASTER_API_KEY',
    'credentials.apiKey.placeholder': 'API anahtarını girin',
    'credentials.apiSecret.label': 'ASTER_API_SECRET',
    'credentials.apiSecret.placeholder': 'Gizli anahtarı girin',
    'credentials.start': 'Başlat',
    'credentials.stop': 'Durdur',
    'credentials.save': 'Kaydet',
    'credentials.saving': 'Kaydediliyor…',
    'credentials.saved': 'Kaydedildi ✓',
    'credentials.error': 'Hata',
    'trades.title': 'İşlem geçmişi',
    'trades.subtitle': 'Son işlemler ve sonuç tek bakışta.',
    'trades.empty': 'Henüz işlem yok.',
    'trades.viewDetails': 'Detayları gör',
    'trades.summary.placeholder.label': 'Performans',
    'trades.summary.placeholder.value': 'Şimdilik veri yok',
    'trades.summary.hint': 'Yeni telemetri geldiğinde AI notu burada görünecek.',
    'trades.metric.trades': 'İşlemler',
    'trades.metric.totalPnl': 'Toplam PNL',
    'trades.metric.winRate': 'Kazanma oranı',
    'trades.metric.avgR': 'Ortalama R',
    'trades.postmortem.label': 'Post-mortem koçu',
    'trades.modal.noMetadata': 'Ek veri yok.',
    'trades.synthetic.badge': 'Gerçekleşen PnL',
    'trades.synthetic.note': 'Borsa gerçekleşen PnL akışından eşitlendi; giriş/çıkış fiyatları yok.',
    'trades.synthetic.incomeType': 'Gelir türü',
    'trades.synthetic.info': 'Borsa bilgisi',
    'trades.completed.title': 'Kapanan pozisyonlar',
    'trades.completed.subtitle': 'Pozisyon yöneticisinin kaydettiği çıkışlar.',
    'trades.completed.empty': 'Bot bir işlemi kapattığında burada görünecek.',
    'trades.completed.pnl': 'Gerçekleşen PNL',
    'trades.completed.reason': 'Çıkış nedeni',
    'trades.completed.noReason': 'Neden kaydedilmedi.',
    'pnl.title': 'PNL Gelişimi',
    'pnl.subtitle': 'Bot çalışmaya başladığından beri gerçekleşen PNL’in nasıl ilerlediğini izleyin.',
    'pnl.tradesWon': 'Kazanılan işlemler',
    'pnl.tradesLost': 'Kaybedilen işlemler',
    'pnl.metaLabel': 'Bot başlangıcından beri gerçekleşen PNL',
    'pnl.legendLabel': 'Kümülatif gerçekleşen PNL',
    'pnl.empty': 'Henüz PNL verisi yok. Grafiği doldurmak için işlem yapın.',
    'pnl.expandAria': 'Genişletilmiş performans grafiğini aç',
    'ai.feed.label': 'Otopilot',
    'ai.feed.title': 'Otonom strateji kokpiti',
    'ai.feed.subtitle': 'Burada strateji telemetrisi ve yapay zekânın otonom aksiyonları görünür. Sohbetler gösterge panosundaki ayrı bir sohbette yer alır.',
    'ai.feed.disabled': 'Aktivite akışını görmek için AI modunu açın.',
    'ai.feed.empty': 'Otonom kararlar gerçekleşir gerçekleşmez burada belirecek.',
    'ai.requests.title': 'YZ kararları',
    'ai.requests.subtitle': 'İşlem taleplerine ait en güncel YZ incelemeleri ve sonuçları.',
    'ai.requests.empty': 'YZ karar geçmişi burada görünecek.',
    'ai.requests.status.pending': 'Yanıt bekleniyor',
    'ai.requests.status.responded': 'Yanıt alındı',
    'ai.requests.status.accepted': 'Giriş onaylandı',
    'ai.requests.status.rejected': 'Giriş reddedildi',
    'ai.requests.status.analysed': 'Analiz tamamlandı',
    'ai.requests.status.decided': 'Karar kaydedildi',
    'ai.feed.reasonLabel': 'Gerekçe',
    'ai.feed.responseLabel': 'Son yanıt',
    'ai.feed.awaitingResponse': 'Yapay zekâ yanıtı bekleniyor…',
    'ai.feed.reason.plan_pending': 'Yapay zekâ planı talep edildi',
    'ai.feed.reason.plan_timeout': 'Yapay zekâ planı zamanında yanıt vermedi',
    'ai.feed.reason.trend_pending': 'Trend taraması talep edildi',
    'ai.feed.reason.trend_timeout': 'Trend taraması zamanında yanıt vermedi',
    'common.autoScroll': 'Otomatik kaydırma',
    'common.close': 'Kapat',
    'common.save': 'Kaydet',
    'common.saving': 'Kaydediliyor…',
    'common.saved': 'Kaydedildi ✓',
    'common.error': 'Hata',
    'common.expand': 'Genişlet',
    'common.collapse': 'Daralt',
    'common.analyze': 'Piyasayı analiz et',
    'chat.label': 'Gösterge paneli sohbeti',
    'chat.title': 'Strateji asistanı',
    'chat.subtitle': 'Trading asistanıyla ChatGPT tarzı bir çalışma alanında konuşun. Konsol için ayrı bir API anahtarı gerekir.',
    'chat.empty': 'Sohbete başlamak için gösterge paneli sohbeti API anahtarı ekleyin.',
    'chat.inputLabel': 'Strateji AI’ına sorun',
    'chat.placeholder': 'Asistanınıza bir mesaj gönderin…',
    'chat.analyze': 'Piyasayı analiz et',
    'chat.analyzing': 'Analiz ediliyor…',
    'chat.analyze.hint': 'Piyasa analizini açmak için AI ayarlarına bir OpenAI anahtarı ekleyin.',
    'chat.analyze.pending': 'Piyasa analizi yürütülüyor…',
    'chat.automation.toggle': 'Otomatikleştir',
    'chat.automation.interval': 'Aralık (dakika)',
    'chat.automation.nextRunLabel': 'Sonraki çalıştırma',
    'chat.automation.running': 'Otomasyon çalışıyor…',
    'chat.automation.scheduled': 'Otomatik döngü {{minutes}} dakika içinde planlandı.',
    'chat.automation.stopped': 'Otomasyon devre dışı bırakıldı.',
    'chat.automation.rescheduled': 'Otomasyon aralığı {{minutes}} dakikaya güncellendi.',
    'chat.send': 'Gönder',
    'chat.sending': 'Gönderiliyor…',
    'chat.status.analyzing': 'Piyasa analizi yapılıyor…',
    'chat.status.disabled': 'AI modu devre dışı.',
    'chat.status.keyRequired': 'OpenAI anahtarı gerekli.',
    'chat.status.fallback': 'Piyasa analizi (yedek mod).',
    'chat.status.ready': 'Piyasa analizi hazır.',
    'chat.status.failed': 'Piyasa analizi başarısız.',
    'chat.status.enableAi': 'Önce AI modunu açın.',
    'chat.status.emptyMessage': 'Bir mesaj yazın.',
    'chat.status.thinking': 'Strateji AI’ı düşünüyor…',
    'chat.status.error': 'Sohbet kullanılabilir değil.',
    'chat.placeholder.disabled': 'Gösterge paneli sohbetini kullanmak için AI modunu açın.',
    'chat.placeholder.key': 'Başlamak için AI ayarlarına bir OpenAI anahtarı ekleyin.',
    'chat.placeholder.prompt': 'Strateji asistanınıza işlemleriniz hakkında sorun.',
    'chat.analysis.none': 'Analiz alınamadı.',
    'chat.reply.none': 'Yanıt alınamadı.',
    'chat.key.ready': 'Sohbet anahtarı aktif.',
    'chat.role.analysis': 'Piyasa analizi',
    'ai.config.title': 'AI modunu yapılandır',
    'ai.config.subtitle': 'Botun işlemleri otonom yönetebilmesi için OpenAI anahtarlarını ve limitleri girin.',
    'ai.config.save': 'Kaydet',
    'ai.config.saving': 'Kaydediliyor…',
    'ai.config.saved': 'Kaydedildi ✓',
    'ai.config.error': 'Hata',
    'ai.config.access.title': 'Erişim',
    'ai.config.access.openai': 'OpenAI API anahtarı',
    'ai.config.access.openaiPlaceholder': 'sk-...',
    'ai.config.access.openaiHint': 'Yalnızca yerelde saklanır. Otonom yürütmeyi sağlar.',
    'ai.config.access.chat': 'Gösterge paneli sohbet anahtarı',
    'ai.config.access.chatPlaceholder': 'sk-...',
    'ai.config.access.chatHint': 'Bu ayrı OpenAI anahtarı sohbet için kullanılır ve trading isteklerinden ayrıdır. Kaydedilene kadar sohbet penceresi devre dışıdır.',
    'ai.config.budget.title': 'Günlük bütçe',
    'ai.config.budget.label': 'Günlük bütçe (USD)',
    'ai.config.budget.placeholder': '20',
    'ai.config.budget.hint': 'Yapay zekânın bütçe içinde kalması için harcama limiti belirleyin.',
    'ai.config.model.title': 'Model',
    'ai.config.model.label': 'Model',
    'ai.config.model.group.gpt5': 'GPT-5 serisi',
    'ai.config.model.group.gpt41': 'GPT-4.1 serisi',
    'ai.config.model.group.gpt4o': 'GPT-4o serisi',
    'ai.config.model.group.reasoning': 'Muhakeme modelleri',
    'ai.config.model.group.legacy': 'Eski modeller',
    'ai.config.model.hint': 'Gerçek zamanlı piyasa analizi için OpenAI modelini seçin.',
    'ai.config.baseline.title': 'Baz pozisyon',
    'ai.config.baseline.label': 'İşlem başına baz tutar (USDT)',
    'ai.config.baseline.placeholder': '250',
    'ai.config.baseline.hint': '<code>ASTER_DEFAULT_NOTIONAL</code> değerini tanımlar: risk çarpanları uygulanmadan önce AI’nın referans aldığı minimum USDT tutarı.',
    'ai.config.footer': 'AI modu açıkken strateji motoru, günlük bütçeyi aşmadan pozisyon boyutu, kaldıraç, stoplar ve FastTP’yi sürekli ayarlar.',
    'quick.title': 'Strateji hızlı başlatma',
    'quick.subtitle': 'Bir preset seçin, riski ve kaldıraçı rahatınıza göre ayarlayın.',
    'quick.apply': 'Preseti uygula',
    'quick.applyChanges': 'Değişiklikleri uygula',
    'quick.applyProgress': 'Uygulanıyor…',
    'quick.applyRestarting': 'Yeniden başlatılıyor…',
    'quick.applySuccess': 'Uygulandı ✓',
    'quick.applyRestarted': 'Yeniden başlatıldı ✓',
    'quick.applyError': 'Hata',
    'quick.presets.low.title': 'Low',
    'quick.presets.low.subtitle': 'Düşük frekans · İşlem başına %30 risk · %33 sermaye',
    'quick.presets.mid.title': 'Mid',
    'quick.presets.mid.subtitle': 'Dengeli trading · İşlem başına %50 risk · %66 sermaye',
    'quick.presets.high.title': 'High',
    'quick.presets.high.subtitle': 'Yüksek frekans · Agresif · İşlem başına %100 risk',
    'quick.presets.att.title': 'ATT',
    'quick.presets.att.subtitle': 'Trend karşıtı kurulum',
    'quick.leverage.title': 'Kaldıraç',
    'quick.leverage.placeholder': 'Temel kaldıraç: –',
    'quick.notional.title': 'Pozisyon aralığı',
    'quick.notional.details': 'Uyarlanabilir pozisyon aralığı: {{min}} – {{max}} işlem başına.',
    'quick.notional.unlimited': 'hesap sermayesi',
    'quick.description': 'Önerilen risk parametrelerini yüklemek için bir profil seçin.',
    'quick.risk.label': 'İşlem başına risk',
    'quick.risk.aria': 'İşlem başına risk (%)',
    'quick.risk.min': '%0,25',
    'quick.risk.max': '%100',
    'quick.leverage.label': 'Kaldıraç',
    'quick.leverage.aria': 'Kaldıraç çarpanı',
    'quick.leverage.min': '1×',
    'quick.leverage.max': 'En fazla 25×',
    'quick.baseline.label': 'İşlem başına baz tutar (USDT)',
    'quick.baseline.placeholder': '250',
    'quick.baseline.unit': 'USDT',
    'quick.baseline.hint': '<code>ASTER_DEFAULT_NOTIONAL</code> değerini belirler — bot risk kuralları uygulanmadan önce her işlem için ayırdığı baz pozisyon.',
    'quick.funding.title': 'Funding filtreleri',
    'quick.funding.details': 'Funding kontrolleri seçilen presete göre değişir.',
    'quick.ml.title': 'ML politikası',
    'quick.ml.empty': 'ML politikasını görmek için bir preset yükleyin.',
    'quick.ml.none': 'Bu preset için ML açıklaması yok.',
    'env.title': 'Ortam yapılandırması',
    'env.expand': 'Genişlet',
    'env.collapse': 'Daralt',
    'env.save': 'Kaydet',
    'env.saving': 'Kaydediliyor…',
    'env.saved': 'Kaydedildi ✓',
    'env.error': 'Hata',
    'env.subtitle': 'Servisi yeniden başlatmadan herhangi bir <code>ASTER_*</code> parametresini değiştirin. Değişiklikler otomatik kaydedilir.',
    'logs.activity.title': 'Aktivite akışı',
    'logs.activity.subtitle': 'Kilit işlemler, uyarılar ve yüksek sinyal olayları.',
    'logs.debug.title': 'Gerçek zamanlı debug logları',
    'modals.decision.title': 'İşlem kararının nedeni',
    'modals.trade.title': 'İşlem detayları',
    'modals.pnl.title': 'PNL Gelişimi',
    'modals.pnl.subtitle': 'Bot çalışmaya başladığından beri gerçekleşen PNL’in nasıl ilerlediğini izleyin.',
    'footer.note': 'Aster için tasarlandı — tam şeffaflıkla uyarlanabilir trading. Stratejinizi güvenle geliştirmek için canlı logları ve AI ipuçlarını kullanın.',
  },

  zh: {
    'language.english': '英语',
    'language.russian': '俄语',
    'language.chinese': '中文（普通话）',
    'language.german': '德语',
    'language.french': '法语',
    'language.spanish': '西班牙语',
    'language.turkish': '土耳其语',
    'language.korean': '韩语',
    'language.switcher': '选择语言',
    'nav.menu': '模块',
    'nav.overview': '概览',
    'nav.trades': '交易',
    'nav.playbook': '策略手册',
    'nav.config': '配置',
    'nav.logs': '日志',
    'ticker.label': '最热门交易币种 · 前 20 名：',
    'ticker.empty': '正在收集市场领头羊…',
    'ticker.noData': '当前没有市场数据。',
    'hero.badge': 'MrAster – 自动化交易套件',
    'hero.heading': '借助 AI 调优的自动化把握每一次行情波动。',
    'hero.description':
      '几秒内部署加密货币机器人，实时串流遥测，并依靠 AI 副驾在 Standard、Pro 和 AI 模式下保持每一次执行的全程透明。',
    'hero.launch': '启动 Aster',
    'hero.download': '下载成交记录',
    'hero.share': '在 X 上分享',
    'hero.metrics.trades': '总成交数',
    'hero.metrics.pnl': '总盈亏',
    'hero.metrics.winrate': '总体胜率',
    'hero.metrics.volume': '总成交量',
    'hero.mode.label': '模式',
    'hero.mode.standard': '标准',
    'hero.mode.pro': '专业',
    'hero.mode.ai': 'AI',
    'hero.mode.paper': '启用模拟模式',
    'active.title': '当前持仓',
    'active.subtitle': '所有模式下的实时敞口。',
    'active.mode': '全部模式',
    'active.mode.paper': '模拟模式',
    'active.mode.unrealized': '总未实现PNL',
    'active.notifications.title': '仓位更新',
    'active.notifications.subtitle': '实时呈现当前持仓的更新动态。',
    'active.notifications.empty': '暂无最新的风控更新。',
    'active.empty': '暂无持仓。',
    'active.empty.paper': '模拟交易尚未产生。',
    'active.notifications.closed': '仓位已平仓',
    'active.table.symbol': '交易对',
    'active.table.size': '仓位规模',
    'active.table.entry': '开仓价',
    'active.table.mark': '标记价格',
    'active.table.leverage': '杠杆',
    'active.table.margin': '保证金',
    'active.table.pnl': '盈亏 (ROE%)',
    'active.management.fasttp': 'FastTP 平仓已调整',
    'active.management.breakeven': '止损已移到保本位',
    'active.management.trail': '追踪止损已收紧',
    'active.management.autoHalf': '自动止盈已缩减仓位',
    'active.management.scaleHalf': '慢速减仓已执行',
    'active.management.timeCut': '按时间减仓已执行',
    'active.management.reduceOnly': '已下达仅减仓委托',
    'active.management.generic': '机器人已调整此仓位',
    'active.management.justNow': '刚刚',
    'active.management.oneMinuteAgo': '1 分钟前',
    'active.management.minutesAgo': '{{value}} 分钟前',
    'active.management.hoursAgo': '{{value}} 小时前',
    'active.management.daysAgo': '{{value}} 天前',
    'status.title': '状态',
    'status.state': '运行状态',
    'status.pid': 'PID',
    'status.started': '启动时间',
    'status.uptime': '运行时长',
    'status.indicator.running': '运行中',
    'status.indicator.stopped': '已停止',
    'status.indicator.offline': '离线',
    'status.aiBudget': 'AI 预算（每日）',
    'status.aiBudget.standard': '标准',
    'status.aiBudget.pro': '专业模式',
    'status.aiBudget.paper': '模拟模式',
    'status.aiBudgetMeta': '尚未配置预算。',
    'status.aiBudgetMeta.disabled': 'AI 模式已关闭。',
    'status.aiBudgetMeta.unlimited': '当日已使用 {{spent}} USD · 无上限',
    'status.aiBudgetMeta.limited': '当日已使用 {{spent}} / {{limit}} USD · 剩余 {{remaining}} USD',
    'status.aiBudgetMeta.paper': '模拟模式不会消耗预算。',
    'status.tradeDecisions': '交易决策',
    'status.decisions.accepted': '已执行：',
    'status.decisions.skipped': '已跳过：',
    'status.decisions.empty': '暂时还没有交易决策。',
    'status.decisions.noneSkipped': '尚未记录被跳过的交易。',
    'status.decisions.noneYet': '暂时还没有交易决策。',
    'status.decisions.noReason': '此原因下暂未出现交易。请在下一次决策后再查看。',
    'status.decisions.noReasonShort': '此原因下暂未出现交易。',
    'status.decisions.showDetails': '显示详情',
    'status.decisions.hideDetails': '隐藏详情',
    'status.decisions.download': '下载',
    'status.decisions.exportError': '当前无法下载被跳过的交易。',
    'credentials.title': '交易所凭证',
    'credentials.apiKey.label': 'ASTER_API_KEY',
    'credentials.apiKey.placeholder': '输入 API 密钥',
    'credentials.apiSecret.label': 'ASTER_API_SECRET',
    'credentials.apiSecret.placeholder': '输入私钥',
    'credentials.start': '启动',
    'credentials.stop': '停止',
    'credentials.save': '保存',
    'credentials.saving': '正在保存…',
    'credentials.saved': '已保存 ✓',
    'credentials.error': '错误',
    'trades.title': '交易历史',
    'trades.subtitle': '最新成交与结果一目了然。',
    'trades.empty': '暂时没有交易。',
    'trades.viewDetails': '查看详情',
    'trades.summary.placeholder.label': '表现',
    'trades.summary.placeholder.value': '暂无数据',
    'trades.summary.hint': '一旦出现新的遥测数据，AI 提示会在此显示。',
    'trades.metric.trades': '交易次数',
    'trades.metric.totalPnl': '总盈亏',
    'trades.metric.winRate': '胜率',
    'trades.metric.avgR': '平均 R 值',
    'trades.postmortem.label': '复盘教练',
    'trades.modal.noMetadata': '没有更多补充数据。',
    'trades.synthetic.badge': '已实现 PnL',
    'trades.synthetic.note': '来自交易所已实现 PnL 数据，缺少进出场价格。',
    'trades.synthetic.incomeType': '收益类型',
    'trades.synthetic.info': '交易所信息',
    'trades.completed.title': '已完成仓位',
    'trades.completed.subtitle': '来自仓位管理器的平仓记录。',
    'trades.completed.empty': '机器人下一次平仓后会显示在这里。',
    'trades.completed.pnl': '已实现PNL',
    'trades.completed.reason': '离场原因',
    'trades.completed.noReason': '未记录原因。',
    'pnl.title': 'PNL 走势',
    'pnl.subtitle': '跟踪机器人启动以来的已实现 PNL 变化。',
    'pnl.tradesWon': '盈利笔数',
    'pnl.tradesLost': '亏损笔数',
    'pnl.metaLabel': '机器人启动以来的已实现 PNL',
    'pnl.legendLabel': '累计已实现 PNL',
    'pnl.empty': '尚无盈亏数据。完成交易后即可生成图表。',
    'pnl.expandAria': '打开绩效图表的扩展视图',
    'ai.feed.label': '自动播报',
    'ai.feed.title': '自主策略驾驶舱',
    'ai.feed.subtitle': '此处显示策略遥测与 AI 自主操作。聊天内容被放在仪表盘单独的聊天区。',
    'ai.feed.disabled': '开启 AI 模式后即可查看活动信息流。',
    'ai.feed.empty': '自主决策会在事件发生时实时显示在此处。',
    'ai.requests.title': 'AI 决策',
    'ai.requests.subtitle': '展示策略副驾对交易请求的最新审核与结果。',
    'ai.requests.empty': 'AI 决策记录会显示在这里。',
    'ai.requests.status.pending': '等待回复',
    'ai.requests.status.responded': '已收到回复',
    'ai.requests.status.accepted': '准许入场',
    'ai.requests.status.rejected': '拒绝入场',
    'ai.requests.status.analysed': '分析完成',
    'ai.requests.status.decided': '决策已记录',
    'ai.feed.reasonLabel': '原因',
    'ai.feed.responseLabel': '最新回复',
    'ai.feed.awaitingResponse': '等待 AI 回复…',
    'ai.feed.reason.plan_pending': '已请求 AI 计划',
    'ai.feed.reason.plan_timeout': 'AI 计划响应超时',
    'ai.feed.reason.trend_pending': '已请求趋势扫描',
    'ai.feed.reason.trend_timeout': '趋势扫描响应超时',
    'common.autoScroll': '自动滚动',
    'common.close': '关闭',
    'common.save': '保存',
    'common.saving': '正在保存…',
    'common.saved': '已保存 ✓',
    'common.error': '错误',
    'common.expand': '展开',
    'common.collapse': '收起',
    'common.analyze': '市场分析',
    'chat.label': '仪表盘聊天',
    'chat.title': '策略助手',
    'chat.subtitle': '与交易助手在 ChatGPT 风格的工作区交流。控制台需单独的 API 密钥。',
    'chat.empty': '请提供仪表盘聊天的 API 密钥以开始对话。',
    'chat.inputLabel': '向策略 AI 提问',
    'chat.placeholder': '给您的助手发送消息…',
    'chat.analyze': '市场分析',
    'chat.analyzing': '正在分析…',
    'chat.analyze.hint': '在 AI 设置中添加 OpenAI 密钥即可启用市场分析。',
    'chat.analyze.pending': '市场分析执行中…',
    'chat.automation.toggle': '自动执行',
    'chat.automation.interval': '间隔（分钟）',
    'chat.automation.nextRunLabel': '下次运行还剩',
    'chat.automation.running': '正在自动执行…',
    'chat.automation.scheduled': '自动循环将在 {{minutes}} 分钟后运行。',
    'chat.automation.stopped': '自动执行已关闭。',
    'chat.automation.rescheduled': '自动执行间隔更新为 {{minutes}} 分钟。',
    'chat.send': '发送',
    'chat.sending': '正在发送…',
    'chat.status.analyzing': '市场分析中…',
    'chat.status.disabled': 'AI 模式已关闭。',
    'chat.status.keyRequired': '需要 OpenAI 密钥。',
    'chat.status.fallback': '市场分析（备用模式）。',
    'chat.status.ready': '市场分析就绪。',
    'chat.status.failed': '市场分析失败。',
    'chat.status.enableAi': '请先开启 AI 模式。',
    'chat.status.emptyMessage': '请输入消息。',
    'chat.status.thinking': '策略 AI 正在思考…',
    'chat.status.error': '聊天不可用。',
    'chat.placeholder.disabled': '启用 AI 模式即可使用仪表盘聊天。',
    'chat.placeholder.key': '在 AI 设置中添加 OpenAI 密钥即可开始对话。',
    'chat.placeholder.prompt': '向策略助手询问您的交易情况。',
    'chat.analysis.none': '未获取到分析。',
    'chat.reply.none': '未收到回复。',
    'chat.key.ready': '聊天密钥已激活。',
    'chat.role.analysis': '市场分析',
    'ai.config.title': 'AI 模式设置',
    'ai.config.subtitle': '配置 OpenAI 密钥与限制，让机器人可以自主管理交易。',
    'ai.config.save': '保存',
    'ai.config.saving': '正在保存…',
    'ai.config.saved': '已保存 ✓',
    'ai.config.error': '错误',
    'ai.config.access.title': '访问',
    'ai.config.access.openai': 'OpenAI API 密钥',
    'ai.config.access.openaiPlaceholder': 'sk-...',
    'ai.config.access.openaiHint': '仅保存在本地。用于自主执行交易。',
    'ai.config.access.chat': '仪表盘聊天密钥',
    'ai.config.access.chatPlaceholder': 'sk-...',
    'ai.config.access.chatHint': '该独立的 OpenAI 密钥用于聊天，并隔离交易请求。保存之前聊天窗口保持禁用。',
    'ai.config.budget.title': '每日预算',
    'ai.config.budget.label': '每日预算 (USD)',
    'ai.config.budget.placeholder': '20',
    'ai.config.budget.hint': '设置 AI 花费上限，让自主控制始终在预算之内。',
    'ai.config.model.title': '模型',
    'ai.config.model.label': '模型',
    'ai.config.model.group.gpt5': 'GPT-5 系列',
    'ai.config.model.group.gpt41': 'GPT-4.1 系列',
    'ai.config.model.group.gpt4o': 'GPT-4o 系列',
    'ai.config.model.group.reasoning': '推理模型',
    'ai.config.model.group.legacy': '旧版模型',
    'ai.config.model.hint': '选择用于实时市场分析的 OpenAI 模型。',
    'ai.config.baseline.title': '基础仓位',
    'ai.config.baseline.label': '每笔基础仓位 (USDT)',
    'ai.config.baseline.placeholder': '250',
    'ai.config.baseline.hint':
      '对应 <code>ASTER_DEFAULT_NOTIONAL</code>：AI 在风险乘数与约束之前参考的最低 USDT 数量。',
    'ai.config.footer':
      '当 AI 模式开启时，策略引擎会在遵守每日预算的前提下持续调节仓位大小、杠杆、止损和 FastTP。',
    'quick.title': '策略快速启动',
    'quick.subtitle': '选择预设并按您的偏好调整风险与杠杆。',
    'quick.apply': '应用预设',
    'quick.applyChanges': '应用更改',
    'quick.applyProgress': '正在应用…',
    'quick.applyRestarting': '正在重启…',
    'quick.applySuccess': '已应用 ✓',
    'quick.applyRestarted': '已重启 ✓',
    'quick.applyError': '错误',
    'quick.presets.low.title': 'Low',
    'quick.presets.low.subtitle': '低频交易 · 单笔风险 30% · 33% 资金占用',
    'quick.presets.mid.title': 'Mid',
    'quick.presets.mid.subtitle': '均衡交易 · 单笔风险 50% · 66% 资金占用',
    'quick.presets.high.title': 'High',
    'quick.presets.high.subtitle': '高频 · 进取 · 单笔风险 100%',
    'quick.presets.att.title': 'ATT',
    'quick.presets.att.subtitle': '逆势策略',
    'quick.leverage.title': '杠杆',
    'quick.leverage.placeholder': '基础杠杆：–',
    'quick.notional.title': '仓位范围',
    'quick.notional.details': '自适应仓位范围：每笔交易 {{min}} – {{max}}。',
    'quick.notional.unlimited': '账户权益',
    'quick.description': '选择一个配置以载入推荐的风险参数。',
    'quick.risk.label': '单笔风险',
    'quick.risk.aria': '单笔风险 (%)',
    'quick.risk.min': '0.25%',
    'quick.risk.max': '100%',
    'quick.leverage.label': '杠杆',
    'quick.leverage.aria': '杠杆倍数',
    'quick.leverage.min': '1×',
    'quick.leverage.max': '最高 25×',
    'quick.baseline.label': '每笔基础下注 (USDT)',
    'quick.baseline.placeholder': '250',
    'quick.baseline.unit': 'USDT',
    'quick.baseline.hint': '设置 <code>ASTER_DEFAULT_NOTIONAL</code> —— 在风险约束之前机器人为每笔交易预留的基础仓位。',
    'quick.funding.title': '资金费过滤器',
    'quick.funding.details': '资金费控制取决于所选预设。',
    'quick.ml.title': 'ML 策略',
    'quick.ml.empty': '载入预设后会显示 ML 策略细节。',
    'quick.ml.none': '该预设没有 ML 策略说明。',
    'env.title': '环境配置',
    'env.expand': '展开',
    'env.collapse': '收起',
    'env.save': '保存',
    'env.saving': '正在保存…',
    'env.saved': '已保存 ✓',
    'env.error': '错误',
    'env.subtitle': '无需重启服务即可修改任意 <code>ASTER_*</code> 参数。更改会自动保存。',
    'logs.activity.title': '活动信息流',
    'logs.activity.subtitle': '关键交易、预警和高信号事件。',
    'logs.debug.title': '实时调试日志',
    'modals.decision.title': '交易决策原因',
    'modals.trade.title': '交易详情',
    'modals.pnl.title': 'PNL 走势',
    'modals.pnl.subtitle': '跟踪机器人启动以来的已实现 PNL 变化。',
    'footer.note': '为 Aster 打造——自适应交易并保持完全透明。利用实时日志和 AI 提示，自信地优化策略。',
  },
};

let currentLanguage = DEFAULT_LANGUAGE;
const i18nRegistry = Array.from(i18nElements).map((element) => {
  const key = element.dataset.i18n;
  const attr = element.dataset.i18nAttr || null;
  if (!key) {
    return null;
  }
  const defaultValue = attr ? element.getAttribute(attr) ?? '' : element.innerHTML ?? '';
  if (attr) {
    element.dataset.i18nDefaultAttr = defaultValue;
  } else {
    element.dataset.i18nDefault = defaultValue;
  }
  return { element, key, attr };
}).filter(Boolean);

let currentConfig = {};
let reconnectTimer = null;
let activePositionsStreamReconnectTimer = null;
let pnlChart = null;
let pnlChartExpanded = null;
let proMode = false;
let aiMode = false;
let paperMode = false;
let selectedPreset = 'mid';
let autoScrollEnabled = true;
let compactSkipAggregate = null;
let quickConfigPristine = true;
let envCollapsed = true;
let mostTradedTimer = null;
let lastAiBudget = null;
let lastMostTradedAssets = [];
let latestTradesSnapshot = null;
let lastTradeStats = null;
let lastBotStatus = { ...DEFAULT_BOT_STATUS };
let statusHydrated = false;
let tradesHydrated = false;
let tradesRefreshInFlight = null;
let aiChatHistory = [];
let aiChatPending = false;
let aiAnalyzePending = false;
let activePositions = [];
let activePositionSymbols = new Set();
let tradeHistoryEmptyStreak = 0;
let aiRequestsEmptyStreak = 0;
const POSITION_NOTIFICATION_HISTORY_LIMIT = 15;
const MANAGEMENT_EXIT_REASON_KEYS = [
  'management_exit_reason',
  'managementExitReason',
  'exit_reason',
  'exitReason',
];
const MANAGEMENT_BLOCK_EXIT_REASON_KEYS = ['exit_reason', 'exitReason', 'last_reason', 'lastReason', 'reason'];
const MANAGEMENT_EXIT_HINT_KEYS = [
  'expected_r_stop_hit',
  'expected_r_stop',
  'breakeven_guard',
  'breakeven',
  'trail',
  'fasttp_exit',
  'fasttp',
  'auto_half_take_profit',
  'time_cut',
  'time_stop',
  'compression_time_cut',
  'compression_scale_down',
  'scale_half',
];
let positionNotificationHistory = [];
let completedPositionsHistory = [];
const completedPositionsIndex = new Map();
let positionUpdatesRefreshTimer = null;
let tradesRefreshTimer = null;
let tradeViewportSyncHandle = null;
let lastDecisionStats = null;
const aiChatSubmit = aiChatForm ? aiChatForm.querySelector('button[type="submit"]') : null;
let analyzeButtonDefaultLabel = btnAnalyzeMarket ? btnAnalyzeMarket.textContent : 'Analyze Market';
let takeProposalsButtonDefaultLabel = getDefaultTakeProposalsLabel();
let lastPnlChartPayload = null;
let pnlModalHideTimer = null;
let pnlModalFinalizeHandler = null;
let pnlModalReturnTarget = null;
let tradeModalHideTimer = null;
let tradeModalFinalizeHandler = null;
let tradeModalReturnTarget = null;
let aiRequestModalHideTimer = null;
let aiRequestModalFinalizeHandler = null;
let aiRequestModalReturnTarget = null;
let playbookModalHideTimer = null;
let playbookModalFinalizeHandler = null;
let playbookModalReturnTarget = null;
let decisionModalHideTimer = null;
let decisionModalFinalizeHandler = null;
let decisionModalReturnTarget = null;
let decisionReasonsExpanded = false;
let decisionReasonsAvailable = false;
let automationActive = false;
let automationTimeoutId = null;
let automationCountdownIntervalId = null;
let automationTargetTimestamp = null;
let lastModeBeforeStandard = null;
const decisionReasonEvents = new Map();
const DECISION_REASON_EVENT_LIMIT = 40;
let pendingPlaybookResponseCount = 0;
let lastPlaybookState = null;
let lastPlaybookActivity = [];
let lastPlaybookProcess = [];
let lastPlaybookMarketOverview = null;
const tradeProposalRegistry = new Map();
const fallbackProposalKeys = new Map();
let fallbackProposalCounter = 0;
let automatedExecutionTimer = null;
let automatedExecutionInFlight = false;
let automationCycleInProgress = false;
let heroMetricsSnapshot = {
  totalTrades: 0,
  totalPnl: 0,
  totalPnlDisplay: '0 USDT',
  realizedPnl: 0,
  aiBudgetSpent: 0,
  winRate: 0,
  winRateDisplay: '0.0%',
};
const NEAR_MISS_COLLECTION_WINDOW_MS = 5 * 60 * 1000;
const NEAR_MISS_REFRESH_INTERVAL_MS = 5000;
let nearMissEntries = [];
let nearMissReadyAt = Date.now() + NEAR_MISS_COLLECTION_WINDOW_MS;
let nearMissRenderTimer = null;
let nearMissLastRenderedAt = null;

function formatTemplate(template, replacements = {}) {
  if (typeof template !== 'string') {
    return template;
  }
  return Object.keys(replacements).reduce((acc, key) => {
    const value = replacements[key];
    const pattern = new RegExp(`{{\\s*${key}\\s*}}`, 'g');
    return acc.replace(pattern, value);
  }, template);
}

function translate(key, fallback, replacements = {}, lang = currentLanguage) {
  const pack = TRANSLATIONS[lang] || {};
  let template = pack[key];
  if (template === undefined) {
    if (lang !== DEFAULT_LANGUAGE) {
      return translate(key, fallback, replacements, DEFAULT_LANGUAGE);
    }
    template = fallback !== undefined ? fallback : key;
  }
  return formatTemplate(template, replacements);
}

function getDefaultValueForEntry(entry) {
  if (entry.attr) {
    return entry.element.dataset.i18nDefaultAttr ?? '';
  }
  return entry.element.dataset.i18nDefault ?? '';
}

function applyTranslations(lang) {
  const targetLang = SUPPORTED_LANGUAGES.includes(lang) ? lang : DEFAULT_LANGUAGE;
  currentLanguage = targetLang;
  const htmlLang = targetLang === DEFAULT_LANGUAGE ? 'en' : targetLang;
  document.documentElement.setAttribute('lang', htmlLang);
  i18nRegistry.forEach((entry) => {
    const fallback = getDefaultValueForEntry(entry);
    const value = targetLang === DEFAULT_LANGUAGE ? fallback : translate(entry.key, fallback, {}, targetLang);
    if (entry.attr) {
      entry.element.setAttribute(entry.attr, value);
    } else {
      entry.element.innerHTML = value;
    }
  });
  updateLanguageButtonsState();
  refreshEnvironmentToggleLabels();
  analyzeButtonDefaultLabel = translate('chat.analyze', getDefaultAnalyzeLabel(), {}, targetLang);
  if (btnAnalyzeMarket) {
    btnAnalyzeMarket.textContent = aiAnalyzePending
      ? translate('chat.analyzing', 'Analyzing…')
      : analyzeButtonDefaultLabel;
  }
  takeProposalsButtonDefaultLabel = translate(
    'chat.proposal.takeAll',
    getDefaultTakeProposalsLabel(),
    {},
    targetLang
  );
  updateTakeProposalsButtonState();
  updateAutomationCountdownDisplay();
  updateModeButtons();
  updateAiBudgetModeLabel();
  updateActivePositionsView();
  renderTradeSummary(lastTradeStats, latestTradesSnapshot?.history_summary);
  renderDecisionStats(lastDecisionStats);
  renderNearMissList(true);
  renderAiBudget(lastAiBudget);
  if (latestTradesSnapshot) {
    renderHeroMetrics(
      latestTradesSnapshot.cumulative_stats,
      latestTradesSnapshot.stats,
      latestTradesSnapshot.history,
      latestTradesSnapshot.hero_metrics,
      latestTradesSnapshot.open ?? latestTradesSnapshot.open_positions ?? null,
      latestTradesSnapshot.history_summary,
    );
  }
  if (btnSaveConfig) {
    const state = btnSaveConfig.dataset.state || 'idle';
    if (state === 'saving') {
      btnSaveConfig.textContent = translate('common.saving', 'Saving…');
    } else if (state === 'saved') {
      btnSaveConfig.textContent = translate('common.saved', 'Saved ✓');
    } else if (state === 'error') {
      btnSaveConfig.textContent = translate('common.error', 'Error');
    } else {
      btnSaveConfig.textContent = translate('env.save', 'Save');
    }
  }
  if (btnSaveCredentials) {
    const state = btnSaveCredentials.dataset.state || 'idle';
    if (state === 'saving') {
      btnSaveCredentials.textContent = translate('common.saving', 'Saving…');
    } else if (state === 'saved') {
      btnSaveCredentials.textContent = translate('common.saved', 'Saved ✓');
    } else if (state === 'error') {
      btnSaveCredentials.textContent = translate('common.error', 'Error');
    } else {
      btnSaveCredentials.textContent = translate('credentials.save', 'Save');
    }
  }
  if (btnSaveAi) {
    const state = btnSaveAi.dataset.state || 'idle';
    if (state === 'saving') {
      btnSaveAi.textContent = translate('common.saving', 'Saving…');
    } else if (state === 'saved') {
      btnSaveAi.textContent = translate('common.saved', 'Saved ✓');
    } else if (state === 'error') {
      btnSaveAi.textContent = translate('common.error', 'Error');
    } else {
      btnSaveAi.textContent = translate('ai.config.save', 'Save');
    }
  }
  if (btnApplyPreset) {
    const state = btnApplyPreset.dataset.state || 'idle';
    switch (state) {
      case 'applying':
        btnApplyPreset.textContent = translate('quick.applyProgress', 'Applying…');
        break;
      case 'restarting':
        btnApplyPreset.textContent = translate('quick.applyRestarting', 'Restarting…');
        break;
      case 'restarted':
        btnApplyPreset.textContent = translate('quick.applyRestarted', 'Restarted ✓');
        break;
      case 'applied':
        btnApplyPreset.textContent = translate('quick.applySuccess', 'Applied ✓');
        break;
      case 'error':
        btnApplyPreset.textContent = translate('quick.applyError', 'Error');
        break;
      case 'dirty':
        btnApplyPreset.textContent = translate('quick.applyChanges', 'Apply changes');
        break;
      default:
        btnApplyPreset.textContent = translate('quick.apply', 'Apply preset');
        break;
    }
  }
  syncAiChatAvailability();
}

function getDefaultAnalyzeLabel() {
  if (!btnAnalyzeMarket) return 'Analyze Market';
  const fallback = btnAnalyzeMarket.dataset.i18nDefault || btnAnalyzeMarket.textContent || 'Analyze Market';
  return fallback.trim() ? fallback : 'Analyze Market';
}

function getDefaultTakeProposalsLabel() {
  if (!btnTakeTradeProposals) return 'Take trade proposals';
  const fallback =
    btnTakeTradeProposals.dataset.i18nDefault ||
    btnTakeTradeProposals.textContent ||
    'Take trade proposals';
  const trimmed = fallback.trim();
  return trimmed ? trimmed : 'Take trade proposals';
}

function getTakeProposalsWorkingLabel() {
  return translate('chat.proposal.takeAll.pending', 'Queuing trade proposals…');
}

function getTakeProposalsHintLabel() {
  return translate(
    'chat.proposal.takeAll.hint',
    'Ask the strategy AI to analyze the market to receive proposals.'
  );
}

function getTakeProposalsSuccessLabel() {
  return translate(
    'chat.proposal.takeAll.success',
    'All available trade proposals have been queued for execution.'
  );
}

function getTakeProposalsEmptyLabel() {
  return translate(
    'chat.proposal.takeAll.empty',
    'No trade proposals are waiting for execution.'
  );
}

function parseProposalTimestamp(candidate) {
  if (candidate === null || candidate === undefined) {
    return null;
  }
  if (typeof candidate === 'number') {
    return Number.isFinite(candidate) ? candidate : null;
  }
  if (typeof candidate === 'string') {
    const trimmed = candidate.trim();
    if (!trimmed) {
      return null;
    }
    const numeric = Number(trimmed);
    if (Number.isFinite(numeric)) {
      return numeric;
    }
    const parsedDate = Date.parse(trimmed);
    if (!Number.isNaN(parsedDate)) {
      return parsedDate;
    }
  }
  return null;
}

function buildProposalFingerprint(raw) {
  if (!raw || typeof raw !== 'object') {
    return null;
  }
  try {
    const omitKeys = new Set([
      'id',
      'proposal_id',
      'proposalId',
      'uuid',
      'uid',
      'external_id',
      'trade_id',
    ]);
    const payload = {};
    Object.keys(raw)
      .filter((key) => !omitKeys.has(key))
      .sort()
      .forEach((key) => {
        payload[key] = raw[key];
      });
    return JSON.stringify(payload);
  } catch (err) {
    console.warn('Unable to build proposal fingerprint', err);
    return null;
  }
}

function normalizeTradeProposal(data) {
  if (!data || typeof data !== 'object') {
    return null;
  }
  const normalized = { ...data };
  const idCandidates = [
    normalized.id,
    normalized.proposal_id,
    normalized.proposalId,
    normalized.uuid,
    normalized.uid,
    normalized.external_id,
    normalized.trade_id,
  ]
    .map((value) => {
      if (value === null || value === undefined) {
        return '';
      }
      return value.toString().trim();
    })
    .filter(Boolean);
  if (idCandidates.length > 0) {
    normalized.id = idCandidates[0];
    return normalized;
  }

  const fingerprint = buildProposalFingerprint(normalized);
  if (fingerprint && fallbackProposalKeys.has(fingerprint)) {
    normalized.id = fallbackProposalKeys.get(fingerprint);
    return normalized;
  }

  const symbol = (normalized.symbol || '').toString().trim().toUpperCase();
  const direction = (normalized.direction || '').toString().trim().toUpperCase();
  const entryKind = (normalized.entry_kind || '').toString().trim().toLowerCase();
  const tsCandidates = [
    normalized.ts,
    normalized.timestamp,
    normalized.generated_at,
    normalized.generatedAt,
    normalized.created_at,
    normalized.createdAt,
    normalized.updated_at,
    normalized.updatedAt,
  ];
  let ts = null;
  for (const candidate of tsCandidates) {
    const parsed = parseProposalTimestamp(candidate);
    if (parsed !== null) {
      ts = parsed;
      break;
    }
  }
  if (ts === null) {
    ts = Date.now();
  }
  fallbackProposalCounter += 1;
  const suffix = `${ts}-${fallbackProposalCounter}`;
  const parts = ['auto'];
  parts.push(symbol || 'trade');
  parts.push(direction || 'idea');
  if (entryKind) {
    parts.push(entryKind);
  }
  normalized.id = `${parts.join('-')}-${suffix}`;
  if (fingerprint) {
    fallbackProposalKeys.set(fingerprint, normalized.id);
  }
  return normalized;
}

function registerTradeProposal(data) {
  const normalized = normalizeTradeProposal(data);
  if (!normalized || !normalized.id) return null;
  const key = normalized.id;
  const existing = tradeProposalRegistry.get(key) || {};
  const merged = { ...existing, ...normalized };
  tradeProposalRegistry.set(key, merged);
  const fingerprint = buildProposalFingerprint(merged);
  if (fingerprint) {
    fallbackProposalKeys.set(fingerprint, merged.id);
  }
  updateTakeProposalsButtonState();
  return merged;
}

function shouldAutoExecuteTradeProposals() {
  return automationActive && hasDashboardChatKey();
}

function requestAutomatedTradeExecution() {
  if (!shouldAutoExecuteTradeProposals() || automationCycleInProgress) {
    return;
  }
  if (getPendingTradeProposals().length === 0) {
    return;
  }
  if (automatedExecutionTimer) {
    clearTimeout(automatedExecutionTimer);
  }
  automatedExecutionTimer = setTimeout(processAutomatedTradeExecution, 150);
}

async function processAutomatedTradeExecution() {
  if (automatedExecutionTimer) {
    clearTimeout(automatedExecutionTimer);
    automatedExecutionTimer = null;
  }
  if (!shouldAutoExecuteTradeProposals() || automationCycleInProgress) {
    return;
  }
  if (automatedExecutionInFlight) {
    return;
  }
  if (getPendingTradeProposals().length === 0) {
    return;
  }
  automatedExecutionInFlight = true;
  try {
    await handleTakeTradeProposals();
  } catch (err) {
    console.warn('Automated trade proposal execution failed', err);
  } finally {
    automatedExecutionInFlight = false;
    if (shouldAutoExecuteTradeProposals() && !automationCycleInProgress && getPendingTradeProposals().length > 0) {
      requestAutomatedTradeExecution();
    }
  }
}

function pruneTradeProposalRegistry(validList) {
  if (!Array.isArray(validList)) {
    return;
  }
  const validIds = new Set();
  validList.forEach((item) => {
    if (item && item.id) {
      validIds.add(item.id);
    }
  });
  Array.from(tradeProposalRegistry.entries()).forEach(([key, value]) => {
    if (!validIds.has(key)) {
      tradeProposalRegistry.delete(key);
      const fingerprint = buildProposalFingerprint(value);
      if (fingerprint) {
        fallbackProposalKeys.delete(fingerprint);
      }
    }
  });
  updateTakeProposalsButtonState();
}

function getPendingTradeProposals() {
  return Array.from(tradeProposalRegistry.values())
    .filter((proposal) => {
      const status = (proposal.status || '').toString().toLowerCase();
      return !['queued', 'executed', 'completed', 'processing'].includes(status);
    })
    .sort((a, b) => {
      const aTs = Number(a.ts || a.queued_at || 0);
      const bTs = Number(b.ts || b.queued_at || 0);
      return aTs - bTs;
    });
}

function updateTakeProposalsButtonState() {
  if (!btnTakeTradeProposals) return;
  const state = btnTakeTradeProposals.dataset.state || 'idle';
  const hasPending = getPendingTradeProposals().length > 0;
  if (state === 'working') {
    btnTakeTradeProposals.disabled = true;
    btnTakeTradeProposals.textContent = getTakeProposalsWorkingLabel();
    btnTakeTradeProposals.removeAttribute('title');
    return;
  }
  btnTakeTradeProposals.textContent = translate(
    'chat.proposal.takeAll',
    takeProposalsButtonDefaultLabel || getDefaultTakeProposalsLabel()
  );
  btnTakeTradeProposals.disabled = !hasPending;
  if (hasPending) {
    btnTakeTradeProposals.removeAttribute('title');
  } else {
    btnTakeTradeProposals.title = getTakeProposalsHintLabel();
  }
}

function sanitizeAutomationInterval() {
  if (!automationIntervalInput) {
    return 5;
  }
  const raw = Number.parseInt(automationIntervalInput.value, 10);
  const minutes = Number.isFinite(raw) && raw >= 1 ? Math.min(raw, 1440) : 5;
  automationIntervalInput.value = minutes.toString();
  return minutes;
}

function getAutomationIntervalMinutes() {
  if (!automationIntervalInput) {
    return 5;
  }
  const raw = Number.parseInt(automationIntervalInput.value, 10);
  if (!Number.isFinite(raw) || raw < 1) {
    return sanitizeAutomationInterval();
  }
  return Math.min(raw, 1440);
}

function clearAutomationTimers() {
  if (automationTimeoutId) {
    clearTimeout(automationTimeoutId);
    automationTimeoutId = null;
  }
  if (automationCountdownIntervalId) {
    clearInterval(automationCountdownIntervalId);
    automationCountdownIntervalId = null;
  }
}

function updateAutomationCountdownDisplay() {
  if (!automationCountdown) {
    return;
  }
  if (!automationActive) {
    automationCountdown.hidden = true;
    automationCountdown.classList.remove('is-running');
    if (automationCountdownLabel) {
      automationCountdownLabel.textContent = translate('chat.automation.nextRunLabel', 'Next run in');
    }
    if (automationCountdownValue) {
      automationCountdownValue.textContent = '';
    }
    return;
  }

  if (!automationTargetTimestamp) {
    automationCountdown.hidden = false;
    automationCountdown.classList.add('is-running');
    if (automationCountdownLabel) {
      automationCountdownLabel.textContent = translate('chat.automation.running', 'Running now…');
    }
    if (automationCountdownValue) {
      automationCountdownValue.textContent = '';
    }
    return;
  }

  const now = Date.now();
  const remaining = Math.max(automationTargetTimestamp - now, 0);
  const totalSeconds = Math.ceil(remaining / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  const formatted = `${minutes}:${seconds.toString().padStart(2, '0')}`;

  automationCountdown.hidden = false;
  automationCountdown.classList.remove('is-running');
  if (automationCountdownLabel) {
    automationCountdownLabel.textContent = translate('chat.automation.nextRunLabel', 'Next run in');
  }
  if (automationCountdownValue) {
    automationCountdownValue.textContent = formatted;
  }
}

function stopAutomation(options = {}) {
  const { message } = options;
  automationActive = false;
  automationCycleInProgress = false;
  if (automatedExecutionTimer) {
    clearTimeout(automatedExecutionTimer);
    automatedExecutionTimer = null;
  }
  automatedExecutionInFlight = false;
  clearAutomationTimers();
  automationTargetTimestamp = null;
  if (automationToggle) {
    automationToggle.checked = false;
  }
  updateAutomationCountdownDisplay();
  if (message) {
    setChatStatus(message);
  }
}

function scheduleAutomationCycle() {
  if (!automationActive) {
    return;
  }
  const minutes = getAutomationIntervalMinutes();
  const delayMs = Math.min(minutes * 60_000, 2_147_483_647);
  automationTargetTimestamp = Date.now() + delayMs;
  clearAutomationTimers();
  updateAutomationCountdownDisplay();
  automationCountdownIntervalId = setInterval(updateAutomationCountdownDisplay, 1000);
  automationTimeoutId = setTimeout(() => {
    automationTargetTimestamp = null;
    updateAutomationCountdownDisplay();
    runAutomationCycle().catch((err) => {
      console.warn('Automation cycle failed', err);
    });
  }, delayMs);
}

async function runAutomationCycle() {
  if (!automationActive || automationCycleInProgress) {
    return;
  }
  automationCycleInProgress = true;
  try {
    updateAutomationCountdownDisplay();
    const analysisSuccessful = await runMarketAnalysis({ automated: true });
    if (!automationActive) {
      return;
    }
    if (analysisSuccessful) {
      try {
        await handleTakeTradeProposals();
      } catch (err) {
        console.warn('Automated trade proposal execution failed', err);
      }
    }
  } finally {
    automationCycleInProgress = false;
    if (automationActive) {
      scheduleAutomationCycle();
    }
  }
}

function startAutomation() {
  if (automationActive) {
    return;
  }
  const minutes = sanitizeAutomationInterval();
  if (!hasDashboardChatKey()) {
    stopAutomation();
    setChatStatus(translate('chat.status.keyRequired', 'OpenAI key required.'));
    setChatKeyIndicator('missing', translate('chat.status.keyRequired', 'OpenAI key required.'));
    return;
  }
  automationActive = true;
  requestAutomatedTradeExecution();
  scheduleAutomationCycle();
  const summary = translate('chat.automation.scheduled', 'Automated cycle scheduled for {{minutes}} minute(s).', {
    minutes,
  });
  setChatStatus(summary);
}

async function runMarketAnalysis(options = {}) {
  const { automated = false } = options;
  if (!btnAnalyzeMarket) {
    return false;
  }
  if (aiAnalyzePending) {
    return false;
  }
  if (!hasDashboardChatKey()) {
    setChatStatus(translate('chat.status.keyRequired', 'OpenAI key required.'));
    setChatKeyIndicator('missing', translate('chat.status.keyRequired', 'OpenAI key required.'));
    if (automated) {
      stopAutomation();
    }
    return false;
  }
  aiAnalyzePending = true;
  btnAnalyzeMarket.textContent = translate('chat.analyzing', 'Analyzing…');
  updateAnalyzeButtonAvailability();
  setChatStatus(translate('chat.status.analyzing', 'Analyzing market…'));
  let success = false;
  try {
    const res = await fetch('/api/ai/analyze', { method: 'POST' });
    const text = await res.text();
    let data = {};
    try {
      data = text ? JSON.parse(text) : {};
    } catch (parseErr) {
      data = {};
    }
    if (!res.ok) {
      const detail = data && typeof data === 'object' ? data.detail || data.message : null;
      throw new Error(detail || 'Market analysis failed');
    }
    const analysis =
      (data.analysis || '').toString().trim() || translate('chat.analysis.none', 'No analysis returned.');
    appendChatMessage('assistant', analysis, {
      model: data.model,
      source: data.source || 'analysis',
      roleLabel: translate('chat.role.analysis', 'Market Analysis'),
    });
    if (data.source === 'fallback') {
      setChatStatus(translate('chat.status.fallback', 'Market analysis (fallback).'));
    } else {
      setChatStatus(translate('chat.status.ready', 'Market analysis ready.'));
    }
    setChatKeyIndicator('ready', translate('chat.key.ready', 'Dedicated chat key active'));
    const tradeProposals = Array.isArray(data.trade_proposals) ? data.trade_proposals : [];
    if (tradeProposals.length > 0) {
      tradeProposals.forEach((proposal) => appendTradeProposalCard(proposal));
    } else {
      loadTrades().catch((err) => {
        console.warn('Failed to refresh trade proposals after analysis', err);
      });
    }
    success = true;
  } catch (err) {
    const defaultError = translate('chat.status.failed', 'Market analysis failed.');
    const rawMessage = (err?.message || '').trim();
    const errorMessage =
      rawMessage && rawMessage !== 'Market analysis failed' && rawMessage !== 'Market analysis failed.'
        ? rawMessage
        : defaultError;
    appendChatMessage('assistant', errorMessage, {
      source: 'error',
      roleLabel: translate('chat.role.analysis', 'Market Analysis'),
    });
    setChatStatus(translate('chat.status.failed', 'Market analysis failed.'));
    if (automated && rawMessage && rawMessage.toLowerCase().includes('key')) {
      stopAutomation();
    }
  } finally {
    aiAnalyzePending = false;
    btnAnalyzeMarket.textContent = analyzeButtonDefaultLabel;
    updateAnalyzeButtonAvailability();
  }
  return success;
}

function updateLanguageButtonsState() {
  languageButtons.forEach((button) => {
    const lang = button.dataset.lang;
    const isActive = lang === currentLanguage;
    button.classList.toggle('active', isActive);
    button.setAttribute('aria-pressed', isActive ? 'true' : 'false');
  });
}

function refreshEnvironmentToggleLabels() {
  if (!btnToggleEnv) return;
  const defaultExpand = btnToggleEnv.dataset.i18nDefaultExpand || btnToggleEnv.dataset.labelExpand || 'Expand';
  const defaultCollapse = btnToggleEnv.dataset.i18nDefaultCollapse || btnToggleEnv.dataset.labelCollapse || 'Collapse';
  const defaultAriaExpand = btnToggleEnv.dataset.i18nDefaultAriaExpand || btnToggleEnv.dataset.ariaExpand || defaultExpand;
  const defaultAriaCollapse = btnToggleEnv.dataset.i18nDefaultAriaCollapse || btnToggleEnv.dataset.ariaCollapse || defaultCollapse;
  btnToggleEnv.dataset.labelExpand = translate('env.expand', defaultExpand);
  btnToggleEnv.dataset.labelCollapse = translate('env.collapse', defaultCollapse);
  btnToggleEnv.dataset.ariaExpand = translate('env.expand', defaultAriaExpand);
  btnToggleEnv.dataset.ariaCollapse = translate('env.collapse', defaultAriaCollapse);
  if (!btnToggleEnv.dataset.i18nDefaultExpand) {
    btnToggleEnv.dataset.i18nDefaultExpand = defaultExpand;
  }
  if (!btnToggleEnv.dataset.i18nDefaultCollapse) {
    btnToggleEnv.dataset.i18nDefaultCollapse = defaultCollapse;
  }
  if (!btnToggleEnv.dataset.i18nDefaultAriaExpand) {
    btnToggleEnv.dataset.i18nDefaultAriaExpand = defaultAriaExpand;
  }
  if (!btnToggleEnv.dataset.i18nDefaultAriaCollapse) {
    btnToggleEnv.dataset.i18nDefaultAriaCollapse = defaultAriaCollapse;
  }
  syncCollapseToggle(btnToggleEnv, envCollapsed);
}

function setLanguage(lang) {
  applyTranslations(lang);
}

languageButtons.forEach((button) => {
  button.addEventListener('click', () => {
    const lang = button.dataset.lang;
    setLanguage(lang);
  });
});

applyTranslations(currentLanguage);
renderCompletedPositionsHistory();

function hasDashboardChatKey() {
  const env = currentConfig?.env || {};
  const chatKey = (env.ASTER_CHAT_OPENAI_API_KEY || '').trim();
  const primaryKey = (env.ASTER_OPENAI_API_KEY || '').trim();
  return chatKey.length > 0 || primaryKey.length > 0;
}

function setChatKeyIndicator(state, message) {
  if (!chatKeyIndicator) return;
  const text = (message || '').toString();
  chatKeyIndicator.textContent = text;
  if (state) {
    chatKeyIndicator.dataset.state = state;
  } else {
    chatKeyIndicator.removeAttribute('data-state');
  }
}

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
    aiBudgetModeLabel.textContent = '';
    aiBudgetModeLabel.style.display = 'none';
    aiBudgetModeLabel.setAttribute('aria-hidden', 'true');
    return;
  }
  aiBudgetModeLabel.style.display = '';
  aiBudgetModeLabel.removeAttribute('aria-hidden');
  if (active === 'pro') {
    aiBudgetModeLabel.textContent = translate('status.aiBudget.pro', 'Pro-Mode');
  } else {
    aiBudgetModeLabel.textContent = translate('status.aiBudget.standard', 'Standard');
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
    summary:
      'Capital preservation first: slower signal intake, narrower exposure, 30% base risk per trade, a 4× base leverage cap, and a 33% equity utilisation guard.',
    riskProfile: 'conservative',
    risk: 30,
    leverage: 4,
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
    funding: {
      enabled: true,
      maxLong: 0.0007,
      maxShort: 0.0009,
    },
    alpha: {
      threshold: 0.6,
      minConf: 0.28,
      promoteDelta: 0.18,
      rewardMargin: 0.06,
    },
    alphaWarmup: 55,
    banditEnabled: true,
    alphaEnabled: true,
    equityFraction: 0.33,
    maxOpenGlobal: 0,
    maxOpenPerSymbol: 1,
    trendBias: 'with',
    notional: { min: 1, max: 200 },
  },
  mid: {
    label: 'Mid',
    summary:
      'Balanced cadence with moderate risk, 50% base risk per trade, 10× base leverage, and a 66% equity utilisation ceiling geared toward steady account growth.',
    riskProfile: 'balanced',
    risk: 50,
    leverage: 10,
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
    funding: {
      enabled: true,
      maxLong: 0.001,
      maxShort: 0.001,
    },
    alpha: {
      threshold: 0.55,
      minConf: 0.22,
      promoteDelta: 0.15,
      rewardMargin: 0.05,
    },
    alphaWarmup: 40,
    banditEnabled: true,
    alphaEnabled: true,
    equityFraction: 0.66,
    maxOpenGlobal: 0,
    maxOpenPerSymbol: 1,
    trendBias: 'with',
    notional: { min: 200, max: 1500 },
  },
  high: {
    label: 'High',
    summary:
      'High-frequency execution with wider risk budgets, 100% base risk per trade, leverage auto-set to the exchange maximum, an unlimited AI spend cap, and full (100%) equity deployment when signals align.',
    riskProfile: 'aggressive',
    unlimitedBudget: true,
    risk: 100,
    leverage: 'max',
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
    funding: {
      enabled: true,
      maxLong: 0.0014,
      maxShort: 0.0018,
    },
    alpha: {
      threshold: 0.52,
      minConf: 0.18,
      promoteDelta: 0.12,
      rewardMargin: 0.04,
    },
    alphaWarmup: 32,
    banditEnabled: true,
    alphaEnabled: true,
    equityFraction: 1.0,
    maxOpenGlobal: 0,
    maxOpenPerSymbol: 1,
    trendBias: 'with',
    notional: { min: 1500, max: Infinity },
  },
  att: {
    label: 'ATT',
    summary:
      'Against-the-trend fading: contrarian plays with tighter stops, disciplined sizing, exchange-max leverage, and no AI budget ceiling.',
    riskProfile: 'aggressive',
    unlimitedBudget: true,
    risk: 0.75,
    leverage: 'max',
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
    funding: {
      enabled: true,
      maxLong: 0.0011,
      maxShort: 0.0013,
    },
    alpha: {
      threshold: 0.6,
      minConf: 0.25,
      promoteDelta: 0.16,
      rewardMargin: 0.05,
    },
    alphaWarmup: 45,
    banditEnabled: true,
    alphaEnabled: true,
    equityFraction: 1.0,
    maxOpenGlobal: 0,
    maxOpenPerSymbol: 1,
    trendBias: 'against',
    notional: { min: 1500, max: Infinity },
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

const EVENT_RISK_SEVERITY_BANDS = [
  { min: 0.75, key: 'critical', fallback: 'Critical risk' },
  { min: 0.55, key: 'high', fallback: 'High risk' },
  { min: 0.35, key: 'elevated', fallback: 'Elevated' },
  { min: 0.2, key: 'watch', fallback: 'Watch' },
  { min: 0, key: 'calm', fallback: 'Calm' },
];

const DECISION_REASON_LABELS = {
  spread: 'Spread too wide',
  wicky: 'Wicks too volatile',
  few_klines: 'Not enough recent candles',
  edge_r: 'Expected edge too small',
  klines_err: 'Market data unavailable',
  funding_long: 'Funding too expensive for longs',
  funding_short: 'Funding too expensive for shorts',
  policy_filter: 'AI filter rejected the setup',
  filtered: 'Signal blocked by safety filters',
  position_size: 'Position size below minimum',
  order_failed: 'Order could not be placed',
  sentinel_veto: 'Sentinel vetoed trade',
  ai_risk_zero: 'AI sized trade to zero',
  sentinel_block: 'Sentinel block',
  fallback_rules: 'Fallback rules triggered',
  plan_pending: 'AI plan pending',
  plan_timeout: 'AI plan timeout',
  trend_pending: 'Trend scan pending (waiting for AI response)',
  trend_timeout: 'Trend scan timeout',
  ai_trend_skip: 'AI declined trend setup',
  ai_trend_invalid: 'AI returned invalid trend setup',
  quote_volume: 'Quote volume guard',
  quote_volume_cooldown: 'Quote volume cooldown',
  position_cap_symbol: 'Per-symbol position cap',
  position_cap_global: 'Global position cap',
  base_strategy_skip: 'Base strategy veto',
};

const LOG_REASON_CATEGORY_MAP = {
  quote_volume: 'volume',
  quote_volume_cooldown: 'volume',
  qv_score: 'volume',
  spread: 'spread',
  oracle_gap: 'oracle',
  oracle_gap_clamped: 'oracle',
  sentinel_veto: 'sentinel',
  sentinel_block: 'sentinel',
  sentinel_factor: 'sentinel',
  sentinel_event_risk: 'sentinel',
  sentinel_hype: 'sentinel',
  funding_long: 'funding',
  funding_short: 'funding',
  funding: 'funding',
  policy_filter: 'ai',
  filtered: 'ai',
  fallback_rules: 'ai',
  ai_trend_skip: 'ai',
  ai_trend_invalid: 'ai',
  plan_pending: 'ai',
  plan_timeout: 'ai',
  trend_pending: 'ai',
  trend_timeout: 'ai',
  ai_risk_zero: 'ai',
  base_strategy_skip: 'ai',
  order_failed: 'orders',
  position_size: 'orders',
  position_cap_symbol: 'orders',
  position_cap_global: 'orders',
  few_klines: 'data',
  klines_err: 'data',
  wicky: 'volatility',
  edge_r: 'edge',
};

const LOG_REASON_COLOR_MAP = {
  ai_risk_zero: { base: '#EA580C', accent: '#FB923C', text: '#4a1a05' },
  ai_trend_invalid: { base: '#1E293B', accent: '#475569', text: '#E2E8F0' },
  ai_trend_skip: { base: '#3B82F6', accent: '#60A5FA', text: '#0b2f58' },
  base_strategy_skip: { base: '#312E81', accent: '#4338CA', text: '#EEF2FF' },
  edge_r: { base: '#6366F1', accent: '#818CF8', text: '#1e1b4b' },
  fallback_rules: { base: '#22D3EE', accent: '#67E8F9', text: '#03414b' },
  filtered: { base: '#2563EB', accent: '#60A5FA', text: '#0b2b5c' },
  funding: { base: '#B45309', accent: '#F97316', text: '#3b1300' },
  funding_long: { base: '#F59E0B', accent: '#FBBF24', text: '#43290b' },
  funding_short: { base: '#D97706', accent: '#F59E0B', text: '#421504' },
  few_klines: { base: '#38BDF8', accent: '#7DD3FC', text: '#0b3d5c' },
  klines_err: { base: '#94A3B8', accent: '#E2E8F0', text: '#111827' },
  oracle_gap: { base: '#0891B2', accent: '#22D3EE', text: '#012d36' },
  oracle_gap_clamped: { base: '#155E75', accent: '#38BDF8', text: '#ECFEFF' },
  order_failed: { base: '#EF4444', accent: '#F87171', text: '#600b0b' },
  plan_pending: { base: '#A855F7', accent: '#C084FC', text: '#3a0a58' },
  plan_timeout: { base: '#F43F5E', accent: '#FB7185', text: '#5e0617' },
  policy_filter: { base: '#0F766E', accent: '#2DD4BF', text: '#022c22' },
  position_cap_global: { base: '#4338CA', accent: '#6366F1', text: '#E0E7FF' },
  position_cap_symbol: { base: '#5B21B6', accent: '#7C3AED', text: '#EDE9FE' },
  position_size: { base: '#22C55E', accent: '#4ADE80', text: '#06472b' },
  qv_score: { base: '#047857', accent: '#34D399', text: '#01211a' },
  quote_volume: { base: '#10B981', accent: '#34D399', text: '#034032' },
  quote_volume_cooldown: { base: '#0D9488', accent: '#2DD4BF', text: '#023532' },
  sentinel_block: { base: '#DB2777', accent: '#FB7185', text: '#4f0c2c' },
  sentinel_event_risk: { base: '#F97316', accent: '#FDBA74', text: '#4a1a05' },
  sentinel_factor: { base: '#E879F9', accent: '#F0ABFC', text: '#521054' },
  sentinel_hype: { base: '#FACC15', accent: '#FDE68A', text: '#3b2600' },
  sentinel_veto: { base: '#EC4899', accent: '#F472B6', text: '#4f0c2c' },
  spread: { base: '#8B5CF6', accent: '#A78BFA', text: '#2e1065' },
  trend_pending: { base: '#1D4ED8', accent: '#3B82F6', text: '#0a1f4f' },
  trend_timeout: { base: '#B91C1C', accent: '#F87171', text: '#5f0505' },
  wicky: { base: '#FB7185', accent: '#F9A8D4', text: '#4c0519' },
};

const LOG_LABEL_CATEGORY_MAP = {
  'ai feed': 'ai',
  'ai request': 'ai',
  'bot status': 'system',
  'scan complete': 'scan',
  scan: 'scan',
  settings: 'system',
  'trade placed': 'trade',
  'trade win': 'trade',
  'trade loss': 'trade',
  'fast tp': 'trade',
};

const FRIENDLY_LEVEL_LABELS = {
  success: 'Trade',
  info: 'Update',
  warning: 'Heads-up',
  error: 'Issue',
  system: 'System',
  debug: 'Detail',
};

function isTruthy(value) {
  if (typeof value === 'boolean') return value;
  if (typeof value === 'number') return value !== 0;
  if (typeof value === 'string') {
    const normalized = value.trim().toLowerCase();
    if (!normalized) return false;
    return ['1', 'true', 'yes', 'on'].includes(normalized);
  }
  return false;
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

function updateDefaultNotionalInputs(value) {
  const textValue = value === undefined || value === null ? '' : value.toString();
  if (inputDefaultNotional) {
    inputDefaultNotional.value = textValue;
  }
  if (inputAiDefaultNotional) {
    inputAiDefaultNotional.value = textValue;
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
  if (inputChatOpenAiKey) {
    inputChatOpenAiKey.value = env?.ASTER_CHAT_OPENAI_API_KEY ?? '';
  }
  if (inputAiBudget) {
    inputAiBudget.value = env?.ASTER_AI_DAILY_BUDGET_USD ?? '20';
  }
  if (inputAiModel) {
    const model = env?.ASTER_AI_MODEL ?? 'gpt-4.1';
    const existingOption = Array.from(inputAiModel.options).find((option) => option.value === model);
    if (existingOption) {
      inputAiModel.value = model;
    } else {
      const fallbackOption = new Option(model, model, true, true);
      inputAiModel.add(fallbackOption);
    }
  }
  updateDefaultNotionalInputs(env?.ASTER_DEFAULT_NOTIONAL);
  syncAiChatAvailability();
}

async function loadConfig() {
  const res = await fetch('/api/config');
  if (!res.ok) throw new Error('Unable to load configuration');
  currentConfig = await res.json();
  renderConfig(currentConfig.env);
  renderCredentials(currentConfig.env);
  syncPaperModeFromEnv(currentConfig.env);
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
  if (inputChatOpenAiKey) {
    payload.ASTER_CHAT_OPENAI_API_KEY = inputChatOpenAiKey.value.trim();
  }
  if (inputAiBudget) {
    const value = inputAiBudget.value.trim();
    payload.ASTER_AI_DAILY_BUDGET_USD = value === '' ? '0' : value;
  }
  if (inputAiModel) {
    payload.ASTER_AI_MODEL = inputAiModel.value.trim();
  }
  if (inputAiDefaultNotional) {
    const value = inputAiDefaultNotional.value.trim();
    if (value !== '') {
      const numeric = Number(value);
      if (Number.isFinite(numeric) && numeric >= 0) {
        payload.ASTER_DEFAULT_NOTIONAL = numeric.toString();
      }
    }
  }
  return payload;
}

async function saveConfig() {
  const payload = gatherConfigPayload();
  btnSaveConfig.disabled = true;
  btnSaveConfig.textContent = translate('common.saving', 'Saving…');
  btnSaveConfig.dataset.state = 'saving';
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
    btnSaveConfig.textContent = translate('common.saved', 'Saved ✓');
    btnSaveConfig.dataset.state = 'saved';
    setTimeout(() => {
      btnSaveConfig.dataset.state = 'idle';
      btnSaveConfig.textContent = translate('env.save', 'Save');
    }, 1500);
  } catch (err) {
    btnSaveConfig.textContent = translate('common.error', 'Error');
    btnSaveConfig.dataset.state = 'error';
    alert(err.message);
    setTimeout(() => {
      btnSaveConfig.dataset.state = 'idle';
      btnSaveConfig.textContent = translate('env.save', 'Save');
    }, 2000);
  } finally {
    btnSaveConfig.disabled = false;
  }
}

async function saveCredentials() {
  const payload = gatherCredentialPayload();
  if (!btnSaveCredentials) return;
  btnSaveCredentials.disabled = true;
  btnSaveCredentials.textContent = translate('common.saving', 'Saving…');
  btnSaveCredentials.dataset.state = 'saving';
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
    btnSaveCredentials.textContent = translate('common.saved', 'Saved ✓');
    btnSaveCredentials.dataset.state = 'saved';
    setTimeout(() => {
      btnSaveCredentials.dataset.state = 'idle';
      btnSaveCredentials.textContent = translate('credentials.save', 'Save');
    }, 1500);
  } catch (err) {
    btnSaveCredentials.textContent = translate('common.error', 'Error');
    btnSaveCredentials.dataset.state = 'error';
    alert(err.message);
    setTimeout(() => {
      btnSaveCredentials.dataset.state = 'idle';
      btnSaveCredentials.textContent = translate('credentials.save', 'Save');
    }, 2000);
  } finally {
    btnSaveCredentials.disabled = false;
  }
}

async function saveAiConfig() {
  if (!btnSaveAi) return;
  const payload = gatherAiPayload();
  btnSaveAi.disabled = true;
  btnSaveAi.textContent = translate('common.saving', 'Saving…');
  btnSaveAi.dataset.state = 'saving';
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
    btnSaveAi.textContent = translate('common.saved', 'Saved ✓');
    btnSaveAi.dataset.state = 'saved';
    setTimeout(() => {
      btnSaveAi.dataset.state = 'idle';
      btnSaveAi.textContent = translate('ai.config.save', 'Save');
    }, 1500);
  } catch (err) {
    btnSaveAi.textContent = translate('common.error', 'Error');
    btnSaveAi.dataset.state = 'error';
    alert(err.message);
    setTimeout(() => {
      btnSaveAi.dataset.state = 'idle';
      btnSaveAi.textContent = translate('ai.config.save', 'Save');
    }, 2000);
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

function markStale(element, stale) {
  if (!element) return;
  if (stale) {
    element.setAttribute('data-stale', 'true');
  } else {
    element.removeAttribute('data-stale');
  }
}

function setTradeDataStale(stale) {
  tradeDataCards.forEach((card) => markStale(card, stale));
}

function isValidOpenPositionsPayload(payload) {
  if (payload === undefined || payload === null) {
    return false;
  }
  if (Array.isArray(payload)) {
    return true;
  }
  return typeof payload === 'object';
}

function mergeTradeSnapshot(previous, next) {
  const snapshot = next && typeof next === 'object' ? { ...next } : {};

  if (!Array.isArray(snapshot.history)) {
    snapshot.history = Array.isArray(previous?.history) ? previous.history : [];
  }

  if (!snapshot.stats || typeof snapshot.stats !== 'object') {
    snapshot.stats = previous?.stats ?? null;
  }

  if (!snapshot.decision_stats || typeof snapshot.decision_stats !== 'object') {
    snapshot.decision_stats = previous?.decision_stats ?? null;
  }

  if (!snapshot.cumulative_stats || typeof snapshot.cumulative_stats !== 'object') {
    snapshot.cumulative_stats = previous?.cumulative_stats ?? null;
  }

  if (!snapshot.ai_budget || typeof snapshot.ai_budget !== 'object') {
    snapshot.ai_budget = previous?.ai_budget ?? null;
  }

  if (!Array.isArray(snapshot.ai_requests)) {
    snapshot.ai_requests = Array.isArray(previous?.ai_requests) ? previous.ai_requests : [];
  }

  if (!Array.isArray(snapshot.exchange_positions)) {
    snapshot.exchange_positions = Array.isArray(previous?.exchange_positions)
      ? previous.exchange_positions
      : [];
  }

  if (!snapshot.playbook || typeof snapshot.playbook !== 'object') {
    snapshot.playbook = previous?.playbook ?? null;
  }

  if (!Array.isArray(snapshot.playbook_activity)) {
    snapshot.playbook_activity = Array.isArray(previous?.playbook_activity)
      ? previous.playbook_activity
      : [];
  }

  if (!Array.isArray(snapshot.playbook_process)) {
    snapshot.playbook_process = Array.isArray(previous?.playbook_process)
      ? previous.playbook_process
      : [];
  }

  if (!snapshot.playbook_market_overview || typeof snapshot.playbook_market_overview !== 'object') {
    snapshot.playbook_market_overview = previous?.playbook_market_overview ?? null;
  }

  if (!snapshot.hero_metrics || typeof snapshot.hero_metrics !== 'object') {
    snapshot.hero_metrics = previous?.hero_metrics ?? null;
  }

  if (!snapshot.history_summary || typeof snapshot.history_summary !== 'object') {
    snapshot.history_summary = previous?.history_summary ?? null;
  }

  if (!isValidOpenPositionsPayload(snapshot.open)) {
    snapshot.open = {};
  }

  if (!Array.isArray(snapshot.ai_trade_proposals)) {
    snapshot.ai_trade_proposals = Array.isArray(previous?.ai_trade_proposals)
      ? previous.ai_trade_proposals
      : [];
  }

  return snapshot;
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

function formatTickerRank(position) {
  const numeric = Number(position);
  if (!Number.isFinite(numeric) || numeric <= 0) return '';
  const value = Math.floor(numeric);
  const mod100 = value % 100;
  if (mod100 >= 11 && mod100 <= 13) {
    return `${value}th`;
  }
  switch (value % 10) {
    case 1:
      return `${value}st`;
    case 2:
      return `${value}nd`;
    case 3:
      return `${value}rd`;
    default:
      return `${value}th`;
  }
}

function createTickerItem(asset, rank) {
  const item = document.createElement('div');
  item.className = 'ticker-item';
  item.setAttribute('role', 'listitem');
  item.dataset.symbol = (asset.symbol || asset.base || '').toString().toUpperCase();
  item.tabIndex = 0;

  const logo = buildTickerLogo(asset);

  const meta = document.createElement('div');
  meta.className = 'ticker-meta';

  const header = document.createElement('div');
  header.className = 'ticker-symbol-line';

  const rankLabel = document.createElement('span');
  rankLabel.className = 'ticker-rank';
  rankLabel.textContent = formatTickerRank(rank);

  const symbol = document.createElement('span');
  symbol.className = 'ticker-symbol';
  symbol.textContent = (asset.base || asset.symbol || '').toString().toUpperCase();

  const price = document.createElement('span');
  price.className = 'ticker-price';
  price.textContent = formatPriceDisplay(asset.price);

  header.append(rankLabel, symbol);

  meta.append(header, price);

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
      const originals = Array.from(tickerTrack.querySelectorAll('.ticker-item:not(.ticker-item-duplicate)'));
      if (originals.length === 0) return;
      const styles = window.getComputedStyle(tickerTrack);
      const gap = parseFloat(styles.columnGap || styles.gap || '0');
      const totalWidth = originals.reduce((sum, child) => sum + child.getBoundingClientRect().width, 0);
      const translate = Math.ceil(totalWidth + gap * Math.max(0, originals.length - 1));
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
      tickerEmpty.textContent = error || translate('ticker.noData', 'No market data available right now.');
    }
    return;
  }

  if (tickerEmpty) {
    tickerEmpty.textContent = '';
  }

  const fragment = document.createDocumentFragment();
  assets.forEach((asset, index) => {
    fragment.appendChild(createTickerItem(asset, index + 1));
  });
  tickerTrack.appendChild(fragment);

  const ensureTickerFill = () => {
    const originals = Array.from(tickerTrack.querySelectorAll('.ticker-item:not(.ticker-item-duplicate)'));
    if (originals.length === 0) return;
    const styles = window.getComputedStyle(tickerTrack);
    const gap = parseFloat(styles.columnGap || styles.gap || '0');
    const baseWidth = originals.reduce((sum, node) => sum + node.getBoundingClientRect().width, 0);
    const totalBaseWidth = baseWidth + gap * Math.max(0, originals.length - 1);
    const viewportWidth = tickerTrack.parentElement
      ? tickerTrack.parentElement.getBoundingClientRect().width
      : 0;
    const minTrackWidth = Math.max(totalBaseWidth * 3, viewportWidth + totalBaseWidth * 2);

    const createDuplicate = (node) => {
      const clone = node.cloneNode(true);
      clone.classList.add('ticker-item-duplicate');
      clone.setAttribute('aria-hidden', 'true');
      clone.tabIndex = -1;
      clone.setAttribute('tabindex', '-1');
      return clone;
    };

    originals
      .slice()
      .reverse()
      .forEach((node) => {
        tickerTrack.insertBefore(createDuplicate(node), tickerTrack.firstChild);
      });

    while (tickerTrack.scrollWidth < minTrackWidth) {
      originals.forEach((node) => {
        tickerTrack.appendChild(createDuplicate(node));
      });
    }

    computeTickerMetrics(assets);
  };

  window.requestAnimationFrame(() => {
    window.requestAnimationFrame(ensureTickerFill);
  });
}

function handleTickerActivation(event) {
  if (!tickerTrack) return;
  const item = event.target.closest('.ticker-item');
  if (!item) return;
  const symbol = item.dataset.symbol;
  const url = buildAsterPositionUrl(symbol);
  if (!url) return;
  openAsterPositionUrl(url);
}

if (tickerTrack) {
  tickerTrack.addEventListener('click', (event) => {
    handleTickerActivation(event);
  });
  tickerTrack.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleTickerActivation(event);
    }
  });
}

async function loadMostTradedCoins() {
  if (!tickerContainer) return;
  try {
    if (tickerEmpty) {
    tickerEmpty.textContent = translate('ticker.empty', 'Gathering market leaders…');
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
    console.warn('Failed to load most traded assets', err);
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
  if (normalized === 'BUY') return 'Long';
  if (normalized === 'SELL') return 'Short';
  return normalized.charAt(0) + normalized.slice(1).toLowerCase();
}

const ACTIVE_POSITION_SIGNED_SIZE_KEYS = [
  'positionAmt',
  'position_amt',
  'position_amount',
  'qty',
  'quantity',
  'size',
];

const ACTIVE_POSITION_NOTIONAL_KEYS = [
  'notional',
  'notional_usdt',
  'notionalUsd',
  'notionalUSD',
  'positionNotional',
  'position_notional',
  'size_usdt',
  'sizeUSDT',
  'sizeUsd',
];

const TAKE_PROFIT_FIELD_KEYS = [
  'tp',
  'take',
  'take_price',
  'takePrice',
  'take_profit',
  'takeProfit',
  'takeProfitPrice',
  'take_profit_price',
  'take_profit_next',
  'takeProfitNext',
  'tp_price',
  'tpPrice',
  'tp_target',
  'tpTarget',
  'next_tp',
  'target',
  'target_price',
  'targetPrice',
];

const STOP_LOSS_FIELD_KEYS = [
  'sl',
  'stop',
  'stop_price',
  'stopPrice',
  'stop_price_next',
  'stopPriceNext',
  'stop_loss',
  'stopLoss',
  'stopLossPrice',
  'stop_loss_price',
  'stop_loss_next',
  'stopLossNext',
  'stop_target',
  'stopTarget',
  'stop_trigger',
  'stopTrigger',
  'next_stop',
];

const ACTIVE_POSITION_ALIASES = {
  symbol: ['symbol', 'sym', 'ticker', 'pair'],
  size: [...ACTIVE_POSITION_NOTIONAL_KEYS, ...ACTIVE_POSITION_SIGNED_SIZE_KEYS],
  entry: ['entry', 'entry_price', 'entryPrice'],
  mark: ['mark', 'mark_price', 'markPrice', 'lastPrice', 'price'],
  roe: ['roe_percent', 'roe_pct', 'roePercent', 'pnl_percent', 'pnl_pct', 'roe'],
  pnl: [
    'pnl',
    'unrealized',
    'unrealized_pnl',
    'pnl_unrealized',
    'pnlUnrealized',
    'unrealizedProfit',
    'pnl_usd',
    'pnlUsd',
    'pnl_usdt',
    'computedPnl',
    'computed_pnl',
    'realized',
    'realized_pnl',
    'realizedPnl',
    'realizedPNL',
    'realized_profit',
    'realizedProfit',
    'pnl_realized',
    'pnlRealized',
  ],
  leverage: ['leverage', 'lever', 'leverage_value', 'leverageValue'],
  margin: [
    'margin',
    'positionMargin',
    'isolatedMargin',
    'initialMargin',
    'positionInitialMargin',
    'margin_usd',
    'marginUsd',
    'margin_usdt',
  ],
  side: ['side', 'positionSide', 'direction'],
};

const COMPLETED_POSITION_PNL_KEYS = Array.from(
  new Set([...(ACTIVE_POSITION_ALIASES.pnl || [])])
);

const COMPLETED_POSITION_R_KEYS = [
  'r',
  'r_multiple',
  'rMultiple',
  'reward_r',
  'rewardR',
  'pnl_r',
  'pnlR',
  'pnl_r_multiple',
  'pnlRMultiple',
  'rr',
  'rratio',
];

const POSITION_MEANINGFUL_FIELD_KEYS = Array.from(
  new Set(
    [
      ...ACTIVE_POSITION_SIGNED_SIZE_KEYS,
      ...ACTIVE_POSITION_NOTIONAL_KEYS,
      ...(ACTIVE_POSITION_ALIASES.entry || []),
      ...(ACTIVE_POSITION_ALIASES.mark || []),
      ...(ACTIVE_POSITION_ALIASES.pnl || []),
      ...(ACTIVE_POSITION_ALIASES.margin || []),
      ...(ACTIVE_POSITION_ALIASES.roe || []),
      ...TAKE_PROFIT_FIELD_KEYS,
      ...STOP_LOSS_FIELD_KEYS,
    ].filter(Boolean),
  ),
);

function hasMeaningfulPositionFields(position) {
  if (!position || typeof position !== 'object') {
    return false;
  }
  for (const key of POSITION_MEANINGFUL_FIELD_KEYS) {
    if (!(key in position)) continue;
    const raw = unwrapPositionValue(position[key]);
    const numeric = toNumeric(raw);
    if (Number.isFinite(numeric) && Math.abs(numeric) > 1e-9) {
      return true;
    }
  }
  return false;
}

function hasPositionManagementContext(position) {
  if (!position || typeof position !== 'object') {
    return false;
  }
  const managementEvents = normaliseManagementEvents(position);
  if (Array.isArray(managementEvents) && managementEvents.length > 0) {
    return true;
  }
  const exitReason = extractPositionManagementExitReason(position);
  if (exitReason) {
    return true;
  }
  const managementBlock = position.management;
  if (managementBlock && typeof managementBlock === 'object') {
    const managementHints = [
      'last_exit_reason',
      'last_exit_qty',
      'max_favourable_move',
      'expected_r_stop',
      'expected_r_stop_hit',
    ];
    return managementHints.some((key) => Boolean(managementBlock[key]));
  }
  return false;
}

function shouldDisplayActivePosition(position) {
  if (!position || typeof position !== 'object') {
    return false;
  }
  const symbol = getNormalizedActivePositionSymbol(position);
  if (!symbol) {
    return false;
  }
  if (hasMeaningfulPositionFields(position)) {
    return true;
  }
  return hasPositionManagementContext(position);
}

const ACTIVE_POSITION_FIELD_LABELS = {
  symbol: 'Symbol',
  size: 'Size',
  entry: 'Entry price',
  mark: 'Mark price',
  leverage: 'Leverage',
  margin: 'Margin',
  pnl: 'PNL (ROE%)',
};

function applyActivePositionLabel(cell, key) {
  if (cell && ACTIVE_POSITION_FIELD_LABELS[key]) {
    cell.setAttribute('data-label', ACTIVE_POSITION_FIELD_LABELS[key]);
  }
}

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
    const mapped = mapPositionCollection(collection).filter(
      (item) => shouldDisplayActivePosition(item) && !isPositionLikelyClosed(item),
    );
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

function inspectPositionSize(position) {
  const info = { hasZero: false, hasNonZero: false };
  const sizeKeys = ACTIVE_POSITION_ALIASES.size || [];

  if (!position || typeof position !== 'object') {
    return info;
  }

  for (const key of sizeKeys) {
    if (!(key in position)) continue;
    const considerNumeric = (value) => {
      const numeric = toNumeric(value);
      if (!Number.isFinite(numeric)) return;
      if (Math.abs(numeric) < 1e-9) {
        info.hasZero = true;
      } else {
        info.hasNonZero = true;
      }
    };

    const direct = unwrapPositionValue(position[key]);
    considerNumeric(direct);
    if (info.hasNonZero) {
      return info;
    }

    const raw = position[key];
    if (Array.isArray(raw) && raw.length > 0) {
      for (const candidate of raw) {
        considerNumeric(unwrapPositionValue(candidate));
        if (info.hasNonZero) {
          return info;
        }
      }
    }
  }

  return info;
}

function sizeLooksClosed(position, sizeInfo) {
  const info = sizeInfo ?? inspectPositionSize(position);
  if (info.hasNonZero) {
    return false;
  }
  return info.hasZero;
}

function isPositionLikelyClosed(position) {
  if (!position || typeof position !== 'object') {
    return false;
  }

  const sizeInfo = inspectPositionSize(position);
  const hasOpenSize = sizeInfo.hasNonZero;

  for (const key of POSITION_CLOSED_FLAG_KEYS) {
    if (!(key in position)) continue;
    const flag = parseFlagValue(position[key], CLOSED_FLAG_POSITIVE_TOKENS, CLOSED_FLAG_NEGATIVE_TOKENS);
    if (flag === true) {
      if (hasOpenSize) {
        continue;
      }
      return true;
    }
    if (flag === false) {
      return false;
    }
  }

  for (const key of POSITION_OPEN_FLAG_KEYS) {
    if (!(key in position)) continue;
    const flag = parseFlagValue(position[key], OPEN_FLAG_POSITIVE_TOKENS, OPEN_FLAG_NEGATIVE_TOKENS);
    if (flag === true) {
      return false;
    }
    if (flag === false) {
      if (hasOpenSize) {
        continue;
      }
      return true;
    }
  }

  for (const key of POSITION_STATUS_KEYS) {
    if (!(key in position)) continue;
    const tokens = tokeniseTextValue(position[key]);
    if (!tokens.length) continue;
    if (tokens.some((token) => POSITION_CLOSED_STATUS_TOKENS.includes(token))) {
      if (hasOpenSize) {
        continue;
      }
      return true;
    }
    if (tokens.some((token) => POSITION_OPEN_STATUS_TOKENS.includes(token))) {
      return false;
    }
  }

  if (hasClosedTimestamp(position) && !hasOpenSize) {
    return true;
  }

  if (sizeLooksClosed(position, sizeInfo)) {
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

function collectFieldCandidates(field) {
  if (field === undefined || field === null) return [];
  if (typeof field === 'number') return [field];
  if (typeof field === 'string') {
    const trimmed = field.trim();
    return trimmed ? [trimmed] : [];
  }
  if (typeof field !== 'object') return [];

  const candidates = [];
  const seen = new Set();

  const visit = (candidate) => {
    if (candidate === undefined || candidate === null) return;
    if (typeof candidate === 'number') {
      candidates.push(candidate);
      return;
    }
    if (typeof candidate === 'string') {
      const trimmed = candidate.trim();
      if (trimmed) {
        candidates.push(trimmed);
      }
      return;
    }
    if (Array.isArray(candidate)) {
      candidate.forEach((item) => visit(unwrapPositionValue(item)));
      return;
    }
    if (typeof candidate === 'object') {
      if (seen.has(candidate)) return;
      seen.add(candidate);
      const prioritizedKeys = [
        'value',
        'price',
        'amount',
        'qty',
        'trigger',
        'level',
        'target',
        'tp',
        'sl',
        'take_profit',
        'takeProfit',
        'stop_loss',
        'stopLoss',
        'next',
        'next_price',
        'nextPrice',
        'price_next',
      ];
      prioritizedKeys.forEach((key) => {
        if (key in candidate) {
          visit(unwrapPositionValue(candidate[key]));
        }
      });
      Object.values(candidate).forEach((value) => visit(unwrapPositionValue(value)));
    }
  };

  if (Number.isFinite(field.numeric)) {
    visit(field.numeric);
  }
  if ('value' in field) {
    visit(field.value);
  }
  if ('raw' in field) {
    visit(field.raw);
  }

  return candidates;
}

function resolveNumericFromCandidates(candidates) {
  for (const candidate of candidates) {
    const numeric = toNumeric(candidate);
    if (Number.isFinite(numeric)) {
      return numeric;
    }
  }
  return null;
}

function resolveFieldNumeric(field) {
  if (!field) return null;
  if (typeof field === 'number' || typeof field === 'string') {
    const numeric = toNumeric(field);
    return Number.isFinite(numeric) ? numeric : null;
  }
  const candidates = collectFieldCandidates(field);
  return resolveNumericFromCandidates(candidates);
}

function normalizeSymbolValue(symbol) {
  if (symbol === undefined || symbol === null) return '';
  return symbol.toString().trim().toUpperCase();
}

function getNormalizedActivePositionSymbol(position) {
  if (!position || typeof position !== 'object') return '';
  const aliasField = pickFieldValue(position, ACTIVE_POSITION_ALIASES.symbol || []);
  const aliasSymbol = normalizeSymbolValue(aliasField.value);
  if (aliasSymbol) return aliasSymbol;
  return normalizeSymbolValue(position.symbol);
}

function hasActivePositionForSymbol(symbol) {
  const target = normalizeSymbolValue(symbol);
  if (!target) return false;
  return activePositions.some((position) => getNormalizedActivePositionSymbol(position) === target);
}

function extractProposalSymbol(proposal) {
  if (!proposal || typeof proposal !== 'object') return '';
  const candidates = [proposal.symbol, proposal.sym, proposal.ticker, proposal.pair, proposal.asset];
  for (let index = 0; index < candidates.length; index += 1) {
    const normalized = normalizeSymbolValue(candidates[index]);
    if (normalized) {
      return normalized;
    }
  }
  return '';
}

function tradeProposalConflictsWithActivePosition(proposal) {
  const normalizedSymbol = extractProposalSymbol(proposal);
  if (!normalizedSymbol) {
    return false;
  }
  return hasActivePositionForSymbol(normalizedSymbol);
}

function formatSignedNumber(value, digits = 2) {
  if (!Number.isFinite(value)) return null;
  const abs = Math.abs(value).toFixed(digits);
  if (value > 0) return `+${abs}`;
  if (value < 0) return `-${abs}`;
  return abs;
}

function extractFieldStringSource(field) {
  if (!field) return null;
  if (typeof field.value === 'string' && field.value.trim()) {
    return field.value;
  }
  if (Array.isArray(field.raw)) {
    for (const entry of field.raw) {
      if (typeof entry === 'string' && entry.trim()) {
        return entry;
      }
      if (entry && typeof entry === 'object') {
        if (typeof entry.value === 'string' && entry.value.trim()) {
          return entry.value;
        }
        if (typeof entry.price === 'string' && entry.price.trim()) {
          return entry.price;
        }
      }
    }
  }
  return null;
}

function parseLocalizedPercent(field) {
  const source = extractFieldStringSource(field);
  if (typeof source !== 'string') return null;
  const trimmed = source.trim();
  if (!trimmed || !trimmed.includes(',')) {
    return null;
  }

  const lastComma = trimmed.lastIndexOf(',');
  if (lastComma === -1) return null;
  const digitsAfterComma = trimmed.length - lastComma - 1;
  if (digitsAfterComma <= 0) {
    return null;
  }

  const hasPercentSign = trimmed.includes('%');
  const lastDot = trimmed.lastIndexOf('.');
  const commaLooksDecimal =
    hasPercentSign || digitsAfterComma !== 3 || lastDot === -1 || lastDot < lastComma;
  if (!commaLooksDecimal) {
    return null;
  }

  let normalized = trimmed.replace(/\s+/g, '');
  if (lastDot > lastComma && lastDot !== -1) {
    normalized = normalized.replace(/,/g, '');
  } else {
    normalized = normalized.replace(/\./g, '');
    normalized = normalized.replace(/,/g, '.');
  }
  normalized = normalized.replace(/[^0-9+-.eE]/g, '');
  if (!normalized || normalized === '+' || normalized === '-') {
    return null;
  }
  const parsed = Number(normalized);
  return Number.isFinite(parsed) ? parsed : null;
}

function formatPercentField(field, digits = 2) {
  if (!field) {
    return null;
  }

  let numeric = field.numeric;
  const localized = parseLocalizedPercent(field);
  if (!Number.isFinite(numeric) && Number.isFinite(localized)) {
    numeric = localized;
  } else if (Number.isFinite(numeric) && Number.isFinite(localized) && numeric < 0) {
    numeric = localized;
  }

  if (!Number.isFinite(numeric)) {
    return null;
  }

  const key = (field.key || '').toString();
  const keyHintsPercent = /percent|pct/i.test(key);
  if (!keyHintsPercent && Math.abs(numeric) <= 10) {
    numeric *= 100;
  }
  const abs = Math.abs(numeric).toFixed(digits);
  const sign = numeric > 0 ? '+' : numeric < 0 ? '-' : '';
  return { text: `${sign}${abs}%`, numeric };
}

function computeActivePositionsTotalPnl(positions) {
  const entries = Array.isArray(positions) ? positions : [];
  let total = 0;
  let counted = 0;

  entries.forEach((position) => {
    const pnlField = pickNumericField(position, ACTIVE_POSITION_ALIASES.pnl || []);
    if (Number.isFinite(pnlField.numeric)) {
      total += pnlField.numeric;
      counted += 1;
    }
  });

  if (counted === 0) {
    if (entries.length === 0) {
      return { text: '0.00 USDT', tone: null };
    }
    return { text: '–', tone: null };
  }

  const formatted = formatSignedNumber(total, 2) ?? '0.00';
  const tone = total > 0 ? 'profit' : total < 0 ? 'loss' : null;
  return { text: `${formatted} USDT`, tone };
}

function formatPositionSize(value) {
  if (!Number.isFinite(value)) return '–';
  const abs = Math.abs(value);
  let formatted;
  if (abs >= 1000) {
    formatted = abs.toLocaleString(undefined, { maximumFractionDigits: 0 });
  } else if (abs >= 100) {
    formatted = abs.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  } else if (abs >= 10) {
    formatted = abs.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  } else if (abs >= 1) {
    formatted = abs.toLocaleString(undefined, { minimumFractionDigits: 3, maximumFractionDigits: 3 });
  } else if (abs >= 0.1) {
    formatted = abs.toLocaleString(undefined, { minimumFractionDigits: 4, maximumFractionDigits: 4 });
  } else {
    formatted = abs.toLocaleString(undefined, { minimumFractionDigits: 5, maximumFractionDigits: 5 });
  }
  return `${formatted} USDT`;
}

function formatLeverage(value) {
  if (!Number.isFinite(value) || value <= 0) return '–';
  const abs = Math.abs(value);
  let maximumFractionDigits = 2;
  if (abs >= 100) {
    maximumFractionDigits = 0;
  } else if (abs >= 10) {
    maximumFractionDigits = 1;
  }
  const formatted = abs.toLocaleString(undefined, {
    minimumFractionDigits: 0,
    maximumFractionDigits,
  });
  return `${formatted}×`;
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

function extractPositionSide(position, sizeField, signedQuantityField) {
  const field = pickFieldValue(position, ACTIVE_POSITION_ALIASES.side || []);
  if (field.value) return field.value;
  const numericSources = [signedQuantityField, sizeField].filter(
    (candidate) => candidate && Number.isFinite(candidate.numeric),
  );
  for (let index = 0; index < numericSources.length; index += 1) {
    const numeric = numericSources[index].numeric;
    if (numeric > 0) return 'BUY';
    if (numeric < 0) return 'SELL';
  }
  return null;
}

function normalizeTpSlMeta(meta) {
  if (!meta || typeof meta !== 'object') return null;
  const normalized = {};
  const priceKeys = ['price', 'stopPrice', 'triggerPrice', 'limitPrice'];
  for (const key of priceKeys) {
    if (!(key in meta)) continue;
    const numeric = toNumeric(meta[key]);
    if (!Number.isFinite(numeric) || numeric <= 0) continue;
    const absolute = Math.abs(numeric);
    if (normalized.price == null) {
      normalized.price = absolute;
    }
    normalized[key] = absolute;
  }
  if (meta.workingType) {
    normalized.workingType = meta.workingType.toString().toUpperCase();
  }
  if (meta.type) {
    normalized.type = meta.type.toString().toUpperCase();
  }
  if (meta.positionSide) {
    normalized.positionSide = meta.positionSide;
  }
  ['reduceOnly', 'closePosition', 'inferredReduceOnly'].forEach((flag) => {
    if (Object.prototype.hasOwnProperty.call(meta, flag)) {
      normalized[flag] = Boolean(meta[flag]);
    }
  });
  if (meta.source) {
    normalized.source = meta.source;
  }
  return normalized;
}

const TP_SL_BOOLEAN_POSITIVE_TOKENS = ['true', 'yes', 'on', 'enabled', 'active', 'enable'];
const TP_SL_BOOLEAN_NEGATIVE_TOKENS = ['false', 'no', 'off', 'disabled', 'inactive', 'disable'];
const TP_SL_TAKE_KIND_HINTS = ['TAKE', 'TP', 'TARGET', 'PROFIT'];
const TP_SL_STOP_KIND_HINTS = ['STOP', 'SL', 'LOSS', 'RISK', 'CUT'];

function interpretTpSlFlag(value) {
  return parseFlagValue(value, TP_SL_BOOLEAN_POSITIVE_TOKENS, TP_SL_BOOLEAN_NEGATIVE_TOKENS);
}

function inferTpSlKindFromText(value) {
  if (!value) return null;
  const normalized = value.toString().toUpperCase();
  if (TP_SL_TAKE_KIND_HINTS.some((hint) => normalized.includes(hint))) {
    return 'take';
  }
  if (TP_SL_STOP_KIND_HINTS.some((hint) => normalized.includes(hint))) {
    return 'stop';
  }
  return null;
}

function inferTpSlKindFromValue(value) {
  if (!value || typeof value !== 'object') return null;

  const booleanMappings = [
    {
      keys: [
        'isTp',
        'is_tp',
        'isTake',
        'is_take',
        'isTakeProfit',
        'tpActive',
        'tp_active',
        'takeActive',
        'take_active',
        'takeProfitActive',
      ],
      kind: 'take',
    },
    {
      keys: [
        'isSl',
        'is_sl',
        'isStop',
        'is_stop',
        'isStopLoss',
        'slActive',
        'sl_active',
        'stopActive',
        'stop_active',
        'stopLossActive',
      ],
      kind: 'stop',
    },
  ];

  for (const mapping of booleanMappings) {
    for (const key of mapping.keys) {
      if (!Object.prototype.hasOwnProperty.call(value, key)) continue;
      const interpreted = interpretTpSlFlag(value[key]);
      if (interpreted === true) return mapping.kind;
      if (interpreted === false) continue;
    }
  }

  const textFields = [
    value.kind,
    value.tag,
    value.type,
    value.orderType,
    value.triggerType,
    value.stopType,
    value.category,
    value.label,
    value.name,
    value.strategyType,
  ];

  for (const field of textFields) {
    const inferred = inferTpSlKindFromText(field);
    if (inferred) return inferred;
  }

  return null;
}

function matchesTpSlKind(normalized, source, expectedKind) {
  const inferred = inferTpSlKindFromValue(source) || inferTpSlKindFromValue(normalized);
  if (!inferred) return true;
  return inferred === expectedKind;
}

function extractTpSlEntry(position, kind) {
  const keys = kind === 'take' ? TAKE_PROFIT_FIELD_KEYS : STOP_LOSS_FIELD_KEYS;
  const numericField = pickNumericField(position, keys);
  let price =
    Number.isFinite(numericField.numeric) && Math.abs(numericField.numeric) > 0
      ? Math.abs(numericField.numeric)
      : null;

  let meta = null;
  const bucketCandidates = [];
  if (position && typeof position === 'object') {
    if (position.tp_sl_meta && typeof position.tp_sl_meta === 'object') {
      bucketCandidates.push(position.tp_sl_meta);
    }
    if (position.tpSlMeta && typeof position.tpSlMeta === 'object') {
      bucketCandidates.push(position.tpSlMeta);
    }
    if (position.bracket_meta && typeof position.bracket_meta === 'object') {
      bucketCandidates.push(position.bracket_meta);
    }
    if (position.brackets && typeof position.brackets === 'object') {
      bucketCandidates.push(position.brackets);
    }
  }

  const directKeys = kind === 'take' ? ['take', 'tp'] : ['stop', 'sl'];
  const searchKeys = [
    ...new Set([
      ...directKeys,
      ...keys,
      'price',
      'stopPrice',
      'triggerPrice',
      'limitPrice',
      'orders',
      'legs',
      'list',
      'items',
      'entries',
      'targets',
      'stops',
      'levels',
      'data',
      'payload',
      'children',
      'tpOrders',
      'tp_orders',
      'slOrders',
      'sl_orders',
    ]),
  ];
  const searchKeySet = new Set(searchKeys);

  const ensurePrice = (value) => {
    const numeric = toNumeric(value);
    if (!Number.isFinite(numeric) || numeric <= 0) return;
    if (!Number.isFinite(price)) {
      price = Math.abs(numeric);
    }
  };

  const visited = new Set();

  const resolveMeta = (candidate) => {
    if (meta) return true;
    if (candidate === undefined || candidate === null) return false;
    if (Array.isArray(candidate)) {
      for (const item of candidate) {
        if (resolveMeta(item)) return true;
      }
      return false;
    }
    if (typeof candidate !== 'object') {
      ensurePrice(candidate);
      return false;
    }
    if (visited.has(candidate)) {
      return false;
    }
    visited.add(candidate);

    const normalized = normalizeTpSlMeta(candidate);
    if (normalized && matchesTpSlKind(normalized, candidate, kind)) {
      if (!Number.isFinite(price) && Number.isFinite(normalized.price)) {
        price = Math.abs(normalized.price);
      }
      meta = normalized;
      return true;
    }

    for (const key of searchKeys) {
      if (!Object.prototype.hasOwnProperty.call(candidate, key)) continue;
      if (resolveMeta(candidate[key])) {
        return true;
      }
    }

    for (const key of Object.keys(candidate)) {
      if (searchKeySet.has(key)) continue;
      if (resolveMeta(candidate[key])) {
        return true;
      }
    }

    return false;
  };

  for (const bucket of bucketCandidates) {
    if (resolveMeta(bucket)) {
      break;
    }
  }

  if (!Number.isFinite(price) && meta) {
    const metaPrice = toNumeric(meta.price);
    if (Number.isFinite(metaPrice) && Math.abs(metaPrice) > 0) {
      price = Math.abs(metaPrice);
    }
  }

  return { price: Number.isFinite(price) && price > 0 ? price : null, meta };
}

function resolveTpSlEffectivePrice(entry) {
  if (!entry || typeof entry !== 'object') return null;

  const candidates = [];
  const seen = new Set();
  const pushCandidate = (value) => {
    const numeric = toNumeric(value);
    if (!Number.isFinite(numeric)) return;
    const absolute = Math.abs(numeric);
    if (absolute <= 0) return;
    if (seen.has(absolute)) return;
    seen.add(absolute);
    candidates.push(absolute);
  };

  const meta = entry.meta && typeof entry.meta === 'object' ? entry.meta : null;
  if (meta) {
    ['triggerPrice', 'stopPrice', 'price', 'limitPrice'].forEach((key) => {
      if (Object.prototype.hasOwnProperty.call(meta, key)) {
        pushCandidate(meta[key]);
      }
    });
  }

  ['triggerPrice', 'stopPrice', 'price', 'limitPrice'].forEach((key) => {
    if (Object.prototype.hasOwnProperty.call(entry, key)) {
      pushCandidate(entry[key]);
    }
  });

  if (Number.isFinite(entry.price)) {
    pushCandidate(entry.price);
  }

  return candidates.length ? candidates[0] : null;
}

function computePositionProgressValue(takeEntry, stopEntry, markPrice, side) {
  const takePrice = resolveTpSlEffectivePrice(takeEntry);
  const stopPrice = resolveTpSlEffectivePrice(stopEntry);
  const mark = Number.isFinite(markPrice) ? Math.abs(markPrice) : null;

  if (!Number.isFinite(takePrice) || !Number.isFinite(stopPrice) || !Number.isFinite(mark)) {
    return null;
  }
  if (takePrice === stopPrice) {
    return null;
  }

  const min = Math.min(takePrice, stopPrice);
  const max = Math.max(takePrice, stopPrice);
  const clamped = Math.min(Math.max(mark, min), max);
  const relative = (clamped - min) / (max - min);
  let profitIsMax = null;

  if (side) {
    const normalized = side.toString().toLowerCase();
    if (normalized === 'buy' || normalized === 'long') {
      profitIsMax = true;
    } else if (normalized === 'sell' || normalized === 'short') {
      profitIsMax = false;
    }
  }

  if (profitIsMax === null) {
    profitIsMax = takePrice >= stopPrice;
  }
  const ratio = profitIsMax ? relative : 1 - relative;

  return Math.max(0, Math.min(1, ratio));
}

function computeProgressIndicatorColor(progressValue) {
  if (!Number.isFinite(progressValue)) {
    return null;
  }

  const clamped = Math.max(0, Math.min(1, progressValue));
  const start = { r: 239, g: 68, b: 68 }; // Stop loss (red)
  const end = { r: 34, g: 197, b: 94 }; // Take profit (green)

  const mix = (from, to) => Math.round(from + (to - from) * clamped);
  const r = mix(start.r, end.r);
  const g = mix(start.g, end.g);
  const b = mix(start.b, end.b);

  return {
    solid: `rgb(${r}, ${g}, ${b})`,
    glow: `rgba(${r}, ${g}, ${b}, 0.45)`,
    halo: `rgba(${r}, ${g}, ${b}, 0.2)`,
  };
}

const MANAGEMENT_EVENT_LABELS = {
  fasttp_exit: () => translate('active.management.fasttp', 'FastTP exit adjusted'),
  breakeven: () => translate('active.management.breakeven', 'Stop moved to breakeven'),
  trail: () => translate('active.management.trail', 'Trailing stop tightened'),
  auto_half_take_profit: () =>
    translate('active.management.autoHalf', 'Auto take-profit scaled position'),
  scale_half: () => translate('active.management.scaleHalf', 'Slow scale-out executed'),
  time_cut: () => translate('active.management.timeCut', 'Time-based reduction executed'),
  reduce_only: () => translate('active.management.reduceOnly', 'Reduce-only order placed'),
};

function formatManagementEventLabel(action) {
  if (!action) return translate('active.management.generic', 'Bot adjusted this position');
  const normalized = action.toString().toLowerCase();
  const resolver = MANAGEMENT_EVENT_LABELS[normalized];
  if (typeof resolver === 'function') {
    return resolver();
  }
  return translate('active.management.generic', 'Bot adjusted this position');
}

function parseManagementEventTimestamp(rawTs) {
  if (rawTs == null) return null;
  let ts = Number(rawTs);
  if (Number.isFinite(ts)) {
    if (ts > 1e12) {
      return ts / 1000;
    }
    return ts;
  }
  const numeric = toNumeric(rawTs);
  if (Number.isFinite(numeric)) {
    return numeric > 1e12 ? numeric / 1000 : numeric;
  }
  const parsed = Date.parse(rawTs);
  if (Number.isFinite(parsed)) {
    return parsed / 1000;
  }
  return null;
}

function normaliseManagementEvents(position) {
  if (!position || typeof position !== 'object') {
    return [];
  }

  const pools = [];
  const direct = position.management_events || position.managementEvents;
  if (Array.isArray(direct)) {
    pools.push(...direct);
  }
  const management = position.management;
  if (management && Array.isArray(management.events)) {
    pools.push(...management.events);
  }

  const normalized = pools
    .map((entry) => {
      if (!entry || typeof entry !== 'object') return null;
      const rawAction =
        entry.action || entry.event || entry.type || entry.kind || entry.reason || entry.name;
      if (!rawAction) return null;
      const ts = parseManagementEventTimestamp(entry.ts || entry.time || entry.timestamp || entry.at);
      return {
        action: rawAction.toString().toLowerCase(),
        rawAction,
        ts,
        data: entry,
      };
    })
    .filter(Boolean);

  normalized.sort((a, b) => {
    const aTs = Number.isFinite(a.ts) ? a.ts : -Infinity;
    const bTs = Number.isFinite(b.ts) ? b.ts : -Infinity;
    return bTs - aTs;
  });

  if (normalized.length > MAX_MANAGEMENT_EVENTS) {
    return normalized.slice(0, MAX_MANAGEMENT_EVENTS);
  }
  return normalized;
}

function cacheLatestManagementEvent(position, event) {
  if (!position || typeof position !== 'object' || !event) {
    return;
  }
  const symbolKey = getNormalizedActivePositionSymbol(position);
  if (!symbolKey) {
    return;
  }
  activePositionManagementCache.set(symbolKey, {
    action: event.action,
    rawAction: event.rawAction,
    ts: event.ts,
    data: event.data,
  });
}

function recallCachedManagementEvent(position) {
  const symbolKey = getNormalizedActivePositionSymbol(position);
  if (!symbolKey) {
    return null;
  }
  return activePositionManagementCache.get(symbolKey) || null;
}

function clearCachedManagementEvent(position) {
  const symbolKey = getNormalizedActivePositionSymbol(position);
  if (!symbolKey) {
    return;
  }
  activePositionManagementCache.delete(symbolKey);
}

function resolveLatestManagementEvent(position) {
  const events = normaliseManagementEvents(position);
  if (events.length) {
    const latest = events[0];
    cacheLatestManagementEvent(position, latest);
    return latest;
  }
  return recallCachedManagementEvent(position);
}

function formatManagementRelativeTime(ts) {
  if (!Number.isFinite(ts)) return null;
  const now = Date.now() / 1000;
  const delta = Math.max(0, now - ts);
  if (delta < 45) {
    return translate('active.management.justNow', 'just now');
  }
  if (delta < 90) {
    return translate('active.management.oneMinuteAgo', '1m ago');
  }
  const minutes = Math.floor(delta / 60);
  if (minutes < 60) {
    return translate('active.management.minutesAgo', '{{value}}m ago', { value: minutes });
  }
  const hours = Math.floor(delta / 3600);
  if (hours < 24) {
    return translate('active.management.hoursAgo', '{{value}}h ago', { value: hours });
  }
  const days = Math.floor(delta / 86400);
  return translate('active.management.daysAgo', '{{value}}d ago', { value: days });
}

function updateNotificationRelativeTime(element, timestamp) {
  if (!(element instanceof HTMLElement)) return;
  if (!Number.isFinite(timestamp)) return;
  const timeLabel = element.querySelector('.active-position-management-time');
  if (!timeLabel) return;
  const relative = formatManagementRelativeTime(timestamp);
  if (relative) {
    timeLabel.textContent = relative;
  }
}

function getNotificationElementSymbol(element) {
  if (!(element instanceof HTMLElement)) return '';
  const symbolValue =
    element.dataset?.symbol || element.dataset?.symbolNormalized || element.dataset?.symbolText || '';
  return normalizeSymbolValue(symbolValue);
}

function prunePositionNotificationHistory() {
  if (!Array.isArray(positionNotificationHistory) || !positionNotificationHistory.length) {
    positionNotificationHistory = [];
    return;
  }
  positionNotificationHistory = positionNotificationHistory.filter((entry) => {
    const normalizedSymbol = normalizeSymbolValue(entry?.symbol);
    return Boolean(normalizedSymbol);
  });
}

function rememberPositionNotifications(notifications) {
  if (!Array.isArray(notifications) || notifications.length === 0) {
    return;
  }
  const entries = notifications
    .map((element) => {
      if (!(element instanceof HTMLElement)) return null;
      const normalizedSymbol = getNotificationElementSymbol(element);
      if (!normalizedSymbol) {
        return null;
      }
      const rawTs = element.dataset?.timestamp;
      const parsedTs = rawTs ? Number(rawTs) : Number.NaN;
      const ts = Number.isFinite(parsedTs) ? parsedTs : Date.now() / 1000;
      const symbolText = element
        .querySelector('.active-position-management-symbol')
        ?.textContent?.trim();
      const labelText = element
        .querySelector('.active-position-management-label')
        ?.textContent?.trim();
      const action = element.dataset?.action || '';
      const signature = `${symbolText || ''}|${action}|${ts}|${labelText || ''}`;
      const template = element.cloneNode(true);
      if (template && Number.isFinite(ts)) {
        template.dataset.timestamp = ts.toString();
      }
      if (template) {
        template.dataset.symbol = normalizedSymbol;
      }
      return { ts, signature, template, symbol: normalizedSymbol };
    })
    .filter((entry) => entry && entry.template);

  if (!entries.length) {
    return;
  }

  const merged = [...entries, ...positionNotificationHistory];
  const seen = new Set();
  positionNotificationHistory = merged.filter((entry) => {
    const symbol = normalizeSymbolValue(entry?.symbol);
    const key = entry.signature || `${entry.ts}|${entry.template?.textContent || ''}`;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return Boolean(entry.template);
  });
  positionNotificationHistory.sort((a, b) => b.ts - a.ts);
  if (positionNotificationHistory.length > POSITION_NOTIFICATION_HISTORY_LIMIT) {
    positionNotificationHistory.length = POSITION_NOTIFICATION_HISTORY_LIMIT;
  }
}

function buildHistoricalNotifications(limit = 5) {
  if (!positionNotificationHistory.length) {
    return [];
  }
  const nodes = [];
  positionNotificationHistory.slice(0, limit).forEach((entry) => {
    const normalizedSymbol = normalizeSymbolValue(entry?.symbol);
    if (!normalizedSymbol) {
      return;
    }
    const template = entry?.template;
    if (!template) return;
    const clone = template.cloneNode(true);
    if (!clone) return;
    if (Number.isFinite(entry.ts)) {
      clone.dataset.timestamp = entry.ts.toString();
      updateNotificationRelativeTime(clone, entry.ts);
    }
    clone.dataset.symbol = normalizedSymbol;
    if (!clone.hasAttribute('role')) {
      clone.setAttribute('role', 'listitem');
    }
    nodes.push(clone);
  });
  return nodes;
}

function refreshRenderedPositionNotifications() {
  if (!activePositionsNotifications) return;
  Array.from(activePositionsNotifications.children || []).forEach((element) => {
    if (!(element instanceof HTMLElement)) return;
    const rawTs = element.dataset?.timestamp;
    const parsedTs = rawTs ? Number(rawTs) : Number.NaN;
    if (!Number.isFinite(parsedTs)) return;
    updateNotificationRelativeTime(element, parsedTs);
  });
}

function renderPositionNotifications(notifications) {
  const relevantNotifications = Array.isArray(notifications)
    ? notifications.filter((notification) => notification instanceof HTMLElement)
    : [];
  const hasNotifications = relevantNotifications.length > 0;

  if (activePositionsNotifications) {
    const notificationFragment = document.createDocumentFragment();
    relevantNotifications.forEach((notification) => {
      if (notification && !notification.hasAttribute('role')) {
        notification.setAttribute('role', 'listitem');
      }
      notificationFragment.append(notification);
    });
    activePositionsNotifications.replaceChildren(notificationFragment);
    activePositionsNotifications.removeAttribute('hidden');
  }

  setPositionNotificationsEmptyState(!hasNotifications);

  if (hasNotifications) {
    notifications.forEach((notification) => {
      if (!(notification instanceof HTMLElement)) return;
      const rawTs = notification.dataset?.timestamp;
      const ts = rawTs ? Number(rawTs) : Number.NaN;
      if (Number.isFinite(ts)) {
        updateNotificationRelativeTime(notification, ts);
      }
    });
  }
}

function setPositionNotificationsEmptyState(isEmpty) {
  if (!activePositionsNotificationsEmpty) return;
  if (isEmpty) {
    activePositionsNotificationsEmpty.removeAttribute('hidden');
  } else {
    activePositionsNotificationsEmpty.setAttribute('hidden', 'true');
  }
}

function buildCompletedPositionCard(entry) {
  if (!entry || !entry.position) {
    return null;
  }
  const position = entry.position;
  const referenceTimestamp = Number.isFinite(entry.ts)
    ? Number(entry.ts)
    : getPositionTimestamp(position);
  const pnlField = pickNumericField(position, COMPLETED_POSITION_PNL_KEYS);
  const pnlNumeric = Number.isFinite(pnlField.numeric) ? pnlField.numeric : null;
  const pnlTone = pnlNumeric > 0 ? 'profit' : pnlNumeric < 0 ? 'loss' : 'neutral';
  const pnlDisplay = pnlNumeric !== null
    ? `${formatSignedNumber(pnlNumeric, 2)} USDT`
    : pnlField.value
      ? pnlField.value.toString()
      : '—';
  const roeField = pickFieldValue(position, ACTIVE_POSITION_ALIASES.roe || []);
  const roeNumeric = toNumeric(roeField.value);
  let roeDisplay = null;
  if (Number.isFinite(roeNumeric)) {
    roeDisplay = `${formatSignedNumber(roeNumeric, 2)}%`;
  } else {
    const roeText = extractFieldStringSource(roeField);
    if (roeText) {
      roeDisplay = roeText;
    }
  }
  const rField = pickNumericField(position, COMPLETED_POSITION_R_KEYS);
  const rTone = Number.isFinite(rField.numeric)
    ? rField.numeric > 0
      ? 'profit'
      : rField.numeric < 0
        ? 'loss'
        : 'neutral'
    : null;
  const rDisplay = Number.isFinite(rField.numeric)
    ? `${formatSignedNumber(rField.numeric, 2)} R`
    : null;
  const notionalField = pickNumericField(position, ACTIVE_POSITION_NOTIONAL_KEYS || []);
  const notionalDisplay = Number.isFinite(notionalField.numeric)
    ? `${formatNumber(Math.abs(notionalField.numeric), 2)} USDT`
    : null;
  const signedSizeField = pickNumericField(position, ACTIVE_POSITION_SIGNED_SIZE_KEYS || []);
  const side = extractPositionSide(position, notionalField, signedSizeField);
  const reasonCode = extractPositionManagementExitReason(position);
  const reasonLabel = reasonCode
    ? friendlyReason(reasonCode)
    : translate('trades.completed.noReason', 'No exit reason logged.');
  const postmortemSummary = extractPostmortemSummary(position);
  const relativeTime = Number.isFinite(referenceTimestamp) ? formatRelativeTime(referenceTimestamp) : null;
  const absoluteTimeLabel = Number.isFinite(referenceTimestamp)
    ? formatTimestamp(new Date(referenceTimestamp * 1000).toISOString())
    : null;

  const card = document.createElement('button');
  card.type = 'button';
  card.className = 'completed-position-card';
  card.setAttribute('role', 'listitem');
  if (pnlTone && pnlTone !== 'neutral') {
    card.dataset.pnl = pnlTone;
  }

  const header = document.createElement('div');
  header.className = 'completed-position-card__header';

  const title = document.createElement('div');
  title.className = 'completed-position-card__title';
  const symbol = document.createElement('span');
  symbol.className = 'completed-position-card__symbol';
  symbol.textContent = getPositionSymbol(position) || '—';
  title.append(symbol);
  const sideBadge = buildSideBadge(side);
  if (sideBadge) {
    sideBadge.classList.add('completed-position-card__side');
    title.append(sideBadge);
  }
  header.append(title);

  const pnlEl = document.createElement('span');
  const pnlToneClass = pnlTone && pnlTone !== 'neutral' ? `tone-${pnlTone}` : '';
  pnlEl.className = `completed-position-card__pnl ${pnlToneClass}`.trim();
  pnlEl.textContent = pnlDisplay;
  header.append(pnlEl);

  card.append(header);

  const meta = document.createElement('div');
  meta.className = 'completed-position-card__meta';
  if (relativeTime) {
    const time = document.createElement('span');
    time.textContent = relativeTime;
    if (absoluteTimeLabel && absoluteTimeLabel !== '–') {
      time.title = absoluteTimeLabel;
    }
    meta.append(time);
  }
  const reason = document.createElement('span');
  reason.className = 'completed-position-card__reason';
  reason.textContent = reasonLabel;
  meta.append(reason);
  card.append(meta);

  const metrics = document.createElement('div');
  metrics.className = 'completed-position-card__metrics';
  const metricEntries = [
    {
      label: translate('trades.completed.pnl', 'Realized PNL'),
      value: pnlDisplay,
      tone: pnlTone,
    },
    {
      label: 'Notional',
      value: notionalDisplay,
    },
    {
      label: 'R multiple',
      value: rDisplay,
      tone: rTone,
    },
    {
      label: 'ROE',
      value: roeDisplay,
    },
  ].filter((metric) => metric.value);
  metricEntries.forEach((metric) => {
    const item = document.createElement('div');
    item.className = 'completed-position-card__metric';
    const label = document.createElement('span');
    label.className = 'completed-position-card__metric-label';
    label.textContent = metric.label;
    const value = document.createElement('span');
    value.className = 'completed-position-card__metric-value';
    value.textContent = metric.value;
    if (metric.tone && metric.tone !== 'neutral') {
      value.classList.add(`tone-${metric.tone}`);
    }
    item.append(label, value);
    metrics.append(item);
  });
  if (metrics.childElementCount > 0) {
    card.append(metrics);
  }

  if (postmortemSummary) {
    const snippet = document.createElement('div');
    snippet.className = 'completed-position-card__postmortem';
    const label = document.createElement('span');
    label.className = 'completed-position-card__postmortem-label';
    label.textContent = translate('trades.postmortem.label', 'Post-mortem coach');
    const text = document.createElement('p');
    text.className = 'completed-position-card__postmortem-text';
    text.textContent = postmortemSummary;
    snippet.append(label, text);
    card.append(snippet);
  }

  const actions = document.createElement('div');
  actions.className = 'completed-position-card__actions';
  const actionHint = document.createElement('span');
  actionHint.className = 'completed-position-card__hint';
  actionHint.textContent = translate('trades.viewDetails', 'View details');
  actions.append(actionHint);
  card.append(actions);

  const symbolLabel = getPositionSymbol(position) || translate('trades.completed.title', 'Completed positions');
  const accessibleTime = relativeTime || absoluteTimeLabel || '';
  card.setAttribute('aria-label', `${symbolLabel} · ${accessibleTime} · ${reasonLabel}`.trim());

  card.addEventListener('click', () => {
    openCompletedPositionModal(position, { timestamp: referenceTimestamp, returnTarget: card });
  });

  return card;
}

function normalizeStatNumber(value, fallback = NaN) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : fallback;
}

function normalizeStatInteger(value, fallback = NaN) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? Math.round(numeric) : fallback;
}

function syncCompletedPositionsStats(summary) {
  if (!summary || typeof summary !== 'object') {
    return;
  }
  const trades = Math.max(0, normalizeStatInteger(summary.trades ?? summary.count, 0));
  const realizedCandidate =
    summary.realized_pnl ?? summary.realizedPnl ?? summary.total_pnl ?? summary.totalPnl ?? summary.realized;
  const realizedPnl = normalizeStatNumber(realizedCandidate, 0);
  const totalR = normalizeStatNumber(summary.total_r ?? summary.totalR, 0);
  let wins = normalizeStatInteger(summary.wins, NaN);
  let losses = normalizeStatInteger(summary.losses, NaN);
  let draws = normalizeStatInteger(summary.draws, NaN);
  const winRate = normalizeStatNumber(summary.win_rate ?? summary.winRate, NaN);
  if (Number.isNaN(wins) && Number.isFinite(winRate) && trades > 0) {
    wins = Math.round(trades * winRate);
  }
  if (Number.isNaN(wins)) {
    wins = 0;
  }
  if (Number.isNaN(losses)) {
    losses = 0;
  }
  if (Number.isNaN(draws)) {
    draws = 0;
  }
  let accounted = wins + losses + draws;
  if (accounted < trades) {
    draws += trades - accounted;
  } else if (accounted > trades) {
    const overflow = accounted - trades;
    if (draws >= overflow) {
      draws -= overflow;
    } else if (losses >= overflow - draws) {
      losses -= overflow - draws;
      draws = 0;
    }
  }
  completedPositionsStatsTotals = {
    trades,
    realizedPnl,
    totalR,
    wins,
    losses,
    draws,
  };
}

function incrementCompletedPositionsStats(position) {
  if (!position || typeof position !== 'object') {
    return;
  }
  completedPositionsStatsTotals.trades += 1;
  const pnlField = pickNumericField(position, COMPLETED_POSITION_PNL_KEYS);
  if (Number.isFinite(pnlField.numeric)) {
    completedPositionsStatsTotals.realizedPnl += pnlField.numeric;
    if (pnlField.numeric > 0) {
      completedPositionsStatsTotals.wins += 1;
    } else if (pnlField.numeric < 0) {
      completedPositionsStatsTotals.losses += 1;
    } else {
      completedPositionsStatsTotals.draws += 1;
    }
  } else {
    completedPositionsStatsTotals.draws += 1;
  }
  const rField = pickNumericField(position, COMPLETED_POSITION_R_KEYS);
  if (Number.isFinite(rField.numeric)) {
    completedPositionsStatsTotals.totalR += rField.numeric;
  }
}

function buildCompletedPositionsSummaryFromTotals() {
  if (!completedPositionsStatsTotals || completedPositionsStatsTotals.trades <= 0) {
    return null;
  }
  const { trades, realizedPnl, totalR, wins, losses, draws } = completedPositionsStatsTotals;
  const avgR = trades > 0 ? totalR / trades : 0;
  const winRate = trades > 0 ? wins / trades : 0;
  return {
    trades,
    realized_pnl: realizedPnl,
    total_r: totalR,
    avg_r: avgR,
    win_rate: winRate,
    wins,
    losses,
    draws,
  };
}

function setTradeSummaryOverride(summary) {
  tradeSummaryOverride = summary && typeof summary === 'object' ? summary : null;
}

function getTradeSummaryOverride() {
  return tradeSummaryOverride;
}

function refreshTradeSummaryFromCompletedPositions() {
  const override = buildCompletedPositionsSummaryFromTotals();
  if (!override) {
    return;
  }
  setTradeSummaryOverride(override);
  renderTradeSummary(lastTradeStats, override);
}

function renderCompletedPositionsHistory() {
  if (!completedPositionsList || !completedPositionsEmpty) {
    return;
  }
  const hasEntries = completedPositionsHistory.length > 0;
  if (!hasEntries) {
    completedPositionsList.replaceChildren();
    completedPositionsEmpty.removeAttribute('hidden');
    if (completedPositionsPanel) {
      completedPositionsPanel.setAttribute('data-empty', 'true');
    }
    return;
  }
  completedPositionsEmpty.setAttribute('hidden', '');
  if (completedPositionsPanel) {
    completedPositionsPanel.removeAttribute('data-empty');
  }
  const fragment = document.createDocumentFragment();
  completedPositionsHistory.forEach((entry) => {
    const card = buildCompletedPositionCard(entry);
    if (card) {
      fragment.append(card);
    }
  });
  completedPositionsList.replaceChildren(fragment);
}

function isPlainObject(value) {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function deepEqual(a, b) {
  if (a === b) return true;
  if (Array.isArray(a) && Array.isArray(b)) {
    if (a.length !== b.length) return false;
    for (let index = 0; index < a.length; index += 1) {
      if (!deepEqual(a[index], b[index])) {
        return false;
      }
    }
    return true;
  }
  if (isPlainObject(a) && isPlainObject(b)) {
    const keysA = Object.keys(a);
    const keysB = Object.keys(b);
    if (keysA.length !== keysB.length) return false;
    for (let index = 0; index < keysA.length; index += 1) {
      const key = keysA[index];
      if (!Object.prototype.hasOwnProperty.call(b, key)) {
        return false;
      }
      if (!deepEqual(a[key], b[key])) {
        return false;
      }
    }
    return true;
  }
  return Object.is(a, b);
}

function cloneCompletedPositionValue(value) {
  if (Array.isArray(value)) {
    return value.map((item) => cloneCompletedPositionValue(item));
  }
  if (isPlainObject(value)) {
    const clone = {};
    Object.entries(value).forEach(([key, entryValue]) => {
      const cloned = cloneCompletedPositionValue(entryValue);
      if (cloned !== undefined) {
        clone[key] = cloned;
      }
    });
    return clone;
  }
  return value;
}

function mergeCompletedPositionPayload(target, source) {
  let base = isPlainObject(target) ? target : {};
  let changed = !isPlainObject(target);
  if (!source || typeof source !== 'object') {
    return { payload: base, changed };
  }
  Object.entries(source).forEach(([key, value]) => {
    if (value === undefined || value === null) {
      return;
    }
    if (Array.isArray(value)) {
      if (!value.length) {
        return;
      }
      const normalizedArray = cloneCompletedPositionValue(value);
      const existingArray = Array.isArray(base[key]) ? base[key] : null;
      if (!existingArray || !deepEqual(existingArray, normalizedArray)) {
        base[key] = normalizedArray;
        changed = true;
      }
      return;
    }
    if (isPlainObject(value)) {
      const existingValue = isPlainObject(base[key]) ? base[key] : {};
      if (!isPlainObject(base[key])) {
        base[key] = existingValue;
      }
      const nested = mergeCompletedPositionPayload(existingValue, value);
      if (nested.changed) {
        changed = true;
      }
      return;
    }
    if (typeof value === 'string') {
      const trimmed = value.trim();
      if (!trimmed) {
        return;
      }
      if (base[key] !== trimmed) {
        base[key] = trimmed;
        changed = true;
      }
      return;
    }
    if (!Object.is(base[key], value)) {
      base[key] = value;
      changed = true;
    }
  });
  return { payload: base, changed };
}

function getCompletedPositionKey(position) {
  if (!position || typeof position !== 'object') {
    return '';
  }
  for (let index = 0; index < COMPLETED_POSITION_IDENTIFIER_KEYS.length; index += 1) {
    const key = COMPLETED_POSITION_IDENTIFIER_KEYS[index];
    if (!(key in position)) {
      continue;
    }
    const raw = unwrapPositionValue(position[key]);
    if (raw === undefined || raw === null) {
      continue;
    }
    const text = raw.toString().trim();
    if (text) {
      return `${key}:${text}`;
    }
  }
  const symbol = getPositionSymbol(position) || '';
  const closedTs = getPositionClosedTimestamp(position);
  const openedTs = getPositionTimestamp(position);
  const tsCandidate = Number.isFinite(closedTs) && closedTs > 0 ? closedTs : openedTs;
  if (symbol && Number.isFinite(tsCandidate) && tsCandidate >= 0) {
    return `${symbol}:${tsCandidate.toFixed(3)}`;
  }
  if (Number.isFinite(tsCandidate) && tsCandidate >= 0) {
    return tsCandidate.toFixed(3);
  }
  if (symbol) {
    return symbol;
  }
  return '';
}

function registerCompletedPosition(position, options = {}) {
  if (!position || typeof position !== 'object') {
    return false;
  }
  const key = getCompletedPositionKey(position);
  if (!key) {
    return false;
  }
  const timestampHint = Number(options.timestamp);
  const closedTs = getPositionClosedTimestamp(position);
  const openedTs = getPositionTimestamp(position);
  const resolvedTimestamp = Number.isFinite(timestampHint) && timestampHint >= 0
    ? timestampHint
    : Number.isFinite(closedTs) && closedTs >= 0
      ? closedTs
      : Number.isFinite(openedTs) && openedTs >= 0
        ? openedTs
        : Date.now() / 1000;
  const existing = completedPositionsIndex.get(key);
  if (existing) {
    const { changed } = mergeCompletedPositionPayload(existing.position, position);
    const timestampChanged = !Object.is(existing.ts, resolvedTimestamp);
    if (timestampChanged) {
      existing.ts = resolvedTimestamp;
    }
    return changed || timestampChanged;
  }
  const { payload } = mergeCompletedPositionPayload({}, position);
  const entry = {
    key,
    position: payload,
    ts: resolvedTimestamp,
  };
  completedPositionsIndex.set(key, entry);
  if (options.countTowardsStats !== false) {
    incrementCompletedPositionsStats(position);
  }
  return true;
}

function rebuildCompletedPositionsHistory() {
  const entries = Array.from(completedPositionsIndex.values());
  if (!entries.length) {
    completedPositionsHistory = [];
    return;
  }
  entries.sort((a, b) => b.ts - a.ts);
  if (entries.length > COMPLETED_POSITIONS_HISTORY_LIMIT) {
    const trimmed = entries.slice(0, COMPLETED_POSITIONS_HISTORY_LIMIT);
    const keepKeys = new Set(trimmed.map((entry) => entry.key));
    completedPositionsIndex.forEach((entry, key) => {
      if (!keepKeys.has(key)) {
        completedPositionsIndex.delete(key);
      }
    });
    completedPositionsHistory = trimmed;
    return;
  }
  completedPositionsHistory = entries;
}

function rememberCompletedPositions(positions = [], options = {}) {
  const entries = Array.isArray(positions) ? positions : [];
  if (!entries.length) {
    return;
  }
  const {
    countTowardsStats = true,
    skipSummaryRefresh = false,
    timestampResolver = null,
  } = options || {};
  let mutated = false;
  entries.forEach((position) => {
    if (!position || typeof position !== 'object') {
      return;
    }
    const timestampHint =
      typeof timestampResolver === 'function' ? timestampResolver(position) : undefined;
    const changed = registerCompletedPosition(position, {
      countTowardsStats,
      timestamp: timestampHint,
    });
    if (changed) {
      mutated = true;
    }
  });
  if (!mutated) {
    return;
  }
  rebuildCompletedPositionsHistory();
  renderCompletedPositionsHistory();
  if (!skipSummaryRefresh) {
    refreshTradeSummaryFromCompletedPositions();
  }
}

function syncCompletedPositionsFromTrades(history = []) {
  completedPositionsIndex.clear();
  if (!Array.isArray(history) || history.length === 0) {
    completedPositionsHistory = [];
    completedPositionsStatsTotals = { ...COMPLETED_POSITIONS_STATS_DEFAULTS };
    renderCompletedPositionsHistory();
    refreshTradeSummaryFromCompletedPositions();
    return;
  }
  const { entries, stats } = buildCompletedPositionsFromHistoryEntries(history);
  completedPositionsStatsTotals = stats;
  if (!entries.length) {
    completedPositionsHistory = [];
    renderCompletedPositionsHistory();
    refreshTradeSummaryFromCompletedPositions();
    return;
  }
  const limit = Math.max(COMPLETED_POSITIONS_HISTORY_LIMIT * 3, COMPLETED_POSITIONS_HISTORY_LIMIT);
  const subset = entries.slice(0, limit);
  subset.forEach((entry) => {
    completedPositionsIndex.set(entry.key, entry);
  });
  completedPositionsHistory = subset;
  renderCompletedPositionsHistory();
  refreshTradeSummaryFromCompletedPositions();
}

function syncExchangeCompletedPositions(entries = []) {
  if (!Array.isArray(entries) || entries.length === 0) {
    return;
  }
  rememberCompletedPositions(entries, {
    countTowardsStats: false,
    skipSummaryRefresh: true,
    timestampResolver: (entry) => getPositionClosedTimestamp(entry),
  });
}

function refreshPositionUpdatesFromHistory() {
  refreshRenderedPositionNotifications();
  if (activePositionsNotifications && activePositionsNotifications.children.length > 0) {
    setPositionNotificationsEmptyState(false);
    return;
  }
  const historical = buildHistoricalNotifications(5);
  if (!historical.length) {
    setPositionNotificationsEmptyState(true);
    return;
  }
  renderPositionNotifications(historical);
}

function ensurePositionUpdatesRefreshTimer() {
  if (positionUpdatesRefreshTimer) return;
  positionUpdatesRefreshTimer = setInterval(() => {
    refreshPositionUpdatesFromHistory();
  }, POSITION_NOTIFICATIONS_REFRESH_INTERVAL_MS);
}

function buildPositionManagementSummary(position, options = {}) {
  const latest = resolveLatestManagementEvent(position);
  if (!latest) return null;

  const container = document.createElement('div');
  container.className = 'active-position-management';
  container.setAttribute('role', 'listitem');
  container.dataset.action = latest.action || '';
  const normalizedSymbol = getNormalizedActivePositionSymbol(position);
  if (normalizedSymbol) {
    container.dataset.symbol = normalizedSymbol;
  }
  const timestampNumeric = Number.isFinite(latest.ts) ? Number(latest.ts) : null;
  if (timestampNumeric !== null) {
    container.dataset.timestamp = timestampNumeric.toString();
  }

  const { includeSymbol = false, symbolText = null } = options || {};
  if (includeSymbol) {
    const symbolLabel = document.createElement('span');
    symbolLabel.className = 'active-position-management-symbol';
    symbolLabel.textContent = symbolText || getPositionSymbol(position);
    container.append(symbolLabel);

    const arrow = document.createElement('span');
    arrow.className = 'active-position-management-arrow';
    arrow.textContent = '→';
    container.append(arrow);
  }

  const label = document.createElement('span');
  label.className = 'active-position-management-label';
  label.textContent = formatManagementEventLabel(latest.action);
  container.append(label);

  const relative = formatManagementRelativeTime(latest.ts);
  if (relative) {
    const time = document.createElement('span');
    time.className = 'active-position-management-time';
    time.textContent = relative;
    container.append(time);
  }

  const detailParts = [];
  const { data } = latest;
  if (data && typeof data === 'object') {
    const pctGain = toNumeric(data.pct_gain);
    if (Number.isFinite(pctGain)) {
      const pctText = `${(pctGain * 100).toFixed(1)}%`;
      detailParts.push(`Δ ${pctText}`);
    }
    const rNow = toNumeric(data.r);
    if (Number.isFinite(rNow)) {
      detailParts.push(`R ${rNow.toFixed(2)}`);
    }
    const stopPrice = toNumeric(data.stop);
    if (Number.isFinite(stopPrice) && stopPrice > 0) {
      detailParts.push(`Stop ${formatPriceDisplay(stopPrice, { maximumFractionDigits: 6 })}`);
    }
    const exitPrice = toNumeric(data.exit || data.price || data.target);
    if (Number.isFinite(exitPrice) && exitPrice > 0) {
      detailParts.push(`Exit ${formatPriceDisplay(exitPrice, { maximumFractionDigits: 6 })}`);
    }
  }
  if (detailParts.length) {
    container.title = detailParts.join(' · ');
  }

  return container;
}

function buildClosedPositionNotification(position, options = {}) {
  const container = document.createElement('div');
  container.className = 'active-position-management';
  container.setAttribute('role', 'listitem');
  container.dataset.action = 'closed';
  const normalizedSymbol = getNormalizedActivePositionSymbol(position);
  if (normalizedSymbol) {
    container.dataset.symbol = normalizedSymbol;
  }
  const closedTs = getPositionTimestamp(position);
  const closedTimestamp = Number.isFinite(closedTs) && closedTs > 0 ? closedTs : Date.now() / 1000;
  container.dataset.timestamp = closedTimestamp.toString();

  const { includeSymbol = true, symbolText = null } = options || {};

  if (includeSymbol) {
    const symbolLabel = document.createElement('span');
    symbolLabel.className = 'active-position-management-symbol';
    symbolLabel.textContent = symbolText || getPositionSymbol(position);
    container.append(symbolLabel);

    const arrow = document.createElement('span');
    arrow.className = 'active-position-management-arrow';
    arrow.textContent = '→';
    container.append(arrow);
  }

  const label = document.createElement('span');
  label.className = 'active-position-management-label';
  label.textContent = translate('active.notifications.closed', 'Position closed');
  container.append(label);

  const time = document.createElement('span');
  time.className = 'active-position-management-time';
  time.textContent = formatManagementRelativeTime(Date.now() / 1000);
  container.append(time);

  let reasonLabel = '';
  const reasonCode = extractPositionManagementExitReason(position);
  if (reasonCode) {
    const friendlyLabel = friendlyReason(reasonCode);
    if (friendlyLabel) {
      reasonLabel = friendlyLabel;
      const reasonBadge = document.createElement('span');
      reasonBadge.className = 'active-position-management-reason';
      reasonBadge.textContent = friendlyLabel;
      container.append(reasonBadge);
    }
  }

  const detailParts = [];
  if (reasonLabel) {
    detailParts.push(reasonLabel);
  }
  const pnlField = pickNumericField(position, ACTIVE_POSITION_ALIASES.pnl || []);
  if (Number.isFinite(pnlField.numeric)) {
    detailParts.push(`${formatSignedNumber(pnlField.numeric, 2)} USDT`);
  }
  const roeField = pickNumericField(position, ACTIVE_POSITION_ALIASES.roe || []);
  const pctField = formatPercentField(roeField, 2);
  if (pctField && pctField.text) {
    detailParts.push(pctField.text);
  }
  if (detailParts.length) {
    container.title = detailParts.join(' · ');
  }

  return container;
}

function extractPositionManagementExitReason(position) {
  if (!position || typeof position !== 'object') {
    return '';
  }
  for (let index = 0; index < MANAGEMENT_EXIT_REASON_KEYS.length; index += 1) {
    const key = MANAGEMENT_EXIT_REASON_KEYS[index];
    if (position[key]) {
      return position[key];
    }
  }
  const management = position.management;
  if (management && typeof management === 'object') {
    for (let index = 0; index < MANAGEMENT_BLOCK_EXIT_REASON_KEYS.length; index += 1) {
      const key = MANAGEMENT_BLOCK_EXIT_REASON_KEYS[index];
      if (management[key]) {
        return management[key];
      }
    }
    for (let index = 0; index < MANAGEMENT_EXIT_HINT_KEYS.length; index += 1) {
      const hintKey = MANAGEMENT_EXIT_HINT_KEYS[index];
      if (!Object.prototype.hasOwnProperty.call(management, hintKey)) {
        continue;
      }
      const value = management[hintKey];
      if (typeof value === 'string') {
        const trimmed = value.trim();
        if (trimmed) {
          return trimmed;
        }
      }
      if (value) {
        return hintKey;
      }
    }
  }
  const eventReason = extractLatestManagementEventAction(position);
  if (eventReason) {
    return eventReason;
  }
  return '';
}

function extractLatestManagementEventAction(position) {
  if (!position || typeof position !== 'object') {
    return '';
  }
  const pools = [];
  const management = position.management;
  if (management && Array.isArray(management.events)) {
    pools.push(...management.events);
  }
  if (Array.isArray(position.management_events)) {
    pools.push(...position.management_events);
  }
  if (!pools.length) {
    return '';
  }
  for (let index = pools.length - 1; index >= 0; index -= 1) {
    const entry = pools[index];
    if (!entry || typeof entry !== 'object') {
      continue;
    }
    const raw = entry.action || entry.event || entry.reason || entry.type || entry.name;
    if (!raw) {
      continue;
    }
    const label = raw.toString().trim();
    if (label) {
      return label;
    }
  }
  return '';
}

function buildPositionProgressBar({ takeEntry, stopEntry, markPrice, side, pnlTone }) {
  const container = document.createElement('div');
  container.className = 'position-progress-container';

  const track = document.createElement('div');
  track.className = 'position-progress-track';
  container.append(track);

  const indicator = document.createElement('div');
  indicator.className = 'position-progress-indicator';
  track.append(indicator);

  const progressValue = computePositionProgressValue(takeEntry, stopEntry, markPrice, side);
  let indicatorValue = progressValue;

  if (indicatorValue === null && Number.isFinite(pnlTone)) {
    if (pnlTone > 0) {
      indicatorValue = 1;
    } else if (pnlTone < 0) {
      indicatorValue = 0;
    } else {
      indicatorValue = 0.5;
    }
  }

  if (indicatorValue === null) {
    container.classList.add('is-inactive');
  } else {
    indicator.style.left = `${(indicatorValue * 100).toFixed(2)}%`;
    const indicatorColors = computeProgressIndicatorColor(indicatorValue);
    if (indicatorColors) {
      indicator.style.background = indicatorColors.solid;
      indicator.style.borderColor = indicatorColors.solid;
      indicator.style.boxShadow = `0 0 0 1px rgba(15, 23, 42, 0.35), 0 0 0 4px ${indicatorColors.halo}, 0 0 8px 0 ${indicatorColors.glow}`;
    }
  }

  return container;
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

function getPositionClosedTimestamp(position) {
  if (!position || typeof position !== 'object') return Number.NEGATIVE_INFINITY;
  for (const key of POSITION_CLOSED_TIMESTAMP_KEYS) {
    if (!(key in position)) continue;
    const raw = unwrapPositionValue(position[key]);
    if (raw === undefined || raw === null || raw === '') {
      continue;
    }
    const numeric = toNumeric(raw);
    if (Number.isFinite(numeric) && numeric > 0) {
      if (numeric > 1e12 || numeric > 1e10) {
        return numeric / 1000;
      }
      return numeric;
    }
    if (typeof raw === 'string') {
      const parsed = Date.parse(raw);
      if (Number.isFinite(parsed)) {
        return parsed / 1000;
      }
    }
  }
  return Number.NEGATIVE_INFINITY;
}

function computePositionDurationSeconds(position) {
  const openedTs = getPositionTimestamp(position);
  const closedTs = getPositionClosedTimestamp(position);
  if (Number.isFinite(openedTs) && Number.isFinite(closedTs)) {
    return Math.max(0, Math.round(closedTs - openedTs));
  }
  return null;
}

function updateActivePositionsView(options = {}) {
  if (!activePositionsRows) return;
  const { closedPositions = [] } = options || {};
  const positions = Array.isArray(activePositions) ? activePositions : [];
  const sorted = positions.slice().sort((a, b) => getPositionTimestamp(b) - getPositionTimestamp(a));
  const rowsFragment = document.createDocumentFragment();

  const hasRows = sorted.length > 0;

  const totalPnlInfo = computeActivePositionsTotalPnl(sorted);

  if (activePositionsModeLabel) {
    activePositionsModeLabel.classList.remove('tone-profit', 'tone-loss');
    activePositionsModeLabel.textContent = totalPnlInfo.text;
    if (totalPnlInfo.tone === 'profit') {
      activePositionsModeLabel.classList.add('tone-profit');
    } else if (totalPnlInfo.tone === 'loss') {
      activePositionsModeLabel.classList.add('tone-loss');
    }
  }
  if (activePositionsWrapper) {
    activePositionsWrapper.removeAttribute('hidden');
  }
  if (activePositionsCard) {
    if (hasRows) {
      activePositionsCard.removeAttribute('data-empty');
    } else {
      activePositionsCard.setAttribute('data-empty', 'true');
    }
  }

  const managementNotifications = [];

  sorted.forEach((position) => {
    const row = document.createElement('tr');

    const sizeField = pickNumericField(position, ACTIVE_POSITION_ALIASES.size || []);
    const signedQuantityField = pickNumericField(position, ACTIVE_POSITION_SIGNED_SIZE_KEYS || []);
    const notionalField = pickNumericField(position, ACTIVE_POSITION_NOTIONAL_KEYS || []);
    const entryField = pickNumericField(position, ACTIVE_POSITION_ALIASES.entry || []);
    const markField = pickNumericField(position, ACTIVE_POSITION_ALIASES.mark || []);
    const takeEntry = extractTpSlEntry(position, 'take');
    const stopEntry = extractTpSlEntry(position, 'stop');
    const pnlField = pickNumericField(position, ACTIVE_POSITION_ALIASES.pnl || []);
    const roePercentSource = pickNumericField(position, ACTIVE_POSITION_ALIASES.roe || []);
    const pnlToneNumeric = Number.isFinite(pnlField.numeric)
      ? pnlField.numeric
      : Number.isFinite(roePercentSource.numeric)
          ? roePercentSource.numeric
          : null;

    const symbolCell = document.createElement('td');
    symbolCell.className = 'active-positions-symbol-cell';
    const symbolWrapper = document.createElement('div');
    symbolWrapper.className = 'active-positions-symbol-wrapper';
    const symbolLabel = document.createElement('span');
    symbolLabel.className = 'active-positions-symbol';
    const symbolValue = getPositionSymbol(position);
    symbolLabel.textContent = symbolValue;
    symbolWrapper.append(symbolLabel);
    const sideValue = extractPositionSide(position, sizeField, signedQuantityField);
    const sideBadge = buildSideBadge(sideValue);
    if (sideBadge) {
      symbolWrapper.append(sideBadge);
    }
    const markNumeric = derivePositionMarkPrice({
      mark: markField.numeric,
      entry: entryField.numeric,
      quantity: signedQuantityField.numeric,
      notional: notionalField.numeric,
      pnl: pnlField.numeric,
      side: sideValue,
    });
    symbolCell.append(symbolWrapper);
    symbolCell.append(
      buildPositionProgressBar({
        takeEntry,
        stopEntry,
        markPrice: markNumeric,
        side: sideValue,
        pnlTone: pnlToneNumeric,
      }),
    );
    const managementSummary = buildPositionManagementSummary(position, {
      includeSymbol: true,
      symbolText: symbolValue,
    });
    if (managementSummary) {
      managementNotifications.push(managementSummary);
    }
    applyActivePositionLabel(symbolCell, 'symbol');
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
    const notionalNumeric = Number.isFinite(notionalField.numeric) ? Math.abs(notionalField.numeric) : null;
    const quantityNumeric = Number.isFinite(signedQuantityField.numeric)
      ? Math.abs(signedQuantityField.numeric)
      : null;
    const sizeNumeric = Number.isFinite(notionalNumeric)
      ? notionalNumeric
      : Number.isFinite(sizeField.numeric)
      ? Math.abs(sizeField.numeric)
      : quantityNumeric;
    sizeCell.textContent = formatPositionSize(sizeNumeric);
    applyActivePositionLabel(sizeCell, 'size');
    row.append(sizeCell);

    const entryCell = document.createElement('td');
    entryCell.className = 'numeric';
    entryCell.textContent = formatPriceDisplay(entryField.numeric, {
      minimumFractionDigits: 6,
      maximumFractionDigits: 6,
    });
    applyActivePositionLabel(entryCell, 'entry');
    row.append(entryCell);

    const markCell = document.createElement('td');
    markCell.className = 'numeric';
    markCell.textContent = formatPriceDisplay(markNumeric, {
      minimumFractionDigits: 6,
      maximumFractionDigits: 6,
    });
    applyActivePositionLabel(markCell, 'mark');
    row.append(markCell);

    const leverageCell = document.createElement('td');
    leverageCell.className = 'numeric';
    const leverageField = pickNumericField(position, ACTIVE_POSITION_ALIASES.leverage || []);
    const leverageNumeric = Number.isFinite(leverageField.numeric) ? Math.abs(leverageField.numeric) : null;
    leverageCell.textContent = formatLeverage(leverageField.numeric);
    applyActivePositionLabel(leverageCell, 'leverage');
    row.append(leverageCell);

    const marginCell = document.createElement('td');
    marginCell.className = 'numeric';
    const marginField = pickNumericField(position, ACTIVE_POSITION_ALIASES.margin || []);
    let marginNumeric = Number.isFinite(marginField.numeric) ? Math.abs(marginField.numeric) : null;
    if (!Number.isFinite(marginNumeric) || marginNumeric <= 0) {
      if (Number.isFinite(notionalNumeric) && Number.isFinite(leverageNumeric) && leverageNumeric > 0) {
        marginNumeric = notionalNumeric / leverageNumeric;
      }
      if (!Number.isFinite(marginNumeric) || marginNumeric <= 0) {
        const priceForNotional = Number.isFinite(markNumeric)
          ? Math.abs(markNumeric)
          : Number.isFinite(entryField.numeric)
              ? Math.abs(entryField.numeric)
              : null;
        if (
          Number.isFinite(quantityNumeric) &&
          Number.isFinite(priceForNotional) &&
          Number.isFinite(leverageNumeric) &&
          leverageNumeric > 0
        ) {
          const candidate = (quantityNumeric * priceForNotional) / leverageNumeric;
          if (Number.isFinite(candidate) && candidate > 0) {
            marginNumeric = candidate;
          }
        }
      }
    }
    if (Number.isFinite(marginNumeric) && marginNumeric > 0) {
      marginCell.textContent = formatPositionSize(marginNumeric);
    } else {
      marginCell.textContent = '–';
    }
    applyActivePositionLabel(marginCell, 'margin');
    row.append(marginCell);

    const pnlCell = document.createElement('td');
    pnlCell.className = 'numeric';
    const pnlPercentField = formatPercentField(roePercentSource, 2);
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
    applyActivePositionLabel(pnlCell, 'pnl');
    row.append(pnlCell);

    rowsFragment.append(row);
  });

  closedPositions.forEach((position) => {
    const symbolValue = getPositionSymbol(position);
    const closedNotification = buildClosedPositionNotification(position, {
      includeSymbol: true,
      symbolText: symbolValue,
    });
    if (closedNotification) {
      managementNotifications.push(closedNotification);
    }
  });

  closedPositions.forEach((position) => clearCachedManagementEvent(position));
  rememberCompletedPositions(closedPositions);
  if (closedPositions.length > 0) {
    scheduleTradesRefresh(500);
  }

  const notifications = managementNotifications.slice();
  const sortedNotifications = notifications
    .map((element) => {
      const raw = element?.dataset?.timestamp;
      const parsed = raw ? Number(raw) : Number.NaN;
      return {
        element,
        ts: Number.isFinite(parsed) ? parsed : 0,
      };
    })
    .sort((a, b) => b.ts - a.ts)
    .map((entry) => entry.element);

  const limitedNotifications = sortedNotifications.slice(0, 5);
  rememberPositionNotifications(limitedNotifications);
  let notificationsToRender = limitedNotifications.filter((element) => element instanceof HTMLElement);
  if (!notificationsToRender.length) {
    notificationsToRender = buildHistoricalNotifications(5);
  }

  renderPositionNotifications(notificationsToRender);
  ensurePositionUpdatesRefreshTimer();

  activePositionsRows.replaceChildren(rowsFragment);
}

function applyActivePositionsPayload(openPayload, options = {}) {
  const normalizedPayload =
    openPayload === undefined || openPayload === null ? [] : openPayload;
  const { syncSnapshot = true } = options || {};
  if (syncSnapshot) {
    if (latestTradesSnapshot && typeof latestTradesSnapshot === 'object') {
      latestTradesSnapshot.open = normalizedPayload;
    } else if (normalizedPayload !== undefined) {
      latestTradesSnapshot = { open: normalizedPayload };
    }
  }
  renderActivePositions(normalizedPayload);
}

function renderActivePositions(openPositions) {
  const previousPositions = Array.isArray(activePositions) ? activePositions.slice() : [];
  const nextPositions = normaliseActivePositions(openPositions);

  const nextSymbols = new Set();
  nextPositions.forEach((position) => {
    const symbol = getNormalizedActivePositionSymbol(position);
    if (symbol) {
      nextSymbols.add(symbol);
    }
  });

  const closedPositions = [];
  const seenSymbols = new Set();
  previousPositions.forEach((position) => {
    const symbol = getNormalizedActivePositionSymbol(position);
    if (!symbol || seenSymbols.has(symbol)) {
      return;
    }
    if (!nextSymbols.has(symbol)) {
      closedPositions.push(position);
      seenSymbols.add(symbol);
    }
  });

  activePositions = nextPositions;
  activePositionSymbols = nextSymbols;
  prunePositionNotificationHistory();
  updateActivePositionsView({ closedPositions });
  refreshTradeProposalPlacementAvailability();
}

function refreshTradeProposalPlacementAvailability() {
  if (!aiChatMessages) return;
  tradeProposalRegistry.forEach((proposal, key) => {
    if (!proposal || !key) return;
    const card = aiChatMessages.querySelector(`.ai-trade-proposal[data-proposal-id="${key}"]`);
    if (!card) return;
    applyTradeProposalStatus(card, proposal, { skipRegistry: true });
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

function extractDecisionNotes(record) {
  if (!record || typeof record !== 'object') {
    return { reasonCode: '', reasonLabel: '', notes: [] };
  }
  const reasonCode = record.decision_reason ? String(record.decision_reason).trim() : '';
  const reasonLabel = reasonCode ? friendlyReason(reasonCode) : '';
  const noteCandidates = [];
  ['decision_note', 'risk_note', 'explanation'].forEach((key) => {
    const raw = record[key];
    if (typeof raw === 'string') {
      const cleaned = raw.trim();
      if (cleaned) {
        noteCandidates.push(cleaned);
      }
    }
  });
  if (Array.isArray(record.notes)) {
    record.notes.forEach((entry) => {
      if (typeof entry === 'string') {
        const cleaned = entry.trim();
        if (cleaned) {
          noteCandidates.push(cleaned);
        }
      }
    });
  }
  const uniqueNotes = [];
  noteCandidates.forEach((note) => {
    if (!uniqueNotes.includes(note)) {
      uniqueNotes.push(note);
    }
  });
  return { reasonCode, reasonLabel, notes: uniqueNotes };
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

function normaliseDetailKey(key) {
  return (key || '')
    .toString()
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '');
}

function parseExtraFieldPairs(raw) {
  if (!raw) return [];
  const normalized = raw.replace(/[{}]/g, '').trim();
  if (!normalized) return [];
  const entries = [];
  const quotedPattern = /'([^']+)'\s*:\s*'([^']+)'/g;
  let quotedMatch = quotedPattern.exec(normalized);
  while (quotedMatch) {
    entries.push({ key: quotedMatch[1], value: quotedMatch[2] });
    quotedMatch = quotedPattern.exec(normalized);
  }
  if (!entries.length) {
    const simplePattern = /([A-Za-z0-9_]+)\s*[=:]\s*([\d.+-]+)/g;
    let simpleMatch = simplePattern.exec(normalized);
    while (simpleMatch) {
      entries.push({ key: simpleMatch[1], value: simpleMatch[2] });
      simpleMatch = simplePattern.exec(normalized);
    }
  }
  return entries.map(({ key, value }) => {
    const textValue = value !== undefined && value !== null ? value.toString() : '';
    const numericCandidate = Number(textValue);
    return {
      key,
      label: toTitleWords(key),
      value: textValue,
      numericValue: Number.isFinite(numericCandidate) ? numericCandidate : null,
      normalizedKey: normaliseDetailKey(key),
    };
  });
}

function formatDetailEntries(entries) {
  if (!Array.isArray(entries) || !entries.length) {
    return '';
  }
  return entries.map((entry) => `${entry.label} ${entry.value}`).join(' • ');
}

function formatExtraDetails(raw) {
  return formatDetailEntries(parseExtraFieldPairs(raw));
}

function resolveLogCategory(friendly) {
  if (!friendly || typeof friendly !== 'object') return '';
  const reasonKey = friendly.reason ? friendly.reason.toString().toLowerCase() : '';
  if (reasonKey && LOG_REASON_CATEGORY_MAP[reasonKey]) {
    return LOG_REASON_CATEGORY_MAP[reasonKey];
  }
  const labelKey = friendly.label ? friendly.label.toString().toLowerCase() : '';
  if (labelKey && LOG_LABEL_CATEGORY_MAP[labelKey]) {
    return LOG_LABEL_CATEGORY_MAP[labelKey];
  }
  return '';
}

function normaliseLogReasonKey(reason) {
  return (reason || '')
    .toString()
    .trim()
    .toLowerCase();
}

function getLogReasonClass(reason) {
  const key = normaliseLogReasonKey(reason);
  if (!key) return '';
  const token = key.replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
  return token ? `reason-${token}` : '';
}

function getLogClassList(friendly) {
  const classes = [];
  const category = resolveLogCategory(friendly);
  if (category) {
    classes.push(`category-${category}`);
  }
  const reasonClass = getLogReasonClass(friendly?.reason);
  if (reasonClass) {
    classes.push(reasonClass);
  }
  return classes;
}

function hexToRgba(hex, alpha = 1) {
  if (!hex) return '';
  const raw = hex.toString().trim().replace(/^#/, '');
  if (!raw) return '';
  const normalized = raw.length === 3 ? raw.split('').map((char) => char + char).join('') : raw;
  if (normalized.length !== 6) return '';
  const r = parseInt(normalized.slice(0, 2), 16);
  const g = parseInt(normalized.slice(2, 4), 16);
  const b = parseInt(normalized.slice(4, 6), 16);
  if ([r, g, b].some((component) => Number.isNaN(component))) return '';
  const clampedAlpha = Math.max(0, Math.min(1, Number(alpha)));
  return `rgba(${r}, ${g}, ${b}, ${clampedAlpha})`;
}

function applyLogReasonStyles(element, reason) {
  if (!element) return;
  const key = normaliseLogReasonKey(reason);
  if (!key) return;
  const palette = LOG_REASON_COLOR_MAP[key];
  if (!palette) return;
  const base = palette.base || null;
  const accent = palette.accent || base;
  const backgroundStart =
    palette.backgroundStart ||
    (base ? hexToRgba(base, palette.backgroundStartAlpha ?? palette.backgroundAlpha ?? 0.24) : '');
  const backgroundEnd =
    palette.backgroundEnd ||
    (accent ? hexToRgba(accent, palette.backgroundEndAlpha ?? 0.12) : '');
  const background = palette.background || backgroundStart;
  const border = palette.border || (base ? hexToRgba(base, palette.borderAlpha ?? 0.36) : '');
  const badgeStart =
    palette.badgeStart || (accent ? hexToRgba(accent, palette.badgeAlpha ?? 0.36) : '');
  const badgeEnd =
    palette.badgeEnd ||
    (base ? hexToRgba(base, palette.badgeEndAlpha ?? palette.badgeAlpha ?? 0.22) : badgeStart);
  const badge = palette.badge || badgeStart;
  const badgeText = palette.badgeText || palette.text || '';

  if (backgroundStart) {
    element.style.setProperty('--log-reason-bg-start', backgroundStart);
  }
  if (backgroundEnd) {
    element.style.setProperty('--log-reason-bg-end', backgroundEnd);
  }
  if (background) {
    element.style.setProperty('--log-reason-bg', background);
  }
  if (border) {
    element.style.setProperty('--log-reason-border', border);
  }
  if (badgeStart) {
    element.style.setProperty('--log-reason-badge-start', badgeStart);
  }
  if (badgeEnd) {
    element.style.setProperty('--log-reason-badge-end', badgeEnd);
  }
  if (badge) {
    element.style.setProperty('--log-reason-badge-bg', badge);
  }
  if (badgeText) {
    element.style.setProperty('--log-reason-badge-text', badgeText);
  }

  element.classList.add('log-reason-themed');
}

function humanizeLogLine(line, fallbackLevel = 'info') {
  const parsed = parseStructuredLog(line, fallbackLevel);
  const baseLevel = (parsed.level || fallbackLevel || 'info').toLowerCase();
  let severity = baseLevel;
  let label = FRIENDLY_LEVEL_LABELS[severity] || severity.toUpperCase();
  let relevant = severity !== 'debug';
  let text = parsed.message || parsed.raw;

  const aiFeedMatch = parsed.message?.match(/^AI_FEED\s+(.*)$/);
  if (aiFeedMatch) {
    const detail = aiFeedMatch[1]?.trim();
    let feedKind = '';
    let headline = detail || '';
    if (detail) {
      const parts = detail.split('|').map((part) => part.trim()).filter(Boolean);
      if (parts.length >= 2) {
        [feedKind] = parts;
        headline = parts.slice(1).join(' | ');
      }
    }
    const normalizedKind = feedKind.toLowerCase();
    const symbolMatch = headline.match(/\b([A-Z]{3,}(?:USDT|USDC|USD|BTC|ETH))\b/);
    const symbol = symbolMatch ? symbolMatch[1] : undefined;
    if (normalizedKind === 'query') {
      text = headline ? `Sent to AI: ${headline}` : 'Sent to the strategy AI for review.';
      label = 'AI request';
      severity = 'info';
    } else {
      text = headline ? `AI activity: ${headline}` : 'AI activity updated.';
      label = 'AI feed';
      severity = 'system';
    }
    relevant = true;
    return { text, label, severity, relevant, parsed, symbol, refreshTrades: true };
  }

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

  const quoteVolumeBelowMatch = parsed.message?.match(
    /^Skip\s+(\S+)\s+[—–-]\s+quote volume\s+([\d.]+)\s+below minimum\s+([\d.]+)/i,
  );
  if (quoteVolumeBelowMatch) {
    const [, symbol, current, threshold] = quoteVolumeBelowMatch;
    const currentText = formatNumber(current, 2);
    const thresholdText = formatNumber(threshold, 2);
    const detail = `Quote volume ${currentText} • Min ${thresholdText}`;
    text = `Skipped ${symbol} — Quote volume ${currentText} below minimum ${thresholdText}.`;
    label = 'Skipped trade';
    severity = 'warning';
    relevant = true;
    return {
      text,
      label,
      severity,
      relevant,
      parsed,
      reason: 'quote_volume',
      symbol: symbol ? symbol.toString().toUpperCase() : undefined,
      detail,
    };
  }

  const quoteVolumeCooldownMatch = parsed.message?.match(
    /^Skip\s+(\S+)\s+[—–-]\s+quote volume cooldown active for\s+([\d.]+)\s+more cycles?\.?/i,
  );
  if (quoteVolumeCooldownMatch) {
    const [, symbol, remaining] = quoteVolumeCooldownMatch;
    const count = Number(remaining);
    const cycles = Number.isFinite(count) ? `${count} more ${count === 1 ? 'cycle' : 'cycles'}` : `${remaining} more cycles`;
    text = `Skipped ${symbol} — Quote volume cooldown active (${cycles}).`;
    label = 'Skipped trade';
    severity = 'warning';
    relevant = true;
    return {
      text,
      label,
      severity,
      relevant,
      parsed,
      reason: 'quote_volume_cooldown',
      symbol: symbol ? symbol.toString().toUpperCase() : undefined,
    };
  }

  const positionCapSymbolMatch = parsed.message?.match(
    /^Skip\s+(\S+)\s+[—–-]\s+per-symbol position cap reached\s*\((\d+)\)\.?/i,
  );
  if (positionCapSymbolMatch) {
    const [, symbol, cap] = positionCapSymbolMatch;
    const capNum = Number(cap);
    const capText = Number.isFinite(capNum) ? capNum.toString() : cap;
    text = `Skipped ${symbol} — Per-symbol position cap reached (${capText}).`;
    label = 'Skipped trade';
    severity = 'warning';
    relevant = true;
    return {
      text,
      label,
      severity,
      relevant,
      parsed,
      reason: 'position_cap_symbol',
      symbol: symbol ? symbol.toString().toUpperCase() : undefined,
      detail: `Cap ${capText}`,
    };
  }

  const positionCapGlobalMatch = parsed.message?.match(
    /^Skip\s+(\S+)\s+[—–-]\s+global position cap reached\s*\((\d+)\/(\d+)\)\.?/i,
  );
  if (positionCapGlobalMatch) {
    const [, symbol, current, limit] = positionCapGlobalMatch;
    text = `Skipped ${symbol} — Global position cap reached (${current}/${limit}).`;
    label = 'Skipped trade';
    severity = 'warning';
    relevant = true;
    return {
      text,
      label,
      severity,
      relevant,
      parsed,
      reason: 'position_cap_global',
      symbol: symbol ? symbol.toString().toUpperCase() : undefined,
      detail: `Open ${current} / Limit ${limit}`,
    };
  }

  const baseStrategySkipMatch = parsed.message?.match(
    /^Skip\s+(\S+)\s+[—–-]\s+base strategy reported\s+([^;]+);\s+avoiding AI trend scan\.?/i,
  );
  if (baseStrategySkipMatch) {
    const [, symbol, reasonText] = baseStrategySkipMatch;
    const cleaned = reasonText ? reasonText.trim() : '';
    text = `Skipped ${symbol} — Base strategy veto (${cleaned || 'no detail'}).`;
    label = 'Skipped trade';
    severity = 'debug';
    relevant = false;
    return {
      text,
      label,
      severity,
      relevant,
      parsed,
      symbol: symbol ? symbol.toString().toUpperCase() : undefined,
      detail: cleaned,
    };
  }

  const skipMatch = parsed.message?.match(/^SKIP (\S+): ([\w_]+)(.*)$/);
  if (skipMatch) {
    const [, symbol, reason, extraRaw] = skipMatch;
    const reasonKey = reason ? reason.toString().toLowerCase() : '';
    const detailPairs = parseExtraFieldPairs(extraRaw);
    const detail = formatDetailEntries(detailPairs);
    const reasonLabel = friendlyReason(reasonKey || reason);
    text = `Skipped ${symbol} — ${reasonLabel}${detail ? ` (${detail})` : ''}.`;
    label = 'Skipped trade';
    severity = 'warning';
    relevant = true;
    return {
      text,
      label,
      severity,
      relevant,
      parsed,
      reason: reasonKey || reason,
      symbol: symbol ? symbol.toString().toUpperCase() : undefined,
      detail,
      detailPairs,
    };
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
    return {
      text,
      label,
      severity,
      relevant,
      parsed,
      reason: 'policy_filter',
      symbol: symbol ? symbol.toString().toUpperCase() : undefined,
    };
  }

  const entryFailMatch = parsed.message?.match(/^entry fail (\S+):\s*(.*)$/i);
  if (entryFailMatch) {
    const [, symbol, detail] = entryFailMatch;
    text = `Order for ${symbol} failed${detail ? `: ${detail}` : '.'}`;
    label = 'Order issue';
    severity = 'error';
    relevant = true;
    return {
      text,
      label,
      severity,
      relevant,
      parsed,
      reason: 'order_failed',
      symbol: symbol ? symbol.toString().toUpperCase() : undefined,
    };
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
    if (!res.ok) throw new Error('Unable to refresh status');
    const data = await res.json();
    lastBotStatus = data;
    const running = data.running;
    statusIndicator.textContent = running
      ? translate('status.indicator.running', 'Running')
      : translate('status.indicator.stopped', 'Stopped');
    statusIndicator.className = `pill ${running ? 'running' : 'stopped'}`;
    statusPid.textContent = data.pid ?? '–';
    statusStarted.textContent = data.started_at
      ? new Date(data.started_at * 1000).toLocaleString()
      : '–';
    statusUptime.textContent = running ? formatDuration(data.uptime_s) : '–';
    btnStart.disabled = running;
    btnStop.disabled = !running;
    statusHydrated = true;
    markStale(statusCard, false);
  } catch (err) {
    console.warn('Failed to refresh bot status', err);
    if (!statusHydrated) {
      lastBotStatus = { ...DEFAULT_BOT_STATUS };
      statusIndicator.textContent = translate('status.indicator.offline', 'Offline');
      statusIndicator.className = 'pill stopped';
      statusPid.textContent = '–';
      statusStarted.textContent = '–';
      statusUptime.textContent = '–';
      return;
    }
    markStale(statusCard, true);
  }
}

function appendLogLine({ line, level, ts }) {
  const normalizedLevel = (level || 'info').toLowerCase();
  const parsed = parseStructuredLog(line, normalizedLevel);
  const derivedLevel = (parsed.level || normalizedLevel).toLowerCase();
  const el = document.createElement('div');
  el.className = `log-line ${derivedLevel}`.trim();
  const rawMessage = (parsed.message || parsed.raw || '').toString();
  if (/^\s*skip\b/i.test(rawMessage)) {
    el.classList.add('is-skip');
  }
  if (/\b(entry|exit|trade)\b/i.test(rawMessage)) {
    el.classList.add('is-trade');
  }
  if (/\bai(?:[_\s:-]|\b)/i.test(rawMessage)) {
    el.classList.add('is-ai');
  }

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

function connectActivePositionsStream() {
  if (activePositionsStreamReconnectTimer) {
    clearTimeout(activePositionsStreamReconnectTimer);
    activePositionsStreamReconnectTimer = null;
  }
  const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
  const socket = new WebSocket(`${protocol}://${location.host}/ws/positions`);
  socket.addEventListener('message', (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data && data.type === 'positions') {
        const payload = data.open ?? data.payload ?? data.positions;
        if (payload !== undefined) {
          applyActivePositionsPayload(payload);
        }
      }
    } catch (err) {
      console.error('Position stream parse error', err);
    }
  });
  socket.addEventListener('close', () => {
    activePositionsStreamReconnectTimer = setTimeout(connectActivePositionsStream, 2000);
  });
  socket.addEventListener('error', () => {
    socket.close();
  });
}

function createMetric(label, value, tone = 'neutral') {
  const metric = document.createElement('div');
  metric.className = 'trade-metric';
  const labelEl = document.createElement('span');
  labelEl.className = 'metric-label';
  labelEl.textContent = label;
  const valueEl = document.createElement('span');
  valueEl.className = 'metric-value';
  if (tone && tone !== 'neutral') {
    valueEl.classList.add(tone);
  }
  valueEl.textContent = value ?? '–';
  metric.append(labelEl, valueEl);
  return metric;
}

function createTradeDetail(label, value, options = {}) {
  const { tone = 'neutral', muted = false, monospace = false } = options;
  const container = document.createElement('span');
  container.className = 'trade-detail';
  if (tone && tone !== 'neutral') {
    container.classList.add(tone);
  }
  if (muted) {
    container.classList.add('muted');
  }
  if (monospace) {
    container.classList.add('monospace');
  }

  const labelEl = document.createElement('span');
  labelEl.className = 'trade-detail-label';
  labelEl.textContent = label;
  const valueEl = document.createElement('span');
  valueEl.className = 'trade-detail-value';
  valueEl.textContent = value ?? '–';

  container.append(labelEl, valueEl);
  return container;
}

const TRADE_ENTRY_KEYS = ['entry', 'entry_price', 'entryPrice', 'expected_entry', 'avg_entry'];
const TRADE_EXIT_KEYS = ['exit', 'exit_price', 'exitPrice', 'exit_px', 'avg_exit'];
const TRADE_SIZE_KEYS = [
  'qty',
  'quantity',
  'size',
  'size_usd',
  'size_usdt',
  'notional',
  'notional_usd',
  'notionalUsd',
];

function pickTradeNumber(trade, keys) {
  if (!trade || typeof trade !== 'object' || !Array.isArray(keys)) return null;
  for (const key of keys) {
    if (!key) continue;
    const value = trade[key];
    if (value === undefined || value === null) continue;
    const numeric = Number(value);
    if (Number.isFinite(numeric)) {
      return numeric;
    }
  }
  return null;
}

function getTradeEntryPrice(trade) {
  return pickTradeNumber(trade, TRADE_ENTRY_KEYS);
}

function getTradeExitPrice(trade) {
  return pickTradeNumber(trade, TRADE_EXIT_KEYS);
}

function getTradeSize(trade) {
  return pickTradeNumber(trade, TRADE_SIZE_KEYS);
}

function getTradeBucketLabel(trade) {
  if (!trade || typeof trade !== 'object') return null;
  const candidates = [trade.bucket, trade.size_bucket, trade.bandit_bucket, trade.bucket_label];
  for (const candidate of candidates) {
    if (candidate === undefined || candidate === null) continue;
    const value = candidate.toString().trim();
    if (value) {
      return value;
    }
  }
  return null;
}

function buildTradeDetailContent(trade) {
  const pnl = extractRealizedPnl(trade);
  const pnlTone = pnl > 0 ? 'profit' : pnl < 0 ? 'loss' : 'neutral';
  const pnlDisplay = `${pnl > 0 ? '+' : ''}${formatNumber(pnl, 2)} USDT`;
  const rValue = Number(trade.pnl_r ?? 0);
  const rTone = rValue > 0 ? 'profit' : rValue < 0 ? 'loss' : 'neutral';
  const rDisplay = `${rValue > 0 ? '+' : ''}${formatNumber(rValue, 2)} R`;
  const durationSeconds = computeDurationSeconds(trade.opened_at_iso, trade.closed_at_iso);
  const entryPrice = getTradeEntryPrice(trade);
  const exitPrice = getTradeExitPrice(trade);
  const sizeValue = getTradeSize(trade);
  const bucketLabel = getTradeBucketLabel(trade);
  const syntheticSource = (trade.synthetic_source || '').toString().toLowerCase();
  const isSynthetic = Boolean(trade.synthetic) || Boolean(syntheticSource);
  const isRealizedIncome = isSynthetic && syntheticSource === 'realized_income';
  const context = trade.context && typeof trade.context === 'object' ? trade.context : null;

  const container = document.createElement('div');
  container.className = 'trade-modal-content';

  const highlight = document.createElement('div');
  highlight.className = 'trade-modal-highlight';

  const priceGroup = document.createElement('div');
  priceGroup.className = 'trade-detail-group';
  if (entryPrice !== null) {
    priceGroup.append(
      createTradeDetail('Entry', formatNumber(entryPrice, 4), {
        monospace: true,
      })
    );
  }
  if (exitPrice !== null) {
    priceGroup.append(
      createTradeDetail('Exit', formatNumber(exitPrice, 4), {
        monospace: true,
      })
    );
  }
  if (priceGroup.children.length > 0) {
    highlight.append(priceGroup);
  }

  const resultGroup = document.createElement('div');
  resultGroup.className = 'trade-detail-group';
  const pnlLabel =
    pnlTone === 'profit' ? 'Realized profit' : pnlTone === 'loss' ? 'Realized loss' : 'Realized PNL';
  resultGroup.append(
    createTradeDetail(pnlLabel, pnlDisplay, { tone: pnlTone }),
    createTradeDetail('R multiple', rDisplay, { tone: rTone, muted: rTone === 'neutral' })
  );
  highlight.append(resultGroup);

  const timeGroup = document.createElement('div');
  timeGroup.className = 'trade-detail-group';
  const windowStart = formatTimeShort(trade.opened_at_iso);
  const windowEnd = formatTimeShort(trade.closed_at_iso);
  if (windowStart !== '–' || windowEnd !== '–') {
    timeGroup.append(
      createTradeDetail('Window', `${windowStart} → ${windowEnd}`, {
        monospace: true,
      })
    );
  }
  if (Number.isFinite(durationSeconds)) {
    timeGroup.append(createTradeDetail('Duration', formatDuration(durationSeconds), { muted: true }));
  }
  if (timeGroup.children.length > 0) {
    highlight.append(timeGroup);
  }

  if (isRealizedIncome) {
    const syntheticNote = document.createElement('p');
    syntheticNote.className = 'trade-synthetic-note';
    syntheticNote.textContent = translate(
      'trades.synthetic.note',
      'Synced from exchange realized PnL; entry/exit data unavailable.'
    );
    highlight.append(syntheticNote);
    const metaParts = [];
    const incomeType = context?.income_type || trade.income_type;
    if (incomeType) {
      metaParts.push(incomeType.toString());
    }
    const incomeInfo = context?.income_info || context?.info || trade.income_info;
    if (incomeInfo) {
      metaParts.push(incomeInfo.toString());
    }
    if (metaParts.length > 0) {
      const meta = document.createElement('p');
      meta.className = 'trade-synthetic-meta';
      meta.textContent = metaParts.join(' · ');
      highlight.append(meta);
    }
  }

  container.append(highlight);

  const metricGrid = document.createElement('div');
  metricGrid.className = 'trade-metric-grid';
  const metrics = [
    createMetric('Realized PNL (USDT)', pnlDisplay, pnlTone),
    createMetric('R multiple', rDisplay, rTone),
  ];
  metrics.forEach((metric) => metricGrid.append(metric));

  const optionalMetrics = [];
  if (sizeValue !== null) {
    optionalMetrics.push(createMetric('Size', formatNumber(sizeValue, 4)));
  }
  if (bucketLabel) {
    optionalMetrics.push(createMetric('Bandit bucket', bucketLabel.toString().toUpperCase()));
  }
  const openedText = formatTimestamp(trade.opened_at_iso);
  if (openedText && openedText !== '–') {
    optionalMetrics.push(createMetric('Opened', openedText));
  }
  const closedText = formatTimestamp(trade.closed_at_iso);
  if (closedText && closedText !== '–') {
    optionalMetrics.push(createMetric('Closed', closedText));
  }
  if (Number.isFinite(durationSeconds)) {
    optionalMetrics.push(createMetric('Duration', formatDuration(durationSeconds)));
  }
  if (entryPrice !== null) {
    optionalMetrics.push(createMetric('Entry', formatNumber(entryPrice, 4)));
  }
  if (exitPrice !== null) {
    optionalMetrics.push(createMetric('Exit', formatNumber(exitPrice, 4)));
  }
  if (isRealizedIncome) {
    const incomeType = context?.income_type || trade.income_type;
    if (incomeType) {
      optionalMetrics.push(
        createMetric(translate('trades.synthetic.incomeType', 'Income type'), incomeType.toString())
      );
    }
    const incomeInfo = context?.income_info || context?.info || trade.income_info;
    if (incomeInfo) {
      optionalMetrics.push(
        createMetric(translate('trades.synthetic.info', 'Exchange info'), incomeInfo.toString())
      );
    }
  }
  optionalMetrics.forEach((metric) => metricGrid.append(metric));
  container.append(metricGrid);

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
      container.append(contextWrapper);
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
      sentinelMeta.innerHTML = `Event risk ${(risk * 100).toFixed(1)}% · Hype ${(hype * 100).toFixed(1)}% · Size factor ${Number(
        sentinel.actions?.size_factor ?? 1
      ).toFixed(2)}×`;
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

    container.append(aiSection);
  }

  const postmortem = trade.postmortem && typeof trade.postmortem === 'object' ? trade.postmortem : null;
  if (postmortem && postmortem.analysis) {
    const postSection = document.createElement('div');
    postSection.className = 'trade-postmortem';
    const heading = document.createElement('h4');
    heading.textContent = translate('trades.postmortem.label', 'Post-mortem coach');
    const summary = document.createElement('p');
    summary.textContent = postmortem.analysis;
    postSection.append(heading, summary);
    container.append(postSection);
  }

  return container;
}

function buildCompletedPositionDetailContent(position) {
  const pnlField = pickNumericField(position, COMPLETED_POSITION_PNL_KEYS);
  const pnlNumeric = Number.isFinite(pnlField.numeric) ? pnlField.numeric : null;
  const pnlTone = pnlNumeric > 0 ? 'profit' : pnlNumeric < 0 ? 'loss' : 'neutral';
  const pnlDisplay = pnlNumeric !== null
    ? `${formatSignedNumber(pnlNumeric, 2)} USDT`
    : pnlField.value
      ? pnlField.value.toString()
      : '—';
  const rField = pickNumericField(position, COMPLETED_POSITION_R_KEYS);
  const rNumeric = Number.isFinite(rField.numeric) ? rField.numeric : null;
  const rTone = rNumeric > 0 ? 'profit' : rNumeric < 0 ? 'loss' : 'neutral';
  const rDisplay = rNumeric !== null ? `${formatSignedNumber(rNumeric, 2)} R` : null;
  const roeField = pickFieldValue(position, ACTIVE_POSITION_ALIASES.roe || []);
  const roeNumeric = toNumeric(roeField.value);
  let roeDisplay = null;
  if (Number.isFinite(roeNumeric)) {
    roeDisplay = `${formatSignedNumber(roeNumeric, 2)}%`;
  } else {
    const roeText = extractFieldStringSource(roeField);
    if (roeText) {
      roeDisplay = roeText;
    }
  }
  const notionalField = pickNumericField(position, ACTIVE_POSITION_NOTIONAL_KEYS || []);
  const notionalDisplay = Number.isFinite(notionalField.numeric)
    ? `${formatNumber(Math.abs(notionalField.numeric), 2)} USDT`
    : null;
  const leverageField = pickNumericField(position, ACTIVE_POSITION_ALIASES.leverage || []);
  const leverageDisplay = Number.isFinite(leverageField.numeric)
    ? formatLeverage(leverageField.numeric)
    : null;
  const entryField = pickNumericField(position, TRADE_ENTRY_KEYS);
  const exitField = pickNumericField(position, TRADE_EXIT_KEYS);
  const openedTs = getPositionTimestamp(position);
  const closedTs = getPositionClosedTimestamp(position);
  const openedLabel = Number.isFinite(openedTs)
    ? formatTimestamp(new Date(openedTs * 1000).toISOString())
    : null;
  const closedLabel = Number.isFinite(closedTs)
    ? formatTimestamp(new Date(closedTs * 1000).toISOString())
    : null;
  const durationSeconds = computePositionDurationSeconds(position);
  const reasonCode = extractPositionManagementExitReason(position);
  const reasonLabel = reasonCode
    ? friendlyReason(reasonCode)
    : translate('trades.completed.noReason', 'No exit reason logged.');

  const container = document.createElement('div');
  container.className = 'trade-modal-content completed-position-modal-content';

  const highlight = document.createElement('div');
  highlight.className = 'trade-modal-highlight';
  const statsGroup = document.createElement('div');
  statsGroup.className = 'trade-detail-group';
  statsGroup.append(
    createTradeDetail(translate('trades.completed.pnl', 'Realized PNL'), pnlDisplay, { tone: pnlTone })
  );
  if (roeDisplay) {
    statsGroup.append(createTradeDetail('ROE', roeDisplay));
  }
  if (rDisplay) {
    statsGroup.append(createTradeDetail('R multiple', rDisplay, { tone: rTone }));
  }
  highlight.append(statsGroup);
  container.append(highlight);

  const metricGrid = document.createElement('div');
  metricGrid.className = 'trade-metric-grid';
  const metrics = [];
  if (notionalDisplay) {
    metrics.push(createMetric('Notional', notionalDisplay));
  }
  if (leverageDisplay) {
    metrics.push(createMetric('Leverage', leverageDisplay));
  }
  if (Number.isFinite(entryField.numeric)) {
    metrics.push(createMetric('Entry', formatNumber(entryField.numeric, 4)));
  }
  if (Number.isFinite(exitField.numeric)) {
    metrics.push(createMetric('Exit', formatNumber(exitField.numeric, 4)));
  }
  if (openedLabel && openedLabel !== '–') {
    metrics.push(createMetric('Opened', openedLabel));
  }
  if (closedLabel && closedLabel !== '–') {
    metrics.push(createMetric('Closed', closedLabel));
  }
  if (Number.isFinite(durationSeconds)) {
    metrics.push(createMetric('Duration', formatDuration(durationSeconds)));
  }
  if (reasonLabel) {
    metrics.push(createMetric(translate('trades.completed.reason', 'Exit reason'), reasonLabel));
  }
  metrics.forEach((metric) => metricGrid.append(metric));
  if (metricGrid.childElementCount > 0) {
    container.append(metricGrid);
  }

  const postmortem = position.postmortem && typeof position.postmortem === 'object' ? position.postmortem : null;
  if (postmortem && postmortem.analysis) {
    const postSection = document.createElement('div');
    postSection.className = 'trade-postmortem';
    const heading = document.createElement('h4');
    heading.textContent = translate('trades.postmortem.label', 'Post-mortem coach');
    const summary = document.createElement('p');
    summary.textContent = postmortem.analysis;
    postSection.append(heading, summary);
    container.append(postSection);
  }

  return container;
}

function buildTradeSummaryCard(trade) {
  const pnl = extractRealizedPnl(trade);
  const pnlTone = pnl > 0 ? 'profit' : pnl < 0 ? 'loss' : 'neutral';
  const pnlDisplay = `${pnl > 0 ? '+' : ''}${formatNumber(pnl, 2)} USDT`;
  const rValue = Number(trade.pnl_r ?? 0);
  const rTone = rValue > 0 ? 'profit' : rValue < 0 ? 'loss' : 'neutral';
  const rDisplay = `${rValue > 0 ? '+' : ''}${formatNumber(rValue, 2)} R`;
  const durationSeconds = computeDurationSeconds(trade.opened_at_iso, trade.closed_at_iso);
  const syntheticSource = (trade.synthetic_source || '').toString().toLowerCase();
  const isSyntheticIncome = Boolean(trade.synthetic) || syntheticSource === 'realized_income';
  const syntheticLabel = isSyntheticIncome
    ? translate('trades.synthetic.badge', 'Realized PnL')
    : null;
  const postmortemSummary = extractPostmortemSummary(trade);

  const card = document.createElement('button');
  card.type = 'button';
  card.className = 'trade-card';
  if (trade.side) {
    card.dataset.side = trade.side.toString().toLowerCase();
  }
  if (pnlTone && pnlTone !== 'neutral') {
    card.dataset.pnl = pnlTone;
  }
  if (isSyntheticIncome) {
    card.dataset.synthetic = 'true';
  }

  const top = document.createElement('div');
  top.className = 'trade-card-top';

  const main = document.createElement('div');
  main.className = 'trade-card-main';

  const symbol = document.createElement('span');
  symbol.className = 'trade-card-symbol';
  symbol.textContent = trade.symbol || '–';
  main.append(symbol);

  if (trade.side) {
    const sideBadge = document.createElement('span');
    sideBadge.className = 'trade-card-side';
    sideBadge.textContent = formatSideLabel(trade.side);
    main.append(sideBadge);
  }

  if (syntheticLabel) {
    const badge = document.createElement('span');
    badge.className = 'trade-card-badge';
    badge.textContent = syntheticLabel;
    main.append(badge);
  }

  const pnlEl = document.createElement('span');
  pnlEl.className = `trade-card-pnl ${pnlTone}`.trim();
  pnlEl.textContent = pnlDisplay;
  top.append(main, pnlEl);

  const bottom = document.createElement('div');
  bottom.className = 'trade-card-bottom';

  const info = document.createElement('div');
  info.className = 'trade-card-info';

  const timestampLabel = formatTimestamp(trade.closed_at_iso || trade.opened_at_iso);
  if (timestampLabel && timestampLabel !== '–') {
    const timeSpan = document.createElement('span');
    timeSpan.textContent = `Closed ${timestampLabel}`;
    info.append(timeSpan);
  }

  const windowStart = formatTimeShort(trade.opened_at_iso);
  const windowEnd = formatTimeShort(trade.closed_at_iso);
  if (windowStart !== '–' || windowEnd !== '–') {
    const windowSpan = document.createElement('span');
    windowSpan.className = 'trade-card-window';
    windowSpan.textContent = `Window ${windowStart} → ${windowEnd}`;
    info.append(windowSpan);
  }

  if (Number.isFinite(durationSeconds)) {
    const durationSpan = document.createElement('span');
    durationSpan.textContent = `Held ${formatDuration(durationSeconds)}`;
    info.append(durationSpan);
  }

  if (info.children.length === 0) {
    const placeholder = document.createElement('span');
    placeholder.textContent = 'Timing data unavailable';
    info.append(placeholder);
  }

  if (syntheticLabel) {
    const note = document.createElement('span');
    note.className = 'trade-card-note';
    note.textContent = syntheticLabel;
    info.append(note);
  }

  const actions = document.createElement('div');
  actions.className = 'trade-card-actions';

  const rSpan = document.createElement('span');
  rSpan.className = `trade-card-r ${rTone}`.trim();
  rSpan.textContent = rDisplay;
  actions.append(rSpan);

  const hint = document.createElement('span');
  hint.className = 'trade-card-hint';
  hint.textContent = translate('trades.viewDetails', 'View details');
  actions.append(hint);

  bottom.append(info, actions);

  if (postmortemSummary) {
    const snippet = document.createElement('div');
    snippet.className = 'trade-card-postmortem';

    const labelEl = document.createElement('span');
    labelEl.className = 'trade-card-postmortem-label';
    labelEl.textContent = translate('trades.postmortem.label', 'Post-mortem coach');

    const textEl = document.createElement('p');
    textEl.className = 'trade-card-postmortem-text';
    textEl.textContent = postmortemSummary;

    snippet.append(labelEl, textEl);
    bottom.insertBefore(snippet, actions);
  }

  card.append(top, bottom);

  const symbolLabel = trade.symbol || 'trade';
  const sideLabel = trade.side ? `${formatSideLabel(trade.side)} ` : '';
  const accessibleTime =
    timestampLabel && timestampLabel !== '–' ? `closed ${timestampLabel}` : 'timestamp unavailable';
  card.setAttribute('aria-label', `View ${sideLabel}${symbolLabel} details (${accessibleTime})`);
  card.addEventListener('click', () => openTradeModal(trade, card));

  return card;
}

function extractPostmortemSummary(trade) {
  if (!trade || typeof trade !== 'object') return null;
  const postmortem = trade.postmortem && typeof trade.postmortem === 'object' ? trade.postmortem : null;
  if (!postmortem) return null;
  const candidates = [
    postmortem.card_summary,
    postmortem.summary,
    postmortem.note,
    postmortem.analysis,
  ];
  for (const candidate of candidates) {
    if (typeof candidate !== 'string') continue;
    const trimmed = candidate.trim();
    if (!trimmed) continue;
    const normalized = trimmed.replace(/\s+/g, ' ');
    if (!normalized) continue;
    return truncatePostmortemSummary(normalized);
  }
  return null;
}

function truncatePostmortemSummary(text, limit = 220) {
  if (typeof text !== 'string') return '';
  if (text.length <= limit) return text;
  const slice = text.slice(0, limit - 1);
  const lastSpace = slice.lastIndexOf(' ');
  const safe = lastSpace > limit * 0.5 ? slice.slice(0, lastSpace) : slice;
  return `${safe.trimEnd()}…`;
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

function getTradeTimestamp(trade) {
  if (!trade || typeof trade !== 'object') return 0;
  const closed = Date.parse(trade.closed_at_iso);
  if (Number.isFinite(closed)) return closed;
  const opened = Date.parse(trade.opened_at_iso);
  return Number.isFinite(opened) ? opened : 0;
}

function extractRealizedPnl(trade) {
  if (!trade || typeof trade !== 'object') {
    return 0;
  }

  const field = pickNumericField(trade, COMPLETED_POSITION_PNL_KEYS);
  if (Number.isFinite(field.numeric)) {
    return field.numeric;
  }

  const incomeValue = toNumeric(trade.income);
  if (Number.isFinite(incomeValue)) {
    return incomeValue;
  }

  const context = trade.context && typeof trade.context === 'object' ? trade.context : null;
  if (context) {
    const contextField = pickNumericField(context, COMPLETED_POSITION_PNL_KEYS);
    if (Number.isFinite(contextField.numeric)) {
      return contextField.numeric;
    }
    const contextIncome = toNumeric(context.income);
    if (Number.isFinite(contextIncome)) {
      return contextIncome;
    }
  }

  return 0;
}

function renderTradeHistory(history) {
  if (!tradeList) return;

  const hasHistory = Array.isArray(history) && history.length > 0;
  if (!hasHistory) {
    tradeHistoryEmptyStreak += 1;
    if (tradeList.childElementCount > 0 && tradeHistoryEmptyStreak === 1) {
      return;
    }
    const fragment = document.createDocumentFragment();
    const empty = document.createElement('div');
    empty.className = 'trade-empty';
    empty.textContent = translate('trades.empty', 'No trades yet.');
    fragment.append(empty);
    tradeList.replaceChildren(fragment);
    tradeList.style.removeProperty('max-height');
    tradeList.removeAttribute('data-viewport-locked');
    tradeHistoryEmptyStreak = Math.min(Math.max(tradeHistoryEmptyStreak, 1), 2);
    return;
  }

  tradeHistoryEmptyStreak = 0;

  const sortedHistory = [...history].sort((a, b) => getTradeTimestamp(b) - getTradeTimestamp(a));

  const fragment = document.createDocumentFragment();
  sortedHistory.forEach((trade) => {
    const card = buildTradeSummaryCard(trade);
    fragment.append(card);
  });

  tradeList.replaceChildren(fragment);

  requestTradeListViewportSync();
  syncCompletedPositionsFromTrades(sortedHistory);
}

function handleTradeModalKeydown(event) {
  if (event.key === 'Escape') {
    closeTradeModal();
  }
}

function presentTradeModalContent({ title, subtitle, content, returnTarget } = {}) {
  if (!tradeModal || !tradeModalBody) return;

  const active =
    returnTarget instanceof HTMLElement
      ? returnTarget
      : document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
  tradeModalReturnTarget = active && active !== document.body ? active : null;

  if (tradeModalHideTimer) {
    clearTimeout(tradeModalHideTimer);
    tradeModalHideTimer = null;
  }
  if (tradeModalFinalizeHandler) {
    tradeModal.removeEventListener('transitionend', tradeModalFinalizeHandler);
    tradeModalFinalizeHandler = null;
  }

  const resolvedContent = content instanceof Node ? content : document.createElement('div');
  tradeModalBody.innerHTML = '';
  tradeModalBody.append(resolvedContent);
  tradeModalBody.scrollTop = 0;

  if (tradeModalTitle) {
    tradeModalTitle.textContent = title || translate('modals.trade.title', 'Trade details');
  }

  if (tradeModalSubtitle) {
    tradeModalSubtitle.textContent =
      subtitle || translate('trades.modal.noMetadata', 'No additional metadata available.');
  }

  tradeModal.removeAttribute('hidden');
  tradeModal.removeAttribute('aria-hidden');
  requestAnimationFrame(() => {
    tradeModal.classList.add('is-active');
  });
  document.body.classList.add('modal-open');

  document.addEventListener('keydown', handleTradeModalKeydown);
  if (tradeModalClose) {
    setTimeout(() => tradeModalClose.focus(), 120);
  }
}

function openTradeModal(trade, returnTarget) {
  if (!tradeModal || !tradeModalBody) return;

  const pnl = extractRealizedPnl(trade);
  const pnlTone = pnl > 0 ? 'profit' : pnl < 0 ? 'loss' : 'neutral';
  const pnlDisplay = `${pnl > 0 ? '+' : ''}${formatNumber(pnl, 2)} USDT`;
  const durationSeconds = computeDurationSeconds(trade.opened_at_iso, trade.closed_at_iso);
  const symbol = trade.symbol || 'Trade';
  const sideLabel = trade.side ? formatSideLabel(trade.side) : null;
  const titleParts = [symbol];
  if (sideLabel) {
    titleParts.push(sideLabel);
  }

  const outcomeLabel =
    pnlTone === 'profit' ? 'Realized profit' : pnlTone === 'loss' ? 'Realized loss' : 'Flat';
  const timestampLabel = formatTimestamp(trade.closed_at_iso || trade.opened_at_iso);
  const subtitleParts = [];
  if (timestampLabel && timestampLabel !== '–') {
    subtitleParts.push(`Closed ${timestampLabel}`);
  }
  if (Number.isFinite(durationSeconds)) {
    subtitleParts.push(`Held ${formatDuration(durationSeconds)}`);
  }
  subtitleParts.push(`${outcomeLabel} ${pnlDisplay}`);

  const content = buildTradeDetailContent(trade);
  presentTradeModalContent({
    title: titleParts.filter(Boolean).join(' · '),
    subtitle: subtitleParts.filter(Boolean).join(' · '),
    content,
    returnTarget,
  });
}

function openCompletedPositionModal(position, options = {}) {
  if (!tradeModal || !tradeModalBody || !position) return;
  const { timestamp, returnTarget } = options || {};
  const notionalField = pickNumericField(position, ACTIVE_POSITION_NOTIONAL_KEYS || []);
  const signedSizeField = pickNumericField(position, ACTIVE_POSITION_SIGNED_SIZE_KEYS || []);
  const side = extractPositionSide(position, notionalField, signedSizeField);
  const titleParts = [getPositionSymbol(position) || translate('trades.completed.title', 'Completed positions')];
  if (side) {
    titleParts.push(formatSideLabel(side));
  }
  const referenceTimestamp = Number.isFinite(timestamp)
    ? Number(timestamp)
    : getPositionClosedTimestamp(position);
  const subtitleParts = [];
  if (Number.isFinite(referenceTimestamp)) {
    const absolute = formatTimestamp(new Date(referenceTimestamp * 1000).toISOString());
    if (absolute && absolute !== '–') {
      subtitleParts.push(`Closed ${absolute}`);
    }
  }
  const durationSeconds = computePositionDurationSeconds(position);
  if (Number.isFinite(durationSeconds)) {
    subtitleParts.push(`Held ${formatDuration(durationSeconds)}`);
  }
  const pnlField = pickNumericField(position, COMPLETED_POSITION_PNL_KEYS);
  if (Number.isFinite(pnlField.numeric)) {
    subtitleParts.push(
      `${translate('trades.completed.pnl', 'Realized PNL')} ${formatSignedNumber(pnlField.numeric, 2)} USDT`,
    );
  }

  const content = buildCompletedPositionDetailContent(position);
  presentTradeModalContent({
    title: titleParts.filter(Boolean).join(' · '),
    subtitle: subtitleParts.filter(Boolean).join(' · '),
    content,
    returnTarget,
  });
}

function closeTradeModal() {
  if (!tradeModal) {
    return;
  }

  if (tradeModalHideTimer) {
    clearTimeout(tradeModalHideTimer);
    tradeModalHideTimer = null;
  }
  if (tradeModalFinalizeHandler) {
    tradeModal.removeEventListener('transitionend', tradeModalFinalizeHandler);
    tradeModalFinalizeHandler = null;
  }
  if (tradeModal.hasAttribute('hidden')) {
    return;
  }

  tradeModal.classList.remove('is-active');
  tradeModal.setAttribute('aria-hidden', 'true');
  document.body.classList.remove('modal-open');

  const finalize = () => {
    if (tradeModalHideTimer) {
      clearTimeout(tradeModalHideTimer);
      tradeModalHideTimer = null;
    }
    if (!tradeModal.hasAttribute('hidden')) {
      tradeModal.setAttribute('hidden', '');
    }
    if (tradeModalFinalizeHandler) {
      tradeModal.removeEventListener('transitionend', tradeModalFinalizeHandler);
      tradeModalFinalizeHandler = null;
    }
    const restoreTarget =
      tradeModalReturnTarget && typeof tradeModalReturnTarget.focus === 'function' ? tradeModalReturnTarget : null;
    tradeModalReturnTarget = null;
    if (restoreTarget) {
      restoreTarget.focus({ preventScroll: true });
    }
  };

  tradeModalFinalizeHandler = finalize;
  tradeModal.addEventListener('transitionend', finalize);
  tradeModalHideTimer = setTimeout(finalize, 280);

  document.removeEventListener('keydown', handleTradeModalKeydown);
}

function handleDecisionModalKeydown(event) {
  if (event.key === 'Escape') {
    closeDecisionModal();
  }
}

function renderDecisionModalEvents(events, reasonLabel) {
  const list = document.createElement('ul');
  list.className = 'decision-modal-list';

  events.forEach((event) => {
    const item = document.createElement('li');
    item.className = 'decision-modal-event';

    const header = document.createElement('div');
    header.className = 'decision-modal-event-header';

    const symbol = document.createElement('span');
    symbol.className = 'decision-modal-symbol';
    symbol.textContent = event.symbol || reasonLabel || '—';
    header.append(symbol);

    const time = document.createElement('span');
    time.className = 'decision-modal-time';
    if (event.occurredAtIso) {
      time.textContent = formatRelativeTime(event.occurredAtIso);
      time.title = new Date(event.occurredAtIso).toLocaleString();
    } else if (Number.isFinite(event.occurredAt)) {
      time.textContent = formatRelativeTime(event.occurredAt);
      time.title = new Date(event.occurredAt * 1000).toLocaleString();
    } else {
      time.textContent = 'Time unavailable';
    }
    header.append(time);

    item.append(header);

    if (event.message) {
      const message = document.createElement('p');
      message.className = 'decision-modal-message';
      message.textContent = event.message;
      item.append(message);
    }

    if (event.detail) {
      const detail = document.createElement('p');
      detail.className = 'decision-modal-detail';
      detail.textContent = event.detail;
      item.append(detail);
    }

    if (event.trade) {
      const actionRow = document.createElement('div');
      actionRow.className = 'decision-modal-actions';
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'decision-modal-view-trade';
      button.textContent = 'View trade details';
      button.addEventListener('click', () => {
        closeDecisionModal();
        openTradeModal(event.trade, button);
      });
      actionRow.append(button);
      item.append(actionRow);
    }

    list.append(item);
  });

  return list;
}

function openDecisionModal(reason, options = {}) {
  if (!decisionModal || !decisionModalBody) return;
  const { label: labelOverride, count, returnTarget } = options;
  const reasonLabel = labelOverride || friendlyReason(reason);
  const events = collectDecisionEvents(reason);

  const active =
    returnTarget instanceof HTMLElement
      ? returnTarget
      : document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
  decisionModalReturnTarget = active && active !== document.body ? active : null;

  if (decisionModalHideTimer) {
    clearTimeout(decisionModalHideTimer);
    decisionModalHideTimer = null;
  }
  if (decisionModalFinalizeHandler) {
    decisionModal.removeEventListener('transitionend', decisionModalFinalizeHandler);
    decisionModalFinalizeHandler = null;
  }

  decisionModalBody.innerHTML = '';

  if (decisionModalTitle) {
    decisionModalTitle.textContent = reasonLabel || translate('modals.decision.title', 'Trade decision reason');
  }

  const subtitleParts = [];
  if (Number.isFinite(count)) {
    subtitleParts.push(`${count} total skips recorded`);
  }
  if (events.length > 0) {
    subtitleParts.push(`Showing ${events.length} recent ${events.length === 1 ? 'entry' : 'entries'}`);
  } else {
    subtitleParts.push(translate('status.decisions.noReasonShort', 'No recorded trades for this reason yet.'));
  }
  if (decisionModalSubtitle) {
    decisionModalSubtitle.textContent = subtitleParts.join(' · ');
  }

  if (events.length > 0) {
    decisionModalBody.append(renderDecisionModalEvents(events, reasonLabel));
  } else {
    const empty = document.createElement('p');
    empty.className = 'decision-modal-empty';
    empty.textContent = translate(
      'status.decisions.noReason',
      'No recorded trades for this reason yet. Check back after the next decision.'
    );
    decisionModalBody.append(empty);
  }

  decisionModal.removeAttribute('hidden');
  decisionModal.removeAttribute('aria-hidden');
  requestAnimationFrame(() => {
    decisionModal.classList.add('is-active');
  });
  document.body.classList.add('modal-open');
  document.addEventListener('keydown', handleDecisionModalKeydown);
  if (decisionModalClose) {
    setTimeout(() => decisionModalClose.focus(), 120);
  }
}

function closeDecisionModal() {
  if (!decisionModal) {
    return;
  }

  if (decisionModalHideTimer) {
    clearTimeout(decisionModalHideTimer);
    decisionModalHideTimer = null;
  }

  if (decisionModalFinalizeHandler) {
    decisionModal.removeEventListener('transitionend', decisionModalFinalizeHandler);
    decisionModalFinalizeHandler = null;
  }

  if (decisionModal.hasAttribute('hidden')) {
    return;
  }

  decisionModal.classList.remove('is-active');
  decisionModal.setAttribute('aria-hidden', 'true');
  document.body.classList.remove('modal-open');

  const finalize = () => {
    if (decisionModalHideTimer) {
      clearTimeout(decisionModalHideTimer);
      decisionModalHideTimer = null;
    }
    if (!decisionModal.hasAttribute('hidden')) {
      decisionModal.setAttribute('hidden', '');
    }
    if (decisionModalFinalizeHandler) {
      decisionModal.removeEventListener('transitionend', decisionModalFinalizeHandler);
      decisionModalFinalizeHandler = null;
    }
    const restoreTarget =
      decisionModalReturnTarget && typeof decisionModalReturnTarget.focus === 'function'
        ? decisionModalReturnTarget
        : null;
    decisionModalReturnTarget = null;
    if (restoreTarget) {
      restoreTarget.focus({ preventScroll: true });
    }
  };

  decisionModalFinalizeHandler = finalize;
  decisionModal.addEventListener('transitionend', finalize);
  decisionModalHideTimer = setTimeout(finalize, 280);
  document.removeEventListener('keydown', handleDecisionModalKeydown);
}

function renderAiBudget(budget) {
  if (!aiBudgetCard || !aiBudgetModeLabel || !aiBudgetMeta || !aiBudgetFill) return;
  lastAiBudget = budget || null;
  aiBudgetCard.classList.toggle('active', aiMode);
  updateAiBudgetModeLabel();
  if (paperMode) {
    aiBudgetFill.style.width = '0%';
    aiBudgetMeta.textContent = translate('status.aiBudgetMeta.paper', 'Paper mode does not use a budget.');
    return;
  }
  if (!aiMode) {
    aiBudgetFill.style.width = '0%';
    aiBudgetMeta.textContent = translate('status.aiBudgetMeta.disabled', 'AI-Mode disabled.');
    return;
  }
  let limit = Number((budget && budget.limit) ?? 0);
  let spent = Number((budget && budget.spent) ?? 0);
  if (!Number.isFinite(spent) || spent < 0) {
    spent = 0;
  }
  const presetMode = (currentConfig?.env?.ASTER_PRESET_MODE || '').toString().toLowerCase();
  const presetForcesUnlimited = presetMode === 'high' || presetMode === 'att';
  if (!Number.isFinite(limit) || limit <= 0) {
    const envLimit = Number(currentConfig?.env?.ASTER_AI_DAILY_BUDGET_USD ?? 0);
    if (!presetForcesUnlimited && Number.isFinite(envLimit) && envLimit > 0) {
      limit = envLimit;
    }
  }
  const hasLimit = Number.isFinite(limit) && limit > 0;
  aiBudgetCard.classList.toggle('unlimited', !hasLimit);
  if (!Number.isFinite(limit) || limit < 0) {
    limit = 0;
  }
  let requestCount = Number((budget && budget.count) ?? 0);
  if (!Number.isFinite(requestCount) || requestCount < 0) {
    requestCount = 0;
  }
  requestCount = Math.floor(requestCount);
  const requestLabel = translate(
    requestCount === 1 ? 'status.aiBudgetMeta.requests.one' : 'status.aiBudgetMeta.requests.many',
    `${requestCount} ${requestCount === 1 ? 'request' : 'requests'} today`,
    { count: requestCount }
  );
  if (!hasLimit) {
    const presetNote = presetForcesUnlimited
      ? presetMode === 'high'
        ? ' · High preset removes the AI spend cap.'
        : ' · ATT preset removes the AI spend cap.'
      : '';
    aiBudgetFill.style.width = '0%';
    aiBudgetMeta.textContent = translate(
      presetForcesUnlimited ? 'status.aiBudgetMeta.unlimitedPreset' : 'status.aiBudgetMeta.unlimited',
      `Spent ${spent.toFixed(2)} USD · unlimited budget${presetNote} · ${requestLabel}`,
      { spent: spent.toFixed(2), note: presetNote, requests: requestCount, requests_label: requestLabel }
    );
    return;
  }
  const pct = clampValue(limit > 0 ? (spent / limit) * 100 : 0, 0, 100);
  aiBudgetFill.style.width = `${pct.toFixed(1)}%`;
  const remaining = Math.max(0, limit - spent);
  aiBudgetMeta.textContent = translate(
    'status.aiBudgetMeta.limited',
    `Spent ${spent.toFixed(2)} / ${limit.toFixed(2)} USD · remaining ${remaining.toFixed(2)} USD · ${requestLabel}`,
    {
      spent: spent.toFixed(2),
      limit: limit.toFixed(2),
      remaining: remaining.toFixed(2),
      requests: requestCount,
      requests_label: requestLabel,
    }
  );
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
  const items = Array.from(tradeList.querySelectorAll('.trade-card'));
  if (items.length <= 2) {
    tradeList.style.removeProperty('max-height');
    tradeList.removeAttribute('data-viewport-locked');
    return;
  }

  const sample = items.slice(0, 2);
  let visibleHeight = 0;
  sample.forEach((item) => {
    visibleHeight += item.getBoundingClientRect().height;
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
  const totalHeight =
    visibleHeight + gapValue * Math.max(0, sample.length - 1) + paddingTop + paddingBottom + 4;

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
  window.addEventListener('resize', () => requestTradeListViewportSync());
}

function toTitleCase(value) {
  const text = (value ?? '').toString().trim();
  if (!text) return '';
  return text
    .replace(/[_\-]+/g, ' ')
    .split(' ')
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

const PLAYBOOK_PROCESS_STATUS_FALLBACKS = {
  pending: 'Awaiting AI response',
  applied: 'Playbook applied',
  failed: 'Refresh failed',
};

const PLAYBOOK_PROCESS_STAGE_FALLBACKS = {
  requested: 'Request sent',
  applied: 'Applied',
  failed: 'Failed',
  info: 'Update logged',
};

const PLAYBOOK_SIZE_BIAS_PRIORITY = ['BUY', 'SELL', 'LONG', 'SHORT', 'S', 'M', 'L'];

function formatPlaybookMultiplier(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return '–';
  return `×${numeric.toFixed(2)}`;
}

function formatPlaybookSigned(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return '0.00';
  const sign = numeric >= 0 ? '+' : '';
  return `${sign}${numeric.toFixed(2)}`;
}

function formatPlaybookPercent(value, fractionDigits = 0) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return '–';
  const percentage = numeric * 100;
  return `${percentage.toFixed(fractionDigits)}%`;
}

function formatPlaybookSizeLabel(label) {
  const text = (label ?? '').toString().trim();
  if (!text) return '';
  if (text.length <= 3) return text.toUpperCase();
  return toTitleCase(text);
}

function normalizePlaybookSizeBiasEntries(map) {
  if (!map || typeof map !== 'object') return [];
  const entries = [];
  Object.entries(map).forEach(([key, rawValue]) => {
    const numeric = Number(rawValue);
    if (!Number.isFinite(numeric)) return;
    const label = formatPlaybookSizeLabel(key);
    if (!label) return;
    entries.push({ label, value: numeric });
  });
  entries.sort((a, b) => {
    const aIndex = PLAYBOOK_SIZE_BIAS_PRIORITY.indexOf(a.label.toUpperCase());
    const bIndex = PLAYBOOK_SIZE_BIAS_PRIORITY.indexOf(b.label.toUpperCase());
    if (aIndex !== -1 || bIndex !== -1) {
      if (aIndex === -1) return 1;
      if (bIndex === -1) return -1;
      if (aIndex !== bIndex) return aIndex - bIndex;
    }
    return a.label.localeCompare(b.label, undefined, { sensitivity: 'base' });
  });
  return entries;
}

function getPlaybookActivityTimestampMs(entry) {
  if (!entry || typeof entry !== 'object') return Number.NEGATIVE_INFINITY;
  const epoch = Number(entry.ts_epoch);
  if (Number.isFinite(epoch)) {
    return epoch * 1000;
  }
  const ts = entry.ts;
  if (!ts) return Number.NEGATIVE_INFINITY;
  const parsed = Date.parse(ts);
  return Number.isNaN(parsed) ? Number.NEGATIVE_INFINITY : parsed;
}

function getPlaybookProcessStatusLabel(statusKey) {
  const normalized = (statusKey || 'pending').toString().toLowerCase();
  return translate(
    `playbook.process.status.${normalized}`,
    PLAYBOOK_PROCESS_STATUS_FALLBACKS[normalized] || PLAYBOOK_PROCESS_STATUS_FALLBACKS.pending
  );
}

function getPlaybookProcessStageLabel(stageKey) {
  const normalized = (stageKey || 'info').toString().toLowerCase();
  return translate(
    `playbook.process.stage.${normalized}`,
    PLAYBOOK_PROCESS_STAGE_FALLBACKS[normalized] || PLAYBOOK_PROCESS_STAGE_FALLBACKS.info
  );
}

function getPlaybookKindLabel(kind) {
  const normalized = (kind || '').toString().toLowerCase();
  switch (normalized) {
    case 'query':
      return translate('playbook.kind.query', 'Request');
    case 'playbook':
      return translate('playbook.kind.applied', 'Applied');
    case 'error':
      return translate('playbook.kind.error', 'Error');
    case 'warning':
      return translate('playbook.kind.warning', 'Warning');
    default:
      return translate('playbook.kind.update', 'Update');
  }
}

function getPlaybookKindClass(kind) {
  const normalized = (kind || '').toString().toLowerCase();
  if (normalized === 'query') return 'kind--query';
  if (normalized === 'error') return 'kind--error';
  if (normalized === 'warning') return 'kind--warning';
  if (normalized === 'playbook') return 'kind--applied';
  return '';
}

function buildPlaybookMeta(entry) {
  if (!entry || typeof entry !== 'object') return [];
  const rows = [];
  const requestId = entry.request_id ? String(entry.request_id).trim() : '';
  if (requestId) {
    rows.push({ label: translate('playbook.meta.requestId', 'Request ID'), value: requestId });
  }
  const modeLabel = toTitleCase(entry.mode || '');
  const biasLabel = toTitleCase(entry.bias || '');
  if (modeLabel || biasLabel) {
    const modeValue = biasLabel ? `${modeLabel} (${biasLabel})` : modeLabel;
    rows.push({ label: translate('playbook.meta.mode', 'Mode'), value: modeValue });
  }
  if (entry.size_bias && typeof entry.size_bias === 'object') {
    const parts = normalizePlaybookSizeBiasEntries(entry.size_bias).map(
      (item) => `${item.label} ${formatPlaybookMultiplier(item.value)}`
    );
    if (parts.length > 0) {
      rows.push({
        label: translate('playbook.meta.sizeBias', 'Size bias'),
        value: parts.join(' · '),
      });
    }
  }
  if (Number.isFinite(Number(entry.sl_bias))) {
    rows.push({ label: translate('playbook.meta.sl', 'SL bias'), value: formatPlaybookMultiplier(entry.sl_bias) });
  }
  if (Number.isFinite(Number(entry.tp_bias))) {
    rows.push({ label: translate('playbook.meta.tp', 'TP bias'), value: formatPlaybookMultiplier(entry.tp_bias) });
  }
  if (Number.isFinite(Number(entry.confidence))) {
    rows.push({
      label: translate('playbook.meta.confidence', 'Confidence'),
      value: formatPlaybookPercent(entry.confidence, entry.confidence < 0.1 ? 1 : 0),
    });
  }
  if (Array.isArray(entry.features) && entry.features.length > 0) {
    const focusText = entry.features
      .slice(0, 3)
      .map((feature) => {
        const name = feature && typeof feature.name === 'string' ? feature.name : '';
        return `${name} ${formatPlaybookSigned(feature.value)}`.trim();
      })
      .join(' · ');
    if (focusText) {
      rows.push({ label: translate('playbook.meta.features', 'Focus'), value: focusText });
    }
  }
  if (entry.snapshot_summary) {
    rows.push({
      label: translate('playbook.meta.snapshot', 'Snapshot'),
      value: String(entry.snapshot_summary),
    });
  }
  if (entry.reason) {
    rows.push({ label: translate('playbook.meta.reason', 'Reason'), value: entry.reason });
  }
  if (entry.notes && (!entry.body || !entry.body.includes(entry.notes))) {
    rows.push({ label: translate('playbook.meta.notes', 'Notes'), value: entry.notes });
  }
  return rows;
}

function extractTimestampMs(entry, keys = []) {
  if (!entry || typeof entry !== 'object') return Number.NaN;
  for (const key of keys) {
    const isoKey = key.endsWith('_iso') ? key : `${key}_iso`;
    if (entry[key] !== undefined || entry[isoKey] !== undefined) {
      const resolved = resolveTimestampMs(entry[key], entry[isoKey]);
      if (Number.isFinite(resolved)) return resolved;
    }
    const rawValue = entry[key];
    if (typeof rawValue === 'string' && rawValue.trim()) {
      const parsed = Date.parse(rawValue);
      if (Number.isFinite(parsed)) return parsed;
    }
    const isoValue = entry[isoKey];
    if (typeof isoValue === 'string' && isoValue.trim()) {
      const parsedIso = Date.parse(isoValue);
      if (Number.isFinite(parsedIso)) return parsedIso;
    }
  }
  return Number.NaN;
}

function formatPlaybookCardTimestamp(entry, keys = []) {
  const timestampMs = extractTimestampMs(entry, keys);
  if (!Number.isFinite(timestampMs)) return null;
  const iso = new Date(timestampMs).toISOString();
  const label = formatTimestamp(iso);
  return {
    label: label && label !== '–' ? label : null,
    relative: formatRelativeTime(iso),
    iso,
  };
}

function composePlaybookName(source, fallback) {
  const primary = source && typeof source === 'object' ? source : {};
  const fallbackSource = fallback && typeof fallback === 'object' ? fallback : {};
  const modeText = toTitleCase(primary.mode || fallbackSource.mode || '');
  const biasText = toTitleCase(primary.bias || fallbackSource.bias || '');
  if (modeText && biasText) return `${modeText} (${biasText})`;
  if (modeText) return modeText;
  if (biasText) return biasText;
  return '';
}

function createPlaybookSummaryContent(state, { hint } = {}) {
  if (!state || typeof state !== 'object') return null;

  const fragment = document.createDocumentFragment();

  const header = document.createElement('div');
  header.className = 'playbook-summary-header';
  const activeLabel = document.createElement('span');
  activeLabel.textContent = translate('playbook.active', 'Active playbook:');
  header.append(activeLabel);
  const activeValue = document.createElement('strong');
  const modeText = toTitleCase(state.mode || 'baseline');
  const biasText = toTitleCase(state.bias || 'neutral');
  activeValue.textContent = biasText ? `${modeText} (${biasText})` : modeText;
  header.append(activeValue);
  const timestampInfo = formatPlaybookCardTimestamp(state, PLAYBOOK_CARD_TIMESTAMP_KEYS.summary);
  const refreshedValue = state.refreshed_ts || state.refreshed;
  if (timestampInfo?.relative) {
    const refreshed = document.createElement('span');
    refreshed.textContent = `${translate('playbook.refreshed', 'Refreshed')} ${timestampInfo.relative}`;
    if (timestampInfo.iso) {
      refreshed.title = timestampInfo.label || timestampInfo.iso;
    }
    header.append(refreshed);
  } else if (refreshedValue) {
    const refreshed = document.createElement('span');
    refreshed.textContent = `${translate('playbook.refreshed', 'Refreshed')} ${formatRelativeTime(refreshedValue)}`;
    header.append(refreshed);
  }
  fragment.append(header);

  const stats = [];
  if (Number.isFinite(Number(state.sl_bias))) {
    stats.push({ label: translate('playbook.sl', 'SL bias'), value: formatPlaybookMultiplier(state.sl_bias) });
  }
  if (Number.isFinite(Number(state.tp_bias))) {
    stats.push({ label: translate('playbook.tp', 'TP bias'), value: formatPlaybookMultiplier(state.tp_bias) });
  }
  if (Number.isFinite(Number(state.confidence))) {
    stats.push({
      label: translate('playbook.confidence', 'Confidence'),
      value: formatPlaybookPercent(state.confidence, state.confidence < 0.1 ? 1 : 0),
    });
  }

  if (stats.length > 0) {
    const grid = document.createElement('div');
    grid.className = 'playbook-summary-grid';
    stats.forEach((stat) => {
      const item = document.createElement('div');
      item.className = 'playbook-summary-item';
      const label = document.createElement('span');
      label.className = 'label';
      label.textContent = stat.label;
      const value = document.createElement('span');
      value.className = 'value';
      value.textContent = stat.value;
      item.append(label, value);
      grid.append(item);
    });
    fragment.append(grid);
  }

  const sizeEntries = normalizePlaybookSizeBiasEntries(state.size_bias);
  if (sizeEntries.length > 0) {
    const sizeSection = document.createElement('div');
    sizeSection.className = 'playbook-size-bias';
    const label = document.createElement('span');
    label.className = 'label';
    label.textContent = translate('playbook.sizeBias', 'Size bias');
    sizeSection.append(label);
    const values = document.createElement('div');
    values.className = 'playbook-size-bias-values';
    sizeEntries.forEach((entry) => {
      const chip = document.createElement('span');
      chip.textContent = `${entry.label} ${formatPlaybookMultiplier(entry.value)}`;
      values.append(chip);
    });
    sizeSection.append(values);
    fragment.append(sizeSection);
  }

  if (Array.isArray(state.features) && state.features.length > 0) {
    const featuresSection = document.createElement('div');
    featuresSection.className = 'playbook-features';
    const title = document.createElement('div');
    title.className = 'playbook-features-title';
    title.textContent = translate('playbook.features', 'Focus signals');
    featuresSection.append(title);
    const list = document.createElement('div');
    list.className = 'playbook-feature-list';
    state.features.forEach((feature) => {
      if (!feature) return;
      const chip = document.createElement('span');
      chip.className = 'playbook-feature';
      const name = feature && typeof feature.name === 'string' ? feature.name : '';
      chip.textContent = `${name} ${formatPlaybookSigned(feature.value)}`.trim();
      list.append(chip);
    });
    featuresSection.append(list);
    fragment.append(featuresSection);
  }

  const strategy = state.strategy && typeof state.strategy === 'object' ? state.strategy : null;
  if (strategy) {
    const strategySection = document.createElement('div');
    strategySection.className = 'playbook-strategy';

    const strategyTitle = document.createElement('h3');
    strategyTitle.className = 'playbook-strategy-title';
    strategyTitle.textContent = translate('playbook.strategy.title', 'Strategy in play');
    strategySection.append(strategyTitle);

    const strategyName = document.createElement('div');
    strategyName.className = 'playbook-strategy-name';
    strategyName.textContent = strategy.name || translate('playbook.strategy.untitled', 'Unnamed strategy');
    strategySection.append(strategyName);

    const metaContainer = document.createElement('div');
    metaContainer.className = 'playbook-strategy-meta';
    const addMetaRow = (labelText, valueText) => {
      if (!valueText || typeof valueText !== 'string' || !valueText.trim()) return;
      const row = document.createElement('div');
      row.className = 'playbook-strategy-meta-row';
      const labelEl = document.createElement('span');
      labelEl.className = 'label';
      labelEl.textContent = labelText;
      const valueEl = document.createElement('span');
      valueEl.className = 'value';
      valueEl.textContent = valueText.trim();
      row.append(labelEl, valueEl);
      metaContainer.append(row);
    };

    addMetaRow(
      translate('playbook.strategy.objective', 'Objective'),
      typeof strategy.objective === 'string' ? strategy.objective : null
    );
    const reasonText =
      (typeof state.reason === 'string' && state.reason.trim())
        ? state.reason
        : typeof strategy.why_active === 'string'
        ? strategy.why_active
        : null;
    addMetaRow(translate('playbook.strategy.reason', 'Why it is active'), reasonText);
    if (metaContainer.childElementCount > 0) {
      strategySection.append(metaContainer);
    }

    const normalizedSignals = Array.isArray(strategy.market_signals)
      ? strategy.market_signals.filter((item) => typeof item === 'string' && item.trim())
      : [];
    if (normalizedSignals.length > 0) {
      const signalsSection = document.createElement('div');
      signalsSection.className = 'playbook-strategy-section';
      const sectionTitle = document.createElement('div');
      sectionTitle.className = 'playbook-strategy-section-title';
      sectionTitle.textContent = translate('playbook.strategy.signals', 'Key market signals');
      signalsSection.append(sectionTitle);
      const list = document.createElement('ul');
      list.className = 'playbook-strategy-list';
      normalizedSignals.forEach((signal) => {
        const item = document.createElement('li');
        item.textContent = signal.trim();
        list.append(item);
      });
      signalsSection.append(list);
      strategySection.append(signalsSection);
    }

    const normalizedActions = Array.isArray(strategy.actions)
      ? strategy.actions.filter(
          (action) =>
            action &&
            typeof action === 'object' &&
            ((typeof action.title === 'string' && action.title.trim()) ||
              (typeof action.detail === 'string' && action.detail.trim()))
        )
      : [];
    if (normalizedActions.length > 0) {
      const actionsSection = document.createElement('div');
      actionsSection.className = 'playbook-strategy-section';
      const sectionTitle = document.createElement('div');
      sectionTitle.className = 'playbook-strategy-section-title';
      sectionTitle.textContent = translate('playbook.strategy.actions', 'Execution steps');
      actionsSection.append(sectionTitle);
      const list = document.createElement('ol');
      list.className = 'playbook-strategy-actions';
      normalizedActions.forEach((action) => {
        const item = document.createElement('li');
        item.className = 'playbook-strategy-action';
        if (typeof action.title === 'string' && action.title.trim()) {
          const titleEl = document.createElement('span');
          titleEl.className = 'playbook-strategy-action-title';
          titleEl.textContent = action.title.trim();
          item.append(titleEl);
        }
        if (typeof action.detail === 'string' && action.detail.trim()) {
          const detailEl = document.createElement('p');
          detailEl.className = 'playbook-strategy-action-detail';
          detailEl.textContent = action.detail.trim();
          item.append(detailEl);
        }
        if (typeof action.trigger === 'string' && action.trigger.trim()) {
          const triggerEl = document.createElement('div');
          triggerEl.className = 'playbook-strategy-action-trigger';
          triggerEl.textContent = `${translate('playbook.strategy.trigger', 'Trigger')}: ${action.trigger.trim()}`;
          item.append(triggerEl);
        }
        list.append(item);
      });
      actionsSection.append(list);
      strategySection.append(actionsSection);
    }

    const normalizedRisk = Array.isArray(strategy.risk_controls)
      ? strategy.risk_controls.filter((item) => typeof item === 'string' && item.trim())
      : [];
    if (normalizedRisk.length > 0) {
      const riskSection = document.createElement('div');
      riskSection.className = 'playbook-strategy-section';
      const sectionTitle = document.createElement('div');
      sectionTitle.className = 'playbook-strategy-section-title';
      sectionTitle.textContent = translate('playbook.strategy.risk', 'Risk controls');
      riskSection.append(sectionTitle);
      const list = document.createElement('ul');
      list.className = 'playbook-strategy-list';
      normalizedRisk.forEach((itemText) => {
        const item = document.createElement('li');
        item.textContent = itemText.trim();
        list.append(item);
      });
      riskSection.append(list);
      strategySection.append(riskSection);
    }

    fragment.append(strategySection);
  }

  if (state.notes) {
    const notes = document.createElement('p');
    notes.className = 'playbook-notes';
    notes.textContent = state.notes;
    fragment.append(notes);
  }

  if (hint) {
    fragment.append(hint);
  }

  return fragment;
}

function renderPlaybookOverview(playbook, activity, process, marketOverview) {
  lastPlaybookState = playbook && typeof playbook === 'object' ? { ...playbook } : null;
  lastPlaybookActivity = Array.isArray(activity) ? activity.slice() : [];
  lastPlaybookProcess = Array.isArray(process) ? process.slice() : [];
  lastPlaybookMarketOverview =
    marketOverview && typeof marketOverview === 'object' ? { ...marketOverview } : null;
  renderPlaybookSummarySection();
  renderPlaybookRequestList();
  renderPlaybookRiskIndicator();
  updatePlaybookPendingState();
}

function renderPlaybookSummarySection() {
  if (!playbookSummaryContainer) return;
  const hintNode = aiHint && playbookSummaryContainer.contains(aiHint) ? aiHint : null;
  const fragment = document.createDocumentFragment();

  if (!aiMode) {
    const disabled = document.createElement('p');
    disabled.className = 'playbook-empty';
    disabled.textContent = translate('playbook.disabled', 'Enable AI mode to view the playbook overview.');
    fragment.append(disabled);
    if (hintNode) fragment.append(hintNode);
    playbookSummaryContainer.replaceChildren(fragment);
    return;
  }

  if (!lastPlaybookState) {
    const empty = document.createElement('p');
    empty.className = 'playbook-empty';
    empty.textContent = translate('playbook.empty', 'No playbook has been applied yet.');
    fragment.append(empty);
    if (hintNode) fragment.append(hintNode);
    playbookSummaryContainer.replaceChildren(fragment);
    return;
  }
  const summaryContent = createPlaybookSummaryContent(lastPlaybookState, { hint: hintNode });
  if (summaryContent) {
    fragment.append(summaryContent);
  }
  playbookSummaryContainer.replaceChildren(fragment);
}

function renderPlaybookRequestList() {
  if (!playbookRequestList) return;
  const fragment = document.createDocumentFragment();

  if (!aiMode) {
    const disabled = document.createElement('p');
    disabled.className = 'playbook-request-empty';
    disabled.textContent = translate('playbook.disabled', 'Enable AI mode to view the playbook overview.');
    fragment.append(disabled);
    playbookRequestList.replaceChildren(fragment);
    return;
  }

  const entries = Array.isArray(lastPlaybookProcess) ? lastPlaybookProcess.slice() : [];
  if (!entries.length) {
    const empty = document.createElement('p');
    empty.className = 'playbook-request-empty';
    empty.textContent = translate('playbook.process.empty', 'No refresh activity recorded yet.');
    fragment.append(empty);
    playbookRequestList.replaceChildren(fragment);
    return;
  }

  entries.forEach((entry) => {
    const card = buildPlaybookRequestCard(entry);
    if (card) {
      fragment.append(card);
    }
  });
  playbookRequestList.replaceChildren(fragment);
}

function describeEventRisk(value) {
  const numeric = clampValue(Number(value) || 0, 0, 1);
  for (const band of EVENT_RISK_SEVERITY_BANDS) {
    if (numeric >= band.min) {
      return {
        level: band.key,
        label: translate(`playbook.risk.level.${band.key}`, band.fallback),
        value: numeric,
      };
    }
  }
  const fallback = EVENT_RISK_SEVERITY_BANDS[EVENT_RISK_SEVERITY_BANDS.length - 1];
  return {
    level: fallback.key,
    label: translate(`playbook.risk.level.${fallback.key}`, fallback.fallback),
    value: numeric,
  };
}

function renderPlaybookRiskIndicator() {
  if (!playbookRiskIndicator) return;

  const indicator = playbookRiskIndicator;
  const valueNode = playbookRiskValue;
  const statusNode = playbookRiskStatus;

  const resetFill = () => {
    if (!playbookRiskFill) return;
    playbookRiskFill.style.width = '12%';
    playbookRiskFill.style.background = '';
    playbookRiskFill.style.boxShadow = '';
  };

  if (!aiMode) {
    indicator.dataset.state = 'disabled';
    indicator.removeAttribute('data-level');
    if (valueNode) valueNode.textContent = '–';
    if (statusNode) {
      statusNode.textContent = translate('playbook.risk.disabled', 'Enable AI mode to see event risk');
    }
    resetFill();
    indicator.setAttribute(
      'aria-label',
      translate('playbook.risk.aria.disabled', 'Global event risk indicator is disabled while AI mode is off.'),
    );
    return;
  }

  const sentinelOverview =
    lastPlaybookMarketOverview && typeof lastPlaybookMarketOverview === 'object'
      ? lastPlaybookMarketOverview.sentinel || null
      : null;
  const avgRiskRaw =
    sentinelOverview && typeof sentinelOverview === 'object'
      ? Number(sentinelOverview.avg_event_risk)
      : Number.NaN;

  if (!Number.isFinite(avgRiskRaw)) {
    indicator.dataset.state = 'pending';
    indicator.removeAttribute('data-level');
    if (valueNode) valueNode.textContent = '–';
    if (statusNode) {
      statusNode.textContent = translate('playbook.risk.pending', 'Waiting for telemetry…');
    }
    resetFill();
    indicator.setAttribute(
      'aria-label',
      translate('playbook.risk.aria.pending', 'Waiting for global event risk telemetry'),
    );
    return;
  }

  const clamped = clampValue(avgRiskRaw, 0, 1);
  const severity = describeEventRisk(clamped);
  const digits = clamped >= 0.1 ? 0 : 1;
  const displayValue = `${(clamped * 100).toFixed(digits)}%`;

  indicator.dataset.state = 'ready';
  indicator.dataset.level = severity.level;
  if (valueNode) valueNode.textContent = displayValue;
  if (statusNode) statusNode.textContent = severity.label;

  const hue = Math.round((1 - clamped) * 120);
  const saturation = 84;
  const lightness = clamped > 0.65 ? 56 : 52;
  const color = `hsl(${hue}, ${saturation}%, ${lightness}%)`;
  if (playbookRiskFill) {
    playbookRiskFill.style.width = `${Math.max(6, clamped * 100)}%`;
    playbookRiskFill.style.background = color;
    playbookRiskFill.style.boxShadow = `0 0 22px hsla(${hue}, ${saturation}%, ${lightness}%, 0.45)`;
  }

  indicator.setAttribute(
    'aria-label',
    translate('playbook.risk.aria.value', 'Global event risk {{value}} ({{status}})', {
      value: displayValue,
      status: severity.label,
    }),
  );
}

function buildPlaybookRequestCard(entry) {
  if (!entry || typeof entry !== 'object') return null;

  const statusKey = (entry.status || 'pending').toString().toLowerCase();
  const statusLabel = getPlaybookProcessStatusLabel(statusKey);
  const playbookLabel = composePlaybookName(entry, lastPlaybookState);
  const timestampInfo = formatPlaybookCardTimestamp(entry, PLAYBOOK_CARD_TIMESTAMP_KEYS.process);

  const card = document.createElement('button');
  card.type = 'button';
  card.className = 'playbook-request-card';
  card.dataset.status = statusKey;

  const header = document.createElement('div');
  header.className = 'playbook-request-card__header';

  const title = document.createElement('div');
  title.className = 'playbook-request-card__title';
  const name = document.createElement('span');
  name.className = 'playbook-request-card__name';
  name.textContent = playbookLabel || translate('playbook.card.playbookFallback', 'Playbook not selected');
  title.append(name);
  if (entry.request_id) {
    const id = document.createElement('span');
    id.className = 'playbook-request-card__id';
    id.textContent = `#${entry.request_id}`;
    title.append(id);
  }
  header.append(title);

  if (statusLabel) {
    const statusEl = document.createElement('span');
    statusEl.className = `playbook-process-status status-${statusKey} playbook-request-card__status`;
    statusEl.textContent = statusLabel;
    header.append(statusEl);
  }

  card.append(header);

  const meta = document.createElement('div');
  meta.className = 'playbook-request-card__meta';
  if (timestampInfo?.label) {
    const timeSpan = document.createElement('span');
    timeSpan.textContent = timestampInfo.label;
    if (timestampInfo.relative) {
      timeSpan.title = timestampInfo.relative;
    }
    meta.append(timeSpan);
  }
  const relativeText = formatRelativeTime(entry.completed_ts || entry.failed_ts || entry.requested_ts);
  if (relativeText && relativeText !== timestampInfo?.relative) {
    const relativeSpan = document.createElement('span');
    relativeSpan.textContent = relativeText;
    meta.append(relativeSpan);
  }
  if (entry.snapshot_summary) {
    const snapshotSpan = document.createElement('span');
    snapshotSpan.textContent = entry.snapshot_summary;
    meta.append(snapshotSpan);
  }
  if (meta.children.length > 0) {
    card.append(meta);
  }

  const chips = [];
  if (Number.isFinite(Number(entry.sl_bias))) {
    chips.push(`${translate('playbook.sl', 'SL bias')}: ${formatPlaybookMultiplier(entry.sl_bias)}`);
  }
  if (Number.isFinite(Number(entry.tp_bias))) {
    chips.push(`${translate('playbook.tp', 'TP bias')}: ${formatPlaybookMultiplier(entry.tp_bias)}`);
  }
  if (Number.isFinite(Number(entry.confidence))) {
    chips.push(`${translate('playbook.confidence', 'Confidence')} ${formatPlaybookPercent(entry.confidence)}`);
  }
  const sizePreview = normalizePlaybookSizeBiasEntries(entry.size_bias).slice(0, 2);
  sizePreview.forEach((item) => {
    chips.push(`${item.label} ${formatPlaybookMultiplier(item.value)}`);
  });
  if (chips.length > 0) {
    const chipList = document.createElement('div');
    chipList.className = 'playbook-request-card__chips';
    chips.forEach((text) => {
      const chip = document.createElement('span');
      chip.textContent = text;
      chipList.append(chip);
    });
    card.append(chipList);
  }

  const noteTextCandidates = [entry.snapshot_summary, entry.reason, entry.notes].filter(
    (value) => typeof value === 'string' && value.trim()
  );
  if (noteTextCandidates.length > 0) {
    const note = document.createElement('p');
    note.className = 'playbook-request-card__note';
    const preview = noteTextCandidates[0].trim();
    note.textContent = preview.length > 200 ? `${preview.slice(0, 197).trimEnd()}…` : preview;
    card.append(note);
  }

  const actions = document.createElement('div');
  actions.className = 'playbook-request-card__actions';
  const hint = document.createElement('span');
  hint.className = 'playbook-request-card__hint';
  hint.textContent = translate('trades.viewDetails', 'View details');
  actions.append(hint);
  card.append(actions);

  const accessibleParts = [];
  if (statusLabel) accessibleParts.push(statusLabel);
  if (timestampInfo?.label) accessibleParts.push(timestampInfo.label);
  if (noteTextCandidates[0]) accessibleParts.push(noteTextCandidates[0].trim());
  const accessibleSuffix = accessibleParts.length > 0 ? ` (${accessibleParts.join(' · ')})` : '';
  card.setAttribute(
    'aria-label',
    `${translate('playbook.modal.title', 'Playbook details')}: ${name.textContent}${accessibleSuffix}`
  );

  card.addEventListener('click', () => openPlaybookModal(entry, card));

  return card;
}

function collectPlaybookActivityForRequest(entry) {
  const requestId = entry && entry.request_id ? entry.request_id.toString().trim() : '';
  if (!requestId) return [];
  return lastPlaybookActivity
    .filter((item) => {
      if (!item || typeof item !== 'object') return false;
      const candidateId = item.request_id === undefined ? '' : String(item.request_id).trim();
      return candidateId === requestId;
    })
    .sort((a, b) => getPlaybookActivityTimestampMs(a) - getPlaybookActivityTimestampMs(b));
}

function buildPlaybookRequestDetailContent(entry) {
  const container = document.createElement('div');
  container.className = 'playbook-modal-content';

  const summaryState = {
    ...(lastPlaybookState && typeof lastPlaybookState === 'object' ? lastPlaybookState : {}),
    ...(entry && typeof entry === 'object' ? entry : {}),
  };
  const summaryContent = createPlaybookSummaryContent(summaryState);
  if (summaryContent && summaryContent.childNodes.length > 0) {
    const section = document.createElement('section');
    section.className = 'playbook-modal-section';
    const header = document.createElement('div');
    header.className = 'playbook-modal-section__header';
    const title = document.createElement('h3');
    title.className = 'playbook-modal-section__title';
    title.textContent = translate('playbook.summary.title', 'Active regime snapshot');
    header.append(title);
    const subtitle = document.createElement('p');
    subtitle.className = 'playbook-modal-section__subtitle';
    subtitle.textContent = translate(
      'playbook.summary.subtitle',
      'Bias multipliers, focus signals, and the current strategy in play.'
    );
    header.append(subtitle);
    section.append(header);
    const body = document.createElement('div');
    body.className = 'playbook-modal-section__body';
    body.append(summaryContent);
    section.append(body);
    container.append(section);
  }

  const processItem = createPlaybookProcessItem(entry);
  if (processItem) {
    const section = document.createElement('section');
    section.className = 'playbook-modal-section';
    const header = document.createElement('div');
    header.className = 'playbook-modal-section__header';
    const title = document.createElement('h3');
    title.className = 'playbook-modal-section__title';
    title.textContent = translate('playbook.process.title', 'Playbook refresh timeline');
    header.append(title);
    const subtitle = document.createElement('p');
    subtitle.className = 'playbook-modal-section__subtitle';
    subtitle.textContent = translate(
      'playbook.process.subtitle',
      'Follow each stage in the refresh pipeline — from the initial request to the final applied update.'
    );
    header.append(subtitle);
    section.append(header);
    const body = document.createElement('div');
    body.className = 'playbook-modal-section__body';
    body.append(processItem);
    section.append(body);
    container.append(section);
  }

  const relatedActivity = collectPlaybookActivityForRequest(entry);
  const activitySection = document.createElement('section');
  activitySection.className = 'playbook-modal-section';
  const activityHeader = document.createElement('div');
  activityHeader.className = 'playbook-modal-section__header';
  const activityTitle = document.createElement('h3');
  activityTitle.className = 'playbook-modal-section__title';
  activityTitle.textContent = translate('playbook.activity.title', 'Playbook communications');
  activityHeader.append(activityTitle);
  const activitySubtitle = document.createElement('p');
  activitySubtitle.className = 'playbook-modal-section__subtitle';
  activitySubtitle.textContent = translate(
    'playbook.activity.subtitle',
    'Requests, updates, and diagnostics between the bot and the AI.'
  );
  activityHeader.append(activitySubtitle);
  activitySection.append(activityHeader);
  const activityBody = document.createElement('div');
  activityBody.className = 'playbook-modal-section__body';
  const activityList = document.createElement('div');
  activityList.className = 'playbook-modal-activity-list';
  if (relatedActivity.length > 0) {
    relatedActivity.forEach((item) => {
      const node = createPlaybookActivityItem(item);
      if (node) {
        activityList.append(node);
      }
    });
  } else {
    const empty = document.createElement('p');
    empty.className = 'playbook-modal-activity-empty';
    empty.textContent = translate('playbook.activity.empty', 'No playbook communications recorded yet.');
    activityList.append(empty);
  }
  activityBody.append(activityList);
  activitySection.append(activityBody);
  container.append(activitySection);

  return container;
}

function openPlaybookModal(entry, returnTarget) {
  if (!playbookModal || !playbookModalBody) return;

  const safe = entry && typeof entry === 'object' ? entry : {};
  const statusKey = (safe.status || 'pending').toString().toLowerCase();
  const statusLabel = getPlaybookProcessStatusLabel(statusKey);
  const playbookLabel = composePlaybookName(safe, lastPlaybookState);
  const timestampInfo = formatPlaybookCardTimestamp(safe, PLAYBOOK_CARD_TIMESTAMP_KEYS.process);

  if (playbookModalTitle) {
    playbookModalTitle.textContent = playbookLabel || translate('playbook.modal.title', 'Playbook details');
  }
  if (playbookModalSubtitle) {
    const subtitleParts = [];
    if (statusLabel) subtitleParts.push(statusLabel);
    if (timestampInfo?.label) subtitleParts.push(timestampInfo.label);
    if (safe.request_id) subtitleParts.push(`#${safe.request_id}`);
    playbookModalSubtitle.textContent =
      subtitleParts.length > 0
        ? subtitleParts.join(' · ')
        : translate('playbook.modal.subtitleFallback', 'No additional metadata available.');
  }

  const active =
    returnTarget instanceof HTMLElement
      ? returnTarget
      : document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
  playbookModalReturnTarget = active && active !== document.body ? active : null;

  if (playbookModalHideTimer) {
    clearTimeout(playbookModalHideTimer);
    playbookModalHideTimer = null;
  }
  if (playbookModalFinalizeHandler) {
    playbookModal.removeEventListener('transitionend', playbookModalFinalizeHandler);
    playbookModalFinalizeHandler = null;
  }

  playbookModalBody.innerHTML = '';
  const content = buildPlaybookRequestDetailContent(safe);
  if (content) {
    playbookModalBody.append(content);
  }
  playbookModalBody.scrollTop = 0;

  playbookModal.removeAttribute('hidden');
  playbookModal.removeAttribute('aria-hidden');
  requestAnimationFrame(() => {
    playbookModal.classList.add('is-active');
  });
  document.body.classList.add('modal-open');

  document.addEventListener('keydown', handlePlaybookModalKeydown);
  if (playbookModalClose) {
    setTimeout(() => playbookModalClose.focus(), 120);
  }
}

function closePlaybookModal() {
  if (!playbookModal) return;

  if (playbookModalHideTimer) {
    clearTimeout(playbookModalHideTimer);
    playbookModalHideTimer = null;
  }
  if (playbookModalFinalizeHandler) {
    playbookModal.removeEventListener('transitionend', playbookModalFinalizeHandler);
    playbookModalFinalizeHandler = null;
  }
  if (playbookModal.hasAttribute('hidden')) {
    return;
  }

  playbookModal.classList.remove('is-active');
  playbookModal.setAttribute('aria-hidden', 'true');
  document.body.classList.remove('modal-open');

  const finalize = () => {
    if (playbookModalHideTimer) {
      clearTimeout(playbookModalHideTimer);
      playbookModalHideTimer = null;
    }
    if (!playbookModal.hasAttribute('hidden')) {
      playbookModal.setAttribute('hidden', '');
    }
    if (playbookModalFinalizeHandler) {
      playbookModal.removeEventListener('transitionend', playbookModalFinalizeHandler);
      playbookModalFinalizeHandler = null;
    }
    const restoreTarget =
      playbookModalReturnTarget && typeof playbookModalReturnTarget.focus === 'function'
        ? playbookModalReturnTarget
        : null;
    playbookModalReturnTarget = null;
    if (restoreTarget) {
      restoreTarget.focus({ preventScroll: true });
    }
  };

  playbookModalFinalizeHandler = finalize;
  playbookModal.addEventListener('transitionend', finalize);
  playbookModalHideTimer = setTimeout(finalize, 280);

  document.removeEventListener('keydown', handlePlaybookModalKeydown);
}

function handlePlaybookModalKeydown(event) {
  if (event.key === 'Escape') {
    closePlaybookModal();
  }
}

function resolveTimestampMs(epochValue, isoValue) {
  if (epochValue !== undefined && epochValue !== null) {
    const numeric = Number(epochValue);
    if (Number.isFinite(numeric)) {
      return numeric > 1e12 ? numeric : numeric * 1000;
    }
  }
  if (isoValue) {
    const parsed = Date.parse(isoValue);
    if (Number.isFinite(parsed)) return parsed;
  }
  return null;
}

function createPlaybookProcessItem(entry) {
  if (!entry || typeof entry !== 'object') return null;

  const wrapper = document.createElement('article');
  wrapper.className = 'playbook-process-item';

  const header = document.createElement('div');
  header.className = 'playbook-process-item-header';

  const statusKey = (entry.status || 'pending').toString().toLowerCase();
  const status = document.createElement('span');
  status.className = `playbook-process-status status-${statusKey}`;
  status.textContent = getPlaybookProcessStatusLabel(statusKey);
  header.append(status);

  const headline = document.createElement('span');
  headline.className = 'playbook-process-headline';
  const modeText = toTitleCase(entry.mode || '');
  const biasText = toTitleCase(entry.bias || '');
  if (modeText && biasText) {
    headline.textContent = `${modeText} (${biasText})`;
  } else if (modeText) {
    headline.textContent = modeText;
  } else if (biasText) {
    headline.textContent = biasText;
  } else {
    headline.textContent = translate('playbook.process.untitled', 'Playbook update');
  }
  header.append(headline);

  const metaParts = [];
  const referenceTs = entry.completed_ts || entry.failed_ts || entry.requested_ts;
  const timeText = formatRelativeTime(referenceTs);
  if (timeText) metaParts.push(timeText);
  if (entry.request_id) metaParts.push(`#${entry.request_id}`);
  if (entry.snapshot_summary) metaParts.push(entry.snapshot_summary);
  if (metaParts.length > 0) {
    const meta = document.createElement('span');
    meta.className = 'playbook-process-meta';
    meta.textContent = metaParts.join(' · ');
    header.append(meta);
  }

  wrapper.append(header);

  const referenceIso = entry.completed_ts_iso || entry.failed_ts_iso || entry.requested_ts_iso;
  const referenceTimestampMs =
    resolveTimestampMs(entry.completed_ts, entry.completed_ts_iso) ||
    resolveTimestampMs(entry.failed_ts, entry.failed_ts_iso) ||
    resolveTimestampMs(entry.requested_ts, referenceIso);

  const stepEntries = Array.isArray(entry.steps)
    ? entry.steps
        .map((step) => (step && typeof step === 'object' ? { ...step } : null))
        .filter(Boolean)
    : [];
  if (entry.notes) {
    stepEntries.push({
      stage: 'info',
      headline: translate('playbook.process.notes', 'Notes'),
      body: entry.notes,
      ts_epoch: entry.completed_ts || entry.failed_ts || entry.requested_ts,
      ts: referenceIso,
    });
  }

  if (stepEntries.length > 0) {
    const decoratedSteps = stepEntries
      .map((step, index) => {
        const tsMs = resolveTimestampMs(step.ts_epoch, step.ts) || referenceTimestampMs;
        return { step, index, tsMs };
      })
      .sort((a, b) => {
        const aHasTs = Number.isFinite(a.tsMs);
        const bHasTs = Number.isFinite(b.tsMs);
        if (aHasTs && bHasTs) return a.tsMs - b.tsMs;
        if (aHasTs) return -1;
        if (bHasTs) return 1;
        return a.index - b.index;
      })
      .map((entry) => entry.step);

    const list = document.createElement('ol');
    list.className = 'playbook-process-steps';

    decoratedSteps.forEach((step, position) => {
      if (!step || typeof step !== 'object') return;

      const item = document.createElement('li');
      item.className = 'playbook-process-step';

      const label = document.createElement('div');
      label.className = 'playbook-process-step-label';

      const stepPrefix = translate('playbook.process.stepLabel', 'Step');
      const number = document.createElement('span');
      number.className = 'playbook-process-step-number';
      number.textContent = `${stepPrefix} ${position + 1}`;
      label.append(number);

      const stage = document.createElement('span');
      stage.className = 'playbook-process-step-stage';
      stage.textContent = getPlaybookProcessStageLabel(step.stage);
      label.append(stage);

      item.append(label);

      const body = document.createElement('div');
      body.className = 'playbook-process-step-body';

      const headlineText = typeof step.headline === 'string' ? step.headline.trim() : '';
      const summaryText = typeof step.snapshot_summary === 'string' ? step.snapshot_summary.trim() : '';
      const bodyText = typeof step.body === 'string' ? step.body.trim() : '';

      const detailLines = [];
      if (headlineText) detailLines.push({ className: 'playbook-process-step-headline', text: headlineText });
      if (summaryText && summaryText !== headlineText)
        detailLines.push({ className: 'playbook-process-step-summary', text: summaryText });
      if (bodyText && bodyText !== headlineText && bodyText !== summaryText)
        detailLines.push({ className: 'playbook-process-step-description', text: bodyText });

      if (detailLines.length === 0) {
        detailLines.push({
          className: 'playbook-process-step-description',
          text: translate('playbook.process.step.noDetails', 'No additional context provided.'),
        });
      }

      detailLines.forEach((line) => {
        const lineEl = document.createElement('p');
        lineEl.className = `playbook-process-step-text ${line.className}`.trim();
        lineEl.textContent = line.text;
        body.append(lineEl);
      });

      const metaRow = document.createElement('div');
      metaRow.className = 'playbook-process-step-meta';

      const kindValue = typeof step.kind === 'string' ? step.kind.trim() : '';
      if (kindValue) {
        const kindLabel = getPlaybookKindLabel(kindValue);
        const kindChip = document.createElement('span');
        kindChip.className = 'playbook-process-step-kind';
        kindChip.textContent = kindLabel;
        metaRow.append(kindChip);
      }

      const tsMs = resolveTimestampMs(step.ts_epoch, step.ts) || referenceTimestampMs;
      const timeText = formatRelativeTime(step.ts_epoch || step.ts || referenceTs);
      if (timeText) {
        const timeEl = document.createElement('time');
        timeEl.className = 'playbook-process-step-time';
        timeEl.textContent = timeText;
        if (Number.isFinite(tsMs)) {
          timeEl.dateTime = new Date(tsMs).toISOString();
        }
        metaRow.append(timeEl);
      }

      if (metaRow.childElementCount > 0) {
        body.append(metaRow);
      }

      item.append(body);
      list.append(item);
    });

    wrapper.append(list);
  }

  return wrapper;
}

function getPlaybookActivityToneKey(entry) {
  if (!entry || typeof entry !== 'object') return '';
  const candidates = [entry.reason, entry.headline, entry.notes, entry.kind, entry.mode];
  for (const value of candidates) {
    if (typeof value !== 'string') continue;
    const cleaned = value.trim();
    if (cleaned) {
      return cleaned.toLowerCase();
    }
  }
  return '';
}

function classifyPlaybookActivityImportance(entry) {
  const toneSource = getPlaybookActivityToneKey(entry);
  if (!toneSource) return 'balanced';
  const mutedKeywords = [
    'skip',
    'skipped',
    'ignored',
    'noop',
    'no trade',
    'cooldown',
    'waiting',
    'paused',
    'dismissed',
  ];
  if (mutedKeywords.some((term) => toneSource.includes(term))) {
    return 'muted';
  }
  const brightKeywords = [
    'filled',
    'executed',
    'update',
    'updated',
    'applied',
    'orderbook',
    'playbook',
    'trade',
    'entry',
    'exit',
    'filled',
    'triggered',
  ];
  if (brightKeywords.some((term) => toneSource.includes(term))) {
    return 'bright';
  }
  if (entry && typeof entry === 'object') {
    const kind = (entry.kind || '').toString().toLowerCase();
    if (kind.includes('playbook') || kind.includes('orderbook') || kind.includes('trade')) {
      return 'bright';
    }
    if (kind.includes('query') || kind.includes('warning')) {
      return 'muted';
    }
  }
  return 'balanced';
}

function hashPlaybookActivityKey(key) {
  let hash = 0;
  if (!key) return hash;
  for (let index = 0; index < key.length; index += 1) {
    hash = (hash << 5) - hash + key.charCodeAt(index);
    hash |= 0;
  }
  return Math.abs(hash);
}

function buildPlaybookActivityPalette(entry) {
  const toneKey = getPlaybookActivityToneKey(entry) || 'default';
  const importance = classifyPlaybookActivityImportance(entry);
  const hash = hashPlaybookActivityKey(toneKey);
  const huePrimary = hash % 360;
  const hueOffset = 24 + ((hash >> 5) % 96);
  const hueSecondary = (huePrimary + hueOffset) % 360;
  const tonePresets = {
    bright: { saturation: 72, lightness: 52 },
    balanced: { saturation: 60, lightness: 44 },
    muted: { saturation: 42, lightness: 30 },
  };
  const preset = tonePresets[importance] || tonePresets.balanced;
  const saturation = preset.saturation;
  const lightness = preset.lightness;
  const lightnessSecondary = Math.min(lightness + 10, 70);
  const gradient = `linear-gradient(135deg, hsla(${huePrimary}, ${saturation}%, ${lightness}%, 0.82), hsla(${hueSecondary}, ${saturation + 6}%, ${lightnessSecondary}%, 0.88))`;
  const border = `hsla(${huePrimary}, ${Math.max(28, saturation - 14)}%, ${Math.max(12, lightness - 18)}%, 0.72)`;
  const glow = `hsla(${hueSecondary}, ${saturation + 10}%, ${Math.min(84, lightnessSecondary + 14)}%, 0.6)`;
  const chipBg = `hsla(${huePrimary}, ${saturation}%, ${Math.min(78, lightnessSecondary + 12)}%, 0.35)`;
  const chipBorder = `hsla(${huePrimary}, ${saturation}%, ${Math.max(24, lightness - 10)}%, 0.65)`;
  const chipText = importance === 'muted'
    ? `hsla(${hueSecondary}, ${Math.min(56, saturation)}%, ${Math.min(88, lightnessSecondary + 18)}%, 0.92)`
    : `hsla(${hueSecondary}, ${Math.min(78, saturation + 12)}%, ${Math.min(90, lightnessSecondary + 24)}%, 0.98)`;
  return {
    gradient,
    border,
    glow,
    chipBg,
    chipBorder,
    chipText,
    toneClass: `tone--${importance}`,
  };
}

function applyPlaybookActivityPalette(element, entry) {
  if (!(element instanceof HTMLElement)) return;
  const palette = buildPlaybookActivityPalette(entry);
  if (!palette) return;
  element.style.setProperty('--activity-gradient', palette.gradient);
  element.style.setProperty('--activity-border', palette.border);
  element.style.setProperty('--activity-glow', palette.glow);
  element.style.setProperty('--activity-chip-bg', palette.chipBg);
  element.style.setProperty('--activity-chip-border', palette.chipBorder);
  element.style.setProperty('--activity-chip-text', palette.chipText);
  element.classList.add(palette.toneClass);
}

function createPlaybookActivityItem(entry) {
  if (!entry || typeof entry !== 'object') return null;
  const wrapper = document.createElement('article');
  wrapper.className = 'playbook-activity-item';
  applyPlaybookActivityPalette(wrapper, entry);

  const headerRow = document.createElement('div');
  headerRow.className = 'playbook-activity-header-row';
  const titleWrap = document.createElement('div');
  titleWrap.className = 'playbook-activity-title-wrap';
  const kindEl = document.createElement('span');
  const kindClass = getPlaybookKindClass(entry.kind);
  kindEl.className = ['playbook-activity-kind', kindClass].filter(Boolean).join(' ');
  kindEl.textContent = getPlaybookKindLabel(entry.kind);
  titleWrap.append(kindEl);
  const title = document.createElement('h4');
  title.className = 'playbook-activity-title';
  title.textContent = entry.headline || getPlaybookKindLabel(entry.kind);
  titleWrap.append(title);
  headerRow.append(titleWrap);
  const time = document.createElement('time');
  time.className = 'playbook-activity-time';
  const timestampMs = getPlaybookActivityTimestampMs(entry);
  if (Number.isFinite(timestampMs) && timestampMs > Number.NEGATIVE_INFINITY) {
    const iso = new Date(timestampMs).toISOString();
    const timestampLabel = formatTimestamp(iso);
    if (timestampLabel && timestampLabel !== '–') {
      time.textContent = timestampLabel;
      time.dateTime = iso;
      time.title = formatRelativeTime(timestampMs / 1000);
      headerRow.append(time);
    }
  }
  wrapper.append(headerRow);

  const body = document.createElement('div');
  body.className = 'playbook-activity-body';
  const detailLines = [];
  const bodyText = typeof entry.body === 'string' ? entry.body.trim() : '';
  if (bodyText) {
    bodyText
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter((line) => line.length > 0)
      .forEach((line) => detailLines.push(line));
  }
  const noteText = typeof entry.notes === 'string' ? entry.notes.trim() : '';
  if (noteText && !detailLines.includes(noteText)) {
    detailLines.push(noteText);
  }
  detailLines.forEach((line) => {
    const paragraph = document.createElement('p');
    paragraph.textContent = line;
    body.append(paragraph);
  });

  const metaItems = buildPlaybookMeta(entry);
  if (metaItems.length > 0) {
    const metaList = document.createElement('ul');
    metaList.className = 'playbook-activity-meta';
    metaItems.forEach((item) => {
      const li = document.createElement('li');
      const label = document.createElement('span');
      label.className = 'label';
      label.textContent = item.label;
      const value = document.createElement('span');
      value.className = 'value';
      value.textContent = item.value;
      li.append(label, value);
      metaList.append(li);
    });
    body.append(metaList);
  }

  if (body.childElementCount > 0) {
    wrapper.append(body);
  }
  return wrapper;
}

function updatePlaybookPendingState() {
  if (!aiMode) {
    pendingPlaybookResponseCount = 0;
    return;
  }
  const pendingIds = new Set();
  for (const entry of lastPlaybookActivity) {
    if (!entry || typeof entry !== 'object') continue;
    const rawId = entry.request_id;
    const requestId = rawId === undefined || rawId === null ? '' : String(rawId).trim();
    if (!requestId) continue;
    const kind = (entry.kind || '').toString().toLowerCase();
    if (kind === 'query') {
      pendingIds.add(requestId);
    } else if (pendingIds.has(requestId)) {
      pendingIds.delete(requestId);
    }
  }
  const awaitingResponses = pendingIds.size;
  if (awaitingResponses > 0) {
    const changed = pendingPlaybookResponseCount !== awaitingResponses;
    pendingPlaybookResponseCount = awaitingResponses;
    const delay = awaitingResponses > 2 ? 900 : 600;
    if (changed || !tradesRefreshTimer) {
      scheduleTradesRefresh(delay);
    }
  } else if (pendingPlaybookResponseCount !== 0) {
    pendingPlaybookResponseCount = 0;
  }
}

const AI_REQUEST_STATUS_FALLBACKS = {
  pending: 'Awaiting response',
  responded: 'Response received',
  accepted: 'Entry approved',
  rejected: 'Entry rejected',
  analysed: 'Analysis complete',
  decided: 'Decision logged',
};

function getAiRequestStatusLabel(statusKey) {
  const normalized = (statusKey || 'pending').toString().toLowerCase();
  return translate(
    `ai.requests.status.${normalized}`,
    AI_REQUEST_STATUS_FALLBACKS[normalized] || AI_REQUEST_STATUS_FALLBACKS.pending
  );
}

function collectAiRequestDetailData(item) {
  const metricsParts = [];
  const safe = item && typeof item === 'object' ? item : {};
  const decisionText = (safe.decision || '').toString().trim();
  if (decisionText) {
    metricsParts.push(`Decision: ${decisionText}`);
  }
  const takeValue = safe.take;
  if (typeof takeValue === 'boolean' && !decisionText) {
    metricsParts.push(`Decision: ${takeValue ? 'Take trade' : 'Skip trade'}`);
  }
  const parseNumeric = (value) => {
    if (value === null || value === undefined) return null;
    const numeric = Number(value);
    return Number.isFinite(numeric) ? numeric : null;
  };

  const confidenceVal = parseNumeric(safe.confidence);
  if (confidenceVal !== null && confidenceVal > 0) {
    metricsParts.push(`Confidence ${confidenceVal.toFixed(2)}`);
  }
  const sizeMult = parseNumeric(safe.size_multiplier);
  if (sizeMult !== null) {
    metricsParts.push(`Size ×${sizeMult.toFixed(2)}`);
  }
  const slMult = parseNumeric(safe.sl_multiplier);
  if (slMult !== null) {
    metricsParts.push(`SL ×${slMult.toFixed(2)}`);
  }
  const tpMult = parseNumeric(safe.tp_multiplier);
  if (tpMult !== null) {
    metricsParts.push(`TP ×${tpMult.toFixed(2)}`);
  }

  const noteCandidates = [];
  const pushUniqueNote = (value) => {
    if (!value) return;
    const text = value.toString().trim();
    if (!text) return;
    if (!noteCandidates.includes(text)) {
      noteCandidates.push(text);
    }
  };
  pushUniqueNote(safe.decision_reason);
  pushUniqueNote(safe.decision_note);
  pushUniqueNote(safe.risk_note);
  if (Array.isArray(safe.notes)) {
    safe.notes.forEach((note) => pushUniqueNote(note));
  }

  const events = Array.isArray(safe.events) ? safe.events.slice() : [];
  const requestPayload = safe.request_payload ?? safe.requestPayload ?? null;
  const responsePayload = safe.response_payload ?? safe.responsePayload ?? null;

  return { metricsParts, noteCandidates, events, requestPayload, responsePayload };
}

function buildAiRequestDetailContent(item) {
  const { metricsParts, noteCandidates, events, requestPayload, responsePayload } =
    collectAiRequestDetailData(item);
  const container = document.createElement('div');
  container.className = 'ai-request-modal-content';

  const body = document.createElement('div');
  body.className = 'ai-request-card__body';

  if (metricsParts.length > 0) {
    const metrics = document.createElement('div');
    metrics.className = 'ai-request-card__metrics';
    metricsParts.forEach((text) => {
      const chip = document.createElement('span');
      chip.textContent = text;
      metrics.append(chip);
    });
    body.append(metrics);
  }

  if (noteCandidates.length > 0) {
    const noteList = document.createElement('ul');
    noteList.className = 'ai-request-card__notes';
    noteCandidates.slice(0, 6).forEach((note) => {
      const li = document.createElement('li');
      li.textContent = note;
      noteList.append(li);
    });
    body.append(noteList);
  }

  if (events.length > 0) {
    const toMillis = (value) => {
      if (!value) return 0;
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return 0;
      return date.getTime();
    };
    events.sort((a, b) => toMillis(a?.ts) - toMillis(b?.ts));
    const timeline = document.createElement('ol');
    timeline.className = 'ai-request-card__events';
    events.forEach((event) => {
      if (!event || typeof event !== 'object') return;
      const eventItem = document.createElement('li');
      const kind = (event.kind || 'info').toString().toLowerCase();
      eventItem.className = `ai-request-card__event ai-request-card__event--${kind}`;
      const header = document.createElement('div');
      header.className = 'ai-request-card__event-header';
      const kindLabel = document.createElement('span');
      kindLabel.className = 'ai-request-card__event-kind';
      kindLabel.textContent = kind.toUpperCase();
      header.append(kindLabel);
      const eventTime = document.createElement('span');
      eventTime.className = 'ai-request-card__event-time';
      eventTime.textContent = formatTimeShort(event.ts) || formatTimestamp(event.ts);
      eventTime.dateTime = event.ts || '';
      header.append(eventTime);
      eventItem.append(header);
      const headline = (event.headline || '').toString().trim();
      if (headline) {
        const headlineEl = document.createElement('div');
        headlineEl.className = 'ai-request-card__event-headline';
        headlineEl.textContent = headline;
        eventItem.append(headlineEl);
      }
      const bodyText = (event.body || '').toString().trim();
      if (bodyText) {
        const bodyEl = document.createElement('div');
        bodyEl.className = 'ai-request-card__event-body';
        bodyEl.textContent = bodyText;
        eventItem.append(bodyEl);
      }
      timeline.append(eventItem);
    });
    if (timeline.children.length > 0) {
      body.append(timeline);
    }
  }

  const renderJsonSection = (label, payload) => {
    if (payload === null || payload === undefined) return;
    let formatted = '';
    if (typeof payload === 'string') {
      const trimmed = payload.trim();
      if (!trimmed) return;
      try {
        formatted = JSON.stringify(JSON.parse(trimmed), null, 2);
      } catch (err) {
        formatted = trimmed;
      }
    } else {
      try {
        formatted = JSON.stringify(payload, null, 2);
      } catch (err) {
        formatted = String(payload);
      }
    }
    if (!formatted) return;
    const section = document.createElement('section');
    section.className = 'ai-request-card__json';
    const heading = document.createElement('h3');
    heading.className = 'ai-request-card__json-title';
    heading.textContent = label;
    const pre = document.createElement('pre');
    pre.textContent = formatted;
    section.append(heading, pre);
    body.append(section);
  };

  renderJsonSection(
    translate('ai.requests.modal.requestPayload', 'AI request payload'),
    requestPayload
  );
  renderJsonSection(
    translate('ai.requests.modal.responsePayload', 'AI response payload'),
    responsePayload
  );

  if (body.children.length === 0) {
    const empty = document.createElement('p');
    empty.className = 'ai-request-modal-empty';
    empty.textContent = translate('ai.requests.modal.empty', 'No additional details available.');
    body.append(empty);
  }

  container.append(body);
  return container;
}

function getAiRequestTimestamp(item) {
  if (!item || typeof item !== 'object') return 0;
  const ts = item.updated_at || item.created_at;
  const time = ts ? new Date(ts).getTime() : 0;
  return Number.isFinite(time) ? time : 0;
}

function getAiRequestScrollStep() {
  if (!aiRequestList) return 0;
  const firstCard = aiRequestList.querySelector('.ai-request-card');
  if (!firstCard) return 0;
  const { gap } = getComputedStyle(aiRequestList);
  const gapValue = Number.parseFloat(gap) || 0;
  return firstCard.getBoundingClientRect().width + gapValue;
}

function updateAiRequestNavButtons() {
  if (!aiRequestList || !aiRequestPrev || !aiRequestNext) return;
  const maxScroll = Math.max(aiRequestList.scrollWidth - aiRequestList.clientWidth, 0);
  if (maxScroll <= 2) {
    aiRequestPrev.disabled = true;
    aiRequestNext.disabled = true;
    return;
  }
  aiRequestPrev.disabled = aiRequestList.scrollLeft <= 1;
  aiRequestNext.disabled = aiRequestList.scrollLeft >= maxScroll - 1;
}

function scrollAiRequests(direction = 1) {
  if (!aiRequestList) return;
  const step = getAiRequestScrollStep() || aiRequestList.clientWidth * 0.9;
  aiRequestList.scrollBy({ left: step * direction, behavior: 'smooth' });
}

function resetAiRequestScrollPosition() {
  if (!aiRequestList) return;
  aiRequestList.scrollTo({ left: 0, behavior: 'auto' });
  requestAnimationFrame(updateAiRequestNavButtons);
}

function renderAiRequests(requests) {
  if (!aiRequestList) return;
  const fragment = document.createDocumentFragment();
  if (!aiMode) {
    aiRequestsEmptyStreak = 0;
    const disabled = document.createElement('div');
    disabled.className = 'ai-request-empty';
    disabled.textContent = translate('ai.feed.disabled', 'Enable AI mode to view the activity feed.');
    fragment.append(disabled);
    aiRequestList.replaceChildren(fragment);
    resetAiRequestScrollPosition();
    return;
  }
  const items = Array.isArray(requests)
    ? [...requests]
        .sort((a, b) => getAiRequestTimestamp(b) - getAiRequestTimestamp(a))
        .slice(0, 30)
    : [];
  if (items.length === 0) {
    aiRequestsEmptyStreak += 1;
    if (aiRequestList.childElementCount > 0 && aiRequestsEmptyStreak === 1) {
      return;
    }
    const empty = document.createElement('div');
    empty.className = 'ai-request-empty';
    empty.textContent = translate(
      'ai.requests.empty',
      'AI decisions will appear here once the bot consults the strategy copilot.'
    );
    fragment.append(empty);
    aiRequestList.replaceChildren(fragment);
    aiRequestsEmptyStreak = Math.min(Math.max(aiRequestsEmptyStreak, 1), 2);
    resetAiRequestScrollPosition();
    return;
  }
  aiRequestsEmptyStreak = 0;
  items.forEach((rawItem) => {
    if (!rawItem || typeof rawItem !== 'object') return;
    const item = rawItem;
    const statusKey = (item.status || 'pending').toString().toLowerCase();
    const statusLabel = getAiRequestStatusLabel(statusKey);
    const symbol = (item.symbol || '').toString().toUpperCase();
    const sideLabel = formatSideLabel(item.side || '');
    const detailData = collectAiRequestDetailData(item);
    const card = document.createElement('button');
    card.type = 'button';
    card.className = 'ai-request-card';
    card.dataset.status = statusKey;
    card.setAttribute('role', 'listitem');

    const header = document.createElement('div');
    header.className = 'ai-request-card__header';

    const title = document.createElement('div');
    title.className = 'ai-request-card__title';
    const symbolEl = document.createElement('span');
    symbolEl.className = 'ai-request-card__symbol';
    symbolEl.textContent = symbol || '—';
    title.append(symbolEl);

    if (sideLabel && sideLabel !== '—') {
      const sideEl = document.createElement('span');
      sideEl.className = 'ai-request-card__side';
      sideEl.textContent = sideLabel;
      title.append(sideEl);
    }

    header.append(title);

    if (statusLabel) {
      const statusEl = document.createElement('span');
      statusEl.className = `ai-request-card__status ${statusKey}`;
      statusEl.textContent = statusLabel;
      header.append(statusEl);
    }

    card.append(header);

    const timestamp = item.updated_at || item.created_at;
    const timestampLabel = formatTimestamp(timestamp);
    const meta = document.createElement('div');
    meta.className = 'ai-request-card__meta';
    if (timestampLabel && timestampLabel !== '–') {
      const timeEl = document.createElement('span');
      timeEl.className = 'ai-request-card__time';
      timeEl.textContent = timestampLabel;
      timeEl.dateTime = timestamp || '';
      meta.append(timeEl);
    }

    const decisionMetric = detailData.metricsParts.find((text) => text.startsWith('Decision:'));
    if (decisionMetric) {
      const decisionPreview = document.createElement('span');
      decisionPreview.textContent = decisionMetric.replace(/^Decision:\s*/, '');
      meta.append(decisionPreview);
    }

    if (meta.children.length > 0) {
      card.append(meta);
    }

    if (detailData.metricsParts.length > 0) {
      const preview = document.createElement('div');
      preview.className = 'ai-request-card__metrics ai-request-card__preview';
      detailData.metricsParts.slice(0, 3).forEach((text) => {
        const chip = document.createElement('span');
        chip.textContent = text;
        preview.append(chip);
      });
      card.append(preview);
    }

    const notePreviewText = detailData.noteCandidates[0];
    if (notePreviewText) {
      const notePreview = document.createElement('p');
      notePreview.className = 'ai-request-card__note';
      notePreview.textContent =
        notePreviewText.length > 160 ? `${notePreviewText.slice(0, 157).trimEnd()}…` : notePreviewText;
      card.append(notePreview);
    }

    const actions = document.createElement('div');
    actions.className = 'ai-request-card__actions';
    const hint = document.createElement('span');
    hint.className = 'ai-request-card__hint';
    hint.textContent = translate('trades.viewDetails', 'View details');
    actions.append(hint);
    card.append(actions);

    const accessibleParts = [];
    if (sideLabel && sideLabel !== '—') {
      accessibleParts.push(sideLabel);
    }
    if (statusLabel) {
      accessibleParts.push(statusLabel);
    }
    if (timestampLabel && timestampLabel !== '–') {
      accessibleParts.push(timestampLabel);
    }
    if (decisionMetric) {
      accessibleParts.push(decisionMetric.replace(/^Decision:\s*/, ''));
    }
    const accessibleSuffix = accessibleParts.length > 0 ? ` (${accessibleParts.join(' · ')})` : '';
    const baseLabel = symbol ? `View AI decision for ${symbol}` : 'View AI decision details';
    card.setAttribute('aria-label', `${baseLabel}${accessibleSuffix}`);

    card.addEventListener('click', () => openAiRequestModal(item, card));

    fragment.append(card);
  });
  aiRequestList.replaceChildren(fragment);
  resetAiRequestScrollPosition();
}

function openAiRequestModal(request, returnTarget) {
  if (!aiRequestModal || !aiRequestModalBody) return;

  const safe = request && typeof request === 'object' ? request : {};
  const statusKey = (safe.status || 'pending').toString().toLowerCase();
  const statusLabel = getAiRequestStatusLabel(statusKey);
  const symbol = (safe.symbol || '').toString().toUpperCase();
  const sideLabel = formatSideLabel(safe.side || '');
  const detailData = collectAiRequestDetailData(safe);

  const titleParts = [];
  if (symbol) {
    titleParts.push(symbol);
  }
  if (sideLabel && sideLabel !== '—') {
    titleParts.push(sideLabel);
  }
  if (aiRequestModalTitle) {
    aiRequestModalTitle.textContent =
      titleParts.length > 0 ? titleParts.join(' · ') : translate('ai.requests.modal.title', 'AI decision');
  }

  const decisionMetric = detailData.metricsParts.find((text) => text.startsWith('Decision:'));
  const timestamp = safe.updated_at || safe.created_at;
  const timestampLabel = formatTimestamp(timestamp);
  const subtitleParts = [];
  if (statusLabel) {
    subtitleParts.push(statusLabel);
  }
  if (timestampLabel && timestampLabel !== '–') {
    subtitleParts.push(timestampLabel);
  }
  if (decisionMetric) {
    subtitleParts.push(decisionMetric.replace(/^Decision:\s*/, ''));
  }
  if (aiRequestModalSubtitle) {
    aiRequestModalSubtitle.textContent =
      subtitleParts.filter(Boolean).join(' · ') ||
      translate('ai.requests.modal.noMetadata', 'No additional context available.');
  }

  const active =
    returnTarget instanceof HTMLElement
      ? returnTarget
      : document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
  aiRequestModalReturnTarget = active && active !== document.body ? active : null;

  if (aiRequestModalHideTimer) {
    clearTimeout(aiRequestModalHideTimer);
    aiRequestModalHideTimer = null;
  }
  if (aiRequestModalFinalizeHandler) {
    aiRequestModal.removeEventListener('transitionend', aiRequestModalFinalizeHandler);
    aiRequestModalFinalizeHandler = null;
  }

  aiRequestModalBody.innerHTML = '';
  const content = buildAiRequestDetailContent(safe);
  aiRequestModalBody.append(content);
  aiRequestModalBody.scrollTop = 0;

  aiRequestModal.removeAttribute('hidden');
  aiRequestModal.removeAttribute('aria-hidden');
  requestAnimationFrame(() => {
    aiRequestModal.classList.add('is-active');
  });
  document.body.classList.add('modal-open');

  document.addEventListener('keydown', handleAiRequestModalKeydown);
  if (aiRequestModalClose) {
    setTimeout(() => aiRequestModalClose.focus(), 120);
  }
}

function closeAiRequestModal() {
  if (!aiRequestModal) {
    return;
  }

  if (aiRequestModalHideTimer) {
    clearTimeout(aiRequestModalHideTimer);
    aiRequestModalHideTimer = null;
  }
  if (aiRequestModalFinalizeHandler) {
    aiRequestModal.removeEventListener('transitionend', aiRequestModalFinalizeHandler);
    aiRequestModalFinalizeHandler = null;
  }
  if (aiRequestModal.hasAttribute('hidden')) {
    return;
  }

  aiRequestModal.classList.remove('is-active');
  aiRequestModal.setAttribute('aria-hidden', 'true');
  document.body.classList.remove('modal-open');

  const finalize = () => {
    if (aiRequestModalHideTimer) {
      clearTimeout(aiRequestModalHideTimer);
      aiRequestModalHideTimer = null;
    }
    if (!aiRequestModal.hasAttribute('hidden')) {
      aiRequestModal.setAttribute('hidden', '');
    }
    if (aiRequestModalFinalizeHandler) {
      aiRequestModal.removeEventListener('transitionend', aiRequestModalFinalizeHandler);
      aiRequestModalFinalizeHandler = null;
    }
    const restoreTarget =
      aiRequestModalReturnTarget && typeof aiRequestModalReturnTarget.focus === 'function'
        ? aiRequestModalReturnTarget
        : null;
    aiRequestModalReturnTarget = null;
    if (restoreTarget) {
      restoreTarget.focus({ preventScroll: true });
    }
  };

  aiRequestModalFinalizeHandler = finalize;
  aiRequestModal.addEventListener('transitionend', finalize);
  aiRequestModalHideTimer = setTimeout(finalize, 280);

  document.removeEventListener('keydown', handleAiRequestModalKeydown);
}

function handleAiRequestModalKeydown(event) {
  if (event.key === 'Escape') {
    closeAiRequestModal();
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
  const shouldAutoScroll = autoScrollEnabled && isScrolledToBottom(aiChatMessages);
  const msg = document.createElement('div');
  msg.className = `ai-chat-message ${role === 'user' ? 'user' : 'assistant'}`;
  const roleLabel = document.createElement('div');
  roleLabel.className = 'ai-chat-role';
  const displayLabel = meta.roleLabel || (role === 'user' ? 'You' : 'Strategy Copilot');
  roleLabel.textContent = displayLabel;
  const text = document.createElement('p');
  text.className = 'ai-chat-text';
  text.textContent = message;
  msg.append(roleLabel, text);
  const metaParts = [];
  if (meta.model) metaParts.push(meta.model);
  if (meta.source && meta.source !== 'openai') {
    const source = (meta.source || '').toString();
    const label = source === 'missing_chat_key' ? 'dashboard' : source.replace(/_/g, ' ');
    metaParts.push(label);
  }
  if (metaParts.length > 0) {
    const metaEl = document.createElement('div');
    metaEl.className = 'ai-chat-meta';
    metaEl.textContent = metaParts.join(' • ');
    msg.append(metaEl);
  }
  aiChatMessages.append(msg);
  if (shouldAutoScroll) {
    const behavior = aiChatMessages.scrollHeight > aiChatMessages.clientHeight ? 'smooth' : 'auto';
    scrollToBottom(aiChatMessages, behavior);
  }
}

function applyTradeProposalStatus(cardEl, data, options = {}) {
  if (!cardEl) return;
  const { skipRegistry = false } = options;
  let normalizedUpdate = null;
  if (skipRegistry) {
    normalizedUpdate = normalizeTradeProposal(data);
  } else {
    normalizedUpdate = registerTradeProposal(data);
    if (!normalizedUpdate) {
      normalizedUpdate = normalizeTradeProposal(data);
    }
  }
  if (!normalizedUpdate) return;

  const statusText = (normalizedUpdate.status || '').toString().toLowerCase();
  const statusEl = cardEl.querySelector('.ai-trade-proposal__status');
  const actionBtn = cardEl.querySelector('.ai-trade-proposal__action');
  const errorMessage = (normalizedUpdate.error || '').toString().trim();
  const idleLabel = translate('chat.proposal.execute', 'Place via Aster');
  const conflict = tradeProposalConflictsWithActivePosition(normalizedUpdate);
  const symbol = extractProposalSymbol(normalizedUpdate);

  cardEl.classList.remove('queued', 'failed');
  if (symbol) {
    cardEl.dataset.symbol = symbol;
  } else {
    delete cardEl.dataset.symbol;
  }
  if (conflict) {
    cardEl.dataset.positionConflict = 'true';
  } else {
    cardEl.dataset.positionConflict = 'false';
  }

  if (conflict) {
    if (statusEl) {
      statusEl.textContent = translate('chat.proposal.alreadyOpen', 'Already open position for symbol');
    }
    if (actionBtn) {
      actionBtn.disabled = true;
      actionBtn.textContent = idleLabel;
    }
    return;
  }

  if (statusText === 'executed' || statusText === 'completed') {
    cardEl.classList.add('queued');
    if (statusEl) {
      statusEl.textContent = translate('chat.proposal.statusExecuted', 'Trade placed via the Aster API.');
    }
    if (actionBtn) {
      actionBtn.disabled = true;
      actionBtn.textContent = translate('chat.proposal.executedLabel', 'Trade placed');
    }
    return;
  }

  if (statusText === 'queued') {
    cardEl.classList.add('queued');
    if (statusEl) {
      statusEl.textContent = translate('chat.proposal.statusQueued', 'Manual trade queued for execution.');
    }
    if (actionBtn) {
      actionBtn.disabled = true;
      actionBtn.textContent = translate('chat.proposal.queued', 'Manual trade queued');
    }
    return;
  }

  if (statusText === 'failed') {
    cardEl.classList.add('failed');
    if (statusEl) {
      statusEl.textContent = errorMessage || translate('chat.proposal.statusFailedDetailed', 'The bot could not execute this trade.');
    }
    if (actionBtn) {
      actionBtn.disabled = false;
      actionBtn.textContent = translate('chat.proposal.retry', 'Retry');
    }
    return;
  }

  if (statusText === 'processing') {
    if (statusEl) {
      statusEl.textContent = translate('chat.proposal.statusProcessing', 'Trade is being placed via the Aster API…');
    }
    if (actionBtn) {
      actionBtn.disabled = true;
      actionBtn.textContent = translate('chat.proposal.executing', 'Placing…');
    }
    return;
  }

  if (statusEl) {
    statusEl.textContent = translate('chat.proposal.statusPending', 'Ready to place via the Aster API.');
  }
  if (actionBtn) {
    actionBtn.disabled = false;
    actionBtn.textContent = idleLabel;
  }
}

function appendTradeProposalCard(proposal) {
  if (!aiChatMessages) return;
  const normalizedProposal = registerTradeProposal(proposal);
  if (!normalizedProposal) return;
  const existing = aiChatMessages.querySelector(
    `.ai-trade-proposal[data-proposal-id="${normalizedProposal.id}"]`
  );
  if (existing) {
    applyTradeProposalStatus(existing, normalizedProposal, { skipRegistry: true });
    requestAutomatedTradeExecution();
    return;
  }
  const empty = aiChatMessages.querySelector('.ai-chat-empty');
  if (empty) empty.remove();
  const shouldAutoScroll = autoScrollEnabled && isScrolledToBottom(aiChatMessages);

  const card = document.createElement('div');
  card.className = 'ai-trade-proposal';
  card.dataset.proposalId = normalizedProposal.id;

  const symbol = (normalizedProposal.symbol || '').toString().toUpperCase();
  const direction = (normalizedProposal.direction || '').toString().toUpperCase();
  if (direction === 'LONG') {
    card.classList.add('long');
  } else if (direction === 'SHORT') {
    card.classList.add('short');
  }

  const header = document.createElement('div');
  header.className = 'ai-trade-proposal__header';
  const title = document.createElement('div');
  title.className = 'ai-trade-proposal__title';
  if (symbol && direction) {
    title.textContent = `${symbol} ${direction}`;
  } else if (symbol) {
    title.textContent = symbol;
  } else if (direction) {
    title.textContent = direction;
  } else {
    title.textContent = translate('chat.proposal.idea', 'Trade Idea');
  }
  header.append(title);
  card.append(header);

  const grid = document.createElement('div');
  grid.className = 'ai-trade-proposal__grid';

  const addCell = (label, value) => {
    const cell = document.createElement('div');
    cell.className = 'ai-trade-proposal__cell';
    const labelEl = document.createElement('span');
    labelEl.className = 'ai-trade-proposal__label';
    labelEl.textContent = label;
    const valueEl = document.createElement('span');
    valueEl.className = 'ai-trade-proposal__value';
    valueEl.textContent = value;
    cell.append(labelEl, valueEl);
    grid.append(cell);
  };

  const formatNumber = (value, { maximumFractionDigits = 4 } = {}) => {
    const num = Number(value);
    if (!Number.isFinite(num)) return '—';
    const opts = {
      maximumFractionDigits,
      minimumFractionDigits: 0,
    };
    if (Math.abs(num) >= 1000) {
      opts.maximumFractionDigits = Math.min(opts.maximumFractionDigits, 2);
    } else if (Math.abs(num) >= 1) {
      opts.maximumFractionDigits = Math.min(opts.maximumFractionDigits, 3);
    } else {
      opts.maximumFractionDigits = Math.min(opts.maximumFractionDigits, 6);
    }
    return num.toLocaleString(undefined, opts);
  };

  const formatEntry = () => {
    const entryKind = (normalizedProposal.entry_kind || '').toString().toLowerCase();
    const entryLabel = (normalizedProposal.entry_label || '').toString();
    const entryPrice = Number(normalizedProposal.entry_price);
    let base = '';
    if (entryKind === 'limit' && Number.isFinite(entryPrice)) {
      base = `${translate('chat.proposal.entry.limit', 'Limit')} ${formatNumber(entryPrice)}`;
    } else {
      base = translate('chat.proposal.entry.market', 'Market');
    }
    if (entryLabel) {
      base = `${base} · ${entryLabel}`;
    }
    return base;
  };

  const formatPrice = (raw) => {
    if (raw === null || raw === undefined) return '—';
    return formatNumber(raw);
  };

  const formatSizing = () => {
    const notional = Number(normalizedProposal.notional);
    if (Number.isFinite(notional) && notional > 0) {
      return `${formatNumber(notional, { maximumFractionDigits: 2 })} USDT`;
    }
    const mult = Number(normalizedProposal.size_multiplier);
    if (Number.isFinite(mult) && mult > 0) {
      return `${formatNumber(mult, { maximumFractionDigits: 2 })}×`;
    }
    return '—';
  };

  const formatConfidence = () => {
    const value = Number(normalizedProposal.confidence);
    if (Number.isFinite(value) && value > 0) {
      const clamped = Math.min(Math.max(value, 0), 1);
      return `${Math.round(clamped * 100)}%`;
    }
    const label = (normalizedProposal.confidence_label ?? '').toString().trim();
    if (label) return label;
    return '';
  };

  const formatString = (raw, fallback = '—') => {
    if (raw === null || raw === undefined) return fallback;
    const text = raw.toString().trim();
    return text || fallback;
  };

  const formatTimeframe = () => {
    const primary = (normalizedProposal.timeframe ?? '').toString().trim();
    if (primary) return primary;
    const secondary = (normalizedProposal.timeframe_label ?? '').toString().trim();
    if (secondary) return secondary;
    return translate('chat.proposal.timeframe.na', 'N/A');
  };

  addCell(translate('chat.proposal.entry', 'Entry'), formatEntry());
  addCell(translate('chat.proposal.stop', 'Stop-Loss'), formatPrice(normalizedProposal.stop_loss));
  addCell(translate('chat.proposal.take', 'Take-Profit'), formatPrice(normalizedProposal.take_profit));
  addCell(translate('chat.proposal.size', 'Position Size'), formatSizing());
  const confidenceText = formatConfidence();
  if (confidenceText) {
    addCell(translate('chat.proposal.confidence', 'Confidence'), confidenceText);
  }
  addCell(translate('chat.proposal.timeframe', 'Timeframe'), formatTimeframe());

  if (normalizedProposal.risk_reward !== undefined) {
    const rr = Number(normalizedProposal.risk_reward);
    if (Number.isFinite(rr) && rr > 0) {
      addCell(translate('chat.proposal.riskReward', 'R/R'), formatNumber(rr, { maximumFractionDigits: 2 }));
    }
  }

  card.append(grid);

  if (normalizedProposal.note) {
    const note = normalizedProposal.note.toString().trim();
    if (note) {
      const noteEl = document.createElement('div');
      noteEl.className = 'ai-trade-proposal__note';
      noteEl.textContent = note;
      card.append(noteEl);
    }
  }

  const actions = document.createElement('div');
  actions.className = 'ai-trade-proposal__actions';
  const actionBtn = document.createElement('button');
  actionBtn.type = 'button';
  actionBtn.className = 'ai-trade-proposal__action';
  const idleLabel = translate('chat.proposal.execute', 'Place via Aster');
  const workingLabel = translate('chat.proposal.executing', 'Placing…');
  const successLabel = translate('chat.proposal.executedLabel', 'Trade placed');
  const retryLabel = translate('chat.proposal.retry', 'Retry');
  actionBtn.textContent = idleLabel;
  actions.append(actionBtn);
  card.append(actions);

  const statusEl = document.createElement('div');
  statusEl.className = 'ai-trade-proposal__status';
  statusEl.textContent = translate('chat.proposal.statusPending', 'Ready to place via the Aster API.');
  card.append(statusEl);

  actionBtn.addEventListener('click', async () => {
    if (!normalizedProposal.id) return;
    actionBtn.disabled = true;
    actionBtn.textContent = workingLabel;
    statusEl.textContent = translate('chat.proposal.statusExecuting', 'Placing trade via the Aster API…');
    setChatStatus(translate('chat.proposal.statusExecuting', 'Placing trade via the Aster API…'));
    try {
      const payload = await executeTradeProposal(normalizedProposal.id);
      applyTradeProposalStatus(card, payload);
      if (!card.classList.contains('queued')) {
        card.classList.add('queued');
        actionBtn.textContent = successLabel;
        statusEl.textContent = translate('chat.proposal.statusExecuted', 'Trade placed via the Aster API.');
      }
      setChatStatus(translate('chat.proposal.statusExecuted', 'Trade placed via the Aster API.'));
    } catch (err) {
      const message =
        (err?.message || '').trim() || translate('chat.proposal.statusFailed', 'Failed to place trade proposal.');
      statusEl.textContent = message;
      setChatStatus(message);
      actionBtn.disabled = false;
      actionBtn.textContent = retryLabel;
    }
  });

  aiChatMessages.append(card);
  applyTradeProposalStatus(card, normalizedProposal, { skipRegistry: true });
  if (shouldAutoScroll) {
    const behavior = aiChatMessages.scrollHeight > aiChatMessages.clientHeight ? 'smooth' : 'auto';
    scrollToBottom(aiChatMessages, behavior);
  }
  requestAutomatedTradeExecution();
}

function setChatStatus(message) {
  if (aiChatStatus) {
    aiChatStatus.textContent = message || '';
  }
}

function updateAnalyzeButtonAvailability() {
  if (!btnAnalyzeMarket) return;
  const hasKey = hasDashboardChatKey();
  const shouldDisable = !hasKey || aiAnalyzePending;
  btnAnalyzeMarket.disabled = shouldDisable;
  if (!hasKey) {
    btnAnalyzeMarket.title = translate(
      'chat.analyze.hint',
      'Add an OpenAI API key in the AI controls to analyze the market.'
    );
  } else if (aiAnalyzePending) {
    btnAnalyzeMarket.title = translate('chat.analyze.pending', 'Market analysis in progress…');
  } else {
    btnAnalyzeMarket.title = '';
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
  if (!aiChatInput) {
    updateAnalyzeButtonAvailability();
    return;
  }
  const hasKey = hasDashboardChatKey();
  updateAnalyzeButtonAvailability();
  if (!aiMode) {
    stopAutomation();
    aiChatInput.value = '';
    aiChatInput.disabled = true;
    if (aiChatSubmit) aiChatSubmit.disabled = true;
    aiChatHistory = [];
    aiChatPending = false;
    resetChatPlaceholder(translate('chat.placeholder.disabled', 'Enable AI-Mode to access the dashboard chat.'));
    setChatStatus(translate('chat.status.disabled', 'AI-Mode disabled.'));
    setChatKeyIndicator('disabled', translate('chat.status.disabled', 'AI-Mode disabled.'));
    return;
  }

  if (!hasKey) {
    stopAutomation();
    aiChatInput.value = '';
    aiChatInput.disabled = true;
    if (aiChatSubmit) aiChatSubmit.disabled = true;
    aiChatHistory = [];
    aiChatPending = false;
    resetChatPlaceholder(
      translate('chat.placeholder.key', 'Add an OpenAI API key in the AI controls to start a conversation.')
    );
    setChatStatus(translate('chat.status.keyRequired', 'OpenAI key required.'));
    setChatKeyIndicator('missing', translate('chat.status.keyRequired', 'OpenAI key required.'));
    return;
  }

  aiChatInput.disabled = false;
  if (aiChatSubmit) aiChatSubmit.disabled = false;
  if (
    aiChatMessages &&
    !aiChatMessages.querySelector('.ai-chat-message') &&
    !aiChatMessages.querySelector('.ai-chat-empty')
  ) {
    resetChatPlaceholder(
      translate('chat.placeholder.prompt', 'Ask the strategy copilot anything about your trades.')
    );
  }
  const existingPlaceholder = aiChatMessages?.querySelector('.ai-chat-empty');
  if (existingPlaceholder) {
    existingPlaceholder.textContent = translate(
      'chat.placeholder.prompt',
      'Ask the strategy copilot anything about your trades.'
    );
  }
  setChatStatus('');
  setChatKeyIndicator('ready', translate('chat.key.ready', 'Dedicated chat key active'));
}

const TRADE_VOLUME_PRIMARY_KEYS = [
  'size_usdt',
  'sizeUsd',
  'sizeUSD',
  'size_usd',
  'notional',
  'notional_usdt',
  'notionalUsd',
  'notionalUSD',
  'positionNotional',
  'usd_value',
  'usdValue',
  'usd_size',
  'usdSize',
];

const TRADE_VOLUME_QTY_KEYS = [
  'qty',
  'quantity',
  'size',
  'signed_qty',
  'signedQty',
  'signedQuantity',
  'filled_qty',
  'filledQty',
  'amount',
];

const TRADE_VOLUME_PRICE_KEYS = [
  'notional_price',
  'entry',
  'entry_price',
  'entryPrice',
  'expected_entry',
  'avg_entry',
  'price',
  'avg_price',
  'avgPrice',
  'mark',
  'mark_price',
  'markPrice',
  'exit',
  'exit_price',
  'exitPrice',
];

function coerceTradeNumber(value) {
  if (value === null || value === undefined || value === '') return null;
  if (typeof value === 'number') {
    return Number.isFinite(value) ? value : null;
  }
  const text = value.toString().trim();
  if (!text) return null;
  const direct = Number(text.replace(/,/g, ''));
  if (Number.isFinite(direct)) return direct;
  const match = text.replace(/,/g, '').match(/-?\d+(?:\.\d+)?/);
  if (!match) return null;
  const parsed = Number(match[0]);
  return Number.isFinite(parsed) ? parsed : null;
}

function lookupTradeNumber(source, key) {
  if (!source || typeof source !== 'object' || !key) return null;
  const direct = coerceTradeNumber(source[key]);
  if (direct !== null && direct !== undefined) {
    return direct;
  }
  const extra = source.extra;
  if (extra && typeof extra === 'object') {
    const nested = coerceTradeNumber(extra[key]);
    if (nested !== null && nested !== undefined) {
      return nested;
    }
  }
  const context = source.context;
  if (context && typeof context === 'object') {
    const nested = coerceTradeNumber(context[key]);
    if (nested !== null && nested !== undefined) {
      return nested;
    }
  }
  return null;
}

function lookupTradeValue(source, key) {
  if (!source || typeof source !== 'object' || !key) return null;
  if (key in source && source[key] !== undefined && source[key] !== null) {
    return source[key];
  }
  const extra = source.extra;
  if (extra && typeof extra === 'object' && extra[key] !== undefined && extra[key] !== null) {
    return extra[key];
  }
  const context = source.context;
  if (context && typeof context === 'object' && context[key] !== undefined && context[key] !== null) {
    return context[key];
  }
  return null;
}

function collectTradeIdentifierSources(trade) {
  const sources = [];
  if (!trade || typeof trade !== 'object') {
    return sources;
  }

  const queue = [];
  const visited = new Set();
  const enqueue = (candidate) => {
    if (!candidate || typeof candidate !== 'object') return;
    if (visited.has(candidate)) return;
    visited.add(candidate);
    queue.push(candidate);
  };

  enqueue(trade);
  while (queue.length) {
    const current = queue.shift();
    sources.push(current);
    for (const key of TRADE_POSITION_CONTAINER_KEYS) {
      const nested = current[key];
      if (nested && typeof nested === 'object') {
        enqueue(nested);
      }
    }
  }

  return sources;
}

function parseTradeTimestamp(value) {
  const numeric = Number(value);
  if (Number.isFinite(numeric)) {
    return numeric;
  }
  if (typeof value === 'string') {
    const trimmed = value.trim();
    if (!trimmed) {
      return null;
    }
    const direct = Number(trimmed);
    if (Number.isFinite(direct)) {
      return direct;
    }
    const parsed = Date.parse(trimmed);
    if (!Number.isNaN(parsed)) {
      return parsed / 1000;
    }
  }
  return null;
}

function extractTradePositionKey(trade) {
  if (!trade || typeof trade !== 'object') {
    return '';
  }
  const identifierSources = collectTradeIdentifierSources(trade);
  for (const source of identifierSources) {
    for (const key of TRADE_POSITION_IDENTIFIER_KEYS) {
      const value = lookupTradeValue(source, key);
      if (value === null || value === undefined) {
        continue;
      }
      const text = value.toString().trim();
      if (text) {
        return `${key}:${text}`;
      }
    }
  }
  const symbolCandidates = [trade.symbol, trade.s, trade.pair, trade.instrument, trade.asset, trade.base];
  const symbol = symbolCandidates
    .map((candidate) => (candidate === null || candidate === undefined ? '' : candidate.toString().trim().toUpperCase()))
    .find((candidate) => candidate) || '';
  for (const key of TRADE_TIMESTAMP_IDENTIFIER_KEYS) {
    const candidate = lookupTradeValue(trade, key);
    if (candidate === null || candidate === undefined) {
      continue;
    }
    const parsed = parseTradeTimestamp(candidate);
    if (Number.isFinite(parsed)) {
      const tsLabel = parsed.toFixed(3);
      return symbol ? `${symbol}:${tsLabel}` : `ts:${tsLabel}`;
    }
  }
  if (symbol) {
    return symbol;
  }
  return '';
}

function countHistoryPositions(historyEntries) {
  if (!Array.isArray(historyEntries) || historyEntries.length === 0) {
    return 0;
  }
  const identifiers = new Set();
  let fallback = 0;
  historyEntries.forEach((trade) => {
    const key = extractTradePositionKey(trade);
    if (key) {
      identifiers.add(key);
    } else {
      fallback += 1;
    }
  });
  return identifiers.size + fallback;
}

function resolveTradePnlValue(trade) {
  if (!trade || typeof trade !== 'object') {
    return null;
  }
  for (const key of COMPLETED_POSITION_PNL_KEYS) {
    const candidate = lookupTradeNumber(trade, key);
    if (Number.isFinite(candidate)) {
      return candidate;
    }
  }
  const incomeValue = lookupTradeNumber(trade, 'income');
  if (Number.isFinite(incomeValue)) {
    return incomeValue;
  }
  return null;
}

function summarizeHistoryWinLoss(historyEntries) {
  if (!Array.isArray(historyEntries) || historyEntries.length === 0) {
    return null;
  }
  const bucketPnls = new Map();
  const fallbackPnls = [];
  historyEntries.forEach((trade) => {
    const pnlValue = resolveTradePnlValue(trade);
    if (!Number.isFinite(pnlValue)) {
      return;
    }
    const key = extractTradePositionKey(trade);
    if (key) {
      const next = (bucketPnls.get(key) ?? 0) + pnlValue;
      bucketPnls.set(key, next);
    } else {
      fallbackPnls.push(pnlValue);
    }
  });
  if (bucketPnls.size === 0 && fallbackPnls.length === 0) {
    return null;
  }
  let wins = 0;
  let losses = 0;
  let draws = 0;
  const finalizeBucket = (value) => {
    if (value > 0) {
      wins += 1;
    } else if (value < 0) {
      losses += 1;
    } else {
      draws += 1;
    }
  };
  bucketPnls.forEach(finalizeBucket);
  fallbackPnls.forEach(finalizeBucket);
  const total = wins + losses + draws;
  if (total <= 0) {
    return null;
  }
  return { wins, losses, draws, total };
}

function isSyntheticTradeHistoryEntry(trade) {
  if (!trade || typeof trade !== 'object') {
    return false;
  }
  if (Boolean(trade.synthetic)) {
    return true;
  }
  const syntheticSource =
    trade.synthetic_source ?? trade.syntheticSource ?? trade.synthetic_origin ?? trade.syntheticOrigin;
  if (typeof syntheticSource === 'string' && syntheticSource.trim()) {
    return true;
  }
  return false;
}

function resolveTradeHistoryTimestamp(trade) {
  if (!trade || typeof trade !== 'object') {
    return Number.NEGATIVE_INFINITY;
  }
  for (const key of TRADE_TIMESTAMP_IDENTIFIER_KEYS) {
    const candidate = lookupTradeValue(trade, key);
    if (candidate === undefined || candidate === null || candidate === '') {
      continue;
    }
    const parsed = parseTradeTimestamp(candidate);
    if (!Number.isFinite(parsed)) {
      continue;
    }
    if (parsed > 1e12 || parsed > 1e10) {
      return parsed / 1000;
    }
    return parsed;
  }
  return Number.NEGATIVE_INFINITY;
}

function buildCompletedPositionsFromHistoryEntries(historyEntries = []) {
  const stats = { ...COMPLETED_POSITIONS_STATS_DEFAULTS };
  if (!Array.isArray(historyEntries) || historyEntries.length === 0) {
    return { entries: [], stats };
  }
  const buckets = new Map();
  let fallbackCounter = 0;
  historyEntries.forEach((trade) => {
    if (!trade || typeof trade !== 'object') {
      return;
    }
    if (isSyntheticTradeHistoryEntry(trade)) {
      return;
    }
    let bucketKey = extractTradePositionKey(trade);
    if (!bucketKey) {
      fallbackCounter += 1;
      bucketKey = `fallback:${fallbackCounter}`;
    }
    let bucket = buckets.get(bucketKey);
    if (!bucket) {
      bucket = {
        key: bucketKey,
        position: {},
        ts: Number.NEGATIVE_INFINITY,
      };
      buckets.set(bucketKey, bucket);
    }
    mergeCompletedPositionPayload(bucket.position, trade);
    const closedTs = getPositionClosedTimestamp(bucket.position);
    const openedTs = getPositionTimestamp(bucket.position);
    if (Number.isFinite(closedTs) && closedTs > Number.NEGATIVE_INFINITY) {
      bucket.ts = closedTs;
    } else if (Number.isFinite(openedTs) && openedTs > Number.NEGATIVE_INFINITY) {
      bucket.ts = openedTs;
    } else {
      const fallbackTs = resolveTradeHistoryTimestamp(trade);
      if (Number.isFinite(fallbackTs) && fallbackTs > Number.NEGATIVE_INFINITY) {
        bucket.ts = fallbackTs;
      }
    }
  });
  const entries = Array.from(buckets.values()).map((entry) => ({
    key: entry.key,
    position: entry.position,
    ts: Number.isFinite(entry.ts) ? entry.ts : Number.NEGATIVE_INFINITY,
  }));
  entries.sort((a, b) => {
    const tsA = Number.isFinite(a.ts) ? a.ts : Number.NEGATIVE_INFINITY;
    const tsB = Number.isFinite(b.ts) ? b.ts : Number.NEGATIVE_INFINITY;
    if (tsA === tsB) {
      return 0;
    }
    return tsB > tsA ? 1 : -1;
  });
  stats.trades = entries.length;
  entries.forEach((entry) => {
    const pnlField = pickNumericField(entry.position, COMPLETED_POSITION_PNL_KEYS);
    if (Number.isFinite(pnlField.numeric)) {
      stats.realizedPnl += pnlField.numeric;
      if (pnlField.numeric > 0) {
        stats.wins += 1;
      } else if (pnlField.numeric < 0) {
        stats.losses += 1;
      } else {
        stats.draws += 1;
      }
    } else {
      stats.draws += 1;
    }
    const rField = pickNumericField(entry.position, COMPLETED_POSITION_R_KEYS);
    if (Number.isFinite(rField.numeric)) {
      stats.totalR += rField.numeric;
    }
  });
  return { entries, stats };
}

function estimateTradeVolume(entry) {
  if (!entry || typeof entry !== 'object') {
    return 0;
  }

  for (const key of TRADE_VOLUME_PRIMARY_KEYS) {
    const volume = lookupTradeNumber(entry, key);
    if (volume !== null && volume !== undefined && Math.abs(volume) > 0) {
      return Math.abs(volume);
    }
  }

  let qtyValue = null;
  for (const key of TRADE_VOLUME_QTY_KEYS) {
    const qty = lookupTradeNumber(entry, key);
    if (qty !== null && qty !== undefined && Math.abs(qty) > 0) {
      qtyValue = Math.abs(qty);
      break;
    }
  }

  let priceValue = null;
  for (const key of TRADE_VOLUME_PRICE_KEYS) {
    const price = lookupTradeNumber(entry, key);
    if (price !== null && price !== undefined && price > 0) {
      priceValue = price;
      break;
    }
  }

  if (qtyValue !== null && priceValue !== null) {
    return qtyValue * priceValue;
  }

  if (Array.isArray(entry.fills)) {
    let fillsVolume = 0;
    for (const fill of entry.fills) {
      if (!fill || typeof fill !== 'object') continue;
      const fillQty = lookupTradeNumber(fill, 'qty') ?? lookupTradeNumber(fill, 'size');
      const fillPrice = lookupTradeNumber(fill, 'price');
      if (
        fillQty === null ||
        fillQty === undefined ||
        fillPrice === null ||
        fillPrice === undefined ||
        fillPrice <= 0
      ) {
        continue;
      }
      const qtyAbs = Math.abs(fillQty);
      if (qtyAbs <= 0) continue;
      fillsVolume += qtyAbs * fillPrice;
    }
    if (fillsVolume > 0) {
      return fillsVolume;
    }
  }

  return 0;
}

function deriveHistoryVolume(historyEntries) {
  if (!Array.isArray(historyEntries) || historyEntries.length === 0) {
    return 0;
  }
  let total = 0;
  for (const trade of historyEntries) {
    const volume = estimateTradeVolume(trade);
    if (Number.isFinite(volume) && volume > 0) {
      total += volume;
    }
  }
  return total;
}

function renderHeroMetrics(
  cumulativeStats,
  sessionStats,
  historyEntries = null,
  preparedMetrics = null,
  openPositions = null,
  historySummary = null,
) {
  if (!heroTotalTrades || !heroTotalPnl || !heroTotalWinRate) return;

  const totals = cumulativeStats && typeof cumulativeStats === 'object' ? cumulativeStats : {};
  const fallback = sessionStats && typeof sessionStats === 'object' ? sessionStats : {};
  const historyList = Array.isArray(historyEntries) ? historyEntries : [];
  const summaryStats = historySummary && typeof historySummary === 'object' ? historySummary : null;
  const serverMetrics = preparedMetrics && typeof preparedMetrics === 'object' ? preparedMetrics : null;

  const resolveNumericField = (source, keys) => {
    if (!source) return null;
    for (const key of keys) {
      if (!(key in source)) continue;
      const numeric = Number(source[key]);
      if (Number.isFinite(numeric)) {
        return numeric;
      }
    }
    return null;
  };

  const parsePositiveInteger = (value) => {
    if (value == null) return null;
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return null;
    if (numeric <= 0) return null;
    return Math.round(Math.abs(numeric));
  };

  const pickFirstFinite = (...candidates) => {
    for (const candidate of candidates) {
      if (candidate == null) continue;
      const numeric = Number(candidate);
      if (Number.isFinite(numeric)) {
        return numeric;
      }
    }
    return null;
  };

  const normalizeOpenPositionPayload = (payload) => {
    if (!payload) return [];
    if (Array.isArray(payload)) {
      return payload.filter((entry) => entry && typeof entry === 'object');
    }
    if (typeof payload === 'object') {
      return Object.values(payload).filter((entry) => entry && typeof entry === 'object');
    }
    return [];
  };

  const openPayloadSources = [
    openPositions,
    totals?.open_positions ?? totals?.openPositions,
    fallback?.open_positions ?? fallback?.openPositions,
  ];
  let normalizedOpenPositions = [];
  for (const source of openPayloadSources) {
    if (!source) continue;
    const normalized = normalizeOpenPositionPayload(source);
    if (normalized.length > 0) {
      normalizedOpenPositions = normalized;
      break;
    }
  }
  const openPositionsCount = normalizedOpenPositions.length;

  const serverTotalTrades = resolveNumericField(serverMetrics, ['total_trades', 'totalTrades']);
  const historyTradeCount = historyList.length > 0 ? countHistoryPositions(historyList) : null;
  const tradeCountCandidates = [
    serverTotalTrades != null ? parsePositiveInteger(serverTotalTrades) : null,
    historyTradeCount,
    parsePositiveInteger(fallback.count ?? fallback.total_trades ?? fallback.totalTrades),
    parsePositiveInteger(totals.total_trades ?? totals.count),
  ];
  let totalTrades = tradeCountCandidates.find((value) => value != null) ?? 0;
  if (openPositionsCount > 0) {
    totalTrades += openPositionsCount;
  }
  heroTotalTrades.textContent = totalTrades.toLocaleString();

  const aiBudgetSpentRaw = pickFirstFinite(
    resolveNumericField(sessionStats, ['ai_budget_spent', 'aiBudgetSpent']),
    resolveNumericField(serverMetrics, ['ai_budget_spent', 'aiBudgetSpent']),
    resolveNumericField(totals, ['ai_budget_spent', 'aiBudgetSpent']),
    resolveNumericField(fallback, ['ai_budget_spent', 'aiBudgetSpent']),
  );
  const aiBudgetSpent = Number.isFinite(aiBudgetSpentRaw) ? Math.max(aiBudgetSpentRaw, 0) : 0;

  const summaryRealizedPnl = pickFirstFinite(
    resolveNumericField(summaryStats, ['realized_pnl', 'realizedPnl']),
    resolveNumericField(summaryStats, ['total_pnl', 'totalPnl']),
    resolveNumericField(summaryStats, ['realized']),
  );

  const realizedPnlRaw = pickFirstFinite(
    summaryRealizedPnl,
    resolveNumericField(sessionStats, ['realized_pnl', 'realizedPnl']),
    resolveNumericField(sessionStats, ['total_pnl', 'totalPnl']),
    resolveNumericField(serverMetrics, ['realized_pnl', 'realizedPnl']),
    resolveNumericField(totals, ['realized_pnl', 'realizedPnl']),
    resolveNumericField(fallback, ['realized_pnl', 'realizedPnl']),
    totals.total_pnl,
    fallback.total_pnl,
  );

  const historyDerivedRealizedPnl = (() => {
    if (!Array.isArray(historyList) || historyList.length === 0) {
      return null;
    }
    let total = 0;
    let counted = 0;
    for (const entry of historyList) {
      const pnlField = pickNumericField(entry, COMPLETED_POSITION_PNL_KEYS);
      if (!Number.isFinite(pnlField.numeric)) {
        continue;
      }
      total += pnlField.numeric;
      counted += 1;
    }
    return counted > 0 ? total : null;
  })();

  const hasCompletedStats =
    completedPositionsStatsTotals && completedPositionsStatsTotals.trades > 0;
  const completedPositionsRealizedPnl = hasCompletedStats
    ? Number(completedPositionsStatsTotals.realizedPnl)
    : null;
  const completedRealizedPnl = Number.isFinite(completedPositionsRealizedPnl)
    ? completedPositionsRealizedPnl
    : Number.isFinite(summaryRealizedPnl)
      ? summaryRealizedPnl
      : Number.isFinite(historyDerivedRealizedPnl)
        ? historyDerivedRealizedPnl
        : null;
  const realizedBaseline = Number.isFinite(completedRealizedPnl)
    ? completedRealizedPnl
    : null;

  const serverNetPnl = resolveNumericField(serverMetrics, ['total_pnl', 'totalPnl']);
  const fallbackNetPnl = pickFirstFinite(
    totals.total_pnl,
    resolveNumericField(totals, ['total_pnl', 'totalPnl']),
    fallback.total_pnl,
    resolveNumericField(fallback, ['total_pnl', 'totalPnl']),
  );

  let netPnl = null;
  if (Number.isFinite(realizedBaseline)) {
    netPnl = realizedBaseline;
  } else if (Number.isFinite(realizedPnlRaw)) {
    netPnl = realizedPnlRaw - aiBudgetSpent;
  } else if (Number.isFinite(serverNetPnl)) {
    netPnl = serverNetPnl;
  } else if (Number.isFinite(fallbackNetPnl)) {
    netPnl = fallbackNetPnl;
  } else {
    netPnl = 0;
  }

  if (!Number.isFinite(netPnl)) {
    netPnl = 0;
  }

  const realizedPnl = Number.isFinite(realizedBaseline)
    ? realizedBaseline
    : Number.isFinite(realizedPnlRaw)
      ? realizedPnlRaw
      : netPnl + aiBudgetSpent;

  if (Number.isFinite(netPnl)) {
    const formatted = Math.abs(netPnl).toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
    const prefix = netPnl > 0 ? '+' : netPnl < 0 ? '-' : '';
    heroTotalPnl.textContent = `${prefix}${formatted} USDT`;
  } else {
    heroTotalPnl.textContent = '0 USDT';
  }

  heroTotalPnl.classList.remove(
    'hero-total-pnl--positive',
    'hero-total-pnl--negative',
    'hero-total-pnl--neutral',
  );
  const pnlToneClass = netPnl > 0
    ? 'hero-total-pnl--positive'
    : netPnl < 0
    ? 'hero-total-pnl--negative'
    : 'hero-total-pnl--neutral';
  heroTotalPnl.classList.add(pnlToneClass);

  if (heroTotalPnlNote) {
    const formatSignedValue = (value, unit) => {
      if (!Number.isFinite(value)) return `—`;
      const absValue = Math.abs(value).toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
      const prefix = value > 0 ? '+' : value < 0 ? '-' : '';
      return `${prefix}${absValue} ${unit}`;
    };
    const formatUnsignedValue = (value, unit) => {
      if (!Number.isFinite(value)) return '—';
      const absValue = Math.abs(value).toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
      return `${absValue} ${unit}`;
    };
    const realizedDisplay = formatSignedValue(realizedPnl, 'USDT');
    const aiSpentDisplay = formatUnsignedValue(aiBudgetSpent, 'USD');
    heroTotalPnlNote.textContent = translate(
      'hero.metrics.pnlNote.detail',
      'Realized {{realized}} − AI budget {{spent}}',
      { realized: realizedDisplay, spent: aiSpentDisplay },
    );
  }

  const normalizeWinRate = (value) => {
    if (value == null) return null;
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return null;
    if (numeric < 0) return 0;
    if (numeric > 1) return 1;
    return numeric;
  };

  const historyWinLossSummary = summarizeHistoryWinLoss(historyList);

  const historyWinRate = (() => {
    if (!historyWinLossSummary) return null;
    if (historyWinLossSummary.total <= 0) return null;
    if (historyWinLossSummary.wins <= 0) return 0;
    return Math.min(1, historyWinLossSummary.wins / historyWinLossSummary.total);
  })();

  const fallbackWinRate = normalizeWinRate(fallback.win_rate ?? fallback.winRate);
  const totalsWinRate = normalizeWinRate(totals.win_rate ?? totals.winRate);
  const serverWinRate = normalizeWinRate(resolveNumericField(serverMetrics, ['win_rate', 'winRate']));
  const winsRaw = Number(totals.wins ?? fallback.wins ?? 0);
  const lossesRaw = Number(totals.losses ?? fallback.losses ?? 0);
  const drawsRaw = Number(totals.draws ?? fallback.draws ?? 0);
  const denominator = totalTrades > 0 ? totalTrades : winsRaw + lossesRaw + drawsRaw;
  const derivedTotalsWinRate =
    denominator > 0 && Number.isFinite(winsRaw)
      ? Math.max(0, Math.min(1, winsRaw / denominator))
      : null;
  const computedWinRate =
    historyWinRate ??
    serverWinRate ??
    totalsWinRate ??
    derivedTotalsWinRate ??
    fallbackWinRate ??
    0;

  heroTotalWinRate.textContent = `${(computedWinRate * 100).toFixed(1)}%`;

  const parseTradeCount = (...candidates) => {
    for (const candidate of candidates) {
      if (candidate == null) continue;
      const numeric = Number(candidate);
      if (Number.isFinite(numeric)) {
        return Math.max(0, Math.round(numeric));
      }
    }
    return null;
  };

  let winsCount = null;
  let lossesCount = null;

  if (historyWinLossSummary) {
    winsCount = historyWinLossSummary.wins;
    lossesCount = historyWinLossSummary.losses;
  } else {
    winsCount = parseTradeCount(
      resolveNumericField(serverMetrics, ['wins']),
      totals.wins,
      totals.profitable_trades,
      totals.positive_trades,
      totals.green_trades,
      fallback.wins,
      fallback.profitable_trades,
      fallback.positive_trades,
      fallback.green_trades,
    );
    lossesCount = parseTradeCount(
      resolveNumericField(serverMetrics, ['losses']),
      totals.losses,
      totals.unprofitable_trades,
      totals.negative_trades,
      totals.red_trades,
      fallback.losses,
      fallback.unprofitable_trades,
      fallback.negative_trades,
      fallback.red_trades,
    );
  }

  if (pnlTradesWonValue) {
    pnlTradesWonValue.textContent = winsCount != null ? winsCount.toLocaleString() : '—';
  }
  if (pnlTradesLostValue) {
    pnlTradesLostValue.textContent = lossesCount != null ? lossesCount.toLocaleString() : '—';
  }

  heroMetricsSnapshot = {
    totalTrades,
    totalPnl: Number.isFinite(netPnl) ? netPnl : 0,
    totalPnlDisplay: heroTotalPnl.textContent,
    realizedPnl: Number.isFinite(realizedPnl) ? realizedPnl : Number.isFinite(netPnl) ? netPnl : 0,
    aiBudgetSpent: Number.isFinite(aiBudgetSpent) ? aiBudgetSpent : 0,
    winRate: computedWinRate,
    winRateDisplay: heroTotalWinRate.textContent,
  };
}

function setShareFeedback(message, { tone } = {}) {
  if (!shareFeedback) return;
  const text = (message || '').toString();
  shareFeedback.textContent = text;
  if (tone) {
    shareFeedback.dataset.tone = tone;
  } else {
    shareFeedback.removeAttribute('data-tone');
  }
}

function buildShareText(snapshot) {
  const totalTradesRaw = Number(
    snapshot?.totalTrades ?? snapshot?.total_trades ?? snapshot?.count ?? 0,
  );
  const totalTrades = Number.isFinite(totalTradesRaw) ? totalTradesRaw : 0;

  const totalPnlRaw = Number(snapshot?.totalPnl ?? snapshot?.total_pnl ?? 0);
  const totalPnlFormatted = Number.isFinite(totalPnlRaw)
    ? `${
        totalPnlRaw < 0
          ? '-'
          : ''
      }${Math.abs(totalPnlRaw).toLocaleString('de-DE', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })} USDT`
    : '0,00 USDT';

  let winRateRaw = snapshot?.winRate;
  if (!Number.isFinite(winRateRaw)) {
    winRateRaw = Number(snapshot?.win_rate);
  }
  if (!Number.isFinite(winRateRaw)) {
    winRateRaw = 0;
  }
  const winRatePercent = (winRateRaw * 100).toFixed(1);

  const funnyLines = [
    'Bot says: still stretching before the next moon mission 🚀',
    'Trading desk vibes: coffee in hand, charts on loop ☕📈',
    'Status update: gains loading… please hold the line ⏳',
    'Today’s alpha: patience is the ultimate leverage 🧘',
    'Meanwhile, MrAster is polishing its crystal ball 🔮',
  ];
  const funnyIndex = Math.floor(Math.random() * funnyLines.length);
  const funnyLine = funnyLines[funnyIndex] ?? funnyLines[0];

  const lines = [
    `Total Trades: ${totalTrades.toLocaleString()}`,
    `Total PNL: ${totalPnlFormatted}`,
    `Total Win Rate: ${winRatePercent}%`,
    '',
    funnyLine,
    '',
    'https://github.com/Blindripper/MrAster',
  ];

  return lines.join('\n');
}

async function copyShareText(text) {
  if (!text) return false;
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch (error) {
    console.warn('Clipboard write failed', error);
  }

  try {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.setAttribute('readonly', '');
    textarea.style.position = 'absolute';
    textarea.style.left = '-9999px';
    document.body.append(textarea);
    textarea.select();
    document.execCommand('copy');
    textarea.remove();
    return true;
  } catch (error) {
    console.warn('Fallback clipboard write failed', error);
    return false;
  }
}

function openTweetComposer(text) {
  if (!text) return false;
  const url = new URL('https://twitter.com/intent/tweet');
  url.searchParams.set('text', text);
  const popup = window.open(url.toString(), '_blank', 'width=600,height=840');
  if (popup) {
    popup.opener = null;
    return true;
  }
  return false;
}

function determineShareVariant(snapshot) {
  const totalPnl = Number(snapshot?.totalPnl ?? 0);
  if (Number.isFinite(totalPnl) && totalPnl < 0) {
    return 'low';
  }
  return 'high';
}

function buildShareImageUrl(variant) {
  const url = new URL(`/share/${variant}`, window.location.origin);
  return url.toString();
}

async function fetchShareImage(variant) {
  const url = buildShareImageUrl(variant);
  let response;
  try {
    response = await fetch(url, { cache: 'no-cache' });
  } catch (error) {
    console.warn('Unable to request share image', error);
    throw error;
  }

  if (!response?.ok) {
    throw new Error(`Failed to load share image: ${response?.status}`);
  }

  const blob = await response.blob();
  const type = blob.type || 'image/jpeg';
  const extension = type.includes('png') ? 'png' : 'jpg';

  return { blob, type, extension, variant, url };
}

async function shareImageToX(image, shareText) {
  if (!image) return false;
  try {
    if (!navigator.share || typeof File === 'undefined') {
      return false;
    }
  } catch (error) {
    console.warn('Web Share API unavailable', error);
    return false;
  }

  const shareData = {
    title: 'MrAster trading stats',
    text: shareText,
    files: [new File([image.blob], `mraster-${image.variant}.${image.extension}`, { type: image.type })],
  };

  if (typeof navigator.canShare === 'function') {
    try {
      if (!navigator.canShare(shareData)) {
        console.warn('navigator.canShare reported files unsupported. Attempting share anyway.');
      }
    } catch (error) {
      console.warn('navigator.canShare threw unexpectedly', error);
    }
  }

  try {
    await navigator.share(shareData);
    return true;
  } catch (error) {
    if (error?.name !== 'AbortError') {
      console.warn('System share failed', error);
    }
    return false;
  }
}

async function copyShareImageToClipboard(image) {
  if (!image || !navigator.clipboard?.write || typeof ClipboardItem === 'undefined') {
    return false;
  }
  try {
    const item = new ClipboardItem({ [image.type]: image.blob });
    await navigator.clipboard.write([item]);
    return true;
  } catch (error) {
    console.warn('Clipboard image write failed', error);
    return false;
  }
}

function escapeHtml(value) {
  return (value ?? '')
    .toString()
    .replace(/[&<>'"]/g, (char) => {
      switch (char) {
        case '&':
          return '&amp;';
        case '<':
          return '&lt;';
        case '>':
          return '&gt;';
        case '"':
          return '&quot;';
        case "'":
          return '&#39;';
        default:
          return char;
      }
    });
}

function openMemeComposerShell() {
  try {
    const popup = window.open('', MEME_COMPOSER_WINDOW_NAME, MEME_COMPOSER_WINDOW_FEATURES);
    if (!popup) {
      return null;
    }

    popup.opener = null;
    const doc = popup.document;
    doc.open();
    doc.write(`
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <title>MrAster Meme Composer</title>
          <style>
            :root { color-scheme: dark; }
            * { box-sizing: border-box; }
            body {
              margin: 0;
              padding: 24px;
              background: #05060c;
              color: #f5f6fa;
              font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
              display: flex;
              justify-content: center;
            }
            .composer {
              width: 100%;
              max-width: 880px;
              display: flex;
              flex-direction: column;
              gap: 24px;
            }
            .composer h1 {
              margin: 0;
              font-size: 24px;
              font-weight: 600;
            }
            .composer-content {
              background: #0f111a;
              border-radius: 18px;
              padding: 24px;
              border: 1px solid rgba(255, 255, 255, 0.08);
              min-height: 200px;
              display: flex;
              align-items: center;
              justify-content: center;
              text-align: center;
            }
            .composer-content.composer-ready {
              flex-direction: column;
              gap: 24px;
              align-items: stretch;
              justify-content: flex-start;
              text-align: left;
            }
            .composer-status {
              margin: 0;
              font-size: 16px;
              opacity: 0.75;
            }
            .composer-image,
            .composer-caption {
              background: #0f111a;
              border-radius: 18px;
              border: 1px solid rgba(255, 255, 255, 0.08);
              overflow: hidden;
            }
            .composer-image img {
              display: block;
              width: 100%;
              height: auto;
            }
            .composer-caption {
              padding: 24px;
            }
            .composer-caption h2 {
              margin-top: 0;
              margin-bottom: 12px;
              font-size: 18px;
            }
            .composer-hint {
              margin: 0 0 16px;
              font-size: 18px;
              font-weight: 600;
              opacity: 0.9;
            }
            .composer-caption pre {
              margin: 0;
              padding: 16px;
              border-radius: 12px;
              background: rgba(255, 255, 255, 0.05);
              font-family: 'JetBrains Mono', 'Fira Code', monospace;
              font-size: 14px;
              white-space: pre-wrap;
              word-break: break-word;
              border: 1px solid rgba(255, 255, 255, 0.08);
            }
            .composer-error {
              margin: 0;
              color: #ff9393;
              font-weight: 500;
            }
          </style>
        </head>
        <body>
          <div class="composer">
            <h1>MrAster Meme Composer</h1>
            <div class="composer-content" data-composer-root>
              <p class="composer-status">Preparing meme…</p>
            </div>
          </div>
        </body>
      </html>
    `);
    doc.close();

    if (!popup.__mrAsterComposerUnloadHandler) {
      popup.__mrAsterComposerUnloadHandler = () => {
        if (typeof popup.__mrAsterComposerCleanup === 'function') {
          try {
            popup.__mrAsterComposerCleanup();
          } catch (cleanupError) {
            console.warn('Failed to release meme composer resources', cleanupError);
          }
          popup.__mrAsterComposerCleanup = null;
        }
        popup.__mrAsterComposerUnloadAttached = false;
      };
    }
    popup.__mrAsterComposerUnloadAttached = false;

    return popup;
  } catch (error) {
    console.warn('Unable to open meme composer window', error);
    return null;
  }
}

function renderMemeComposer(windowRef, image, shareText) {
  if (!windowRef) return false;
  try {
    const doc = windowRef.document;
    const container = doc?.querySelector('[data-composer-root]');
    if (!container) {
      return false;
    }

    if (typeof windowRef.__mrAsterComposerCleanup === 'function') {
      try {
        windowRef.__mrAsterComposerCleanup();
      } catch (cleanupError) {
        console.warn('Failed to reset previous meme composer state', cleanupError);
      }
      windowRef.__mrAsterComposerCleanup = null;
    }

    let imageSrc = '';
    let cleanup = null;
    if (image?.blob instanceof Blob) {
      const objectUrl = URL.createObjectURL(image.blob);
      imageSrc = objectUrl;
      cleanup = () => {
        try {
          URL.revokeObjectURL(objectUrl);
        } catch (revokeError) {
          console.warn('Failed to revoke meme composer object URL', revokeError);
        }
      };
    } else if (image?.url) {
      imageSrc = image.url;
    }

    if (cleanup) {
      windowRef.__mrAsterComposerCleanup = cleanup;
      if (!windowRef.__mrAsterComposerUnloadAttached && windowRef.__mrAsterComposerUnloadHandler) {
        windowRef.addEventListener('beforeunload', windowRef.__mrAsterComposerUnloadHandler, { once: true });
        windowRef.__mrAsterComposerUnloadAttached = true;
      }
    }

    container.innerHTML = `
      <div class="composer-image">
        ${
          imageSrc
            ? `<img src="${imageSrc}" alt="MrAster meme preview" draggable="true" />`
            : '<p class="composer-error">We could not load the meme image.</p>'
        }
      </div>
      <div class="composer-caption">
        <h2>Post text</h2>
        <p class="composer-hint">Paste this Meme into your X Post. Simply drag and drop the Picture.</p>
      </div>
    `;
    container.classList.add('composer-ready');

    windowRef.focus();
    return true;
  } catch (error) {
    console.warn('Failed to render meme composer content', error);
    return false;
  }
}

function renderMemeComposerError(windowRef, message) {
  if (!windowRef) return false;
  try {
    const doc = windowRef.document;
    const container = doc?.querySelector('[data-composer-root]');
    if (!container) {
      return false;
    }

    if (typeof windowRef.__mrAsterComposerCleanup === 'function') {
      try {
        windowRef.__mrAsterComposerCleanup();
      } catch (cleanupError) {
        console.warn('Failed to reset meme composer on error', cleanupError);
      }
      windowRef.__mrAsterComposerCleanup = null;
    }

    container.classList.remove('composer-ready');
    container.innerHTML = `<p class="composer-error">${escapeHtml(message || 'Unable to load meme composer.')}</p>`;
    return true;
  } catch (error) {
    console.warn('Failed to render meme composer error state', error);
    return false;
  }
}

async function handlePostToX(event) {
  if (event?.preventDefault) {
    event.preventDefault();
  }
  if (!btnPostX) return;
  const snapshot = heroMetricsSnapshot || {};
  const shareText = buildShareText(snapshot);
  const variant = determineShareVariant(snapshot);
  const memeComposerWindow = openMemeComposerShell();
  let memeComposerReady = false;

  btnPostX.disabled = true;
  setShareFeedback('Preparing your X post…');

  try {
    const image = await fetchShareImage(variant);
    memeComposerReady = renderMemeComposer(memeComposerWindow, image, shareText);
    const sharedViaSystem = await shareImageToX(image, shareText);

    if (sharedViaSystem) {
      setShareFeedback('System share sheet opened with the performance snapshot attached. Select X to finish your post.');
      return;
    }

    const [clipboardSuccess, imageCopied] = await Promise.all([
      copyShareText(shareText),
      copyShareImageToClipboard(image),
    ]);

    const composerOpened = openTweetComposer(shareText);

    if (clipboardSuccess && imageCopied) {
      setShareFeedback(
        memeComposerReady
          ? 'Post text and image copied! The X composer and meme composer opened—paste the meme directly into your post.'
          : 'Post text and image copied! The composer opened—paste to attach the snapshot instantly.'
      );
    } else if (clipboardSuccess) {
      setShareFeedback(
        memeComposerReady
          ? 'Post text copied! Grab the meme from the composer window and add it to the X composer.'
          : 'Post text copied! Use the composer to add the image manually if it was not copied.'
      );
    } else if (imageCopied) {
      setShareFeedback(
        memeComposerReady
          ? 'Image copied to your clipboard! The meme composer is open if you need to drag or download it. Add your text manually in X.'
          : 'Image copied to your clipboard! Paste it into the composer and add your text manually.'
      );
    } else {
      setShareFeedback(
        memeComposerReady
          ? 'Compose windows opened. Copy the stats manually if clipboard access is blocked.'
          : 'Compose window opened. Copy the stats manually if clipboard access is blocked.'
      );
    }

    if (!composerOpened) {
      console.warn('Tweet composer window blocked');
    }
    if (memeComposerWindow && !memeComposerReady) {
      console.warn('Meme composer window blocked or failed to render');
    }
  } catch (error) {
    console.error('Failed to prepare X post', error);
    renderMemeComposerError(
      memeComposerWindow,
      'We could not load the meme preview. Close this window and try sharing again.'
    );
    setShareFeedback('We could not prepare the X post. Please try again.');
  } finally {
    btnPostX.disabled = false;
  }
}

function resolveTradeSummaryPayload(summaryOverride) {
  const override = getTradeSummaryOverride();
  if (override && typeof override === 'object') {
    return override;
  }
  if (summaryOverride && typeof summaryOverride === 'object') {
    return summaryOverride;
  }
  return buildCompletedPositionsSummaryFromTotals();
}

function renderTradeSummary(stats, summaryOverride = null) {
  if (!tradeSummary) {
    return;
  }
  lastTradeStats = stats || null;
  const summary = resolveTradeSummaryPayload(summaryOverride);
  const fragment = document.createDocumentFragment();
  if (!stats && !summary) {
    const placeholder = document.createElement('div');
    placeholder.className = 'trade-metric muted';
    placeholder.innerHTML = `
      <span class="metric-label">${translate('trades.summary.placeholder.label', 'Performance')}</span>
      <span class="metric-value">${translate('trades.summary.placeholder.value', 'No data yet')}</span>
    `;
    fragment.append(placeholder);
    tradeSummary.replaceChildren(fragment);
    setAiHintMessage(
      translate('trades.summary.hint', 'AI insight will appear once new telemetry is available.')
    );
    return;
  }
  const tradesCountCandidate = summary?.trades ?? summary?.count ?? stats?.count ?? 0;
  const tradesCount = Number.isFinite(Number(tradesCountCandidate))
    ? Math.max(0, Math.round(Number(tradesCountCandidate)))
    : 0;
  const realizedTotalCandidate =
    summary?.realized_pnl ?? summary?.realizedPnl ?? stats?.total_pnl ?? stats?.totalPnl ?? 0;
  const realizedTotalNumeric = Number(realizedTotalCandidate);
  const realizedTotal = Number.isFinite(realizedTotalNumeric) ? realizedTotalNumeric : 0;
  const avgRCandidate = summary?.avg_r ?? summary?.avgR;
  const totalRSource = summary?.total_r ?? summary?.totalR ?? stats?.total_r ?? stats?.totalR ?? 0;
  const totalRNumeric = Number(totalRSource);
  const avgR = Number.isFinite(Number(avgRCandidate))
    ? Number(avgRCandidate)
    : tradesCount > 0 && Number.isFinite(totalRNumeric)
      ? totalRNumeric / tradesCount
      : 0;
  const winRateCandidate = summary?.win_rate ?? summary?.winRate;
  const winRateValue = Number.isFinite(Number(winRateCandidate))
    ? Number(winRateCandidate)
    : Number.isFinite(Number(stats?.win_rate))
      ? Number(stats.win_rate)
      : tradesCount > 0 && Number.isFinite(Number(summary?.wins))
        ? Number(summary.wins) / tradesCount
        : 0;
  const normalizedWinRate = Math.min(Math.max(winRateValue, 0), 1);
  const metrics = [
    {
      label: translate('trades.metric.trades', 'Trades'),
      value: tradesCount,
      tone: 'neutral',
    },
    {
      label: translate('trades.metric.totalPnl', 'Realized PNL'),
      value: `${realizedTotal > 0 ? '+' : ''}${formatNumber(realizedTotal, 2)} USDT`,
      tone: realizedTotal > 0 ? 'profit' : realizedTotal < 0 ? 'loss' : 'neutral',
    },
    {
      label: translate('trades.metric.winRate', 'Win rate'),
      value: `${((normalizedWinRate ?? 0) * 100).toFixed(1)}%`,
      tone: 'neutral',
    },
    {
      label: translate('trades.metric.avgR', 'Avg R'),
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
    fragment.append(el);
  }
  tradeSummary.replaceChildren(fragment);
  setAiHintMessage(stats?.ai_hint);
}

function updateDecisionReasonsVisibility() {
  if (!decisionReasonsContainer) return;
  const hasReasons = decisionReasonsAvailable;
  const isExpanded = hasReasons && decisionReasonsExpanded;

  if (decisionReasonsToggle) {
    if (!hasReasons) {
      decisionReasonsToggle.setAttribute('hidden', '');
      decisionReasonsToggle.disabled = true;
    } else {
      decisionReasonsToggle.removeAttribute('hidden');
      decisionReasonsToggle.disabled = false;
    }
    decisionReasonsToggle.setAttribute('aria-expanded', isExpanded ? 'true' : 'false');
    decisionReasonsToggle.classList.toggle('is-expanded', isExpanded);
  }

  if (!hasReasons) {
    decisionReasonsContainer.setAttribute('hidden', '');
  } else if (isExpanded) {
    decisionReasonsContainer.removeAttribute('hidden');
  } else {
    decisionReasonsContainer.setAttribute('hidden', '');
  }

  const labelText = isExpanded
    ? translate('status.decisions.hideDetails', 'Hide details')
    : translate('status.decisions.showDetails', 'Details');
  if (decisionReasonsToggleLabel) {
    decisionReasonsToggleLabel.textContent = labelText;
  } else if (decisionReasonsToggle) {
    decisionReasonsToggle.textContent = labelText;
  }
}

function updateDecisionReasonsDownloadState(enabled) {
  if (!decisionReasonsDownload) return;
  if (enabled) {
    decisionReasonsDownload.removeAttribute('disabled');
    decisionReasonsDownload.setAttribute('aria-disabled', 'false');
  } else {
    decisionReasonsDownload.setAttribute('disabled', 'true');
    decisionReasonsDownload.setAttribute('aria-disabled', 'true');
  }
}

function renderDecisionStats(stats) {
  lastDecisionStats = stats || null;
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

  const fragment = document.createDocumentFragment();

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
    li.textContent = taken > 0
      ? translate('status.decisions.noneSkipped', 'No skipped trades recorded.')
      : translate('status.decisions.noneYet', 'No trade decisions yet.');
    fragment.append(li);
    decisionReasons.replaceChildren(fragment);
    decisionReasonsExpanded = false;
    decisionReasonsAvailable = false;
    updateDecisionReasonsVisibility();
    updateDecisionReasonsDownloadState(false);
    return;
  }

  items.sort((a, b) => {
    if (b.count !== a.count) return b.count - a.count;
    return a.label.localeCompare(b.label);
  });

  for (const item of items) {
    const li = document.createElement('li');
    li.dataset.reason = item.reason;
    li.dataset.count = item.count.toString();
    li.dataset.label = item.label;
    li.setAttribute('role', 'button');
    li.setAttribute('tabindex', '0');
    li.setAttribute('aria-label', `Show trades affected by ${item.label}`);
    const labelEl = document.createElement('span');
    labelEl.className = 'reason-label';
    labelEl.textContent = item.label;
    const countEl = document.createElement('span');
    countEl.className = 'reason-count';
    countEl.textContent = item.count.toString();
    li.append(labelEl, countEl);
    fragment.append(li);
  }

  decisionReasons.replaceChildren(fragment);
  decisionReasonsAvailable = true;
  updateDecisionReasonsVisibility();
  updateDecisionReasonsDownloadState(true);
}

function normaliseDecisionReason(reason) {
  return (reason || '')
    .toString()
    .trim()
    .toLowerCase();
}

function recordDecisionEvent(reason, event = {}) {
  const key = normaliseDecisionReason(reason);
  if (!key || !event) return;
  const entry = { ...event };
  entry.reason = key;
  if (entry.occurredAt === undefined || entry.occurredAt === null) {
    if (entry.occurredAtIso) {
      const parsed = Date.parse(entry.occurredAtIso);
      entry.occurredAt = Number.isFinite(parsed) ? parsed / 1000 : undefined;
    } else if (entry.parsed?.timestamp) {
      const parsed = Date.parse(entry.parsed.timestamp);
      entry.occurredAt = Number.isFinite(parsed) ? parsed / 1000 : undefined;
    }
  }
  if (entry.occurredAt !== undefined && entry.occurredAt !== null) {
    entry.occurredAt = Number(entry.occurredAt);
    if (!Number.isFinite(entry.occurredAt)) {
      entry.occurredAt = undefined;
    }
  }
  const existing = decisionReasonEvents.get(key) || [];
  existing.push(entry);
  while (existing.length > DECISION_REASON_EVENT_LIMIT) {
    existing.shift();
  }
  decisionReasonEvents.set(key, existing);
}

function buildDecisionEventFromTrade(trade) {
  if (!trade || typeof trade !== 'object') return null;
  const timestamp = getTradeTimestamp(trade);
  const occurredAt = Number.isFinite(timestamp) ? timestamp / 1000 : undefined;
  const messageParts = [];
  const aiMeta = trade.ai && typeof trade.ai === 'object' ? trade.ai : null;
  if (aiMeta?.decision_note) {
    messageParts.push(aiMeta.decision_note);
  } else if (aiMeta?.decision_reason) {
    messageParts.push(`Reason: ${friendlyReason(aiMeta.decision_reason)}`);
  } else if (trade.decision_note) {
    messageParts.push(trade.decision_note);
  }
  const message = messageParts.join(' ');
  return {
    type: 'trade',
    symbol: trade.symbol || '—',
    occurredAt,
    occurredAtIso: trade.closed_at_iso || trade.opened_at_iso || null,
    message,
    trade,
  };
}

function collectDecisionEvents(reason) {
  const key = normaliseDecisionReason(reason);
  if (!key) return [];
  const combined = [];
  const seen = new Set();
  const pushEvent = (event) => {
    if (!event) return;
    const symbol = event.symbol || '';
    const message = event.message || '';
    const occurredAt = Number.isFinite(event.occurredAt) ? event.occurredAt : '';
    const signature = `${event.type || 'log'}|${key}|${symbol}|${occurredAt}|${message}`;
    if (seen.has(signature)) return;
    seen.add(signature);
    combined.push(event);
  };

  const stored = decisionReasonEvents.get(key) || [];
  stored.forEach((event) => pushEvent({ ...event, type: event.type || 'log' }));

  const history = Array.isArray(latestTradesSnapshot?.history) ? latestTradesSnapshot.history : [];
  history.forEach((trade) => {
    if (!trade || typeof trade !== 'object') return;
    const aiMeta = trade.ai && typeof trade.ai === 'object' ? trade.ai : null;
    const reasonCandidates = [
      aiMeta?.decision_reason,
      trade.decision_reason,
      aiMeta?.plan?.decision_reason,
    ];
    const tradeReason = normaliseDecisionReason(reasonCandidates.find((value) => value));
    if (tradeReason && tradeReason === key) {
      pushEvent(buildDecisionEventFromTrade(trade));
    }
  });

  combined.sort((a, b) => {
    const aTs = Number.isFinite(a?.occurredAt) ? a.occurredAt : -Infinity;
    const bTs = Number.isFinite(b?.occurredAt) ? b.occurredAt : -Infinity;
    if (bTs !== aTs) return bTs - aTs;
    return (b?.symbol || '').localeCompare(a?.symbol || '');
  });

  return combined;
}

function formatDecisionEventTime(event) {
  if (!event) {
    return { label: '', title: '' };
  }
  if (event.occurredAtIso) {
    const parsed = new Date(event.occurredAtIso);
    if (!Number.isNaN(parsed.getTime())) {
      return {
        label: formatRelativeTime(event.occurredAtIso),
        title: parsed.toLocaleString(),
      };
    }
  }
  if (Number.isFinite(event.occurredAt)) {
    const parsed = new Date(event.occurredAt * 1000);
    if (!Number.isNaN(parsed.getTime())) {
      return {
        label: formatRelativeTime(event.occurredAt),
        title: parsed.toLocaleString(),
      };
    }
  }
  return { label: translate('common.timeUnknown', 'Time unavailable'), title: '' };
}

function renderDecisionDetailPairs(detailPairs = []) {
  const entries = Array.isArray(detailPairs) ? detailPairs : [];
  if (entries.length === 0) return null;
  const dl = document.createElement('dl');
  dl.className = 'no-cross-detail-grid';
  entries.forEach((entry) => {
    const dt = document.createElement('dt');
    dt.textContent = entry.label || entry.key || 'Detail';
    const dd = document.createElement('dd');
    dd.textContent = entry.value ?? '—';
    dl.append(dt, dd);
  });
  return dl;
}

function deriveGateFamilyKey(normalizedKey) {
  if (!normalizedKey) return '';
  return normalizedKey.replace(/(min|max|gate|threshold|limit|cap|pad)$/i, '');
}


function buildSkippedTradeExportPayload() {
  const stats = lastDecisionStats || latestTradesSnapshot?.decision_stats || null;
  const rejectedCounts = stats?.rejected && typeof stats.rejected === 'object' ? stats.rejected : {};
  const reasonKeys = new Set(Object.keys(rejectedCounts || {}));
  if (!reasonKeys.size && decisionReasonEvents.size > 0) {
    decisionReasonEvents.forEach((_, key) => reasonKeys.add(key));
  }
  const decisions = Array.from(reasonKeys).map((reasonKey) => {
    const events = collectDecisionEvents(reasonKey).map((event) => ({
      type: event?.type || 'log',
      symbol: event?.symbol ?? null,
      occurred_at: Number.isFinite(event?.occurredAt) ? event.occurredAt : null,
      occurred_at_iso: event?.occurredAtIso ?? null,
      message: event?.message ?? null,
      detail: event?.detail ?? null,
      parsed: event?.parsed ?? null,
      trade: event?.trade ?? null,
    }));
    const countValue = Number(rejectedCounts?.[reasonKey]);
    return {
      reason: reasonKey,
      label: friendlyReason(reasonKey),
      count: Number.isFinite(countValue) ? countValue : events.length,
      events,
    };
  });

  const filtered = decisions
    .filter((entry) => (entry.count ?? 0) > 0 || entry.events.length > 0)
    .sort((a, b) => {
      if ((b.count ?? 0) !== (a.count ?? 0)) {
        return (b.count ?? 0) - (a.count ?? 0);
      }
      return a.label.localeCompare(b.label);
    });

  if (!filtered.length) {
    return null;
  }

  const totalSkipped = filtered.reduce((sum, entry) => sum + (Number(entry.count) || 0), 0);
  const payload = {
    generated_at: new Date().toISOString(),
    total_skipped: totalSkipped,
    reasons: filtered,
  };
  const taken = Number(stats?.taken);
  if (Number.isFinite(taken)) {
    payload.total_taken = taken;
  }
  return payload;
}

function downloadDecisionReasonExport() {
  try {
    const payload = buildSkippedTradeExportPayload();
    if (!payload) {
      alert(translate('status.decisions.noneSkipped', 'No skipped trades recorded.'));
      return;
    }
    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    link.href = url;
    link.download = `mraster-skipped-trades-${timestamp}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch (err) {
    console.error('Unable to download skipped trades', err);
    alert(translate('status.decisions.exportError', 'Unable to download skipped trades right now.'));
  }
}

const DETAIL_GATE_HINTS = ['gate', 'min', 'max', 'cap', 'threshold', 'limit'];

function isGateDetailEntry(entry) {
  if (!entry) return false;
  const normalized = entry.normalizedKey || normaliseDetailKey(entry.key || entry.label || '');
  if (!normalized) return false;
  return DETAIL_GATE_HINTS.some((hint) => normalized.includes(hint));
}

function resolveNearMissComparison(detailPairs) {
  if (!Array.isArray(detailPairs) || detailPairs.length < 2) {
    return null;
  }
  const entries = detailPairs.map((entry) => ({
    key: entry.key,
    label: entry.label,
    valueText: entry.value,
    numericValue: Number.isFinite(entry.numericValue)
      ? entry.numericValue
      : Number(entry.value),
    normalizedKey: entry.normalizedKey || normaliseDetailKey(entry.key || entry.label || ''),
    isGate: isGateDetailEntry(entry),
  }));
  const comparisons = [];
  for (let i = 0; i < entries.length - 1; i += 1) {
    const current = entries[i];
    const next = entries[i + 1];
    if (!current || !next) continue;
    if (current.isGate || !next.isGate) continue;
    if (!Number.isFinite(current.numericValue) || !Number.isFinite(next.numericValue)) continue;
    comparisons.push({
      metricLabel: current.label,
      metricValueText: current.valueText,
      metricValue: current.numericValue,
      gateLabel: next.label,
      gateValueText: next.valueText,
      gateValue: next.numericValue,
    });
    i += 1;
  }
  if (!comparisons.length) {
    return null;
  }
  let best = null;
  comparisons.forEach((comparison) => {
    const diff = comparison.metricValue - comparison.gateValue;
    let percent = null;
    if (Math.abs(comparison.gateValue) > 1e-9) {
      percent = (diff / comparison.gateValue) * 100;
    } else if (Math.abs(comparison.metricValue) > 1e-9) {
      percent = (diff / Math.abs(comparison.metricValue)) * 100;
    }
    const score = Number.isFinite(percent) ? Math.abs(percent) : Math.abs(diff);
    if (!best || score < best.score) {
      best = {
        metricLabel: comparison.metricLabel,
        metricValueText: comparison.metricValueText,
        metricValue: comparison.metricValue,
        gateLabel: comparison.gateLabel,
        gateValueText: comparison.gateValueText,
        gateValue: comparison.gateValue,
        diff,
        percentDiff: Number.isFinite(percent) ? percent : null,
        score,
      };
    }
  });
  return best;
}

function pruneNearMissEntries(now = Date.now()) {
  if (!nearMissEntries.length) return;
  const cutoff = now - NEAR_MISS_COLLECTION_WINDOW_MS;
  nearMissEntries = nearMissEntries.filter((entry) => entry.tsMs >= cutoff);
}

function captureNearMissEvent(friendly, timestampSeconds) {
  if (!nearMissList || !friendly || !friendly.reason) return;
  const comparison = resolveNearMissComparison(friendly.detailPairs);
  if (!comparison) return;
  const tsMs = Number.isFinite(timestampSeconds) ? timestampSeconds * 1000 : Date.now();
  const entry = {
    id: `${friendly.reason || 'skip'}-${friendly.symbol || 'symbol'}-${tsMs}`,
    tsMs,
    symbol: friendly.symbol ? friendly.symbol.toUpperCase() : '—',
    reason: friendly.reason,
    reasonLabel:
      friendlyReason(friendly.reason)
        || friendly.label
        || translate('watchlist.nearMiss.reasonFallback', 'Filter rule'),
    metricLabel: comparison.metricLabel,
    metricValueText: comparison.metricValueText,
    gateLabel: comparison.gateLabel,
    gateValueText: comparison.gateValueText,
    diff: comparison.diff,
    percentDiff: comparison.percentDiff,
    score: comparison.score,
  };
  nearMissEntries.push(entry);
  pruneNearMissEntries();
}

function formatNearMissTimestamp(tsMs) {
  const date = new Date(tsMs);
  if (Number.isNaN(date.getTime())) {
    return '—';
  }
  const datePart = date.toLocaleDateString(undefined, { month: 'short', day: '2-digit' });
  const timePart = date.toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
  return `${datePart} ${timePart}`;
}

function formatNearMissMetaTime(tsMs) {
  const date = new Date(tsMs);
  if (Number.isNaN(date.getTime())) {
    return '—';
  }
  return date.toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

function formatNearMissCountdown(ms) {
  const totalSeconds = Math.max(0, Math.round(ms / 1000));
  const minutes = Math.floor(totalSeconds / 60)
    .toString()
    .padStart(2, '0');
  const seconds = (totalSeconds % 60).toString().padStart(2, '0');
  return `${minutes}:${seconds}`;
}

function buildNearMissMetricCell(label, valueText) {
  const cell = document.createElement('div');
  cell.className = 'near-miss-cell near-miss-metric';
  const labelEl = document.createElement('span');
  labelEl.textContent = label || '—';
  const valueEl = document.createElement('strong');
  valueEl.textContent = valueText ?? '—';
  cell.append(labelEl, valueEl);
  return cell;
}

function createNearMissHeaderRow() {
  const headers = [
    translate('watchlist.nearMiss.col.rank', 'Rank'),
    translate('watchlist.nearMiss.col.time', 'Date/Time'),
    translate('watchlist.nearMiss.col.symbol', 'Symbol'),
    translate('watchlist.nearMiss.col.reason', 'Reason'),
    translate('watchlist.nearMiss.col.gate', 'Filter Gate'),
    translate('watchlist.nearMiss.col.value', 'Filter Value'),
    translate('watchlist.nearMiss.col.percent', '% diff'),
  ];
  const row = document.createElement('div');
  row.className = 'near-miss-row near-miss-row-header';
  headers.forEach((text) => {
    const cell = document.createElement('div');
    cell.className = 'near-miss-cell';
    cell.textContent = text;
    row.append(cell);
  });
  return row;
}

function createNearMissRow(entry, rank) {
  const row = document.createElement('div');
  row.className = 'near-miss-row';

  const rankCell = document.createElement('div');
  rankCell.className = 'near-miss-cell near-miss-rank';
  rankCell.textContent = rank.toString().padStart(2, '0');

  const timeCell = document.createElement('div');
  timeCell.className = 'near-miss-cell';
  timeCell.textContent = formatNearMissTimestamp(entry.tsMs);

  const symbolCell = document.createElement('div');
  symbolCell.className = 'near-miss-cell near-miss-symbol';
  symbolCell.textContent = entry.symbol || '—';

  const reasonCell = document.createElement('div');
  reasonCell.className = 'near-miss-cell near-miss-reason';
  reasonCell.textContent = entry.reasonLabel || '—';

  const gateCell = buildNearMissMetricCell(entry.gateLabel, entry.gateValueText);
  const valueCell = buildNearMissMetricCell(entry.metricLabel, entry.metricValueText);

  const percentCell = document.createElement('div');
  percentCell.className = 'near-miss-cell near-miss-percent';
  if (Number.isFinite(entry.percentDiff)) {
    const value = entry.percentDiff;
    const sign = value > 0 ? '+' : '';
    const absValue = Math.abs(value);
    const digits = absValue >= 10 ? 1 : 2;
    percentCell.textContent = `${sign}${absValue.toFixed(digits)}%`;
    if (value > 0) {
      percentCell.classList.add('positive');
    } else if (value < 0) {
      percentCell.classList.add('negative');
    }
  } else if (Number.isFinite(entry.diff)) {
    const sign = entry.diff > 0 ? '+' : '';
    percentCell.textContent = `${sign}${entry.diff.toPrecision(3)}`;
  } else {
    percentCell.textContent = '—';
  }

  row.append(rankCell, timeCell, symbolCell, reasonCell, gateCell, valueCell, percentCell);
  return row;
}

function renderNearMissList(force = false) {
  if (!nearMissList) return;
  const now = Date.now();
  pruneNearMissEntries(now);
  if (now < nearMissReadyAt) {
    const countdown = formatNearMissCountdown(nearMissReadyAt - now);
    if (nearMissMeta) {
      nearMissMeta.textContent = translate(
        'watchlist.nearMiss.collectingMeta',
        'Collecting · {{time}} left',
        { time: countdown },
      );
    }
    if (force || !nearMissLastRenderedAt || now - nearMissLastRenderedAt >= NEAR_MISS_REFRESH_INTERVAL_MS) {
      const placeholder = document.createElement('div');
      placeholder.className = 'near-miss-empty';
      placeholder.textContent = translate(
        'watchlist.nearMiss.collectingBody',
        'Collecting initial filter misses. Ready in {{time}}.',
        { time: countdown },
      );
      nearMissList.replaceChildren(placeholder);
      nearMissLastRenderedAt = now;
    }
    return;
  }

  if (!nearMissEntries.length) {
    if (nearMissMeta) {
      nearMissMeta.textContent = translate(
        'watchlist.nearMiss.meta',
        'Updated {{time}} · Last 5 min',
        { time: formatNearMissMetaTime(now) },
      );
    }
    const empty = document.createElement('div');
    empty.className = 'near-miss-empty';
    empty.textContent = translate(
      'watchlist.nearMiss.empty',
      'No skipped trades recorded in the last 5 minutes.',
    );
    nearMissList.replaceChildren(empty);
    nearMissLastRenderedAt = now;
    return;
  }

  const ranked = nearMissEntries
    .slice()
    .sort((a, b) => {
      if (a.score !== b.score) return a.score - b.score;
      if (a.tsMs !== b.tsMs) return b.tsMs - a.tsMs;
      return (a.symbol || '').localeCompare(b.symbol || '');
    })
    .slice(0, 10);

  const fragment = document.createDocumentFragment();
  fragment.append(createNearMissHeaderRow());
  ranked.forEach((entry, index) => {
    fragment.append(createNearMissRow(entry, index + 1));
  });
  nearMissList.replaceChildren(fragment);
  if (nearMissMeta) {
    nearMissMeta.textContent = translate(
      'watchlist.nearMiss.meta',
      'Updated {{time}} · Last 5 min',
      { time: formatNearMissMetaTime(now) },
    );
  }
  nearMissLastRenderedAt = now;
}

function startNearMissMonitor() {
  if (!nearMissList) return;
  nearMissReadyAt = Date.now() + NEAR_MISS_COLLECTION_WINDOW_MS;
  pruneNearMissEntries();
  renderNearMissList(true);
  if (nearMissRenderTimer) {
    clearInterval(nearMissRenderTimer);
  }
  nearMissRenderTimer = setInterval(() => {
    renderNearMissList();
  }, NEAR_MISS_REFRESH_INTERVAL_MS);
}

function findDecisionReasonItem(element) {
  if (!element) return null;
  if (element instanceof HTMLElement) {
    return element.closest('li[data-reason]');
  }
  return null;
}

function activateDecisionReasonItem(item) {
  if (!item) return;
  const reason = item.dataset.reason;
  if (!reason) return;
  const label = item.dataset.label;
  const countRaw = Number(item.dataset.count);
  const count = Number.isFinite(countRaw) ? countRaw : undefined;
  openDecisionModal(reason, {
    label,
    count,
    returnTarget: item,
  });
}

function getPnlChartPalette() {
  const styles = getComputedStyle(document.documentElement);
  return {
    accent: styles.getPropertyValue('--accent-strong').trim() || '#f0a94b',
    accentSoft: styles.getPropertyValue('--accent-soft').trim() || 'rgba(240, 169, 75, 0.18)',
    textMuted: styles.getPropertyValue('--text-muted').trim() || '#a09889',
    gridLine: styles.getPropertyValue('--grid-line').trim() || 'rgba(255, 232, 168, 0.08)',
    canvasBg: styles.getPropertyValue('--surface-base').trim() || '#07070c',
  };
}

class PnlCanvasChart {
  constructor(canvas, { variant = 'default' } = {}) {
    this.canvas = canvas;
    this.variant = variant;
    this.payload = null;
    this.resizeObserver = null;
    this.boundResize = this.handleResize.bind(this);
    if (canvas && typeof ResizeObserver === 'function') {
      this.resizeObserver = new ResizeObserver(() => this.redraw());
      this.resizeObserver.observe(canvas);
    } else {
      window.addEventListener('resize', this.boundResize);
    }
  }

  destroy() {
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
      this.resizeObserver = null;
    } else {
      window.removeEventListener('resize', this.boundResize);
    }
    const ctx = this.canvas?.getContext?.('2d');
    if (ctx) {
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }
    this.payload = null;
  }

  handleResize() {
    this.redraw();
  }

  render(payload) {
    this.payload = {
      labels: Array.isArray(payload?.labels) ? payload.labels.slice() : [],
      values: Array.isArray(payload?.values)
        ? payload.values.map((value) => {
            const numeric = Number(value);
            return Number.isFinite(numeric) ? numeric : 0;
          })
        : [],
    };
    this.redraw();
  }

  redraw() {
    if (!this.canvas || !this.payload || this.payload.values.length === 0) {
      return;
    }
    const ctx = this.canvas.getContext('2d');
    if (!ctx) return;
    const cssWidth = this.canvas.clientWidth || this.canvas.offsetWidth || this.canvas.width;
    const cssHeight = this.canvas.clientHeight || this.canvas.offsetHeight || this.canvas.height;
    if (!cssWidth || !cssHeight) {
      return;
    }
    const dpr = window.devicePixelRatio || 1;
    const width = Math.max(1, Math.round(cssWidth * dpr));
    const height = Math.max(1, Math.round(cssHeight * dpr));
    if (this.canvas.width !== width || this.canvas.height !== height) {
      this.canvas.width = width;
      this.canvas.height = height;
    }
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, cssWidth, cssHeight);

    const palette = getPnlChartPalette();
    ctx.fillStyle = palette.canvasBg;
    ctx.fillRect(0, 0, cssWidth, cssHeight);

    const padding = this.variant === 'expanded'
      ? { top: 28, right: 28, bottom: 44, left: 72 }
      : { top: 16, right: 18, bottom: 32, left: 58 };
    const innerWidth = Math.max(1, cssWidth - padding.left - padding.right);
    const innerHeight = Math.max(1, cssHeight - padding.top - padding.bottom);

    let minValue = Math.min(0, ...this.payload.values);
    let maxValue = Math.max(0, ...this.payload.values);
    let range = maxValue - minValue;
    if (!Number.isFinite(range) || range <= 0) {
      const fallback = Math.max(Math.abs(maxValue), Math.abs(minValue), 1);
      minValue = minValue === maxValue ? minValue - fallback / 2 : minValue;
      maxValue = maxValue === minValue ? maxValue + fallback / 2 : maxValue;
      range = maxValue - minValue || fallback || 1;
    }

    const ySteps = this.variant === 'expanded' ? 5 : 4;
    ctx.strokeStyle = palette.gridLine;
    ctx.lineWidth = 1;
    ctx.font = `${this.variant === 'expanded' ? 13 : 11}px/1.2 var(--font-family, 'Inter', system-ui, sans-serif)`;
    ctx.fillStyle = palette.textMuted;
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    for (let step = 0; step <= ySteps; step += 1) {
      const ratio = step / ySteps;
      const y = padding.top + innerHeight - ratio * innerHeight;
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(padding.left + innerWidth, y);
      ctx.stroke();
      const value = minValue + range * ratio;
      ctx.fillText(value.toFixed(2), padding.left - 8, y);
    }

    const points = this.payload.values.map((value, index) => {
      const progress = this.payload.values.length === 1 ? 0 : index / (this.payload.values.length - 1);
      const x = padding.left + progress * innerWidth;
      const normalized = (value - minValue) / range;
      const clamped = Number.isFinite(normalized) ? Math.min(Math.max(normalized, 0), 1) : 0.5;
      const y = padding.top + (1 - clamped) * innerHeight;
      return {
        x,
        y,
        value,
        label: this.payload.labels[index] || `Trade ${index + 1}`,
      };
    });

    if (points.length === 0) return;

    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 1; i < points.length; i += 1) {
      ctx.lineTo(points[i].x, points[i].y);
    }
    ctx.lineTo(points[points.length - 1].x, padding.top + innerHeight);
    ctx.lineTo(points[0].x, padding.top + innerHeight);
    ctx.closePath();
    ctx.fillStyle = palette.accentSoft;
    ctx.fill();

    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 1; i < points.length; i += 1) {
      ctx.lineTo(points[i].x, points[i].y);
    }
    ctx.strokeStyle = palette.accent;
    ctx.lineWidth = 2;
    ctx.stroke();

    ctx.fillStyle = '#0c0d12';
    ctx.strokeStyle = palette.accent;
    const pointRadius = this.variant === 'expanded' ? 3 : 2.4;
    points.forEach((point) => {
      ctx.beginPath();
      ctx.arc(point.x, point.y, pointRadius, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
    });

    ctx.fillStyle = palette.textMuted;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.font = `${this.variant === 'expanded' ? 13 : 11}px/1.2 var(--font-family, 'Inter', system-ui, sans-serif)`;
    const labelIndexes = [];
    if (points.length > 0) labelIndexes.push(0);
    if (points.length > 2) labelIndexes.push(Math.floor((points.length - 1) / 2));
    if (points.length > 1) labelIndexes.push(points.length - 1);
    const seen = new Set();
    labelIndexes.forEach((index) => {
      if (seen.has(index)) return;
      seen.add(index);
      const point = points[index];
      ctx.fillText(point.label, point.x, padding.top + innerHeight + 6);
    });
  }
}

function handlePnlModalKeydown(event) {
  if (event.key === 'Escape') {
    closePnlModal();
  }
}

function openPnlModal() {
  if (!pnlChartModal || !pnlChartModalCanvas) return;
  if (!lastPnlChartPayload || !Array.isArray(lastPnlChartPayload.values) || lastPnlChartPayload.values.length === 0) {
    return;
  }

  const active = document.activeElement instanceof HTMLElement ? document.activeElement : null;
  pnlModalReturnTarget = active && active !== document.body ? active : pnlChartWrapper;

  if (pnlModalHideTimer) {
    clearTimeout(pnlModalHideTimer);
    pnlModalHideTimer = null;
  }

  if (pnlModalFinalizeHandler && pnlChartModal) {
    pnlChartModal.removeEventListener('transitionend', pnlModalFinalizeHandler);
    pnlModalFinalizeHandler = null;
  }

  if (pnlChartExpanded) {
    pnlChartExpanded.destroy();
    pnlChartExpanded = null;
  }

  pnlChartModal.removeAttribute('hidden');
  pnlChartModal.removeAttribute('aria-hidden');
  requestAnimationFrame(() => {
    pnlChartModal.classList.add('is-active');
  });
  document.body.classList.add('modal-open');

  pnlChartExpanded = new PnlCanvasChart(pnlChartModalCanvas, { variant: 'expanded' });
  pnlChartExpanded.render(lastPnlChartPayload);

  document.addEventListener('keydown', handlePnlModalKeydown);
  if (pnlChartModalClose) {
    setTimeout(() => pnlChartModalClose.focus(), 120);
  }
}

function closePnlModal() {
  if (!pnlChartModal) {
    return;
  }

  if (pnlModalHideTimer) {
    clearTimeout(pnlModalHideTimer);
    pnlModalHideTimer = null;
  }

  if (pnlModalFinalizeHandler) {
    pnlChartModal.removeEventListener('transitionend', pnlModalFinalizeHandler);
    pnlModalFinalizeHandler = null;
  }

  if (pnlChartModal.hasAttribute('hidden')) {
    return;
  }

  pnlChartModal.classList.remove('is-active');
  pnlChartModal.setAttribute('aria-hidden', 'true');
  document.body.classList.remove('modal-open');

  if (pnlChartExpanded) {
    pnlChartExpanded.destroy();
    pnlChartExpanded = null;
  }

  const finalize = () => {
    if (pnlModalHideTimer) {
      clearTimeout(pnlModalHideTimer);
      pnlModalHideTimer = null;
    }
    if (!pnlChartModal.hasAttribute('hidden')) {
      pnlChartModal.setAttribute('hidden', '');
    }
    if (pnlModalFinalizeHandler) {
      pnlChartModal.removeEventListener('transitionend', pnlModalFinalizeHandler);
      pnlModalFinalizeHandler = null;
    }
    const restoreTarget = pnlModalReturnTarget && typeof pnlModalReturnTarget.focus === 'function'
      ? pnlModalReturnTarget
      : pnlChartWrapper?.classList.contains('is-interactive')
        ? pnlChartWrapper
        : null;
    pnlModalReturnTarget = null;
    if (restoreTarget && typeof restoreTarget.focus === 'function') {
      restoreTarget.focus({ preventScroll: true });
    }
  };

  pnlModalFinalizeHandler = finalize;
  pnlChartModal.addEventListener('transitionend', finalize);
  pnlModalHideTimer = setTimeout(finalize, 280);

  document.removeEventListener('keydown', handlePnlModalKeydown);
}

function formatPnlSeriesLabel(rawLabel, fallbackIndex) {
  const labelIndex = Number.isFinite(fallbackIndex) ? fallbackIndex : 0;
  if (typeof rawLabel === 'string' && rawLabel.trim()) {
    const date = new Date(rawLabel);
    if (!Number.isNaN(date.getTime())) {
      return date.toLocaleString(undefined, {
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      });
    }
    return rawLabel;
  }
  if (Number.isFinite(rawLabel)) {
    const numeric = Number(rawLabel);
    const ms = numeric > 9_999_999_999 ? numeric : numeric * 1000;
    const date = new Date(ms);
    if (!Number.isNaN(date.getTime())) {
      return date.toLocaleString(undefined, {
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      });
    }
  }
  return `Trade ${labelIndex + 1}`;
}

function prepareServerPnlSeries(seriesPayload) {
  if (!seriesPayload || typeof seriesPayload !== 'object') return null;
  const rawValues = Array.isArray(seriesPayload.values) ? seriesPayload.values : [];
  const rawLabels = Array.isArray(seriesPayload.labels) ? seriesPayload.labels : [];
  if (rawValues.length === 0) return null;
  const labels = [];
  const values = [];
  rawValues.forEach((value, index) => {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return;
    const label = formatPnlSeriesLabel(rawLabels[index], labels.length);
    labels.push(label);
    values.push(Number(numeric));
  });
  if (values.length === 0) return null;
  return { labels, values };
}

function buildHistoryPnlSeries(history) {
  const entries = Array.isArray(history) ? history.slice() : [];
  const prepared = entries
    .map((trade) => {
      if (!trade || typeof trade !== 'object') return null;
      const pnl = extractRealizedPnl(trade);
      if (Number.isNaN(pnl)) return null;
      return { trade, pnl };
    })
    .filter(Boolean)
    .sort((a, b) => {
      const aDate = new Date(a.trade.closed_at_iso || a.trade.opened_at_iso || 0).getTime();
      const bDate = new Date(b.trade.closed_at_iso || b.trade.opened_at_iso || 0).getTime();
      return aDate - bDate;
    });

  if (prepared.length === 0) {
    return null;
  }

  const labels = [];
  const values = [];
  let cumulative = 0;
  for (const { trade, pnl } of prepared) {
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

  return { labels, values };
}

function renderPnlChart(history, seriesPayload) {
  if (!pnlChartCanvas) return;

  const payload = prepareServerPnlSeries(seriesPayload) || buildHistoryPnlSeries(history);

  if (!payload || payload.values.length === 0) {
    if (
      tradeHistoryEmptyStreak === 1 &&
      lastPnlChartPayload &&
      Array.isArray(lastPnlChartPayload.values) &&
      lastPnlChartPayload.values.length > 0
    ) {
      return;
    }
    if (pnlChart) {
      pnlChart.destroy();
      pnlChart = null;
    }
    lastPnlChartPayload = null;
    pnlChartCanvas.style.display = 'none';
    if (pnlEmptyState) {
      pnlEmptyState.style.display = 'flex';
    }
    if (pnlChartWrapper) {
      pnlChartWrapper.classList.remove('is-interactive');
      pnlChartWrapper.removeAttribute('tabindex');
      pnlChartWrapper.removeAttribute('role');
      pnlChartWrapper.removeAttribute('aria-label');
    }
    closePnlModal();
    return;
  }

  if (pnlEmptyState) {
    pnlEmptyState.style.display = 'none';
  }
  pnlChartCanvas.style.display = 'block';

  lastPnlChartPayload = {
    labels: payload.labels.slice(),
    values: payload.values.slice(),
  };

  if (pnlChartWrapper) {
    pnlChartWrapper.classList.add('is-interactive');
    pnlChartWrapper.setAttribute('tabindex', '0');
    pnlChartWrapper.setAttribute('role', 'button');
    pnlChartWrapper.setAttribute(
      'aria-label',
      translate('pnl.expandAria', 'Expand performance overview chart')
    );
  }

  if (!pnlChart) {
    pnlChart = new PnlCanvasChart(pnlChartCanvas);
  }
  pnlChart.render(lastPnlChartPayload);
}

function appendCompactLog({ line, level, ts }) {
  if (!compactLogStream) return;
  const friendly = humanizeLogLine(line, level);
  if (friendly?.refreshTrades) {
    scheduleTradesRefresh(250);
  }
  const timestampSeconds = Number.isFinite(ts)
    ? Number(ts)
    : friendly?.parsed?.timestamp
      ? Date.parse(friendly.parsed.timestamp) / 1000
      : undefined;
  if (friendly?.reason) {
    recordDecisionEvent(friendly.reason, {
      type: 'log',
      symbol: friendly.symbol,
      message: friendly.text,
      detail: friendly.detail,
      detailPairs: friendly.detailPairs ? friendly.detailPairs.map((entry) => ({ ...entry })) : null,
      occurredAt: Number.isFinite(timestampSeconds) ? timestampSeconds : undefined,
      occurredAtIso: friendly.parsed?.timestamp || null,
      parsed: friendly.parsed,
    });
    if (friendly.detailPairs && friendly.detailPairs.length > 0) {
      captureNearMissEvent(friendly, timestampSeconds);
    }
  }
  if (!friendly || !friendly.relevant) return;

  const candidateTimestamp = Number.isFinite(timestampSeconds)
    ? Number(timestampSeconds)
    : Date.now() / 1000;
  const isFewKlines = friendly.reason === 'few_klines';
  const skipKey = isFewKlines ? `${friendly.symbol || ''}::${friendly.reason}` : '';

  if (
    isFewKlines &&
    compactSkipAggregate &&
    compactSkipAggregate.key === skipKey &&
    compactSkipAggregate.element &&
    compactSkipAggregate.element.isConnected
  ) {
    const withinWindow = !compactSkipAggregate.lastTimestamp
      || candidateTimestamp - compactSkipAggregate.lastTimestamp <= COMPACT_SKIP_AGGREGATION_WINDOW;
    if (withinWindow) {
      compactSkipAggregate.count += 1;
      const messageEl = compactSkipAggregate.element.querySelector('.log-message');
      if (messageEl) {
        const base =
          compactSkipAggregate.baseText || messageEl.dataset.baseText || friendly.text || line;
        messageEl.dataset.baseText = base;
        messageEl.textContent = `${base} (x${compactSkipAggregate.count})`;
      }
      const timeEl = compactSkipAggregate.element.querySelector('.log-time');
      if (timeEl) {
        const dateObj = new Date(candidateTimestamp * 1000);
        if (!Number.isNaN(dateObj.getTime())) {
          timeEl.textContent = dateObj.toLocaleTimeString();
        }
      }
      compactSkipAggregate.lastTimestamp = candidateTimestamp;
      return;
    }
  }

  compactSkipAggregate = null;

  const severity = (friendly.severity || level || 'info').toLowerCase();
  const el = document.createElement('div');
  el.className = `log-line ${severity}`.trim();
  const classificationClasses = getLogClassList(friendly);
  if (classificationClasses.length > 0) {
    el.classList.add(...classificationClasses);
  }
  const normalizedLabel = (friendly.label || '').toString().toLowerCase();
  if (normalizedLabel.includes('skip')) {
    el.classList.add('is-skip');
  }
  if (normalizedLabel.includes('ai')) {
    el.classList.add('is-ai');
  }
  if (normalizedLabel.includes('trade')) {
    el.classList.add('is-trade');
  }
  const reasonKey = normaliseLogReasonKey(friendly.reason);
  if (reasonKey) {
    if (reasonKey.includes('skip')) {
      el.classList.add('is-skip');
    }
    if (reasonKey.startsWith('ai') || reasonKey.includes('policy')) {
      el.classList.add('is-ai');
    }
  }
  applyLogReasonStyles(el, friendly.reason);

  const meta = document.createElement('div');
  meta.className = 'log-meta';

  const displayTimestamp =
    Number.isFinite(timestampSeconds) || isFewKlines ? candidateTimestamp : undefined;
  if (displayTimestamp) {
    const time = document.createElement('span');
    time.className = 'log-time';
    time.textContent = new Date(displayTimestamp * 1000).toLocaleTimeString();
    meta.append(time);
  }

  const label = document.createElement('span');
  label.className = 'log-level';
  label.textContent = friendly.label || FRIENDLY_LEVEL_LABELS[severity] || severity.toUpperCase();
  meta.append(label);

  const message = document.createElement('div');
  message.className = 'log-message';
  message.dataset.baseText = friendly.text || line;
  message.textContent = friendly.text || line;

  el.append(meta, message);

  if (isFewKlines) {
    const note = document.createElement('div');
    note.className = 'log-note';
    note.textContent = translate(
      'logs.activity.waitingForCandlesNote',
      'Waiting for more recent candles on {{symbol}} before evaluating new trades.',
      { symbol: friendly.symbol || 'this market' }
    );
    el.append(note);
  }

  compactLogStream.append(el);

  if (isFewKlines) {
    compactSkipAggregate = {
      key: skipKey,
      element: el,
      count: 1,
      baseText: friendly.text || line,
      lastTimestamp: candidateTimestamp,
    };
  }

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

  const bannedTopKeys = new Set([
    'manual_request',
    'request_id',
    'decision_note',
    'risk_note',
    'explanation',
    'notes',
    'indicators',
    'bandit_features',
    'features',
  ]);

  const highlightKeys = new Set([
    'symbol',
    'asset',
    'ticker',
    'side',
    'direction',
    'decision',
    'take',
    'bucket',
    'policy_bucket',
    'confidence',
    'alpha_prob',
    'alpha_conf',
    'size_multiplier',
    'policy_size_multiplier',
    'sl_multiplier',
    'tp_multiplier',
    'decision_reason',
    'reason',
    'reason_label',
    'qty',
    'notional',
    'entry',
    'entry_price',
    'sl',
    'stop_loss',
    'tp',
    'take_profit',
    'expected_r',
    'expected_return',
    'timeframe',
  ]);

  const scalarEntries = [];
  Object.entries(record).forEach(([key, value]) => {
    if (bannedTopKeys.has(key)) return;
    if (value === null || value === undefined) return;
    if (typeof value === 'object') return;
    scalarEntries.push([key, value]);
  });
  const scalarMap = new Map(scalarEntries);

  const indicatorSource =
    record && typeof record.indicators === 'object' && record.indicators !== null
      ? record.indicators
      : null;
  const indicatorMap = new Map(
    indicatorSource ? Object.entries(indicatorSource).filter(([, value]) => value !== null && value !== undefined) : []
  );

  const featureSourceRaw =
    record && typeof record.bandit_features === 'object' && record.bandit_features !== null
      ? record.bandit_features
      : record && typeof record.features === 'object' && record.features !== null
        ? record.features
        : null;
  const featureMap = new Map(
    featureSourceRaw ? Object.entries(featureSourceRaw).filter(([, value]) => value !== null && value !== undefined) : []
  );

  const indicatorFormatting = {
    rsi: { label: 'RSI', digits: 1 },
    bb_position: { label: 'BB%', digits: 1, scale: 100 },
    bb_width: { label: 'BB width', digits: 4 },
    supertrend_dir: { label: 'Supertrend direction', digits: 1, signed: true },
    supertrend: { label: 'Supertrend', digits: 2 },
    stoch_rsi_d: { label: 'Stochastic %D', digits: 1 },
    stoch_rsi_k: { label: 'Stochastic %K', digits: 1 },
  };

  const featureFormatting = {
    atr_pct: { label: 'ATR %', digits: 2, scale: 100 },
    adx: { label: 'ADX', digits: 1 },
    slope_htf: { label: 'Slope (HTF)', digits: 3, signed: true },
    spread_bps: { label: 'Spread (bps)', digits: 1, scale: 10000 },
    funding: { label: 'Funding %', digits: 4, scale: 100, signed: true },
    qv_score: { label: 'Quiet volatility', digits: 2 },
    trend: { label: 'Trend', digits: 0, signed: true },
    regime_adx: { label: 'Regime ADX', digits: 1 },
    regime_slope: { label: 'Regime slope', digits: 3, signed: true },
  };

  const indicatorPriority = ['rsi', 'bb_position', 'bb_width', 'supertrend_dir', 'supertrend', 'stoch_rsi_d'];
  const featurePriority = ['atr_pct', 'adx', 'slope_htf', 'spread_bps', 'funding', 'qv_score', 'trend', 'regime_adx', 'regime_slope'];

  function firstText(keys) {
    for (const key of keys) {
      const value = record[key];
      if (typeof value === 'string') {
        const trimmed = value.trim();
        if (trimmed) {
          return trimmed;
        }
      }
    }
    return null;
  }

  function formatNumber(value, { digits = 2, signed = false, scale = 1, suffix = '' } = {}) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return '';
    const scaled = numeric * scale;
    let text = scaled.toFixed(digits);
    if (signed && scaled > 0) {
      text = `+${text}`;
    }
    return suffix ? `${text}${suffix}` : text;
  }

  function formatBoolean(value) {
    return value ? 'yes' : 'no';
  }

  function formatGeneralScalar(key, value) {
    if (typeof value === 'boolean') {
      return `${toTitleWords(key)} ${formatBoolean(value)}`;
    }
    const numeric = Number(value);
    if (Number.isFinite(numeric)) {
      const digits = Math.abs(numeric) >= 100 ? 0 : Math.abs(numeric) >= 10 ? 1 : 2;
      return `${toTitleWords(key)} ${numeric.toFixed(digits)}`;
    }
    return `${toTitleWords(key)} ${String(value)}`;
  }

  const sentences = [];

  const symbol = firstText(['symbol', 'asset', 'ticker']);
  const side = firstText(['side', 'direction']);
  const decision = firstText(['decision']);
  const bucket = firstText(['bucket', 'policy_bucket']);
  const takeValue = Object.prototype.hasOwnProperty.call(record, 'take') ? record.take : null;
  const actionText = typeof takeValue === 'boolean' ? (takeValue ? 'enter the trade' : 'skip the trade') : '';
  const summaryParts = [];
  if (symbol) {
    summaryParts.push(symbol.toUpperCase());
    scalarMap.delete('symbol');
  }
  if (side) {
    summaryParts.push(side.toUpperCase());
    scalarMap.delete('side');
  }
  const decisionParts = [];
  if (decision) {
    decisionParts.push(decision.toUpperCase());
    scalarMap.delete('decision');
  }
  if (actionText) {
    decisionParts.push(actionText);
    scalarMap.delete('take');
  }
  if (decisionParts.length > 0) {
    summaryParts.push(decisionParts.join(' — '));
  }
  if (bucket) {
    summaryParts.push(`bucket ${bucket}`);
    scalarMap.delete('bucket');
    scalarMap.delete('policy_bucket');
  }
  if (summaryParts.length > 0) {
    sentences.push(`${summaryParts.join(', ')}.`);
  }

  const reasonLabel =
    firstText(['reason_label']) ||
    (record.decision_reason ? friendlyReason(record.decision_reason) : null) ||
    firstText(['reason']);
  if (reasonLabel) {
    sentences.push(`Reason: ${reasonLabel}.`);
    scalarMap.delete('reason_label');
    scalarMap.delete('decision_reason');
    scalarMap.delete('reason');
  }

  const confidenceParts = [];
  if (Number.isFinite(Number(record.confidence))) {
    confidenceParts.push(`confidence ${formatNumber(record.confidence)}`);
    scalarMap.delete('confidence');
  }
  if (Number.isFinite(Number(record.alpha_prob))) {
    confidenceParts.push(`alpha probability ${formatNumber(record.alpha_prob, { digits: 3 })}`);
    scalarMap.delete('alpha_prob');
  }
  if (Number.isFinite(Number(record.alpha_conf))) {
    confidenceParts.push(`model confidence ${formatNumber(record.alpha_conf)}`);
    scalarMap.delete('alpha_conf');
  }
  if (confidenceParts.length > 0) {
    sentences.push(`Confidence metrics: ${confidenceParts.join(', ')}.`);
  }

  const multiplierParts = [];
  const sizeMultiplier =
    Number.isFinite(Number(record.size_multiplier))
      ? Number(record.size_multiplier)
      : Number(record.policy_size_multiplier);
  if (Number.isFinite(Number(sizeMultiplier))) {
    multiplierParts.push(`size ×${formatNumber(sizeMultiplier, { digits: 2 })}`);
    scalarMap.delete('size_multiplier');
    scalarMap.delete('policy_size_multiplier');
  }
  if (Number.isFinite(Number(record.sl_multiplier))) {
    multiplierParts.push(`stop-loss ×${formatNumber(record.sl_multiplier, { digits: 2 })}`);
    scalarMap.delete('sl_multiplier');
  }
  if (Number.isFinite(Number(record.tp_multiplier))) {
    multiplierParts.push(`take-profit ×${formatNumber(record.tp_multiplier, { digits: 2 })}`);
    scalarMap.delete('tp_multiplier');
  }
  if (multiplierParts.length > 0) {
    sentences.push(`Sizing multipliers: ${multiplierParts.join(', ')}.`);
  }

  const tradeLevels = [];
  const entryPrice =
    Number.isFinite(Number(record.entry))
      ? Number(record.entry)
      : Number.isFinite(Number(record.entry_price))
        ? Number(record.entry_price)
        : null;
  if (Number.isFinite(entryPrice)) {
    tradeLevels.push(`entry ${formatNumber(entryPrice, { digits: 4 })}`);
    scalarMap.delete('entry');
    scalarMap.delete('entry_price');
  }
  const stopPrice =
    Number.isFinite(Number(record.sl))
      ? Number(record.sl)
      : Number.isFinite(Number(record.stop_loss))
        ? Number(record.stop_loss)
        : null;
  if (Number.isFinite(stopPrice)) {
    tradeLevels.push(`stop ${formatNumber(stopPrice, { digits: 4 })}`);
    scalarMap.delete('sl');
    scalarMap.delete('stop_loss');
  }
  const targetPrice =
    Number.isFinite(Number(record.tp))
      ? Number(record.tp)
      : Number.isFinite(Number(record.take_profit))
        ? Number(record.take_profit)
        : null;
  if (Number.isFinite(targetPrice)) {
    tradeLevels.push(`target ${formatNumber(targetPrice, { digits: 4 })}`);
    scalarMap.delete('tp');
    scalarMap.delete('take_profit');
  }
  if (tradeLevels.length > 0) {
    sentences.push(`Trade levels: ${tradeLevels.join(', ')}.`);
  }

  const quantityParts = [];
  if (Number.isFinite(Number(record.qty))) {
    quantityParts.push(`quantity ${formatNumber(record.qty, { digits: 4 })}`);
    scalarMap.delete('qty');
  }
  if (Number.isFinite(Number(record.notional))) {
    quantityParts.push(`notional ${formatNumber(record.notional, { digits: 2 })}`);
    scalarMap.delete('notional');
  }
  const timeframe = firstText(['timeframe']);
  if (timeframe) {
    quantityParts.push(`timeframe ${timeframe}`);
    scalarMap.delete('timeframe');
  }
  if (Number.isFinite(Number(record.expected_r))) {
    quantityParts.push(`expected return ${formatNumber(record.expected_r, { digits: 2, signed: true })}`);
    scalarMap.delete('expected_r');
  } else if (Number.isFinite(Number(record.expected_return))) {
    quantityParts.push(`expected return ${formatNumber(record.expected_return, { digits: 2, signed: true })}`);
    scalarMap.delete('expected_return');
  }
  if (quantityParts.length > 0) {
    sentences.push(`Position outline: ${quantityParts.join(', ')}.`);
  }

  function consumeMapEntries(sourceMap, priorityKeys, formatting, label) {
    const fragments = [];

    function consume(key) {
      if (!sourceMap.has(key)) return;
      const fmt = formatting[key] || {};
      const rendered = formatNumber(sourceMap.get(key), fmt);
      if (!rendered) {
        sourceMap.delete(key);
        return;
      }
      const prefix = fmt.label || toTitleWords(key);
      fragments.push(`${prefix} ${rendered}`);
      sourceMap.delete(key);
    }

    priorityKeys.forEach((key) => consume(key));

    for (const key of Array.from(sourceMap.keys())) {
      if (fragments.length >= 6) break;
      consume(key);
    }

    if (fragments.length > 0) {
      sentences.push(`${label}: ${fragments.join(', ')}.`);
    }
  }

  consumeMapEntries(indicatorMap, indicatorPriority, indicatorFormatting, 'Indicator snapshot');
  consumeMapEntries(featureMap, featurePriority, featureFormatting, 'Model inputs');

  const extraItems = [];
  for (const [key, value] of scalarMap.entries()) {
    if (highlightKeys.has(key)) continue;
    extraItems.push(formatGeneralScalar(key, value));
    if (extraItems.length >= 6) break;
  }
  if (extraItems.length > 0) {
    sentences.push(`Additional data: ${extraItems.join(', ')}.`);
  }

  return sentences.join(' ');
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

function isUnlimitedLeverage(value) {
  if (value === undefined || value === null) return false;
  const token = value.toString().trim().toLowerCase();
  return token === 'max' || token === 'unlimited' || token === '∞' || token === 'inf';
}

function numbersDiffer(a, b, tolerance = 1e-6) {
  const numA = Number(a);
  const numB = Number(b);
  const aValid = Number.isFinite(numA);
  const bValid = Number.isFinite(numB);
  if (!aValid && !bValid) return false;
  if (!aValid || !bValid) return true;
  return Math.abs(numA - numB) > tolerance;
}

function getPresetScaling(preset) {
  if (!preset) {
    return { safeRisk: 1, safeLeverage: 1, ratio: 1, unlimited: false };
  }
  const riskMin = riskSlider ? Number(riskSlider.min) : 0.25;
  const riskMax = riskSlider ? Number(riskSlider.max) : 100;
  const leverageMin = leverageSlider ? Number(leverageSlider.min) : 1;
  const leverageMax = leverageSlider ? Number(leverageSlider.max) : 5;
  const rawRisk = riskSlider ? Number(riskSlider.value) : Number(preset.risk ?? 1);
  const presetUnlimited = isUnlimitedLeverage(preset.leverage);
  const sliderUnlimited = leverageSlider ? leverageSlider.dataset.unlimited === 'true' : false;
  const unlimited = presetUnlimited || sliderUnlimited;
  const sliderMaxValue = leverageSlider ? Number(leverageSlider.max) : leverageMax;
  const rawLeverage = unlimited
    ? sliderMaxValue
    : leverageSlider
    ? Number(leverageSlider.value)
    : Number(preset.leverage ?? 1);
  const safeRisk = clampValue(rawRisk, riskMin, riskMax);
  const safeLeverage = unlimited
    ? sliderMaxValue
    : clampValue(rawLeverage, leverageMin, leverageMax);
  const baselineRisk = Number(preset.risk ?? 1) || 1;
  const ratio = clampValue(baselineRisk > 0 ? safeRisk / baselineRisk : 1, 0.2, 4);
  return { safeRisk, safeLeverage, ratio, unlimited };
}

function getEnvNumber(env, key, fallback) {
  if (!env || env[key] === undefined || env[key] === null || env[key] === '') {
    return fallback;
  }
  const numeric = Number(env[key]);
  return Number.isFinite(numeric) ? numeric : fallback;
}

function getEnvBoolean(env, key, fallback) {
  if (!env || env[key] === undefined || env[key] === null || env[key] === '') {
    return fallback;
  }
  return isTruthy(env[key]);
}

function formatFundingRate(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return '–';
  const percent = numeric * 100;
  const digits = Math.abs(percent) >= 0.1 ? 2 : 3;
  return `${percent.toFixed(digits)}%`;
}

function formatMultiplierValue(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return '–';
  return `${numeric.toFixed(2)}×`;
}

function appendPresetMetaItem(list, { label, value, detail, note }) {
  if (!list) return;
  const item = document.createElement('li');
  if (label) {
    const labelEl = document.createElement('span');
    labelEl.className = 'preset-meta-label';
    labelEl.textContent = label;
    item.append(labelEl);
  }
  if (value) {
    const valueEl = document.createElement('span');
    valueEl.className = 'preset-meta-value';
    valueEl.textContent = value;
    item.append(valueEl);
  }
  if (detail) {
    const detailEl = document.createElement('span');
    detailEl.className = 'preset-meta-detail';
    detailEl.textContent = detail;
    item.append(detailEl);
  }
  if (note) {
    const noteEl = document.createElement('span');
    noteEl.className = 'preset-meta-note';
    noteEl.textContent = note;
    item.append(noteEl);
  }
  list.append(item);
}

function renderPresetMeta(presetKey = selectedPreset) {
  const preset = PRESETS[presetKey];
  if (!preset || (!presetFundingDetails && !presetMlDetails)) return;

  const env = currentConfig?.env ?? {};
  const { ratio, unlimited, safeLeverage } = getPresetScaling(preset);
  if (presetLeverageDetails) {
    if (unlimited || isUnlimitedLeverage(preset.leverage)) {
      presetLeverageDetails.textContent = 'Leverage base: exchange maximum (auto-detected per symbol).';
    } else {
      const baseLev = Number(preset.leverage ?? safeLeverage ?? 0);
      const display = Number.isFinite(baseLev) && baseLev > 0 ? `${Math.round(baseLev)}×` : `${Math.round(safeLeverage)}×`;
      presetLeverageDetails.textContent = `Leverage base: ${display} (capped by symbol limits).`;
    }
  }

  if (presetNotionalDetails) {
    const coerce = (value) => {
      if (value === undefined || value === null) return NaN;
      const numeric = Number(value);
      return Number.isFinite(numeric) ? numeric : NaN;
    };
    const minValue = coerce(preset?.notional?.min);
    const maxValue = coerce(preset?.notional?.max);
    const unlimitedLabel = translate('quick.notional.unlimited', 'account equity');
    const minDisplay = Number.isFinite(minValue)
      ? `${formatNumber(minValue, minValue >= 100 ? 0 : 2)} USDT`
      : unlimitedLabel;
    const maxDisplay = Number.isFinite(maxValue)
      ? `${formatNumber(maxValue, maxValue >= 100 ? 0 : 2)} USDT`
      : unlimitedLabel;
    presetNotionalDetails.textContent = translate(
      'quick.notional.details',
      'Adaptive position size: {{min}} – {{max}} per trade.',
      { min: minDisplay, max: maxDisplay },
    );
  }

  const fundingTarget = {
    enabled: preset.funding?.enabled !== false,
    maxLong: Number(preset.funding?.maxLong ?? 0.001),
    maxShort: Number(preset.funding?.maxShort ?? 0.001),
  };
  const fundingCurrent = {
    enabled: getEnvBoolean(env, 'ASTER_FUNDING_FILTER_ENABLED', fundingTarget.enabled),
    maxLong: getEnvNumber(env, 'ASTER_FUNDING_MAX_LONG', fundingTarget.maxLong),
    maxShort: getEnvNumber(env, 'ASTER_FUNDING_MAX_SHORT', fundingTarget.maxShort),
  };

  if (presetFundingDetails) {
    let text;
    if (fundingTarget.enabled) {
      text = `Enabled · Long cap ${formatFundingRate(fundingTarget.maxLong)} · Short cap ${formatFundingRate(fundingTarget.maxShort)}`;
    } else {
      text = 'Disabled — trades ignore funding drift for this preset.';
    }
    const differs =
      fundingCurrent.enabled !== fundingTarget.enabled ||
      numbersDiffer(fundingCurrent.maxLong, fundingTarget.maxLong, 1e-5) ||
      numbersDiffer(fundingCurrent.maxShort, fundingTarget.maxShort, 1e-5);
    if (differs) {
      const currentSummary = fundingCurrent.enabled
        ? `${formatFundingRate(fundingCurrent.maxLong)} / ${formatFundingRate(fundingCurrent.maxShort)}`
        : 'disabled';
      presetFundingDetails.innerHTML = `${text} <span class="preset-meta-note">Current: ${currentSummary}</span>`;
    } else {
      presetFundingDetails.textContent = text;
    }
  }

  if (presetMlDetails) {
    presetMlDetails.innerHTML = '';
    const banditTargetEnabled = preset.banditEnabled !== false;
    const alphaTargetEnabled = preset.alphaEnabled !== false;

    const sizeTarget = {
      base: Number(preset.sizeMult?.base ?? 1) * ratio,
      s: Number(preset.sizeMult?.s ?? preset.sizeMult?.base ?? 1) * ratio,
      m: Number(preset.sizeMult?.m ?? 1.4) * ratio,
      l: Number(preset.sizeMult?.l ?? 1.9) * ratio,
    };
    const sizeCurrent = {
      base: getEnvNumber(env, 'ASTER_SIZE_MULT', sizeTarget.base),
      s: getEnvNumber(env, 'ASTER_SIZE_MULT_S', sizeTarget.s),
      m: getEnvNumber(env, 'ASTER_SIZE_MULT_M', sizeTarget.m),
      l: getEnvNumber(env, 'ASTER_SIZE_MULT_L', sizeTarget.l),
    };
    const banditCurrentEnabled = getEnvBoolean(env, 'ASTER_BANDIT_ENABLED', banditTargetEnabled);

    const banditDetail = banditTargetEnabled
      ? `Target buckets — S ${formatMultiplierValue(sizeTarget.s)} · M ${formatMultiplierValue(sizeTarget.m)} · L ${formatMultiplierValue(sizeTarget.l)}`
      : 'Target preset disables ML gating for entries.';

    let banditNote = '';
    if (
      banditCurrentEnabled !== banditTargetEnabled ||
      numbersDiffer(sizeTarget.s, sizeCurrent.s, 1e-3) ||
      numbersDiffer(sizeTarget.m, sizeCurrent.m, 1e-3) ||
      numbersDiffer(sizeTarget.l, sizeCurrent.l, 1e-3)
    ) {
      if (banditCurrentEnabled) {
        banditNote = `Current: S ${formatMultiplierValue(sizeCurrent.s)} · M ${formatMultiplierValue(sizeCurrent.m)} · L ${formatMultiplierValue(sizeCurrent.l)}`;
      } else {
        banditNote = 'Current: disabled';
      }
    }

    appendPresetMetaItem(presetMlDetails, {
      label: 'Bandit gate',
      value: banditTargetEnabled ? 'Enabled' : 'Disabled',
      detail: banditDetail,
      note: banditNote,
    });

    const alphaTarget = {
      threshold: Number(preset.alpha?.threshold ?? 0.55),
      minConf: Number(preset.alpha?.minConf ?? 0.2),
      promoteDelta: Number(preset.alpha?.promoteDelta ?? 0.15),
      rewardMargin: Number(preset.alpha?.rewardMargin ?? 0.05),
      warmup: Number(preset.alphaWarmup ?? 40),
    };
    const alphaCurrentEnabled = getEnvBoolean(env, 'ASTER_ALPHA_ENABLED', alphaTargetEnabled);
    const alphaCurrent = {
      threshold: getEnvNumber(env, 'ASTER_ALPHA_THRESHOLD', alphaTarget.threshold),
      minConf: getEnvNumber(env, 'ASTER_ALPHA_MIN_CONF', alphaTarget.minConf),
      promoteDelta: getEnvNumber(env, 'ASTER_ALPHA_PROMOTE_DELTA', alphaTarget.promoteDelta),
      rewardMargin: getEnvNumber(env, 'ASTER_ALPHA_REWARD_MARGIN', alphaTarget.rewardMargin),
      warmup: getEnvNumber(env, 'ASTER_ALPHA_WARMUP', alphaTarget.warmup),
    };

    const alphaDetail = alphaTargetEnabled
      ? `Target — threshold ${formatNumber(alphaTarget.threshold, 2)}, min conf ${formatNumber(alphaTarget.minConf, 2)}, promote Δ ${formatNumber(alphaTarget.promoteDelta, 2)}, warmup ${Math.round(alphaTarget.warmup)} trades`
      : 'Target preset disables the alpha filter.';

    let alphaNote = '';
    if (
      alphaCurrentEnabled !== alphaTargetEnabled ||
      numbersDiffer(alphaCurrent.threshold, alphaTarget.threshold, 1e-4) ||
      numbersDiffer(alphaCurrent.minConf, alphaTarget.minConf, 1e-4) ||
      numbersDiffer(alphaCurrent.promoteDelta, alphaTarget.promoteDelta, 1e-4) ||
      numbersDiffer(alphaCurrent.warmup, alphaTarget.warmup, 0.5)
    ) {
      if (alphaCurrentEnabled) {
        alphaNote = `Current — threshold ${formatNumber(alphaCurrent.threshold, 2)}, min conf ${formatNumber(alphaCurrent.minConf, 2)}, promote Δ ${formatNumber(alphaCurrent.promoteDelta, 2)}, warmup ${Math.round(alphaCurrent.warmup)} trades`;
      } else {
        alphaNote = 'Current: disabled';
      }
    }

    appendPresetMetaItem(presetMlDetails, {
      label: 'Alpha filter',
      value: alphaTargetEnabled ? 'Enabled' : 'Disabled',
      detail: alphaDetail,
      note: alphaNote,
    });

    if (alphaTargetEnabled) {
      let rewardNote = '';
      if (numbersDiffer(alphaCurrent.rewardMargin, alphaTarget.rewardMargin, 1e-4)) {
        rewardNote = `Current: ${formatNumber(alphaCurrent.rewardMargin, 2)} R`;
      }
      appendPresetMetaItem(presetMlDetails, {
        label: 'Alpha reward',
        value: `${formatNumber(alphaTarget.rewardMargin, 2)} R`,
        detail: 'Minimum realised edge needed to reinforce the model.',
        note: rewardNote,
      });
    }

    if (!presetMlDetails.children.length) {
      const empty = document.createElement('li');
      empty.className = 'preset-meta-empty';
      empty.textContent = translate('quick.ml.none', 'No ML policy details available for this preset.');
      presetMlDetails.append(empty);
    }
  }
}

function refreshPresetMeta() {
  renderPresetMeta(selectedPreset);
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
  if (leverageSlider.dataset.unlimited === 'true') {
    leverageValue.textContent = '∞';
    setRangeBackground(leverageSlider);
    return;
  }
  const numeric = Number(leverageSlider.value);
  leverageValue.textContent = `${numeric.toFixed(0)}×`;
  setRangeBackground(leverageSlider);
}

function resetQuickConfigButton() {
  quickConfigPristine = true;
  if (btnApplyPreset && !btnApplyPreset.disabled) {
    btnApplyPreset.textContent = translate('quick.apply', 'Apply preset');
  }
  if (btnApplyPreset) {
    btnApplyPreset.dataset.state = 'idle';
  }
}

function markQuickConfigDirty() {
  quickConfigPristine = false;
  if (btnApplyPreset && !btnApplyPreset.disabled) {
    btnApplyPreset.textContent = translate('quick.applyChanges', 'Apply changes');
  }
  if (btnApplyPreset) {
    btnApplyPreset.dataset.state = 'dirty';
  }
}

function buildQuickSetupPayload() {
  const presetKey = PRESETS[selectedPreset] ? selectedPreset : 'mid';
  const preset = PRESETS[presetKey];
  const { safeRisk, safeLeverage, ratio, unlimited } = getPresetScaling(preset);

  const payload = {
    ASTER_PRESET_MODE: presetKey,
    ASTER_RISK_PER_TRADE: toFixedString(safeRisk / 100, 4),
    ASTER_LEVERAGE: unlimited ? 'max' : toFixedString(safeLeverage, 0),
    ASTER_RISK_PROFILE: preset.riskProfile || 'balanced',
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
    ASTER_MAX_OPEN_GLOBAL: toFixedString(preset.maxOpenGlobal ?? 0, 0),
    ASTER_MAX_OPEN_PER_SYMBOL: toFixedString(preset.maxOpenPerSymbol ?? 1, 0),
    ASTER_FUNDING_FILTER_ENABLED: preset?.funding?.enabled === false ? 'false' : 'true',
    ASTER_FUNDING_MAX_LONG: toFixedString(preset?.funding?.maxLong ?? 0.001, 4),
    ASTER_FUNDING_MAX_SHORT: toFixedString(preset?.funding?.maxShort ?? 0.001, 4),
    ASTER_BANDIT_ENABLED: preset?.banditEnabled === false ? 'false' : 'true',
    ASTER_ALPHA_ENABLED: preset?.alphaEnabled === false ? 'false' : 'true',
    ASTER_ALPHA_THRESHOLD: toFixedString(preset.alpha.threshold, 2),
    ASTER_ALPHA_MIN_CONF: toFixedString(preset.alpha.minConf, 2),
    ASTER_ALPHA_PROMOTE_DELTA: toFixedString(preset.alpha.promoteDelta, 2),
    ASTER_ALPHA_REWARD_MARGIN: toFixedString(preset.alpha.rewardMargin, 2),
    ASTER_ALPHA_WARMUP: toFixedString(preset?.alphaWarmup ?? 40, 0),
  };

  if (preset.unlimitedBudget) {
    payload.ASTER_AI_DAILY_BUDGET_USD = '0';
  }

  if (inputDefaultNotional) {
    const value = inputDefaultNotional.value.trim();
    if (value !== '') {
      const numeric = Number(value);
      if (Number.isFinite(numeric) && numeric >= 0) {
        payload.ASTER_DEFAULT_NOTIONAL = numeric.toString();
      }
    } else if (currentConfig?.env?.ASTER_DEFAULT_NOTIONAL !== undefined) {
      payload.ASTER_DEFAULT_NOTIONAL = currentConfig.env.ASTER_DEFAULT_NOTIONAL;
    }
  }

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
  if (leverageSlider && env.ASTER_LEVERAGE !== undefined && env.ASTER_LEVERAGE !== null) {
    const raw = env.ASTER_LEVERAGE.toString();
    const sliderMax = leverageSlider.max || '5';
    if (isUnlimitedLeverage(raw)) {
      leverageSlider.dataset.unlimited = 'true';
      leverageSlider.disabled = true;
      leverageSlider.value = sliderMax;
    } else {
      leverageSlider.dataset.unlimited = 'false';
      leverageSlider.disabled = false;
      const lev = clampValue(Number(raw), Number(leverageSlider.min), Number(leverageSlider.max));
      leverageSlider.value = lev.toString();
    }
    updateLeverageValue();
  }
  updateDefaultNotionalInputs(env?.ASTER_DEFAULT_NOTIONAL);
  updateRiskValue();
  updateLeverageValue();
  refreshPresetMeta();
  resetQuickConfigButton();
}

async function saveQuickSetup() {
  if (!btnApplyPreset) return;
  const restoreMode = lastModeBeforeStandard;
  const payload = buildQuickSetupPayload();
  btnApplyPreset.disabled = true;
  btnApplyPreset.textContent = translate('quick.applyProgress', 'Applying…');
  btnApplyPreset.dataset.state = 'applying';
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
      restarted = await restartBotIfNeeded({ restoreMode });
    } catch (restartErr) {
      throw new Error(`Bot restart failed: ${restartErr.message}`);
    }
    btnApplyPreset.textContent = restarted
      ? translate('quick.applyRestarted', 'Restarted ✓')
      : translate('quick.applySuccess', 'Applied ✓');
    btnApplyPreset.dataset.state = restarted ? 'restarted' : 'applied';
    setTimeout(() => {
      if (btnApplyPreset && !btnApplyPreset.disabled) {
        resetQuickConfigButton();
      }
    }, 1800);
  } catch (err) {
    btnApplyPreset.textContent = translate('quick.applyError', 'Error');
    btnApplyPreset.dataset.state = 'error';
    alert(err.message);
    setTimeout(() => {
      if (btnApplyPreset && !btnApplyPreset.disabled) {
        btnApplyPreset.textContent = translate('quick.applyChanges', 'Apply changes');
        btnApplyPreset.dataset.state = 'dirty';
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
    const summary = `${preset.label} preset: ${preset.summary}`;
    presetDescription.textContent = preset.unlimitedBudget ? `${summary} (AI budget: unlimited).` : summary;
  }
  if (riskSlider) {
    riskSlider.value = preset.risk.toString();
  }
  if (leverageSlider) {
    const unlimitedPreset = isUnlimitedLeverage(preset.leverage);
    leverageSlider.dataset.unlimited = unlimitedPreset ? 'true' : 'false';
    leverageSlider.disabled = unlimitedPreset;
    const sliderMax = leverageSlider.max || '5';
    leverageSlider.value = unlimitedPreset
      ? sliderMax
      : Number(preset.leverage ?? leverageSlider.value).toString();
  }
  updateRiskValue();
  updateLeverageValue();
  refreshPresetMeta();
  if (!silent) {
    markQuickConfigDirty();
  }
}

function setAiMode(state) {
  aiMode = Boolean(state);
  if (!aiMode) {
    stopAutomation();
  }
  document.body.classList.toggle('ai-mode', aiMode);
  renderAiBudget(lastAiBudget);
  renderPlaybookOverview(
    lastPlaybookState,
    lastPlaybookActivity,
    lastPlaybookProcess,
    lastPlaybookMarketOverview,
  );
  syncAiChatAvailability();
}

function setPaperMode(state) {
  paperMode = Boolean(state);
  if (document.body) {
    document.body.classList.toggle('paper-mode', paperMode);
  }
  if (paperModeToggle) {
    paperModeToggle.checked = paperMode;
  }
  updateActivePositionsView();
}

async function syncModeFromEnv(env) {
  lastModeBeforeStandard = null;
  const raw = (env?.ASTER_MODE || '').toString().toLowerCase();
  if (raw === 'ai') {
    await selectMode('ai', { persist: false });
  } else if (raw === 'pro') {
    await selectMode('pro', { persist: false });
  } else {
    await selectMode('standard', { persist: false });
  }
}

function syncPaperModeFromEnv(env) {
  const raw = env?.ASTER_PAPER;
  setPaperMode(isTruthy(raw));
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
  syncPaperModeFromEnv(currentConfig.env);
}

async function selectMode(mode, options = {}) {
  const { persist = false } = options;
  const target = (mode || '').toString().toLowerCase();
  const current = getCurrentMode();
  if (!['standard', 'pro', 'ai'].includes(target) || target === current) {
    return;
  }

  const previous = current;
  if (target === 'standard' && previous !== 'standard') {
    lastModeBeforeStandard = previous;
  } else if (target !== 'standard') {
    lastModeBeforeStandard = null;
  }
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

async function persistPaperMode(enabled) {
  const payload = { env: { ASTER_PAPER: enabled ? 'true' : 'false' } };
  const res = await fetch('/api/config', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || 'Unable to update paper mode');
  }
  currentConfig = await res.json();
  renderConfig(currentConfig.env);
  renderCredentials(currentConfig.env);
  syncQuickSetupFromEnv(currentConfig.env);
  await syncModeFromEnv(currentConfig.env);
  syncPaperModeFromEnv(currentConfig.env);
}

async function executeTradeProposal(proposalId) {
  const res = await fetch('/api/ai/proposals/execute', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ proposalId }),
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
    throw new Error(detail || translate('chat.proposal.statusFailed', 'Failed to place trade proposal.'));
  }
  const payload = data && typeof data === 'object' ? data.proposal || {} : {};
  registerTradeProposal(payload);
  return payload;
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
      cumulative_stats: snapshot?.cumulative_stats ?? {},
      history_summary: snapshot?.history_summary ?? null,
      hero_metrics: snapshot?.hero_metrics ?? null,
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
  if (tradesRefreshInFlight) {
    return tradesRefreshInFlight;
  }

  const previousSnapshot = latestTradesSnapshot;

  const refreshPromise = (async () => {
    try {
      const res = await fetch('/api/trades');
      if (!res.ok) throw new Error('Unable to load trades');
      const data = await res.json();
      const snapshot = mergeTradeSnapshot(previousSnapshot, data);
      latestTradesSnapshot = snapshot;
      tradesHydrated = true;
      setTradeDataStale(false);
      renderTradeHistory(snapshot.history);
      renderTradeSummary(snapshot.stats, snapshot.history_summary);
      if (!completedPositionsHistory.length) {
        syncCompletedPositionsStats(snapshot.history_summary || snapshot.stats);
        setTradeSummaryOverride(null);
      }
      renderHeroMetrics(
        snapshot.cumulative_stats,
        snapshot.stats,
        snapshot.history,
        snapshot.hero_metrics,
        snapshot.open ?? snapshot.open_positions ?? null,
        snapshot.history_summary,
      );
      renderDecisionStats(snapshot.decision_stats);
      renderPnlChart(snapshot.history, snapshot.pnl_series);
      renderAiBudget(snapshot.ai_budget);
      renderAiRequests(snapshot.ai_requests);
      renderPlaybookOverview(
        snapshot.playbook,
        snapshot.playbook_activity,
        snapshot.playbook_process,
        snapshot.playbook_market_overview,
      );
      const exchangePositions = Array.isArray(snapshot.exchange_positions)
        ? snapshot.exchange_positions
        : [];
      if (exchangePositions.length > 0) {
        syncExchangeCompletedPositions(exchangePositions);
      }
      applyActivePositionsPayload(snapshot.open, { syncSnapshot: false });
      const proposals = Array.isArray(snapshot.ai_trade_proposals)
        ? snapshot.ai_trade_proposals
        : [];
      proposals.forEach((proposal) => appendTradeProposalCard(proposal));
      pruneTradeProposalRegistry(proposals);
      return snapshot;
    } catch (err) {
      console.warn('Failed to refresh dashboard data', err);
      if (previousSnapshot && tradesHydrated) {
        setTradeDataStale(true);
        return previousSnapshot;
      }
      return null;
    } finally {
      tradesRefreshInFlight = null;
    }
  })();

  tradesRefreshInFlight = refreshPromise;
  return refreshPromise;
}

async function handleTakeTradeProposals() {
  const pending = getPendingTradeProposals();
  if (pending.length === 0) {
    setChatStatus(getTakeProposalsEmptyLabel());
    updateTakeProposalsButtonState();
    return;
  }
  if (btnTakeTradeProposals) {
    btnTakeTradeProposals.dataset.state = 'working';
    updateTakeProposalsButtonState();
  }
  setChatStatus(getTakeProposalsWorkingLabel());
  const errors = [];
  for (const proposal of pending) {
    try {
      const payload = await executeTradeProposal(proposal.id);
      appendTradeProposalCard(payload);
    } catch (err) {
      errors.push(err);
      break;
    }
  }
  if (btnTakeTradeProposals) {
    btnTakeTradeProposals.dataset.state = 'idle';
    updateTakeProposalsButtonState();
  } else {
    updateTakeProposalsButtonState();
  }
  if (errors.length > 0) {
    const firstError = errors[0];
    const message = (firstError?.message || '').trim() || getTakeProposalsHintLabel();
    setChatStatus(message);
    return;
  }
  try {
    await loadTrades();
  } catch (err) {
    console.warn('Failed to refresh trades after executing proposals', err);
  }
  setChatStatus(getTakeProposalsSuccessLabel());
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

async function restartBotIfNeeded(options = {}) {
  const { restoreMode = null } = options;
  const currentMode = getCurrentMode();
  const normalizedRestore = typeof restoreMode === 'string' ? restoreMode.toLowerCase() : null;
  const wantsRestore = normalizedRestore && normalizedRestore !== 'standard';

  if (currentMode !== 'standard' && !wantsRestore) {
    return false;
  }

  if (wantsRestore && currentMode !== normalizedRestore) {
    try {
      await selectMode(normalizedRestore, { persist: true });
    } catch (err) {
      console.warn('Unable to restore previous mode before restart', err);
      lastModeBeforeStandard = normalizedRestore;
    }
  }

  await updateStatus();
  if (!lastBotStatus.running) {
    if (wantsRestore) {
      lastModeBeforeStandard = null;
    }
    return false;
  }

  if (btnApplyPreset) {
    btnApplyPreset.textContent = translate('quick.applyRestarting', 'Restarting…');
    btnApplyPreset.dataset.state = 'restarting';
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

  if (wantsRestore) {
    lastModeBeforeStandard = null;
  }

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
btnPostX?.addEventListener('click', handlePostToX);

if (pnlChartWrapper) {
  pnlChartWrapper.addEventListener('click', () => {
    if (pnlChartWrapper.classList.contains('is-interactive')) {
      openPnlModal();
    }
  });
  pnlChartWrapper.addEventListener('keydown', (event) => {
    if (!pnlChartWrapper.classList.contains('is-interactive')) {
      return;
    }
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      openPnlModal();
    }
  });
}

if (decisionReasons) {
  decisionReasons.addEventListener('click', (event) => {
    const item = findDecisionReasonItem(event.target);
    if (!item) return;
    event.preventDefault();
    activateDecisionReasonItem(item);
  });
  decisionReasons.addEventListener('keydown', (event) => {
    if (event.key !== 'Enter' && event.key !== ' ') {
      return;
    }
    const item = findDecisionReasonItem(event.target);
    if (!item) return;
    event.preventDefault();
    activateDecisionReasonItem(item);
  });
}

decisionReasonsToggle?.addEventListener('click', () => {
  if (!decisionReasonsAvailable) return;
  decisionReasonsExpanded = !decisionReasonsExpanded;
  updateDecisionReasonsVisibility();
});

decisionReasonsDownload?.addEventListener('click', () => {
  if (decisionReasonsDownload.disabled) return;
  downloadDecisionReasonExport();
});

updateDecisionReasonsVisibility();

tradeModalClose?.addEventListener('click', () => {
  closeTradeModal();
});

aiRequestModalClose?.addEventListener('click', () => {
  closeAiRequestModal();
});

playbookModalClose?.addEventListener('click', () => {
  closePlaybookModal();
});

if (aiRequestModal) {
  aiRequestModal.addEventListener('click', (event) => {
    if (event.target === aiRequestModal) {
      closeAiRequestModal();
    }
  });
}

if (playbookModal) {
  playbookModal.addEventListener('click', (event) => {
    if (event.target === playbookModal) {
      closePlaybookModal();
    }
  });
}

if (tradeModal) {
  tradeModal.addEventListener('click', (event) => {
    if (event.target === tradeModal) {
      closeTradeModal();
    }
  });
}

aiRequestList?.addEventListener('scroll', updateAiRequestNavButtons);

aiRequestPrev?.addEventListener('click', () => {
  scrollAiRequests(-1);
});

aiRequestNext?.addEventListener('click', () => {
  scrollAiRequests(1);
});

window.addEventListener('resize', () => {
  updateAiRequestNavButtons();
});

pnlChartModalClose?.addEventListener('click', () => {
  closePnlModal();
});

if (pnlChartModal) {
  pnlChartModal.addEventListener('click', (event) => {
    if (event.target === pnlChartModal) {
      closePnlModal();
    }
  });
}

decisionModalClose?.addEventListener('click', () => {
  closeDecisionModal();
});

if (decisionModal) {
  decisionModal.addEventListener('click', (event) => {
    if (event.target === decisionModal) {
      closeDecisionModal();
    }
  });
}

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

if (paperModeToggle) {
  paperModeToggle.addEventListener('change', () => {
    const desired = paperModeToggle.checked;
    const previous = paperMode;
    setPaperMode(desired);
    paperModeToggle.disabled = true;
    persistPaperMode(desired)
      .catch((err) => {
        alert(err.message);
        setPaperMode(previous);
      })
      .finally(() => {
        paperModeToggle.disabled = false;
      });
  });
}

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
  refreshPresetMeta();
});
riskSlider?.addEventListener('change', () => {
  updateRiskValue();
  markQuickConfigDirty();
  refreshPresetMeta();
});
leverageSlider?.addEventListener('input', () => {
  updateLeverageValue();
  markQuickConfigDirty();
  refreshPresetMeta();
});
leverageSlider?.addEventListener('change', () => {
  updateLeverageValue();
  markQuickConfigDirty();
  refreshPresetMeta();
});

inputDefaultNotional?.addEventListener('input', () => {
  if (inputAiDefaultNotional) {
    inputAiDefaultNotional.value = inputDefaultNotional.value;
  }
  markQuickConfigDirty();
});
inputDefaultNotional?.addEventListener('change', () => {
  if (inputAiDefaultNotional) {
    inputAiDefaultNotional.value = inputDefaultNotional.value;
  }
  markQuickConfigDirty();
});

inputAiDefaultNotional?.addEventListener('input', () => {
  if (inputDefaultNotional) {
    inputDefaultNotional.value = inputAiDefaultNotional.value;
  }
});
inputAiDefaultNotional?.addEventListener('change', () => {
  if (inputDefaultNotional) {
    inputDefaultNotional.value = inputAiDefaultNotional.value;
  }
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

if (automationToggle) {
  automationToggle.addEventListener('change', () => {
    if (automationToggle.checked) {
      startAutomation();
    } else {
      stopAutomation({ message: translate('chat.automation.stopped', 'Automation disabled.') });
    }
  });
}

if (automationIntervalInput) {
  automationIntervalInput.addEventListener('change', () => {
    const minutes = sanitizeAutomationInterval();
    if (automationActive) {
      scheduleAutomationCycle();
      const message = translate(
        'chat.automation.rescheduled',
        'Automation interval updated to {{minutes}} minute(s).',
        { minutes }
      );
      setChatStatus(message);
    }
  });
  automationIntervalInput.addEventListener('blur', () => {
    sanitizeAutomationInterval();
  });
}

if (btnAnalyzeMarket) {
  btnAnalyzeMarket.addEventListener('click', () => {
    runMarketAnalysis();
  });
}

sanitizeAutomationInterval();
updateAutomationCountdownDisplay();

btnTakeTradeProposals?.addEventListener('click', handleTakeTradeProposals);

updateTakeProposalsButtonState();

if (aiChatForm && aiChatInput) {
  aiChatForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (aiChatPending) {
      return;
    }
    if (!aiMode) {
      setChatStatus(translate('chat.status.enableAi', 'Please enable AI-Mode first.'));
      return;
    }
    if (!hasDashboardChatKey()) {
      setChatStatus(translate('chat.status.keyRequired', 'OpenAI key required.'));
      setChatKeyIndicator('missing', translate('chat.status.keyRequired', 'OpenAI key required.'));
      return;
    }
    const message = (aiChatInput.value || '').trim();
    if (!message) {
      setChatStatus(translate('chat.status.emptyMessage', 'Please enter a message.'));
      return;
    }
    aiChatPending = true;
    aiChatInput.disabled = true;
    if (aiChatSubmit) aiChatSubmit.disabled = true;
    setChatStatus(translate('chat.status.thinking', 'Strategy AI is thinking…'));
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
      const focusSymbols = Array.isArray(data.analysis_focus) ? data.analysis_focus : [];
      const analysisText = (data.analysis || '').toString().trim();
      const fallbackReply = (data.reply || '').toString() || translate('chat.reply.none', 'No reply received.');
      const assistantMessage = analysisText || fallbackReply;
      let roleLabel = translate('chat.role.analysis', 'Market Analysis');
      if (analysisText && focusSymbols.length === 1) {
        roleLabel = `${focusSymbols[0]} ${translate('chat.role.analysis', 'Market Analysis')}`;
      }
      appendChatMessage('assistant', assistantMessage, {
        model: data.model,
        source: data.source,
        roleLabel: analysisText ? roleLabel : undefined,
      });
      aiChatHistory.push({ role: 'assistant', content: assistantMessage });
      if (aiChatHistory.length > 12) {
        aiChatHistory = aiChatHistory.slice(-12);
      }

      const proposals = Array.isArray(data.trade_proposals) ? data.trade_proposals : [];
      if (proposals.length > 0) {
        proposals.forEach((proposal) => appendTradeProposalCard(proposal));
      } else if (analysisText) {
        loadTrades().catch(() => {});
      }

      if (analysisText) {
        if (data.source === 'fallback') {
          setChatStatus(translate('chat.status.fallback', 'Market analysis (fallback).'));
        } else {
          setChatStatus(translate('chat.status.ready', 'Market analysis ready.'));
        }
        setChatKeyIndicator('ready', translate('chat.key.ready', 'Dedicated chat key active'));
      } else {
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
          statusMessage = statusMessage
            ? `${statusMessage} · Manual trade queued (${summary})`
            : `Manual trade queued (${summary})`;
        }
        setChatStatus(statusMessage);
      }
    } catch (err) {
      appendChatMessage('assistant', err?.message || 'Chat failed.', { source: 'error' });
      setChatStatus(translate('chat.status.error', 'Chat failed.'));
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

if (nearMissList) {
  startNearMissMonitor();
}

async function init() {
  await loadConfig();
  await updateStatus();
  await loadTrades();
  await loadMostTradedCoins();
  connectLogs();
  connectActivePositionsStream();
  setInterval(updateStatus, 5000);
  setInterval(loadTrades, 5000);
  if (tickerContainer) {
    if (mostTradedTimer) {
      clearInterval(mostTradedTimer);
    }
    mostTradedTimer = setInterval(loadMostTradedCoins, 60000);
  }
}

init().catch((err) => console.error(err));
