import pandas as pd
from sklearn.model_selection import train_test_split
from app.features import FEATURE_COLUMNS
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    average_precision_score, roc_auc_score,
    confusion_matrix, precision_score, recall_score, f1_score,
)
from app.features import add_features
from app.features import FEATURE_COLUMNS_V2, add_features_v2
from pathlib import Path
import joblib
import json
from datetime import date
from pathlib import Path
import sklearn



DATA_PATH = "data/paysim.csv"
RANDOM_STATE = 42
NORMAL_PER_FRAUD = 10   # 10 transactions normales pour 1 fraude dans le train

# 1. Chargement : on ne lit que les colonnes utiles
df = pd.read_csv(DATA_PATH, usecols=FEATURE_COLUMNS + ["isFraud"])
X = df[FEATURE_COLUMNS]
y = df["isFraud"]

# 2. Découpage stratifié : AVANT toute autre opération
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
)

# 3. Sous-échantillonnage du TRAIN uniquement
train = X_train.copy()
train["isFraud"] = y_train
frauds = train[train["isFraud"] == 1]
normals = train[train["isFraud"] == 0].sample(
    n=len(frauds) * NORMAL_PER_FRAUD, random_state=RANDOM_STATE
)
train_bal = pd.concat([frauds, normals]).sample(frac=1, random_state=RANDOM_STATE)
X_train_bal = train_bal[FEATURE_COLUMNS]
y_train_bal = train_bal["isFraud"]

# 4. Vérifications
print("Train complet   :", len(X_train), "dont fraudes :", int(y_train.sum()))
print("Train équilibré :", len(X_train_bal), "dont fraudes :", int(y_train_bal.sum()))
print("Test            :", len(X_test), "dont fraudes :", int(y_test.sum()))
print(f"Taux de fraude test : {y_test.mean() * 100:.3f} %")
# partie 2 
CATEGORICAL = ["type"]
NUMERIC = [
    "amount", "oldbalanceOrg", "newbalanceOrig",
    "oldbalanceDest", "newbalanceDest",
    "isAccountEmptied", "amountToBalanceRatio", "destWasEmpty",
]

def make_pipeline(model, scale=False):
    numeric_step = StandardScaler() if scale else "passthrough"
    prep = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
        ("num", numeric_step, NUMERIC),
    ])
    return Pipeline([
        ("features", FunctionTransformer(add_features)),   # variables dérivées
        ("prep", prep),                                    # encodage + échelle
        ("model", model),
    ])

models = {
    "Régression logistique": make_pipeline(
        LogisticRegression(max_iter=1000), scale=True),
    "Random Forest": make_pipeline(
        RandomForestClassifier(
            n_estimators=200, max_depth=12, min_samples_leaf=5,
            n_jobs=-1, random_state=RANDOM_STATE)),
}

for name, pipe in models.items():
    pipe.fit(X_train_bal, y_train_bal)
    scores = pipe.predict_proba(X_test)[:, 1]


    print(f"\n===== {name} =====")
    print(f"AUC-PR  : {average_precision_score(y_test, scores):.4f}")
    print(f"AUC-ROC : {roc_auc_score(y_test, scores):.4f}")
    print("seuil | précision | rappel |   F1   |  VP |   FP |  FN")
    for t in (0.20, 0.40, 0.50, 0.60, 0.75, 0.90,0.95):
        pred = scores >= t
        tn, fp, fn, tp = confusion_matrix(y_test, pred).ravel()
        p = precision_score(y_test, pred, zero_division=0)
        r = recall_score(y_test, pred)
        f = f1_score(y_test, pred)
        print(f"{t:5.2f} | {p:9.3f} | {r:6.3f} | {f:6.3f} | {tp:4d} | {fp:5d} | {fn:4d}")
        
# teste de model choisi 
# Simule ce que Spring enverra : soldes projetés toujours cohérents
X_test_prod = X_test.copy()
X_test_prod["newbalanceOrig"] = (X_test_prod["oldbalanceOrg"] - X_test_prod["amount"]).clip(lower=0)
X_test_prod["newbalanceDest"] = X_test_prod["oldbalanceDest"] + X_test_prod["amount"]

