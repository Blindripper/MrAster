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
const aiRequestList = document.getElementById('ai-request-list');
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
const btnApplyPreset = document.getElementById('btn-apply-preset');
const tickerContainer = document.getElementById('market-ticker');
const tickerTrack = document.getElementById('ticker-track');
const tickerEmpty = document.getElementById('ticker-empty');
const aiBudgetCard = document.getElementById('ai-budget');
const aiBudgetModeLabel = document.getElementById('ai-budget-mode');
const aiBudgetMeta = document.getElementById('ai-budget-meta');
const aiBudgetFill = document.getElementById('ai-budget-fill');
const skipRankingList = document.getElementById('skip-ranking-list');
const skipRankingDetail = document.getElementById('skip-ranking-detail');
const aiChatMessages = document.getElementById('ai-chat-messages');
const aiChatForm = document.getElementById('ai-chat-form');
const aiChatInput = document.getElementById('ai-chat-input');
const aiChatStatus = document.getElementById('ai-chat-status');
const chatKeyIndicator = document.getElementById('chat-key-indicator');
const btnAnalyzeMarket = document.getElementById('btn-analyze-market');
const btnTakeTradeProposals = document.getElementById('btn-take-proposals');
const activePositionsCard = document.getElementById('active-positions-card');
const activePositionsModeLabel = document.getElementById('active-positions-mode');
const activePositionsWrapper = document.getElementById('active-positions-wrapper');
const activePositionsEmpty = document.getElementById('active-positions-empty');
const activePositionsRows = document.getElementById('active-positions-rows');
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
const shareFeedback = document.getElementById('share-feedback');
const MEME_COMPOSER_WINDOW_NAME = 'mraster-meme-composer';
const MEME_COMPOSER_WINDOW_FEATURES =
  'width=920,height=1080,menubar=no,toolbar=no,location=no,status=no,resizable=yes,scrollbars=yes';

const languageButtons = document.querySelectorAll('.language-button[data-lang]');
const i18nElements = document.querySelectorAll('[data-i18n]');

if (btnSaveConfig) btnSaveConfig.dataset.state = 'idle';
if (btnSaveCredentials) btnSaveCredentials.dataset.state = 'idle';
if (btnSaveAi) btnSaveAi.dataset.state = 'idle';
if (btnApplyPreset) btnApplyPreset.dataset.state = 'idle';
if (btnTakeTradeProposals) btnTakeTradeProposals.dataset.state = 'idle';

const DEFAULT_BOT_STATUS = { running: false, pid: null, started_at: null, uptime_s: null };

