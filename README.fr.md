<div align="center">
  <img src="assets/mraster-logo.png" alt="Logo MrAster" width="240" />
  <h1>Bot de trading MrAster</h1>
  <p><strong>Votre copilote crypto-futures : surveille le marché, gère le risque et vous tient informé.</strong></p>
  <p>
    <a href="#-mraster-en-60-secondes">Pourquoi MrAster ?</a>
    ·
    <a href="#-demarrage-rapide">Démarrage rapide</a>
    ·
    <a href="#-tour-dhorizon-du-dashboard">Tour du dashboard</a>
    ·
    <a href="#-sous-le-capot-pour-les-makers">Sous le capot</a>
  </p>
</div>

<p align="center">
  <a href="https://www.python.org/" target="_blank"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python 3.10+" /></a>
  <a href="#-tour-dhorizon-du-dashboard"><img src="https://img.shields.io/badge/Contrôle-Dashboard%20web%20clair-8A2BE2" alt="Dashboard" /></a>
  <a href="#-priorite-a-la-securite"><img src="https://img.shields.io/badge/Mode-Paper%20ou%20live-FF8C00" alt="Modes" /></a>
  <a href="#-priorite-a-la-securite"><img src="https://img.shields.io/badge/Rappel-Le%20trading%20comporte%20des%20risques-E63946" alt="Risque" /></a>
</p>

> « Démarrez le backend, ouvrez le navigateur et laissez les copilotes s’occuper du reste. »

---

## ✨ MrAster en 60 secondes

- **Trading automatisé en douceur** – MrAster scanne le marché des futures, propose des trades et peut les exécuter avec des garde-fous intégrés.
- **Dashboard toujours accessible** – Lancez ou arrêtez le bot, ajustez le risque et lisez les explications de l’IA sur une page unique.
- **Une IA respectueuse du budget** – Plafonds journaliers, temps de repos et sentinelle d’actualités pour rester efficace sans exploser les coûts.
- **Installation sans surprise** – Entraînez-vous en mode papier avant de basculer sur des ordres réels.

## 🚀 Démarrage rapide

1. **Préparez Python**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
2. **Lancez le backend**
   ```bash
   python dashboard_server.py
   # ou activez l’auto-reload
   uvicorn dashboard_server:app --host 0.0.0.0 --port 8000
   ```
3. **Finalisez dans le navigateur**
   Ouvrez <http://localhost:8000>, connectez vos clés d’exchange (ou le mode papier) et suivez l’assistant.

> Plutôt en mode headless ? Exportez `ASTER_PAPER=true` (optionnel) puis lancez `python aster_multi_bot.py`. Avec `ASTER_RUN_ONCE=true`, un seul cycle de scan est exécuté.

## 🖥️ Tour d’horizon du dashboard

- **Contrôle en un clic** – Démarrez, arrêtez ou relancez le bot supervisé (`aster_multi_bot.py`) sans passer par le terminal.
- **Logs & alertes en direct** – Suivez chaque idée de trade, réponse IA et alerte de garde en temps réel.
- **Le risque, simplement** – Choisissez un preset (Low / Mid / High / ATT) ou passez en mode Pro pour ajuster chaque variable `ASTER_*`.
- **Édition de config sécurisée** – Modifiez votre environnement en toute sécurité : MrAster valide chaque champ avant application.
- **Copilotes IA visibles** – Lisez des notes claires, surveillez le budget consommé et échangez directement avec eux.
- **Instantanés de performance** – Consultez PnL, historique des trades et heatmaps sans changer d’onglet.

## 🛡️ Priorité à la sécurité

- **Mode papier** : testez vos stratégies avec des exécutions simulées avant de risquer vos fonds.
- **Plafonds budgétaires** : les copilotes IA respectent votre limite quotidienne tant que vous ne la relevez pas.
- **Alertes sentinelles** : actualités brûlantes, funding atypique et pics de volatilité s’affichent instantanément.
- **Vous gardez la main** : arrêtez le bot, modifiez la config ou suspendez l’autonomie quand vous le souhaitez.

