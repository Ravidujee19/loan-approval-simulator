from agents.applicant_evaluator.app.services.payments import monthly_payment


def test_monthly_payment_zero_rate():
    assert monthly_payment(1200, 0.0, 12) == 100.0


def test_monthly_payment_positive():
    p = monthly_payment(100000, 0.12, 24)
    assert p > 0
