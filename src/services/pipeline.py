"""
新闻 → 行业/标的 → 大盘+行情 → 操作建议 → 模拟下单。主流程编排。
"""
from __future__ import annotations

from typing import Any

from src.config import settings
from src.services.broker_live import get_live_broker
from src.services.broker_sim import get_sim_broker
from src.services.llm import get_industries_and_symbols, get_trading_suggestions, get_trading_suggestions_multi
from src.services.market import get_market_and_symbols_quote_cached
from src.services.news_fetcher import fetch_recent_news_cached


def run_news_to_trade(
    news_limit: int = 50,
    dry_run: bool = True,
    broker: Any | None = None,
    news_items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    执行完整链路：拉新闻（或使用注入的 news_items）→ LLM 得行业+标的 → 取大盘与标的行情 → LLM 得操作建议 → 按建议下单（dry_run 则不下单）。
    broker 不传时使用本地 SimBroker；传入则可为第三方模拟/实盘实现。
    若传入 news_items，则不再拉取线上新闻，直接以此做分析（用于热点事件分析）。
    """
    result: dict[str, Any] = {
        "news": [],
        "industries_and_symbols": {},
        "market": {},
        "suggestions": {},
        "orders": [],
        "error": None,
    }
    # 1) 新闻：注入或拉取（带缓存）
    if news_items is None:
        news_items = fetch_recent_news_cached(limit=news_limit)
    result["news"] = [{"time": n.get("time"), "content": (n.get("title", "") + " " + n.get("content", ""))[:200]} for n in news_items]
    if not news_items:
        result["error"] = "no news fetched"
        return result
    # 2) LLM 行业+标的
    ir = get_industries_and_symbols(news_items)
    result["industries_and_symbols"] = ir
    symbols = ir.get("symbols") or []
    if ir.get("error"):
        result["error"] = ir.get("error")
    if not symbols:
        return result
    # 3) 大盘+标的行情（带 60s 缓存）
    market = get_market_and_symbols_quote_cached(symbols)
    result["market"] = market
    symbols_quote = market.get("symbols") or []
    # 新闻摘要（供 LLM）
    news_summary = "\n".join(f"[{n.get('time')}] {n.get('content', '')}" for n in news_items[:30])
    # 4) LLM 操作建议
    sug = get_trading_suggestions(news_summary, market.get("index") or {}, symbols_quote)
    result["suggestions"] = sug
    if sug.get("error"):
        result["error"] = sug.get("error")
    # 5) 下单（仅 buy/sell，hold 不调）
    if dry_run:
        result["orders"] = [{"dry_run": True, "action": a} for a in (sug.get("actions") or []) if (a.get("action") or "hold") in ("buy", "sell")]
        return result
    if broker is None:
        broker = get_live_broker() if getattr(settings, "use_live_broker", False) else get_sim_broker()
    orders_out = []
    for a in sug.get("actions") or []:
        act = (a.get("action") or "hold").lower()
        if act not in ("buy", "sell"):
            continue
        sym = str(a.get("symbol", "")).strip().zfill(6)
        vol = max(100, (int(a.get("suggested_amount") or 0) // 100) * 100)
        if act == "buy":
            r = broker.order_buy(sym, vol, price=None)
        else:
            r = broker.order_sell(sym, vol, price=None)
        orders_out.append({"action": act, "symbol": sym, "volume": vol, "result": r})
    result["orders"] = orders_out
    return result


def run_news_to_trade_multi(
    news_limit: int = 50,
    dry_run: bool = True,
    broker: Any | None = None,
    news_items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    与 run_news_to_trade 相同链路，但操作建议采用多视角分别生成后投票合并。
    若传入 news_items，则不再拉取线上新闻，直接以此做分析。
    """
    result: dict[str, Any] = {
        "news": [],
        "industries_and_symbols": {},
        "market": {},
        "suggestions": {},
        "orders": [],
        "error": None,
    }
    if news_items is None:
        news_items = fetch_recent_news_cached(limit=news_limit)
    result["news"] = [{"time": n.get("time"), "content": (n.get("title", "") + " " + n.get("content", ""))[:200]} for n in news_items]
    if not news_items:
        result["error"] = "no news fetched"
        return result
    ir = get_industries_and_symbols(news_items)
    result["industries_and_symbols"] = ir
    symbols = ir.get("symbols") or []
    if ir.get("error"):
        result["error"] = ir.get("error")
    if not symbols:
        return result
    market = get_market_and_symbols_quote_cached(symbols)
    result["market"] = market
    symbols_quote = market.get("symbols") or []
    news_summary = "\n".join(f"[{n.get('time')}] {n.get('content', '')}" for n in news_items[:30])
    sug = get_trading_suggestions_multi(news_summary, market.get("index") or {}, symbols_quote)
    result["suggestions"] = sug
    if sug.get("error"):
        result["error"] = sug.get("error")
    if dry_run:
        result["orders"] = [{"dry_run": True, "action": a} for a in (sug.get("combined", {}).get("actions") or []) if (a.get("action") or "hold") in ("buy", "sell")]
        return result
    if broker is None:
        broker = get_live_broker() if getattr(settings, "use_live_broker", False) else get_sim_broker()
    orders_out = []
    for a in sug.get("combined", {}).get("actions") or []:
        act = (a.get("action") or "hold").lower()
        if act not in ("buy", "sell"):
            continue
        sym = str(a.get("symbol", "")).strip().zfill(6)
        vol = max(100, (int(a.get("suggested_amount") or 0) // 100) * 100)
        if act == "buy":
            r = broker.order_buy(sym, vol, price=None)
        else:
            r = broker.order_sell(sym, vol, price=None)
        orders_out.append({"action": act, "symbol": sym, "volume": vol, "result": r})
    result["orders"] = orders_out
    return result
