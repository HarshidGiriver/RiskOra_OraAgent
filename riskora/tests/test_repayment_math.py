"""
Unit tests for RISKORA Repayment Amortization and Allocation Engine
Verifies mathematical precision of amortization schedules, final zero-balance settlement,
and exact penny reconciliation across Pro-Rata, LCF, and EFF waterfalls.
"""

import pytest
from riskora.backend.database import init_db
from riskora.backend.services.repayment_service import (
    generate_repayment_schedule, execute_repayment
)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_amortization_schedule_zero_balance_reconciliation():
    # Test on seeded Loan 1 (LN-2026-001, 80,000 INR, 12 months, 14.5% APR)
    schedule = generate_repayment_schedule(1, frequency="MONTHLY")
    assert len(schedule) == 12

    # Verify each payment has positive principal and interest
    for item in schedule:
        assert item["scheduled_principal"] > 0
        assert item["scheduled_interest"] > 0
        assert round(item["scheduled_principal"] + item["scheduled_interest"], 2) == item["scheduled_total"]

    # Verify final payment reaches exactly 0.00 remaining balance
    final_item = schedule[-1]
    assert final_item["remaining_balance"] == 0.0, f"Remaining balance {final_item['remaining_balance']} != 0.00"

    # Verify sum of principal payments equals original principal (80,000 INR)
    total_principal_paid = sum(item["scheduled_principal"] for item in schedule)
    assert round(total_principal_paid, 2) == 80000.0, f"Total principal {total_principal_paid} != 80,000.00"

def test_repayment_allocation_waterfalls_zero_penny_leak():
    # Test on Loan 4 (LN-2026-004, multi-lender syndicate with 3 participants)
    test_payment = 12500.50

    # 1. Pro-Rata Policy
    res_pr = execute_repayment(4, test_payment, allocation_policy="PRO_RATA")
    sum_pr = sum(a["total_payout"] for a in res_pr["allocations"])
    assert round(sum_pr, 2) == test_payment, f"Pro-Rata payout sum {sum_pr} != {test_payment}"

    # 2. Largest Contribution First (LCF) Policy
    res_lcf = execute_repayment(4, test_payment, allocation_policy="LARGEST_CONTRIBUTION_FIRST")
    sum_lcf = sum(a["total_payout"] for a in res_lcf["allocations"])
    assert round(sum_lcf, 2) == test_payment, f"LCF payout sum {sum_lcf} != {test_payment}"

    # 3. Earliest Funding First (EFF) Policy
    res_eff = execute_repayment(4, test_payment, allocation_policy="EARLIEST_FUNDING_FIRST")
    sum_eff = sum(a["total_payout"] for a in res_eff["allocations"])
    assert round(sum_eff, 2) == test_payment, f"EFF payout sum {sum_eff} != {test_payment}"
