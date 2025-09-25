from fastapi import FastAPI
import requests
from predict import predict_and_recommend  # import your existing function

app = FastAPI()

@app.post("/recommend")
def recommend(applicant: dict):
    # Step 1: Optionally send applicant to Applicant Agent (if needed)
    # response = requests.post("http://localhost:8000/applicant", json=applicant)
    # applicant_data = response.json()

    # Step 2: Optionally get scores from Score Agent
    # score_response = requests.post("http://localhost:8001/score", json=applicant)
    # scored_data = score_response.json()

    # Step 3: Use local ML function
    result = predict_and_recommend(applicant)  # you can replace applicant with scored_data if you get it from Score Agent
    return result
