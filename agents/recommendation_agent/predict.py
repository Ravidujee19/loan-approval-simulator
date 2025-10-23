from __future__ import annotations
from pathlib import Path
import os, json, sys
import joblib
import pandas as pd

from agents.recommendation_agent.features import RiskFeatureBuilder  # noqa: F401
import types
main_mod = sys.modules.get("__main__")
if main_mod is None:
    main_mod = types.ModuleType("__main__")
    sys.modules["__main__"] = main_mod
setattr(main_mod, "RiskFeatureBuilder", RiskFeatureBuilder)

HERE = Path(__file__).parent                 
REPO_ROOT = HERE.parents[1]                   

CANDIDATE_DIRS = [
    HERE / "models",                          
    REPO_ROOT / "models",                     
    REPO_ROOT / "agents" / "score_agent" / "models",  
]

MODEL_FILENAME = "risk_cluster_pipeline.joblib"
CLUSTER_JSON = "cluster_to_risk.json"
RECS_JSON = "recommendations.json"

def _light_validate(pipe) -> bool:
    """Accept if the object has a predict()."""
    return hasattr(pipe, "predict")

def _try_load(dir_path: Path):
    mp = dir_path / MODEL_FILENAME
    if not mp.exists():
        return None
    try:
        pipe = joblib.load(mp)
    except Exception:
        return None
    if not _light_validate(pipe):
        return None
    return pipe, dir_path / CLUSTER_JSON, dir_path / RECS_JSON

def _resolve_model():
    # Mannual override
    override = os.getenv("RECOMMENDER_MODEL_DIR")
    if override:
        out = _try_load(Path(override))
        if out:
            return out

    # check candidates
    for d in CANDIDATE_DIRS:
        out = _try_load(d)
        if out:
            return out

    # recursive search from repo root
    for mp in REPO_ROOT.rglob(MODEL_FILENAME):
        out = _try_load(mp.parent)
        if out:
            return out

    tried = ", ".join(str(p) for p in CANDIDATE_DIRS)
    raise FileNotFoundError(
        f"Could not load {MODEL_FILENAME}. Tried: {tried} and recursive search under {REPO_ROOT}.\n"
        "Set RECOMMENDER_MODEL_DIR to the correct folder if needed."
    )

PIPE, CLUSTER_MAP_PATH, RECS_PATH = _resolve_model()

if not CLUSTER_MAP_PATH.exists():
    raise FileNotFoundError(f"Missing {CLUSTER_JSON} next to model at: {CLUSTER_MAP_PATH}")
if not RECS_PATH.exists():
    raise FileNotFoundError(f"Missing {RECS_JSON} next to model at: {RECS_PATH}")

with CLUSTER_MAP_PATH.open() as f:
    CLUSTER_TO_RISK = json.load(f)
with RECS_PATH.open() as f:
    RECS = json.load(f)

def rule_override(app: dict) -> str | None:
    income = float(app.get("income_annum", 0))
    loan   = float(app.get("loan_amount", 0))
    cibil  = float(app.get("cibil_score", 0))
    monthly_income = income / 12.0
    r = 0.12 / 12
    n = max(int(float(app.get("loan_term", 1)) * 12), 1)
    if loan > 0:
        pow_ = (1 + r) ** n
        emi = loan * r * pow_ / (pow_ - 1)
    else:
        emi = 0.0
    dti = emi / (monthly_income + 1e-6)
    if (cibil < 600 and (loan / (income + 1e-6) > 3 or dti > 0.6)): return "High Risk"
    if (cibil > 720 and (loan / (income + 1e-6) < 0.5 and dti < 0.25)): return "Low Risk"
    return None

def predict_and_recommend(applicant: dict) -> dict:
    row = pd.DataFrame([applicant])
    cluster = int(PIPE.predict(row)[0])
    risk = CLUSTER_TO_RISK.get(str(cluster), f"Cluster {cluster}")
    override = rule_override(applicant)
    if override is not None:
        risk = override
    tips = RECS[risk]
    return {"cluster": cluster, "risk_level": risk, "recommendations": tips}

def recommend(features: dict, approved: bool = False) -> dict:
    return predict_and_recommend(features)

