<div align="center">
  <img src="assets/mraster-logo.png" alt="MrAster 标志" width="240" />
  <h1>MrAster 量化交易机器人</h1>
  <p><strong>你的加密期货贴心副驾驶：洞察市场、管理风险、实时反馈。</strong></p>
  <p>
    <a href="#-60-%e7%a7%92%e6%9c%89%e5%a4%9f%e4%ba%86%e8%a7%a3-mraster">为什么选择 MrAster？</a>
    ·
    <a href="#-%e5%bf%ab%e9%80%9f%e5%85%a5%e9%97%a8">快速上手</a>
    ·
    <a href="#-dashboard-%e6%a0%87%e7%b4%80">Dashboard 一览</a>
    ·
    <a href="#-%e6%8a%80%e8%a1%93%e7%9c%8b%e9%bb%9e">技术细节</a>
  </p>
</div>

<p align="center">
  <a href="https://www.python.org/" target="_blank"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python 3.10+" /></a>
  <a href="#-dashboard-%e6%a0%87%e7%b4%80"><img src="https://img.shields.io/badge/%e6%8e%a7%e5%88%b6-%e6%b8%85%e7%95%a5%e7%9a%84%e7%b6%b2%e9%a0%81%e6%8e%a7%e5%88%b6%e5%8f%b0-8A2BE2" alt="Dashboard" /></a>
  <a href="#-%e7%a9%a9%e4%bf%9d%e7%ac%ac%e4%b8%80"><img src="https://img.shields.io/badge/%e6%a8%a1%e5%bc%8f-Paper%20%e6%88%96%e5%ae%9e%e6%96%bd-FF8C00" alt="Modes" /></a>
  <a href="#-%e7%a9%a9%e4%bf%9d%e7%ac%ac%e4%b8%80"><img src="https://img.shields.io/badge/%e6%8f%90%e9%86%92-%e4%ba%a4%e6%98%93%e6%9c%89%e9%a3%8e%e9%99%a9-E63946" alt="Risk" /></a>
</p>

> “开启后端，打开浏览器，把繁重的工作交给副驾驶。”

---

## ✨ 60 秒了解 MrAster

- **省心的自动交易** – MrAster 扫描期货市场、生成交易建议，并可在安全栏杆的保护下执行。
- **随时可用的控制台** – 启动或停止机器人、调整风险滑块、在一页内阅读 AI 解读。
- **尊重预算的 AI** – 日度限额、冷却时间、新闻哨兵让副驾驶既给力又节省。
- **无痛上手** – 先在 Paper 模式中排练，再切换到真实订单。

## 🚀 快速入门

1. **准备 Python 环境**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
2. **启动后端**
   ```bash
   python dashboard_server.py
   # 或开启自动重载
   uvicorn dashboard_server:app --host 0.0.0.0 --port 8000
   ```
3. **浏览器完成配置**
   打开 <http://localhost:8000>，连接交易所密钥（或 Paper 模式），跟随引导即可。

> 偏好无界面模式？设置 `ASTER_PAPER=true`（可选）并运行 `python aster_multi_bot.py`。加上 `ASTER_RUN_ONCE=true` 可只扫描一轮。

## 🖥️ Dashboard 标纪

- **一键掌控** – 无需终端即可启动、停止或重启监管模式的 `aster_multi_bot.py`。
- **实时日志与提醒** – 每条交易想法、AI 回复、护栏告警即时呈现。
- **风险滑块简单明了** – 选择 Low / Mid / High / ATT 预设，或切换 Pro 模式调节每个 `ASTER_*` 参数。
- **安全编辑配置** – 在应用之前自动校验输入，保障环境更新安全。
- **AI 副驾驶面板** – 阅读浅显易懂的笔记、查看预算消耗，并直接对话。
- **绩效快照** – 统一界面内查看盈亏、交易历史与市场热力图。

## 🛡️ 稳保第一

- **Paper 模式**：先用模拟成交检验策略，再投入真金白银。
- **预算上限**：AI 助手遵守每日美元限额，除非你手动放宽。
- **哨兵预警**：突发新闻、异常资金费率、波动率脉冲立即提醒。
- **完全掌控权**：随时暂停机器人、修改设置或停用自动化。

## 🤓 技术看点（开发者专享）

想了解引擎、护栏与配置面板？展开下列模块。

<details>
<summary><strong>AI 副驾驶栈</strong></summary>

