from types import SimpleNamespace

from agents.applicant_evaluator.app.services.evaluator import clamp


def test_clamp():
    assert clamp(120, 0, 100) == 100
    assert clamp(-1, 0, 100) == 0
    assert clamp(50, 0, 100) == 50
