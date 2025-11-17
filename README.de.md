<div align="center">
  <img src="assets/mraster-logo.png" alt="MrAster-Logo" width="240" />
  <h1>MrAster Trading Bot</h1>
  <p><strong>Dein freundlicher Krypto-Futures-Copilot: beobachtet den Markt, managt Risiken und hält dich auf dem Laufenden.</strong></p>
  <p>
    <a href="#-mraster-in-60-sekunden">Warum MrAster?</a>
    ·
    <a href="#-schnellstart">Schnellstart</a>
    ·
    <a href="#-dashboard-auf-einen-blick">Dashboard-Überblick</a>
    ·
    <a href="#-unter-der-haube-fuer-builder">Unter der Haube</a>
  </p>
</div>

<p align="center">
  <a href="https://www.python.org/" target="_blank"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python 3.10+" /></a>
  <a href="#-dashboard-auf-einen-blick"><img src="https://img.shields.io/badge/Steuerung-Sauberes%20Web-Dashboard-8A2BE2" alt="Dashboard" /></a>
  <a href="#-sicherheit-geht-vor"><img src="https://img.shields.io/badge/Modus-Paper%20oder%20Live-FF8C00" alt="Modi" /></a>
  <a href="#-sicherheit-geht-vor"><img src="https://img.shields.io/badge/Reminder-Trading%20ist%20riskant-E63946" alt="Risikohinweis" /></a>
</p>

> „Backend anschalten, Browser öffnen und die Copiloten die schwere Arbeit erledigen lassen.“

---

## ✨ MrAster in 60 Sekunden

- **Handelsautomatisierung ohne Stress** – MrAster scannt den Futures-Markt, schlägt Trades vor und kann sie mit eingebauten Schutzmechanismen ausführen.
- **Immer sichtbares Dashboard** – Starte oder stoppe den Bot, passe Risikoregler an und lies AI-Erklärungen auf einer einzigen, übersichtlichen Seite.
- **KI, die dein Budget respektiert** – Tagesbudgets, Cooldowns und ein News-Sentinel halten die Copiloten hilfreich und bezahlbar.
- **Keine Rätsel beim Setup** – Nutze den Paper-Modus, um zu üben, bevor du auf Live-Orders umstellst.

## 🚀 Schnellstart

1. **Python einrichten**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
2. **Backend starten**
   ```bash
   python dashboard_server.py
   # oder mit Auto-Reload
   uvicorn dashboard_server:app --host 0.0.0.0 --port 8000
   ```
3. **Im Browser abschließen**
   Öffne <http://localhost:8000>, verbinde deine Exchange-Keys (oder Paper-Modus) und folge der geführten Einrichtung.

> Lieber headless? Setze `ASTER_PAPER=true` (optional) und rufe `python aster_multi_bot.py` auf. Mit `ASTER_RUN_ONCE=true` wird genau ein Scan-Durchlauf ausgeführt.

## 🖥️ Dashboard auf einen Blick

- **Steuerung mit einem Klick** – Starte, stoppe oder starte den überwachten Bot (`aster_multi_bot.py`) neu, ohne das Terminal zu berühren.
- **Live-Logs & Alerts** – Verfolge jede Trade-Idee, jede KI-Antwort und jede Schutzwarnung in Echtzeit.
- **Risikoeinstellungen leicht gemacht** – Wähle ein Preset (Low / Mid / High / ATT) oder wechsle in den Pro-Modus, um jede `ASTER_*`-Stellschraube anzupassen.
- **Sicheres Config-Editing** – Aktualisiere deine Umgebung sicher; MrAster validiert alle Felder, bevor sie übernommen werden.
- **KI-Copiloten im Blick** – Lies verständliche Trade-Notizen, prüfe das verbrauchte Budget und chatte direkt zurück.
- **Performance-Schnappschüsse** – Analysiere PnL, Trade-Historie und Markt-Heatmaps ohne Kontextwechsel.

## 🛡️ Sicherheit geht vor

- **Paper-Modus**: Probiere Strategien mit simulierten Fills aus, bevor du echtes Geld riskierst.
- **Budget-Grenzen**: KI-Helfer respektieren dein tägliches USD-Limit, sofern du es nicht explizit anhebst.
- **Sentinel-Warnungen**: Breaking News, ungewöhnliche Funding-Raten und Volatilitätsspitzen werden sofort gemeldet.
- **Du bleibst in Kontrolle**: Stoppe den Bot, ändere Einstellungen oder pausiere die Autonomie jederzeit.

