# Simple NLP-based extractor for applicant details

import re
import spacy

# load spaCy model once (use: python -m spacy download en_core_web_sm)
nlp = spacy.load("en_core_web_sm")

def extract_applicant_details(text: str) -> dict:
    """Extract approximate applicant info from free text."""
    doc = nlp(text)
    data = {}

    # --- Money-like entities (income / loan) ---
    money_entities = [ent.text for ent in doc.ents if ent.label_ == "MONEY"]
    if money_entities:
        # crude heuristic: first is income, second is loan
        clean_nums = [int(re.sub(r"\D", "", m)) for m in money_entities if re.sub(r"\D", "", m)]
        if len(clean_nums) >= 1:
            data["income_annum"] = clean_nums[0]
        if len(clean_nums) >= 2:
            data["loan_amount"] = clean_nums[1]

    # --- Loan term (years or months) ---
    m = re.search(r"(\d+)\s*(years?|months?)", text.lower())
    if m:
        term = int(m.group(1))
        data["loan_term"] = term * 12 if "year" in m.group(2) else term

    # --- CIBIL or credit score ---
    m = re.search(r"(?:cibil|credit)\s*score\s*(\d{3})", text.lower())
    if m:
        data["cibil_score"] = int(m.group(1))

    # --- Dependents ---
    m = re.search(r"(\d+)\s*dependents?", text.lower())
    if m:
        data["no_of_dependents"] = int(m.group(1))

    # --- Education ---
    if "graduate" in text.lower():
        data["education"] = "Graduate"
    elif "not graduate" in text.lower():
        data["education"] = "Not Graduate"

    # --- Employment ---
    if "self-employed" in text.lower() or "own business" in text.lower():
        data["self_employed"] = True
    else:
        data["self_employed"] = False

    return data


def validate_consistency(extracted: dict, provided: dict) -> list[str]:
    """Compare NLP-extracted fields against provided form JSON."""
    mismatches = []
    for key, val in extracted.items():
        if key in provided and str(provided[key]) != str(val):
            mismatches.append(f"Inconsistent value for '{key}': NLP→{val}, Form→{provided[key]}")
    return mismatches
