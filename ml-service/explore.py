import pandas as pd

PATH = "data/paysim.csv"
df =pd.read_csv(PATH)

print("=== 1. Aperçu ===")
print(df.shape)
print(df.dtypes)
print(df.head())
print("valeurs manquantes :", df.isna().sum().sum())

print("\n=== 2. Déséquilibre ===")
print(df["isFraud"].value_counts())
print(f"taux de fraude : {df['isFraud'].mean() * 100:.3f} %")

print("\n=== 3. Fraude par type de transaction ===")
print(df.groupby("type")["isFraud"].agg(["count", "sum", "mean"]))

print("\n=== 4. Montants : fraude vs normale ===")
print(df.groupby("isFraud")["amount"].describe())

print("\n=== 5. Comptes vidés ===")
df["emptied"] = (df["newbalanceOrig"] == 0) & (df["oldbalanceOrg"] > 0)
print(pd.crosstab(df["emptied"], df["isFraud"], normalize="index"))

print("\n=== 6. Incohérence des soldes (origine) ===")
df["errOrig"] = df["oldbalanceOrg"] - df["amount"] - df["newbalanceOrig"]
print(df.groupby("isFraud")["errOrig"].describe())

print("\n=== 7. isFlaggedFraud ===")
print(pd.crosstab(df["isFlaggedFraud"], df["isFraud"]))