## 🤓 Unter der Haube (für Builder)

Neugierig auf Engines, Schutzmechanismen und Konfiguration? Klappe die folgenden Abschnitte für den technischen Überblick aus.

<details>
<summary><strong>AI-Copilot-Stack</strong></summary>

- **AITradeAdvisor** bündelt jede Anfrage mit Regime-Stats, Orderbuch-Kontext und strukturierten Prompts, verteilt sie per Thread-Pool (inklusive Caching und Preislimits) und liefert JSON-Pläne samt Overrides und Erklärungen.
- **DailyBudgetTracker + BudgetLearner** sorgen für doppeltes Ausgaben-Gating: Ein rollendes Ledger hält Durchschnittswerte pro Modell, während der Learner Symbol-Budgets anpasst und teure Calls aussetzt, wenn die Edge sinkt – alles nach jeder OpenAI-Antwort aktualisiert.
- **NewsTrendSentinel** (`ASTER_AI_SENTINEL_*`) verbindet 24h-Marktdaten mit optionalen externen News zu Event-Risiko-Labels, Positions-Clamps und Hype-Faktoren, bevor die Anfrage den Advisor erreicht.
- **PostmortemLearning** destilliert qualitative Trade-Reviews in persistente numerische Features, damit der nächste Plan „weiß“, was der letzte Exit gelehrt hat.
- **ParameterTuner** sammelt Trade-Ergebnisse, berechnet Größen-/ATR-Bias neu und eskaliert erst zu LLM-Vorschlägen, wenn genug relevante Historie vorhanden ist.
- **PlaybookManager** pflegt ein lebendes Playbook aus Marktregimen, Direktiven und strukturierten Risikoanpassungen, das der Advisor jeder Payload hinzufügt.
- **Pending-Queue & Concurrency-Guards** drosseln die Autonomie mit `ASTER_AI_CONCURRENCY`, `ASTER_AI_PENDING_LIMIT` und globalen Cooldowns, damit API-Budgets geschont werden und dennoch anstehende Intents im Dashboard erscheinen.

</details>

<details>
<summary><strong>Trading-Engine</strong></summary>

- **RSI-Signale mit Trendbestätigung** – Konfigurierbar über `ASTER_*`-Variablen oder den Dashboard-Editor.
- **Multi-Armed-Bandit-Policy (`BanditPolicy`)** kombiniert LinUCB-Exploration mit dem optionalen Alpha-Modell (`ml_policy.py`), um TAKE/SKIP und Größen-Buckets (S/M/L) zu bestimmen.
- **Market-Hygiene-Filter** reinigen den Feed: Funding- und Spread-Grenzen, Docht-Filter sowie gecachte Klines/24h-Ticker glätten Börsenrauschen.
- **Oracle-Aware Non-Arbitrage Guard** begrenzt den Mark/Oracle-Gap mit dem Premium-Index (nach Jez, 2025) und lenkt Entries von Funding-Fallen weg.

</details>

<details>
<summary><strong>Risiko- & Order-Management</strong></summary>

- **BracketGuard** (`brackets_guard.py`) repariert Stop-Loss- und Take-Profit-Orders und versteht alte wie neue Bot-Signaturen.
- **FastTP** reduziert adverse Bewegungen mit ATR-Begrenzungen und Cooldown-Logik.
- **Equity- und Exposure-Limits** (`ASTER_MAX_OPEN_*`, `ASTER_EQUITY_FRACTION`) plus persistenter Zustand (`aster_state.json`) sorgen für Kontinuität über Neustarts hinweg.

</details>

<details>
<summary><strong>Strategie, Risiko und Positionierung</strong></summary>

