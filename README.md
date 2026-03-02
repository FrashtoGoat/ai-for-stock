# ai-for-stock

基于 OpenClaw 自动化框架 + 多开源 AI 炒股项目的自动炒股服务端。

## 架构

- **本仓库**：提供 A 股数据与日报 API（AKShare），供 OpenClaw 工作流/Agent 调用。
- **OpenClaw**：定时触发、多 Agent、飞书/钉钉推送、可选浏览器下单。

## Phase 1：每日决策日报

- 复用 [daily_stock_analysis](https://github.com/ZhuLinsen/daily_stock_analysis) 的决策仪表盘输出格式。
- 数据源：**AKShare**（替代原项目数据源）。
- 输出：一句话结论、买卖点位、操作检查清单；可对接飞书/钉钉 Webhook。

## 快速开始

```bash
# 创建虚拟环境并安装依赖
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -e .

# 配置环境变量（复制 .env.example 为 .env 并填写）
cp .env.example .env

# 启动 API 服务
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**运行测试**：`pip install -e ".[dev]"` 后执行 `pytest tests/ -v`。

- 日报接口：`GET http://localhost:8000/api/daily-report?symbols=600519,000001`
- **生成并推送**：`GET http://localhost:8000/api/daily-report/push`（生成日报并推到已配置的飞书/钉钉）
- **新闻→操作建议→模拟交易**：`POST /api/news-trade/run?dry_run=true`（仅建议），`?dry_run=false` 执行模拟下单；`?multi=true` 启用多视角合并建议；`GET /api/news-trade/suggestions`、`GET /api/news-trade/suggestions-multi`（仅返回建议）
- **热点事件分析**：`POST /api/news-trade/analyze`，body `{"news_text": "美国和以色列袭击伊朗…", "multi": false}`，用自定义新闻跑完整分析链路（不拉线上快讯）
- **图表（图文报告）**：`GET http://localhost:8000/api/chart?symbol=600519&days=60` 返回 PNG 近 N 日收盘价曲线，供报告或 OpenClaw 内嵌
- 健康检查：`GET http://localhost:8000/health`
- **接口文档**：启动后访问 `http://localhost:8000/docs` 查看 Swagger UI。

## 前端（Vue 3 + Vite + Element Plus）

提供简易决策台页面，便于本地调试：健康状态、日报、新闻→交易建议与执行、标的图表。

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 http://localhost:5173 。前端会通过 Vite 代理将 `/api`、`/health` 转发到后端（默认 `localhost:8000`），因此需先启动后端。详见 [frontend/README.md](frontend/README.md)。

## 接下来干嘛（立即可做）

1. **本地跑通**：`uvicorn src.main:app --reload --port 8000`，再 `cd frontend && npm run dev`，浏览器打开前端，点日报/图表/热点分析。
2. **配置 LLM**：`.env` 里填 `OPENAI_API_BASE`、`OPENAI_API_KEY`、`OPENAI_MODEL`，前端「热点事件分析」或「单视角建议」才能出结果。
3. **配置推送**：填 `FEISHU_WEBHOOK_URL` 或 `DINGTALK_WEBHOOK_URL`，访问 `GET /api/daily-report/push` 试推一次。
4. **定时日报**：
   - **OpenClaw**：见 [docs/openclaw-daily-report.md](docs/openclaw-daily-report.md)，cron + HTTP Tool 调 push 接口。
   - **系统定时**：Windows 用任务计划程序跑 `scripts/daily-report-push.ps1`；Linux/Mac 用 crontab 跑 `scripts/daily-report-push.sh`。

## 环境变量

| 变量 | 说明 |
|------|------|
| `STOCK_SYMBOLS_DEFAULT` | 默认自选股代码，逗号分隔，如 `600519,000001` |
| `FEISHU_WEBHOOK_URL` | 飞书 Webhook（可选） |
| `DINGTALK_WEBHOOK_URL` | 钉钉 Webhook（可选） |
| `OPENAI_API_BASE` | 大模型 API 地址（OpenAI 兼容，如 DeepSeek） |
| `OPENAI_API_KEY` | 大模型 API Key |
| `OPENAI_MODEL` | 模型名，如 `gpt-4o-mini`、`deepseek-chat` |
| `LLM_TIMEOUT_SECONDS` | 大模型请求超时（默认 60） |
| `LLM_MAX_RETRIES` | 大模型失败重试次数（默认 2） |
| `SIM_BROKER_INITIAL_CASH` | 本地模拟盘初始资金（默认 1000000） |
| `DEFAULT_INDEX_SYMBOL` | 大盘指数代码（默认 399300 沪深300） |
| `CACHE_TTL_SECONDS` | 新闻/行情缓存 TTL（秒），0 不缓存，默认 60 |
| `MAX_SYMBOLS_PER_REQUEST` | 单次请求最大标的数，默认 20 |
| `USE_LIVE_BROKER` | 是否使用实盘 Broker（仅 dry_run=false 时生效），默认 false |
| `NEWS_TRADE_COOLDOWN_SECONDS` | 新闻→交易 下单冷却（秒），冷却内再次 run 返回 429，0 不限制 |
| `PUBLIC_BASE_URL` | 日报推送中图表链接根地址（如 `http://your-server:8000`），可选 |

## 文档与脚本

| 路径 | 说明 |
|------|------|
| [docs/openclaw-daily-report.md](docs/openclaw-daily-report.md) | OpenClaw 定时推送日报的两种方式（Cron+Tool / 系统定时任务） |
| [scripts/daily-report-push.ps1](scripts/daily-report-push.ps1) | Windows：请求 push 接口，可被任务计划程序调用 |
| [scripts/daily-report-push.sh](scripts/daily-report-push.sh) | Linux/Mac：curl 请求 push 接口，可放入 crontab |

## Phase 2：图表能力（已实现）

- 使用 AKShare 日 K + matplotlib 生成标的近 N 日收盘价曲线 PNG。
- `GET /api/chart?symbol=600519&days=60`：OpenClaw 或报告流程可请求该 URL 内嵌图片，实现「图文并茂」。

## Phase 3：多策略多视角（已实现）

- **游资 / 北向 / 价值 / 舆情 / 风控** 五角色分别生成操作建议，再按标的投票合并，降低单一视角偏差；LLM 调用带超时与重试。
- `GET /api/news-trade/suggestions-multi`：仅返回多视角与合并结果；`POST /api/news-trade/run?multi=true`：全链路采用合并建议并可模拟下单。

## 其他

- **缓存**：新闻与行情接口带 60s 内存缓存，短时重复请求不重复拉 AKShare。
- **实盘占位**：`src/services/broker_live.py` 实现 Broker 接口占位；配置 `REAL_BROKER_*` 并在 `broker_live` 内对接券商 API 后，设 `USE_LIVE_BROKER=true` 即可在 pipeline 下单时走实盘。
- **下单冷却**：`NEWS_TRADE_COOLDOWN_SECONDS>0` 时，在冷却期内再次 `POST /api/news-trade/run?dry_run=false` 会返回 429，防止误触重复下单。

## 后续 Phase

- **Phase 4**：FinGenius 16 角色 Agent 协同（OpenClaw 侧配置多 Agent 辩论，本仓库可扩展更多角色或加权合并）。
- 可选：将 OpenBB 数据/图表封装为更多 Tools；在 broker_live 内对接真实券商 API。

## 整合
┌─────────────────────────────────────────────────────┐
│                  OpenClaw 核心调度器                   │
├─────────────────────────────────────────────────────┤
│                                                       │
│  ┌─────────────────────────────────────────────┐    │
│  │  数据层 (AKShare + OpenBB)                   │    │ ← 每日获取行情、龙虎榜、北向资金
│  └─────────────────────────────────────────────┘    │
│                           ↓                          │
│  ┌─────────────────────────────────────────────┐    │
│  │  FinGenius式 16人专家团                        │    │ ← 多智能体辩论分析
│  │  - 舆情分析师、游资猎手、北向专家...              │    │
│  └─────────────────────────────────────────────┘    │
│                           ↓                          │
│  ┌─────────────────────────────────────────────┐    │
│  │  ai-hedge-fund式 多策略碰撞                    │    │ ← 价值派 vs 游资派 vs 北向派
│  └─────────────────────────────────────────────┘    │
│                           ↓                          │
│  ┌─────────────────────────────────────────────┐    │
│  │  daily_stock_analysis式 决策仪表盘             │    │ ← 输出买卖点位、检查清单
│  └─────────────────────────────────────────────┘    │
│                           ↓                          │
│  ┌─────────────────────────────────────────────┐    │
│  │  OpenBB可视化 + 飞书推送                       │    │ ← 图文报告直达手机
│  └─────────────────────────────────────────────┘    │
│                                                       │
└─────────────────────────────────────────────────────┘
