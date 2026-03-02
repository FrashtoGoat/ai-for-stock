"""
大盘指数与标的行情：AKShare 获取指数与个股实时/日线，供操作建议使用。
"""
from __future__ import annotations

from typing import Any

from src.config import settings


def _to_6(s: str) -> str:
    s = str(s).strip()
    if len(s) > 6:
        s = s[:6]
    return s.zfill(6)


def get_index_quote(symbol: str | None = None) -> dict[str, Any]:
    """
    获取大盘指数当前行情（点位、涨跌幅等）。
    symbol 默认用配置 DEFAULT_INDEX_SYMBOL（如 399300 沪深300）。
    """
    sym = (symbol or settings.default_index_symbol or "399300").strip()
    out: dict[str, Any] = {"symbol": sym, "name": "", "price": None, "pct_change": None, "source": "daily"}
    try:
        import akshare as ak
        # 先试日 K，取最近一行
        df = ak.stock_zh_index_daily_em(symbol=sym)
        if df is not None and not df.empty:
            row = df.iloc[-1]
            cols = list(df.columns)
            out["price"] = float(row.get("收盘", row.get("close", 0)) or 0)
            out["pct_change"] = float(row.get("涨跌幅", row.get("pct_change", 0)) or 0)
            out["name"] = "沪深300" if "300" in sym else "指数"
            return out
    except Exception:
        pass
    try:
        import akshare as ak
        # 东方财富指数实时
        df = ak.stock_zh_index_spot_em()
        if df is not None and not df.empty:
            df["代码"] = df["代码"].astype(str).str.strip()
            need = {sym, _to_6(sym)}
            for c in need:
                sub = df[df["代码"] == c]
                if not sub.empty:
                    row = sub.iloc[0]
                    out["price"] = float(row.get("最新价", row.get("收盘", 0)) or 0)
                    out["pct_change"] = float(row.get("涨跌幅", 0)) or 0
                    out["name"] = str(row.get("名称", ""))
                    out["source"] = "spot"
                    return out
    except Exception:
        pass
    return out


def get_symbols_quote(symbols: list[str]) -> list[dict[str, Any]]:
    """获取指定 A 股代码列表的实时行情（与 daily_report 同源逻辑）。"""
    if not symbols:
        return []
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        if df is None or df.empty:
            return []
        need_6 = {_to_6(s) for s in symbols}
        df["代码"] = df["代码"].astype(str).str.zfill(6)
        df = df[df["代码"].isin(need_6)]
        return df.to_dict("records")
    except Exception:
        return []


def get_market_and_symbols_quote(symbols: list[str], index_symbol: str | None = None) -> dict[str, Any]:
    """
    返回 { "index": {...}, "symbols": [...] }，供 LLM 操作建议使用。
    """
    return {
        "index": get_index_quote(index_symbol),
        "symbols": get_symbols_quote(symbols),
    }


def get_market_and_symbols_quote_cached(
    symbols: list[str],
    index_symbol: str | None = None,
    ttl: float | None = None,
) -> dict[str, Any]:
    """带缓存的行情获取，ttl 秒内相同 symbols 返回缓存；ttl<=0 不缓存。"""
    from src.services.cache import get_or_set
    t = ttl if ttl is not None else getattr(settings, "cache_ttl_seconds", 60.0)
    if t <= 0:
        return get_market_and_symbols_quote(symbols, index_symbol)
    key_index = f"index:{index_symbol or settings.default_index_symbol or '399300'}"
    key_syms = "symbols:" + ",".join(sorted(s.strip().zfill(6) for s in symbols))
    index = get_or_set(key_index, lambda: get_index_quote(index_symbol), ttl=t)
    syms = get_or_set(key_syms, lambda: get_symbols_quote(symbols), ttl=t)
    return {"index": index, "symbols": syms}
