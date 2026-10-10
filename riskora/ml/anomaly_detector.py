"""
RISKORA - Anomaly and Suspicious Profile Detection Engine
Identifies unusual financial combinations, multivariate outliers, and profile inconsistencies.
Provides objective decision-support signals ("Enhanced verification recommended")
without making unproven fraud accusations.
"""

from typing import Dict, Any, List

def detect_anomalies(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates borrower record for multivariate anomalies and unusual patterns.
    Returns:
    - anomaly_detected: bool
    - anomaly_score: float (0.0 to 1.0)
    - anomaly_flags: List[str]
    - recommended_review_intensity: str ('Standard', 'Enhanced Verification', 'Credit Committee Review')
    """
    flags: List[str] = []
    severity_points = 0.0

    try:
        age = float(record.get('Age', 35))
        income = float(record.get('Income', 300000))
        loan_amount = float(record.get('Loan Amount', 50000))
        credit_score = float(record.get('Credit Score', 650))
        months_employed = float(record.get('Months Employed', 24) or 0)
        dti = float(record.get('DTI Ratio', 0.35) or 0.35)
        num_credit_lines = float(record.get('Number of Credit Lines', 4) or 4)
    except (ValueError, TypeError):
        return {
            "anomaly_detected": True,
            "anomaly_score": 0.85,
            "anomaly_flags": ["Malformed profile data preventing standard verification"],
            "recommended_review_intensity": "Enhanced Verification"
        }

    # 1. Age vs Employment Tenure Physics Check
    max_legal_working_months = max(0, (age - 18) * 12)
    if months_employed > max_legal_working_months and age < 60:
        flags.append(f"Employment tenure ({months_employed:.0f} mos) exceeds feasible working years since age 18 ({max_legal_working_months:.0f} mos)")
        severity_points += 0.40

    # 2. Extreme Leverage / Income Anomaly
    if income > 0:
        leverage_ratio = loan_amount / income
        if leverage_ratio > 2.5:
            flags.append(f"Unusually high debt leverage ratio ({leverage_ratio:.1f}x annual income)")
            severity_points += 0.35

    # 3. Credit Line Disconnect
    if credit_score > 780 and num_credit_lines <= 1:
        flags.append("Thin-file anomaly: Prime credit score (>780) with only 1 credit trade line")
        severity_points += 0.25

    # 4. Severe DTI combined with low credit score
    if dti > 0.70 and credit_score < 560:
        flags.append(f"Compounded distress pattern: Critical DTI ({dti:.1%}) combined with subprime credit score ({credit_score:.0f})")
        severity_points += 0.30

    # 5. Income vs Stated Education Contradiction Outlier
    education = record.get('Education', '')
    if education == 'High School' and income > 2500000:
        flags.append(f"Upper-decile income outlier for demographic segment (₹{income:,.0f})")
        severity_points += 0.15

    # 6. Ultra-short tenure with high loan amount
    if months_employed <= 3 and loan_amount > 200000:
        flags.append(f"High ticket loan (₹{loan_amount:,.0f}) requested with new job tenure (<3 months)")
        severity_points += 0.25

    anomaly_score = min(1.0, round(severity_points, 2))
    anomaly_detected = len(flags) > 0 or anomaly_score >= 0.30

    if anomaly_score >= 0.60:
        review_intensity = "Credit Committee Review"
    elif anomaly_score >= 0.25:
        review_intensity = "Enhanced Verification"
    else:
        review_intensity = "Standard"

    return {
        "anomaly_detected": anomaly_detected,
        "anomaly_score": anomaly_score,
        "anomaly_flags": flags,
        "recommended_review_intensity": review_intensity
    }
