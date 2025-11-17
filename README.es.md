<div align="center">
  <img src="assets/mraster-logo.png" alt="Logotipo de MrAster" width="240" />
  <h1>Bot de trading MrAster</h1>
  <p><strong>Tu copiloto amigable de futuros cripto: vigila el mercado, gestiona el riesgo y te mantiene informado.</strong></p>
  <p>
    <a href="#-mraster-en-60-segundos">¿Por qué MrAster?</a>
    ·
    <a href="#-inicio-rapido">Inicio rápido</a>
    ·
    <a href="#-panorama-del-dashboard">Panorama del dashboard</a>
    ·
    <a href="#-bajo-el-capot-para-makers">Bajo el capó</a>
  </p>
</div>

<p align="center">
  <a href="https://www.python.org/" target="_blank"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python 3.10+" /></a>
  <a href="#-panorama-del-dashboard"><img src="https://img.shields.io/badge/Control-Dashboard%20web%20limpio-8A2BE2" alt="Dashboard" /></a>
  <a href="#-seguridad-ante-todo"><img src="https://img.shields.io/badge/Modo-Paper%20o%20live-FF8C00" alt="Modos" /></a>
  <a href="#-seguridad-ante-todo"><img src="https://img.shields.io/badge/Recordatorio-El%20trading%20es%20riesgoso-E63946" alt="Riesgo" /></a>
</p>

> “Enciende el backend, abre el navegador y deja que los copilotos hagan el trabajo pesado.”

---

## ✨ MrAster en 60 segundos

- **Trading automatizado sin estrés** – MrAster escanea el mercado de futuros, sugiere operaciones y puede ejecutarlas con barandas integradas.
- **Dashboard siempre disponible** – Inicia o detén el bot, ajusta el riesgo y lee explicaciones de la IA desde una sola página.
- **IA que respeta tu presupuesto** – Límites diarios, enfriamientos y un centinela de noticias mantienen a los copilotos útiles y asequibles.
- **Configuración sin misterio** – Practica en modo paper antes de pasar a órdenes reales.

## 🚀 Inicio rápido

1. **Prepara Python**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
2. **Arranca el backend**
   ```bash
   python dashboard_server.py
   # o con auto-reload
   uvicorn dashboard_server:app --host 0.0.0.0 --port 8000
   ```
3. **Termina en el navegador**
   Abre <http://localhost:8000>, conecta tus llaves del exchange (o modo paper) y sigue la guía paso a paso.

> ¿Prefieres headless? Exporta `ASTER_PAPER=true` (opcional) y ejecuta `python aster_multi_bot.py`. Con `ASTER_RUN_ONCE=true` se realiza un solo ciclo de escaneo.

## 🖥️ Panorama del dashboard

- **Control a un clic** – Inicia, detén o reinicia el bot supervisado (`aster_multi_bot.py`) sin tocar la terminal.
- **Logs y alertas en vivo** – Sigue cada idea, respuesta de la IA y advertencia de guardia en tiempo real.
- **Riesgo simplificado** – Elige un preset (Low / Mid / High / ATT) o cambia a modo Pro para ajustar cada variable `ASTER_*`.
- **Edición de configuración segura** – Actualiza el entorno con validación automática antes de aplicar cambios.
- **Copilotos IA visibles** – Lee notas claras, monitorea el presupuesto consumido y conversa desde la misma interfaz.
- **Instantáneas de rendimiento** – Revisa PnL, historial y heatmaps sin salir del dashboard.

## 🛡️ Seguridad ante todo

- **Modo paper**: Ensaya estrategias con ejecuciones simuladas antes de arriesgar capital real.
- **Topes de presupuesto**: Los copilotos de IA respetan tu límite diario salvo que lo eleves manualmente.
- **Alertas del centinela**: Noticias urgentes, funding inusual y picos de volatilidad aparecen al instante.
- **Tú tienes el control**: Detén el bot, cambia ajustes o pausa la autonomía cuando quieras.

