import pytest
from fastapi.testclient import TestClient

from app.main import app, predictor

VALID = {"type": "TRANSFER", "amount": 9500.0, "oldbalanceOrg": 9500.0, "oldbalanceDest": 0.0}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:      # le "with" déclenche le chargement du modèle
        yield c


needs_model = pytest.mark.skipif(
    not (predictor.__class__ and __import__("pathlib").Path("models/model.joblib").exists()),
    reason="model.joblib absent")


@needs_model
def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["model_loaded"] is True


@needs_model
def test_predict_returns_score_and_version(client):
    r = client.post("/predict", json=VALID)
    assert r.status_code == 200
    body = r.json()
    assert 0.0 <= body["score"] <= 1.0
    assert body["modelVersion"]


def test_unknown_type_is_rejected(client):
    r = client.post("/predict", json={**VALID, "type": "CRYPTO"})
    assert r.status_code == 422


def test_negative_amount_is_rejected(client):
    r = client.post("/predict", json={**VALID, "amount": -5})
    assert r.status_code == 422


def test_missing_field_is_rejected(client):
    r = client.post("/predict", json={"type": "TRANSFER", "amount": 100})
    assert r.status_code == 422


@needs_model
def test_api_key_is_enforced_when_configured(client, monkeypatch):
    monkeypatch.setenv("ML_API_KEY", "secret")
    assert client.post("/predict", json=VALID).status_code == 401
    ok = client.post("/predict", json=VALID, headers={"X-API-Key": "secret"})
    assert ok.status_code == 200