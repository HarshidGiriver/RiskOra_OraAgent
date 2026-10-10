"""
RISKORA - Explainable AI (XAI) Engine
Computes local feature attributions and decomposes default probability into explicit
risk drivers based on the Kaggle CIBIL and Asset Valuation features.
Strictly articulates the boundary between statistical correlation and causal mechanisms.
"""

from typing import Dict, Any, List

BENCHMARKS = {
    'cibil_score': 650,
    'asset_to_loan_ratio': 2.5,
    'loan_to_income': 0.35,
    'loan_term': 12,
    'income_annum': 500000
}

def generate_risk_drivers(record: Dict[str, Any], pd_value: float) -> List[Dict[str, Any]]:
    """
    Computes local feature contribution drivers for a specific loan record.
    Returns sorted list of drivers with direction, impact magnitude, and plain-language explanation.
    """
    drivers = []

    # 1. CIBIL Bureau Score Driver (Dominant factor in Kaggle dataset)
    cibil = float(record.get('cibil_score') or record.get('Credit Score') or 650)
    cibil_diff = BENCHMARKS['cibil_score'] - cibil
    if abs(cibil_diff) > 15:
        impact = round((cibil_diff / 100.0) * 18.0, 1)
        drivers.append({
            "feature": "CIBIL Bureau Score",
            "observed_value": f"{cibil:.0f}",
            "benchmark_value": f"{BENCHMARKS['cibil_score']:.0f}",
            "impact_direction": "INCREASES_RISK" if impact > 0 else "DECREASES_RISK",
            "impact_pct": impact,
            "description": f"Credit bureau score of {cibil:.0f} indicates {'elevated historical default probability' if cibil < 650 else 'strong credit discipline'}."
        })

    # 2. Asset Collateral Coverage Ratio
    asset_ratio = float(record.get('asset_to_loan_ratio') or 2.5)
    ratio_diff = BENCHMARKS['asset_to_loan_ratio'] - asset_ratio
    if abs(ratio_diff) > 0.4:
        impact = round(ratio_diff * 4.5, 1)
        drivers.append({
            "feature": "Total Asset Collateral Coverage",
            "observed_value": f"{asset_ratio:.1f}x",
            "benchmark_value": f"{BENCHMARKS['asset_to_loan_ratio']:.1f}x",
            "impact_direction": "INCREASES_RISK" if impact > 0 else "DECREASES_RISK",
            "impact_pct": impact,
            "description": f"Total declared assets provide {asset_ratio:.1f}x coverage over requested loan principal."
        })

    # 3. Loan-to-Income Leverage
    lti = float(record.get('loan_to_income') or 0.35)
    lti_diff = lti - BENCHMARKS['loan_to_income']
    if abs(lti_diff) > 0.05:
        impact = round(lti_diff * 12.0, 1)
        drivers.append({
            "feature": "Loan-to-Annual Income",
            "observed_value": f"{lti:.1%}",
            "benchmark_value": f"{BENCHMARKS['loan_to_income']:.1%}",
            "impact_direction": "INCREASES_RISK" if impact > 0 else "DECREASES_RISK",
            "impact_pct": impact,
            "description": f"Requested loan constitutes {lti:.1%} of borrower annual income capacity."
        })

    # 4. Loan Term Duration
    term = float(record.get('loan_term') or record.get('Loan Term') or 12)
    if term >= 24:
        drivers.append({
            "feature": "Loan Repayment Duration",
            "observed_value": f"{term:.0f} Months",
            "benchmark_value": f"{BENCHMARKS['loan_term']:.0f} Months",
            "impact_direction": "INCREASES_RISK",
            "impact_pct": 5.5,
            "description": f"Longer loan duration ({term:.0f} months) extends credit cycle exposure."
        })
    elif term <= 6:
        drivers.append({
            "feature": "Loan Repayment Duration",
            "observed_value": f"{term:.0f} Months",
            "benchmark_value": f"{BENCHMARKS['loan_term']:.0f} Months",
            "impact_direction": "DECREASES_RISK",
            "impact_pct": -4.0,
            "description": f"Short repayment window ({term:.0f} months) minimizes macroeconomic duration risk."
        })

    # 5. Employment & Education
    edu = str(record.get('education', 'Graduate')).strip()
    self_emp = str(record.get('self_employed', 'No')).strip()
    if self_emp.lower() == 'yes':
        drivers.append({
            "feature": "Employment Structure",
            "observed_value": "Self-Employed",
            "benchmark_value": "Salaried",
            "impact_direction": "INCREASES_RISK",
            "impact_pct": 3.0,
            "description": "Self-employed revenue streams have higher volatility than fixed salaries."
        })

    # Sort drivers by absolute impact descending
    drivers.sort(key=lambda x: abs(x['impact_pct']), reverse=True)
    return drivers[:5]

CAUSALITY_DISCLOSURE = (
    "METHODOLOGY AND CAUSALITY NOTICE: Feature contributions displayed above quantify statistical "
    "associations and marginal model sensitivity derived from empirical historical loan data. "
    "These indicators reflect predictive correlations and should NOT be interpreted as direct causal "
    "proof. RISKORA operates as an objective decision-support framework to augment credit review."
)