## 🤓 Bajo el capó (para makers)

¿Quieres conocer motores, guardas y superficie de configuración? Despliega los bloques siguientes.

<details>
<summary><strong>Stack de copilotos IA</strong></summary>

- **AITradeAdvisor** arma cada solicitud con estadísticas de régimen, contexto del libro y prompts estructurados, las despacha por un pool de hilos (con caché y tablas de precios) y devuelve planes JSON con overrides y explicaciones.
- **DailyBudgetTracker + BudgetLearner** forman una doble compuerta de gasto: el tracker mantiene promedios por modelo y el learner ajusta presupuestos por símbolo y suspende llamadas costosas cuando la edge cae, todo actualizado tras cada respuesta de OpenAI.
- **NewsTrendSentinel** (`ASTER_AI_SENTINEL_*`) fusiona métricas de 24h y noticias externas en etiquetas de riesgo, límites de tamaño y multiplicadores de hype antes de que la solicitud llegue al asesor.
- **PostmortemLearning** destila revisiones cualitativas en features numéricas persistentes para que el siguiente plan incorpore lecciones del último cierre.
- **ParameterTuner** recoge resultados de trades, recalcula sesgos de tamaño/ATR y solo recurre a sugerencias LLM cuando existe estadística suficiente.
- **PlaybookManager** mantiene un playbook vivo de regímenes, directivas y ajustes estructurados de riesgo que se inyectan en cada payload.
- **Cola pendiente y guardas de concurrencia** moderan la autonomía vía `ASTER_AI_CONCURRENCY`, `ASTER_AI_PENDING_LIMIT` y cooldowns globales, evitando saturar API y presupuesto mientras muestran las intenciones en el dashboard.

</details>

<details>
<summary><strong>Motor de trading</strong></summary>

- **Señales RSI con confirmación de tendencia** – Configurables mediante variables `ASTER_*` o el editor del dashboard.
- **Política bandido multi-brazo (`BanditPolicy`)** combina exploración LinUCB con el modelo alfa opcional (`ml_policy.py`) para decidir TAKE/SKIP y buckets de tamaño (S/M/L).
- **Filtros de higiene de mercado** mantienen limpio el feed: límites de funding y spread, filtros de mechas y velas/tickers en caché suavizan el ruido del exchange.
- **Guardia anti-arbitraje sensible al oráculo** acota la brecha mark/oracle con el índice de prima (Jez, 2025) y aleja entradas de trampas de funding.

</details>

<details>
<summary><strong>Riesgo y gestión de órdenes</strong></summary>

- **BracketGuard** (`brackets_guard.py`) repara stops y take-profits con soporte para firmas antiguas y nuevas.
- **FastTP** recorta movimientos adversos mediante puntos de control basados en ATR y lógica de enfriamiento.
- **Límites de capital y exposición** (`ASTER_MAX_OPEN_*`, `ASTER_EQUITY_FRACTION`) más el estado persistente (`aster_state.json`) aseguran continuidad entre reinicios.

</details>

<details>
<summary><strong>Estrategia, riesgo y posicionamiento</strong></summary>

