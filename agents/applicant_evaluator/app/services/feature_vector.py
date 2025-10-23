from typing import List
from ..schemas.applicant_profile import Features

# exact CSV order 
FEATURE_ORDER = [
    "no_of_dependents",
    "education",               # 1 for Graduate, 0 for Not Graduate
    "self_employed",           # 1 for Yes/True, 0 for No/False
    "income_annum",
    "loan_amount",
    "loan_term",               # YEARS 
    "cibil_score",
    "residential_assets_value",
    "commercial_assets_value",
    "luxury_assets_value",
    "bank_asset_value",
]



def feats_to_dict(f: Features) -> dict:
    return {
        "no_of_dependents": f.no_of_dependents,
        "education": f.education,
        "self_employed": f.self_employed,
        "income_annum": f.income_annum,
        "loan_amount": f.loan_amount,
        "loan_term": f.loan_term,
        "cibil_score": f.cibil_score,
        "residential_assets_value": f.residential_assets_value,
        "commercial_assets_value": f.commercial_assets_value,
        "luxury_assets_value": f.luxury_assets_value,
        "bank_asset_value": f.bank_asset_value,
    }

def to_vector(feats: Features, order: list[str] | None = None) -> list[float]:
    order = order or FEATURE_ORDER
    d = {
        "no_of_dependents": feats.no_of_dependents,
        "education": 1.0 if feats.education == "Graduate" else 0.0,
        "self_employed": 1.0 if bool(feats.self_employed) else 0.0,
        "income_annum": feats.income_annum,
        "loan_amount": feats.loan_amount,
        "loan_term": feats.loan_term,   # keep years
        "cibil_score": feats.cibil_score,
        "residential_assets_value": feats.residential_assets_value,
        "commercial_assets_value": feats.commercial_assets_value,
        "luxury_assets_value": feats.luxury_assets_value,
        "bank_asset_value": feats.bank_asset_value,
    }
    return [float(d[k]) for k in order]
