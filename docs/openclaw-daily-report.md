# OpenClaw 定时推送每日决策日报

两种方式二选一：用 OpenClaw 的 cron 触发 Agent 调我们接口，或用系统定时任务直接请求本服务。

---

## 方式一：OpenClaw Cron + HTTP Tool（推荐）

让 OpenClaw 在每天固定时间触发，通过「调用 HTTP 的 Tool」请求本仓库的 push 接口，日报会由本服务直接推到飞书/钉钉。

### 1. 本服务保持运行

确保 ai-for-stock 已启动，例如：

```bash
cd ai-for-stock
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

若 OpenClaw 与 ai-for-stock 在同一台机，URL 用 `http://127.0.0.1:8000`；若在不同机器，改为本机内网 IP。

### 2. 在 OpenClaw 中配置「调用日报推送」的 Tool

在 OpenClaw 里添加一个能发起 HTTP GET 的 Tool（名称自定，如 `daily_stock_report_push`），请求：

- **Method**: GET  
- **URL**: `http://127.0.0.1:8000/api/daily-report/push`  
  （或带自选股参数：`http://127.0.0.1:8000/api/daily-report/push?symbols=600519,000001`）

具体配置方式以你使用的 OpenClaw 版本为准（插件 / 工作流里的 HTTP 节点 / Tools 配置页等）。

### 3. 添加定时任务

用 OpenClaw 的 cron 在每天收盘后执行一次，让 Agent 调用上面的 Tool。例如每天 18:00（北京时间）：

```bash
openclaw cron add "执行A股每日决策日报并推送" \
  --schedule "0 18 * * *" \
  --tz "Asia/Shanghai" \
  --session isolated \
  --message "请调用 daily_stock_report_push 工具，执行今日日报推送。"
```

若你的版本使用 `--cron` 而不是 `--schedule`，可改为：

```bash
openclaw cron add "执行A股每日决策日报并推送" \
  --cron "0 18 * * *" \
  --tz "Asia/Shanghai" \
  --session isolated \
  --message "请调用 daily_stock_report_push 工具，执行今日日报推送。"
```

执行后，Agent 会调用该 Tool，本服务会生成日报并推到已在 `.env` 中配置的飞书/钉钉 Webhook。

---

## 方式二：系统定时任务直接请求（不依赖 OpenClaw Agent）

不经过 OpenClaw，由系统在固定时间请求本服务的 push 接口。

### Windows（任务计划程序）

1. 用本项目提供的脚本（见下方「脚本说明」）或直接用 PowerShell 请求：
   ```powershell
   Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/daily-report/push" -Method Get
   ```
2. 打开「任务计划程序」→ 创建基本任务 → 触发器选「每天」、时间选 18:00 → 操作选「启动程序」→ 程序填 `powershell.exe`，参数填 `-File "E:\document\AI\mine\ai-for-stock\scripts\daily-report-push.ps1"`（路径按你本机改）。

### Linux / macOS（crontab）

```bash
# 每天 18:00 执行
0 18 * * * curl -sS "http://127.0.0.1:8000/api/daily-report/push" > /dev/null 2>&1
```

或使用项目里的 `scripts/daily-report-push.sh`，在 crontab 里写该脚本的绝对路径即可。

---

## 脚本说明

- **scripts/daily-report-push.ps1**（Windows）：请求本机 8000 端口的 push 接口。  
- **scripts/daily-report-push.sh**（Linux/Mac）：用 curl 请求，默认 URL 为 `http://127.0.0.1:8000/api/daily-report/push`，可在脚本内改 `BASE_URL`。

使用前请先启动 ai-for-stock 服务，并确保 `.env` 中已配置飞书或钉钉 Webhook。
