"""
大模型调用（OpenAI 兼容 API）：新闻→行业/标的、新闻+行情→操作建议。
"""
from __future__ import annotations

import json
import re
from typing import Any

from src.config import settings


def _client():
    from openai import OpenAI
    return OpenAI(
        base_url=settings.openai_api_base or None,
        api_key=settings.openai_api_key or "sk-dummy",
    )


def get_industries_and_symbols(news_items: list[dict[str, Any]]) -> dict[str, Any]:
    """
    根据新闻列表，让大模型提取受影响的行业与 A 股标的（6 位代码）。
    返回 { "industries": [...], "symbols": ["600036", "300750"] }。
    """
    if not settings.openai_api_key:
        return {"industries": [], "symbols": [], "error": "OPENAI_API_KEY not set"}
    text = "\n".join(
        f"[{it.get('time', '')}] {it.get('title', '')} {it.get('content', '')}"
        for it in news_items[:80]
    )
    if not text.strip():
        return {"industries": [], "symbols": []}
    prompt = f"""你是一位 A 股研究员。根据以下财经快讯，列出可能受影响的行业名称，以及相关的 A 股股票代码（仅 6 位数字，如 600036、300750）。
只输出一个 JSON 对象，不要其他文字。格式：{{ "industries": ["行业1", "行业2"], "symbols": ["600036", "300750"] }}
若无法推断标的，symbols 可为空数组。

快讯内容：
{text[:12000]}
"""
    try:
        client = _client()
        r = client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        raw = (r.choices[0].message.content or "").strip()
        # 提取 JSON
        m = re.search(r"\{[\s\S]*\}", raw)
        if m:
            data = json.loads(m.group())
            syms = [str(s).strip().replace(" ", "") for s in (data.get("symbols") or [])]
            syms = [s.zfill(6) for s in syms if s.isdigit() and 0 < len(s) <= 6]
            return {"industries": data.get("industries") or [], "symbols": list(dict.fromkeys(syms))}
        return {"industries": [], "symbols": [], "raw": raw}
    except Exception as e:
        return {"industries": [], "symbols": [], "error": str(e)}


def get_trading_suggestions(
    news_summary: str,
    index_info: dict[str, Any],
    symbols_quote: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    根据新闻摘要、大盘信息、标的行情，生成操作建议。
    返回 { "summary": "一句话", "actions": [ { "symbol", "action": "buy"|"sell"|"hold", "reason", "suggested_amount" } ] }。
    """
    if not settings.openai_api_key:
        return {"summary": "", "actions": [], "error": "OPENAI_API_KEY not set"}
    index_str = json.dumps(index_info, ensure_ascii=False)
    symbols_str = json.dumps(symbols_quote[:30], ensure_ascii=False, indent=0)
    prompt = f"""你是一位 A 股交易顾问。根据以下信息给出操作建议。
1) 新闻/快讯摘要
2) 大盘指数当前情况
3) 相关标的的当前行情（名称、代码、最新价、涨跌幅、量比等）

要求：
- 输出一个 JSON 对象，格式：{{ "summary": "一句话结论", "actions": [ {{ "symbol": "600036", "action": "buy或sell或hold", "reason": "简短理由", "suggested_amount": 100 }} ] }}
- action 只能是 buy、sell、hold 之一；suggested_amount 为建议股数（100 的整数倍），hold 可为 0。
- 不要输出除该 JSON 以外的内容。

新闻/快讯摘要：
{news_summary[:4000]}

大盘：
{index_str}

标的行情：
{symbols_str}
"""
    try:
        client = _client()
        r = client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        raw = (r.choices[0].message.content or "").strip()
        m = re.search(r"\{[\s\S]*\}", raw)
        if m:
            data = json.loads(m.group())
            actions = data.get("actions") or []
            for a in actions:
                if isinstance(a, dict):
                    a["action"] = (a.get("action") or "hold").lower().strip()
                    if a["action"] not in ("buy", "sell", "hold"):
                        a["action"] = "hold"
                    a["suggested_amount"] = max(0, int(a.get("suggested_amount") or 0) // 100 * 100)
            return {"summary": data.get("summary") or "", "actions": actions}
        return {"summary": "", "actions": [], "raw": raw}
    except Exception as e:
        return {"summary": "", "actions": [], "error": str(e)}
