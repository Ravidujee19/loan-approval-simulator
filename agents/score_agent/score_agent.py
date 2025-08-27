from fastapi import FastAPI
import pandas as pd
import joblib

app = FastAPI()

# Load each model model and scaler once at startup and get the one with highest accuracy
LRegModel = joblib.load("agents/score_agent/logisticRegression.pkl")
LRegScaler = joblib.load("agents/score_agent/logisticRegressionScaler.pkl")




#####after done training models must check which gets the highjest accuracy and then get the one with highest accuracy

def score_applicant(applicant_data: dict):
    # Convert to DataFrame
    applicant_df = pd.DataFrame([applicant_data])

    # Clean columns
    applicant_df.columns = applicant_df.columns.str.strip()
    for col in applicant_df.select_dtypes(include='object').columns:
        applicant_df[col] = applicant_df[col].str.strip()

    # To encode categorical features
    applicant_df = pd.get_dummies(applicant_df, drop_first=True)

    # Align with training features
    applicant_df = applicant_df.reindex(columns=LRegModel.feature_names_in_, fill_value=0)

    # Scale
    applicant_scaled = LRegScaler.transform(applicant_df)

    # Predict
    prob = LRegModel.predict_proba(applicant_scaled)[:, 1][0]
    pred = LRegModel.predict(applicant_scaled)[0]

    return {
        "prediction": "Approved" if pred == 1 else "Rejected",
        "probability": float(prob)
    }


###From here we get the applicant data of ravidu aiyya. it calls the function above

@app.post("/score")         ####ravidu aiyyas applicant data comes here
def score_endpoint(applicant: dict):
    return score_applicant(applicant)