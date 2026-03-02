"""
模拟盘实现：本地内存记录资金与持仓，不真实下单。
可用于无第三方模拟 API 时跑通流程；后续可替换为对接掘金/宽易等平台的 HTTP 客户端。
"""
from __future__ import annotations

import time
from typing import Any

from src.config import settings
from src.services.market import get_symbols_quote


class SimBroker:
    """本地模拟 Broker：初始资金可配置，持仓与订单存在内存。"""

    def __init__(self, initial_cash: float = 1_000_000.0):
        self._cash = initial_cash
        self._positions: dict[str, dict[str, Any]] = {}  # symbol -> { volume, cost, name }
        self._orders: list[dict[str, Any]] = []

    def get_balance(self) -> dict[str, Any]:
        # 总资产 = 现金 + 持仓市值（按最新价估算）
        total = self._cash
        if self._positions:
            syms = list(self._positions.keys())
            quotes = get_symbols_quote(syms)
            for q in quotes:
                code = str(q.get("代码", "")).zfill(6)
                if code in self._positions:
                    p = self._positions[code]
                    price = float(q.get("最新价", q.get("收盘", 0)) or 0)
                    total += p["volume"] * price
        return {"available": self._cash, "total": round(total, 2), "frozen": 0}

    def get_positions(self) -> list[dict[str, Any]]:
        out = []
        if not self._positions:
            return out
        quotes = get_symbols_quote(list(self._positions.keys()))
        price_by = {str(q.get("代码", "")).zfill(6): float(q.get("最新价", q.get("收盘", 0)) or 0) for q in quotes}
        for sym, p in self._positions.items():
            out.append({
                "symbol": sym,
                "name": p.get("name", ""),
                "volume": p["volume"],
                "cost": p["cost"],
                "current_price": price_by.get(sym, p["cost"]),
            })
        return out

    def order_buy(self, symbol: str, volume: int, price: float | None = None) -> dict[str, Any]:
        symbol = str(symbol).strip().zfill(6)
        volume = max(0, (volume // 100) * 100)
        if volume == 0:
            return {"order_id": "", "status": "rejected", "message": "volume must be multiple of 100"}
        # 用当前价估算所需资金
        quotes = get_symbols_quote([symbol])
        use_price = price
        if use_price is None and quotes:
            use_price = float(quotes[0].get("最新价", quotes[0].get("收盘", 0)) or 0)
        if use_price is None:
            use_price = 0.0
        need = use_price * volume
        if need > self._cash:
            return {"order_id": "", "status": "rejected", "message": "insufficient balance"}
        order_id = f"sim_buy_{symbol}_{int(time.time() * 1000)}"
        self._cash -= need
        old = self._positions.get(symbol, {"volume": 0, "cost": 0, "name": ""})
        old_vol, old_cost = old.get("volume", 0), old.get("cost", 0) or use_price
        new_vol = old_vol + volume
        new_cost = (old_vol * old_cost + volume * use_price) / new_vol if new_vol else use_price
        self._positions[symbol] = {
            "volume": new_vol,
            "cost": new_cost,
            "name": quotes[0].get("名称", symbol) if quotes else old.get("name", symbol),
        }
        self._orders.append({"order_id": order_id, "symbol": symbol, "side": "buy", "volume": volume, "price": use_price})
        return {"order_id": order_id, "status": "filled", "volume": volume, "price": use_price}

    def order_sell(self, symbol: str, volume: int, price: float | None = None) -> dict[str, Any]:
        symbol = str(symbol).strip().zfill(6)
        volume = max(0, (volume // 100) * 100)
        pos = self._positions.get(symbol, {})
        have = pos.get("volume", 0)
        if volume == 0 or have < volume:
            return {"order_id": "", "status": "rejected", "message": "insufficient position"}
        quotes = get_symbols_quote([symbol])
        use_price = price
        if use_price is None and quotes:
            use_price = float(quotes[0].get("最新价", quotes[0].get("收盘", 0)) or 0)
        if use_price is None:
            use_price = pos.get("cost", 0)
        order_id = f"sim_sell_{symbol}_{int(time.time() * 1000)}"
        self._cash += use_price * volume
        pos["volume"] -= volume
        if pos["volume"] <= 0:
            del self._positions[symbol]
        self._orders.append({"order_id": order_id, "symbol": symbol, "side": "sell", "volume": volume, "price": use_price})
        return {"order_id": order_id, "status": "filled", "volume": volume, "price": use_price}


def get_sim_broker(initial_cash: float | None = None) -> SimBroker:
    """从配置或默认资金创建本地模拟 Broker。若配置了 SIM_BROKER_BASE_URL，后续可改为返回 HTTP 客户端实现的 Broker。"""
    if initial_cash is not None:
        return SimBroker(initial_cash=initial_cash)
    return SimBroker(initial_cash=settings.sim_broker_initial_cash)
