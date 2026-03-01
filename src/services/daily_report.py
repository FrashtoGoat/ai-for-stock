"""
每日决策日报：复用 daily_stock_analysis 的决策仪表盘输出格式，数据源为 AKShare。
输出：一句话结论、买卖点位、操作检查清单。
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

# 决策仪表盘模板：六个维度检查清单（与 daily_stock_analysis / 常见投顾清单对齐）
CHECKLIST_DIMENSIONS = [
    {"id": "technical", "name": "技术形态", "hint": "MACD顶背离、KDJ/RSI超买、高位长上影线"},
    {"id": "volume_capital", "name": "成交量资金", "hint": "成交量突增、主力净流入为负、量价背离"},
    {"id": "sentiment", "name": "消息面情绪", "hint": "利好兑现、媒体密集报道、分析师集体上调"},
    {"id": "lhb_holders", "name": "龙虎榜股东", "hint": "机构净卖出、股东人数急增、人均持股下降"},
    {"id": "order_book", "name": "盘口交易", "hint": "卖盘厚重、内盘远大于外盘、大宗折价交易"},
    {"id": "conclusion", "name": "综合判断", "hint": "≥2个警惕信号减仓，≥1个危险信号止盈"},
]


def _fetch_spot(symbols: list[str]) -> list[dict[str, Any]]:
    """用 AKShare 拉取指定代码的 A 股实时行情（东方财富）。"""
    try:
        import akshare as ak
        # 东方财富全 A 行情，再按代码过滤（接口可能只返回前 N 条，故先取再筛）
        df = ak.stock_zh_a_spot_em()
        if df is None or df.empty:
            return []
        # 统一为 6 位代码比较
        def to_6(s: str) -> str:
            s = str(s).strip()
            if len(s) > 6:
                s = s[:6]
            return s.zfill(6)
        need_6 = {to_6(s) for s in symbols}
        df["代码"] = df["代码"].astype(str).str.zfill(6)
        df = df[df["代码"].isin(need_6)]
        return df.to_dict("records")
    except Exception:
        return []


def _summary_one_sentence(rows: list[dict[str, Any]]) -> str:
    """根据行情生成一句话结论（规则版，后续可换 LLM）。"""
    if not rows:
        return "今日未获取到自选股行情，请检查代码或网络。"
    parts = []
    for r in rows:
        name = r.get("名称", r.get("name", ""))
        code = r.get("代码", r.get("code", ""))
        pct = r.get("涨跌幅", r.get("涨跌幅度", None))
        if pct is None:
            pct = 0.0
        try:
            pct = float(pct)
        except (TypeError, ValueError):
            pct = 0.0
        if pct > 3:
            parts.append(f"{name}({code}) 强势上涨 {pct:.1f}%")
        elif pct > 0:
            parts.append(f"{name}({code}) 小幅上涨 {pct:.1f}%")
        elif pct > -3:
            parts.append(f"{name}({code}) 小幅回调 {pct:.1f}%")
        else:
            parts.append(f"{name}({code}) 下跌 {pct:.1f}%")
    return "；".join(parts[:5]) + ("..." if len(parts) > 5 else "")


def _buy_sell_points(rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    """根据量比/换手率等生成简易买卖点位说明（规则版）。"""
    buy, sell = [], []
    for r in rows:
        name = r.get("名称", r.get("name", ""))
        code = r.get("代码", r.get("code", ""))
        pct = r.get("涨跌幅", r.get("涨跌幅度", 0))
        try:
            pct = float(pct)
        except (TypeError, ValueError):
            pct = 0.0
        # 量比、换手率 字段名可能为 量比、换手率
        lb = r.get("量比", None)
        try:
            lb = float(lb) if lb is not None else None
        except (TypeError, ValueError):
            lb = None
        hs = r.get("换手率", None)
        try:
            hs = float(hs) if hs is not None else None
        except (TypeError, ValueError):
            hs = None
        label = f"{name}({code})"
        if lb is not None and hs is not None:
            if hs > 10 and lb > 5 and pct > 0:
                buy.append(f"{label}：换手{hs:.1f}% 量比{lb:.1f} 偏强，可关注低位支撑")
            elif hs >= 5 and lb is not None and lb < 2 and pct < 0:
                sell.append(f"{label}：换手{hs:.1f}% 量比{lb:.1f} 偏弱，注意风险")
        if pct > 5 and not any(label in b for b in buy):
            buy.append(f"{label}：涨幅{pct:.1f}%，可设止盈持有")
        if pct < -5:
            sell.append(f"{label}：跌幅{pct:.1f}%，观望或设好止损")
    return {"buy": buy[:10], "sell": sell[:10]}


def _checklist_items(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """生成六维检查清单（规则版，后续可接 LLM 或更多数据源）。"""
    out = []
    for dim in CHECKLIST_DIMENSIONS:
        out.append({
            "dimension": dim["name"],
            "dimension_id": dim["id"],
            "hint": dim["hint"],
            "status": "pending",  # pending / caution / danger
            "remark": "请结合盘面与消息自行核对。",
        })
    return out


def build_daily_report(symbols: list[str]) -> dict[str, Any]:
    """
    生成每日决策日报（决策仪表盘格式）。
    symbols: A 股代码列表，如 ["600519", "000001"]。
    """
    symbols = [re.sub(r"^[a-zA-Z]+", "", str(s).strip()) for s in symbols if str(s).strip()]
    if not symbols:
        symbols = ["600519", "000001"]
    rows = _fetch_spot(symbols)
    summary = _summary_one_sentence(rows)
    points = _buy_sell_points(rows)
    checklist = _checklist_items(rows)
    return {
        "summary": summary,
        "buy_sell_points": points,
        "checklist": checklist,
        "symbols_queried": symbols,
        "symbols_fetched": [r.get("代码", "") for r in rows],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
