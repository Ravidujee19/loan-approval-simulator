from fastapi import FastAPI
import pandas as pd
import joblib

app = FastAPI()

# Load model and scaler once at startup
model = joblib.load("agents/score_agent/logisticRegression.pkl")
scaler = joblib.load("agents/score_agent/logisticRegressionScaler.pkl")

def score_applicant(applicant_data: dict):
    # Convert to DataFrame
    applicant_df = pd.DataFrame([applicant_data])

    # Clean columns
    applicant_df.columns = applicant_df.columns.str.strip()
    for col in applicant_df.select_dtypes(include='object').columns:
        applicant_df[col] = applicant_df[col].str.strip()

    # One-hot encode categorical features
    applicant_df = pd.get_dummies(applicant_df, drop_first=True)

    # Align with training features
    applicant_df = applicant_df.reindex(columns=model.feature_names_in_, fill_value=0)

    # Scale
    applicant_scaled = scaler.transform(applicant_df)

    # Predict
    prob = model.predict_proba(applicant_scaled)[:, 1][0]
    pred = model.predict(applicant_scaled)[0]

    return {
        "prediction": "Approved" if pred == 1 else "Rejected",
        "probability": float(prob)
    }

@app.post("/score")
def score_endpoint(applicant: dict):
    return score_applicant(applicant)