- **AITradeAdvisor** 将状态统计、订单簿上下文与结构化提示整合后，分发到线程池（带缓存与价格限制），最终返回包含 override 与解释的 JSON 方案。
- **DailyBudgetTracker + BudgetLearner** 双层控制支出：前者维护模型平均成本，后者在 edge 走弱时调整品种预算并暂停昂贵请求——所有更新在每次 OpenAI 响应后即时生效。
- **NewsTrendSentinel** (`ASTER_AI_SENTINEL_*`) 融合 24 小时市场数据与外部新闻，为 Advisor 提供事件风险标签、仓位夹紧与热度系数。
- **PostmortemLearning** 将定性复盘沉淀为持久化数值特征，帮助下一次计划吸收上一次离场的教训。
- **ParameterTuner** 收集交易结果、重估仓位/ATR 偏差，在统计显著前不会轻易请出 LLM。
- **PlaybookManager** 维护一份动态战术手册，记录市场状态、操作指令与风险调节，并注入每个请求。
- **待处理队列与并发护栏** 借助 `ASTER_AI_CONCURRENCY`、`ASTER_AI_PENDING_LIMIT` 与全局冷却防止 API/Budget 过载，同时保证任务在控制台可见。

</details>

<details>
<summary><strong>交易引擎</strong></summary>

- **RSI 信号 + 趋势确认** – 通过 `ASTER_*` 环境变量或控制台编辑器自定义。
- **多臂强盗策略 (`BanditPolicy`)** 将 LinUCB 探索与可选 Alpha 模型 (`ml_policy.py`) 结合，决定 TAKE/SKIP 与仓位档位 (S/M/L)。
- **市场卫生过滤** – 资金费率、点差、长影线过滤及缓存行情平滑交易所噪声。
- **Oracle 感知防套利护栏** – 利用溢价指数（Jez, 2025）限制 Mark/Oracle 偏差，规避资金费率陷阱。

</details>

<details>
<summary><strong>风险与订单管理</strong></summary>

- **BracketGuard** (`brackets_guard.py`) 修复止损/止盈单，兼容旧版与新版机器人签名。
- **FastTP** 通过 ATR 阈值与冷却策略减少不利波动。
- **权益与敞口上限** (`ASTER_MAX_OPEN_*`, `ASTER_EQUITY_FRACTION`) 搭配持久状态 (`aster_state.json`) 确保重启后也能延续。

</details>

<details>
<summary><strong>策略、风险与仓位</strong></summary>

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `ASTER_INTERVAL` / `ASTER_HTF_INTERVAL` | `5m` / `30m` | 信号与确认周期。 |
| `ASTER_RSI_BUY_MIN` / `ASTER_RSI_SELL_MAX` | `51` / `49`* | 多/空入场 RSI 阈值。 |
| `ASTER_ALLOW_TREND_ALIGN` | `false` | 强制不同周期趋势同向。 |
| `ASTER_TREND_BIAS` | `with` | 顺势或逆势操作。 |
| `ASTER_MIN_QUOTE_VOL_USDT` | `150000` | 可交易品种的最低成交额。 |
| `ASTER_SPREAD_BPS_MAX` | `0.0030` | 最大允许点差（bps）。 |
| `ASTER_WICKINESS_MAX` | `0.97` | 过滤影线过长的 K 线。 |
| `ASTER_MIN_EDGE_R` | `0.30` | 批准交易的最小 Edge（以 R 计）。 |
| `ASTER_DEFAULT_NOTIONAL` | `0` | 缺乏自适应数据时的基础名义仓位（0 = 交由 AI 计算）。 |
| `ASTER_SIZE_MULT_FLOOR` | `0` | 仓位倍数下限（1.0 = 强制基础仓位）。 |
| `ASTER_MAX_NOTIONAL_USDT` | `0` | 名义价值硬上限（0 = 交由杠杆/权益护栏决定）。 |
| `ASTER_SIZE_MULT_CAP` | `3.0` | 所有调整后的仓位倍数上限。 |
| `ASTER_CONFIDENCE_SIZING` | `true` | 启用信心加权仓位。 |
| `ASTER_CONFIDENCE_SIZE_MIN` / `ASTER_CONFIDENCE_SIZE_MAX` | `1.0` / `3.0` | 信心倍数目标区间。 |
| `ASTER_CONFIDENCE_SIZE_BLEND` / `ASTER_CONFIDENCE_SIZE_EXP` | `1` / `2.0` | 融合权重与指数（>1 强化高信心）。 |
| `ASTER_RISK_PER_TRADE` | `0.007`* | 单笔风险占权益比例。 |
| `ASTER_EQUITY_FRACTION` | `0.66` | 最大权益占用比例（33% / 66% / 100% 取决于预设）。 |
| `ASTER_LEVERAGE` | `10` | 默认杠杆（Low 4× / Mid 10× / High & ATT 交易所上限）。 |
| `ASTER_MAX_OPEN_GLOBAL` | `0` | 同时持仓总数限制（0 = 不限）。 |
| `ASTER_MAX_OPEN_PER_SYMBOL` | `1` | 单品种持仓限制（0 = 不限）。 |
| `ASTER_SL_ATR_MULT` / `ASTER_TP_ATR_MULT` | `1.0` / `1.6` | 止损/止盈 ATR 倍数。 |
| `FAST_TP_ENABLED` | `true` | 启用 FastTP。 |
| `FASTTP_MIN_R` | `0.30` | FastTP 启动前的最小收益（R）。 |
| `FAST_TP_RET1` / `FAST_TP_RET3` | `-0.0010` / `-0.0020` | 回撤触发阈值。 |
| `FASTTP_SNAP_ATR` | `0.25` | Snap 机制所需 ATR 距离。 |
| `FASTTP_COOLDOWN_S` | `15` | FastTP 检查冷却秒数。 |
| `ASTER_FUNDING_FILTER_ENABLED` | `true` | 启用资金费率过滤。 |
| `ASTER_FUNDING_MAX_LONG` / `ASTER_FUNDING_MAX_SHORT` | `0.0010` | 多/空方向的资金费率上限。 |
| `ASTER_NON_ARB_FILTER_ENABLED` | `true` | 启用防套利夹层。 |
| `ASTER_NON_ARB_CLAMP_BPS` | `0.0005` | 溢价夹层宽度（±bps）。 |
| `ASTER_NON_ARB_EDGE_THRESHOLD` | `0.00005` | 允许的资金费率 Edge 阈值。 |
| `ASTER_NON_ARB_SKIP_GAP` | `0.0015` | 触发直接跳过的 Mark/Oracle 差距。 |

