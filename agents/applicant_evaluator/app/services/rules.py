def check(fields: dict):
    warnings, hard_stops = [], []

    # CIBIL must be 300–900
    cibil = fields.get("cibil_score")
    if cibil is not None:
        try:
            cibil = int(cibil)
            if not (300 <= cibil <= 900):
                hard_stops.append("cibil_score_out_of_range")
        except Exception:
            warnings.append("cibil_score_unparsable")

    # Loan Amount sanity vs Income (simple heuristic)
    try:
        income = float(fields.get("income_annum", 0))
        loan_amt = float(fields.get("loan_amount", 0))
        if income > 0 and loan_amt > income * 5:
            warnings.append("loan_amount_gt_5x_income")
    except Exception:
        pass

    # Loan term reasonable
    try:
        term = int(fields.get("loan_term", 0))
        if term <= 0 or term > 480:
            warnings.append("loan_term_unusual")
    except Exception:
        pass

    return warnings, hard_stops
