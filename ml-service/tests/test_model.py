from pathlib import Path

import joblib
import pandas as pd
import pytest

ROOT = Path(__file__).parent.parent
MODEL_PATH = ROOT / "models" / "model.joblib"
COLUMNS = ["type", "amount", "oldbalanceOrg", "oldbalanceDest"]

pytestmark = pytest.mark.skipif(
    not MODEL_PATH.exists(), reason="model.joblib absent : lancer train.py")


@pytest.fixture(scope="module")
def model():
    return joblib.load(MODEL_PATH)


def score(model, **kw):
    row = {"type": "TRANSFER", "amount": 100.0,
           "oldbalanceOrg": 5000.0, "oldbalanceDest": 0.0}
    row.update(kw)
    return float(model.predict_proba(pd.DataFrame([row])[COLUMNS])[0, 1])




def test_score_is_a_probability_like_value(model):
    assert 0.0 <= score(model) <= 1.0


def test_prediction_is_deterministic(model):
    assert score(model, amount=777.0) == score(model, amount=777.0)


def test_destination_balance_has_no_effect_outside_transfer(model):
    a = score(model, type="CASH_OUT", amount=200_000.0,
              oldbalanceOrg=200_000.0, oldbalanceDest=0.0)
    b = score(model, type="CASH_OUT", amount=200_000.0,
              oldbalanceOrg=200_000.0, oldbalanceDest=75_000.0)
    assert a == pytest.approx(b)
