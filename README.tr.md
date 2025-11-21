<div align="center">
  <img src="assets/mraster-logo.png" alt="MrAster logosu" width="240" />
  <h1>MrAster Alım Satım Botu</h1>
  <p><strong>Dost canlısı kripto vadeli işlemler kopilotunuz: piyasayı izler, riski yönetir ve sizi haberdar eder.</strong></p>
  <p>
    <a href="#-60-saniyede-mraster">Neden MrAster?</a>
    ·
    <a href="#-hizli-baslangic">Hızlı başlangıç</a>
    ·
    <a href="#-dashboarda-genel-bakis">Dashboard turu</a>
    ·
    <a href="#-kaputun-altinda-yapimcilar-icin">Kaputun altında</a>
  </p>
</div>

<p align="center">
  <a href="https://www.python.org/" target="_blank"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python 3.10+" /></a>
  <a href="#-dashboarda-genel-bakis"><img src="https://img.shields.io/badge/Kontrol-Tertemiz%20web%20dashboardu-8A2BE2" alt="Dashboard" /></a>
  <a href="#-guvenlik-once"><img src="https://img.shields.io/badge/Mod-Paper%20veya%20canli-FF8C00" alt="Modlar" /></a>
  <a href="#-guvenlik-once"><img src="https://img.shields.io/badge/Uyarı-Alım%20satım%20risklidir-E63946" alt="Risk" /></a>
</p>

> “Backend’i aç, tarayıcıyı başlat ve ağır yükü kopilotlara bırak.”

---

## ✨ 60 saniyede MrAster

- **Stresiz otomatik işlem** – MrAster vadeli işlem piyasasını tarar, işlemler önerir ve yerleşik güvenlik korkuluklarıyla uygulayabilir.
- **Her zaman ulaşılabilir dashboard** – Botu başlat/durdur, risk sürgülerini ayarla ve tek sayfadan AI açıklamalarını oku.
- **Bütçene saygılı AI** – Günlük limitler, soğuma süreleri ve haber nöbetçisi kopilotları faydalı ve uygun maliyetli tutar.
- **Kurulumda sürpriz yok** – Gerçek emirlere geçmeden önce paper modunda prova yap.

## 🚀 Hızlı başlangıç

1. **Python ortamı kur**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
2. **Backend’i çalıştır**
   ```bash
   python dashboard_server.py
   # veya otomatik yenilemeyle
   uvicorn dashboard_server:app --host 0.0.0.0 --port 8000
   ```
3. **Tarayıcıda tamamla**
   <http://localhost:8000> adresini aç, borsa anahtarlarını (veya paper modu) bağla ve kılavuzu takip et.

> Konsolu mu tercih ediyorsun? `ASTER_PAPER=true` (opsiyonel) değişkenini ayarla ve `python aster_multi_bot.py` çalıştır. `ASTER_RUN_ONCE=true` tek tarama döngüsü yapar.

## 🖥️ Dashboard’a genel bakış

- **Tek tıkla kontrol** – `aster_multi_bot.py` gözetimli botunu terminale dokunmadan başlat, durdur veya yeniden başlat.
- **Canlı loglar ve uyarılar** – Her işlem fikrini, AI yanıtını ve koruma uyarısını anlık izle.
- **Risk ayarları kolay** – Low / Mid / High / ATT presetlerini seç veya her `ASTER_*` düğmesini değiştirmek için Pro moduna geç.
- **Güvenli konfigürasyon düzenleme** – Ortam ayarlarını güvenle güncelle; MrAster alanları uygulamadan önce doğrular.
- **AI kopilotlarını izle** – Net ticaret notlarını oku, harcanan bütçeyi gör ve doğrudan sohbet et.
- **Performans anlık görüntüleri** – PnL, işlem geçmişi ve piyasa ısı haritalarını sayfadan çıkmadan incele.

## 🛡️ Güvenlik önce

- **Paper mod**: Gerçek parayı riske atmadan stratejileri simüle edilmiş işlemlerle test et.
- **Bütçe sınırları**: AI yardımcıları günlük USD limitine uyar, limitleri manuel yükseltmedikçe.
- **Nöbetçi uyarıları**: Son dakika haberleri, alışılmadık funding ve volatilite sıçramaları anında görünür.
- **Kontrol sende**: Botu durdur, ayarları değiştir veya otonomiyi istediğin zaman duraklat.

