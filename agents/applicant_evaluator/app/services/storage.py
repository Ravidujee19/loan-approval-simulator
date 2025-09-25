import os, io, uuid, json
from typing import Tuple, Dict, List
from ..config import settings

def _root(applicant_id: str) -> str:
    return os.path.join(settings().STORAGE_DIR, applicant_id)

def ensure_bucket(applicant_id: str):
    os.makedirs(os.path.join(_root(applicant_id), "docs"), exist_ok=True)
    os.makedirs(os.path.join(_root(applicant_id), "profiles"), exist_ok=True)

def save_upload(applicant_id: str, filename: str, fileobj: io.BufferedReader) -> Tuple[str, str]:
    ensure_bucket(applicant_id)
    doc_id = str(uuid.uuid4())
    path = os.path.join(_root(applicant_id), "docs", f"{doc_id}__{filename}")
    with open(path, "wb") as f:
        f.write(fileobj.read())
    return doc_id, path

def list_docs(applicant_id: str) -> List[Dict]:
    ensure_bucket(applicant_id)
    p = os.path.join(_root(applicant_id), "docs")
    if not os.path.exists(p):
        return []
    items = []
    for fn in os.listdir(p):
        full = os.path.join(p, fn)
        if os.path.isfile(full):
            items.append({"doc_id": fn.split("__")[0], "filename": fn.split("__",1)[1], "path": full})
    return items

def read_text(path: str) -> str:
    # read as text; for binary/PDF, return empty / OCR later
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""

def save_profile(applicant_id: str, loan_id: str, payload: dict):
    ensure_bucket(applicant_id)
    path = os.path.join(_root(applicant_id), "profiles", f"{loan_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

def load_profile(applicant_id: str, loan_id: str):
    path = os.path.join(_root(applicant_id), "profiles", f"{loan_id}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
