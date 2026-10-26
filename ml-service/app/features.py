import pandas as pd

FEATURE_COLUMNS = [
    "type", "amount",
    "oldbalanceOrg", "newbalanceOrig",
    "oldbalanceDest", "newbalanceDest",
]

def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["isAccountEmptied"] = ((df["newbalanceOrig"] == 0) & (df["oldbalanceOrg"] > 0)).astype(int)
    df["amountToBalanceRatio"] = df["amount"] / (df["oldbalanceOrg"] + 1)
    df["destWasEmpty"] = (df["oldbalanceDest"] == 0).astype(int)
    return df

FEATURE_COLUMNS_V2 = ["type", "amount", "oldbalanceOrg", "oldbalanceDest"]

def add_features_v2(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Règle métier : hors TRANSFER, il n'y a pas de compte destinataire interne
    df.loc[df["type"] != "TRANSFER", "oldbalanceDest"] = 0.0
    df["isAccountEmptied"] = ((df["oldbalanceOrg"] > 0) & (df["amount"] >= df["oldbalanceOrg"])).astype(int)
    df["amountToBalanceRatio"] = df["amount"] / (df["oldbalanceOrg"] + 1)
    df["destWasEmpty"] = (df["oldbalanceDest"] == 0).astype(int)
    return df