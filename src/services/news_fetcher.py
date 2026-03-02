"""
财经新闻拉取：AKShare 财联社快讯 / 金十资讯，统一结构供 LLM 使用。支持短期缓存。
"""
from __future__ import annotations

from typing import Any

from src.config import settings
from src.services.cache import get_or_set


def fetch_recent_news(limit: int = 50) -> list[dict[str, Any]]:
    """
    拉取近期财经新闻，返回统一结构 [{ "time", "title", "content", "source" }]。
    优先财联社快讯，失败则尝试金十。
    """
    out: list[dict[str, Any]] = []
    try:
        import akshare as ak
        # 财联社快讯
        df = ak.stock_zh_a_alerts_cls()
        if df is not None and not df.empty:
            cols = list(df.columns)
            time_col = "时间" if "时间" in cols else cols[0]
            content_col = "快讯信息" if "快讯信息" in cols else (cols[1] if len(cols) > 1 else "")
            for _, row in df.head(limit).iterrows():
                out.append({
                    "time": str(row.get(time_col, "")),
                    "title": "",
                    "content": str(row.get(content_col, "")),
                    "source": "财联社",
                })
            if out:
                return out
    except Exception:
        pass
    try:
        import akshare as ak
        df = ak.js_news(indicator="最新资讯")
        if df is not None and not df.empty:
            for _, row in df.head(limit).iterrows():
                out.append({
                    "time": str(row.get("datetime", row.get("时间", ""))),
                    "title": "",
                    "content": str(row.get("content", row.get("新闻内容", ""))),
                    "source": "金十",
                })
    except Exception:
        pass
    return out


def fetch_recent_news_cached(limit: int = 50, ttl: float | None = None) -> list[dict[str, Any]]:
    """带缓存的拉取，ttl 秒内重复调用返回缓存结果；ttl<=0 不缓存。"""
    t = ttl if ttl is not None else getattr(settings, "cache_ttl_seconds", 60.0)
    if t <= 0:
        return fetch_recent_news(limit)
    return get_or_set(f"news:{limit}", lambda: fetch_recent_news(limit), ttl=t)
