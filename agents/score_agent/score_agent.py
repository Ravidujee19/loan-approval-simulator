from fastapi import FastAPI
import pandas as pd
import joblib
import json
import os
import shap
import numpy as np

app = FastAPI()


###Creating a dictionary with all models info
models_info = {
    "logisticRegression": {
        "model": joblib.load("agents/score_agent/model/model_info/logisticRegression_info/logisticRegression.pkl"),
        "preprocessor": joblib.load("agents/score_agent/model/model_info/logisticRegression_info/logisticRegression_preprocessor.pkl"),
        "metrics": json.load(open("agents/score_agent/model/model_info/logisticRegression_info/logisticRegression_metrics.json"))
    },
    "mlpClassifier": {
        "model": joblib.load("agents/score_agent/model/model_info/mlpClassifier_info/mlpClassifier.pkl"),
        "preprocessor": joblib.load("agents/score_agent/model/model_info/mlpClassifier_info/mlpClassifier_preprocessor.pkl"), 
        "metrics": json.load(open("agents/score_agent/model/model_info/mlpClassifier_info/mlpClassifier_metrics.json")),
        "background": joblib.load("agents/score_agent/model/model_info/mlpClassifier_info/mlpClassifier_background.pkl")
    }
    ##Add thenura's model
}

# Pick the best model by accuracy
best_model_name = max(models_info, key=lambda name: models_info[name]["metrics"]["accuracy"])
best_model = models_info[best_model_name]["model"]
best_preprocessor = models_info[best_model_name].get("preprocessor", None)
best_metrics = models_info[best_model_name]["metrics"]
best_background = models_info[best_model_name].get("background", None)


print(f"Using best model: {best_model_name} (Accuracy: {best_metrics['accuracy']:.4f})")

# Precompute SHAP explainer for MLP to speed up requests
mlp_explainer = None
if best_model_name == "mlpClassifier" and best_background is not None:
    mlp_explainer = shap.KernelExplainer(best_model.predict_proba, best_background)


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

     # SHAP explanation
    shap_dict = {}
    try:
        if best_model_name == "logisticRegression":
            explainer = shap.LinearExplainer(best_model, best_background)
            shap_values = explainer.shap_values(applicant_transformed)
        elif best_model_name == "mlpClassifier":
            if mlp_explainer is None:
                print("No background data for SHAP. Skipping SHAP values.")
                shap_values = None
            else:
                shap_values = mlp_explainer.shap_values(applicant_transformed)
        else:
            shap_values = None

            # Get feature names
        try:
            feature_names = best_preprocessor.get_feature_names_out()
        except:
            feature_names = applicant_df.columns

        # Convert SHAP to dict
        shap_dict = {}
        if shap_values is not None:
            shap_list = shap_values[1][0] if isinstance(shap_values, list) and len(shap_values) == 2 else shap_values[0]
            for col, val in zip(feature_names, shap_list):
                shap_value = float(np.array(val).flatten()[0])
                shap_dict[col] = round(shap_value, 4)


    except Exception as e:
        import traceback
        print("SHAP computation error:", e)
        traceback.print_exc()
        shap_dict = {}

   
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
        },
        "shap_values": shap_dict
    }


###From here we get the applicant data of ravidu aiyya. it calls the function above

@app.post("/score")         ####ravidu aiyyas applicant data comes here
def score_endpoint(applicant: dict):
    return score_applicant(applicant)
