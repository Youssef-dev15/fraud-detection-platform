import json
from pathlib import Path

import joblib
import pandas as pd

from app.features import FEATURE_COLUMNS_V2

MODELS_DIR = Path(__file__).parent.parent / "models"


class Predictor:
    def __init__(self) -> None:
        self.model = None
        self.version: str | None = None

    @property
    def loaded(self) -> bool:
        return self.model is not None

    def load(self) -> None:
        model_path = MODELS_DIR / "model.joblib"
        if not model_path.exists():
            raise FileNotFoundError(f"Modèle introuvable : {model_path}. Lancer python train.py")
        self.model = joblib.load(model_path)
        meta_path = MODELS_DIR / "model_metadata.json"
        if meta_path.exists():
            self.version = json.loads(meta_path.read_text(encoding="utf-8"))["modelVersion"]
        else:
            self.version = "unknown"

    def predict(self, tx_type: str, amount: float,
                old_balance_orig: float, old_balance_dest: float) -> float:
        row = pd.DataFrame([{
            "type": tx_type,
            "amount": amount,
            "oldbalanceOrg": old_balance_orig,
            "oldbalanceDest": old_balance_dest,
        }])[FEATURE_COLUMNS_V2]
        return float(self.model.predict_proba(row)[0, 1])