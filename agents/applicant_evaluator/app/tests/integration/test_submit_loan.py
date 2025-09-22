import json

from fastapi.testclient import TestClient

from agents.applicant_evaluator.app.main import app

client = TestClient(app)


def auth_headers():
    client.post("/api/v1/auth/register", json={"email": "x@example.com", "password": "User@12345", "role": "applicant"})
    resp = client.post("/api/v1/auth/login", json={"email": "x@example.com", "password": "User@12345"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_full_flow():
    h = auth_headers()
    # create applicant
    app_payload = {
        "first_name": "Foo",
        "last_name": "Bar",
        "email": "x@example.com",
        "phone": "+940000000",
        "dob": "1995-01-01",
        "employment_status": "employed",
        "employer_name": "X",
        "monthly_income": 120000,
        "other_income": 0,
        "existing_monthly_debt": 10000,
    }
    r = client.post("/api/v1/applicants", headers=h, json=app_payload)
    assert r.status_code == 200, r.text
    applicant_id = r.json()["applicant_id"]

    # submit loan
    loan_payload = {
        "applicant_id": applicant_id,
        "amount_requested": 1000000,
        "term_months": 36,
        "loan_type": "personal",
        "purpose": "education",
    }
    r = client.post("/api/v1/loans", headers={**h, "Idempotency-Key": "it-1"}, json=loan_payload)
    assert r.status_code == 200, r.text
    loan = r.json()
    assert loan["evaluation"] is not None
