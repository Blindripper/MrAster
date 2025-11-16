# Skip-Analyse vom 16. November 2025

Auszug aus dem Debug-Log 16:02:42–17:03:05 UTC (siehe Task-Beschreibung) zeigt folgende Skip-Gründe:

| Grund                     | Anzahl |
|--------------------------|:------:|
| `edge_r`                 |   8    |
| `no_cross`               |   3    |
| `spread_tight`           |   2    |
| `stoch_rsi_trend_short`  |   2    |
| `long_overextended`      |   1    |

Die Mehrheit (>50 %) der Abweisungen stammt von `edge_r`, gefolgt von Signal-Absenz (`no_cross`). Diese Verteilung dient als Grundlage für die neue adaptive Relief-Logik in `aster_multi_bot.py`.
