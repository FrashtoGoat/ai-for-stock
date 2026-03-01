# 请求 ai-for-stock 的「生成并推送」接口，由本服务推送到飞书/钉钉。
# 使用前：1) 启动 uvicorn  (uvicorn src.main:app --port 8000)
#         2) .env 中配置 FEISHU_WEBHOOK_URL 或 DINGTALK_WEBHOOK_URL
$baseUrl = "http://127.0.0.1:8000"
$pushUrl = "$baseUrl/api/daily-report/push"
try {
    $r = Invoke-RestMethod -Uri $pushUrl -Method Get -ErrorAction Stop
    Write-Host "OK: report generated and push result:" ($r.push | ConvertTo-Json -Compress)
} catch {
    Write-Host "ERROR: $_"
    exit 1
}
