"""
实盘 Broker 占位：实现 Broker 接口，对接券商 API 后替换内部逻辑。
当前所有操作返回「未实现」错误，避免误触实盘。
"""
from __future__ import annotations

from typing import Any

from src.config import settings


class LiveBroker:
    """
    实盘券商 Broker。需配置 REAL_BROKER_* 并在此类内对接券商 HTTP/柜台 API。
    未配置或未实现时，所有方法返回 status/errcode 表示不可用。
    """

    def __init__(self) -> None:
        self._enabled = bool(
            getattr(settings, "real_broker_base_url", None)
            and getattr(settings, "real_broker_api_key", None)
        )

    def get_balance(self) -> dict[str, Any]:
        if not self._enabled:
            return {"available": 0, "total": 0, "error": "real broker not configured"}
        # TODO: 调用券商资金查询 API
        return {"available": 0, "total": 0, "error": "not implemented"}

    def get_positions(self) -> list[dict[str, Any]]:
        if not self._enabled:
            return []
        # TODO: 调用券商持仓 API
        return []

    def order_buy(self, symbol: str, volume: int, price: float | None = None) -> dict[str, Any]:
        if not self._enabled:
            return {"order_id": "", "status": "rejected", "message": "real broker not configured"}
        # TODO: 调用券商买入 API
        return {"order_id": "", "status": "rejected", "message": "not implemented"}

    def order_sell(self, symbol: str, volume: int, price: float | None = None) -> dict[str, Any]:
        if not self._enabled:
            return {"order_id": "", "status": "rejected", "message": "real broker not configured"}
        # TODO: 调用券商卖出 API
        return {"order_id": "", "status": "rejected", "message": "not implemented"}


def get_live_broker() -> LiveBroker:
    """获取实盘 Broker 实例；未配置时返回的实例所有操作会返回错误。"""
    return LiveBroker()
