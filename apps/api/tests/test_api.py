"""Integration tests for the FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _no_groq(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)


@pytest.fixture
def client():
    from main import app
    return TestClient(app)


class TestHealthEndpoint:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestAnalyzeEndpoint:
    def test_basic_analysis(self, client):
        resp = client.post("/analyze", json={"text": "You agree to binding arbitration."})
        assert resp.status_code == 200
        data = resp.json()
        assert data["signal"] in ("red", "yellow", "green")
        assert "issues" in data
        assert "disclaimer" in data

    def test_empty_text_rejected(self, client):
        resp = client.post("/analyze", json={"text": ""})
        assert resp.status_code == 422

    def test_missing_text_rejected(self, client):
        resp = client.post("/analyze", json={})
        assert resp.status_code == 422

    def test_response_model_fields(self, client):
        resp = client.post("/analyze", json={"text": "Normal terms of service text."})
        assert resp.status_code == 200
        data = resp.json()
        assert "signal" in data
        assert "issue_count" in data
        assert "analysis_source" in data
        assert "rule_locales_used" in data
        assert isinstance(data["issues"], list)

    def test_source_url_passthrough(self, client):
        resp = client.post("/analyze", json={
            "text": "You agree to binding arbitration.",
            "source_url": "https://example.com/tos"
        })
        data = resp.json()
        assert data["source_url"] == "https://example.com/tos"

    def test_text_too_large(self, client):
        resp = client.post("/analyze", json={"text": "x" * 200_000})
        assert resp.status_code == 422
