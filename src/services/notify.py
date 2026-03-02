"""
飞书 / 钉钉 Webhook 推送：将日报内容发到配置的 Webhook。
"""
from __future__ import annotations

import json
from typing import Any

import httpx


def _report_to_markdown(report: dict[str, Any]) -> str:
    """把日报结构转为可读的 Markdown 文案。"""
    lines = [
        "## A股每日决策日报",
        "",
        "### 一句话结论",
        report.get("summary", ""),
        "",
        "### 买卖点位",
    ]
    points = report.get("buy_sell_points", {})
    for label, items in [("买入关注", points.get("buy", [])), ("卖出/观望", points.get("sell", []))]:
        lines.append(f"- **{label}**")
        for item in items:
            lines.append(f"  - {item}")
        if not items:
            lines.append("  - 无")
    lines.extend(["", "### 操作检查清单"])
    for c in report.get("checklist", []):
        lines.append(f"- **{c.get('dimension', '')}**：{c.get('hint', '')} — {c.get('remark', '')}")
    chart_urls = report.get("chart_urls")
    if chart_urls:
        lines.extend(["", "### 图表"])
        for item in chart_urls:
            url = item.get("url", "")
            sym = item.get("symbol", "")
            if url:
                lines.append(f"- [{sym} 近60日]({url})")
    lines.append("")
    lines.append(f"*生成时间: {report.get('generated_at', '')}*")
    return "\n".join(lines)


def push_to_feishu(webhook_url: str, report: dict[str, Any]) -> tuple[bool, str]:
    """推送日报到飞书 Webhook。飞书文本消息单条约 4k 限制，用 text 类型。"""
    text = _report_to_markdown(report)
    if len(text) > 4000:
        text = text[:3990] + "\n...(已截断)"
    body = {"msg_type": "text", "content": {"text": text}}
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.post(webhook_url, json=body)
            if r.status_code == 200:
                j = r.json()
                if j.get("code") != 0 and j.get("code") is not None:
                    return False, j.get("msg", r.text)
                return True, ""
            return False, f"HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return False, str(e)


def push_to_dingtalk(webhook_url: str, report: dict[str, Any]) -> tuple[bool, str]:
    """推送日报到钉钉 Webhook。钉钉 markdown 类型支持更好。"""
    text = _report_to_markdown(report)
    if len(text) > 20000:
        text = text[:19990] + "\n...(已截断)"
    body = {"msgtype": "markdown", "markdown": {"title": "A股每日决策日报", "text": text}}
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.post(webhook_url, json=body)
            if r.status_code == 200:
                j = r.json()
                if j.get("errcode") != 0:
                    return False, j.get("errmsg", r.text)
                return True, ""
            return False, f"HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return False, str(e)
