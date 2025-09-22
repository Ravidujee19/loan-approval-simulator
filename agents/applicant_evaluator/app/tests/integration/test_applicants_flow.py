from fastapi.testclient import TestClient

from agents.applicant_evaluator.app.main import app

client = TestClient(app)


def test_register_login_and_create_applicant():
    r = client.post("/api/v1/auth/register", json={"email": "a@a.com", "password": "User@12345", "role": "applicant"})
    assert r.status_code == 200
    r = client.post("/api/v1/auth/login", json={"email": "a@a.com", "password": "User@12345"})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    p = {
        "first_name": "A",
        "last_name": "B",
        "email": "a@a.com",
        "phone": "+94",
        "dob": "1990-01-01",
        "employment_status": "employed",
        "employer_name": "C",
        "monthly_income": 100000,
        "other_income": 0,
        "existing_monthly_debt": 0
    }
    r = client.post("/api/v1/applicants", headers=headers, json=p)
    assert r.status_code == 200
