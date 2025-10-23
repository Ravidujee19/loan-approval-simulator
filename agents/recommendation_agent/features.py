from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

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