| Variable | Valor por defecto | Descripción |
| --- | --- | --- |
| `ASTER_INTERVAL` / `ASTER_HTF_INTERVAL` | `5m` / `30m` | Marcos temporales de señal y confirmación. |
| `ASTER_RSI_BUY_MIN` / `ASTER_RSI_SELL_MAX` | `51` / `49`* | Umbrales RSI para entradas long/short. |
| `ASTER_ALLOW_TREND_ALIGN` | `false` | Obliga a alinear tendencias entre marcos. |
| `ASTER_TREND_BIAS` | `with` | Opera con/en contra de la tendencia. |
| `ASTER_MIN_QUOTE_VOL_USDT` | `150000` | Volumen mínimo para símbolos operables. |
| `ASTER_SPREAD_BPS_MAX` | `0.0030` | Spread bid/ask máximo (bps). |
| `ASTER_WICKINESS_MAX` | `0.97` | Filtro contra velas demasiado volátiles. |
| `ASTER_MIN_EDGE_R` | `0.30` | Edge mínimo (en R) requerido para aprobar un trade. |
| `ASTER_DEFAULT_NOTIONAL` | `0` | Notional base cuando no hay datos adaptativos (0 = IA lo calcula). |
| `ASTER_SIZE_MULT_FLOOR` | `0` | Mínimo multiplicador de tamaño (1.0 fuerza el notional base). |
| `ASTER_MAX_NOTIONAL_USDT` | `0` | Límite duro sobre el notional (0 = deciden guardas de apalancamiento/capital). |
| `ASTER_SIZE_MULT_CAP` | `3.0` | Multiplicador máximo tras ajustes. |
| `ASTER_CONFIDENCE_SIZING` | `true` | Activa dimensionamiento basado en confianza. |
| `ASTER_CONFIDENCE_SIZE_MIN` / `ASTER_CONFIDENCE_SIZE_MAX` | `1.0` / `3.0` | Metas mínima/máxima del multiplicador. |
| `ASTER_CONFIDENCE_SIZE_BLEND` / `ASTER_CONFIDENCE_SIZE_EXP` | `1` / `2.0` | Peso y exponente para la curva (>1 favorece alta confianza). |
| `ASTER_RISK_PER_TRADE` | `0.007`* | Fracción de capital por trade. |
| `ASTER_EQUITY_FRACTION` | `0.66` | Fracción máxima de equity utilizada (presets 33% / 66% / 100%). |
| `ASTER_LEVERAGE` | `10` | Apalancamiento por defecto (presets: 4× / 10× / máximo del exchange). |
| `ASTER_MAX_OPEN_GLOBAL` | `0` | Límite global de posiciones abiertas (0 = sin límite). |
| `ASTER_MAX_OPEN_PER_SYMBOL` | `1` | Límite por símbolo (0 = sin límite). |
| `ASTER_SL_ATR_MULT` / `ASTER_TP_ATR_MULT` | `1.0` / `1.6` | Multiplicadores ATR para stop y take profit. |
| `FAST_TP_ENABLED` | `true` | Activa FastTP. |
| `FASTTP_MIN_R` | `0.30` | Ganancia mínima (en R) antes de FastTP. |
| `FAST_TP_RET1` / `FAST_TP_RET3` | `-0.0010` / `-0.0020` | Umbrales de retroceso para FastTP. |
| `FASTTP_SNAP_ATR` | `0.25` | Distancia ATR para el mecanismo snap. |
| `FASTTP_COOLDOWN_S` | `15` | Intervalo entre chequeos de FastTP. |
| `ASTER_FUNDING_FILTER_ENABLED` | `true` | Activa el filtro de funding. |
| `ASTER_FUNDING_MAX_LONG` / `ASTER_FUNDING_MAX_SHORT` | `0.0010` | Límites de funding por dirección. |
| `ASTER_NON_ARB_FILTER_ENABLED` | `true` | Activa la pinza mark/oracle anti-arbitraje. |
| `ASTER_NON_ARB_CLAMP_BPS` | `0.0005` | Ancho de la pinza (±bps). |
| `ASTER_NON_ARB_EDGE_THRESHOLD` | `0.00005` | Edge de funding tolerado antes de bloquear. |
| `ASTER_NON_ARB_SKIP_GAP` | `0.0015` | Brecha mark/oracle que fuerza un skip. |

*Cuando se lanza desde el dashboard se usan RSI 51/49 y riesgo 0.007. Con solo CLI, las semillas son 52/48 y 0.006 hasta que las reemplaces o sincronices vía `dashboard_config.json`.*

</details>

<details>
<summary><strong>IA, automatización y guardas</strong></summary>

