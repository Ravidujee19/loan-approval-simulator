# amortization & debt ratio helpers

def monthly_payment(principal: float, annual_rate: float, months: int) -> float:
    if months <= 0:
        raise ValueError("months_must_be_positive")
    r = annual_rate / 12.0
    if r == 0:
        return round(principal / months, 2)
    num = principal * (r * (1 + r) ** months)
    den = (1 + r) ** months - 1
    return round(num / den, 2)