| Variable | Standard | Beschreibung |
| --- | --- | --- |
| `ASTER_INTERVAL` / `ASTER_HTF_INTERVAL` | `5m` / `30m` | Zeitrahmen für Signale und Bestätigung. |
| `ASTER_RSI_BUY_MIN` / `ASTER_RSI_SELL_MAX` | `51` / `49`* | RSI-Grenzen für Long- bzw. Short-Einstiege. |
| `ASTER_ALLOW_TREND_ALIGN` | `false` | Erzwingt Trend-Ausrichtung zwischen den Timeframes. |
| `ASTER_TREND_BIAS` | `with` | Handel mit oder gegen den Trend. |
| `ASTER_MIN_QUOTE_VOL_USDT` | `150000` | Minimales Volumen für handelbare Symbole. |
| `ASTER_SPREAD_BPS_MAX` | `0.0030` | Maximal tolerierter Bid/Ask-Spread (bps). |
| `ASTER_WICKINESS_MAX` | `0.97` | Filter gegen übermäßig volatile Kerzen. |
| `ASTER_MIN_EDGE_R` | `0.30` | Mindest-Edge (in R) für Trade-Freigabe. |
| `ASTER_DEFAULT_NOTIONAL` | `0` | Basisnotional, wenn keine adaptiven Daten vorliegen (0 = KI berechnet). |
| `ASTER_SIZE_MULT_FLOOR` | `0` | Mindest-Multiplikator für Positionsgröße (1.0 erzwingt Basisnotional). |
| `ASTER_MAX_NOTIONAL_USDT` | `0` | Harte Obergrenze für Order-Notional (0 = Leverage/Equity-Guards entscheiden). |
| `ASTER_SIZE_MULT_CAP` | `3.0` | Maximale Positionsgrößen-Skalierung nach allen Anpassungen. |
| `ASTER_CONFIDENCE_SIZING` | `true` | Aktiviert Vertrauens-basierte Größenanpassung. |
| `ASTER_CONFIDENCE_SIZE_MIN` / `ASTER_CONFIDENCE_SIZE_MAX` | `1.0` / `3.0` | Untere/obere Multiplikatorziele. |
| `ASTER_CONFIDENCE_SIZE_BLEND` / `ASTER_CONFIDENCE_SIZE_EXP` | `1` / `2.0` | Blend-Gewicht und Exponent für die Kurve (>1 bevorzugt hohes Vertrauen). |
| `ASTER_RISK_PER_TRADE` | `0.007`* | Anteil des Kapitals pro Trade. |
| `ASTER_EQUITY_FRACTION` | `0.66` | Maximal genutzter Eigenkapitalanteil (Presets 33% / 66% / 100%). |
| `ASTER_LEVERAGE` | `10` | Standardhebel (Dashboard-Presets: 4× / 10× / Exchange-Max). |
| `ASTER_MAX_OPEN_GLOBAL` | `0` | Globale Begrenzung gleichzeitiger Positionen (0 = unbegrenzt). |
| `ASTER_MAX_OPEN_PER_SYMBOL` | `1` | Begrenzung pro Symbol (0 = unbegrenzt). |
| `ASTER_SL_ATR_MULT` / `ASTER_TP_ATR_MULT` | `1.0` / `1.6` | ATR-Multiplikatoren für Stop und Take-Profit. |
| `FAST_TP_ENABLED` | `true` | Aktiviert FastTP. |
| `FASTTP_MIN_R` | `0.30` | Mindestgewinn (in R), bevor FastTP greift. |
| `FAST_TP_RET1` / `FAST_TP_RET3` | `-0.0010` / `-0.0020` | Rücklauf-Schwellen für FastTP. |
| `FASTTP_SNAP_ATR` | `0.25` | ATR-Distanz für Snap-Mechanismus. |
| `FASTTP_COOLDOWN_S` | `15` | Wartezeit zwischen FastTP-Checks. |
| `ASTER_FUNDING_FILTER_ENABLED` | `true` | Aktiviert Funding-Filter. |
| `ASTER_FUNDING_MAX_LONG` / `ASTER_FUNDING_MAX_SHORT` | `0.0010` | Funding-Grenzen pro Richtung. |
| `ASTER_NON_ARB_FILTER_ENABLED` | `true` | Aktiviert Mark/Oracle-Clamp gegen Arbitrage. |
| `ASTER_NON_ARB_CLAMP_BPS` | `0.0005` | Breite der Premium-Klammer (±bps). |
| `ASTER_NON_ARB_EDGE_THRESHOLD` | `0.00005` | Tolerierte Funding-Edge vor Blockierung. |
| `ASTER_NON_ARB_SKIP_GAP` | `0.0015` | Absoluter Mark/Oracle-Gap, der zum Skip führt. |

*Beim Dashboard-Start werden RSI 51/49 und 0.007 Risikoanteil gesetzt. CLI-Starts nutzen 52/48 und 0.006, bis überschrieben oder via `dashboard_config.json` synchronisiert.*

</details>

<details>
<summary><strong>KI, Automatisierung & Guardrails</strong></summary>

