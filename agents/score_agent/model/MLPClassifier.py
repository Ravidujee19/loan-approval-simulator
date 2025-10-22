import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, roc_auc_score, classification_report
)
import joblib
import json

df = pd.read_csv("agents/score_agent/model/loan_approval_dataset.csv")
print("Dataset loaded successfully!")
print(df.head())

# To Strip whitespace from column names
df.columns = df.columns.str.strip()

# Strip whitespace from string values in all object columns
for col in df.select_dtypes(include='object').columns:
    df[col] = df[col].str.strip()

# Target variable
y = df['loan_status'].map({'Approved': 1, 'Rejected': 0})

# Check for NaNs in y
print("Missing target values:", y.isnull().sum())

# Features
X = df.drop('loan_status', axis=1)

# Drop  ID column if present
if 'loan_id' in X.columns:
    X = X.drop('loan_id', axis=1)


#To split the training and test data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Identify categorical columns
categorical_cols = X.select_dtypes(include='object').columns.tolist()
numeric_cols = X.select_dtypes(include=['int64', 'float64']).columns.tolist()

# Column transformer for one-hot encode categorical and to scale numeric
preprocessor = ColumnTransformer(
    transformers=[
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_cols),
        ('num', StandardScaler(), numeric_cols)
    ]
)

# Fit on training data, transform both train & test
X_train_processed = preprocessor.fit_transform(X_train)
X_test_processed = preprocessor.transform(X_test)

#Training the MLP Classifier

MLP = MLPClassifier(
    hidden_layer_sizes=(100, 50),  # Two hidden layers
    activation='relu',             # The activation function=rectified linear unit activation function
    solver='adam',                 # Optimizer
    max_iter=500,                  # Increase if not converging
    random_state=42,
    early_stopping=True,
    validation_fraction=0.1,
    n_iter_no_change=20,
    verbose=True,
)

MLP.fit(X_train_processed, y_train)


#evaluate the model
y_pred = MLP.predict(X_test_processed)

y_prob = MLP.predict_proba(X_test_processed)[:, 1]

metrics = {
    "accuracy": accuracy_score(y_test, y_pred),
    "precision": precision_score(y_test, y_pred),
    "recall": recall_score(y_test, y_pred),
    "f1_score": f1_score(y_test, y_pred),
    "roc_auc": roc_auc_score(y_test, y_prob),
    "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),  # convert to list for JSON
    "classification_report": classification_report(y_test, y_pred, target_names=["Rejected", "Approved"], output_dict=True)
}
print("\n--- MLP Classifier Metrics ---")
for key, value in metrics.items():
    print(f"{key}: {value}")

# Save MLP model and preprocessor
joblib.dump(MLP, "agents/score_agent/mlpClassifier.pkl")
joblib.dump(preprocessor, "agents/score_agent/mlpClassifier_preprocessor.pkl")



# Save metrics to JSON file
with open("agents/score_agent/mlpClassifier_metrics.json", "w") as f:
    json.dump(metrics, f, indent=4)



print("\nModel, preprocessor, columns, and metrics saved successfully!")