| Variable | Valor por defecto | Descripción |
| --- | --- | --- |
| `ASTER_BANDIT_ENABLED` | `true` | Activa la política LinUCB. |
| `ASTER_AI_MODE` | `false` | Fuerza la ejecución IA incluso en modos Standard/Pro (`ASTER_MODE=ai`). |
| `ASTER_ALPHA_ENABLED` | `true` | Habilita el modelo alfa opcional. |
| `ASTER_ALPHA_THRESHOLD` | `0.55` | Confianza mínima para aprobar un trade. |
| `ASTER_ALPHA_PROMOTE_DELTA` | `0.15` | Confianza adicional para aumentar tamaño. |
| `ASTER_HISTORY_MAX` | `250` | Historial máximo usado para analítica. |
| `ASTER_OPENAI_API_KEY` | vacío | API key para AITradeAdvisor. |
| `ASTER_CHAT_OPENAI_API_KEY` | vacío | Clave específica de chat; usa la principal por defecto. |
| `ASTER_AI_MODEL` | `gpt-4.1` | ID del modelo. |
| `ASTER_AI_DAILY_BUDGET_USD` | `20` | Presupuesto diario (USD); se ignora con `ASTER_PRESET_MODE=high/att`. |
| `ASTER_AI_STRICT_BUDGET` | `true` | Detiene llamadas IA al agotar el presupuesto. |
| `ASTER_AI_MIN_INTERVAL_SECONDS` | `3` | Enfriamiento antes de reevaluar el mismo símbolo. |
| `ASTER_AI_CONCURRENCY` | `4` | Máximo de peticiones LLM simultáneas. |
| `ASTER_AI_PENDING_LIMIT` | `max(4, 3×concurrency)` | Límite de la cola pendiente. |
| `ASTER_AI_GLOBAL_COOLDOWN_SECONDS` | `1.0` | Pausa global entre peticiones. |
| `ASTER_AI_PLAN_TIMEOUT_SECONDS` | `45` | Tiempo de espera antes de recurrir a fallback. |
| `ASTER_AI_SENTINEL_ENABLED` | `true` | Activa el centinela de noticias. |
| `ASTER_AI_SENTINEL_DECAY_MINUTES` | `60` | Duración de una alerta. |
| `ASTER_AI_NEWS_ENDPOINT` | vacío | Fuente externa de noticias. |
| `ASTER_AI_NEWS_API_KEY` | vacío | Token API para el centinela. |
| `ASTER_AI_TEMPERATURE` | `0.3` | Ajuste de creatividad (1.0 = valor del proveedor). |
| `ASTER_AI_DEBUG_STATE` | `false` | Activa logs detallados y dumps de payload. |
| `ASTER_BRACKETS_QUEUE_FILE` | `brackets_queue.json` | Cola para reparaciones de guardas. |

</details>

<details>
<summary><strong>Archivos persistentes</strong></summary>

- **`aster_state.json`** – Guarda posiciones, telemetría IA, estado del centinela y preferencias del dashboard. Elimínalo para reiniciar limpio ante inconsistencias.
- **`dashboard_config.json`** – Refleja el editor del dashboard. Respáldalo para múltiples presets o bórralo para valores por defecto.
- **`brackets_queue.json`** – Lo mantiene `brackets_guard.py` para reparar stops/TP. Archívalo y bórralo si ves reparaciones repetidas.

Detén el backend antes de editar o borrar para evitar escrituras parciales; mueve los archivos fuera del repo si necesitas un snapshot previo.

</details>

## 🔐 Recordatorio de seguridad

- El trading en vivo es arriesgado: comienza en modo paper.
- Mantén las claves API privadas y rótalas con frecuencia.
- Incluso con caché, confirma que los datos de mercado y órdenes estén frescos.
- Ajusta presupuesto y parámetros del centinela a tu tolerancia al riesgo.

¡Felices trades! Si encuentras un bug o tienes una idea, abre un issue o pull request.
