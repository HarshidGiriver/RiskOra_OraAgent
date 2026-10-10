"""
RISKORA - Data Quality Engine
Independent data quality assessment engine evaluating field completeness,
boundary validation, contradiction detection, and formatting consistency.
Completely separated from credit default risk calculation.
"""

from typing import Dict, Any, List, Optional
import math
import numpy as np

REQUIRED_FIELDS = [
    'Age', 'Income', 'Loan Amount', 'Credit Score', 'Months Employed',
    'Number of Credit Lines', 'Interest Rate', 'Loan Term', 'DTI Ratio',
    'Education', 'Employment Type', 'Marital Status', 'Has Mortgage',
    'Has Dependents', 'Loan Purpose', 'Has Co-Signer'
]

def assess_data_quality(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates data quality of a single loan record.
    Returns:
    - quality_score: int (0 - 100)
    - available_fields: int
    - total_fields: int
    - warnings: List[str]
    - validation_status: str ("PASS", "ACCEPTABLE_WITH_WARNINGS", "CRITICAL_DEFICIENCIES")
    """
    warnings: List[str] = []
    penalties = 0

    # 1. Field Completeness Check
    total_fields = len(REQUIRED_FIELDS)
    available_fields = 0
    missing_fields = []

    for field in REQUIRED_FIELDS:
        val = record.get(field)
        if val is None or val == "" or (isinstance(val, float) and math.isnan(val)):
            missing_fields.append(field)
        else:
            available_fields += 1

    if missing_fields:
        for f in missing_fields:
            warnings.append(f"Required attribute missing: '{f}'")
            penalties += 12

    # 2. Domain & Boundary Validations
    age = record.get('Age')
    if age is not None and not (isinstance(age, float) and math.isnan(age)):
        try:
            age_val = float(age)
            if age_val < 18 or age_val > 80:
                warnings.append(f"Age {age_val} falls outside standard micro-lending eligibility window (18–80)")
                penalties += 15
        except (ValueError, TypeError):
            warnings.append("Malformed numeric value for 'Age'")
            penalties += 15

    income = record.get('Income')
    if income is not None and not (isinstance(income, float) and math.isnan(income)):
        try:
            inc_val = float(income)
            if inc_val <= 0:
                warnings.append("Stated annual income must be greater than zero")
                penalties += 25
            elif inc_val > 50000000:
                warnings.append(f"Unusually high stated income (₹{inc_val:,.0f}) requires documentary verification")
                penalties += 8
        except (ValueError, TypeError):
            warnings.append("Malformed numeric value for 'Income'")
            penalties += 20

    credit_score = record.get('Credit Score')
    if credit_score is not None and not (isinstance(credit_score, float) and math.isnan(credit_score)):
        try:
            cs_val = float(credit_score)
            if cs_val < 300 or cs_val > 850:
                warnings.append(f"Credit score {cs_val} is outside standard bureau scale (300–850)")
                penalties += 20
        except (ValueError, TypeError):
            warnings.append("Malformed credit bureau score")
            penalties += 20

    dti = record.get('DTI Ratio')
    if dti is not None and not (isinstance(dti, float) and math.isnan(dti)):
        try:
            dti_val = float(dti)
            if dti_val < 0.0 or dti_val > 2.0:
                warnings.append(f"DTI ratio {dti_val:.2f} is outside plausible financial bounds (0.00–2.00)")
                penalties += 15
        except (ValueError, TypeError):
            warnings.append("Malformed DTI ratio")
            penalties += 15

    # 3. Cross-Field Logical Contradiction Detection
    emp_type = record.get('Employment Type')
    months_emp = record.get('Months Employed')
    if emp_type == 'Unemployed' and months_emp is not None and not (isinstance(months_emp, float) and math.isnan(months_emp)):
        try:
            if float(months_emp) > 0:
                warnings.append("Contradiction: Status is 'Unemployed' but 'Months Employed' > 0")
                penalties += 15
        except (ValueError, TypeError):
            pass

    loan_amt = record.get('Loan Amount')
    if loan_amt is not None and income is not None:
        try:
            la_val = float(loan_amt)
            inc_val = float(income)
            if inc_val > 0 and la_val > (inc_val * 3.5):
                warnings.append(f"Severe leverage alert: Loan Amount (₹{la_val:,.0f}) exceeds 350% of annual income (₹{inc_val:,.0f})")
                penalties += 15
        except (ValueError, TypeError):
            pass

    # Calculate final Data Quality Index
    quality_score = max(5, 100 - penalties)

    if quality_score >= 88 and len(missing_fields) == 0:
        status = "PASS"
    elif quality_score >= 65:
        status = "ACCEPTABLE_WITH_WARNINGS"
    else:
        status = "CRITICAL_DEFICIENCIES"

    return {
        "quality_score": quality_score,
        "available_fields": available_fields,
        "total_fields": total_fields,
        "missing_fields": missing_fields,
        "warnings": warnings,
        "validation_status": status
    }
