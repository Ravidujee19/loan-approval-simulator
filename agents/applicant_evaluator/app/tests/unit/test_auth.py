from agents.applicant_evaluator.app.core.security import create_access_token, decode_token


def test_jwt_roundtrip():
    t = create_access_token("user-id", "applicant", 1)
    payload = decode_token(t)
    assert payload["sub"] == "user-id"
    assert payload["role"] == "applicant"
