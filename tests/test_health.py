"""健康检查与基础 API 可访问性。"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from src.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    j = r.json()
    assert j.get("status") == "ok"
    assert "version" in j


def test_daily_report_requires_symbols_or_default():
    r = client.get("/api/daily-report")
    assert r.status_code in (200, 400)
    if r.status_code == 200:
        body = r.json()
        assert "summary" in body or "checklist" in body or "buy_sell_points" in body
    else:
        assert "symbols" in r.json().get("detail", "").lower() or "STOCK_SYMBOLS" in str(r.json())


def test_daily_report_symbols_capped():
    many = ",".join(["600519"] * 25)
    r = client.get("/api/daily-report", params={"symbols": many})
    assert r.status_code == 200
    body = r.json()
    assert len(body.get("symbols_queried", [])) <= 20


def test_chart_returns_png():
    r = client.get("/api/chart", params={"symbol": "600519", "days": "30"})
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("image/png")
    assert len(r.content) > 100


def test_suggestions_multi_structure():
    mock_result = {
        "suggestions": {
            "perspectives": [{"role": "游资策略", "summary": "x", "actions": []}],
            "combined": {"summary": "y", "actions": []},
        },
        "market": {},
        "industries_and_symbols": {},
        "error": None,
    }
    with patch("src.main.run_news_to_trade_multi", return_value=mock_result):
        r = client.get("/api/news-trade/suggestions-multi")
    assert r.status_code == 200
    body = r.json()
    assert "suggestions" in body
    assert "perspectives" in body["suggestions"]
    assert "combined" in body["suggestions"]


def test_news_trade_run_dry_run_multi():
    mock_out = {
        "news": [],
        "industries_and_symbols": {"symbols": ["600519"]},
        "market": {"index": {}, "symbols": []},
        "suggestions": {"combined": {"summary": "ok", "actions": []}},
        "orders": [],
        "error": None,
    }
    with patch("src.main.run_news_to_trade_multi", return_value=mock_out):
        r = client.post("/api/news-trade/run?dry_run=true&multi=true")
    assert r.status_code == 200
    body = r.json()
    assert "suggestions" in body
    assert body.get("suggestions", {}).get("combined") is not None


def test_news_trade_run_cooldown():
    from src.config import settings
    mock_out = {"orders": [], "suggestions": {}, "error": None}
    with patch("src.main.run_news_to_trade", return_value=mock_out), patch.object(settings, "news_trade_cooldown_seconds", 999.0):
        r1 = client.post("/api/news-trade/run?dry_run=false")
        assert r1.status_code == 200
        r2 = client.post("/api/news-trade/run?dry_run=false")
        assert r2.status_code == 429
        assert "cooldown" in r2.json().get("detail", "")
