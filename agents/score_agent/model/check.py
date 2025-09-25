import joblib

# Load your preprocessor
preprocessor = joblib.load("agents/score_agent/model/model_info/mlpClassifier_info/preprocessor.pkl")

# Get all feature names after transformation
feature_names = preprocessor.get_feature_names_out()

# Print them
print("Features expected by the model:")
for f in feature_names:
    print(f)

