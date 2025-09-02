import joblib
import pandas as pd
import numpy as np
import json
from pathlib import Path

# Config (same as train.py)
ANNUAL_INTEREST = 0.12
MONTHLY_RATE = ANNUAL_INTEREST / 12
NUM_FEATURES = [
    "no_of_dependents", "income_annum", "loan_amount", "loan_term", "cibil_score",
    "residential_assets_value", "commercial_assets_value", "luxury_assets_value", "bank_asset_value"
]
CAT_FEATURES = ["education", "self_employed"]

# Load artifacts
PREPROC = joblib.load("models/reco_preproc.joblib")
KMEANS = joblib.load("models/reco_kmeans.joblib")

# Optional: load rules (if you saved some recommendations in a JSON file)
def load_rules():
    try:
        with open("models/reco_rules.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # Default rules if no custom recommendations are available
        return {
            "0": {"name": "Low Risk", "approved": ["Automate EMI payments", "Prepay loans to save interest"], "rejected": ["Increase income or reduce loan amount"]},
            "1": {"name": "Medium Risk", "approved": ["Keep DTI below 40%", "Consider a longer loan term"], "rejected": ["Improve credit score or increase assets"]},
            "2": {"name": "High Risk", "approved": ["Consider loan insurance", "Improve financial stability"], "rejected": ["Reduce loan amount or increase down payment"]},
        }

RULES = load_rules()

# Function to compute EMI
def compute_emi(principal, monthly_rate, months):
    if months <= 0 or principal <= 0:
        return 0.0
    r, n = monthly_rate, int(months)
    if r == 0:
        return principal / n
    pow_ = (1 + r) ** n
    return principal * r * pow_ / (pow_ - 1)

# Function to process applicant data and make recommendations
def recommend(applicant_data, approved):
    # Clean and standardize the incoming data
    row = {key.strip(): value for key, value in applicant_data.items()}  # Remove any accidental spaces

    # Build DataFrame
    df = pd.DataFrame([row])
    
    # Preprocess the features (same as in training)
    X_processed = PREPROC.transform(df)

    # Predict cluster
    cluster = KMEANS.predict(X_processed)[0]
    
    # Compute dynamic values like EMI, DTI for advice
    loan_amount = row.get("loan_amount", 0)
    loan_term = row.get("loan_term", 1)
    cibil_score = row.get("cibil_score", 0)
    monthly_income = row.get("income_annum", 0) / 12
    emi = compute_emi(loan_amount, MONTHLY_RATE, loan_term * 12)
    dti = emi / monthly_income if monthly_income > 0 else np.nan

    # Get the recommendations
    persona = RULES.get(str(cluster), {}).get("name", f"Cluster {cluster}")
    tips = RULES.get(str(cluster), {}).get("approved" if approved else "rejected", [])
    
    # Provide extra info like DTI and EMI
    extra_info = [
        f"Estimated EMI: {emi:,.2f}",
        f"DTI (Debt-to-Income): {dti * 100:.2f}%" if not np.isnan(dti) else "DTI: Data unavailable"
    ]
    
    return {
       "cluster": int(cluster),

        "persona": persona,
        "approved": approved,
        "advice": extra_info + tips
    }

# Sample applicant data (for testing)
if __name__ == "__main__":
    sample_applicant = {
        "no_of_dependents": 3,
        "income_annum": 300000,            # Low annual income (Rs. 25,000/month)
        "loan_amount": 1200000,            # High loan
        "loan_term": 3,                    # Short term
        "cibil_score": 580,                # Poor CIBIL score
        "residential_assets_value": 0,
        "commercial_assets_value": 0,
        "luxury_assets_value": 0,
        "bank_asset_value": 0,
        "education": "Not Graduate",
        "self_employed": "Yes"
}


    # Test with approved = True
    result = recommend(sample_applicant, approved=True)
    print(json.dumps(result, indent=2))
