# This code is use forn testing purposes only

# from services import rules, feature_builder, feature_vector, extractor
from agents.applicant_evaluator.app.services import rules, feature_builder, feature_vector, extractor

text = "Ravi has 2 dependents, is a Graduate, self-employed, earns 8 lakhs per year and wants a 20 lakhs loan for 20 years with CIBIL score 750."


from agents.applicant_evaluator.app.services.llm_client import call_llm_hf

prompt = "Return a JSON object: {\"test_key\": \"hello world\"}"
ok, resp = call_llm_hf(prompt)
print("OK:", ok)
print("RESP:", resp)


# Sample applicant data
applicant_data = {
    "loan_id": "LN1001",
    "no_of_dependents": 2,
    "education": "Graduate",
    "self_employed": "True",
    "income_annum": 850000,
    "loan_amount": 1800000,
    "loan_term": 240,
    "cibil_score": 760,
    "residential_assets_value": 400000,
    "commercial_assets_value": 250000,
    "luxury_assets_value": 120000,
    "bank_asset_value": 300000
}

# Run through evaluator pipeline
warnings, hard_stops = rules.check(applicant_data)
features_obj = feature_builder.to_features(applicant_data)
feature_vector_list = feature_vector.to_vector(features_obj)

print("Warnings:", warnings)
print("Hard Stops:", hard_stops)
print("\nFeatures Object:", features_obj.model_dump())
print("\nFeature Vector:", feature_vector_list)
print("\nNlp details:", extractor.extract_applicant_details(text))
print("\nNlp vs Form:", extractor.validate_consistency(extractor.extract_applicant_details(text), applicant_data))