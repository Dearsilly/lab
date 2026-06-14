"""Tests for Flask API."""
import json
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from api.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["status"] == "ok"


def test_score_missing_text(client):
    resp = client.post("/api/v1/score", json={})
    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert data["success"] is False


def test_score_empty_text(client):
    resp = client.post("/api/v1/score", json={"text": ""})
    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert data["success"] is False


def test_score_wrong_content_type(client):
    resp = client.post("/api/v1/score", data="not json")
    assert resp.status_code == 400


def test_404(client):
    resp = client.get("/api/v1/nonexistent")
    assert resp.status_code == 404
