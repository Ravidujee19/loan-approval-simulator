from fastapi import FastAPI
import pandas as pd
import joblib
import json
import numpy as np
import os
from typing import Optional

app = FastAPI(title="Score Agent")

# Load models and artifacts
models_info = {
    "logisticRegression": {
        "model": joblib.load("agents/score_agent/model/model_info/logisticRegression_info/logisticRegression.pkl"),
        "scaler": joblib.load("agents/score_agent/model/model_info/logisticRegression_info/logisticRegressionScaler.pkl"),
        "accuracy": json.load(open("agents/score_agent/model/model_info/logisticRegression_info/logisticRegression_accuracy.json"))["accuracy"],
        "columns": json.load(open("agents/score_agent/model/model_info/logisticRegression_info/logisticRegression_columns.json")),
        "preprocessor": None,  
    },
    "mlpClassifier": {
        "model": joblib.load("agents/score_agent/model/model_info/mlpClassifier_info/mlpClassifier.pkl"),
        "preprocessor": joblib.load("agents/score_agent/model/model_info/mlpClassifier_info/preprocessor.pkl"),
        "accuracy": json.load(open("agents/score_agent/model/model_info/mlpClassifier_info/mlpClassifier_accuracy.json"))["accuracy"],
        "columns": json.load(open("agents/score_agent/model/model_info/mlpClassifier_info/mlpClassifier_columns.json")),
        "scaler": None,  
    }
}

# Pick best by accuracy
best_model_name = max(models_info, key=lambda n: models_info[n]["accuracy"])
best = models_info[best_model_name]
best_model = best["model"]
best_preprocessor = best.get("preprocessor")
best_scaler = best.get("scaler")
best_columns = best.get("columns")

print(f"✅ Using best model: {best_model_name} (Accuracy: {best['accuracy']:.4f})")

FEATURE_ORDER = [
    "no_of_dependents","education","self_employed","income_annum","loan_amount",
    "loan_term","cibil_score","residential_assets_value","commercial_assets_value",
    "luxury_assets_value","bank_asset_value",
]

def _normalize_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    # self_employed -> "Yes"/"No"
    if "self_employed" in df.columns:
        df["self_employed"] = (
            df["self_employed"]
            .map({True: "Yes", False: "No", "true": "Yes", "false": "No", 1: "Yes", 0: "No"})
            .fillna(df["self_employed"])
        ).astype(str).str.strip()

    # education normalization
    if "education" in df.columns:
        df["education"] = (
            df["education"]
            .replace({"Grad": "Graduate", "Not_Grad": "Not Graduate", "Not_Graduate": "Not Graduate"})
            .astype(str)
            .str.strip()
        )
        mask = ~df["education"].isin(["Graduate", "Not Graduate"])
        df.loc[mask, "education"] = "Unknown"
    return df

def _transform_for_model(df: pd.DataFrame):
    if best_preprocessor is not None:
        return best_preprocessor.transform(df)
    if best_scaler is not None and best_columns is not None:
        df_dum = pd.get_dummies(df, drop_first=False)
        df_aligned = df_dum.reindex(columns=best_columns, fill_value=0)
        return best_scaler.transform(df_aligned)
    return df.values

def _predict_proba_matrix(X) -> Optional[np.ndarray]:
    if hasattr(best_model, "predict_proba"):
        P = best_model.predict_proba(X)
        if isinstance(P, np.ndarray) and P.ndim == 2 and P.shape[1] >= 2:
            return P
    return None

def _decision_to_prob(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-z))

def _compute_probabilities(X) -> np.ndarray:
    P = _predict_proba_matrix(X)
    if P is not None:
        return P 
    if hasattr(best_model, "decision_function"):
        z = np.atleast_1d(best_model.decision_function(X)).astype(float)
        p = _decision_to_prob(z)
        P = np.column_stack([1.0 - p, p])
        return P
    y = np.atleast_1d(best_model.predict(X)).astype(float)
    P = np.column_stack([1.0 - y, y])
    return P

def _make_df(sample: dict) -> pd.DataFrame:
    row = {k: sample.get(k, None) for k in FEATURE_ORDER}
    df = pd.DataFrame([row])
    df.columns = df.columns.str.strip()
    for c in df.select_dtypes(include="object").columns:
        df[c] = df[c].astype(str).str.strip()
    df = _normalize_categoricals(df)
    return df

