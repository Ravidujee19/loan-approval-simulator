from fastapi import FastAPI
import pandas as pd
import joblib
import json

app = FastAPI()

# --- Load models and artifacts ---
models_info = {
    "logisticRegression": {
        "model": joblib.load("agents/score_agent/model/model_info/logisticRegression_info/logisticRegression.pkl"),
        "scaler": joblib.load("agents/score_agent/model/model_info/logisticRegression_info/logisticRegressionScaler.pkl"),
        "accuracy": json.load(open("agents/score_agent/model/model_info/logisticRegression_info/logisticRegression_accuracy.json"))["accuracy"],
        "columns": json.load(open("agents/score_agent/model/model_info/logisticRegression_info/logisticRegression_columns.json")),
        "preprocessor": None,  # LR path uses scaler+columns
    },
    "mlpClassifier": {
        "model": joblib.load("agents/score_agent/model/model_info/mlpClassifier_info/mlpClassifier.pkl"),
        "preprocessor": joblib.load("agents/score_agent/model/model_info/mlpClassifier_info/preprocessor.pkl"),
        "accuracy": json.load(open("agents/score_agent/model/model_info/mlpClassifier_info/mlpClassifier_accuracy.json"))["accuracy"],
        "columns": json.load(open("agents/score_agent/model/model_info/mlpClassifier_info/mlpClassifier_columns.json")),
        "scaler": None,  # handled inside preprocessor pipeline
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


def _normalize_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    # self_employed -> "Yes"/"No"
    if "self_employed" in df.columns:
        df["self_employed"] = (
            df["self_employed"]
            .map({True: "Yes", False: "No", "true": "Yes", "false": "No", 1: "Yes", 0: "No"})
            .fillna(df["self_employed"])
        )
        df["self_employed"] = df["self_employed"].astype(str).str.strip()

    # education normalization
    if "education" in df.columns:
        df["education"] = (
            df["education"]
            .replace({"Grad": "Graduate", "Not_Grad": "Not Graduate", "Not_Graduate": "Not Graduate"})
            .astype(str)
            .str.strip()
        )
    return df


def _transform_for_model(df: pd.DataFrame):
    """
    - If preprocessor exists (MLP): use it.
    - Else if scaler+columns exist (LR): get_dummies -> reindex -> scale.
    - Else: return df.values as fallback.
    """
    if best_preprocessor is not None:
        return best_preprocessor.transform(df)

    if best_scaler is not None and best_columns is not None:
        df_dum = pd.get_dummies(df, drop_first=False)
        df_aligned = df_dum.reindex(columns=best_columns, fill_value=0)
        return best_scaler.transform(df_aligned)

    return df.values  # last resort


def score_applicant(applicant_data: dict) -> dict:
    # to DataFrame
    df = pd.DataFrame([applicant_data])

    # clean up whitespace
    df.columns = df.columns.str.strip()
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()

    # normalize categoricals
    df = _normalize_categoricals(df)

    # transform
    X = _transform_for_model(df)

    # predict proba/label
    if hasattr(best_model, "predict_proba"):
        prob = float(best_model.predict_proba(X)[:, 1][0])
    else:
        # fallback if model lacks predict_proba
        if hasattr(best_model, "decision_function"):
            import numpy as np
            raw = float(best_model.decision_function(X)[0])
            prob = 1 / (1 + np.exp(-raw))
        else:
            pred_label = int(best_model.predict(X)[0])
            prob = 0.9 if pred_label == 1 else 0.1

    pred = int(best_model.predict(X)[0])
    score = round(prob * 100, 2)

    return {
        "model_used": best_model_name,
        "prediction": "Approved" if pred == 1 else "Rejected",
        "score": score,
    }


@app.post("/score")
def score_endpoint(applicant: dict):
    # terminal error
    return score_applicant(applicant)



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