## 🤓 Sous le capot (pour les makers)

Envie d’en savoir plus sur les moteurs, les garde-fous et la configuration ? Dépliez les sections suivantes.

<details>
<summary><strong>Stack des copilotes IA</strong></summary>

- **AITradeAdvisor** compose chaque requête avec statistiques de régime, contexte carnet d’ordres et prompts structurés, les envoie via un pool de threads (avec cache et barèmes de prix) puis renvoie des plans JSON avec overrides et explications.
- **DailyBudgetTracker + BudgetLearner** assurent un double contrôle des dépenses : un grand livre roulant suit les moyennes par modèle tandis que le learner réalloue les budgets symboles et met en pause les appels coûteux quand l’edge diminue, le tout mis à jour après chaque réponse OpenAI.
- **NewsTrendSentinel** (`ASTER_AI_SENTINEL_*`) fusionne statistiques 24h et actualités externes en étiquettes de risque événementiel, limites de taille et multiplicateurs de hype avant même l’Advisor.
- **PostmortemLearning** distille les revues qualitatives en features numériques persistantes pour que le prochain plan tienne compte de la sortie précédente.
- **ParameterTuner** agrège les résultats de trades, recalcule les biais taille/ATR et ne sollicite l’IA que lorsque la statistique devient significative.
- **PlaybookManager** maintient un playbook vivant de régimes de marché, directives et ajustements structurés de risque injectés dans chaque payload.
- **File d’attente et garde-fous de concurrence** modèrent l’autonomie via `ASTER_AI_CONCURRENCY`, `ASTER_AI_PENDING_LIMIT` et des cooldowns globaux afin de préserver l’API et le budget tout en affichant les intentions dans le dashboard.

</details>

<details>
<summary><strong>Moteur de trading</strong></summary>

- **Signaux RSI avec confirmation de tendance** configurables via les variables `ASTER_*` ou l’éditeur du dashboard.
- **Politique bandit multi-bras (`BanditPolicy`)** mêlant exploration LinUCB et modèle alpha optionnel (`ml_policy.py`) pour décider des actions TAKE/SKIP et des tailles S/M/L.
- **Filtres d’hygiène de marché** : gardes sur funding, spread, mèches et caches de chandeliers/24h lissent le bruit de l’exchange.
- **Garde anti-arbitrage aware oracle** pince l’écart mark/oracle avec l’indice de prime (Jez, 2025) et éloigne des pièges de funding.

</details>

<details>
<summary><strong>Gestion du risque & des ordres</strong></summary>

- **BracketGuard** (`brackets_guard.py`) répare stops et take-profits tout en comprenant les signatures anciennes comme nouvelles.
- **FastTP** réduit les mouvements adverses grâce à des checkpoints basés sur l’ATR et une logique de cooldown.
- **Plafonds sur capital et exposition** (`ASTER_MAX_OPEN_*`, `ASTER_EQUITY_FRACTION`) plus l’état persistant (`aster_state.json`) garantissent la continuité lors des redémarrages.

</details>

<details>
<summary><strong>Stratégie, risque et positionnement</strong></summary>