*从 Dashboard 启动时默认使用 RSI 51/49 与风险 0.007。仅 CLI 启动则为 52/48 和 0.006，直至覆盖或通过 `dashboard_config.json` 同步。*

</details>

<details>
<summary><strong>AI、自动化与护栏</strong></summary>

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `ASTER_BANDIT_ENABLED` | `true` | 启用 LinUCB 策略。 |
| `ASTER_AI_MODE` | `false` | 即便处于 Standard/Pro 也强制启用 AI (`ASTER_MODE=ai`)。 |
| `ASTER_ALPHA_ENABLED` | `true` | 控制可选 Alpha 模型。 |
| `ASTER_ALPHA_THRESHOLD` | `0.55` | 批准交易所需的最低信心。 |
| `ASTER_ALPHA_PROMOTE_DELTA` | `0.15` | 提升仓位时额外需要的信心。 |
| `ASTER_HISTORY_MAX` | `250` | 保存的历史交易数量。 |
| `ASTER_OPENAI_API_KEY` | 空 | AITradeAdvisor 使用的 API Key。 |
| `ASTER_CHAT_OPENAI_API_KEY` | 空 | 控制台聊天专用 Key，若为空则回落至主 Key。 |
| `ASTER_AI_MODEL` | `gpt-4.1` | 使用的模型 ID。 |
| `ASTER_AI_DAILY_BUDGET_USD` | `20` | 日度预算（美元），`ASTER_PRESET_MODE=high/att` 时忽略。 |
| `ASTER_AI_STRICT_BUDGET` | `true` | 预算耗尽后终止 AI 请求。 |
| `ASTER_AI_MIN_INTERVAL_SECONDS` | `3` | 同一品种再次评估的冷却时间。 |
| `ASTER_AI_CONCURRENCY` | `4` | 并发 LLM 请求上限。 |
| `ASTER_AI_PENDING_LIMIT` | `max(4, 3×concurrency)` | 待处理 AI 队列长度上限。 |
| `ASTER_AI_GLOBAL_COOLDOWN_SECONDS` | `1.0` | 请求间隔的全局冷却。 |
| `ASTER_AI_PLAN_TIMEOUT_SECONDS` | `45` | 计划生成超时后转入备用方案。 |
| `ASTER_AI_SENTINEL_ENABLED` | `true` | 启用新闻哨兵。 |
| `ASTER_AI_SENTINEL_DECAY_MINUTES` | `60` | 单条预警的存续时间。 |
| `ASTER_AI_NEWS_ENDPOINT` | 空 | 外部新闻源地址。 |
| `ASTER_AI_NEWS_API_KEY` | 空 | 哨兵使用的 API Token。 |
| `ASTER_AI_TEMPERATURE` | `0.3` | 创造力调节（1.0 = 服务商默认）。 |
| `ASTER_AI_DEBUG_STATE` | `false` | 打开详细日志和 Payload Dump。 |
| `ASTER_BRACKETS_QUEUE_FILE` | `brackets_queue.json` | 护栏修复队列文件。 |

</details>

<details>
<summary><strong>持久化文件</strong></summary>

- **`aster_state.json`** – 存储持仓、AI 遥测、哨兵状态与 Dashboard 偏好。若数据异常，可删除重新生成。
- **`dashboard_config.json`** – 镜像配置编辑器。需要多套预设时可备份，或删除恢复默认。
- **`brackets_queue.json`** – 由 `brackets_guard.py` 维护，用于修复止损/止盈。若频繁触发，可归档后移除。

编辑或删除前先停掉后端以避免部分写入；如需快照，可将文件移出仓库。

</details>

## 🔐 稳健提示

- 真实交易风险极高：请先在 Paper 模式中演练。
- 保管好 API 密钥并定期轮换。
- 即使有缓存，也要确认行情/订单数据是否及时。
- 结合风险偏好调整预算和哨兵参数。

祝交易顺利！发现问题或有想法，欢迎提 Issue 或 Pull Request。