## 🤓 Kaputun altında (yapımcılar için)

Motorları, korumaları ve konfigürasyonu merak mı ediyorsun? Aşağıdaki bölümleri aç.

<details>
<summary><strong>AI kopilot yığını</strong></summary>

- **AITradeAdvisor** her isteği rejim istatistikleri, order book bağlamı ve yapılandırılmış promptlarla paketler, iş parçacığı havuzu üzerinden (önbellek ve fiyat tablolarıyla) yollar ve overrides ile açıklamalar içeren JSON planlar döner.
- **DailyBudgetTracker + BudgetLearner** çift katmanlı harcama kontrolü sunar: tracker model başına ortalamaları tutar, learner ise sembol bütçelerini kaydırır ve edge düştüğünde pahalı çağrıları askıya alır; her OpenAI yanıtından sonra güncellenir.
- **NewsTrendSentinel** (`ASTER_AI_SENTINEL_*`) 24 saatlik piyasa verilerini ve isteğe bağlı haber akışını olay riski etiketlerine, boyut sınırlarına ve hype çarpanlarına dönüştürür.
- **PostmortemLearning** nitel işlem değerlendirmelerini kalıcı sayısal özelliklere çevirerek bir sonraki planın son çıkıştan ders almasını sağlar.
- **ParameterTuner** işlem sonuçlarını toplar, boyut/ATR ofsetlerini yeniden hesaplar ve yeterli istatistik toplanana kadar LLM önerilerine başvurmaz.
- **PlaybookManager** piyasa rejimleri, direktifler ve yapılandırılmış risk ayarlarından oluşan canlı bir oyun kitabını güncel tutar ve her payload’a ekler.
- **Bekleme kuyruğu ve eşzamanlılık korumaları** `ASTER_AI_CONCURRENCY`, `ASTER_AI_PENDING_LIMIT` ve global cooldown’larla otonomiyi sınırlar; API bütçesi korunurken bekleyen niyetler dashboard’da görünür.

</details>

<details>
<summary><strong>İşlem motoru</strong></summary>

- **Trend teyitli RSI sinyalleri** – `ASTER_*` değişkenleri veya dashboard editörüyle yapılandırılabilir.
- **Çok kollu bandit politikası (`BanditPolicy`)** LinUCB keşfini opsiyonel alfa modeli (`ml_policy.py`) ile harmanlar, TAKE/SKIP kararlarını ve S/M/L boyut kovalarını seçer.
- **Piyasa hijyeni filtreleri** beslemeyi temizler: funding ve spread limitleri, fitil filtreleri ve önbelleğe alınmış mum/24h ticker’lar gürültüyü azaltır.
- **Oracle duyarlı arbitraj koruması** (Jez, 2025) mark/oracle farkını premium endeksiyle kelepçeler ve funding tuzaklarından uzaklaştırır.

</details>

<details>
<summary><strong>Risk ve emir yönetimi</strong></summary>

- **BracketGuard** (`brackets_guard.py`) stop-loss ve take-profit emirlerini onarır, eski ve yeni bot imzalarını tanır.
- **FastTP** ATR tabanlı denetim noktaları ve cooldown mantığıyla ters hareketleri törpüler.
- **Sermaye ve pozisyon sınırları** (`ASTER_MAX_OPEN_*`, `ASTER_EQUITY_FRACTION`) ile kalıcı durum (`aster_state.json`) yeniden başlatmalar arasında süreklilik sağlar.

</details>

<details>
<summary><strong>Strateji, risk ve pozisyonlama</strong></summary>