| Variable | Valeur par défaut | Description |
| --- | --- | --- |
| `ASTER_INTERVAL` / `ASTER_HTF_INTERVAL` | `5m` / `30m` | Périodes des signaux et de la confirmation. |
| `ASTER_RSI_BUY_MIN` / `ASTER_RSI_SELL_MAX` | `49` / `51`* | Seuils RSI pour entrées long / short. |
| `ASTER_ALLOW_TREND_ALIGN` | `false` | Force l’alignement des tendances entre horizons. |
| `ASTER_TREND_BIAS` | `with` | Trade dans / contre la tendance. |
| `ASTER_MIN_QUOTE_VOL_USDT` | `900000` | Volume minimal des symboles. |
| `ASTER_SPREAD_BPS_MAX` | `0.0020` | Spread bid/ask maximal (bps). |
| `ASTER_WICKINESS_MAX` | `0.97` | Filtre des chandeliers trop volatils. |
| `ASTER_MIN_EDGE_R` | `0.04` | Edge minimal (en R) pour valider un trade. |
| `ASTER_DEFAULT_NOTIONAL` | `0` | Notionnel de base si aucune donnée adaptative (0 = calculé par l’IA). |
| `ASTER_SIZE_MULT_FLOOR` | `0` | Multiplicateur minimum de taille (1.0 impose le notionnel de base). |
| `ASTER_MAX_NOTIONAL_USDT` | `0` | Limite dure sur le notionnel (0 = laissent les gardes levier/équité décider). |
| `ASTER_SIZE_MULT_CAP` | `3.0` | Multiplicateur maximal après ajustements. |
| `ASTER_CONFIDENCE_SIZING` | `true` | Active le dimensionnement basé sur la confiance. |
| `ASTER_CONFIDENCE_SIZE_MIN` / `ASTER_CONFIDENCE_SIZE_MAX` | `1.0` / `3.0` | Bornes inférieure / supérieure du multiplicateur. |
| `ASTER_CONFIDENCE_SIZE_BLEND` / `ASTER_CONFIDENCE_SIZE_EXP` | `1` / `2.0` | Poids de mélange et exposant (>1 favorise la haute confiance). |
| `ASTER_RISK_PER_TRADE` | `0.007`* | Part du capital risquée par trade. |
| `ASTER_EQUITY_FRACTION` | `0.66` | Part maximale du capital engagée (33 % / 66 % / 100 % via les presets). |
| `ASTER_LEVERAGE` | `10` | Effet de levier par défaut (presets : 4× / 10× / max exchange). |
| `ASTER_MAX_OPEN_GLOBAL` | `0` | Limite globale de positions ouvertes (0 = illimité). |
| `ASTER_MAX_OPEN_PER_SYMBOL` | `1` | Limite par symbole (0 = illimité). |
| `ASTER_SL_ATR_MULT` / `ASTER_TP_ATR_MULT` | `1.0` / `1.6` | Multiplicateurs ATR pour stop et take profit. |
| `FAST_TP_ENABLED` | `true` | Active FastTP. |
| `FASTTP_MIN_R` | `0.30` | Gain minimal (en R) avant déclenchement FastTP. |
| `FAST_TP_RET1` / `FAST_TP_RET3` | `-0.0010` / `-0.0020` | Seuils de retracement pour FastTP. |
| `FASTTP_SNAP_ATR` | `0.25` | Distance ATR pour le mécanisme snap. |
| `FASTTP_COOLDOWN_S` | `15` | Délai entre vérifications FastTP. |
| `ASTER_FUNDING_FILTER_ENABLED` | `true` | Active le filtre funding. |
| `ASTER_FUNDING_MAX_LONG` / `ASTER_FUNDING_MAX_SHORT` | `0.0010` | Limites funding par direction. |
| `ASTER_NON_ARB_FILTER_ENABLED` | `true` | Active la pince mark/oracle anti-arbitrage. |
| `ASTER_NON_ARB_CLAMP_BPS` | `0.0005` | Largeur de la pince (±bps). |
| `ASTER_NON_ARB_EDGE_THRESHOLD` | `0.00005` | Edge funding toléré avant blocage. |
| `ASTER_NON_ARB_SKIP_GAP` | `0.0030` | Ecart mark/oracle déclenchant un skip immédiat. |

*Au lancement depuis le dashboard, les valeurs par défaut sont RSI 51/49 et risque 0.007. En CLI uniquement, la graine est 52/48 et 0.006 jusqu’à ce que vous les remplaciez ou synchronisiez via `dashboard_config.json`.*

</details>

<details>
<summary><strong>IA, automatisation et garde-fous</strong></summary>

