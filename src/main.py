"""
FastAPI 入口：提供每日决策日报等 API，供 OpenClaw 工作流调用。
"""
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

from src.config import settings
from src.services.daily_report import build_daily_report
from src.services.notify import push_to_dingtalk, push_to_feishu

app = FastAPI(
    title="ai-for-stock",
    description="A-share daily report API for OpenClaw (AKShare + daily_stock_analysis template)",
    version="0.1.0",
)


@app.get("/health")
def health():
    """健康检查。"""
    return {"status": "ok"}


@app.get("/api/daily-report")
def get_daily_report(
    symbols: str | None = Query(
        default=None,
        description="A股代码，逗号分隔，如 600519,000001。不传则使用环境变量 STOCK_SYMBOLS_DEFAULT",
    ),
):
    """
    每日决策日报（决策仪表盘格式）。
    返回：一句话结论、买卖点位、操作检查清单；可与飞书/钉钉推送对接。
    """
    if symbols:
        symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
    else:
        symbol_list = [s.strip() for s in settings.stock_symbols_default.split(",") if s.strip()]
    if not symbol_list:
        return JSONResponse(
            status_code=400,
            content={"detail": "symbols 或 STOCK_SYMBOLS_DEFAULT 至少提供一组自选股代码"},
        )
    try:
        report = build_daily_report(symbol_list)
        return report
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": "生成日报失败", "error": str(e)},
        )


@app.get("/api/daily-report/push")
def get_daily_report_and_push(
    symbols: str | None = Query(
        default=None,
        description="A股代码，逗号分隔。不传则使用 STOCK_SYMBOLS_DEFAULT",
    ),
):
    """
    生成日报并推送到已配置的飞书/钉钉 Webhook。
    OpenClaw 定时工作流可直接调此接口，一步完成「生成+推送」。
    """
    if symbols:
        symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
    else:
        symbol_list = [s.strip() for s in settings.stock_symbols_default.split(",") if s.strip()]
    if not symbol_list:
        return JSONResponse(
            status_code=400,
            content={"detail": "symbols 或 STOCK_SYMBOLS_DEFAULT 至少提供一组自选股代码"},
        )
    try:
        report = build_daily_report(symbol_list)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": "生成日报失败", "error": str(e)},
        )
    results = {"report_generated": True, "feishu": None, "dingtalk": None}
    if settings.feishu_webhook_url:
        ok, msg = push_to_feishu(settings.feishu_webhook_url, report)
        results["feishu"] = {"ok": ok, "message": msg or "ok"}
    if settings.dingtalk_webhook_url:
        ok, msg = push_to_dingtalk(settings.dingtalk_webhook_url, report)
        results["dingtalk"] = {"ok": ok, "message": msg or "ok"}
    if not (settings.feishu_webhook_url or settings.dingtalk_webhook_url):
        results["hint"] = "未配置 FEISHU_WEBHOOK_URL 或 DINGTALK_WEBHOOK_URL，仅返回日报未推送"
    return {"report": report, "push": results}
