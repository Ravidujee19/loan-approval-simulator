# Main extractor: uses Ollama (llama3) for structured extraction
# fallback to local regex + spaCy methods

import os
import re
import json
import logging
from typing import Tuple, Dict, List
import requests
import spacy

from .nlp import extract_from_texts
# from .extractor_fallback import extract_applicant_details as legacy_extract_applicant_details

# Load spaCy (used for fallback only)
try:
    nlp = spacy.load("en_core_web_sm")
except Exception:
    nlp = None

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Ollama configuration 
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "8.0"))

# Helper function
def _extract_json_from_text(text: str) -> dict:
    """Extract the first JSON object substring from text."""
    try:
        match = re.search(r"(\{(?:[^{}]|(?R))*\})", text, flags=re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
            start = text.index("{")
            end = text.rindex("}")
            json_str = text[start:end + 1]
        return json.loads(json_str)
    except Exception as e:
        raise ValueError(f"Failed to parse JSON from model output: {e}")


def _build_prompt(text: str) -> str:
    """Prompt for LLM extraction."""
    return f"""
You are an intelligent information extraction assistant.
Given the following applicant description, extract structured loan-related details.

Return ONLY a valid JSON object with the following keys:
- "fields": object with extracted structured data (income_annum, loan_amount, loan_term, cibil_score, no_of_dependents, education, self_employed, etc.)
- "provenance": list of short notes for each field
- "conf": confidence scores (0.0–1.0)
- "extras": additional details like name, age, notes.

Applicant text:
\"\"\"{text}\"\"\"

Output only valid JSON, no extra text or explanations.
"""


def extract_with_ollama(text: str) -> Tuple[Dict, List[Dict], Dict[str, float], Dict]:
    """Extract applicant details using Ollama llama3 model."""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": _build_prompt(text),
        "stream": False,
        "temperature": 0.0,
    }

    logger.info(f"Using Ollama model: {OLLAMA_MODEL}")

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=OLLAMA_TIMEOUT,
        )
        response.raise_for_status()
    except Exception as e:
        raise RuntimeError(f"Ollama request failed: {e}")

    # Ollama returns text in 'response.text'
    output_text = response.text.strip()
    parsed = _extract_json_from_text(output_text)

    fields = parsed.get("fields", {}) or {}
    provenance = parsed.get("provenance", []) or []
    conf = parsed.get("conf", {}) or {}
    extras = parsed.get("extras", {}) or {}

    return fields, provenance, conf, extras


def extract_applicant_details_primary(text: str, docs: List[Dict] = None) -> Tuple[Dict, List[Dict], Dict[str, float], Dict]:
    """Main method — LLM first, fallback to regex/spaCy extractors."""
    docs = docs or [{"filename": "text"}]

    # Try LLM path
    try:
        fields, provenance, conf, extras = extract_with_ollama(text)
        for p in provenance:
            if "source_doc" not in p:
                p["source_doc"] = docs[0].get("filename", "text")
        logger.info("Ollama extraction succeeded.")
        return fields, provenance, conf, extras
    except Exception as e:
        logger.warning(f"Ollama extraction failed: {e}. Using fallback methods.")

    # Fallback path
    try:
        legacy = (text)
    except Exception as e:
        legacy = {}
        logger.exception(f"Legacy extractor failed: {e}")

    try:
        fields2, provenance2, conf2, extras2 = extract_from_texts(docs, [text])
    except Exception as e:
        fields2, provenance2, conf2, extras2 = legacy, [], {}, {}
        logger.exception(f"Regex extractor failed: {e}")

    # Merge fallback outputs
    merged_fields = {**legacy, **fields2}
    merged_conf = conf2 or {}
    merged_provenance = provenance2 or []
    merged_extras = extras2 or {}

    logger.info(f"Fallback extraction complete with fields: {list(merged_fields.keys())}")
    return merged_fields, merged_provenance, merged_conf, merged_extras


def extract_applicant_details(text: str) -> dict:
    """Backward-compatible wrapper for quick field-only extraction."""
    fields, _, _, _ = extract_applicant_details_primary(text)
    return fields