| Variable | Standard | Beschreibung |
| --- | --- | --- |
| `ASTER_BANDIT_ENABLED` | `true` | Aktiviert LinUCB-Policy. |
| `ASTER_AI_MODE` | `false` | Erzwingt KI-Laufzeit selbst bei Standard/Pro. Entspricht `ASTER_MODE=ai`. |
| `ASTER_ALPHA_ENABLED` | `true` | Schaltet das optionale Alpha-Modell. |
| `ASTER_ALPHA_THRESHOLD` | `0.55` | Mindestvertrauen für Trade-Freigabe. |
| `ASTER_ALPHA_PROMOTE_DELTA` | `0.15` | Zusätzliches Vertrauen für Upsizing. |
| `ASTER_HISTORY_MAX` | `250` | Historische Trades für Analysen. |
| `ASTER_OPENAI_API_KEY` | leer | API-Key für AITradeAdvisor. |
| `ASTER_CHAT_OPENAI_API_KEY` | leer | Optionaler Chat-spezifischer OpenAI-Key; fallback zu `ASTER_OPENAI_API_KEY`. |
| `ASTER_AI_MODEL` | `gpt-4.1` | Modell-ID für Analysen. |
| `ASTER_AI_DAILY_BUDGET_USD` | `20` | Tägliches Budget (USD); wird bei `ASTER_PRESET_MODE=high/att` ignoriert. |
| `ASTER_AI_STRICT_BUDGET` | `true` | Stoppt KI-Calls nach Budgetgrenze. |
| `ASTER_AI_MIN_INTERVAL_SECONDS` | `3` | Cooldown, bevor dieselbe Symbolbewertung wiederholt wird. |
| `ASTER_AI_CONCURRENCY` | `4` | Max. gleichzeitige LLM-Anfragen. |
| `ASTER_AI_PENDING_LIMIT` | `max(4, 3×concurrency)` | Limit für wartende KI-Jobs. |
| `ASTER_AI_GLOBAL_COOLDOWN_SECONDS` | `1.0` | Globale Pause zwischen Requests. |
| `ASTER_AI_PLAN_TIMEOUT_SECONDS` | `45` | Timeout für KI-Pläne, bevor Fallbacks greifen. |
| `ASTER_AI_SENTINEL_ENABLED` | `true` | Aktiviert News Sentinel. |
| `ASTER_AI_SENTINEL_DECAY_MINUTES` | `60` | Lebensdauer einer News-Warnung. |
| `ASTER_AI_NEWS_ENDPOINT` | leer | Externe Quelle für Breaking News. |
| `ASTER_AI_NEWS_API_KEY` | leer | API-Token für den Sentinel. |
| `ASTER_AI_TEMPERATURE` | `0.3` | Kreativitäts-Override (1.0 = Provider-Default). |
| `ASTER_AI_DEBUG_STATE` | `false` | Aktiviert ausführliches Logging und Payload-Dumps. |
| `ASTER_BRACKETS_QUEUE_FILE` | `brackets_queue.json` | Queue-Datei für Schutz-Reparaturen. |

</details>

<details>
<summary><strong>Persistenzdateien</strong></summary>

- **`aster_state.json`** – Hauptspeicher für offene Positionen, KI-Telemetrie, Sentinel-Status und Dashboard-UI-Präferenzen. Lösche ihn für einen sauberen Neustart bei Inkonsistenzen.
- **`dashboard_config.json`** – Spiegelt den Editor wider. Sichere mehrere Presets oder entferne sie für Standardwerte.
- **`brackets_queue.json`** – Wird von `brackets_guard.py` gepflegt, um Stop/TP-Aufträge zu reparieren. Archiviere und entferne sie, wenn wiederholte Reparaturen auftreten.

Stoppe das Backend vor dem Bearbeiten oder Löschen dieser Dateien, um Teil-Schreibvorgänge zu vermeiden; verschiebe sie aus dem Repo, wenn du einen Snapshot vor einem frischen Lauf brauchst.

</details>

## 🔐 Sicherheitshinweis

- Live-Trading ist riskant: Probiere zuerst im Paper-Modus.
- Halte API-Keys privat und rotiere sie regelmäßig.
- Auch mit Caching solltest du frische Markt- und Orderdaten prüfen.
- Passe Budget- und Sentinel-Parameter an deine Risikotoleranz an.

Viel Erfolg beim Trading – und wenn du Bugs oder Ideen hast, eröffne gern ein Issue oder einen Pull Request!
