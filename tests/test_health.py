"""健康检查与基础 API 可访问性。"""
import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_daily_report_requires_symbols_or_default():
    r = client.get("/api/daily-report")
    assert r.status_code in (200, 400)
    if r.status_code == 200:
        body = r.json()
        assert "summary" in body or "checklist" in body or "buy_sell_points" in body
    else:
        assert "symbols" in r.json().get("detail", "").lower() or "STOCK_SYMBOLS" in str(r.json())