| Variable | Valeur par défaut | Description |
| --- | --- | --- |
| `ASTER_BANDIT_ENABLED` | `true` | Active la politique LinUCB. |
| `ASTER_AI_MODE` | `false` | Force l’exécution IA même en mode Standard/Pro (`ASTER_MODE=ai`). |
| `ASTER_ALPHA_ENABLED` | `true` | Active le modèle alpha optionnel. |
| `ASTER_ALPHA_THRESHOLD` | `0.55` | Confiance minimale pour valider un trade. |
| `ASTER_ALPHA_PROMOTE_DELTA` | `0.15` | Confiance additionnelle pour augmenter la taille. |
| `ASTER_HISTORY_MAX` | `250` | Profondeur d’historique utilisée pour l’analyse. |
| `ASTER_OPENAI_API_KEY` | vide | Clé API pour AITradeAdvisor. |
| `ASTER_CHAT_OPENAI_API_KEY` | vide | Clé dédiée au chat, retombe sur la principale sinon. |
| `ASTER_AI_MODEL` | `gpt-4.1` | ID du modèle. |
| `ASTER_AI_DAILY_BUDGET_USD` | `20` | Budget quotidien en USD ; ignoré pour `ASTER_PRESET_MODE=high/att`. |
| `ASTER_AI_STRICT_BUDGET` | `true` | Coupe les appels IA après dépassement du budget. |
| `ASTER_AI_MIN_INTERVAL_SECONDS` | `3` | Cooldown avant réévaluation du même symbole. |
| `ASTER_AI_CONCURRENCY` | `4` | Nombre maximal de requêtes LLM simultanées. |
| `ASTER_AI_PENDING_LIMIT` | `max(4, 3×concurrency)` | Limite de la file d’attente IA. |
| `ASTER_AI_GLOBAL_COOLDOWN_SECONDS` | `1.0` | Pause globale entre requêtes. |
| `ASTER_AI_PLAN_TIMEOUT_SECONDS` | `45` | Délai avant bascule sur les fallback. |
| `ASTER_AI_SENTINEL_ENABLED` | `true` | Active la sentinelle d’actualités. |
| `ASTER_AI_SENTINEL_DECAY_MINUTES` | `60` | Durée de vie d’une alerte. |
| `ASTER_AI_NEWS_ENDPOINT` | vide | Source externe d’actualités. |
| `ASTER_AI_NEWS_API_KEY` | vide | Jeton API pour la sentinelle. |
| `ASTER_AI_TEMPERATURE` | `0.3` | Ajustement de créativité (1.0 = valeur fournisseur). |
| `ASTER_AI_DEBUG_STATE` | `false` | Active les logs détaillés et dumps de payloads. |
| `ASTER_BRACKETS_QUEUE_FILE` | `brackets_queue.json` | Fichier de file d’attente pour les réparations de garde-fous. |

</details>

<details>
<summary><strong>Fichiers de persistance</strong></summary>

- **`aster_state.json`** – Stocke positions ouvertes, télémétrie IA, état sentinelle et préférences UI. Supprimez-le pour repartir de zéro en cas d’incohérence.
- **`dashboard_config.json`** – Réplique l’éditeur du dashboard. Sauvegardez-le pour plusieurs presets ou supprimez-le pour revenir aux valeurs de base.
- **`brackets_queue.json`** – Maintenu par `brackets_guard.py` pour restaurer stops/TP. Archivez puis supprimez-le si les réparations deviennent répétitives.

Coupez le backend avant toute édition ou suppression afin d’éviter les écritures partielles ; déplacez les fichiers hors du dépôt si vous avez besoin d’un snapshot.

</details>

## 🔐 Rappel sécurité

- Le trading live est risqué : commencez en mode papier.
- Gardez vos clés API confidentielles et changez-les régulièrement.
- Même avec du cache, vérifiez la fraîcheur des données marché et ordres.
- Ajustez budget et paramètres sentinelle à votre profil de risque.

Bon trading ! Si vous repérez un bug ou avez une idée, ouvrez un issue ou un pull request.
