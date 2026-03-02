"""
大模型调用（OpenAI 兼容 API）：新闻→行业/标的、新闻+行情→操作建议。带超时与重试。
"""
from __future__ import annotations

import json
import re
import time
from typing import Any

from src.config import settings


def _client():
    from openai import OpenAI
    timeout = getattr(settings, "llm_timeout_seconds", 60.0) or 60.0
    return OpenAI(
        base_url=settings.openai_api_base or None,
        api_key=settings.openai_api_key or "sk-dummy",
        timeout=float(timeout),
    )


def _chat_with_retry(messages: list[dict], temperature: float = 0.2) -> str:
    max_retries = max(0, getattr(settings, "llm_max_retries", 2))
    last_err = None
    for attempt in range(max_retries + 1):
        try:
            client = _client()
            r = client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                temperature=temperature,
            )
            return (r.choices[0].message.content or "").strip()
        except Exception as e:
            last_err = e
            if attempt < max_retries:
                time.sleep(1.0 * (attempt + 1))
            else:
                raise last_err
    raise last_err or RuntimeError("llm failed")


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
        raw = _chat_with_retry([{"role": "user", "content": prompt}], temperature=0.2)
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


# 多策略角色（ai-hedge-fund / FinGenius 雏形）：游资/北向/价值/舆情/风控
TRADING_ROLES = [
    ("游资策略", "侧重短线情绪、资金流向、龙虎榜与题材炒作，给出偏短线的买卖建议。"),
    ("北向资金策略", "侧重北向资金流向、外资偏好、估值与流动性，给出偏中短期的买卖建议。"),
    ("价值投资策略", "侧重基本面、估值、长期景气度，给出偏中长期的买卖建议。"),
    ("舆情分析师", "侧重新闻情绪、舆情热度、利好利空解读，给出基于情绪面的买卖建议。"),
    ("风控官", "侧重仓位控制、止损止盈、波动与回撤，给出保守偏防守的买卖建议。"),
]


def get_trading_suggestions(
    news_summary: str,
    index_info: dict[str, Any],
    symbols_quote: list[dict[str, Any]],
    role: tuple[str, str] | None = None,
) -> dict[str, Any]:
    """
    根据新闻摘要、大盘信息、标的行情，生成操作建议。
    role 为 (角色名, 角色说明) 时采用该视角；否则为通用顾问。
    返回 { "summary": "一句话", "actions": [ { "symbol", "action": "buy"|"sell"|"hold", "reason", "suggested_amount" } ] }。
    """
    if not settings.openai_api_key:
        return {"summary": "", "actions": [], "error": "OPENAI_API_KEY not set"}
    index_str = json.dumps(index_info, ensure_ascii=False)
    symbols_str = json.dumps(symbols_quote[:30], ensure_ascii=False, indent=0)
    role_line = ""
    if role:
        name, desc = role
        role_line = f"你是一位【{name}】A 股交易顾问，{desc}\n"
    prompt = f"""{role_line}根据以下信息给出操作建议。
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
        raw = _chat_with_retry([{"role": "user", "content": prompt}], temperature=0.3)
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


def get_trading_suggestions_multi(
    news_summary: str,
    index_info: dict[str, Any],
    symbols_quote: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    多视角（游资/北向/价值/舆情/风控）分别生成建议，再按标的投票合并。
    返回 { "perspectives": [ { "role", "summary", "actions" }, ... ], "combined": { "summary", "actions" } }。
    """
    if not settings.openai_api_key:
        return {"perspectives": [], "combined": {"summary": "", "actions": []}, "error": "OPENAI_API_KEY not set"}
    perspectives: list[dict[str, Any]] = []
    for name, desc in TRADING_ROLES:
        out = get_trading_suggestions(news_summary, index_info, symbols_quote, role=(name, desc))
        perspectives.append({
            "role": name,
            "summary": out.get("summary", ""),
            "actions": out.get("actions", []),
        })
    # 简单合并：按标的投票，取多数 action；summary 取三句拼接
    from collections import Counter
    symbol_actions: dict[str, list[tuple[str, int]]] = {}
    for p in perspectives:
        for a in p.get("actions") or []:
            sym = str(a.get("symbol", "")).strip().zfill(6)
            act = (a.get("action") or "hold").lower()
            if act not in ("buy", "sell", "hold"):
                act = "hold"
            amt = max(0, int(a.get("suggested_amount") or 0) // 100 * 100)
            if sym not in symbol_actions:
                symbol_actions[sym] = []
            symbol_actions[sym].append((act, amt))
    combined_actions = []
    for sym, votes in symbol_actions.items():
        acts = [v[0] for v in votes]
        cnt = Counter(acts)
        best = cnt.most_common(1)[0][0]
        amts = [v[1] for v in votes if v[0] == best]
        suggested_amount = max(amts) if amts else 0
        combined_actions.append({
            "symbol": sym,
            "action": best,
            "reason": f"多视角投票: {dict(cnt)}",
            "suggested_amount": suggested_amount,
        })
    combined_summary = " | ".join(p.get("summary", "") for p in perspectives if p.get("summary"))
    return {
        "perspectives": perspectives,
        "combined": {"summary": combined_summary[:500], "actions": combined_actions},
    }
