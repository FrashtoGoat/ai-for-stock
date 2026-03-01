#!/usr/bin/env bash
# 请求 ai-for-stock 的「生成并推送」接口。
# 使用前：1) 启动 uvicorn  2) .env 中配置 FEISHU_WEBHOOK_URL 或 DINGTALK_WEBHOOK_URL
BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
PUSH_URL="${BASE_URL}/api/daily-report/push"
if curl -sS -f "$PUSH_URL" > /dev/null; then
  echo "OK: daily report pushed"
else
  echo "ERROR: request failed"
  exit 1
fi
