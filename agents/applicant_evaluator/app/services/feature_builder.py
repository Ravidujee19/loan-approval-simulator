from ..schemas.applicant_profile import Features

def to_features(fields: dict) -> Features:
    # education normalization
    edu_raw = (fields.get("education") or "").strip()
    edu = "Graduate" if edu_raw == "Graduate" else ("Not Graduate" if edu_raw == "Not Graduate" else "Not Graduate")

    # self_employed normalization
    se_raw = str(fields.get("self_employed", "")).strip().lower()
    se_bool = True if se_raw in {"yes", "true", "1"} else False

    return Features(
        no_of_dependents = int(fields.get("no_of_dependents", 0)),
        education = edu,                      # "Graduate" / "Not Graduate"
        self_employed = se_bool,              # bool (True/False)
        income_annum = float(fields.get("income_annum", 0.0)),
        loan_amount = float(fields.get("loan_amount", 0.0)),
        loan_term = int(fields.get("loan_term", 2)),   # YEARS 
        cibil_score = int(fields.get("cibil_score", 300)),
        residential_assets_value = float(fields.get("residential_assets_value", 0.0)),
        commercial_assets_value = float(fields.get("commercial_assets_value", 0.0)),
        luxury_assets_value = float(fields.get("luxury_assets_value", 0.0)),
        bank_asset_value = float(fields.get("bank_asset_value", 0.0)),
    )