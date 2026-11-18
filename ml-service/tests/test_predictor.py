
import json
import numpy as np
import pytest

from app import predictor as predictor_module
from app.predictor import Predictor
from app.features import FEATURE_COLUMNS_V2


class FakeModel:
    def predict_proba(self, data):
        return np.array([[0.15, 0.85]])


def test_predictor_initialization():
    predictor = Predictor()

    assert predictor.model is None
    assert predictor.version is None


def test_loaded_false_without_model():
    predictor = Predictor()

    assert predictor.loaded is False


def test_loaded_true_with_model():
    predictor = Predictor()
    predictor.model = FakeModel()

    assert predictor.loaded is True


def test_load_model_success(monkeypatch, tmp_path):
    predictor = Predictor()

    model_path = tmp_path / "model.joblib"
    model_path.touch()

    metadata_path = tmp_path / "model_metadata.json"
    metadata_path.write_text(
        json.dumps({"modelVersion": "v1.0"}),
        encoding="utf-8"
    )

    monkeypatch.setattr(
        predictor_module,
        "MODELS_DIR",
        tmp_path
    )

    monkeypatch.setattr(
        predictor_module.joblib,
        "load",
        lambda path: FakeModel()
    )

    predictor.load()

    assert predictor.loaded is True
    assert predictor.version == "v1.0"


def test_load_without_model_file(monkeypatch, tmp_path):
    predictor = Predictor()

    monkeypatch.setattr(
        predictor_module,
        "MODELS_DIR",
        tmp_path
    )

    with pytest.raises(FileNotFoundError):
        predictor.load()


def test_load_without_metadata(monkeypatch, tmp_path):
    predictor = Predictor()

    model_path = tmp_path / "model.joblib"
    model_path.touch()

    monkeypatch.setattr(
        predictor_module,
        "MODELS_DIR",
        tmp_path
    )

    monkeypatch.setattr(
        predictor_module.joblib,
        "load",
        lambda path: FakeModel()
    )

    predictor.load()

    assert predictor.loaded is True
    assert predictor.version == "unknown"


def test_predict_returns_float():
    predictor = Predictor()
    predictor.model = FakeModel()

    score = predictor.predict(
        tx_type="TRANSFER",
        amount=5000,
        old_balance_orig=10000,
        old_balance_dest=2000
    )

    assert isinstance(score, float)
    assert score == pytest.approx(0.85)


def test_predict_uses_expected_features():
    predictor = Predictor()
    fake_model = FakeModel()

    predictor.model = fake_model

    score = predictor.predict(
        tx_type="CASH_OUT",
        amount=1000,
        old_balance_orig=3000,
        old_balance_dest=500
    )

    assert score == pytest.approx(0.85)
    assert list(FEATURE_COLUMNS_V2) == list(
        FEATURE_COLUMNS_V2
    )


def test_predict_without_loaded_model():
    predictor = Predictor()

    with pytest.raises(AttributeError):
        predictor.predict(
            tx_type="TRANSFER",
            amount=1000,
            old_balance_orig=2000,
            old_balance_dest=500
        )
