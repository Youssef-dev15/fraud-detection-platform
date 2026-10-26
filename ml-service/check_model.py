import joblib
import pandas as pd
from pathlib import Path

model = joblib.load(Path(__file__).parent / "models" / "model.joblib")

sample = pd.DataFrame([
    {"type": "TRANSFER", "amount": 9500.0, "oldbalanceOrg": 9500.0, "oldbalanceDest": 0.0},
    {"type": "PAYMENT",  "amount": 50.0,   "oldbalanceOrg": 4000.0, "oldbalanceDest": 0.0},
])
print(model.predict_proba(sample)[:, 1])