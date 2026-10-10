"""
RISKORA - Funding & Syndicate Management Service
Supports Single-Lender and Fractional Syndication.
Strictly articulates the conceptual distinction between Borrower Default Risk
and Lender Exposure Concentration.
"""

import sqlite3
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from riskora.backend.database import get_db_connection

def pledge_funding(
    loan_id: int,
    lender_id: int,
    contribution_amount: float
) -> Dict[str, Any]:
    """
    Records a funding pledge from a lender into a loan syndicate.
    Validates capital capacity, prevents over-funding, and recalculates exposure shares.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Fetch Loan Details
    cursor.execute("""
    SELECT id, loan_code, loan_amount, funded_amount, status
    FROM loans
    WHERE id = ?
    """, (loan_id,))
    loan = cursor.fetchone()
    if not loan:
        conn.close()
        raise ValueError(f"Loan ID {loan_id} not found.")

    if loan['status'] in ['FULLY_FUNDED', 'ACTIVE', 'COMPLETED', 'DEFAULTED']:
        conn.close()
        raise ValueError(f"Loan {loan['loan_code']} is already closed for new funding (Status: {loan['status']}).")

    requested = loan['loan_amount']
    current_funded = loan['funded_amount'] or 0.0
    remaining = requested - current_funded

    if contribution_amount <= 0:
        conn.close()
        raise ValueError("Contribution amount must be strictly greater than zero.")

    if contribution_amount > (remaining + 0.01):
        conn.close()
        raise ValueError(
            f"Contribution of ₹{contribution_amount:,.2f} exceeds remaining required funding of ₹{remaining:,.2f}."
        )

    # 2. Fetch Lender
    cursor.execute("""
    SELECT id, lender_code, name, available_balance
    FROM lenders
    WHERE id = ?
    """, (lender_id,))
    lender = cursor.fetchone()
    if not lender:
        conn.close()
        raise ValueError(f"Lender ID {lender_id} not found.")

    if lender['available_balance'] < contribution_amount:
        conn.close()
        raise ValueError(
            f"Lender {lender['name']} has insufficient available balance (Available: ₹{lender['available_balance']:,.2f}, Attempted: ₹{contribution_amount:,.2f})."
        )

    now_str = datetime.now(timezone.utc).isoformat()
    new_funded = current_funded + contribution_amount
    share_pct = round((contribution_amount / requested) * 100.0, 2)

    # 3. Insert Funding Position
    cursor.execute("""
    INSERT INTO funding_positions (
        loan_id, lender_id, lender_name, contribution_amount, share_pct, funded_at, status
    ) VALUES (?, ?, ?, ?, ?, ?, 'COMMITTED')
    """, (loan_id, lender_id, lender['name'], contribution_amount, share_pct, now_str))

    # 4. Update Loan Status
    new_status = 'FULLY_FUNDED' if abs(new_funded - requested) < 1.0 else 'FUNDING'
    cursor.execute("""
    UPDATE loans
    SET funded_amount = ?, status = ?
    WHERE id = ?
    """, (new_funded, new_status, loan_id))

    # 5. Deduct from Lender Balance
    cursor.execute("""
    UPDATE lenders
    SET available_balance = available_balance - ?
    WHERE id = ?
    """, (contribution_amount, lender_id))

    # 6. Audit Trail
    cursor.execute("""
    INSERT INTO audit_logs (event_type, target_id, actor, details, timestamp)
    VALUES (?, ?, ?, ?, ?)
    """, (
        "FUNDING_PLEDGED",
        f"LOAN-{loan_id}",
        lender['name'],
        f"Pledged ₹{contribution_amount:,.2f} ({share_pct}% of loan)",
        now_str
    ))

    conn.commit()
    conn.close()

    return get_syndicate_summary(loan_id)

def get_syndicate_summary(loan_id: int) -> Dict[str, Any]:
    """
    Returns full syndicate composition, concentration index, and risk distinction guidance.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT loan_amount, funded_amount, status FROM loans WHERE id = ?", (loan_id,))
    loan_row = cursor.fetchone()
    if not loan_row:
        conn.close()
        raise ValueError(f"Loan ID {loan_id} not found.")

    cursor.execute("""
    SELECT id, lender_id, lender_name, contribution_amount, share_pct, funded_at, status
    FROM funding_positions
    WHERE loan_id = ?
    ORDER BY funded_at ASC
    """, (loan_id,))
    positions = [dict(p) for p in cursor.fetchall()]
    conn.close()

    requested = loan_row['loan_amount']
    funded = loan_row['funded_amount'] or 0.0
    remaining = max(0.0, requested - funded)

    # Calculate Herfindahl-Hirschman Concentration Index (HHI)
    # Range 0.0 to 1.0 (1.0 = Single Lender monopoly, lower = distributed syndicate)
    hhi = 0.0
    if funded > 0:
        hhi = sum((p['contribution_amount'] / funded) ** 2 for p in positions)

    return {
        "loan_id": loan_id,
        "requested_amount": requested,
        "funded_amount": funded,
        "remaining_amount": remaining,
        "funding_progress_pct": round(min(100.0, (funded / requested) * 100.0), 1),
        "funding_status": loan_row['status'],
        "positions_count": len(positions),
        "positions": positions,
        "concentration_metrics": {
            "hhi_index": round(hhi, 4),
            "concentration_tier": "HIGH (Single-Lender Dominant)" if hhi > 0.60 else ("MODERATE" if hhi > 0.35 else "DIVERSIFIED SYNDICATE"),
            "risk_distinction_notice": (
                "CONCEPTUAL DISTINCTION: Fractional syndication distributes lender capital exposure concentration "
                "across multiple participants. It does NOT alter the borrower's inherent default probability (PD)."
            )
        }
    }

def get_lenders_list() -> List[Dict[str, Any]]:
    """Returns available institutional and private lenders."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, lender_code, name, institution_type, total_committed, available_balance, risk_tolerance
    FROM lenders
    ORDER BY id ASC
    """)
    lenders = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return lenders
