"""
FastAPI 入口：提供每日决策日报、新闻→操作建议→交易 等 API。
"""
import logging
import time
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from src.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ai-for-stock")

from src.services.chart import render_chart_png
from src.services.daily_report import build_daily_report
from src.services.notify import push_to_dingtalk, push_to_feishu
from src.services.pipeline import run_news_to_trade, run_news_to_trade_multi

APP_VERSION = "0.1.0"
_news_trade_last_run_time: float = 0.0

app = FastAPI(
    title="ai-for-stock",
    description="A-share daily report API for OpenClaw (AKShare + daily_stock_analysis template)",
    version=APP_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request, call_next):
    logger.info("→ %s %s", request.method, request.url.path)
    try:
        response = await call_next(request)
        logger.info("← %s %s → %s", request.method, request.url.path, response.status_code)
        return response
    except Exception as e:
        logger.exception("请求处理异常 %s %s: %s", request.method, request.url.path, e)
        raise


_MAX_SYMBOLS = 20


def _normalize_symbols(symbols: str | None) -> list[str]:
    if symbols:
        raw = [s.strip() for s in symbols.split(",") if s.strip()]
    else:
        raw = [s.strip() for s in settings.stock_symbols_default.split(",") if s.strip()]
    cap = getattr(settings, "max_symbols_per_request", _MAX_SYMBOLS) or _MAX_SYMBOLS
    return raw[:cap]


@app.get("/health", tags=["系统"])
def health():
    """健康检查。"""
    return {"status": "ok", "version": APP_VERSION}


@app.get("/api/daily-report", tags=["日报"])
def get_daily_report(
    symbols: str | None = Query(
        default=None,
        description="A股代码，逗号分隔，如 600519,000001。不传则使用环境变量 STOCK_SYMBOLS_DEFAULT",
    ),
):
    """
    每日决策日报（决策仪表盘格式）。
    返回：一句话结论、买卖点位、操作检查清单；可与飞书/钉钉推送对接。标的数量受 max_symbols_per_request 限制。
    """
    symbol_list = _normalize_symbols(symbols)
    if not symbol_list:
        return JSONResponse(
            status_code=400,
            content={"detail": "symbols 或 STOCK_SYMBOLS_DEFAULT 至少提供一组自选股代码"},
        )
    try:
        report = build_daily_report(symbol_list)
        return report
    except Exception as e:
        logger.exception("日报生成失败 symbols=%s", symbol_list)
        return JSONResponse(
            status_code=500,
            content={"detail": "生成日报失败", "error": str(e)},
        )


@app.get("/api/daily-report/push", tags=["日报"])
def get_daily_report_and_push(
    symbols: str | None = Query(
        default=None,
        description="A股代码，逗号分隔。不传则使用 STOCK_SYMBOLS_DEFAULT",
    ),
):
    """
    生成日报并推送到已配置的飞书/钉钉 Webhook。
    OpenClaw 定时工作流可直接调此接口，一步完成「生成+推送」。标的数量受 max_symbols_per_request 限制。
    """
    symbol_list = _normalize_symbols(symbols)
    if not symbol_list:
        return JSONResponse(
            status_code=400,
            content={"detail": "symbols 或 STOCK_SYMBOLS_DEFAULT 至少提供一组自选股代码"},
        )
    try:
        report = build_daily_report(symbol_list)
    except Exception as e:
        logger.exception("日报生成失败( push ) symbols=%s", symbol_list)
        return JSONResponse(
            status_code=500,
            content={"detail": "生成日报失败", "error": str(e)},
        )
    if settings.public_base_url:
        base = settings.public_base_url.rstrip("/")
        report["chart_urls"] = [{"symbol": s, "url": f"{base}/api/chart?symbol={s}&days=60"} for s in symbol_list]
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


@app.post("/api/news-trade/run", tags=["新闻→交易"])
def api_news_trade_run(dry_run: bool = True, multi: bool = False):
    """
    执行新闻→行业/标的→大盘与行情→操作建议→（可选）模拟下单。
    dry_run=true 时只执行到操作建议，不下单；multi=true 时采用多视角合并建议。
    当 dry_run=false 且配置了 news_trade_cooldown_seconds>0 时，冷却期内再次调用返回 429。
    """
    global _news_trade_last_run_time
    cooldown = getattr(settings, "news_trade_cooldown_seconds", 0.0) or 0.0
    if not dry_run and cooldown > 0:
        now = time.monotonic()
        if now - _news_trade_last_run_time < cooldown:
            return JSONResponse(
                status_code=429,
                content={"detail": "news-trade run in cooldown", "retry_after_seconds": round(cooldown - (now - _news_trade_last_run_time), 1)},
            )
        _news_trade_last_run_time = now
    try:
        runner = run_news_to_trade_multi if multi else run_news_to_trade
        out = runner(news_limit=50, dry_run=dry_run)
        return out
    except Exception as e:
        logger.exception("news-trade run 失败 dry_run=%s multi=%s", dry_run, multi)
        return JSONResponse(status_code=500, content={"detail": "pipeline failed", "error": str(e)})


@app.get("/api/news-trade/suggestions", tags=["新闻→交易"])
def api_news_trade_suggestions():
    """仅执行到「操作建议」并返回，不下单。便于调试与人工确认。"""
    try:
        out = run_news_to_trade(news_limit=50, dry_run=True)
        return {"suggestions": out.get("suggestions"), "market": out.get("market"), "industries_and_symbols": out.get("industries_and_symbols"), "error": out.get("error")}
    except Exception as e:
        logger.exception("suggestions 失败")
        return JSONResponse(status_code=500, content={"detail": "suggestions failed", "error": str(e)})


@app.get("/api/news-trade/suggestions-multi", tags=["新闻→交易"])
def api_news_trade_suggestions_multi():
    """多视角（游资/北向/价值/舆情/风控）分别给出建议并投票合并，仅返回建议不下单。"""
    try:
        out = run_news_to_trade_multi(news_limit=50, dry_run=True)
        return {
            "suggestions": out.get("suggestions"),
            "market": out.get("market"),
            "industries_and_symbols": out.get("industries_and_symbols"),
            "error": out.get("error"),
        }
    except Exception as e:
        logger.exception("suggestions-multi 失败")
        return JSONResponse(status_code=500, content={"detail": "suggestions-multi failed", "error": str(e)})


@app.get("/api/chart", tags=["图表"])
def api_chart(
    symbol: str = Query(..., description="A 股代码，如 600519"),
    days: int = Query(60, ge=5, le=250, description="近 N 个交易日"),
):
    """生成标的近 N 日收盘价曲线图 PNG，供报告或 OpenClaw 图文并茂。"""
    try:
        png_bytes = render_chart_png(symbol.strip(), days=days)
        return Response(content=png_bytes, media_type="image/png")
    except Exception as e:
        logger.exception("图表生成失败 symbol=%s days=%s", symbol, days)
        return JSONResponse(status_code=500, content={"detail": "chart failed", "error": str(e)})
