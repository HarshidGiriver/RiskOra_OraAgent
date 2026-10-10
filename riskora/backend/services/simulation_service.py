"""
RISKORA - What-If Risk Simulation Service
Enables lenders and credit officers to dynamically simulate counterfactual scenarios
by tweaking borrower attributes (Credit Score, Income, DTI, Loan Amount, Loan Term, Co-Signer).
Computes exact calibrated delta and marginal sensitivity analysis.
"""

from typing import Dict, Any, List, Optional
from riskora.ml.inference_engine import get_engine
from riskora.backend.services.loan_service import get_loan_by_id

SIMULATION_DISCLAIMER = (
    "NOTICE: What-If simulation results represent hypothetical econometric stress-testing "
    "under the current calibrated ML model. These results do not guarantee credit approval "
    "nor do they constitute a legally binding contractual quote."
)

def simulate_scenario(
    loan_id: Optional[int],
    credit_score: int,
    annual_income: float,
    loan_amount: float,
    dti_ratio: float,
    loan_term: int,
    months_employed: int = 24,
    has_cosigner: int = 0
) -> Dict[str, Any]:
    """
    Simulates changes against an existing loan baseline or an arbitrary new hypothetical scenario.
    """
    engine = get_engine()

    # 1. Determine Baseline
    baseline_record = {
        'Age': 35,
        'Income': 300000,
        'Loan Amount': 50000,
        'Credit Score': 640,
        'Months Employed': 24,
        'Number of Credit Lines': 4,
        'Interest Rate': 18.0,
        'Loan Term': 12,
        'DTI Ratio': 0.35,
        'Education': 'Bachelor',
        'Employment Type': 'Salaried',
        'Marital Status': 'Married',
        'Has Mortgage': 0,
        'Has Dependents': 0,
        'Loan Purpose': 'Working Capital',
        'Has Co-Signer': 0
    }

    if loan_id:
        existing = get_loan_by_id(loan_id)
        if existing:
            b = existing['borrower']
            baseline_record = {
                'Age': b['age'],
                'Income': b['annual_income'],
                'Loan Amount': existing['loan_amount'],
                'Credit Score': b['credit_score'],
                'Months Employed': b['months_employed'],
                'Number of Credit Lines': b['num_credit_lines'],
                'Interest Rate': existing['interest_rate'],
                'Loan Term': existing['loan_term'],
                'DTI Ratio': existing['dti_ratio'],
                'Education': b['education'],
                'Employment Type': b['employment_type'],
                'Marital Status': b['marital_status'],
                'Has Mortgage': b['has_mortgage'],
                'Has Dependents': b['has_dependents'],
                'Loan Purpose': existing['loan_purpose'],
                'Has Co-Signer': existing['has_cosigner']
            }

    base_analysis = engine.analyze_loan(baseline_record)
    base_pd = base_analysis['probability_of_default']
    base_score = base_analysis['risk_score']
    base_level = base_analysis['risk_level']

    # 2. Formulate Perturbed Scenario
    scenario_record = baseline_record.copy()
    scenario_record.update({
        'Credit Score': credit_score,
        'Income': annual_income,
        'Loan Amount': loan_amount,
        'DTI Ratio': dti_ratio,
        'Loan Term': loan_term,
        'Months Employed': months_employed,
        'Has Co-Signer': has_cosigner
    })

    scenario_analysis = engine.analyze_loan(scenario_record)
    scen_pd = scenario_analysis['probability_of_default']
    scen_score = scenario_analysis['risk_score']
    scen_level = scenario_analysis['risk_level']

    # 3. Calculate Deltas
    pd_delta_pts = round((scen_pd - base_pd) * 100.0, 2)
    score_delta = scen_score - base_score

    # 4. Generate Sensitivity Analysis
    sensitivities = []
    # Test +50 Credit Score bump
    cs_bump = scenario_record.copy()
    cs_bump['Credit Score'] = min(850, credit_score + 50)
    cs_pd = engine.analyze_loan(cs_bump)['probability_of_default']
    sensitivities.append({
        "lever": "Improve Credit Bureau Score (+50 pts)",
        "projected_pd": round(cs_pd * 100, 2),
        "impact_pct_points": round((cs_pd - scen_pd) * 100, 2)
    })

    # Test adding a Co-Signer
    if not has_cosigner:
        cosign_bump = scenario_record.copy()
        cosign_bump['Has Co-Signer'] = 1
        cosign_pd = engine.analyze_loan(cosign_bump)['probability_of_default']
        sensitivities.append({
            "lever": "Attach Creditworthy Co-Signer Guarantee",
            "projected_pd": round(cosign_pd * 100, 2),
            "impact_pct_points": round((cosign_pd - scen_pd) * 100, 2)
        })

    # Test reducing DTI by 10%
    dti_bump = scenario_record.copy()
    dti_bump['DTI Ratio'] = max(0.10, dti_ratio - 0.10)
    dti_pd = engine.analyze_loan(dti_bump)['probability_of_default']
    sensitivities.append({
        "lever": "Deleverage Debt Burden (-10% DTI)",
        "projected_pd": round(dti_pd * 100, 2),
        "impact_pct_points": round((dti_pd - scen_pd) * 100, 2)
    })

    return {
        "baseline": {
            "probability_of_default": round(base_pd, 4),
            "probability_pct": round(base_pd * 100.0, 2),
            "risk_score": base_score,
            "risk_level": base_level
        },
        "scenario": {
            "probability_of_default": round(scen_pd, 4),
            "probability_pct": round(scen_pd * 100.0, 2),
            "risk_score": scen_score,
            "risk_level": scen_level
        },
        "pd_delta_pct_points": pd_delta_pts,
        "score_delta": score_delta,
        "key_sensitivities": sensitivities,
        "disclaimer": SIMULATION_DISCLAIMER
    }
