# agents/recommendation_agent/predict.py
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

# -----------------------------
# Define the same class used in training (must appear BEFORE joblib.load)
# -----------------------------
ANNUAL_INTEREST = 0.12
MONTHLY_RATE = ANNUAL_INTEREST / 12

RAW_NUM = [
    "no_of_dependents","income_annum","loan_amount","loan_term","cibil_score",
    "residential_assets_value","commercial_assets_value","luxury_assets_value","bank_asset_value"
]
RAW_CAT = ["education","self_employed"]

class RiskFeatureBuilder(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        df = X.copy()
        df.columns = df.columns.str.strip()
        needed = RAW_NUM + RAW_CAT
        missing = [c for c in needed if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        df = df[needed].copy()

        # numerics -> numeric + impute
        df[RAW_NUM] = df[RAW_NUM].apply(pd.to_numeric, errors="coerce")
        df[RAW_NUM] = df[RAW_NUM].fillna(df[RAW_NUM].median(numeric_only=True))

        # guards
        df["loan_term"] = df["loan_term"].clip(lower=1)  # years
        for col in ["income_annum","loan_amount",
                    "residential_assets_value","commercial_assets_value",
                    "luxury_assets_value","bank_asset_value"]:
            df[col] = df[col].clip(lower=0)

        # categoricals
        for c in RAW_CAT:
            if df[c].isna().any():
                df[c] = df[c].fillna("Unknown")

        # engineered features
        df["loan_to_income"] = df["loan_amount"] / (df["income_annum"] + 1e-6)

        def compute_emi(p, r, n):
            if p <= 0 or n <= 0:
                return 0.0
            pow_ = (1 + r) ** n
            return p * r * pow_ / (pow_ - 1)

        term_months = (df["loan_term"] * 12).astype(int).clip(lower=1)
        df["emi"] = [compute_emi(p, MONTHLY_RATE, n) for p, n in zip(df["loan_amount"].values, term_months.values)]
        df["monthly_income"] = df["income_annum"] / 12.0
        df["dti"] = df["emi"] / (df["monthly_income"] + 1e-6)

        for col in ["income_annum","loan_amount",
                    "residential_assets_value","commercial_assets_value",
                    "luxury_assets_value","bank_asset_value"]:
            df[f"log_{col}"] = np.log1p(df[col].clip(lower=0))

        eng = ["loan_to_income","dti","emi","monthly_income",
               "log_income_annum","log_loan_amount",
               "log_residential_assets_value","log_commercial_assets_value",
               "log_luxury_assets_value","log_bank_asset_value"]
        df[eng] = df[eng].replace([np.inf, -np.inf], np.nan)
        df[eng] = df[eng].fillna(df[eng].median(numeric_only=True))
        return df

# -----------------------------
# Load artifacts (now that class exists)
# -----------------------------
PIPE = joblib.load("models/risk_cluster_pipeline.joblib")
with open("models/cluster_to_risk.json") as f:
    CLUSTER_TO_RISK = json.load(f)
with open("models/recommendations.json") as f:
    RECS = json.load(f)

# Optional: override for extreme cases
def rule_override(app):
    income = float(app.get("income_annum", 0))
    loan   = float(app.get("loan_amount", 0))
    cibil  = float(app.get("cibil_score", 0))
    monthly_income = income / 12.0
    r = 0.12 / 12
    n = max(int(float(app.get("loan_term", 1)) * 12), 1)
    if loan > 0:
        pow_ = (1 + r) ** n
        emi = loan * r * pow_ / (pow_ - 1)
    else:
        emi = 0.0
    dti = emi / (monthly_income + 1e-6)

    if (cibil < 600 and (loan / (income + 1e-6) > 3 or dti > 0.6)):
        return "High Risk"
    if (cibil > 720 and (loan / (income + 1e-6) < 0.5 and dti < 0.25)):
        return "Low Risk"
    return None

def predict_and_recommend(applicant: dict):
    row = pd.DataFrame([applicant])
    cluster = int(PIPE.predict(row)[0])
    risk = CLUSTER_TO_RISK.get(str(cluster), f"Cluster {cluster}")
    override = rule_override(applicant)
    if override is not None:
        risk = override
    tips = RECS[risk]
    return {"cluster": cluster, "risk_level": risk, "recommendations": tips}

# Quick test
if __name__ == "__main__":
    low = {
        "no_of_dependents": 1,
        "income_annum": 1500000,
        "loan_amount": 30000000000,
        "loan_term": 10,
        "cibil_score": 690,
        "residential_assets_value": 500000,
        "commercial_assets_value": 200000,
        "luxury_assets_value": 100000,
        "bank_asset_value": 300000,
        "education": "Graduate",
        "self_employed": "No"
    }
    mid = {
        "no_of_dependents": 2,
        "income_annum": 600000,
        "loan_amount": 500000,
        "loan_term": 5,
        "cibil_score": 650,
        "residential_assets_value": 100000,
        "commercial_assets_value": 0,
        "luxury_assets_value": 0,
        "bank_asset_value": 50000,
        "education": "Graduate",
        "self_employed": "Yes"
    }
    high = {
        "no_of_dependents": 4,
        "income_annum": 20000000000,
        "loan_amount": 10000,
        "loan_term": 2,
        "cibil_score": 680,
        "residential_assets_value": 11111110,
        "commercial_assets_value":1111110,
        "luxury_assets_value": 111111110,
        "bank_asset_value": 111110,
        "education": "Not Graduate",
        "self_employed": "Yes"
    }
    for name, app in [("Low", low), ("Medium", mid), ("High", high)]:
        print(name, "→", predict_and_recommend(app))
