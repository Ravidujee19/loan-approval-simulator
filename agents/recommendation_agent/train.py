import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# ---------------- CONFIG ----------------
RAW_NUM = [
    "no_of_dependents","income_annum","loan_amount","loan_term","cibil_score",
    "residential_assets_value","commercial_assets_value","luxury_assets_value","bank_asset_value"
]
RAW_CAT = ["education","self_employed"]

ANNUAL_INTEREST = 0.12
MONTHLY_RATE = ANNUAL_INTEREST / 12

MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)

# ------------- Feature Engineering Transformer -------------
class RiskFeatureBuilder(BaseEstimator, TransformerMixin):
    """Takes a DataFrame with the 11 raw columns and returns a DataFrame
       with engineered risk features appended (loan_to_income, emi, dti, logs),
       plus cleaned raw columns (clipped, imputed)."""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        df = X.copy()
        # Normalize column names and keep only required
        df.columns = df.columns.str.strip()
        needed = RAW_NUM + RAW_CAT
        missing = [c for c in needed if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        df = df[needed].copy()

        # Coerce numerics
        df[RAW_NUM] = df[RAW_NUM].apply(pd.to_numeric, errors="coerce")

        # Basic impute for raw numerics
        df[RAW_NUM] = df[RAW_NUM].fillna(df[RAW_NUM].median(numeric_only=True))
        # Guard/clip
        df["loan_term"] = df["loan_term"].clip(lower=1)  # in years
        for col in ["income_annum","loan_amount",
                    "residential_assets_value","commercial_assets_value",
                    "luxury_assets_value","bank_asset_value"]:
            df[col] = df[col].clip(lower=0)

        # Categorical impute
        for c in RAW_CAT:
            if df[c].isna().any():
                df[c] = df[c].fillna("Unknown")

        # Derived features
        # loan_to_income
        df["loan_to_income"] = df["loan_amount"] / (df["income_annum"] + 1e-6)

        # EMI
        def compute_emi(p, r, n):
            if p <= 0 or n <= 0:
                return 0.0
            pow_ = (1 + r) ** n
            return p * r * pow_ / (pow_ - 1)
        term_months = (df["loan_term"] * 12).astype(int).clip(lower=1)
        df["emi"] = [compute_emi(p, MONTHLY_RATE, n) for p, n in zip(df["loan_amount"].values, term_months.values)]

        # DTI
        df["monthly_income"] = df["income_annum"] / 12.0
        df["dti"] = df["emi"] / (df["monthly_income"] + 1e-6)

        # log transforms (skew guards)
        for col in ["income_annum","loan_amount",
                    "residential_assets_value","commercial_assets_value",
                    "luxury_assets_value","bank_asset_value"]:
            df[f"log_{col}"] = np.log1p(df[col].clip(lower=0))

        # Clean engineered NaN/inf
        eng = ["loan_to_income","dti","emi","monthly_income",
               "log_income_annum","log_loan_amount",
               "log_residential_assets_value","log_commercial_assets_value",
               "log_luxury_assets_value","log_bank_asset_value"]
        df[eng] = df[eng].replace([np.inf, -np.inf], np.nan)
        df[eng] = df[eng].fillna(df[eng].median(numeric_only=True))

        return df

# Features used downstream (post-feature-builder)
NUM_FEATURES = [
    "no_of_dependents","cibil_score","loan_to_income","dti",
    "log_income_annum","log_loan_amount",
    "log_residential_assets_value","log_commercial_assets_value",
    "log_luxury_assets_value","log_bank_asset_value"
]
CAT_FEATURES = RAW_CAT

# ---------------- LOAD DATA ----------------
df_raw = pd.read_csv("data/raw/loan_approval_dataset.csv")
df_raw.columns = df_raw.columns.str.strip()

# ---------------- PIPELINE ----------------
# OneHotEncoder API compat
try:
    ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False)  # sklearn >= 1.2
except TypeError:
    ohe = OneHotEncoder(handle_unknown="ignore", sparse=False)         # sklearn <= 1.1

preproc = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), NUM_FEATURES),
        ("cat", ohe, CAT_FEATURES),
    ],
    remainder="drop",
)

pipe = Pipeline(steps=[
    ("feats", RiskFeatureBuilder()),
    ("prep", preproc),
    ("kmeans", KMeans(n_clusters=3, random_state=42, n_init=10)),
])

# ---------------- FIT ----------------
pipe.fit(df_raw)  # fits feats -> prep -> kmeans
labels = pipe.named_steps["kmeans"].labels_

print("Cluster counts:", np.bincount(labels))

# ---------------- PROFILE & MAP RISK ----------------
# Build engineered frame for profiling (same transform as in pipeline)
fe = RiskFeatureBuilder().transform(df_raw)
profiling = pd.DataFrame({
    "cluster": labels,
    "loan_to_income": fe["loan_to_income"].values,
    "dti": fe["dti"].values,
    "cibil": fe["cibil_score"].values
})
prof = profiling.groupby("cluster").agg(
    avg_lti=("loan_to_income","mean"),
    avg_dti=("dti","mean"),
    avg_cibil=("cibil","mean"),
)
print("\n[Cluster Profiles]\n", prof)

# Sort by worse risk first: high LTI & DTI, low CIBIL
prof_sorted = prof.sort_values(by=["avg_lti","avg_dti","avg_cibil"], ascending=[False, False, True])
risk_names = ["High Risk","Medium Risk","Low Risk"]
cluster_to_risk = {int(c): risk_names[i] for i, c in enumerate(prof_sorted.index)}
print("\n[Cluster → Risk Mapping]\n", cluster_to_risk)

# ---------------- SAVE ----------------
joblib.dump(pipe, MODELS_DIR / "risk_cluster_pipeline.joblib")
with open(MODELS_DIR / "cluster_to_risk.json", "w") as f:
    json.dump({str(k): v for k, v in cluster_to_risk.items()}, f, indent=2)

# Optional: basic recommendations you can edit later
recs = {
    "Low Risk": [
        "Maintain timely EMI payments",
        "Consider part-prepayment to save interest",
        "Keep credit utilization low (<30%)",
    ],
    "Medium Risk": [
        "Keep DTI below ~40%; consider longer tenure",
        "Avoid new credit lines until score improves",
        "Track expenses; build 3–6 month emergency fund",
    ],
    "High Risk": [
        "Reduce loan amount or increase down payment",
        "Improve CIBIL for 3–6 months before reapplying",
        "Add co-borrower or show additional income proof",
    ],
}
with open(MODELS_DIR / "recommendations.json", "w") as f:
    json.dump(recs, f, indent=2)

print("\nTraining complete. Saved:")
print(f"  - {MODELS_DIR/'risk_cluster_pipeline.joblib'}")
print(f"  - {MODELS_DIR/'cluster_to_risk.json'}")
print(f"  - {MODELS_DIR/'recommendations.json'}")
