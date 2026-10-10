"""
RISKORA - Loan Application Service
Manages micro-loan marketplace catalog, faceted filtering, borrower associations,
and loan lifecycle status transitions.
"""

import sqlite3
import json
from typing import Dict, Any, List, Optional
from riskora.backend.database import get_db_connection

def get_loans(
    search: Optional[str] = None,
    risk_level: Optional[str] = None,
    status: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    sort_by: str = "id",
    sort_desc: bool = False,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """Retrieves paginated and filtered list of loans for the Borrower Marketplace."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    SELECT
        l.id, l.loan_code, l.loan_amount, l.funded_amount, l.loan_term,
        l.interest_rate, l.dti_ratio, l.loan_purpose, l.has_cosigner,
        l.repayment_frequency, l.repayment_policy, l.status, l.created_at, l.analyzed_at,
        b.id as borrower_id, b.borrower_code, b.full_name as borrower_name, b.city as borrower_city,
        b.annual_income as borrower_income, b.credit_score as borrower_credit_score,
        b.is_identity_verified, b.bank_verified_monthly_income, b.psychometric_integrity_score,
        b.unbanked_reason, b.device_fingerprint_status, b.enach_mandate_authorized,
        ra.risk_score, ra.risk_level, ra.probability_of_default, ra.data_quality_score, ra.anomaly_detected
    FROM loans l
    JOIN borrowers b ON l.borrower_id = b.id
    LEFT JOIN risk_assessments ra ON l.id = ra.loan_id
    WHERE 1=1
    """
    params: List[Any] = []

    if search:
        search_like = f"%{search.strip()}%"
        query += " AND (l.loan_code LIKE ? OR b.full_name LIKE ? OR l.loan_purpose LIKE ? OR b.city LIKE ?)"
        params.extend([search_like, search_like, search_like, search_like])

    if risk_level and risk_level.upper() != "ALL":
        query += " AND ra.risk_level = ?"
        params.append(risk_level.upper())

    if status and status.upper() != "ALL":
        query += " AND l.status = ?"
        params.append(status.upper())

    if min_amount is not None:
        query += " AND l.loan_amount >= ?"
        params.append(min_amount)

    if max_amount is not None:
        query += " AND l.loan_amount <= ?"
        params.append(max_amount)

    # Count total matching
    count_query = f"SELECT COUNT(*) FROM ({query})"
    cursor.execute(count_query, params)
    total_count = cursor.fetchone()[0]

    # Allowed sorting fields
    sort_map = {
        "id": "l.id",
        "loan_amount": "l.loan_amount",
        "credit_score": "b.credit_score",
        "risk_score": "ra.risk_score",
        "probability_of_default": "ra.probability_of_default",
        "created_at": "l.created_at"
    }
    col = sort_map.get(sort_by, "l.id")
    direction = "DESC" if sort_desc else "ASC"
    query += f" ORDER BY {col} {direction} LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor.execute(query, params)
    rows = cursor.fetchall()

    results = []
    for r in rows:
        funded = r['funded_amount'] or 0.0
        requested = r['loan_amount'] or 1.0
        results.append({
            "id": r['id'],
            "loan_code": r['loan_code'],
            "borrower_id": r['borrower_id'],
            "borrower_name": r['borrower_name'],
            "borrower_city": r['borrower_city'],
            "borrower_income": r['borrower_income'],
            "borrower_credit_score": r['borrower_credit_score'],
            "is_identity_verified": bool(r['is_identity_verified']),
            "bank_verified_monthly_income": float(r['bank_verified_monthly_income'] or (r['borrower_income'] / 12.0)),
            "psychometric_integrity_score": int(r['psychometric_integrity_score'] or 80),
            "unbanked_reason": str(r['unbanked_reason'] or "Lack of formal registered property collateral"),
            "device_fingerprint_status": str(r['device_fingerprint_status'] or "GENUINE_HUMAN"),
            "enach_mandate_authorized": bool(r['enach_mandate_authorized']),
            "loan_amount": r['loan_amount'],
            "funded_amount": funded,
            "remaining_amount": max(0.0, requested - funded),
            "funding_progress_pct": round(min(100.0, (funded / requested) * 100.0), 1),
            "loan_term": r['loan_term'],
            "interest_rate": r['interest_rate'],
            "dti_ratio": r['dti_ratio'],
            "loan_purpose": r['loan_purpose'],
            "has_cosigner": r['has_cosigner'],
            "repayment_frequency": r['repayment_frequency'],
            "repayment_policy": r['repayment_policy'],
            "status": r['status'],
            "created_at": r['created_at'],
            "analyzed_at": r['analyzed_at'],
            "risk_assessment": {
                "risk_score": r['risk_score'],
                "risk_level": r['risk_level'],
                "probability_of_default": r['probability_of_default'],
                "data_quality_score": r['data_quality_score'],
                "anomaly_detected": bool(r['anomaly_detected'])
            } if r['risk_score'] is not None else None
        })

    conn.close()
    return {
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "loans": results
    }

def get_loan_by_id(loan_id: int) -> Optional[Dict[str, Any]]:
    """Fetches comprehensive loan profile including borrower and risk assessment."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        l.*,
        b.borrower_code, b.full_name as borrower_name, b.email as borrower_email,
        b.phone as borrower_phone, b.city as borrower_city, b.age as borrower_age,
        b.education as borrower_education, b.employment_type as borrower_employment_type,
        b.marital_status as borrower_marital_status, b.annual_income as borrower_income,
        b.months_employed as borrower_months_employed, b.credit_score as borrower_credit_score,
        b.num_credit_lines as borrower_num_credit_lines, b.has_mortgage as borrower_has_mortgage,
        b.has_dependents as borrower_has_dependents,
        b.is_identity_verified as borrower_is_identity_verified,
        b.bank_verified_monthly_income as borrower_bank_verified_monthly_income,
        b.psychometric_integrity_score as borrower_psychometric_integrity_score,
        b.unbanked_reason as borrower_unbanked_reason,
        b.device_fingerprint_status as borrower_device_fingerprint_status,
        b.enach_mandate_authorized as borrower_enach_mandate_authorized,
        ra.assessed_at, ra.model_version, ra.probability_of_default, ra.risk_score,
        ra.risk_level, ra.recommended_review_intensity, ra.data_quality_score,
        ra.anomaly_detected, ra.raw_intelligence
    FROM loans l
    JOIN borrowers b ON l.borrower_id = b.id
    LEFT JOIN risk_assessments ra ON l.id = ra.loan_id
    WHERE l.id = ?
    """, (loan_id,))

    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    # Get funding positions
    cursor.execute("""
    SELECT id, lender_id, lender_name, contribution_amount, share_pct, funded_at, status
    FROM funding_positions
    WHERE loan_id = ?
    ORDER BY funded_at ASC
    """, (loan_id,))
    positions = [dict(p) for p in cursor.fetchall()]

    conn.close()

    risk_info = None
    if row['raw_intelligence']:
        try:
            risk_info = json.loads(row['raw_intelligence'])
        except Exception:
            risk_info = {
                "risk_score": row['risk_score'],
                "risk_level": row['risk_level'],
                "probability_of_default": row['probability_of_default'],
                "recommended_review_intensity": row['recommended_review_intensity'],
                "data_quality_score": row['data_quality_score'],
                "model_version": row['model_version']
            }

    funded = row['funded_amount'] or 0.0
    requested = row['loan_amount'] or 1.0

    return {
        "id": row['id'],
        "loan_code": row['loan_code'],
        "borrower": {
            "id": row['borrower_id'],
            "borrower_code": row['borrower_code'],
            "full_name": row['borrower_name'],
            "email": row['borrower_email'],
            "phone": row['borrower_phone'],
            "city": row['borrower_city'],
            "age": row['borrower_age'],
            "education": row['borrower_education'],
            "employment_type": row['borrower_employment_type'],
            "marital_status": row['borrower_marital_status'],
            "annual_income": row['borrower_income'],
            "months_employed": row['borrower_months_employed'],
            "credit_score": row['borrower_credit_score'],
            "num_credit_lines": row['borrower_num_credit_lines'],
            "has_mortgage": row['borrower_has_mortgage'],
            "has_dependents": row['borrower_has_dependents'],
            "is_identity_verified": bool(row['borrower_is_identity_verified']),
            "bank_verified_monthly_income": float(row['borrower_bank_verified_monthly_income'] or (row['borrower_income'] / 12.0)),
            "psychometric_integrity_score": int(row['borrower_psychometric_integrity_score'] or 85),
            "unbanked_reason": str(row['borrower_unbanked_reason'] or "Lack of registered property collateral"),
            "device_fingerprint_status": str(row['borrower_device_fingerprint_status'] or "GENUINE_HUMAN"),
            "enach_mandate_authorized": bool(row['borrower_enach_mandate_authorized'])
        },
        "loan_amount": row['loan_amount'],
        "funded_amount": funded,
        "remaining_amount": max(0.0, requested - funded),
        "funding_progress_pct": round(min(100.0, (funded / requested) * 100.0), 1),
        "loan_term": row['loan_term'],
        "interest_rate": row['interest_rate'],
        "dti_ratio": row['dti_ratio'],
        "loan_purpose": row['loan_purpose'],
        "has_cosigner": row['has_cosigner'],
        "repayment_frequency": row['repayment_frequency'],
        "repayment_policy": row['repayment_policy'],
        "status": row['status'],
        "created_at": row['created_at'],
        "analyzed_at": row['analyzed_at'],
        "funding_positions": positions,
        "risk_assessment": risk_info
    }
