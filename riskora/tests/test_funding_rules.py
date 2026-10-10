"""
Unit tests for RISKORA Funding & Syndicate Management rules
Verifies commitment constraints, over-funding prevention, balance checks,
and Herfindahl-Hirschman concentration indexing.
"""

import pytest
from riskora.backend.database import reset_db
from riskora.backend.services.funding_service import pledge_funding, get_syndicate_summary

@pytest.fixture(autouse=True)
def setup_db():
    reset_db()

def test_funding_pledge_and_overfunding_prevention():
    # Loan 2 (LN-2026-002, 60k requested, 35k already funded -> 25k remaining)
    summary = get_syndicate_summary(2)
    assert summary["remaining_amount"] == 25000.0

    # Test excessive pledge over remaining amount
    with pytest.raises(ValueError, match="exceeds remaining"):
        pledge_funding(loan_id=2, lender_id=1, contribution_amount=30000.0)

    # Test valid pledge of 10,000 INR
    res = pledge_funding(loan_id=2, lender_id=2, contribution_amount=10000.0)
    assert res["funded_amount"] == 45000.0
    assert res["remaining_amount"] == 15000.0
    assert res["funding_status"] == "FUNDING"

    # Complete the syndicate by pledging final 15,000 INR
    res_final = pledge_funding(loan_id=2, lender_id=2, contribution_amount=15000.0)
    assert res_final["funded_amount"] == 60000.0
    assert res_final["remaining_amount"] == 0.0
    assert res_final["funding_status"] == "FULLY_FUNDED"

def test_syndicate_concentration_hhi():
    summary = get_syndicate_summary(4)
    # Loan 4 has 3 participants (50%, 33.3%, 16.7%)
    conc = summary["concentration_metrics"]
    assert "hhi_index" in conc
    assert 0.0 < conc["hhi_index"] < 1.0
    assert "risk_distinction_notice" in conc
