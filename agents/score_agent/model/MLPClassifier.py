import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler,OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score
import joblib
import json

df = pd.read_csv("data/raw/loan_approval_dataset.csv")
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
X = df.drop(['loan_status', 'loan_id'], axis=1, errors='ignore')  # drop loan_id if exists

# Identify numeric and categorical columns
numeric_cols = X.select_dtypes(include=['int64', 'float64']).columns.tolist()
categorical_cols = X.select_dtypes(include=['object']).columns.tolist()

# ColumnTransformer for scaling + encoding
preprocessor = ColumnTransformer([
    ('num', StandardScaler(), numeric_cols),
    ('cat', OneHotEncoder(drop='first', handle_unknown='ignore'), categorical_cols)
])


#To split the training and test data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)


# Fit preprocessor on training data
X_train_transformed = preprocessor.fit_transform(X_train)
X_test_transformed = preprocessor.transform(X_test)



MLP = MLPClassifier(hidden_layer_sizes=(100, 50), max_iter=500, random_state=42)
""""
MLP = MLPClassifier(
    hidden_layer_sizes=(100, 50),  # Two hidden layers
    activation='relu',             # The activation function=rectified linear unit activation function
    solver='adam',                 # Optimizer
    max_iter=500,                  # Increase if not converging
    random_state=42
)
"""

MLP.fit(X_train_transformed, y_train)
y_pred = MLP.predict(X_test_transformed)

print("\n--- MLP Classifier Results ---")
print("Accuracy:", accuracy_score(y_test, y_pred))
accuracy = accuracy_score(y_test, y_pred)


# Save MLP model and preprocessor
joblib.dump(MLP, "agents/score_agent/model/model_info/mlpClassifier_info/mlpClassifier.pkl")
joblib.dump(preprocessor, "agents/score_agent/model/model_info/mlpClassifier_info/preprocessor.pkl")


#to save the accuracy to use in the score agent
import json

with open("agents/score_agent/model/model_info/mlpClassifier_info/mlpClassifier_accuracy.json", "w") as f:
    json.dump({"accuracy": accuracy}, f)


#to save the training coloumns
training_columns = X.columns.tolist()  
with open("agents/score_agent/model/model_info/mlpClassifier_info/mlpClassifier_columns.json", "w") as f:
    json.dump(training_columns, f)
