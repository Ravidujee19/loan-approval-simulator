import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score
import joblib

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

# Drop any non-numeric ID columns if present
if 'loan_id' in X.columns:
    X = X.drop('loan_id', axis=1)

# Encode categorical columns
X = pd.get_dummies(X, drop_first=True)



#To split the training and test data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Scale features
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

MLP = MLPClassifier(
    hidden_layer_sizes=(100, 50),  # Two hidden layers
    activation='relu',             # The activation function=rectified linear unit activation function
    solver='adam',                 # Optimizer
    max_iter=500,                  # Increase if not converging
    random_state=42
)

MLP.fit(X_train, y_train)
y_pred = MLP.predict(X_test)

print("\n--- MLP Classifier Results ---")
print("Accuracy:", accuracy_score(y_test, y_pred))
accuracy = accuracy_score(y_test, y_pred)


# Save MLP model and scaler
joblib.dump(MLP, "agents/score_agent/mlpClassifier.pkl")
joblib.dump(scaler, "agents/score_agent/mlpClassifierScaler.pkl")


#to save the accuracy to use in the score agent
import json

with open("agents/score_agent/mlpClassifier_accuracy.json", "w") as f:
    json.dump({"accuracy": accuracy}, f)
