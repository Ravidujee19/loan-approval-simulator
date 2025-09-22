# /api/v1 helper

from agents.applicant_evaluator.app.core.config import settings


def api_prefix() -> str:
    return f"/api/{settings().API_VERSION}"
