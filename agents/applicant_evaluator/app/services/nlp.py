import re
from typing import Dict, List, Tuple

# small keyword map 
EDU_MAP = {
    "nvq": "diploma", "diploma": "diploma",
    "bsc": "graduate", "ba": "graduate", "beng": "graduate", "undergraduate": "graduate",
    "msc": "postgraduate", "ma": "postgraduate", "mba": "postgraduate", "pg": "postgraduate",
    "phd": "doctorate", "doctorate": "doctorate",
    "alevel": "school", "a-level": "school", "olevel": "school", "o-level": "school",
}

NUM = r"[\d][\d,\. ]*"

def _num(s: str) -> float:
    s = s.replace(" ", "").replace(",", "")
    try:
        return float(s)
    except Exception:
        return 0.0

def extract_from_texts(docs: List[Dict], texts: List[str]) -> Tuple[Dict, List[Dict], Dict[str, float], Dict]:
    """
    Return: fields, provenance, confidences, extras (free-form info like name/age)
    """
    fields: Dict = {}
    provenance: List[Dict] = []
    conf: Dict[str, float] = {}
    extras: Dict[str, str | int | float | bool] = {}

    joined = "\n".join(texts).lower()

    # some identity/extra 
    m = re.search(r"name[:\s]+([a-z\s\.]+)", joined)
    if m:
        extras["name"] = m.group(1).strip()[:80]
    m = re.search(r"age[:\s]+(\d{2})", joined)
    if m:
        extras["age"] = int(m.group(1))

    # income
    m = re.search(r"(annual|yearly)\s+(income|salary)\D+(" + NUM + ")", joined)
    if m:
        val = _num(m.group(3))
        fields["income_annum"] = val
        conf["income_annum"] = 0.85
        provenance.append({"field": "income_annum", "source_doc": docs[0]["filename"] if docs else "", "method": "regex-annual", "snippet": m.group(0)[:120]})
    else:
        m2 = re.search(r"(gross|net)?\s*monthly\s+(income|salary)\D+(" + NUM + ")", joined)
        if m2:
            val = _num(m2.group(3)) * 12
            fields["income_annum"] = val
            conf["income_annum"] = 0.75
            provenance.append({"field": "income_annum", "source_doc": docs[0]["filename"] if docs else "", "method": "regex-monthly*12", "snippet": m2.group(0)[:120]})

    # dependents
    m = re.search(r"dependents?\D+(\d{1,2})", joined)
    if m:
        fields["no_of_dependents"] = int(m.group(1))
        conf["no_of_dependents"] = 0.65
        provenance.append({"field": "no_of_dependents", "source_doc": docs[0]["filename"] if docs else "", "method": "regex", "snippet": m.group(0)[:120]})

    # employment status
    if "self-employed" in joined or "self employed" in joined or "freelance" in joined:
        fields["self_employed"] = "Yes"
        conf["self_employed"] = 0.6
        provenance.append({"field": "self_employed", "source_doc": docs[0]["filename"] if docs else "", "method": "keyword", "snippet": "self employed"})
    elif "employed" in joined:
        fields["self_employed"] = "No"
        conf["self_employed"] = 0.6
        provenance.append({"field": "self_employed", "source_doc": docs[0]["filename"] if docs else "", "method": "keyword", "snippet": "employed"})
    
    # education
    if re.search(r"\bgraduate\b", joined):
        fields["education"] = "Graduate"
        conf["education"] = 0.6
        provenance.append({"field": "education", "source_doc": docs[0]["filename"] if docs else "", "method": "keyword", "snippet": "graduate"})
    elif re.search(r"\bnot\s+graduate\b|\bhigh\s*school\b|\bsecondary\b", joined):
        fields["education"] = "Not Graduate"
        conf["education"] = 0.6
        provenance.append({"field": "education", "source_doc": docs[0]["filename"] if docs else "", "method": "keyword", "snippet": "not graduate"})

    # cibil score
    m = re.search(r"cibil\D+(\d{3})", joined)
    if m:
        score = int(m.group(1))
        fields["cibil_score"] = score
        conf["cibil_score"] = 0.8
        provenance.append({"field": "cibil_score", "source_doc": docs[0]["filename"] if docs else "", "method": "regex", "snippet": m.group(0)[:120]})

    # assets (rough)
    asset_patterns = [
        ("residential_assets_value", r"residential (assets?|property|valuation)\D+(" + NUM + ")"),
        ("commercial_assets_value",  r"commercial (assets?|property|valuation)\D+(" + NUM + ")"),
        ("luxury_assets_value",      r"luxury (assets?|items?)\D+(" + NUM + ")"),
        ("bank_asset_value",         r"(bank assets?|bank balance|savings)\D+(" + NUM + ")"),
    ]
    for key, pat in asset_patterns:
        m = re.search(pat, joined)
        if m:
            fields[key] = _num(m.group(2))
            conf[key] = 0.6
            provenance.append({"field": key, "source_doc": docs[0]["filename"] if docs else "", "method": "regex", "snippet": m.group(0)[:120]})

    # requested loan (optional in docs)
    m_amt = re.search(r"(loan amount|requested amount)\D+(" + NUM + ")", joined)
    if m_amt:
        fields["loan_amount"] = _num(m_amt.group(2))
        conf["loan_amount"] = 0.55
        provenance.append({"field": "loan_amount", "source_doc": docs[0]["filename"] if docs else "", "method": "regex", "snippet": m_amt.group(0)[:120]})

    m_term = re.search(r"(loan term|tenure)\D+(\d{1,3})\s*(months?|yrs?|years?)", joined)
    if m_term:
        n = int(m_term.group(2))
        unit = m_term.group(3)
        months = n * (12 if "yr" in unit or "year" in unit else 1)
        fields["loan_term"] = months
        conf["loan_term"] = 0.55
        provenance.append({"field": "loan_term", "source_doc": docs[0]["filename"] if docs else "", "method": "regex", "snippet": m_term.group(0)[:120]})

    return fields, provenance, conf, extras
