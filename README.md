# MrAster Trading Bot

MrAster ist ein Python-basiertes Trading-Toolkit für Perpetual Futures auf Binance-kompatiblen Börsen. Das Projekt umfasst:

* `aster_multi_bot.py` – der Hauptbot mit Signal-Logik, Bandit-Policy und automatischer Bracket-Order-Verwaltung.
* `brackets_guard.py` – robuster Guard, der Stop-/Take-Profit-Orders repariert.
* `dashboard_server.py` + `dashboard_static/` – ein FastAPI-Dashboard zur Bot-Steuerung samt Log-Streaming.

## Neueste Optimierungen

* **HTTP-Stabilisierung:** Konfigurierbare Retries (`ASTER_HTTP_RETRIES`, `ASTER_HTTP_BACKOFF`, `ASTER_HTTP_TIMEOUT`) schützen vor transienten API-Fehlern.
* **Kline-Caching:** Mehrfach genutzte Kursdaten werden für `ASTER_KLINE_CACHE_SEC` Sekunden geteilt und auf Ausfälle mit Fallbacks abgesichert.
* **Requirements-Datei:** Vereinfachte Installation aller Abhängigkeiten über `requirements.txt`.

## Voraussetzungen

* Python ≥ 3.10 (empfohlen)
* Ein Binance- oder AsterDex-kompatibler Futures-Account (für Live-Betrieb)
* Optional: Zugangsdaten mit Leserechten für Papiermodus nicht notwendig

## Installation

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

## Konfiguration

Der Bot wird über Umgebungsvariablen gesteuert. Die wichtigsten Parameter:

| Variable | Bedeutung | Standard |
| --- | --- | --- |
| `ASTER_API_KEY` / `ASTER_API_SECRET` | Börsen-API-Zugang | leer |
| `ASTER_EXCHANGE_BASE` | REST-Endpunkt (z. B. `https://fapi.binance.com`) | `https://fapi.asterdex.com` |
| `ASTER_PAPER` | Papierhandel aktivieren (`true`/`false`) | `false` |
| `ASTER_RUN_ONCE` | Nur einen Scan durchführen | `false` |
| `ASTER_LOGLEVEL` | Log-Level (`DEBUG`, `INFO`, …) | `INFO` |
| `ASTER_HTTP_RETRIES` | Zusätzliche HTTP-Versuche bei Fehlern | `2` |
| `ASTER_HTTP_BACKOFF` | Basis-Verzögerung (Sekunden) für Retries | `0.6` |
| `ASTER_HTTP_TIMEOUT` | Request-Timeout in Sekunden | `20` |
| `ASTER_KLINE_CACHE_SEC` | Lebensdauer des Kline-Caches | `45` |

Weitere Strategie-Parameter (RSI-Limits, ATR-Multiplikatoren, Positionsgrößen, Universum usw.) lassen sich ebenfalls per ENV setzen; siehe Kopfsektion von `aster_multi_bot.py` bzw. das Dashboard (`/api/config`).

Zum lokalen Arbeiten kann eine `.env`-Datei genutzt werden (z. B. via `python-dotenv` oder manuelles Exportieren vor dem Start).

## Bot starten

```bash
# Papiermodus aktivieren, dann Bot starten
export ASTER_PAPER=true
python aster_multi_bot.py
```

*Mit `CTRL+C` (oder SIGTERM) wird der aktuelle Scan sauber beendet.*

Ein einzelner Analysezyklus lässt sich mit `ASTER_RUN_ONCE=true` ausführen. Der Bot speichert seinen Zustand in `aster_state.json` (Trades, Policy, FastTP-Cooldowns).

## Dashboard verwenden

1. Sicherstellen, dass die Abhängigkeiten installiert sind (`fastapi`, `uvicorn`).
2. Dashboard starten:

   ```bash
   python dashboard_server.py
   # oder mit Reload:
   uvicorn dashboard_server:app --host 0.0.0.0 --port 8000
   ```

3. Browser öffnen: `http://localhost:8000`
4. Logs live verfolgen (`/ws/logs`), Konfiguration bearbeiten und Bot-Prozess über die Buttons starten/stoppen.

Das Dashboard legt `dashboard_config.json` an und schreibt geänderte ENV-Werte zurück. Trades, offene Positionen und AI-Hints basieren auf `aster_state.json`.

## Sicherheit & Hinweise

* Live-Handel birgt finanzielle Risiken. Teste jede Änderung zunächst im Papiermodus.
* API-Schlüssel niemals im Repo oder in öffentlichen Tickets teilen.
* Durch das neue Caching können historische Daten beim API-Ausfall weiterverwendet werden – prüfe daher regelmäßig, ob die Kurse aktuell sind.

Viel Erfolg beim Trading! Beiträge und Issues sind willkommen.
