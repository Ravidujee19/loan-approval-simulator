import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# 1. Load dataset
df = pd.read_csv("data/raw/loan_approval_dataset.csv")

#select numarical features and catgo features separetly
num_features = [
    " no_of_dependents",
    " income_annum",
    " loan_amount",
    " loan_term",
    " cibil_score",
    " residential_assets_value",
    " commercial_assets_value",
    " luxury_assets_value",
    " bank_asset_value",
]
cat_features = [" education", " self_employed"]

#dataset cleaning part
for c in num_features:
    df[c] = pd.to_numeric(df[c], errors="coerce")
df[num_features] = df[num_features].fillna(df[num_features].median())
df[cat_features] = df[cat_features].fillna("Unknown")

X = df[num_features + cat_features]

# 4. Preprocess: scale numerics + one-hot encode categoricals
try:
    # sklearn >= 1.2
    ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
except TypeError:
    # sklearn <= 1.1
    ohe = OneHotEncoder(handle_unknown="ignore", sparse=False)

preproc = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), num_features),
        ("cat", ohe, cat_features),
    ],
    remainder="drop",
)

X_prep = preproc.fit_transform(X)

# 4) Train K-Means
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
kmeans.fit(X_prep)

# Optional: show cluster sizes
labels = kmeans.labels_
unique, counts = np.unique(labels, return_counts=True)
print("[info] cluster sizes:", dict(zip(unique, counts)))

# 5) Save artifacts
Path("models").mkdir(exist_ok=True)
joblib.dump(preproc, "models/reco_preproc.joblib")
joblib.dump(kmeans, "models/reco_kmeans.joblib")
print("✅ Training completed. Saved: models/reco_preproc.joblib, models/reco_kmeans.joblib")

#checking quality of the clusters
print("Inertia:", kmeans.inertia_)
print("Silhouette Score:", silhouette_score(X_prep, kmeans.labels_))
