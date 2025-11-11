<div align="center">
  <img src="assets/mraster-logo.png" alt="MrAster 로고" width="240" />
  <h1>MrAster 트레이딩 봇</h1>
  <p><strong>친근한 크립토 선물 코파일럿: 시장을 살피고, 리스크를 관리하며, 항상 소식을 전해드립니다.</strong></p>
  <p>
    <a href="#-60%ec%b4%88%eb%a7%8c%ec%97%90-%eb%a7%88%ec%8a%a4%ed%84%b0">왜 MrAster인가요?</a>
    ·
    <a href="#-%eb%b9%84%ea%b3%b5-%ec%8b%a4%ec%8a%b5">빠른 시작</a>
    ·
    <a href="#-%eb%8c%80%ec%8b%9c%eb%b3%b4%eb%93%9c-%ed%88%ac%ec%96%b4">대시보드 한눈에 보기</a>
    ·
    <a href="#-%eb%b9%84%ed%95%b4%ec%9d%bc-%ec%a3%bc%ec%86%8c">엔진 속 살펴보기</a>
  </p>
</div>

<p align="center">
  <a href="https://www.python.org/" target="_blank"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python 3.10+" /></a>
  <a href="#-%eb%8c%80%ec%8b%9c%eb%b3%b4%eb%93%9c-%ed%88%ac%ec%96%b4"><img src="https://img.shields.io/badge/%ec%bb%a8%ed%8a%b8%eb%a1%a4-%eb%a7%a5%ec%a0%9c%ed%95%9c%20%ec%9b%b9%20%eb%8c%80%ec%8b%9c%eb%b3%b4%eb%93%9c-8A2BE2" alt="Dashboard" /></a>
  <a href="#-%eb%b3%b4%ec%95%88-%ec%9a%b0%ec%84%a0"><img src="https://img.shields.io/badge/%eb%aa%a8%eb%93%9c-Paper%20%eb%98%90%eb%8a%94%20Live-FF8C00" alt="Modes" /></a>
  <a href="#-%eb%b3%b4%ec%95%88-%ec%9a%b0%ec%84%a0"><img src="https://img.shields.io/badge/%ea%b8%b0%ec%96%b5-%ed%8a%b8%eb%a0%88%ec%9d%b4%eb%94%a9%ec%9d%80%20%ec%9c%84%ed%97%98%ed%95%b4%ec%9a%94-E63946" alt="Risk" /></a>
</p>

> “백엔드를 켜고, 브라우저를 열고, 무거운 일은 코파일럿에게 맡기세요.”

---

## ✨ 60초만에 MrAster

- **스트레스 없는 자동 매매** – MrAster가 선물 시장을 스캔하고, 트레이드를 제안하며, 내장된 가드레일로 직접 실행합니다.
- **항상 열려 있는 대시보드** – 봇을 시작/중지하고, 리스크 슬라이더를 조정하며, 한 페이지에서 AI 설명을 확인하세요.
- **예산을 존중하는 AI** – 일일 한도, 쿨다운, 뉴스 센티넬 덕분에 코파일럿이 유용하면서도 합리적인 비용으로 운영됩니다.
- **혼란 없는 설정** – 실거래 전에는 페이퍼 모드로 충분히 연습하세요.

## 🚀 빠른 시작

1. **Python 설정**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
2. **백엔드 실행**
   ```bash
   python dashboard_server.py
   # 또는 자동 리로드 사용
   uvicorn dashboard_server:app --host 0.0.0.0 --port 8000
   ```
3. **브라우저에서 마무리**
   <http://localhost:8000>을 열고, 거래소 키(또는 페이퍼 모드)를 연결한 뒤 안내에 따라 진행하세요.

> 헤드리스 모드가 더 편하신가요? `ASTER_PAPER=true`(선택)을 설정한 뒤 `python aster_multi_bot.py`를 실행하세요. `ASTER_RUN_ONCE=true`를 주면 단 한 번만 스캔합니다.

## 🖥️ 대시보드 투어

- **원클릭 제어** – `aster_multi_bot.py` 감독 봇을 터미널 없이 시작·중지·재시작합니다.
- **실시간 로그 & 알림** – 모든 트레이드 아이디어, AI 응답, 가드 경고를 실시간으로 확인하세요.
- **쉽게 조절하는 리스크** – Low / Mid / High / ATT 프리셋을 고르거나 Pro 모드에서 모든 `ASTER_*` 변수를 세밀 조정하세요.
- **안전한 설정 편집** – 환경을 안전하게 업데이트하면 MrAster가 필드를 검증합니다.
- **AI 코파일럿 모니터링** – 알기 쉬운 노트, 사용 예산, 대화까지 한눈에 봅니다.
- **성과 스냅샷** – PnL, 트레이드 기록, 시장 히트맵을 페이지 이동 없이 확인하세요.

