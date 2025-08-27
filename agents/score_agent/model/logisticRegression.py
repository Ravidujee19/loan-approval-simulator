
"""
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report



df = pd.read_csv("agents/score_agent/model/loan_approval_dataset.csv")

print(df.head())

df.columns = df.columns.str.strip()
# Features (everything except loan_status)
X = df.drop('loan_status', axis=1)

# Target (loan_status column)
y = df['loan_status']

y = y.map({'Approved':1, 'Rejected':0})  # converts to 1/0

# Encode categorical columns(To convert to numerical so that machine learning model can understand it)
X = pd.get_dummies(X, drop_first=True)


# Drop rows with missing target
y = y.dropna()
X = X.loc[y.index]


# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# Train logistic regression
model = LogisticRegression()
model.fit(X_train, y_train)

# Predict and evaluate
y_pred = model.predict(X_test)
print("Accuracy:", accuracy_score(y_test, y_pred))

"""


import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import os


# Load dataset
df = pd.read_csv("agents/score_agent/model/loan_approval_dataset.csv")
print("Dataset loaded successfully!")
print(df.head())

# Strip whitespace from column names
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

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scale features
LRegScaler = StandardScaler()
X_train = LRegScaler.fit_transform(X_train)
X_test = LRegScaler.transform(X_test)

# Train logistic regression
LReg = LogisticRegression()
LReg.fit(X_train, y_train)

# Predict and evaluate
y_pred = LReg.predict(X_test)

print("\nAccuracy:", accuracy_score(y_test, y_pred))


import joblib

#to save the model as a file to use in scoring agent
joblib.dump(LReg, "agents/score_agent/logisticRegression.pkl")

# To save the scaler
joblib.dump(LRegScaler, "agents/score_agent/logisticRegressionScaler.pkl")

