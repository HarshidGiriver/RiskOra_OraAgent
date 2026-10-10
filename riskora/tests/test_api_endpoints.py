"""
Integration tests for RISKORA REST API Endpoints
Verifies health, catalog querying, ML inference execution, simulation,
and ReportLab PDF streaming.
"""

import pytest
from starlette.testclient import TestClient
from riskora.backend.main import app
from riskora.backend.database import init_db

@pytest.fixture(scope="module")
def client():
    init_db()
    with TestClient(app) as c:
        yield c

def test_api_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HEALTHY"
    assert "active_model" in data

def test_list_loans_and_filtering(client):
    res = client.get("/api/loans")
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert len(data["loans"]) > 0

    # Test search query
    res_search = client.get("/api/loans?search=Jaipur")
    assert res_search.status_code == 200
    assert len(res_search.json()["loans"]) >= 1

def test_real_ml_analysis_endpoint(client):
    # Analyze Loan 1 (LN-2026-001)
    res = client.post("/api/risk/analyze/1")
    assert res.status_code == 200
    data = res.json()
    assert "probability_of_default" in data
    assert "risk_score" in data
    assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
    assert len(data["risk_drivers"]) > 0
    assert data["data_quality"]["quality_score"] > 0

def test_what_if_simulation_endpoint(client):
    payload = {
        "loan_id": 1,
        "credit_score": 750,
        "annual_income": 800000.0,
        "loan_amount": 50000.0,
        "dti_ratio": 0.20,
        "loan_term": 12,
        "months_employed": 60,
        "has_cosigner": 1
    }
    res = client.post("/api/simulation", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "baseline" in data
    assert "scenario" in data
    assert "pd_delta_pct_points" in data

def test_pdf_report_download(client):
    res = client.get("/api/reports/1/pdf")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert len(res.content) > 1000 # Valid binary PDF

def test_borrower_application_zero_trust(client):
    payload = {
        "full_name": "Deepak Verma",
        "phone": "9876543210",
        "city": "Lucknow",
        "annual_income": 480000.0,
        "loan_amount": 65000.0,
        "loan_term": 12,
        "interest_rate": 14.0,
        "loan_purpose": "Retail Inventory",
        "unbanked_reason": "Lack of registered commercial collateral",
        "has_cosigner": 0,
        "enach_mandate_consent": True,
        "terms_agreed": True
    }
    res = client.post("/api/borrowers/apply", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "loan_id" in data
    assert data["status"] == "APPLIED"

def test_ora_analysis_engine_and_certificates(client):
    res = client.post("/api/risk/ora-analyze/1")
    assert res.status_code == 200
    data = res.json()
    assert 300 <= data["ora_score"] <= 900
    assert data["risk_grade"] in ["LOW", "MEDIUM", "HIGH"]
    assert len(data["vector_analysis"]) == 4
    assert len(data["evidence_foundation"]) >= 3
    assert "VERDICT" in data["verdict"]
    assert len(data["cryptographic_hash"]) == 64

    # Test PDF certificate export
    res_cert = client.get("/api/reports/1/ora-certificate")
    assert res_cert.status_code == 200
    assert res_cert.headers["content-type"] == "application/pdf"
    assert len(res_cert.content) > 1000

    # Test performance report export
    res_perf = client.get("/api/reports/1/performance")
    assert res_perf.status_code == 200
    assert res_perf.headers["content-type"] == "application/pdf"
    assert len(res_perf.content) > 1000

def test_single_lender_negotiation_hall_flow(client):
    # Initialize negotiation
    res_get = client.get("/api/negotiations/1")
    assert res_get.status_code == 200
    neg = res_get.json()
    assert neg["loan_id"] == 1
    assert "current_emi" in neg

    # Post counter-offer
    offer_payload = {
        "loan_id": 1,
        "lender_id": 1,
        "proposed_principal": 50000.0,
        "proposed_rate": 13.5,
        "proposed_term": 10,
        "sender_role": "lender",
        "sender_name": "Apex Credit Partners",
        "message": "Counter-offer with competitive 13.5% annual rate."
    }
    res_offer = client.post("/api/negotiations/offer", json=offer_payload)
    assert res_offer.status_code == 200
    offer_data = res_offer.json()
    assert offer_data["current_interest_rate"] == 13.5

    # Accept & lock terms
    res_lock = client.post("/api/negotiations/accept/1")
    assert res_lock.status_code == 200
    assert res_lock.json()["status"] == "ACCEPTED_AND_LOCKED"

def test_mock_lender_creator(client):
    payload = {
        "name": "Kavita Sharma - Angel Pool",
        "capital_pool": 250000.0,
        "institution_type": "Private Individual",
        "risk_tolerance": "BALANCED"
    }
    res = client.post("/api/lenders/mock", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Kavita Sharma - Angel Pool"
    assert data["total_committed"] == 250000.0

def test_final_review_document_pdf_download(client):
    res = client.get("/api/reports/final-review-pdf")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert len(res.content) > 10000


