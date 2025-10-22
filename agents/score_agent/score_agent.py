from fastapi import FastAPI
import pandas as pd
import joblib
import json
import os

app = FastAPI()


###Creating a dictionary with all models info
models_info = {
    "logisticRegression": {
        "model": joblib.load("agents/score_agent/logisticRegression.pkl"),
        "preprocessor": joblib.load("agents/score_agent/logisticRegression_preprocessor.pkl"),
        "metrics": json.load(open("agents/score_agent/logisticRegression_metrics.json"))
    },
    "mlpClassifier": {
        "model": joblib.load("agents/score_agent/mlpClassifier.pkl"),
        "preprocessor": joblib.load("agents/score_agent/mlpClassifier_preprocessor.pkl"), 
        "metrics": json.load(open("agents/score_agent/mlpClassifier_metrics.json"))
    }
    ##Add thenura's model
}

# Pick the best model by accuracy
best_model_name = max(models_info, key=lambda name: models_info[name]["metrics"]["accuracy"])
best_model = models_info[best_model_name]["model"]
best_preprocessor = models_info[best_model_name].get("preprocessor", None)
best_metrics = models_info[best_model_name]["metrics"]


print(f"Using best model: {best_model_name} (Accuracy: {best_metrics['accuracy']:.4f})")


#####after done training models must check which gets the highjest accuracy and then get the one with highest accuracy

def score_applicant(applicant_data: dict):
    # Convert applicant dictionary to a DataFrame
    applicant_df = pd.DataFrame([applicant_data])

    # Clean columns
    applicant_df.columns = applicant_df.columns.str.strip()
    for col in applicant_df.select_dtypes(include='object').columns:
        applicant_df[col] = applicant_df[col].str.strip()

   # Transform using preprocessor (handles encoding + scaling)
    applicant_transformed = best_preprocessor.transform(applicant_df)

    # Predict
    prob = best_model.predict_proba(applicant_transformed)[:, 1][0]
    pred = best_model.predict(applicant_transformed)[0]

    #To get the score out of 100
    score = round(prob * 100, 2)

    
    return {
        "model_used": best_model_name,
        "prediction": "Approved" if pred == 1 else "Rejected",
        "score": score,
        "model_metrics": {
            "accuracy": best_metrics.get("accuracy"),
            "precision": best_metrics.get("precision"),
            "recall": best_metrics.get("recall"),
            "f1_score": best_metrics.get("f1_score"),
            "roc_auc": best_metrics.get("roc_auc")
        }
    }


###From here we get the applicant data of ravidu aiyya. it calls the function above

@app.post("/score")         ####ravidu aiyyas applicant data comes here
def score_endpoint(applicant: dict):
    return score_applicant(applicant)