## 🛡️ 보안 우선

- **페이퍼 모드**: 실거래 전 시뮬레이션으로 전략을 리허설하세요.
- **예산 한도**: AI 도우미는 일일 USD 한도를 준수합니다(직접 상향하지 않는 한).
- **센티넬 알림**: 속보, 비정상적인 펀딩, 변동성 급등이 즉시 표시됩니다.
- **항상 사용자가 주도**: 봇을 멈추거나, 설정을 바꾸거나, 자율성을 일시 중지하세요.

## 🤓 엔진 속 살펴보기 (메이커를 위해)

엔진, 가드, 설정 표면에 대해 궁금하다면 아래 섹션을 펼쳐보세요.

<details>
<summary><strong>AI 코파일럿 스택</strong></summary>

- **AITradeAdvisor**가 레짐 통계, 호가창 컨텍스트, 구조화된 프롬프트를 하나로 묶어 스레드 풀에 전달하고(캐시와 요금표 준수), override와 설명이 포함된 JSON 플랜을 반환합니다.
- **DailyBudgetTracker + BudgetLearner**가 이중 예산 게이트를 구성합니다: 트래커가 모델별 평균을 유지하고, 러너가 심볼 예산을 조정하며 엣지가 약해지면 비용 높은 호출을 건너뜁니다. 모든 업데이트는 OpenAI 응답 이후 즉시 반영됩니다.
- **NewsTrendSentinel** (`ASTER_AI_SENTINEL_*`)은 24시간 시장 데이터와 외부 뉴스를 결합해 이벤트 리스크 라벨, 사이즈 클램프, 하이프 배수를 만든 뒤 어드바이저에게 전달합니다.
- **PostmortemLearning**이 정성적 회고를 지속 가능한 수치 피처로 정제해 다음 플랜이 이전 종료에서 배운 내용을 기억하도록 합니다.
- **ParameterTuner**가 트레이드 결과를 수집하고 사이즈/ATR 편향을 재계산하며 충분한 통계가 모일 때까지 LLM 제안을 사용하지 않습니다.
- **PlaybookManager**는 시장 레짐, 지침, 구조적 리스크 조정을 담은 플레이북을 지속적으로 갱신해 모든 페이로드에 주입합니다.
- **대기열 및 동시성 가드**가 `ASTER_AI_CONCURRENCY`, `ASTER_AI_PENDING_LIMIT`, 전역 쿨다운으로 자율성을 관리해 API와 예산을 보호하면서도 의도를 대시보드에 표시합니다.

</details>

<details>
<summary><strong>트레이딩 엔진</strong></summary>

- **추세 확인을 곁들인 RSI 신호** – `ASTER_*` 변수 또는 대시보드 편집기로 조정 가능합니다.
- **멀티암 밴딧 정책(`BanditPolicy`)** – LinUCB 탐색과 선택형 알파 모델(`ml_policy.py`)을 결합해 TAKE/SKIP, 사이즈 버킷(S/M/L)을 결정합니다.
- **시장 위생 필터** – 펀딩·스프레드 제한, 긴 심지 필터, 캐시된 캔들/24h 티커로 거래소 노이즈를 줄입니다.
- **오라클 인지 비차익 가드** – 프리미엄 인덱스(Jez, 2025)를 사용해 마크/오라클 격차를 조이고 펀딩 함정을 피합니다.

</details>

<details>
<summary><strong>리스크 & 주문 관리</strong></summary>

- **BracketGuard** (`brackets_guard.py`)가 스탑/테이크 프로핏 주문을 수리하며 구버전·신버전 봇 시그니처를 모두 인식합니다.
- **FastTP**는 ATR 기반 체크포인트와 쿨다운 로직으로 불리한 움직임을 줄입니다.
- **자본 및 익스포저 한계** (`ASTER_MAX_OPEN_*`, `ASTER_EQUITY_FRACTION`)와 지속 상태(`aster_state.json`)가 재시작 간 연속성을 보장합니다.

</details>