const DEFAULT_LANGUAGE = 'en';
const SUPPORTED_LANGUAGES = ['en', 'ru', 'zh', 'ko', 'de', 'fr', 'es', 'tr'];
const COMPACT_SKIP_AGGREGATION_WINDOW = 600; // seconds
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
    'active.empty': 'Нет активных позиций.',
    'active.empty.paper': 'Пока нет бумажных сделок.',
    'active.table.symbol': 'Символ',
    'active.table.size': 'Размер',
    'active.table.entry': 'Цена входа',
    'active.table.mark': 'Маркет-прайс',
    'active.table.leverage': 'Плечо',
    'active.table.margin': 'Маржа',
    'active.table.pnl': 'PNL (ROE%)',
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
    'trades.modal.noMetadata': 'Дополнительные данные отсутствуют.',
    'pnl.title': 'Обзор эффективности',
    'pnl.subtitle': 'Совокупный реализованный PNL по вашим сделкам.',
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
  'quick.presets.adaptive.title': 'Adaptive',
  'quick.presets.adaptive.subtitle': 'Adaptive sizing · Dynamic confidence cap',
  'quick.presets.focus.title': 'Focus',
  'quick.presets.focus.subtitle': 'High conviction throttle · AI-weighted sizing',
    'quick.leverage.title': 'Плечо',
    'quick.leverage.placeholder': 'Базовое плечо: –',
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
    'modals.pnl.title': 'Обзор эффективности',
    'modals.pnl.subtitle': 'Совокупный реализованный PNL по вашим сделкам.',
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
    'active.empty': 'Keine aktiven Positionen.',
    'active.empty.paper': 'Noch keine Papier-Trades.',
    'active.table.symbol': 'Symbol',
    'active.table.size': 'Positionsgröße',
    'active.table.entry': 'Einstiegspreis',
    'active.table.mark': 'Markpreis',
    'active.table.leverage': 'Hebel',
    'active.table.margin': 'Margin',
    'active.table.pnl': 'PNL (ROE%)',
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
    'trades.modal.noMetadata': 'Keine zusätzlichen Daten vorhanden.',
    'pnl.title': 'Performance-Überblick',
    'pnl.subtitle': 'Kumulierte realisierte PNL aus deinen Trades.',
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
  'quick.presets.adaptive.title': 'Adaptive',
  'quick.presets.adaptive.subtitle': 'Adaptive sizing · Dynamic confidence cap',
  'quick.presets.focus.title': 'Focus',
  'quick.presets.focus.subtitle': 'High conviction throttle · AI-weighted sizing',
    'quick.leverage.title': 'Hebel',
    'quick.leverage.placeholder': 'Basishebel: –',
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
    'modals.pnl.title': 'Performance-Überblick',
    'modals.pnl.subtitle': 'Kumulierte realisierte PNL aus deinen Trades.',
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
    'active.empty': '활성 포지션이 없습니다.',
    'active.empty.paper': '아직 페이퍼 거래가 없습니다.',
    'active.table.symbol': '심볼',
    'active.table.size': '포지션 규모',
    'active.table.entry': '진입가',
    'active.table.mark': '마크 가격',
    'active.table.leverage': '레버리지',
    'active.table.margin': '증거금',
    'active.table.pnl': 'PNL (ROE%)',
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
    'trades.modal.noMetadata': '추가 메타데이터가 없습니다.',
    'pnl.title': '성과 개요',
    'pnl.subtitle': '거래 기반 누적 실현 PNL입니다.',
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
  'quick.presets.adaptive.title': 'Adaptive',
  'quick.presets.adaptive.subtitle': 'Adaptive sizing · Dynamic confidence cap',
  'quick.presets.focus.title': 'Focus',
  'quick.presets.focus.subtitle': 'High conviction throttle · AI-weighted sizing',
    'quick.leverage.title': '레버리지',
    'quick.leverage.placeholder': '기준 레버리지: –',
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
    'modals.pnl.title': '성과 요약',
    'modals.pnl.subtitle': '거래에서 발생한 누적 실현 PNL.',
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
    'active.empty': 'Aucune position active.',
    'active.empty.paper': 'Aucun trade en mode papier pour l’instant.',
    'active.table.symbol': 'Symbole',
    'active.table.size': 'Taille',
    'active.table.entry': 'Prix d’entrée',
    'active.table.mark': 'Prix de marché',
    'active.table.leverage': 'Effet de levier',
    'active.table.margin': 'Marge',
    'active.table.pnl': 'PNL (ROE %)',
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
    'trades.modal.noMetadata': 'Aucune donnée supplémentaire.',
    'pnl.title': 'Vue d’ensemble des performances',
    'pnl.subtitle': 'PNL réalisé cumulé sur vos trades.',
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
  'quick.presets.adaptive.title': 'Adaptive',
  'quick.presets.adaptive.subtitle': 'Adaptive sizing · Dynamic confidence cap',
  'quick.presets.focus.title': 'Focus',
  'quick.presets.focus.subtitle': 'High conviction throttle · AI-weighted sizing',
    'quick.leverage.title': 'Effet de levier',
    'quick.leverage.placeholder': 'Effet de levier de base : –',
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
    'modals.pnl.title': 'Vue d’ensemble des performances',
    'modals.pnl.subtitle': 'PNL réalisé cumulé sur vos trades.',
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
    'active.empty': 'Sin posiciones activas.',
    'active.empty.paper': 'Todavía no hay operaciones simuladas.',
    'active.table.symbol': 'Símbolo',
    'active.table.size': 'Tamaño',
    'active.table.entry': 'Precio de entrada',
    'active.table.mark': 'Precio de marca',
    'active.table.leverage': 'Apalancamiento',
    'active.table.margin': 'Margen',
    'active.table.pnl': 'PNL (ROE%)',
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
    'trades.modal.noMetadata': 'No hay datos adicionales.',
    'pnl.title': 'Resumen de rendimiento',
    'pnl.subtitle': 'PNL realizado acumulado de tus operaciones.',
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
  'quick.presets.adaptive.title': 'Adaptive',
  'quick.presets.adaptive.subtitle': 'Adaptive sizing · Dynamic confidence cap',
  'quick.presets.focus.title': 'Focus',
  'quick.presets.focus.subtitle': 'High conviction throttle · AI-weighted sizing',
    'quick.leverage.title': 'Apalancamiento',
    'quick.leverage.placeholder': 'Apalancamiento base: –',
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
    'modals.pnl.title': 'Resumen de rendimiento',
    'modals.pnl.subtitle': 'PNL realizado acumulado de tus operaciones.',
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
    'active.empty': 'Aktif pozisyon yok.',
    'active.empty.paper': 'Henüz demo işlemi yok.',
    'active.table.symbol': 'Sembol',
    'active.table.size': 'Büyüklük',
    'active.table.entry': 'Giriş fiyatı',
    'active.table.mark': 'Mark fiyatı',
    'active.table.leverage': 'Kaldıraç',
    'active.table.margin': 'Marj',
    'active.table.pnl': 'PNL (ROE%)',
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
    'trades.modal.noMetadata': 'Ek veri yok.',
    'pnl.title': 'Performans özeti',
    'pnl.subtitle': 'İşlemlerinizin kümülatif gerçekleşen PNL’i.',
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
  'quick.presets.adaptive.title': 'Adaptive',
  'quick.presets.adaptive.subtitle': 'Adaptive sizing · Dynamic confidence cap',
  'quick.presets.focus.title': 'Focus',
  'quick.presets.focus.subtitle': 'High conviction throttle · AI-weighted sizing',
    'quick.leverage.title': 'Kaldıraç',
    'quick.leverage.placeholder': 'Temel kaldıraç: –',
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
    'modals.pnl.title': 'Performans özeti',
    'modals.pnl.subtitle': 'İşlemlerinizin kümülatif gerçekleşen PNL’i.',
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
    'active.empty': '暂无持仓。',
    'active.empty.paper': '模拟交易尚未产生。',
    'active.table.symbol': '交易对',
    'active.table.size': '仓位规模',
    'active.table.entry': '开仓价',
    'active.table.mark': '标记价格',
    'active.table.leverage': '杠杆',
    'active.table.margin': '保证金',
    'active.table.pnl': '盈亏 (ROE%)',
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
    'trades.modal.noMetadata': '没有更多补充数据。',
    'pnl.title': '绩效概览',
    'pnl.subtitle': '基于您的交易计算的累计已实现盈亏。',
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
  'quick.presets.adaptive.title': 'Adaptive',
  'quick.presets.adaptive.subtitle': 'Adaptive sizing · Dynamic confidence cap',
  'quick.presets.focus.title': 'Focus',
  'quick.presets.focus.subtitle': 'High conviction throttle · AI-weighted sizing',
    'quick.leverage.title': '杠杆',
    'quick.leverage.placeholder': '基础杠杆：–',
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
    'modals.pnl.title': '绩效概览',
    'modals.pnl.subtitle': '基于您的交易计算的累计已实现盈亏。',
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
let aiChatHistory = [];
let aiChatPending = false;
let aiAnalyzePending = false;
let activePositions = [];
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
let skipRankingItems = [];
let selectedSkipRankingId = null;
let lastSkipRankingSnapshot = [];
const liveLogActivityEntries = [];
const liveLogActivitySignatures = new Set();
const LIVE_LOG_ACTIVITY_LIMIT = 120;
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
  renderTradeSummary(lastTradeStats);
  renderDecisionStats(lastDecisionStats);
  renderAiBudget(lastAiBudget);
  if (latestTradesSnapshot) {
    renderHeroMetrics(latestTradesSnapshot.cumulative_stats, latestTradesSnapshot.stats);
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

function formatBudgetAmount(value) {
  if (!Number.isFinite(value)) return null;
  const clamped = Math.max(value, 0);
  return clamped.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function renderAiBudget(budget) {
  lastAiBudget = budget && typeof budget === 'object' ? budget : null;
  if (!aiBudgetCard || !aiBudgetMeta || !aiBudgetFill) {
    return;
  }

  const limitRaw = Number(lastAiBudget?.limit);
  const spentRaw = Number(lastAiBudget?.spent);
  const hasLimit = Number.isFinite(limitRaw) && limitRaw > 0;
  const hasSpent = Number.isFinite(spentRaw) && spentRaw >= 0;

  const isAiActive = aiMode;
  const isPaperActive = paperMode;
  const hasBudgetData = hasLimit || hasSpent;

  aiBudgetCard.classList.toggle('active', isAiActive && !isPaperActive && hasBudgetData);
  aiBudgetCard.classList.remove('unlimited');

  if (!isAiActive) {
    aiBudgetFill.style.width = '0%';
    aiBudgetMeta.textContent = translate('status.aiBudgetMeta.disabled', 'AI mode is disabled.');
    return;
  }

  if (isPaperActive) {
    aiBudgetFill.style.width = '0%';
    aiBudgetMeta.textContent = translate(
      'status.aiBudgetMeta.paper',
      'Paper mode does not use budget.',
    );
    return;
  }

  if (!hasBudgetData) {
    aiBudgetFill.style.width = '0%';
    aiBudgetMeta.textContent = translate('status.aiBudgetMeta', 'Budget not configured.');
    return;
  }

  const spent = hasSpent ? Math.max(spentRaw, 0) : 0;
  const limit = hasLimit ? limitRaw : 0;

  let fillPercent = 0;
  if (hasLimit && limit > 0) {
    const ratio = spent / limit;
    fillPercent = Math.max(0, Math.min(Number.isFinite(ratio) ? ratio : 0, 1)) * 100;
  } else if (spent > 0) {
    fillPercent = 100;
  }
  aiBudgetFill.style.width = `${fillPercent.toFixed(0)}%`;

  if (hasLimit && limit > 0) {
    const remaining = Math.max(limit - spent, 0);
    aiBudgetMeta.textContent = translate(
      'status.aiBudgetMeta.limited',
      "Today's spend {{spent}} / {{limit}} USD · {{remaining}} USD remaining",
      {
        spent: formatBudgetAmount(spent) || '0.00',
        limit: formatBudgetAmount(limit) || '0.00',
        remaining: formatBudgetAmount(remaining) || '0.00',
      },
    );
    return;
  }

  aiBudgetCard.classList.add('unlimited');
  aiBudgetMeta.textContent = translate(
    'status.aiBudgetMeta.unlimited',
    "Today's spend {{spent}} USD · no limit",
    {
      spent: formatBudgetAmount(spent) || '0.00',
    },
  );
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
  },
  mid: {
    label: 'Mid',
    summary:
      'Balanced cadence with moderate risk, 50% base risk per trade, 10× base leverage, and a 66% equity utilisation ceiling geared toward steady account growth.',
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
  },
  high: {
    label: 'High',
    summary:
      'High-frequency execution with wider risk budgets, 100% base risk per trade, leverage auto-set to the exchange maximum, an unlimited AI spend cap, and full (100%) equity deployment when signals align.',
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
  },
  att: {
    label: 'ATT',
    summary:
      'Against-the-trend fading: contrarian plays with tighter stops, disciplined sizing, exchange-max leverage, and no AI budget ceiling.',
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
  },
  adaptive: {
    label: 'Adaptive',
    summary:
      'Regime-aware sizing: 55% risk per trade, 8× leverage ceiling, and event-risk driven confidence caps to prioritise quality flows.',
    risk: 55,
    leverage: 8,
    edgeMinR: 0.06,
    slAtr: 1.25,
    tpAtr: 2.15,
    fasttp: {
      minR: 0.22,
      ret1: -0.001,
      ret3: -0.0022,
      snapAtr: 0.24,
      cooldown: 38,
    },
    sizeMult: {
      base: 1.05,
      s: 1.1,
      m: 1.5,
      l: 2.05,
    },
    funding: {
      enabled: true,
      maxLong: 0.0011,
      maxShort: 0.0013,
    },
    alpha: {
      threshold: 0.54,
      minConf: 0.24,
      promoteDelta: 0.16,
      rewardMargin: 0.055,
    },
    alphaWarmup: 36,
    banditEnabled: true,
    alphaEnabled: true,
    equityFraction: 0.7,
    maxOpenGlobal: 0,
    maxOpenPerSymbol: 1,
    trendBias: 'with',
    confidenceSizing: {
      enabled: true,
      base: { min: 0.95, max: 3.1, blend: 0.6, exp: 2.05, cap: 3.4 },
      ranges: {
        min: [0.85, 1.18],
        max: [2.4, 3.9],
        blend: [0.45, 0.78],
        exp: [1.6, 2.45],
        cap: [2.8, 4.1],
        confidence: [0.32, 0.82],
        eventRisk: [0.1, 0.7],
        hype: [0.1, 0.65],
        sentinelFactor: [0.7, 1.6],
        regimeHeat: [-0.4, 0.6],
        budgetRatio: [0.15, 1.1],
      },
      weights: {
        confidence: 0.38,
        eventRisk: 0.22,
        hype: 0.1,
        sentinelFactor: 0.12,
        regimeHeat: 0.1,
        budgetRatio: 0.08,
      },
      drift: 0.7,
      fallbackConfidence: 0.55,
      fallbackEventRisk: 0.24,
      fallbackHype: 0.18,
      fallbackSentinelFactor: 1.0,
      fallbackRegimeHeat: 0,
      fallbackBudgetRatio: 0.2,
      gating: {
        confidenceFloor: 0.35,
        confidencePenaltyHigh: 0.85,
        confidencePenaltyLow: 0.4,
        budgetCeiling: 0.75,
        budgetMax: 1.25,
        budgetPenaltyHigh: 0.9,
        budgetPenaltyLow: 0.45,
      },
    },
  },
  focus: {
    label: 'Focus',
    summary:
      'High-conviction throttle: 45% base risk, 6× leverage, and confidence-weighted caps that open up only when sentinel heat cooperates.',
    risk: 45,
    leverage: 6,
    edgeMinR: 0.07,
    slAtr: 1.2,
    tpAtr: 2.05,
    fasttp: {
      minR: 0.2,
      ret1: -0.0009,
      ret3: -0.0019,
      snapAtr: 0.22,
      cooldown: 48,
    },
    sizeMult: {
      base: 0.95,
      s: 0.95,
      m: 1.35,
      l: 1.85,
    },
    funding: {
      enabled: true,
      maxLong: 0.001,
      maxShort: 0.0012,
    },
    alpha: {
      threshold: 0.58,
      minConf: 0.28,
      promoteDelta: 0.18,
      rewardMargin: 0.06,
    },
    alphaWarmup: 45,
    banditEnabled: true,
    alphaEnabled: true,
    equityFraction: 0.55,
    maxOpenGlobal: 0,
    maxOpenPerSymbol: 1,
    trendBias: 'with',
    confidenceSizing: {
      enabled: true,
      base: { min: 0.9, max: 3.35, blend: 0.68, exp: 2.35, cap: 3.8 },
      ranges: {
        min: [0.8, 1.22],
        max: [2.5, 4.2],
        blend: [0.5, 0.85],
        exp: [1.7, 2.7],
        cap: [3.0, 4.4],
        confidence: [0.38, 0.9],
        eventRisk: [0.08, 0.75],
        hype: [0.08, 0.7],
        sentinelFactor: [0.75, 1.7],
        regimeHeat: [-0.3, 0.7],
        budgetRatio: [0.1, 1.2],
      },
      weights: {
        confidence: 0.46,
        eventRisk: 0.18,
        hype: 0.1,
        sentinelFactor: 0.1,
        regimeHeat: 0.08,
        budgetRatio: 0.08,
      },
      drift: 0.78,
      fallbackConfidence: 0.52,
      fallbackEventRisk: 0.22,
      fallbackHype: 0.16,
      fallbackSentinelFactor: 1.05,
      fallbackRegimeHeat: 0.05,
      fallbackBudgetRatio: 0.18,
      gating: {
        confidenceFloor: 0.42,
        confidencePenaltyHigh: 0.88,
        confidencePenaltyLow: 0.35,
        budgetCeiling: 0.65,
        budgetMax: 1.2,
        budgetPenaltyHigh: 0.92,
        budgetPenaltyLow: 0.4,
      },
      signalBias: 0.05,
    },
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
  filtered: 'Signal blocked by safety filters',
  position_size: 'Position size below minimum',
  order_failed: 'Order could not be placed',
  sentinel_veto: 'Sentinel vetoed trade',
  ai_risk_zero: 'AI sized trade to zero',
  sentinel_block: 'Sentinel block',
  fallback_rules: 'Fallback rules triggered',
  plan_pending: 'AI plan pending',
  plan_timeout: 'AI plan timeout',
  trend_pending: 'Trend scan pending',
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
  no_cross: { base: '#0EA5E9', accent: '#38BDF8', text: '#06374a' },
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

function setEnvInputValue(key, value) {
  if (!envContainer) return;
  const selector = `input[data-key="${key}"]`;
  const input = envContainer.querySelector(selector);
  if (input) {
    input.value = value ?? '';
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
    const model = env?.ASTER_AI_MODEL ?? 'gpt-4o';
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
  let sawZeroSized = false;
  let sawNonZero = false;

  for (const key of sizeKeys) {
    if (!(key in position)) continue;
    const considerNumeric = (value) => {
      const numeric = toNumeric(value);
      if (!Number.isFinite(numeric)) return;
      if (Math.abs(numeric) < 1e-9) {
        sawZeroSized = true;
      } else {
        sawNonZero = true;
      }
    };

    const direct = unwrapPositionValue(position[key]);
    considerNumeric(direct);
    if (sawNonZero) return false;

    const raw = position[key];
    if (Array.isArray(raw) && raw.length > 0) {
      for (const candidate of raw) {
        considerNumeric(unwrapPositionValue(candidate));
        if (sawNonZero) return false;
      }
    }
  }

  if (sawNonZero) {
    return false;
  }
  return sawZeroSized;
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

function computePositionProgressValue(takeEntry, stopEntry, markPrice) {
  const takePrice = Number.isFinite(takeEntry?.price) ? takeEntry.price : null;
  const stopPrice = Number.isFinite(stopEntry?.price) ? stopEntry.price : null;
  const mark = Number.isFinite(markPrice) ? markPrice : null;

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
  const profitIsMax = takePrice >= stopPrice;
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

function buildPositionProgressBar({ takeEntry, stopEntry, markPrice }) {
  const container = document.createElement('div');
  container.className = 'position-progress-container';

  const track = document.createElement('div');
  track.className = 'position-progress-track';
  container.append(track);

  const indicator = document.createElement('div');
  indicator.className = 'position-progress-indicator';
  track.append(indicator);

  const progressValue = computePositionProgressValue(takeEntry, stopEntry, markPrice);
  if (progressValue === null) {
    container.classList.add('is-inactive');
  } else {
    indicator.style.left = `${(progressValue * 100).toFixed(2)}%`;
    const indicatorColors = computeProgressIndicatorColor(progressValue);
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

function updateActivePositionsView() {
  if (!activePositionsRows) return;
  const positions = Array.isArray(activePositions) ? activePositions : [];
  const sorted = positions.slice().sort((a, b) => getPositionTimestamp(b) - getPositionTimestamp(a));
  activePositionsRows.innerHTML = '';

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
  if (activePositionsEmpty) {
    activePositionsEmpty.innerHTML = paperMode
      ? translate('active.empty.paper', 'No paper trades yet.')
      : translate('active.empty', 'No active positions.');
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
    const signedQuantityField = pickNumericField(position, ACTIVE_POSITION_SIGNED_SIZE_KEYS || []);
    const notionalField = pickNumericField(position, ACTIVE_POSITION_NOTIONAL_KEYS || []);
    const entryField = pickNumericField(position, ACTIVE_POSITION_ALIASES.entry || []);
    const markField = pickNumericField(position, ACTIVE_POSITION_ALIASES.mark || []);
    const takeEntry = extractTpSlEntry(position, 'take');
    const stopEntry = extractTpSlEntry(position, 'stop');

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
    symbolCell.append(symbolWrapper);
    symbolCell.append(
      buildPositionProgressBar({
        takeEntry,
        stopEntry,
        markPrice: markField.numeric,
      }),
    );
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
    markCell.textContent = formatPriceDisplay(markField.numeric, {
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
        const priceForNotional = Number.isFinite(markField.numeric)
          ? Math.abs(markField.numeric)
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
    const pnlField = pickNumericField(position, ACTIVE_POSITION_ALIASES.pnl || []);
    const roePercentSource = pickNumericField(position, ACTIVE_POSITION_ALIASES.roe || []);
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

    activePositionsRows.append(row);
  });
}

function renderActivePositions(openPositions) {
  activePositions = normaliseActivePositions(openPositions);
  updateActivePositionsView();
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

  return { metricsParts, noteCandidates, events };
}

function buildAiRequestDetailContent(item) {
  const { metricsParts, noteCandidates, events } = collectAiRequestDetailData(item);
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

  if (body.children.length === 0) {
    const empty = document.createElement('p');
    empty.className = 'ai-request-modal-empty';
    empty.textContent = translate('ai.requests.modal.empty', 'No additional details available.');
    body.append(empty);
  }

  container.append(body);
  return container;
}

function parseSkipTimestamp(item) {
  if (!item || typeof item !== 'object') {
    return { seconds: null, iso: null, label: '' };
  }
  let seconds = Number(item.ts);
  if (!Number.isFinite(seconds)) {
    const isoCandidate = item.ts_iso || item.tsISO || item.timestamp || item.ts_string;
    if (isoCandidate) {
      const parsed = Date.parse(isoCandidate);
      if (Number.isFinite(parsed)) {
        seconds = parsed / 1000;
      }
    }
  }
  let iso = typeof item.ts_iso === 'string' && item.ts_iso ? item.ts_iso : null;
  if (Number.isFinite(seconds) && !iso) {
    try {
      iso = new Date(seconds * 1000).toISOString();
    } catch (err) {
      iso = null;
    }
  }
  const label = Number.isFinite(seconds)
    ? formatRelativeTime(seconds)
    : iso
    ? formatRelativeTime(iso)
    : '';
  return { seconds: Number.isFinite(seconds) ? seconds : null, iso, label };
}

function renderSkipRanking(items) {
  skipRankingItems = Array.isArray(items) ? items.filter((entry) => entry && typeof entry === 'object') : [];
  lastSkipRankingSnapshot = skipRankingItems.slice();
  if (skipRankingList) {
    skipRankingList.innerHTML = '';
    if (skipRankingItems.length === 0) {
      const empty = document.createElement('div');
      empty.className = 'skip-ranking-empty';
      empty.textContent = translate(
        'skipRanking.empty',
        'No skipped trades have been recorded yet. When the bot declines a setup, it will appear here.'
      );
      skipRankingList.append(empty);
    } else {
      skipRankingItems.forEach((item, index) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'skip-ranking-item';
        const itemId = item.id || `skip-${index}`;
        button.dataset.id = itemId;

        const rank = document.createElement('div');
        rank.className = 'skip-ranking-rank';
        rank.textContent = `${index + 1}`;
        button.append(rank);

        const main = document.createElement('div');
        main.className = 'skip-ranking-item-main';
        const header = document.createElement('div');
        header.className = 'skip-ranking-item-header';

        const symbol = document.createElement('span');
        symbol.className = 'skip-ranking-symbol';
        const symbolLabel = (item.symbol || '').toString().toUpperCase();
        const sideLabel = formatSideLabel(item.side || item.direction || '');
        symbol.textContent = sideLabel && sideLabel !== '—' ? `${symbolLabel} · ${sideLabel}`.trim() : symbolLabel || '—';
        header.append(symbol);

        const score = document.createElement('span');
        score.className = 'skip-ranking-score';
        const numericScore = Number(item.score);
        score.textContent = Number.isFinite(numericScore)
          ? translate('skipRanking.scoreLabel', 'Score {{score}}', {
              score: numericScore.toFixed(1),
            })
          : translate('skipRanking.scoreUnknown', 'Score n/a');
        header.append(score);

        main.append(header);

        const chips = document.createElement('div');
        chips.className = 'skip-ranking-meta';

        const confidence = Number(item.confidence);
        if (Number.isFinite(confidence) && confidence > 0) {
          const chip = document.createElement('span');
          chip.className = 'skip-ranking-chip positive';
          chip.textContent = translate('skipRanking.confidenceChip', 'Confidence {{value}}', {
            value: formatNumber(confidence, 2),
          });
          chips.append(chip);
        }

        const sizeMultiplier = Number(item.size_multiplier);
        if (Number.isFinite(sizeMultiplier) && sizeMultiplier > 0) {
          const chip = document.createElement('span');
          chip.className = 'skip-ranking-chip positive';
          chip.textContent = translate('skipRanking.sizeChip', 'Size ×{{value}}', {
            value: formatNumber(sizeMultiplier, 2),
          });
          chips.append(chip);
        }

        const eventRisk = Number(item.event_risk);
        if (Number.isFinite(eventRisk)) {
          const chip = document.createElement('span');
          chip.className = `skip-ranking-chip ${eventRisk > 0.55 ? 'negative' : ''}`.trim();
          chip.textContent = translate('skipRanking.eventRiskChip', 'Event risk {{percent}}%', {
            percent: (clampValue(eventRisk, 0, 1) * 100).toFixed(0),
          });
          chips.append(chip);
        }

        const originLabel = (item.origin || item.plan_origin || '').toString().trim();
        if (originLabel) {
          const chip = document.createElement('span');
          chip.className = 'skip-ranking-chip';
          chip.textContent = translate('skipRanking.originChip', 'Origin {{origin}}', { origin: originLabel });
          chips.append(chip);
        }

        if (chips.children.length > 0) {
          main.append(chips);
        }

        const noteText = (item.decision_note || item.risk_note || item.reason_label || '').toString().trim();
        if (noteText) {
          const note = document.createElement('p');
          note.className = 'skip-ranking-note';
          note.textContent = noteText.length > 160 ? `${noteText.slice(0, 157).trimEnd()}…` : noteText;
          main.append(note);
        }

        button.append(main);

        const tsInfo = parseSkipTimestamp(item);
        if (tsInfo.label) {
          const time = document.createElement('time');
          time.className = 'skip-ranking-item-time';
          time.textContent = tsInfo.label;
          if (tsInfo.iso) time.dateTime = tsInfo.iso;
          button.append(time);
        }

        button.addEventListener('click', () => selectSkipRankingItem(itemId));
        skipRankingList.append(button);
      });
    }
  }

  const nextSelection = skipRankingItems.find((entry) => entry.id === selectedSkipRankingId) || skipRankingItems[0] || null;
  selectSkipRankingItem(nextSelection ? nextSelection.id : null);
}

function selectSkipRankingItem(id) {
  if (!skipRankingItems.length) {
    selectedSkipRankingId = null;
    renderSkipRankingDetail(null);
    return;
  }
  const target = skipRankingItems.find((entry) => entry.id === id) || skipRankingItems[0];
  selectedSkipRankingId = target ? target.id : null;
  if (skipRankingList) {
    const nodes = skipRankingList.querySelectorAll('.skip-ranking-item');
    nodes.forEach((node) => {
      node.classList.toggle('is-active', node.dataset.id === selectedSkipRankingId);
    });
  }
  renderSkipRankingDetail(target || null);
}

function renderSkipRankingDetail(item) {
  if (!skipRankingDetail) return;
  skipRankingDetail.innerHTML = '';
  if (!item || typeof item !== 'object') {
    const empty = document.createElement('div');
    empty.className = 'skip-detail-empty';
    empty.textContent = translate(
      'skipRanking.selectHint',
      'Select a skipped trade from the ranking to inspect its metadata and score breakdown.'
    );
    skipRankingDetail.append(empty);
    return;
  }

  const header = document.createElement('div');
  header.className = 'skip-detail-header';

  const heading = document.createElement('div');
  heading.className = 'skip-detail-heading';
  const symbol = document.createElement('div');
  symbol.className = 'skip-detail-symbol';
  const symbolLabel = (item.symbol || '').toString().toUpperCase();
  const sideLabel = formatSideLabel(item.side || item.direction || '');
  symbol.textContent = sideLabel && sideLabel !== '—' ? `${symbolLabel} · ${sideLabel}`.trim() : symbolLabel || '—';
  heading.append(symbol);

  const score = document.createElement('div');
  score.className = 'skip-detail-score';
  const numericScore = Number(item.score);
  score.textContent = Number.isFinite(numericScore)
    ? translate('skipRanking.detailScore', 'Score {{score}}', { score: numericScore.toFixed(1) })
    : translate('skipRanking.scoreUnknown', 'Score n/a');
  heading.append(score);
  header.append(heading);

  const tsInfo = parseSkipTimestamp(item);
  if (tsInfo.iso || tsInfo.label) {
    const time = document.createElement('time');
    time.className = 'skip-detail-time';
    time.textContent = tsInfo.label || tsInfo.iso;
    if (tsInfo.iso) time.dateTime = tsInfo.iso;
    header.append(time);
  }

  skipRankingDetail.append(header);

  const metricsGrid = document.createElement('div');
  metricsGrid.className = 'skip-detail-metrics';
  const metricDefinitions = [
    { key: 'confidence', label: translate('skipRanking.metric.confidence', 'Confidence'), formatter: (v) => formatNumber(v, 2) },
    { key: 'size_multiplier', label: translate('skipRanking.metric.size', 'Size multiplier'), formatter: (v) => formatNumber(v, 2) },
    { key: 'expected_r', label: translate('skipRanking.metric.expectedR', 'Expected R'), formatter: (v) => formatNumber(v, 2) },
    {
      key: 'event_risk',
      label: translate('skipRanking.metric.eventRisk', 'Event risk'),
      formatter: (v) => `${(clampValue(v, 0, 1) * 100).toFixed(0)}%`,
    },
    {
      key: 'hype_score',
      label: translate('skipRanking.metric.hype', 'Hype'),
      formatter: (v) => `${(clampValue(v, 0, 1) * 100).toFixed(0)}%`,
    },
    {
      key: 'sentinel_factor',
      label: translate('skipRanking.metric.sentinelFactor', 'Sentinel factor'),
      formatter: (v) => formatNumber(v, 2),
    },
    {
      key: 'budget_ratio',
      label: translate('skipRanking.metric.budgetLoad', 'Budget load'),
      formatter: (v) => `${(Math.max(0, Number(v)) * 100).toFixed(0)}%`,
    },
  ];

  const metricsSource = item.metrics && typeof item.metrics === 'object' ? item.metrics : item;
  metricDefinitions.forEach((definition) => {
    const rawValue = metricsSource ? metricsSource[definition.key] : undefined;
    const numeric = Number(rawValue);
    if (!Number.isFinite(numeric)) return;
    const wrapper = document.createElement('div');
    wrapper.className = 'skip-detail-metric';
    const label = document.createElement('span');
    label.className = 'label';
    label.textContent = definition.label;
    const value = document.createElement('span');
    value.className = 'value';
    value.textContent = definition.formatter(numeric);
    wrapper.append(label, value);
    metricsGrid.append(wrapper);
  });

  if (metricsGrid.children.length > 0) {
    skipRankingDetail.append(metricsGrid);
  }

  const reasons = [];
  if (item.reason_label) reasons.push(item.reason_label);
  if (item.decision_note) reasons.push(item.decision_note);
  if (item.risk_note && item.risk_note !== item.decision_note) reasons.push(item.risk_note);
  const uniqueReasons = Array.from(new Set(reasons.map((text) => (text || '').toString().trim()).filter(Boolean)));
  if (uniqueReasons.length > 0) {
    const reasonSection = document.createElement('div');
    reasonSection.className = 'skip-detail-reasons';
    const title = document.createElement('h3');
    title.textContent = translate('skipRanking.reasons', 'Skip reasons');
    reasonSection.append(title);
    uniqueReasons.forEach((text) => {
      const paragraph = document.createElement('p');
      paragraph.className = 'skip-detail-reason';
      paragraph.textContent = text;
      reasonSection.append(paragraph);
    });
    skipRankingDetail.append(reasonSection);
  }

  const breakdownList = Array.isArray(item.score_components) ? item.score_components : [];
  if (breakdownList.length > 0) {
    const breakdown = document.createElement('div');
    breakdown.className = 'skip-detail-breakdown';
    const title = document.createElement('h3');
    title.textContent = translate('skipRanking.breakdown', 'Score breakdown');
    breakdown.append(title);
    const list = document.createElement('ul');
    breakdownList.forEach((component) => {
      if (!component || typeof component !== 'object') return;
      const li = document.createElement('li');
      const label = document.createElement('span');
      label.textContent = component.label || translate('skipRanking.breakdown.unknown', 'Contribution');
      const value = document.createElement('span');
      value.className = 'value';
      const numeric = Number(component.value);
      if (Number.isFinite(numeric)) {
        value.textContent = `${numeric > 0 ? '+' : ''}${numeric.toFixed(1)}`;
        if (numeric > 0) {
          value.classList.add('positive');
        } else if (numeric < 0) {
          value.classList.add('negative');
        }
      } else {
        value.textContent = component.value ?? '0';
      }
      li.append(label, value);
      list.append(li);
    });
    breakdown.append(list);
    skipRankingDetail.append(breakdown);
  }

  const planSection = document.createElement('div');
  planSection.className = 'skip-detail-json';
  const planTitle = document.createElement('h3');
  planTitle.textContent = translate('skipRanking.planMeta', 'Plan metadata');
  const planPre = document.createElement('pre');
  planPre.textContent = JSON.stringify(item.plan ?? {}, null, 2);
  planSection.append(planTitle, planPre);
  skipRankingDetail.append(planSection);

  const contextSection = document.createElement('div');
  contextSection.className = 'skip-detail-json';
  const contextTitle = document.createElement('h3');
  contextTitle.textContent = translate('skipRanking.contextMeta', 'Entry context');
  const contextPre = document.createElement('pre');
  contextPre.textContent = JSON.stringify(item.context ?? {}, null, 2);
  contextSection.append(contextTitle, contextPre);
  skipRankingDetail.append(contextSection);
}

function renderAiRequests(requests) {
  if (!aiRequestList) return;
  aiRequestList.innerHTML = '';
  if (!aiMode) {
    const disabled = document.createElement('div');
    disabled.className = 'ai-request-empty';
    disabled.textContent = translate('ai.feed.disabled', 'Enable AI mode to view the activity feed.');
    aiRequestList.append(disabled);
    return;
  }
  const items = Array.isArray(requests) ? requests.slice(0, 30) : [];
  if (items.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'ai-request-empty';
    empty.textContent = translate(
      'ai.requests.empty',
      'AI decisions will appear here once the bot consults the strategy copilot.'
    );
    aiRequestList.append(empty);
    return;
  }
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

    aiRequestList.append(card);
  });
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

function renderHeroMetrics(cumulativeStats, sessionStats) {
  if (!heroTotalTrades || !heroTotalPnl || !heroTotalWinRate) return;

  const totals = cumulativeStats && typeof cumulativeStats === 'object' ? cumulativeStats : {};
  const fallback = sessionStats && typeof sessionStats === 'object' ? sessionStats : {};

  const totalTradesRaw = Number(
    totals.total_trades ?? totals.count ?? fallback.count ?? 0,
  );
  const totalTrades = Number.isFinite(totalTradesRaw) && totalTradesRaw > 0 ? totalTradesRaw : 0;
  heroTotalTrades.textContent = totalTrades.toLocaleString();

  const netPnlCandidate = totals.total_pnl ?? fallback.total_pnl ?? 0;
  let netPnlRaw = Number(netPnlCandidate);
  let realizedPnlRaw = Number(
    totals.realized_pnl ?? totals.realizedPnl ?? fallback.realized_pnl ?? NaN,
  );
  let aiBudgetSpentRaw = Number(
    totals.ai_budget_spent ?? totals.aiBudgetSpent ?? fallback.ai_budget_spent ?? NaN,
  );

  if (!Number.isFinite(aiBudgetSpentRaw)) {
    aiBudgetSpentRaw = Number((sessionStats || {}).ai_budget_spent ?? NaN);
  }

  if (!Number.isFinite(aiBudgetSpentRaw)) {
    aiBudgetSpentRaw = 0;
  }

  if (!Number.isFinite(realizedPnlRaw)) {
    realizedPnlRaw = Number(fallback.total_pnl ?? NaN);
  }

  if (!Number.isFinite(realizedPnlRaw) && Number.isFinite(netPnlRaw)) {
    realizedPnlRaw = Number(netPnlRaw) + Number(aiBudgetSpentRaw);
  }

  if (!Number.isFinite(netPnlRaw) && Number.isFinite(realizedPnlRaw)) {
    netPnlRaw = Number(realizedPnlRaw) - Number(aiBudgetSpentRaw);
  }

  if (!Number.isFinite(netPnlRaw)) {
    netPnlRaw = 0;
  }

  const netPnl = netPnlRaw;
  const realizedPnl = Number.isFinite(realizedPnlRaw) ? realizedPnlRaw : netPnl + aiBudgetSpentRaw;
  const aiBudgetSpent = Number.isFinite(aiBudgetSpentRaw)
    ? aiBudgetSpentRaw
    : Math.max((realizedPnl || 0) - netPnl, 0);

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

  const winsRaw = Number(totals.wins ?? 0);
  const lossesRaw = Number(totals.losses ?? 0);
  const drawsRaw = Number(totals.draws ?? 0);
  const denominator = totalTrades > 0 ? totalTrades : winsRaw + lossesRaw + drawsRaw;
  let winRate = 0;
  if (denominator > 0 && Number.isFinite(winsRaw)) {
    winRate = winsRaw / denominator;
  } else if (fallback.win_rate != null) {
    winRate = Number(fallback.win_rate) || 0;
  }
  heroTotalWinRate.textContent = `${(winRate * 100).toFixed(1)}%`;

  heroMetricsSnapshot = {
    totalTrades,
    totalPnl: Number.isFinite(netPnl) ? netPnl : 0,
    totalPnlDisplay: heroTotalPnl.textContent,
    realizedPnl: Number.isFinite(realizedPnl) ? realizedPnl : Number.isFinite(netPnl) ? netPnl : 0,
    aiBudgetSpent: Number.isFinite(aiBudgetSpent) ? aiBudgetSpent : 0,
    winRate,
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

function renderTradeSummary(stats) {
  lastTradeStats = stats || null;
  tradeSummary.innerHTML = '';
  if (!stats) {
    const placeholder = document.createElement('div');
    placeholder.className = 'trade-metric muted';
    placeholder.innerHTML = `
      <span class="metric-label">${translate('trades.summary.placeholder.label', 'Performance')}</span>
      <span class="metric-value">${translate('trades.summary.placeholder.value', 'No data yet')}</span>
    `;
    tradeSummary.append(placeholder);
    setAiHintMessage(
      translate('trades.summary.hint', 'AI insight will appear once new telemetry is available.')
    );
    return;
  }
  const avgR = stats.count ? stats.total_r / stats.count : 0;
  const metrics = [
    {
      label: translate('trades.metric.trades', 'Trades'),
      value: stats.count ?? 0,
      tone: 'neutral',
    },
    {
      label: translate('trades.metric.totalPnl', 'Realized PNL'),
      value: `${stats.total_pnl > 0 ? '+' : ''}${formatNumber(stats.total_pnl, 2)} USDT`,
      tone: stats.total_pnl > 0 ? 'profit' : stats.total_pnl < 0 ? 'loss' : 'neutral',
    },
    {
      label: translate('trades.metric.winRate', 'Win rate'),
      value: `${((stats.win_rate ?? 0) * 100).toFixed(1)}%`,
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
    tradeSummary.append(el);
  }
  setAiHintMessage(stats.ai_hint);
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
    li.textContent = taken > 0
      ? translate('status.decisions.noneSkipped', 'No skipped trades recorded.')
      : translate('status.decisions.noneYet', 'No trade decisions yet.');
    decisionReasons.append(li);
    decisionReasonsExpanded = false;
    decisionReasonsAvailable = false;
    updateDecisionReasonsVisibility();
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
    decisionReasons.append(li);
  }

  decisionReasonsAvailable = true;
  updateDecisionReasonsVisibility();
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
  };
}

function buildPnlChartData(payload, { variant = 'default' } = {}) {
  const { accent, accentSoft } = getPnlChartPalette();
  const labels = Array.isArray(payload?.labels) ? payload.labels.slice() : [];
  const values = Array.isArray(payload?.values) ? payload.values.slice() : [];
  const pointRadius = variant === 'expanded' ? 3 : 2.5;
  const pointHoverRadius = variant === 'expanded' ? 5 : 4;
  return {
    labels,
    datasets: [
      {
        label: 'Cumulative PNL (USDT)',
        data: values,
        borderColor: accent,
        backgroundColor: accentSoft,
        tension: 0.35,
        pointRadius,
        pointHoverRadius,
        pointBackgroundColor: '#0c0d12',
        fill: true,
      },
    ],
  };
}

function buildPnlChartOptions({ variant = 'default' } = {}) {
  const { textMuted, gridLine } = getPnlChartPalette();
  const xTicks = {
    maxRotation: 0,
    autoSkip: true,
    color: textMuted,
  };
  const yTicks = {
    callback: (value) => {
      const numeric = Number(value);
      return Number.isFinite(numeric) ? numeric.toFixed(2) : value;
    },
    color: textMuted,
  };
  if (variant === 'expanded') {
    xTicks.font = { size: 13 };
    yTicks.font = { size: 13 };
  }
  const tooltip = {
    callbacks: {
      label: (context) => {
        const value = Number(context?.parsed?.y ?? 0);
        if (!Number.isFinite(value)) {
          return ' 0.00 USDT';
        }
        const sign = value >= 0 ? '+' : '';
        return ` ${sign}${value.toFixed(2)} USDT`;
      },
    },
  };
  if (variant === 'expanded') {
    tooltip.bodyFont = { size: 14 };
    tooltip.titleFont = { size: 13 };
  }
  return {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        ticks: xTicks,
        grid: {
          display: false,
        },
      },
      y: {
        ticks: yTicks,
        grid: {
          color: gridLine,
        },
      },
    },
    plugins: {
      legend: {
        display: false,
      },
      tooltip,
    },
  };
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

  const ctx = pnlChartModalCanvas.getContext('2d');
  if (!ctx || typeof Chart === 'undefined') {
    return;
  }

  pnlChartExpanded = new Chart(ctx, {
    type: 'line',
    data: buildPnlChartData(lastPnlChartPayload, { variant: 'expanded' }),
    options: buildPnlChartOptions({ variant: 'expanded' }),
  });

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

function renderPnlChart(history) {
  if (!pnlChartCanvas || typeof Chart === 'undefined') return;

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

  lastPnlChartPayload = {
    labels: labels.slice(),
    values: values.slice(),
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

  const data = buildPnlChartData(lastPnlChartPayload);
  const options = buildPnlChartOptions();

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
      occurredAt: Number.isFinite(timestampSeconds) ? timestampSeconds : undefined,
      occurredAtIso: friendly.parsed?.timestamp || null,
      parsed: friendly.parsed,
    });
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
    confidenceParts.push(`alpha confidence ${formatNumber(record.alpha_conf)}`);
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

function scaleRange(value, inputRange = [0, 1], outputRange = [0, 1]) {
  const numeric = Number(value);
  let [inMin, inMax] = Array.isArray(inputRange) ? inputRange.map(Number) : [0, 1];
  if (!Number.isFinite(inMin)) inMin = 0;
  if (!Number.isFinite(inMax)) inMax = 1;
  if (inMax === inMin) {
    const [outMin, outMax] = Array.isArray(outputRange) ? outputRange.map(Number) : [0, 1];
    const midpoint = Number.isFinite(outMin) && Number.isFinite(outMax) ? (outMin + outMax) / 2 : 0.5;
    return midpoint;
  }
  if (inMax < inMin) {
    [inMin, inMax] = [inMax, inMin];
  }
  const normalized = Number.isFinite(numeric) ? (numeric - inMin) / (inMax - inMin) : 0.5;
  const clamped = clampValue(normalized, 0, 1);
  let [outMin, outMax] = Array.isArray(outputRange) ? outputRange.map(Number) : [0, 1];
  if (!Number.isFinite(outMin)) outMin = 0;
  if (!Number.isFinite(outMax)) outMax = 1;
  if (outMax < outMin) {
    [outMin, outMax] = [outMax, outMin];
  }
  return outMin + (outMax - outMin) * clamped;
}

function deriveConfidenceSizingContext(preset, env = {}) {
  if (!preset || !preset.confidenceSizing) {
    return null;
  }
  const config = preset.confidenceSizing || {};
  const context = {
    confidence: null,
    confidenceSource: 'default',
    eventRisk: null,
    hype: null,
    sentinelFactor: null,
    regimeSlope: null,
    regimeAdx: null,
    regimeHeat: null,
    budgetRatio: null,
    budgetLimit: null,
    budgetSpent: null,
  };

  const fallbackConfidence = Number(config.fallbackConfidence ?? 0.5);
  if (context.confidence === null) {
    context.confidence = clampValue(
      Number.isFinite(fallbackConfidence) ? fallbackConfidence : 0.5,
      0,
      1,
    );
  }
  context.confidenceSource = 'fallback';

  const fallbackHype = Number(config.fallbackHype ?? 0.18);
  if (context.hype === null) {
    context.hype = clampValue(Number.isFinite(fallbackHype) ? fallbackHype : 0.18, 0, 1);
  }

  const fallbackEventRisk = Number(config.fallbackEventRisk ?? context.hype ?? 0.2);
  if (context.eventRisk === null) {
    context.eventRisk = clampValue(Number.isFinite(fallbackEventRisk) ? fallbackEventRisk : 0.2, 0, 1);
  }

  const fallbackSentinel = Number(config.fallbackSentinelFactor ?? 1.0);
  if (context.sentinelFactor === null) {
    context.sentinelFactor = clampValue(
      Number.isFinite(fallbackSentinel) ? fallbackSentinel : 1.0,
      0.2,
      3.0,
    );
  }

  const fallbackSlope = Number(config.fallbackRegimeSlope ?? 0);
  if (context.regimeSlope === null) {
    context.regimeSlope = clampValue(Number.isFinite(fallbackSlope) ? fallbackSlope : 0, -1.5, 1.5);
  }

  const fallbackAdx = Number(config.fallbackRegimeAdx ?? 0.45);
  if (context.regimeAdx === null) {
    context.regimeAdx = clampValue(Number.isFinite(fallbackAdx) ? fallbackAdx : 0.45, 0, 1);
  }

  const slopeComponent = Number.isFinite(context.regimeSlope) ? context.regimeSlope : 0;
  const adxComponent = Number.isFinite(context.regimeAdx) ? context.regimeAdx : 0.45;
  const eventRiskComponent = Number.isFinite(context.eventRisk) ? context.eventRisk : 0.2;
  const hypeComponent = Number.isFinite(context.hype) ? context.hype : 0.18;
  const sentinelComponent = Number.isFinite(context.sentinelFactor) ? context.sentinelFactor - 1 : 0;
  const rawHeat =
    slopeComponent * 0.45 +
    (adxComponent - 0.5) * 0.35 +
    (eventRiskComponent - 0.25) * 0.25 +
    (hypeComponent - 0.25) * 0.15 +
    sentinelComponent * 0.12;
  context.regimeHeat = clampValue(Number.isFinite(rawHeat) ? rawHeat : 0, -1, 1);

  if (lastAiBudget && typeof lastAiBudget === 'object') {
    const limit = Number(lastAiBudget.limit);
    const spent = Number(lastAiBudget.spent);
    if (Number.isFinite(limit) && limit > 0 && Number.isFinite(spent) && spent >= 0) {
      context.budgetLimit = limit;
      context.budgetSpent = clampValue(spent, 0, Math.max(limit, spent));
      context.budgetRatio = clampValue(spent / limit, 0, 5);
    } else if (Number.isFinite(spent) && spent >= 0) {
      context.budgetSpent = clampValue(spent, 0, spent);
    }
  }

  if (context.budgetRatio === null && env && env.ASTER_AI_DAILY_BUDGET_USD !== undefined) {
    const envLimit = Number(env.ASTER_AI_DAILY_BUDGET_USD);
    if (Number.isFinite(envLimit) && envLimit > 0) {
      context.budgetLimit = envLimit;
    }
  }

  if (context.budgetRatio === null) {
    const fallbackBudgetRatio = Number(config.fallbackBudgetRatio ?? 0.2);
    context.budgetRatio = clampValue(
      Number.isFinite(fallbackBudgetRatio) ? fallbackBudgetRatio : 0.2,
      0,
      5,
    );
  }

  return context;
}

function computeConfidenceSizingTargets(preset, context, env = {}) {
  if (!preset || !preset.confidenceSizing) {
    return null;
  }
  const config = preset.confidenceSizing || {};
  const envState = env || {};
  const ranges = config.ranges || {};
  const weights = config.weights || {};
  const drift = clampValue(Number.isFinite(Number(config.drift)) ? Number(config.drift) : 0.65, 0, 1);
  const safeContext = context || deriveConfidenceSizingContext(preset, envState) || {};

  const metrics = {
    confidence: clampValue(
      Number.isFinite(Number(safeContext.confidence))
        ? Number(safeContext.confidence)
        : Number.isFinite(Number(config.fallbackConfidence))
        ? Number(config.fallbackConfidence)
        : 0.5,
      0,
      1,
    ),
    eventRisk: clampValue(
      Number.isFinite(Number(safeContext.eventRisk))
        ? Number(safeContext.eventRisk)
        : Number.isFinite(Number(config.fallbackEventRisk))
        ? Number(config.fallbackEventRisk)
        : 0.2,
      0,
      1,
    ),
    hype: clampValue(
      Number.isFinite(Number(safeContext.hype))
        ? Number(safeContext.hype)
        : Number.isFinite(Number(config.fallbackHype))
        ? Number(config.fallbackHype)
        : 0.18,
      0,
      1,
    ),
    sentinelFactor: clampValue(
      Number.isFinite(Number(safeContext.sentinelFactor))
        ? Number(safeContext.sentinelFactor)
        : Number.isFinite(Number(config.fallbackSentinelFactor))
        ? Number(config.fallbackSentinelFactor)
        : 1.0,
      0.2,
      3.0,
    ),
    regimeHeat: clampValue(
      Number.isFinite(Number(safeContext.regimeHeat))
        ? Number(safeContext.regimeHeat)
        : Number.isFinite(Number(config.fallbackRegimeHeat))
        ? Number(config.fallbackRegimeHeat)
        : 0,
      -1,
      1,
    ),
    budgetRatio: clampValue(
      Number.isFinite(Number(safeContext.budgetRatio))
        ? Number(safeContext.budgetRatio)
        : Number.isFinite(Number(config.fallbackBudgetRatio))
        ? Number(config.fallbackBudgetRatio)
        : 0.2,
      0,
      5,
    ),
  };

  const rangeFor = (name, fallbackLow, fallbackHigh) => {
    const candidate = ranges[name];
    if (Array.isArray(candidate) && candidate.length >= 2) {
      let [low, high] = candidate.map(Number);
      if (!Number.isFinite(low) || !Number.isFinite(high)) {
        return [fallbackLow, fallbackHigh];
      }
      if (high < low) {
        [low, high] = [high, low];
      }
      if (low === high) {
        const delta = Math.abs(low) * 0.1 || 0.1;
        return [low - delta, high + delta];
      }
      return [low, high];
    }
    return [fallbackLow, fallbackHigh];
  };

  let weightedSum = 0;
  let totalWeight = 0;
  for (const [key, weightRaw] of Object.entries(weights)) {
    const weight = Number(weightRaw);
    if (!Number.isFinite(weight) || weight <= 0) {
      continue;
    }
    let score = 0.5;
    if (key === 'confidence') {
      score = scaleRange(metrics.confidence, rangeFor('confidence', 0, 1), [0, 1]);
    } else if (key === 'eventRisk') {
      score = scaleRange(metrics.eventRisk, rangeFor('eventRisk', 0, 1), [0, 1]);
    } else if (key === 'hype') {
      score = scaleRange(metrics.hype, rangeFor('hype', 0, 1), [0, 1]);
    } else if (key === 'sentinelFactor') {
      score = scaleRange(metrics.sentinelFactor, rangeFor('sentinelFactor', 0.6, 1.6), [0, 1]);
    } else if (key === 'regimeHeat') {
      score = scaleRange(metrics.regimeHeat, rangeFor('regimeHeat', -1, 1), [0, 1]);
    } else if (key === 'budgetRatio') {
      score = 1 - scaleRange(metrics.budgetRatio, rangeFor('budgetRatio', 0, 1.2), [0, 1]);
    } else if (Object.prototype.hasOwnProperty.call(metrics, key)) {
      score = scaleRange(metrics[key], rangeFor(key, 0, 1), [0, 1]);
    }
    weightedSum += score * weight;
    totalWeight += weight;
  }

  let signal = totalWeight > 0 ? clampValue(weightedSum / totalWeight, 0, 1) : 0.5;

  const gating = config.gating || {};
  if (Number.isFinite(metrics.confidence) && gating.confidenceFloor !== undefined) {
    const floor = Number(gating.confidenceFloor);
    if (Number.isFinite(floor) && metrics.confidence < floor) {
      const high = Number.isFinite(Number(gating.confidencePenaltyHigh))
        ? Number(gating.confidencePenaltyHigh)
        : 0.85;
      const low = Number.isFinite(Number(gating.confidencePenaltyLow))
        ? Number(gating.confidencePenaltyLow)
        : 0.35;
      const normalized = scaleRange(metrics.confidence, [0, floor], [0, 1]);
      const penalty = clampValue(low + (high - low) * normalized, 0.2, 1);
      signal *= penalty;
    }
  }
  if (Number.isFinite(metrics.budgetRatio) && gating.budgetCeiling !== undefined) {
    const ceiling = Number(gating.budgetCeiling);
    const upper = Number.isFinite(Number(gating.budgetMax)) ? Number(gating.budgetMax) : ceiling + 0.6;
    if (Number.isFinite(ceiling) && metrics.budgetRatio > ceiling) {
      const high = Number.isFinite(Number(gating.budgetPenaltyHigh))
        ? Number(gating.budgetPenaltyHigh)
        : 0.9;
      const low = Number.isFinite(Number(gating.budgetPenaltyLow)) ? Number(gating.budgetPenaltyLow) : 0.45;
      const normalized = scaleRange(metrics.budgetRatio, [ceiling, upper], [0, 1]);
      const penalty = clampValue(high + (low - high) * normalized, 0.2, 1);
      signal *= penalty;
    }
  }
  if (Number.isFinite(Number(config.signalBias))) {
    signal = clampValue(signal + Number(config.signalBias), 0, 1);
  }

  const computeTarget = (rangeName, baseKey, fallbackRange) => {
    const baseValue = Number(config.base?.[baseKey]);
    const [low, high] = rangeFor(rangeName, fallbackRange[0], fallbackRange[1]);
    const dynamic = scaleRange(signal, [0, 1], [low, high]);
    if (Number.isFinite(baseValue)) {
      return baseValue * (1 - drift) + dynamic * drift;
    }
    return dynamic;
  };

  const target = {
    min: computeTarget('min', 'min', [0.85, 1.15]),
    max: computeTarget('max', 'max', [2.2, 3.6]),
    blend: computeTarget('blend', 'blend', [0.45, 0.8]),
    exp: computeTarget('exp', 'exp', [1.5, 2.5]),
    cap: computeTarget('cap', 'cap', [2.6, 4.2]),
  };

  target.min = clampValue(target.min, 0.5, 1.5);
  target.max = clampValue(target.max, target.min + 0.1, 5.0);
  target.blend = clampValue(target.blend, 0.2, 0.95);
  target.exp = clampValue(target.exp, 1.0, 3.5);
  target.cap = clampValue(Math.max(target.cap, target.max + 0.05), target.max + 0.05, 5.5);

  const currentValues = {
    min: getEnvNumber(envState, 'ASTER_CONFIDENCE_SIZE_MIN', target.min),
    max: getEnvNumber(envState, 'ASTER_CONFIDENCE_SIZE_MAX', target.max),
    blend: getEnvNumber(envState, 'ASTER_CONFIDENCE_SIZE_BLEND', target.blend),
    exp: getEnvNumber(envState, 'ASTER_CONFIDENCE_SIZE_EXP', target.exp),
    cap: getEnvNumber(envState, 'ASTER_SIZE_MULT_CAP', target.cap),
  };

  const noteParts = [];
  if (Number.isFinite(metrics.confidence)) {
    const confidenceLabel = safeContext.confidenceSource ? ` (${safeContext.confidenceSource})` : '';
    noteParts.push(`Confidence ${formatNumber(metrics.confidence, 2)}${confidenceLabel}`);
  }
  if (Number.isFinite(metrics.eventRisk)) {
    noteParts.push(`Event risk ${(metrics.eventRisk * 100).toFixed(0)}%`);
  }
  if (Number.isFinite(metrics.hype)) {
    noteParts.push(`Hype ${(metrics.hype * 100).toFixed(0)}%`);
  }
  if (Number.isFinite(metrics.sentinelFactor)) {
    noteParts.push(`Sentinel factor ${formatNumber(metrics.sentinelFactor, 2)}×`);
  }
  if (Number.isFinite(metrics.regimeHeat)) {
    noteParts.push(`Regime heat ${formatNumber(metrics.regimeHeat, 2)}`);
  }
  if (Number.isFinite(metrics.budgetRatio)) {
    noteParts.push(`Budget load ${(clampValue(metrics.budgetRatio, 0, 5) * 100).toFixed(0)}%`);
  }
  const contextNote = noteParts.length ? `Context — ${noteParts.join(' · ')}` : '';

  return {
    enabled: config.enabled !== false,
    enabledEnv: getEnvBoolean(envState, 'ASTER_CONFIDENCE_SIZING', true),
    target,
    current: currentValues,
    note: contextNote,
    context: {
      ...safeContext,
      confidence: metrics.confidence,
      eventRisk: metrics.eventRisk,
      hype: metrics.hype,
      sentinelFactor: metrics.sentinelFactor,
      regimeHeat: metrics.regimeHeat,
      budgetRatio: metrics.budgetRatio,
      signal,
    },
  };
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

    const envState = currentConfig?.env ?? {};
    const sizingContext = deriveConfidenceSizingContext(preset, envState);
    const sizingTargets = computeConfidenceSizingTargets(preset, sizingContext, envState);
    if (sizingTargets) {
      const { target: sizingTarget, current: sizingCurrent, note: sizingNote, enabledEnv } = sizingTargets;
      const displayValue = `${formatMultiplierValue(sizingTarget.min)} → ${formatMultiplierValue(sizingTarget.max)}`;
      const detailParts = [
        `Blend ${formatNumber(sizingTarget.blend, 2)}`,
        `Exp ${formatNumber(sizingTarget.exp, 2)}`,
        `Cap ${formatMultiplierValue(sizingTarget.cap)}`,
      ];
      const noteParts = [];
      if (!enabledEnv) {
        noteParts.push('Current: disabled');
      }
      const differs =
        enabledEnv &&
        (numbersDiffer(sizingCurrent.min, sizingTarget.min, 1e-3) ||
          numbersDiffer(sizingCurrent.max, sizingTarget.max, 1e-3) ||
          numbersDiffer(sizingCurrent.blend, sizingTarget.blend, 1e-3) ||
          numbersDiffer(sizingCurrent.exp, sizingTarget.exp, 1e-3) ||
          numbersDiffer(sizingCurrent.cap, sizingTarget.cap, 1e-3));
      if (differs) {
        noteParts.push(
          `Current: min ${formatMultiplierValue(sizingCurrent.min)} / max ${formatMultiplierValue(sizingCurrent.max)}, blend ${formatNumber(sizingCurrent.blend, 2)}, exp ${formatNumber(sizingCurrent.exp, 2)}, cap ${formatMultiplierValue(sizingCurrent.cap)}`,
        );
      }
      if (sizingNote) {
        noteParts.push(sizingNote);
      }
      appendPresetMetaItem(presetMlDetails, {
        label: 'Confidence sizing',
        value: displayValue,
        detail: detailParts.join(' · '),
        note: noteParts.join(' · '),
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

  const envState = currentConfig?.env ?? {};
  const sizingContext = deriveConfidenceSizingContext(preset, envState);
  const sizingTargets = computeConfidenceSizingTargets(preset, sizingContext, envState);
  if (sizingTargets) {
    payload.ASTER_CONFIDENCE_SIZING = sizingTargets.enabled === false ? 'false' : 'true';
    payload.ASTER_CONFIDENCE_SIZE_MIN = toFixedString(sizingTargets.target.min, 2);
    payload.ASTER_CONFIDENCE_SIZE_MAX = toFixedString(sizingTargets.target.max, 2);
    payload.ASTER_CONFIDENCE_SIZE_BLEND = toFixedString(sizingTargets.target.blend, 2);
    payload.ASTER_CONFIDENCE_SIZE_EXP = toFixedString(sizingTargets.target.exp, 2);
    payload.ASTER_SIZE_MULT_CAP = toFixedString(sizingTargets.target.cap, 2);
  }

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
  renderSkipRanking(lastSkipRankingSnapshot);
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
    renderHeroMetrics(data.cumulative_stats, data.stats);
    renderDecisionStats(data.decision_stats);
    renderPnlChart(data.history);
    renderAiBudget(data.ai_budget);
    renderAiRequests(data.ai_requests);
    renderSkipRanking(data.skip_ranking);
    renderActivePositions(data.open);
    const proposals = Array.isArray(data.ai_trade_proposals) ? data.ai_trade_proposals : [];
    proposals.forEach((proposal) => appendTradeProposalCard(proposal));
    pruneTradeProposalRegistry(proposals);
  } catch (err) {
    console.warn(err);
  }
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

updateDecisionReasonsVisibility();

tradeModalClose?.addEventListener('click', () => {
  closeTradeModal();
});

aiRequestModalClose?.addEventListener('click', () => {
  closeAiRequestModal();
});

if (aiRequestModal) {
  aiRequestModal.addEventListener('click', (event) => {
    if (event.target === aiRequestModal) {
      closeAiRequestModal();
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
