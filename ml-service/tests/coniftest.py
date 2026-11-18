
import pytest
from fastapi.testclient import TestClient

from app import main


@pytest.fixture
def client(monkeypatch):
    # Éviter de charger le vrai modèle pendant les tests
    monkeypatch.setattr(
        main.predictor,
        "load",
        lambda: None
    )

    with TestClient(main.app) as test_client:
        yield test_client


@pytest.fixture
def ready_client(client, monkeypatch):
    # Simuler un modèle déjà chargé
    main.predictor.model = object()
    main.predictor.version = "test-v1"

    # Simuler une prédiction ML
    monkeypatch.setattr(
        main.predictor,
        "predict",
        lambda *args: 0.85
    )

    yield client

    # Nettoyage
    main.predictor.model = None
    main.predictor.version = None
