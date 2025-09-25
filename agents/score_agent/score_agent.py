from fastapi import FastAPI
import pandas as pd
import joblib
import json
import os

app = FastAPI()


###Creating a dictionary with all models info
models_info = {
    "logisticRegression": {
        "model": joblib.load("agents/score_agent/model/model_info/logisticRegression_info/logisticRegression.pkl"),
        "scaler": joblib.load("agents/score_agent/model/model_info/logisticRegression_info/logisticRegressionScaler.pkl"),
        "accuracy": json.load(open("agents/score_agent/model/model_info/logisticRegression_info/logisticRegression_accuracy.json"))["accuracy"],
        "columns": json.load(open("agents/score_agent/model/model_info/logisticRegression_info/logisticRegression_columns.json"))

    },
    "mlpClassifier": {
        "model": joblib.load("agents/score_agent/model/model_info/mlpClassifier_info/mlpClassifier.pkl"),
        "scaler": joblib.load("agents/score_agent/model/model_info/mlpClassifier_info/mlpClassifierScaler.pkl"),
        "accuracy": json.load(open("agents/score_agent/model/model_info/mlpClassifier_info/mlpClassifier_accuracy.json"))["accuracy"],
         "columns": json.load(open("agents/score_agent/model/model_info/mlpClassifier_info/mlpClassifier_columns.json"))
    }
    ##Add thenura's model
}

# Pick the best model by accuracy
best_model_name = max(models_info, key=lambda name: models_info[name]["accuracy"])
best_model = models_info[best_model_name]["model"]
best_scaler = models_info[best_model_name]["scaler"]

print(f"✅ Using best model: {best_model_name} (Accuracy: {models_info[best_model_name]['accuracy']:.4f})")



#####after done training models must check which gets the highjest accuracy and then get the one with highest accuracy

def score_applicant(applicant_data: dict):
    # Convert applicant dictionary to a DataFrame
    applicant_df = pd.DataFrame([applicant_data])

    # Clean columns
    applicant_df.columns = applicant_df.columns.str.strip()
    for col in applicant_df.select_dtypes(include='object').columns:
        applicant_df[col] = applicant_df[col].str.strip()

    # To encode categorical features
    applicant_df = pd.get_dummies(applicant_df, drop_first=True)

    # Align with training features
    applicant_df = applicant_df.reindex(columns=models_info[best_model_name]["columns"], fill_value=0)  

    
    ##Incase if the model which was the best doesnt have a scaler
    if best_scaler is not None:
        applicant_scaled = best_scaler.transform(applicant_df)
    else:
        applicant_scaled = applicant_df

    # Predict
    prob = best_model.predict_proba(applicant_scaled)[:, 1][0]
    pred = best_model.predict(applicant_scaled)[0]

    #To get the score out of 100
    score = round(prob * 100, 2)

    

    return {
        "model_used": best_model_name,
        "prediction": "Approved" if pred == 1 else "Rejected",
        "score": score
    }


###From here we get the applicant data of ravidu aiyya. it calls the function above

@app.post("/score")         ####ravidu aiyyas applicant data comes here
def score_endpoint(applicant: dict):
    return score_applicant(applicant)