rf = models["Random Forest"]
scores_prod = rf.predict_proba(X_test_prod)[:, 1]
print("\n===== Random Forest, soldes cohérents (simulation production) =====")
print(f"AUC-PR : {average_precision_score(y_test, scores_prod):.4f}")
print("seuil | précision | rappel |   F1   |  VP |   FP |  FN")
for t in (0.20, 0.40, 0.50, 0.75, 0.90):
    pred = scores_prod >= t
    tn, fp, fn, tp = confusion_matrix(y_test, pred).ravel()
    p = precision_score(y_test, pred, zero_division=0)
    r = recall_score(y_test, pred)
    f = f1_score(y_test, pred)
    print(f"{t:5.2f} | {p:9.3f} | {r:6.3f} | {f:6.3f} | {tp:4d} | {fp:5d} | {fn:4d}")
    
# Model V2 random forest

NUMERIC_V2 = ["amount", "oldbalanceOrg", "oldbalanceDest",
              "isAccountEmptied", "amountToBalanceRatio", "destWasEmpty"]

def report(title, y_true, scores):
    print(f"\n===== {title} =====")
    print(f"AUC-PR : {average_precision_score(y_true, scores):.4f}")
    print("seuil | précision | rappel |   F1   |  VP |   FP |  FN")
    for t in (0.20, 0.40, 0.50, 0.75, 0.90):
        pred = scores >= t
        tn, fp, fn, tp = confusion_matrix(y_true, pred).ravel()
        p = precision_score(y_true, pred, zero_division=0)
        r = recall_score(y_true, pred)
        f = f1_score(y_true, pred)
        print(f"{t:5.2f} | {p:9.3f} | {r:6.3f} | {f:6.3f} | {tp:4d} | {fp:5d} | {fn:4d}")

rf_v2 = Pipeline([
    ("features", FunctionTransformer(add_features_v2)),
    ("prep", ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
        ("num", "passthrough", NUMERIC_V2),
    ])),
    ("model", RandomForestClassifier(
        n_estimators=200, max_depth=12, min_samples_leaf=5,
        n_jobs=-1, random_state=RANDOM_STATE)),
])
rf_v2.fit(X_train_bal[FEATURE_COLUMNS_V2], y_train_bal)

# Test 1 : données PaySim telles quelles
report("RF v2 (sans soldes finaux)", y_test,
       rf_v2.predict_proba(X_test[FEATURE_COLUMNS_V2])[:, 1])

# Test 2 : hors TRANSFER, l'application n'a pas de compte destinataire interne,
# donc elle enverra oldbalanceDest = 0
X_test_app = X_test[FEATURE_COLUMNS_V2].copy()
X_test_app.loc[X_test_app["type"] != "TRANSFER", "oldbalanceDest"] = 0
report("RF v2, destinataire absent hors TRANSFER", y_test,
       rf_v2.predict_proba(X_test_app)[:, 1])
#Sauvegarde du modèle et de ses métadonnées
BASE_DIR = Path(__file__).resolve().parent
MODEL_VERSION = "1.0.0"
models_dir = BASE_DIR / "models"
models_dir.mkdir(exist_ok=True)

joblib.dump(rf_v2, models_dir / "model.joblib", compress=3)
scores_final = rf_v2.predict_proba(X_test[FEATURE_COLUMNS_V2])[:, 1]
metadata = {
    "modelVersion": MODEL_VERSION,
    "trainedAt": str(date.today()),
    "dataset": "PaySim (synthétique)",
    "features": FEATURE_COLUMNS_V2,
    "sklearnVersion": sklearn.__version__,
    "thresholds": {"low": 0.40, "high": 0.75},
    "metrics": {"auc_pr": round(float(average_precision_score(y_test, scores_final)), 4)},
}
(models_dir / "model_metadata.json").write_text(
    json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

size_mb = (models_dir / "model.joblib").stat().st_size / 1_000_000
print(f"\nModèle sauvegardé : {size_mb:.1f} Mo")