<details>
<summary><strong>전략, 리스크, 포지셔닝</strong></summary>

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `ASTER_INTERVAL` / `ASTER_HTF_INTERVAL` | `5m` / `30m` | 신호 및 확인 타임프레임. |
| `ASTER_RSI_BUY_MIN` / `ASTER_RSI_SELL_MAX` | `51` / `49`* | 롱/숏 진입 RSI 기준. |
| `ASTER_ALLOW_TREND_ALIGN` | `false` | 타임프레임 간 추세 정렬을 강제합니다. |
| `ASTER_TREND_BIAS` | `with` | 추세와 함께 혹은 역추세로 매매. |
| `ASTER_MIN_QUOTE_VOL_USDT` | `150000` | 거래 가능한 최소 거래대금. |
| `ASTER_SPREAD_BPS_MAX` | `0.0030` | 허용 최대 스프레드(bps). |
| `ASTER_WICKINESS_MAX` | `0.97` | 과도한 심지의 캔들을 필터링. |
| `ASTER_MIN_EDGE_R` | `0.30` | 트레이드를 승인하기 위한 최소 엣지(R). |
| `ASTER_DEFAULT_NOTIONAL` | `0` | 적응 데이터가 없을 때의 기본 노셔널(0 = AI 계산). |
| `ASTER_SIZE_MULT_FLOOR` | `0` | 포지션 사이즈 최소 배수(1.0 = 기본 노셔널 강제). |
| `ASTER_MAX_NOTIONAL_USDT` | `0` | 주문 노셔널 상한(0 = 레버리지/자본 가드 결정). |
| `ASTER_SIZE_MULT_CAP` | `3.0` | 모든 조정 후 최대 사이즈 배수. |
| `ASTER_CONFIDENCE_SIZING` | `true` | 신뢰도 기반 사이징을 활성화. |
| `ASTER_CONFIDENCE_SIZE_MIN` / `ASTER_CONFIDENCE_SIZE_MAX` | `1.0` / `3.0` | 배수의 최소/최대 목표. |
| `ASTER_CONFIDENCE_SIZE_BLEND` / `ASTER_CONFIDENCE_SIZE_EXP` | `1` / `2.0` | 블렌드 가중치와 지수(>1이면 높은 신뢰 반영). |
| `ASTER_RISK_PER_TRADE` | `0.007`* | 트레이드당 자본 비율. |
| `ASTER_EQUITY_FRACTION` | `0.66` | 동시 사용 가능한 자본 비율(프리셋 33% / 66% / 100%). |
| `ASTER_LEVERAGE` | `10` | 기본 레버리지(Low 4× / Mid 10× / High & ATT 거래소 최대). |
| `ASTER_MAX_OPEN_GLOBAL` | `0` | 동시 포지션 수 제한(0 = 제한 없음). |
| `ASTER_MAX_OPEN_PER_SYMBOL` | `1` | 심볼별 포지션 제한(0 = 제한 없음). |
| `ASTER_SL_ATR_MULT` / `ASTER_TP_ATR_MULT` | `1.0` / `1.6` | 스탑·테이크 프로핏 ATR 배수. |
| `FAST_TP_ENABLED` | `true` | FastTP 활성화. |
| `FASTTP_MIN_R` | `0.30` | FastTP가 동작하기 전 최소 이익(R). |
| `FAST_TP_RET1` / `FAST_TP_RET3` | `-0.0010` / `-0.0020` | FastTP 리트레이스먼트 기준. |
| `FASTTP_SNAP_ATR` | `0.25` | 스냅 메커니즘을 위한 ATR 거리. |
| `FASTTP_COOLDOWN_S` | `15` | FastTP 검사 간격(초). |
| `ASTER_FUNDING_FILTER_ENABLED` | `true` | 펀딩 필터 활성화. |
| `ASTER_FUNDING_MAX_LONG` / `ASTER_FUNDING_MAX_SHORT` | `0.0010` | 방향별 펀딩 상한. |
| `ASTER_NON_ARB_FILTER_ENABLED` | `true` | 마크/오라클 클램프 가드 활성화. |
| `ASTER_NON_ARB_CLAMP_BPS` | `0.0005` | 프리미엄 클램프 폭(±bps). |
| `ASTER_NON_ARB_EDGE_THRESHOLD` | `0.00005` | 차익 허용 한계. |
| `ASTER_NON_ARB_SKIP_GAP` | `0.0015` | 즉시 스킵을 유발하는 마크/오라클 격차. |

