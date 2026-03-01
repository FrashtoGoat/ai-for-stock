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

- 日报接口：`GET http://localhost:8000/api/daily-report?symbols=600519,000001`
- **生成并推送**：`GET http://localhost:8000/api/daily-report/push`（生成日报并推到已配置的飞书/钉钉）
- 健康检查：`GET http://localhost:8000/health`

## 接下来干嘛（Phase 1 收尾）

1. **本地跑通**：`uvicorn src.main:app --reload --port 8000`，浏览器访问 `/health` 和 `/api/daily-report` 确认有数据。
2. **配置推送**：在 `.env` 里填 `FEISHU_WEBHOOK_URL` 或 `DINGTALK_WEBHOOK_URL`（见各自机器人文档获取 Webhook 地址）。
3. **试推一次**：访问 `GET /api/daily-report/push`，检查飞书/钉钉是否收到日报。
4. **接 OpenClaw 或系统定时**：
   - **OpenClaw**：见 [docs/openclaw-daily-report.md](docs/openclaw-daily-report.md)，用 cron + HTTP Tool 调 push 接口。
   - **不用 OpenClaw**：用系统定时任务执行 `scripts/daily-report-push.ps1`（Windows）或 `scripts/daily-report-push.sh`（Linux/Mac），脚本会请求本机 push 接口。

## 环境变量

| 变量 | 说明 |
|------|------|
| `STOCK_SYMBOLS_DEFAULT` | 默认自选股代码，逗号分隔，如 `600519,000001` |
| `FEISHU_WEBHOOK_URL` | 飞书 Webhook（可选，供 OpenClaw 或本服务推送） |
| `DINGTALK_WEBHOOK_URL` | 钉钉 Webhook（可选） |

## 文档与脚本

| 路径 | 说明 |
|------|------|
| [docs/openclaw-daily-report.md](docs/openclaw-daily-report.md) | OpenClaw 定时推送日报的两种方式（Cron+Tool / 系统定时任务） |
| [scripts/daily-report-push.ps1](scripts/daily-report-push.ps1) | Windows：请求 push 接口，可被任务计划程序调用 |
| [scripts/daily-report-push.sh](scripts/daily-report-push.sh) | Linux/Mac：curl 请求 push 接口，可放入 crontab |

## 后续 Phase

- **Phase 2**：OpenBB Tools 封装，图文报告。
- **Phase 3**：ai-hedge-fund 多策略 Agent（游资/北向/价值）辩论。
- **Phase 4**：FinGenius 16 角色 Agent 协同。
