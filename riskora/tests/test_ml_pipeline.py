"""
Unit tests for RISKORA Machine Learning & Risk Intelligence Core
Verifies probability bounds, risk score calibration, local explainability drivers,
data quality scoring, and anomaly detection.
"""

import pytest
from riskora.ml.inference_engine import get_engine
from riskora.ml.data_quality import assess_data_quality
from riskora.ml.anomaly_detector import detect_anomalies

def test_inference_engine_prediction_bounds():
    engine = get_engine()
    sample = {
        'Age': 35,
        'Income': 450000,
        'Loan Amount': 60000,
        'Credit Score': 680,
        'Months Employed': 36,
        'Number of Credit Lines': 5,
        'Interest Rate': 16.5,
        'Loan Term': 12,
        'DTI Ratio': 0.28,
        'Education': 'Bachelor',
        'Employment Type': 'Salaried',
        'Marital Status': 'Married',
        'Has Mortgage': 1,
        'Has Dependents': 1,
        'Loan Purpose': 'Business Expansion',
        'Has Co-Signer': 0
    }
    result = engine.analyze_loan(sample)

    assert "probability_of_default" in result
    pd = result["probability_of_default"]
    assert 0.0 < pd < 1.0, f"PD {pd} out of valid probability bounds"

    assert "risk_score" in result
    score = result["risk_score"]
    assert 0 <= score <= 100, f"Risk score {score} out of 0-100 range"

    assert result["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
    assert len(result["risk_drivers"]) > 0

def test_data_quality_engine_penalties():
    # Complete clean record
    clean_record = {
        'Age': 30, 'Income': 300000, 'Loan Amount': 40000, 'Credit Score': 650,
        'Months Employed': 24, 'Number of Credit Lines': 4, 'Interest Rate': 18.0,
        'Loan Term': 12, 'DTI Ratio': 0.32, 'Education': 'Bachelor',
        'Employment Type': 'Salaried', 'Marital Status': 'Single',
        'Has Mortgage': 0, 'Has Dependents': 0, 'Loan Purpose': 'Working Capital',
        'Has Co-Signer': 0
    }
    clean_res = assess_data_quality(clean_record)
    assert clean_res["quality_score"] == 100
    assert clean_res["validation_status"] == "PASS"

    # Deficient record with missing and contradictory values
    bad_record = {
        'Age': 12, # impossible under 18
        'Income': 0, # invalid zero income
        'Employment Type': 'Unemployed',
        'Months Employed': 48 # contradiction
    }
    bad_res = assess_data_quality(bad_record)
    assert bad_res["quality_score"] < 60
    assert len(bad_res["warnings"]) >= 3
    assert bad_res["validation_status"] == "CRITICAL_DEFICIENCIES"

def test_anomaly_detection():
    # Normal borrower
    normal_record = {'Age': 40, 'Income': 500000, 'Loan Amount': 50000, 'Credit Score': 700, 'Months Employed': 48}
    norm_res = detect_anomalies(normal_record)
    assert not norm_res["anomaly_detected"]
    assert norm_res["recommended_review_intensity"] == "Standard"

    # Suspicious profile: Age 20 with 120 months (10 years) employment tenure
    suspicious_record = {'Age': 20, 'Income': 300000, 'Loan Amount': 50000, 'Credit Score': 600, 'Months Employed': 120}
    sus_res = detect_anomalies(suspicious_record)
    assert sus_res["anomaly_detected"]
    assert len(sus_res["anomaly_flags"]) > 0
    assert sus_res["recommended_review_intensity"] in ["Enhanced Verification", "Credit Committee Review"]