*대시보드에서 시작하면 RSI 51/49와 리스크 0.007로 초기화됩니다. CLI에서만 실행 시 52/48과 0.006이 적용되며 값을 덮어쓰거나 `dashboard_config.json`으로 동기화할 때까지 유지됩니다.*

</details>

<details>
<summary><strong>AI, 자동화, 가드레일</strong></summary>

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `ASTER_BANDIT_ENABLED` | `true` | LinUCB 정책을 활성화합니다. |
| `ASTER_AI_MODE` | `false` | Standard/Pro 모드에서도 AI를 강제 실행합니다 (`ASTER_MODE=ai`). |
| `ASTER_ALPHA_ENABLED` | `true` | 선택형 알파 모델 토글. |
| `ASTER_ALPHA_THRESHOLD` | `0.55` | 트레이드 승인 최소 신뢰도. |
| `ASTER_ALPHA_PROMOTE_DELTA` | `0.15` | 포지션 증액 시 요구되는 추가 신뢰도. |
| `ASTER_HISTORY_MAX` | `250` | 분석용으로 보관하는 트레이드 수. |
| `ASTER_OPENAI_API_KEY` | 빈 값 | AITradeAdvisor용 API 키. |
| `ASTER_CHAT_OPENAI_API_KEY` | 빈 값 | 대시보드 채팅 전용 키(없으면 기본 키 사용). |
| `ASTER_AI_MODEL` | `gpt-4.1` | 사용 모델 ID. |
| `ASTER_AI_DAILY_BUDGET_USD` | `20` | 일일 예산(USD). `ASTER_PRESET_MODE=high/att`일 때는 무시됩니다. |
| `ASTER_AI_STRICT_BUDGET` | `true` | 예산 초과 시 AI 호출을 중지합니다. |
| `ASTER_AI_MIN_INTERVAL_SECONDS` | `8` | 동일 심볼 재평가 전 쿨다운. |
| `ASTER_AI_CONCURRENCY` | `3` | 동시 LLM 요청 수. |
| `ASTER_AI_PENDING_LIMIT` | `max(4, 3×concurrency)` | 대기 중인 AI 작업 한도. |
| `ASTER_AI_GLOBAL_COOLDOWN_SECONDS` | `2.0` | 요청 간 전역 쿨다운. |
| `ASTER_AI_PLAN_TIMEOUT_SECONDS` | `45` | 플랜 대기 시간 초과 시 대체 경로로 전환. |
| `ASTER_AI_SENTINEL_ENABLED` | `true` | 뉴스 센티넬 활성화. |
| `ASTER_AI_SENTINEL_DECAY_MINUTES` | `60` | 뉴스 경고 유지 시간. |
| `ASTER_AI_NEWS_ENDPOINT` | 빈 값 | 외부 뉴스 소스. |
| `ASTER_AI_NEWS_API_KEY` | 빈 값 | 센티넬용 API 토큰. |
| `ASTER_AI_TEMPERATURE` | `0.3` | 창의성 조정(1.0 = 기본값). |
| `ASTER_AI_DEBUG_STATE` | `false` | 상세 로그와 페이로드 덤프 활성화. |
| `ASTER_BRACKETS_QUEUE_FILE` | `brackets_queue.json` | 가드 수리 큐 파일. |

</details>

<details>
<summary><strong>영속 파일</strong></summary>

- **`aster_state.json`** – 오픈 포지션, AI 텔레메트리, 센티넬 상태, 대시보드 UI 선호도를 저장합니다. 불일치 발생 시 삭제해 초기화하세요.
- **`dashboard_config.json`** – 대시보드 편집기 상태를 반영합니다. 여러 프리셋을 위해 백업하거나 삭제해 기본값으로 되돌릴 수 있습니다.
- **`brackets_queue.json`** – `brackets_guard.py`가 스탑/테이크프로핏 수리를 위해 유지합니다. 반복 수리가 보이면 보관 후 제거하세요.

부분 기록을 피하려면 편집·삭제 전에 백엔드를 중지하고, 새 세션 전 스냅샷이 필요하면 파일을 리포지토리 밖으로 이동하세요.

</details>

## 🔐 보안 알림

- 실거래는 위험합니다: 먼저 페이퍼 모드에서 연습하세요.
- API 키를 비공개로 보관하고 주기적으로 교체하세요.
- 캐시가 있어도 시장/주문 데이터가 최신인지 확인하세요.
- 예산과 센티넬 파라미터를 리스크 성향에 맞게 조정하세요.

행운을 빕니다! 버그나 아이디어가 있다면 이슈나 PR을 남겨주세요.