| Değişken | Varsayılan | Açıklama |
| --- | --- | --- |
| `ASTER_INTERVAL` / `ASTER_HTF_INTERVAL` | `5m` / `30m` | Sinyal ve teyit zaman aralıkları. |
| `ASTER_RSI_BUY_MIN` / `ASTER_RSI_SELL_MAX` | `49` / `51`* | Long/short girişleri için RSI eşikleri. |
| `ASTER_ALLOW_TREND_ALIGN` | `false` | Zaman dilimleri arasında trend hizası zorunlu. |
| `ASTER_TREND_BIAS` | `with` | Trendle veya trende karşı işlem. |
| `ASTER_MIN_QUOTE_VOL_USDT` | `800000` | İşlem yapılabilir minimum hacim. |
| `ASTER_SPREAD_BPS_MAX` | `0.0020` | Maksimum bid/ask spread’i (bps). |
| `ASTER_WICKINESS_MAX` | `0.97` | Aşırı oynak mumları filtreler. |
| `ASTER_MIN_EDGE_R` | `0.04` | İşlemi onaylamak için gereken minimum edge (R cinsinden). |
| `ASTER_DEFAULT_NOTIONAL` | `0` | Adaptif veri yoksa temel notional (0 = AI hesaplar). |
| `ASTER_SIZE_MULT_FLOOR` | `0` | Pozisyon boyutu için taban çarpan (1.0 = temel notional zorunlu). |
| `ASTER_MAX_NOTIONAL_USDT` | `0` | Emir notional’ı için sert sınır (0 = kaldıraç/sermaye korumaları karar verir). |
| `ASTER_SIZE_MULT_CAP` | `3.0` | Tüm ayarlardan sonraki maksimum boyut çarpanı. |
| `ASTER_CONFIDENCE_SIZING` | `true` | Güven temelli boyutlandırmayı etkinleştirir. |
| `ASTER_CONFIDENCE_SIZE_MIN` / `ASTER_CONFIDENCE_SIZE_MAX` | `1.0` / `3.0` | Çarpanın alt/üst hedefi. |
| `ASTER_CONFIDENCE_SIZE_BLEND` / `ASTER_CONFIDENCE_SIZE_EXP` | `1` / `2.0` | Karışım ağırlığı ve üs (>1 yüksek güveni destekler). |
| `ASTER_RISK_PER_TRADE` | `0.007`* | İşlem başına riske edilen sermaye oranı. |
| `ASTER_EQUITY_FRACTION` | `0.66` | Maksimum kullanılan sermaye payı (presetler 33% / 66% / 100%). |
| `ASTER_LEVERAGE` | `10` | Varsayılan kaldıraç (Low 4× / Mid 10× / High & ATT borsa maksimumu). |
| `ASTER_MAX_OPEN_GLOBAL` | `0` | Eşzamanlı pozisyon sınırı (0 = sınırsız). |
| `ASTER_MAX_OPEN_PER_SYMBOL` | `1` | Sembol başına pozisyon sınırı (0 = sınırsız). |
| `ASTER_SL_ATR_MULT` / `ASTER_TP_ATR_MULT` | `1.0` / `1.6` | Stop ve take-profit için ATR çarpanları. |
| `FAST_TP_ENABLED` | `true` | FastTP’yi açar. |
| `FASTTP_MIN_R` | `0.30` | FastTP tetiklenmeden önce gereken minimum kâr (R). |
| `FAST_TP_RET1` / `FAST_TP_RET3` | `-0.0010` / `-0.0020` | FastTP geri çekilme eşikleri. |
| `FASTTP_SNAP_ATR` | `0.25` | Snap mekanizması için ATR mesafesi. |
| `FASTTP_COOLDOWN_S` | `15` | FastTP kontrolleri arasındaki süre. |
| `ASTER_FUNDING_FILTER_ENABLED` | `true` | Funding filtresini açar. |
| `ASTER_FUNDING_MAX_LONG` / `ASTER_FUNDING_MAX_SHORT` | `0.0010` | Yön başına funding limitleri. |
| `ASTER_NON_ARB_FILTER_ENABLED` | `true` | Mark/oracle klempini etkinleştirir. |
| `ASTER_NON_ARB_CLAMP_BPS` | `0.0005` | Premium klempi genişliği (±bps). |
| `ASTER_NON_ARB_EDGE_THRESHOLD` | `0.00005` | Bloklama öncesi izin verilen funding edge. |
| `ASTER_NON_ARB_SKIP_GAP` | `0.0030` | Skip zorunluluğu oluşturan mark/oracle farkı. |

*Dashboard’dan başlatıldığında RSI 51/49 ve risk 0.007 olarak tohumlanır. Sadece CLI ile açıldığında 52/48 ve 0.006 değerleri kullanılır; üzerine yazana veya `dashboard_config.json` ile senkronlayana kadar.*

</details>

<details>
<summary><strong>AI, otomasyon ve korumalar</strong></summary>

