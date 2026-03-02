"""
简单内存缓存，TTL 秒，用于新闻/行情避免短时重复请求 AKShare。
"""
from __future__ import annotations

import time
from typing import Any, Callable, TypeVar

T = TypeVar("T")

_store: dict[str, tuple[Any, float]] = {}
_DEFAULT_TTL = 60.0


def _key(prefix: str, *parts: Any) -> str:
    return f"{prefix}:{':'.join(str(p) for p in parts)}"


def get_or_set(key: str, factory: Callable[[], T], ttl: float = _DEFAULT_TTL) -> T:
    now = time.monotonic()
    if key in _store:
        val, expiry = _store[key]
        if now < expiry:
            return val
    val = factory()
    _store[key] = (val, now + ttl)
    return val


def clear() -> None:
    _store.clear()
