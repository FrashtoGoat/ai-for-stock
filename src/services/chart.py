"""
图表生成：用 AKShare 拉取 A 股日 K，matplotlib 出图，供报告或 OpenClaw 图文并茂。
"""
from __future__ import annotations

import io
from datetime import datetime, timedelta
from typing import Any


def get_stock_hist(symbol: str, days: int = 60) -> list[dict[str, Any]]:
    """拉取 A 股日 K，返回 [{ date, open, high, low, close, volume }, ...]。"""
    symbol = str(symbol).strip().zfill(6)
    end = datetime.now()
    start = end - timedelta(days=days)
    start_str = start.strftime("%Y%m%d")
    end_str = end.strftime("%Y%m%d")
    try:
        import akshare as ak
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_str, end_date=end_str, adjust="qfq")
        if df is None or df.empty:
            return []
        df = df.sort_values("日期")
        return df.to_dict("records")
    except Exception:
        return []


def render_chart_png(symbol: str, days: int = 60, title: str | None = None) -> bytes:
    """
    绘制标的近期日 K 收盘价曲线，返回 PNG 字节。
    """
    rows = get_stock_hist(symbol, days=days)
    if not rows:
        return _empty_chart_png(symbol)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    fig, ax = plt.subplots(figsize=(10, 4))
    dates = [r.get("日期", r.get("date", "")) for r in rows]
    closes = [float(r.get("收盘", r.get("close", 0)) or 0) for r in rows]
    ax.plot(range(len(dates)), closes, color="#2563eb", linewidth=1.5)
    ax.set_title(title or f"{symbol} close ({days}d)")
    ax.set_ylabel("Close")
    n = len(dates)
    if n > 0:
        step = max(1, n // 6)
        ax.set_xticks(range(0, n, step))
        ax.set_xticklabels([str(dates[i])[:10] for i in range(0, n, step)], rotation=45)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _empty_chart_png(symbol: str) -> bytes:
    """无数据时返回一张占位图。"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.text(0.5, 0.5, f"{symbol} no data", ha="center", va="center", fontsize=14)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100)
    plt.close(fig)
    buf.seek(0)
    return buf.read()