| Değişken | Varsayılan | Açıklama |
| --- | --- | --- |
| `ASTER_BANDIT_ENABLED` | `true` | LinUCB politikasını etkinleştirir. |
| `ASTER_AI_MODE` | `false` | Standard/Pro olsa bile AI çalıştırır (`ASTER_MODE=ai`). |
| `ASTER_ALPHA_ENABLED` | `true` | Opsiyonel alfa modelini aç/kapat. |
| `ASTER_ALPHA_THRESHOLD` | `0.55` | İşlemi onaylamak için minimum güven. |
| `ASTER_ALPHA_PROMOTE_DELTA` | `0.15` | Pozisyon büyütmek için ek güven. |
| `ASTER_HISTORY_MAX` | `250` | Analiz için tutulan işlem geçmişi. |
| `ASTER_OPENAI_API_KEY` | boş | AITradeAdvisor için API anahtarı. |
| `ASTER_CHAT_OPENAI_API_KEY` | boş | Chat’e özel anahtar; yoksa ana anahtarı kullanır. |
| `ASTER_AI_MODEL` | `gpt-4.1` | AI modeli kimliği. |
| `ASTER_AI_DAILY_BUDGET_USD` | `20` | Günlük bütçe (USD); `ASTER_PRESET_MODE=high/att` iken yok sayılır. |
| `ASTER_AI_STRICT_BUDGET` | `true` | Bütçe bitince AI çağrılarını durdurur. |
| `ASTER_AI_MIN_INTERVAL_SECONDS` | `3` | Aynı sembolü yeniden değerlendirmeden önceki cooldown. |
| `ASTER_AI_CONCURRENCY` | `4` | Eşzamanlı LLM isteği sınırı. |
| `ASTER_AI_PENDING_LIMIT` | `max(4, 3×concurrency)` | Bekleyen AI iş kuyruğu limiti. |
| `ASTER_AI_GLOBAL_COOLDOWN_SECONDS` | `1.0` | İstekler arası global bekleme. |
| `ASTER_AI_PLAN_TIMEOUT_SECONDS` | `45` | Plan bekleme süresi; aşılırsa fallback devreye girer. |
| `ASTER_AI_SENTINEL_ENABLED` | `true` | Haber nöbetçisini açar. |
| `ASTER_AI_SENTINEL_DECAY_MINUTES` | `60` | Haber uyarısı ömrü. |
| `ASTER_AI_NEWS_ENDPOINT` | boş | Harici haber kaynağı. |
| `ASTER_AI_NEWS_API_KEY` | boş | Sentinel için API token. |
| `ASTER_AI_TEMPERATURE` | `0.3` | Yaratıcılık ayarı (1.0 = varsayılan sağlayıcı değeri). |
| `ASTER_AI_DEBUG_STATE` | `false` | Ayrıntılı loglar ve payload dökümlerini açar. |
| `ASTER_BRACKETS_QUEUE_FILE` | `brackets_queue.json` | Koruma onarımları için kuyruk dosyası. |

</details>

<details>
<summary><strong>Kalıcı dosyalar</strong></summary>

- **`aster_state.json`** – Açık pozisyonlar, AI telemetrisi, sentinel durumu ve dashboard tercihlerini saklar. Tutarsızlıkta temiz başlangıç için sil.
- **`dashboard_config.json`** – Dashboard editörünü yansıtır. Birden fazla preset için yedekle veya varsayılanlara dönmek için sil.
- **`brackets_queue.json`** – `brackets_guard.py` tarafından stop/TP onarımları için tutulur. Tekrarlayan onarımlar görürsen arşivle ve kaldır.

Kısmi yazımları önlemek için bu dosyaları düzenlemeden/silmeden önce backend’i durdur; yeni bir oturumdan önce anlık görüntü gerekiyorsa repo dışına taşı.

</details>

## 🔐 Güvenlik notu

- Canlı işlem risklidir: önce paper modunda dene.
- API anahtarlarını gizli tut ve düzenli olarak değiştir.
- Önbellek olsa bile piyasa ve emir verilerinin güncel olduğundan emin ol.
- Bütçe ve sentinel parametrelerini risk iştahına göre ayarla.

Keyifli işlemler! Bir hata veya fikir bulursan issue ya da pull request aç.
