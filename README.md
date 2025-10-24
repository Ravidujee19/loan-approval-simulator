
# Loan Approval Simulator

A **multi-agent system** to simulate automated loan approval decisions.  
Built with **FastAPI + React (Vite)** + ML models.  

---

## 🚀 Overview

### Agents
- **Applicant Evaluator** (`agents/applicant_evaluator/`)
  - Extracts + validates applicant data (form + uploaded docs).
  - Builds feature vector → calls Score & Recommendation agents.
  - Persists profiles in `_ae_store/`.

- **Score Agent** (`agents/score_agent/`)
  - ML model predicts **approval score/outcome**.
  - Exposed at `/score`.

- **Recommendation Agent** (`agents/recommendation_agent/`)
  - Generates improvement suggestions.
  - Exposed at `/api/v1/recommend`.

- **Frontend (loan-ui/)**
  - Vite + React app for form input & results dashboard.

---

## 🏗️ Architecture

```
[React Frontend] → [Applicant Evaluator API]
        |                |
        |                + -> calls → [Score Agent]
        |                + -> calls → [Recommendation Agent]
        |
        └── Results stored in _ae_store/<applicant_id>/profiles/<loan_id>.json
```

---

## ⚡ Quickstart 

### 1. Setup environment
```bash
git clone
cd loan-approval-simulator
python -m venv .venv
.venv\Scripts\activate    (Windows)
source .venv/bin/activate (Linux/Mac)

pip install -r requirements.txt
```

### 2. Run services

**Applicant Evaluator (port 8000):**
```bash
uvicorn agents.applicant_evaluator.app.main:app --reload --host 0.0.0.0 --port 8000
```

**Score Agent (port 8001):**
```bash
uvicorn agents.score_agent.api:app --reload --host 0.0.0.0 --port 8001
```

**Recommendation Agent (port 8200):**
```bash
uvicorn agents.recommendation_agent.api:app --reload --host 0.0.0.0 --port 8200
```

**Frontend (port 5173 default):**
```bash
cd loan-ui
npm install
npm run dev
```

---





---

## ✅ Features Implemented
- [x] Multi-agent architecture (Evaluator, Score, Recommender).
- [x] Applicant form + doc upload pipeline.
- [x] Feature vector building & rules engine.
- [x] Model-based scoring.
- [x] Recommendation service.
- [x] React frontend.
- [x] Explainability (feature importance / SHAP).
- [x] Fairness checks (Responsible AI).
- [x] LLM-powered extraction & IR (for documents).

---

## 📂 Repo Structure
```
loan-approval-simulator/
│── agents/
│   ├── applicant_evaluator/
│   ├── score_agent/
│   └── recommendation_agent/
│── loan-ui/                # React frontend
│── models/                 # ML models 
│── data/                   # Sample data
│── requirements.txt
│── README.md
```

---

## 🧑‍💻 Authors
- Team Preditora
