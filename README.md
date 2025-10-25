# MrAster Trading Bot

MrAster ist ein vollständiges Werkzeugset für den Futures-Handel auf Binance-kompatiblen Börsen. Die Suite kombiniert einen regelbasierten
Signal-Scanner, ein mehrarmiges Banditenmodell für Trade-Gating, robuste Order-Verwaltung sowie ein operatives Dashboard mit KI-Unterstützung.

## Inhaltsverzeichnis
- [Highlights](#highlights)
- [Architekturüberblick](#architekturüberblick)
- [Schnellstart](#schnellstart)
- [Konfiguration](#konfiguration)
  - [Kernvariablen](#kernvariablen)
  - [Strategie, Risiko und Positionierung](#strategie-risiko-und-positionierung)
  - [KI, Automatisierung und Guardrails](#ki-automatisierung-und-guardrails)
- [Dashboard](#dashboard)
  - [Betriebsmodi](#betriebsmodi)
  - [Konfigurations-Editor](#konfigurations-editor)
- [Update-Hinweis](#update-hinweis)
- [Sicherheitshinweise](#sicherheitshinweise)

## Highlights

### Trading-Engine
- **RSI-basierte Signale mit Trendabgleich** &ndash; alle Schwellenwerte lassen sich über `ASTER_*`-Variablen verändern.
- **Mehrarmiger Bandit (`BanditPolicy`)** mit LinUCB und optionalem Alpha-Modell aus `ml_policy.py` entscheidet TAKE/SKIP sowie das Größen-Bucket (S/M/L).
- **Funding- und Spread-Filter** vermeiden Trades in illiquiden oder teuren Märkten.
- **Kline- und 24h-Ticker-Caching** reduziert API-Aufrufe und schützt vor kurzzeitigen Börsenausfällen.

### Risiko- und Order-Management
- **BracketGuard** (`brackets_guard.py`) repariert Stop-Loss- und Take-Profit-Orders, achtet auf `working_type` und unterstützt alte wie neue Bot-Signaturen.
- **FastTP** reagiert auf negative Returns und trimmt Positionen mit ATR-gebundenen Checkpoints.
- **Equity-Cache & Positions-Limits** (`ASTER_MAX_OPEN_*`, `ASTER_EQUITY_FRACTION`) halten die Gesamtrisikobelastung im Rahmen.
- **Persistenter Zustand** (`aster_state.json`) hält offene Trades, Policy-Daten und Dashboard-Einstellungen zwischen Sessions aktuell.

### KI und Automatisierung
- **AITradeAdvisor** (AI-Modus) bewertet Signale, passt Hebel & Positionsgrößen an und erklärt Entscheidungen im eigenen Activity-Feed.
- **News Sentinel** (`ASTER_AI_SENTINEL_*`) beobachtet externe Newsfeeds und kann Trades rund um Events blockieren.
- **Budget-Kontrolle** (`ASTER_AI_DAILY_BUDGET_USD`, `ASTER_AI_STRICT_BUDGET`) stoppt KI-Aufrufe bei Budgetüberschreitung.

### Beobachtbarkeit & Resilienz
- **HTTP-Hardening** konfigurierbar über `ASTER_HTTP_RETRIES`, `ASTER_HTTP_BACKOFF`, `ASTER_HTTP_TIMEOUT`.
- **Mehrpersonen-Dashboard** mit Log-Streaming, Prozess-Steuerung und Environment-Editor.
- **Eigenständige Anforderungen**: Ein `requirements.txt` bündelt alle Abhängigkeiten, sodass `pip install -r requirements.txt` genügt.

## Architekturüberblick

```
├── aster_multi_bot.py      # Haupteinstieg, Signale, Policy-Entscheidungen, Orderrouting
├── brackets_guard.py       # Hintergrundprozess für Stop/TP-Reparaturen
├── ml_policy.py            # LinUCB-Bandit & Alpha-Modell (Option)
├── dashboard_server.py     # FastAPI-Backend, Websocket-Logs, Prozess-Steuerung
├── dashboard_static/       # Single-Page-App mit Standard-, Pro- und KI-Modus
└── requirements.txt        # Vollständige Python-Abhängigkeiten
```

Der Bot lässt sich standalone starten oder über das Dashboard kontrollieren. Policy- und State-Dateien werden automatisch gespeichert
und beim nächsten Start wiederhergestellt.

## Schnellstart

### Voraussetzungen
- Python ≥ 3.10 (empfohlen)
- Binance- oder AsterDex-kompatibles Futures-Konto (für Live-Handel)
- Optional: Paper-Trading-Modus funktioniert ohne API-Keys

### Installation
```bash
# Repository klonen
git clone https://example.com/MrAster.git
cd MrAster

# Virtuelle Umgebung anlegen
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Abhängigkeiten installieren
pip install --upgrade pip
pip install -r requirements.txt
```

### Bot starten
```bash
export ASTER_PAPER=true  # Paper-Modus aktivieren
python aster_multi_bot.py
```

Mit `ASTER_RUN_ONCE=true` führt der Bot nur einen Scanzyklus aus. Ein Abbruch via `CTRL+C` (SIGINT) beendet den laufenden Durchlauf sauber.

### Dashboard starten
```bash
python dashboard_server.py
# oder mit Auto-Reload:
uvicorn dashboard_server:app --host 0.0.0.0 --port 8000
```

Die Oberfläche ist anschließend unter <http://localhost:8000> erreichbar. Log-Streams, Konfigurationsänderungen und Bot-Steuerung
stehen direkt im Browser zur Verfügung.

## Konfiguration

Alle relevanten Parameter können per Environment-Variablen gesetzt oder im Dashboard geschrieben werden (`dashboard_config.json`).
Untenstehend eine kuratierte Übersicht. Die vollständige Liste lässt sich jederzeit über den Dashboard-Editor oder den Kopfbereich in
`aster_multi_bot.py` einsehen.

### Kernvariablen

| Variable | Standardwert | Beschreibung |
| --- | --- | --- |
| `ASTER_API_KEY` / `ASTER_API_SECRET` | leer | API-Zugangsdaten für den Live-Handel. |
| `ASTER_EXCHANGE_BASE` | `https://fapi.asterdex.com` | REST-Endpunkt für Markt- und Orderdaten. |
| `ASTER_PAPER` | `false` | Aktiviert den Paper-Trading-Adapter. |
| `ASTER_RUN_ONCE` | `false` | Führt genau einen Scanzyklus aus. |
| `ASTER_LOGLEVEL` | `INFO` | Logging-Verbosity (`DEBUG`, `INFO`, ...). |
| `ASTER_MODE` | `standard` | Default-Dashboard-Modus (`standard`, `pro`, `ai`). |
| `ASTER_LOOP_SLEEP` | `30` | Pause zwischen Scans in Sekunden. |
| `ASTER_STATE_FILE` | `aster_state.json` | Persistenz-Datei für Bot- und KI-Zustand. |
| `ASTER_HTTP_RETRIES` | `2` | Zusätzliche HTTP-Retry-Versuche. |
| `ASTER_HTTP_BACKOFF` | `0.6` | Basiswartezeit (Sekunden) zwischen Retries. |
| `ASTER_HTTP_TIMEOUT` | `20` | HTTP-Timeout in Sekunden. |
| `ASTER_KLINE_CACHE_SEC` | `45` | Lebensdauer des Kline-Caches. |

### Strategie, Risiko und Positionierung

| Variable | Standardwert | Beschreibung |
| --- | --- | --- |
| `ASTER_INTERVAL` / `ASTER_HTF_INTERVAL` | `5m` / `30m` | Zeitrahmen für Signal & Bestätigung. |
| `ASTER_RSI_BUY_MIN` / `ASTER_RSI_SELL_MAX` | `52` / `48` | RSI-Grenzen für Long- bzw. Short-Einstiege. |
| `ASTER_ALLOW_TREND_ALIGN` | `false` | Erzwingt Trendabgleich zwischen Zeitrahmen. |
| `ASTER_TREND_BIAS` | `with` | Handelt mit oder gegen den Trend. |
| `ASTER_MIN_QUOTE_VOL_USDT` | `75000` | Mindestvolumen für handelbare Symbole. |
| `ASTER_SPREAD_BPS_MAX` | `0.0030` | Maximal tolerierter Bid/Ask-Spread (in Bps). |
| `ASTER_WICKINESS_MAX` | `0.97` | Filter gegen übermäßig volatile Kerzen. |
| `ASTER_MIN_EDGE_R` | `0.30` | Minimaler Edge (in R) zur Trade-Freigabe. |
| `ASTER_DEFAULT_NOTIONAL` | `250` | Fallback-Notional, falls keine Berechnung möglich ist. |
| `ASTER_RISK_PER_TRADE` | `0.006` | Anteil des Kapitals pro Trade. |
| `ASTER_EQUITY_FRACTION` | `0.33` | Maximale Equity-Auslastung aller offenen Positionen. |
| `ASTER_LEVERAGE` | `5` | Standardhebel für Orders. |
| `ASTER_MAX_OPEN_GLOBAL` | `4` | Globale Obergrenze gleichzeitiger Positionen. |
| `ASTER_MAX_OPEN_PER_SYMBOL` | `1` | Limit pro Symbol. |
| `ASTER_SL_ATR_MULT` / `ASTER_TP_ATR_MULT` | `1.0` / `1.6` | ATR-Multiplikatoren für Stop & Take-Profit. |
| `FAST_TP_ENABLED` | `true` | Aktiviert FastTP-Teilgewinnsicherung. |
| `FASTTP_MIN_R` | `0.30` | Mindest-R-Gewinn bevor FastTP greift. |
| `FAST_TP_RET1` / `FAST_TP_RET3` | `-0.0010` / `-0.0020` | Rücksetzer-Schwellen für FastTP. |
| `FASTTP_SNAP_ATR` | `0.25` | ATR-Distanz für den Snap-Mechanismus. |
| `FASTTP_COOLDOWN_S` | `15` | Wartezeit zwischen FastTP-Checks. |
| `ASTER_FUNDING_FILTER_ENABLED` | `true` | Aktiviert Funding-Limitierung. |
| `ASTER_FUNDING_MAX_LONG` / `ASTER_FUNDING_MAX_SHORT` | `0.0010` | Funding-Grenzen pro Richtung. |

### KI, Automatisierung und Guardrails

| Variable | Standardwert | Beschreibung |
| --- | --- | --- |
| `ASTER_BANDIT_ENABLED` | `true` | Aktiviert die LinUCB-Policy. |
| `ASTER_ALPHA_ENABLED` | `true` | Schaltet das optionale Alpha-Modell hinzu. |
| `ASTER_ALPHA_THRESHOLD` | `0.55` | Mindest-Confidence für Trade-Freigabe. |
| `ASTER_ALPHA_PROMOTE_DELTA` | `0.15` | Zusatz-Confidence für Upsizing. |
| `ASTER_HISTORY_MAX` | `250` | Anzahl historischer Trades für Analytics. |
| `ASTER_OPENAI_API_KEY` | leer | API-Key für AITradeAdvisor. |
| `ASTER_AI_MODEL` | `gpt-4o` | Modell-ID für KI-Analysen. |
| `ASTER_AI_DAILY_BUDGET_USD` | `1000` | Tägliches Budgetlimit (USD). |
| `ASTER_AI_STRICT_BUDGET` | `true` | Stoppt KI-Aufrufe nach Budgetverbrauch. |
| `ASTER_AI_SENTINEL_ENABLED` | `true` | Aktiviert den News Sentinel. |
| `ASTER_AI_SENTINEL_DECAY_MINUTES` | `90` | Lebensdauer einer News-Warnung. |
| `ASTER_AI_NEWS_ENDPOINT` | leer | Externe Quelle für Breaking-News. |
| `ASTER_AI_NEWS_API_KEY` | leer | API-Token für den Sentinel. |
| `ASTER_BRACKETS_QUEUE_FILE` | `brackets_queue.json` | Queue-Datei für Guard-Reparaturen. |

Weitere Variablen (wie Universums-Filter, Positionsgrößen je Bucket oder Arbeitsweise des Dashboards) finden sich direkt in den Quelltexten
oder in der UI. Jede Änderung im Dashboard wird nach Bestätigung in `dashboard_config.json` persistiert.

## Dashboard

Das Dashboard (FastAPI + Single-Page-App) bietet Prozesssteuerung, Echtzeit-Logs, Konfigurationsverwaltung und KI-Insights.

### Betriebsmodi
- **Standard-Modus**: Vorkonfigurierte Intensitäts-Presets (Low/Mid/High) mit Fokus auf Risiko-per-Trade und Hebelsteuerung.
- **Pro-Modus**: Schaltet den vollständigen Environment-Editor frei, inklusive direkter Bearbeitung aller `ASTER_*`-Variablen und ausführlicher Debug-Logs.
- **AI-Modus**: Aktiviert den AITradeAdvisor, der Signale bewertet, Budget- und News-Grenzen überwacht und Entscheidungen dokumentiert.

### Konfigurations-Editor
- Alle Felder entsprechen eins-zu-eins den Environment-Variablen des Bots.
- Änderungen werden nach dem Speichern in `dashboard_config.json` abgelegt und beim nächsten Start geladen.
- Der State (`aster_state.json`) enthält offene Positionen, Policy-Daten, KI-Hinweise und wird sowohl vom Bot als auch vom Guard genutzt.

## Update-Hinweis

Um auf die neueste Version zu aktualisieren, ohne die virtuelle Umgebung zu löschen, empfiehlt sich:

```bash
git fetch --all --prune && git reset --hard @{u} && git clean -fd -e .venv/
```

## Sicherheitshinweise
- Live-Handel birgt signifikante Risiken: Änderungen immer zuerst im Paper-Modus testen.
- API-Schlüssel niemals commiten oder öffentlich teilen.
- Auch bei aktivem Caching regelmäßig prüfen, ob Markt- und Orderdaten aktuell sind.
- Budget- und Sentinel-Parameter bewusst setzen, um KI-Kosten und Event-Risiken zu kontrollieren.

Viel Erfolg & happy trading! Beiträge und Issue-Reports sind jederzeit willkommen.
