"""
Broker 抽象接口：资金、持仓、买卖。模拟盘与实盘统一实现此接口，主流程只依赖本接口。
"""
from __future__ import annotations

from typing import Any, Protocol


class Broker(Protocol):
    """券商/模拟盘抽象：查资金、查持仓、下单。"""

    def get_balance(self) -> dict[str, Any]:
        """返回 { "available": float, "total": float, ... }"""
        ...

    def get_positions(self) -> list[dict[str, Any]]:
        """返回 [ { "symbol", "name", "volume", "cost", "current_price", ... } ]"""
        ...

    def order_buy(self, symbol: str, volume: int, price: float | None = None) -> dict[str, Any]:
        """市价或限价买入，volume 为股数（100 的整数倍）。返回 { "order_id", "status", ... }"""
        ...

    def order_sell(self, symbol: str, volume: int, price: float | None = None) -> dict[str, Any]:
        """市价或限价卖出。返回 { "order_id", "status", ... }"""
        ...