def _infer_approved_index() -> int:
    env_override = os.getenv("SCORE_APPROVED_CLASS")
    if env_override in {"0", "1"}:
        print(f"ℹ️ SCORE_APPROVED_CLASS override = {env_override}")
        return int(env_override)

    # GOOD and BAD sample
    good = {
        "no_of_dependents": 0,
        "education": "Graduate",
        "self_employed": "No",
        "income_annum": 3_600_000,   
        "loan_amount": 600_000,     
        "loan_term": 10,             
        "cibil_score": 800,
        "residential_assets_value": 1_000_000,
        "commercial_assets_value": 0,
        "luxury_assets_value": 0,
        "bank_asset_value": 500_000,
    }
    bad = {
        "no_of_dependents": 5,
        "education": "Not Graduate",
        "self_employed": "Yes",
        "income_annum": 300_000,     
        "loan_amount": 5_000_000,   
        "loan_term": 2,              
        "cibil_score": 350,
        "residential_assets_value": 0,
        "commercial_assets_value": 0,
        "luxury_assets_value": 0,
        "bank_asset_value": 0,
    }

    D_good = _make_df(good)
    X_good = _transform_for_model(D_good)
    P_good = _compute_probabilities(X_good)  
    D_bad = _make_df(bad)
    X_bad = _transform_for_model(D_bad)
    P_bad = _compute_probabilities(X_bad)

    classes = getattr(best_model, "classes_", None)
    if classes is not None and len(classes) >= 2:
        delta = (P_good[0] - P_bad[0])  
        idx = int(np.argmax(delta))
        print(f"🔎 Auto-detected approved class index via delta: {idx}, classes={list(classes)}")
        return idx

    # Fallback
    if P_good.shape[1] >= 2:
        idx = 1 if P_good[0, 1] > P_bad[0, 1] else 0
        print(f"Fallback approved index={idx} (no classes_)")
        return idx

    print("Could not infer approved index; defaulting to 1")
    return 1

APPROVED_IDX = _infer_approved_index()

def score_applicant(applicant_data: dict) -> dict:
    df = _make_df(applicant_data)
    X = _transform_for_model(df)
    P = _compute_probabilities(X)  # shape (1,2 or more)

    if P.shape[1] > 2:
        approved_prob = float(P[0, min(APPROVED_IDX, P.shape[1]-1)])
    else:
        approved_prob = float(P[0, APPROVED_IDX])

    approved_prob = float(np.clip(approved_prob, 0.0, 1.0))
    score = round(approved_prob * 100.0, 2)
    pred = "Approved" if approved_prob >= 0.5 else "Rejected"

    return {
        "model_used": best_model_name,
        "probability": round(approved_prob, 4),
        "score": score,
        "prediction": pred,
    }


@app.post("/score")
def score_endpoint_legacy(applicant: dict):
    return score_applicant(applicant)

# version manith
# from fastapi import FastAPI
# import pandas as pd
# import joblib
# import json


# app = FastAPI()


# ###Creating a dictionary with all models info
# models_info = {
#     "logisticRegression": {
#         "model": joblib.load("agents/score_agent/model/model_info/logisticRegression_info/logisticRegression.pkl"),
#         "scaler": joblib.load("agents/score_agent/model/model_info/logisticRegression_info/logisticRegressionScaler.pkl"),
#         "accuracy": json.load(open("agents/score_agent/model/model_info/logisticRegression_info/logisticRegression_accuracy.json"))["accuracy"],
#         "columns": json.load(open("agents/score_agent/model/model_info/logisticRegression_info/logisticRegression_columns.json"))

#     },
#     "mlpClassifier": {
#         "model": joblib.load("agents/score_agent/model/model_info/mlpClassifier_info/mlpClassifier.pkl"),
#         "preprocessor": joblib.load("agents/score_agent/model/model_info/mlpClassifier_info/preprocessor.pkl"),
#         "accuracy": json.load(open("agents/score_agent/model/model_info/mlpClassifier_info/mlpClassifier_accuracy.json"))["accuracy"],
#          "columns": json.load(open("agents/score_agent/model/model_info/mlpClassifier_info/mlpClassifier_columns.json"))
#     }
#     ##Add thenura's model
# }

# # Pick the best model by accuracy
# best_model_name = max(models_info, key=lambda name: models_info[name]["accuracy"])
# best_model = models_info[best_model_name]["model"]
# best_preprocessor = models_info[best_model_name].get("preprocessor", None)

# print(f"✅ Using best model: {best_model_name} (Accuracy: {models_info[best_model_name]['accuracy']:.4f})")



# #####after done training models must check which gets the highjest accuracy and then get the one with highest accuracy

# def score_applicant(applicant_data: dict):
#     # Convert applicant dictionary to a DataFrame
#     applicant_df = pd.DataFrame([applicant_data])

#     # Clean columns
#     applicant_df.columns = applicant_df.columns.str.strip()
#     for col in applicant_df.select_dtypes(include='object').columns:
#         applicant_df[col] = applicant_df[col].str.strip()

#     """
#     # To encode categorical features
#     applicant_df = pd.get_dummies(applicant_df, drop_first=True)

#     # Align with training features
#     applicant_df = applicant_df.reindex(columns=models_info[best_model_name]["columns"], fill_value=0)  

    
#     ##Incase if the model which was the best doesnt have a scaler
#     if best_scaler is not None:
#         applicant_scaled = best_scaler.transform(applicant_df)
#     else:
#         applicant_scaled = applicant_df
    
#     """

#     # Transform using preprocessor (handles scaling + encoding)
#     applicant_transformed = best_preprocessor.transform(applicant_df)

#     # Predict
#     prob = best_model.predict_proba(applicant_transformed)[:, 1][0]
#     pred = best_model.predict(applicant_transformed)[0]

#     #To get the score out of 100
#     score = round(prob * 100, 2)

    

#     return {
#         "model_used": best_model_name,
#         "prediction": "Approved" if pred == 1 else "Rejected",
#         "score": score
#     }


# ###From here we get the applicant data of ravidu aiyya. it calls the function above

# @app.post("/score")         ####ravidu aiyyas applicant data comes here
# def score_endpoint(applicant: dict):
#     return score_applicant(applicant)
