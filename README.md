# Loan Approval Simulator – Agents

This project contains two main FastAPI microservices used in the loan approval simulator:

1. **Applicant Evaluator Agent** – Handles authentication, feature validation, and feature engineering (EMI, DTI, burden, etc.).
2. **Score Agent** – Provides credit risk scoring, including probability of default and risk bands.

---

## 📌 Applicant Evaluator Agent

FastAPI service that:

- Authenticates officers (`POST /login`)
- Validates applicant inputs
- Engineers features such as:
  - **EMI** (Equated Monthly Installment)  
  - **DTI** (Debt-to-Income ratio)  
  - **Burden metrics**  

### 🔧 Run Locally (with venv)

```bash
cd agents/applicant_evaluator
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env

# Start server
uvicorn applicant_evaluator:app --host 0.0.0.0 --port 5001 --reload
```

---

## 📌 Score Agent

FastAPI service that provides **credit risk scoring**.

### Endpoints
- `GET /health` → Health check
- `POST /score` → Returns credit score with details:
  ```json
  {
    "score": 720,
    "band": "A",
    "prob_default": 0.02,
    "factors": ["low DTI", "stable income"],
    "confidence": 0.93,
    "model_id": "v1.0"
  }
  ```

### 🔧 Run Locally

```bash
cd agents/score_agent

# Start server
uvicorn score_agent:app --host 0.0.0.0 --port 5002 --reload
```

---

## 📂 Project Structure

```
agents/
│── applicant_evaluator/    # Feature validation & officer login
│   ├── applicant_evaluator.py
│   └── .env.example
│
│── score_agent/            # Credit scoring logic
│   ├── score_agent.py
|   ├── .env.example
│   └── models/             # ML models (future expansion)
```

---

## 🚀 Next Steps

- Containerize both agents using Docker
- Add authentication/authorization middleware
- Extend Score Agent to support multiple ML models (ensemble)
- Integrate with frontend for loan approval workflow




# Applicant Evaluator (FastAPI + React)

See `.http/` for example requests and `Makefile` for common targets.

Run local:
- Backend: `uvicorn agents.applicant_evaluator.app.main:app --reload --port 8000`
- Frontend: `npm --prefix loan-ui install && npm --prefix loan-ui run dev`

Docker:
- `docker compose up --build`

Testing:
- `make coverage` (coverage gate 80% in CI)

