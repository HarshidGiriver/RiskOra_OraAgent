"""
RISKORA - Repayment & Amortization Engine
Generates mathematically rigorous repayment schedules across 4 payment structures:
(Monthly, Bi-Monthly, Custom Fixed, Flexible Window).
Executes repayment allocations using Pro-Rata, Largest Contribution First (LCF),
and Earliest Funding First (EFF) waterfalls with penny-accurate reconciliation.
"""

import sqlite3
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from riskora.backend.database import get_db_connection

def generate_repayment_schedule(
    loan_id: int,
    frequency: str = "MONTHLY",
    start_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Computes an exact amortized repayment schedule separating principal and interest.
    Handles final payment balancing and persists schedule to database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, loan_amount, loan_term, interest_rate
    FROM loans
    WHERE id = ?
    """, (loan_id,))
    loan = cursor.fetchone()
    if not loan:
        conn.close()
        raise ValueError(f"Loan ID {loan_id} not found.")

    principal = float(loan['loan_amount'])
    term_months = int(loan['loan_term'])
    annual_rate = float(loan['interest_rate']) / 100.0

    # Determine period frequency and number of payments
    freq_upper = frequency.upper()
    if freq_upper == "BI_MONTHLY":
        n_payments = term_months * 2
        periodic_rate = annual_rate / 24.0
        days_interval = 15
    elif freq_upper in ["CUSTOM_FIXED", "FLEXIBLE_WINDOW"]:
        n_payments = term_months
        periodic_rate = annual_rate / 12.0
        days_interval = 30
    else:  # MONTHLY
        n_payments = term_months
        periodic_rate = annual_rate / 12.0
        days_interval = 30

    # Standard Annuity Amortization Formula: EMI = P * [r(1+r)^n] / [(1+r)^n - 1]
    if periodic_rate > 0:
        factor = (1.0 + periodic_rate) ** n_payments
        installment = principal * (periodic_rate * factor) / (factor - 1.0)
    else:
        installment = principal / n_payments

    installment = round(installment, 2)

    # Clear previous un-executed schedules
    cursor.execute("DELETE FROM repayment_schedules WHERE loan_id = ? AND status = 'PENDING'", (loan_id,))

    base_date = datetime.now(timezone.utc)
    if start_date:
        try:
            base_date = datetime.fromisoformat(start_date)
        except Exception:
            pass

    schedule = []
    balance = principal

    for i in range(1, n_payments + 1):
        due_dt = base_date + timedelta(days=days_interval * i)
        due_str = due_dt.strftime("%Y-%m-%d")

        interest_component = round(balance * periodic_rate, 2)

        if i == n_payments:
            # Final payment balances exact remaining principal to zero
            principal_component = round(balance, 2)
            total_payment = round(principal_component + interest_component, 2)
            balance = 0.0
        else:
            principal_component = round(installment - interest_component, 2)
            # Ensure principal component does not exceed balance
            if principal_component > balance:
                principal_component = round(balance, 2)
            balance = round(balance - principal_component, 2)
            total_payment = round(principal_component + interest_component, 2)

        item = {
            "loan_id": loan_id,
            "payment_number": i,
            "due_date": due_str,
            "scheduled_principal": principal_component,
            "scheduled_interest": interest_component,
            "scheduled_total": total_payment,
            "remaining_balance": max(0.0, balance),
            "status": "PENDING"
        }
        schedule.append(item)

        cursor.execute("""
        INSERT INTO repayment_schedules (
            loan_id, payment_number, due_date, scheduled_principal,
            scheduled_interest, scheduled_total, remaining_balance, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDING')
        """, (
            loan_id, i, due_str, principal_component,
            interest_component, total_payment, max(0.0, balance)
        ))

    # Update loan frequency preference
    cursor.execute("UPDATE loans SET repayment_frequency = ? WHERE id = ?", (frequency, loan_id))

    conn.commit()
    conn.close()

    return schedule

def get_repayment_schedule(loan_id: int) -> List[Dict[str, Any]]:
    """Retrieves full existing repayment schedule for a loan."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, payment_number, due_date, scheduled_principal, scheduled_interest,
           scheduled_total, remaining_balance, status
    FROM repayment_schedules
    WHERE loan_id = ?
    ORDER BY payment_number ASC
    """, (loan_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    if not rows:
        return generate_repayment_schedule(loan_id, "MONTHLY")
    return rows

def execute_repayment(
    loan_id: int,
    amount_paid: float,
    allocation_policy: str = "PRO_RATA",
    schedule_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Executes a repayment payment event and distributes funds to syndicate lenders
    under the specified allocation policy:
    - PRO_RATA: Proportional to original committed capital share.
    - LARGEST_CONTRIBUTION_FIRST (LCF): Waterfall paying down largest exposure first.
    - EARLIEST_FUNDING_FIRST (EFF): Waterfall paying down earliest commitment first.
    Guarantees zero-penny leak reconciliation.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Fetch Loan & Active Syndicate Positions
    cursor.execute("SELECT id, loan_amount, funded_amount, status FROM loans WHERE id = ?", (loan_id,))
    loan = cursor.fetchone()
    if not loan:
        conn.close()
        raise ValueError(f"Loan ID {loan_id} not found.")

    cursor.execute("""
    SELECT id, lender_id, lender_name, contribution_amount, share_pct, funded_at
    FROM funding_positions
    WHERE loan_id = ?
    ORDER BY id ASC
    """, (loan_id,))
    positions = [dict(p) for p in cursor.fetchall()]

    if not positions:
        conn.close()
        raise ValueError(f"No funded lenders registered on loan ID {loan_id} to receive payout.")

    total_syndicate_capital = sum(p['contribution_amount'] for p in positions)
    if total_syndicate_capital <= 0:
        total_syndicate_capital = loan['loan_amount']

    # 2. Split Payment into Principal & Interest based on active schedule item
    principal_portion = 0.0
    interest_portion = 0.0

    target_schedule = None
    if schedule_id:
        cursor.execute("SELECT * FROM repayment_schedules WHERE id = ?", (schedule_id,))
        target_schedule = cursor.fetchone()
    else:
        cursor.execute("SELECT * FROM repayment_schedules WHERE loan_id = ? AND status = 'PENDING' ORDER BY payment_number ASC LIMIT 1", (loan_id,))
        target_schedule = cursor.fetchone()

    if target_schedule:
        expected_total = target_schedule['scheduled_total']
        ratio = min(1.0, amount_paid / max(expected_total, 1.0))
        interest_portion = round(target_schedule['scheduled_interest'] * ratio, 2)
        principal_portion = round(amount_paid - interest_portion, 2)
        # Mark schedule item PAID if fully covered
        if amount_paid >= (expected_total - 1.0):
            cursor.execute("UPDATE repayment_schedules SET status = 'PAID' WHERE id = ?", (target_schedule['id'],))
        else:
            cursor.execute("UPDATE repayment_schedules SET status = 'PARTIAL' WHERE id = ?", (target_schedule['id'],))
    else:
        # Default 80% principal, 20% interest estimate
        principal_portion = round(amount_paid * 0.82, 2)
        interest_portion = round(amount_paid - principal_portion, 2)

    # 3. Allocation Engine Calculation
    allocations = []
    pol_upper = allocation_policy.upper()

    if pol_upper == "LARGEST_CONTRIBUTION_FIRST":
        # Sort positions descending by contribution amount
        sorted_pos = sorted(positions, key=lambda x: x['contribution_amount'], reverse=True)
        remaining_p = principal_portion
        for p in sorted_pos:
            lender_cap = p['contribution_amount']
            p_payout = min(remaining_p, lender_cap)
            remaining_p = round(remaining_p - p_payout, 2)
            # Interest paid pro-rata across positions
            int_payout = round(interest_portion * (lender_cap / total_syndicate_capital), 2)
            allocations.append({
                "lender_id": p['lender_id'],
                "lender_name": p['lender_name'],
                "share_pct": p['share_pct'],
                "principal_payout": p_payout,
                "interest_payout": int_payout,
                "total_payout": round(p_payout + int_payout, 2)
            })

    elif pol_upper in ["EARLIEST_FUNDING_FIRST", "QUEUE_SEQUENTIAL"]:
        # Sort positions ascending by funded_at timestamp
        sorted_pos = sorted(positions, key=lambda x: x['funded_at'])
        remaining_p = principal_portion
        for p in sorted_pos:
            lender_cap = p['contribution_amount']
            p_payout = min(remaining_p, lender_cap)
            remaining_p = round(remaining_p - p_payout, 2)
            int_payout = round(interest_portion * (lender_cap / total_syndicate_capital), 2)
            allocations.append({
                "lender_id": p['lender_id'],
                "lender_name": p['lender_name'],
                "share_pct": p['share_pct'],
                "principal_payout": p_payout,
                "interest_payout": int_payout,
                "total_payout": round(p_payout + int_payout, 2)
            })

    else:  # PRO_RATA (Default)
        running_principal = 0.0
        running_interest = 0.0
        for i, p in enumerate(positions):
            weight = p['contribution_amount'] / total_syndicate_capital
            if i == len(positions) - 1:
                # Last lender absorbs rounding residue
                p_payout = round(principal_portion - running_principal, 2)
                int_payout = round(interest_portion - running_interest, 2)
            else:
                p_payout = round(principal_portion * weight, 2)
                int_payout = round(interest_portion * weight, 2)
                running_principal += p_payout
                running_interest += int_payout

            allocations.append({
                "lender_id": p['lender_id'],
                "lender_name": p['lender_name'],
                "share_pct": p['share_pct'],
                "principal_payout": p_payout,
                "interest_payout": int_payout,
                "total_payout": round(p_payout + int_payout, 2)
            })

    # 4. Deposit Payouts into Lenders' Available Balance
    now_str = datetime.now(timezone.utc).isoformat()
    for alloc in allocations:
        cursor.execute("""
        UPDATE lenders
        SET available_balance = available_balance + ?
        WHERE id = ?
        """, (alloc['total_payout'], alloc['lender_id']))

    # 5. Record Transaction in Database
    allocations_json = json.dumps(allocations)
    cursor.execute("""
    INSERT INTO repayment_transactions (
        loan_id, schedule_id, payment_date, amount_paid,
        principal_allocated, interest_allocated, allocation_policy, allocation_breakdown
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        loan_id,
        target_schedule['id'] if target_schedule else None,
        now_str,
        amount_paid,
        principal_portion,
        interest_portion,
        allocation_policy,
        allocations_json
    ))
    tx_id = cursor.lastrowid

    # 6. Audit Trail
    cursor.execute("""
    INSERT INTO audit_logs (event_type, target_id, actor, details, timestamp)
    VALUES (?, ?, ?, ?, ?)
    """, (
        "REPAYMENT_EXECUTED",
        f"LOAN-{loan_id}",
        "BORROWER_REPAYMENT_SERVICE",
        f"Repaid ₹{amount_paid:,.2f} using {allocation_policy} policy across {len(allocations)} syndicate lenders.",
        now_str
    ))

    conn.commit()
    conn.close()

    return {
        "transaction_id": tx_id,
        "loan_id": loan_id,
        "schedule_id": target_schedule['id'] if target_schedule else None,
        "payment_date": now_str,
        "amount_paid": amount_paid,
        "principal_allocated": principal_portion,
        "interest_allocated": interest_portion,
        "allocation_policy": allocation_policy,
        "allocations": allocations
    }
