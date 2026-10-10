"""
RISKORA - Relational Database Layer (SQLite)
Defines schema, indices, foreign key constraints, connection management,
and pre-seeding for realistic digital micro-lending loans, borrowers, syndicates,
single-lender negotiations, and ORA risk audit logs.
"""

import sqlite3
import json
import os
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

DB_PATH = "riskora/data/riskora.db"

def get_db_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initializes tables and seeds initial realistic micro-lending portfolio."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        salt TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'lender',
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS lenders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lender_code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        institution_type TEXT DEFAULT 'Private Syndicate',
        total_committed REAL DEFAULT 1000000.0,
        available_balance REAL DEFAULT 750000.0,
        risk_tolerance TEXT DEFAULT 'BALANCED',
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS borrowers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        borrower_code TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        city TEXT,
        age INTEGER NOT NULL,
        education TEXT NOT NULL,
        employment_type TEXT NOT NULL,
        marital_status TEXT NOT NULL,
        annual_income REAL NOT NULL,
        months_employed INTEGER NOT NULL,
        credit_score INTEGER NOT NULL,
        num_credit_lines INTEGER NOT NULL,
        has_mortgage INTEGER DEFAULT 0,
        has_dependents INTEGER DEFAULT 0,
        is_identity_verified INTEGER DEFAULT 1,
        bank_verified_monthly_income REAL DEFAULT 35000.0,
        psychometric_integrity_score INTEGER DEFAULT 84,
        unbanked_reason TEXT DEFAULT 'Lack of registered property collateral for commercial bank loan',
        device_fingerprint_status TEXT DEFAULT 'GENUINE_HUMAN',
        enach_mandate_authorized INTEGER DEFAULT 1,
        terms_agreed INTEGER DEFAULT 1,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS loans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        loan_code TEXT UNIQUE NOT NULL,
        borrower_id INTEGER NOT NULL REFERENCES borrowers(id) ON DELETE CASCADE,
        loan_amount REAL NOT NULL,
        funded_amount REAL DEFAULT 0.0,
        loan_term INTEGER NOT NULL, -- in months
        interest_rate REAL NOT NULL, -- annual percentage
        dti_ratio REAL NOT NULL,
        loan_purpose TEXT NOT NULL,
        has_cosigner INTEGER DEFAULT 0,
        repayment_frequency TEXT DEFAULT 'MONTHLY', -- MONTHLY, BI_MONTHLY, CUSTOM_FIXED, FLEXIBLE_WINDOW
        repayment_policy TEXT DEFAULT 'PRO_RATA', -- PRO_RATA, LARGEST_CONTRIBUTION_FIRST, EARLIEST_FUNDING_FIRST
        status TEXT DEFAULT 'APPLIED', -- APPLIED, ANALYZED, FUNDING, FULLY_FUNDED, ACTIVE, COMPLETED, DEFAULTED
        created_at TEXT NOT NULL,
        analyzed_at TEXT
    );

    CREATE TABLE IF NOT EXISTS risk_assessments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        loan_id INTEGER UNIQUE NOT NULL REFERENCES loans(id) ON DELETE CASCADE,
        assessed_at TEXT NOT NULL,
        model_version TEXT NOT NULL,
        probability_of_default REAL NOT NULL,
        risk_score INTEGER NOT NULL,
        risk_level TEXT NOT NULL,
        recommended_review_intensity TEXT NOT NULL,
        data_quality_score INTEGER NOT NULL,
        anomaly_detected INTEGER NOT NULL,
        raw_intelligence TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS funding_positions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        loan_id INTEGER NOT NULL REFERENCES loans(id) ON DELETE CASCADE,
        lender_id INTEGER NOT NULL REFERENCES lenders(id) ON DELETE CASCADE,
        lender_name TEXT NOT NULL,
        contribution_amount REAL NOT NULL,
        share_pct REAL NOT NULL,
        funded_at TEXT NOT NULL,
        status TEXT DEFAULT 'COMMITTED'
    );

    CREATE TABLE IF NOT EXISTS repayment_schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        loan_id INTEGER NOT NULL REFERENCES loans(id) ON DELETE CASCADE,
        payment_number INTEGER NOT NULL,
        due_date TEXT NOT NULL,
        scheduled_principal REAL NOT NULL,
        scheduled_interest REAL NOT NULL,
        scheduled_total REAL NOT NULL,
        remaining_balance REAL NOT NULL,
        status TEXT DEFAULT 'PENDING' -- PENDING, PAID, PARTIAL, OVERDUE
    );

    CREATE TABLE IF NOT EXISTS repayment_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        loan_id INTEGER NOT NULL REFERENCES loans(id) ON DELETE CASCADE,
        schedule_id INTEGER REFERENCES repayment_schedules(id),
        payment_date TEXT NOT NULL,
        amount_paid REAL NOT NULL,
        principal_allocated REAL NOT NULL,
        interest_allocated REAL NOT NULL,
        allocation_policy TEXT NOT NULL,
        allocation_breakdown TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS negotiations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        loan_id INTEGER NOT NULL REFERENCES loans(id) ON DELETE CASCADE,
        lender_id INTEGER REFERENCES lenders(id) ON DELETE SET NULL,
        current_principal REAL NOT NULL,
        current_interest_rate REAL NOT NULL,
        current_term INTEGER NOT NULL,
        current_emi REAL NOT NULL,
        status TEXT DEFAULT 'OPEN', -- OPEN, ACCEPTED_AND_LOCKED, REJECTED
        history TEXT NOT NULL, -- JSON
        mandate_registered INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS ora_audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        loan_id INTEGER NOT NULL REFERENCES loans(id) ON DELETE CASCADE,
        ora_score INTEGER NOT NULL, -- 300 to 900
        risk_grade TEXT NOT NULL,
        probability_of_default REAL NOT NULL,
        verdict TEXT NOT NULL,
        cryptographic_hash TEXT NOT NULL, -- SHA-256 integrity proof
        vector_analysis TEXT NOT NULL, -- JSON
        evidence_foundation TEXT NOT NULL, -- JSON
        assessed_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS datasets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        uploaded_at TEXT NOT NULL,
        total_rows INTEGER NOT NULL,
        valid_rows INTEGER NOT NULL,
        default_rate REAL NOT NULL,
        roc_auc REAL,
        status TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        target_id TEXT NOT NULL,
        actor TEXT NOT NULL,
        details TEXT NOT NULL,
        timestamp TEXT NOT NULL
    );
    """)

    # Ensure migration columns in borrowers table if table was created previously
    cursor.execute("PRAGMA table_info(borrowers);")
    existing_cols = {row[1] for row in cursor.fetchall()}
    migrations = [
        ("is_identity_verified", "INTEGER DEFAULT 1"),
        ("bank_verified_monthly_income", "REAL DEFAULT 35000.0"),
        ("psychometric_integrity_score", "INTEGER DEFAULT 84"),
        ("unbanked_reason", "TEXT DEFAULT 'Lack of registered property collateral for commercial bank loan'"),
        ("device_fingerprint_status", "TEXT DEFAULT 'GENUINE_HUMAN'"),
        ("enach_mandate_authorized", "INTEGER DEFAULT 1"),
        ("terms_agreed", "INTEGER DEFAULT 1")
    ]
    for col_name, col_def in migrations:
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE borrowers ADD COLUMN {col_name} {col_def};")

    conn.commit()
    seed_initial_data(conn)
    conn.close()

def reset_db():
    """Clears and re-seeds database cleanly (useful for tests and fresh demo reset)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = OFF;")
    tables = [
        "audit_logs", "datasets", "ora_audit_logs", "negotiations",
        "repayment_transactions", "repayment_schedules", "funding_positions",
        "risk_assessments", "loans", "borrowers", "lenders", "users"
    ]
    for t in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {t};")
    conn.commit()
    conn.close()
    init_db()

def seed_initial_data(conn: sqlite3.Connection):
    """Seeds rich demonstration data representing diverse borrower risk profiles."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM lenders")
    if cursor.fetchone()[0] > 0:
        return  # already seeded

    now = datetime.now(timezone.utc).isoformat()

    # 0. Seed Users
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        from riskora.backend.security import hash_password
        users_seed = [
            ("admin", "admin@riskora.institutional", "AdminPassword@2026", "admin"),
            ("underwriter", "underwriter@riskora.institutional", "Underwriter@2026", "underwriter"),
            ("lender", "lender@riskora.institutional", "LenderRiskora@2026", "lender")
        ]
        for uname, uemail, upass, urole in users_seed:
            salt_hex, hash_hex = hash_password(upass)
            cursor.execute(
                "INSERT INTO users (username, email, hashed_password, salt, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (uname, uemail, hash_hex, salt_hex, urole, now)
            )

    # 1. Seed Lenders
    lenders_data = [
        ("LEN-001", "Apex Credit Partners", "Institutional Fund", 2500000.0, 1850000.0, "MODERATE", now),
        ("LEN-002", "BluePeak Micro Capital", "Alternative Credit Fund", 1800000.0, 1200000.0, "CONSERVATIVE", now),
        ("LEN-003", "Vikramaditya Impact Fund", "Impact Investing Syndicate", 1200000.0, 950000.0, "AGGRESSIVE", now)
    ]
    cursor.executemany(
        "INSERT INTO lenders (lender_code, name, institution_type, total_committed, available_balance, risk_tolerance, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        lenders_data
    )

    # 2. Seed Realistic Diverse Borrowers and Loans with Zero Self-Reported Trust Fields
    borrowers_data = [
        # 1. Low Risk Prime Borrower (Established retail expansion)
        ("BR-101", "Sunita Sharma", "sunita.s@example.com", "9876543210", "Jaipur", 41, "Bachelor", "Salaried", "Married", 650000, 72, 745, 6, 1, 1,
         1, 54000.0, 89, "Lack of commercial property title deeds required by nationalized banks", "GENUINE_HUMAN", 1, 1, now),
        # 2. Moderate Risk Gig Entrepreneur (E-commerce inventory)
        ("BR-102", "Rahul Verma", "rahul.v@example.com", "9876543211", "Pune", 29, "Bachelor", "Self-Employed", "Single", 420000, 30, 640, 4, 0, 0,
         1, 35000.0, 82, "Informal digital merchant inflows without 3 years audited ITR", "GENUINE_HUMAN", 1, 1, now),
        # 3. High Risk Borrower (High DTI, Subprime credit, Debt consolidation)
        ("BR-103", "Mohammed Farhan", "m.farhan@example.com", "9876543212", "Hyderabad", 34, "High School", "Gig/Contract", "Married", 280000, 14, 535, 3, 0, 2,
         1, 23000.0, 68, "Subprime bureau score from pandemic delivery gig transition", "GENUINE_HUMAN", 1, 1, now),
        # 4. Low Risk Prime with Co-Signer (Medical clinic equipment)
        ("BR-104", "Dr. Ananya Sen", "ananya.sen@example.com", "9876543213", "Kolkata", 38, "Master", "Salaried", "Married", 950000, 90, 780, 8, 1, 1,
         1, 79000.0, 94, "Urgent diagnostic machine purchase cycle faster than 45-day bank queue", "GENUINE_HUMAN", 1, 1, now),
        # 5. Moderate Risk Self-Employed (Craft textile workshop)
        ("BR-105", "Pooja Patel", "pooja.p@example.com", "9876543214", "Ahmedabad", 45, "Associate", "Self-Employed", "Married", 480000, 48, 625, 5, 0, 2,
         1, 40000.0, 78, "Seasonal handloom cash receivables not recognized as bank collateral", "GENUINE_HUMAN", 1, 1, now),
        # 6. High Risk Unemployed transition (Emergency medical)
        ("BR-106", "Karan Malhotra", "karan.m@example.com", "9876543215", "Delhi", 31, "High School", "Unemployed", "Single", 180000, 0, 490, 2, 0, 1,
         1, 15000.0, 61, "Employment gap during hospital treatment; no active salary slip", "GENUINE_HUMAN", 1, 1, now),
        # 7. Moderate Risk Agricultural supply distributor
        ("BR-107", "Rameshwar Goud", "rameshwar.g@example.com", "9876543216", "Nagpur", 50, "High School", "Self-Employed", "Married", 360000, 60, 660, 4, 1, 3,
         1, 30000.0, 84, "Rural mandi trade receivables outside formal banking clearing", "GENUINE_HUMAN", 1, 1, now),
        # 8. Anomaly Edge-Case Borrower (High requested loan relative to short tenure)
        ("BR-108", "David Lyngdoh", "david.l@example.com", "9876543217", "Shillong", 22, "High School", "Gig/Contract", "Single", 210000, 2, 570, 1, 0, 0,
         1, 17500.0, 71, "Thin-file first generation digital earner without collateral history", "GENUINE_HUMAN", 1, 1, now),
    ]

    for b in borrowers_data:
        cursor.execute("""
            INSERT INTO borrowers (
                borrower_code, full_name, email, phone, city, age, education, employment_type, marital_status,
                annual_income, months_employed, credit_score, num_credit_lines, has_mortgage, has_dependents,
                is_identity_verified, bank_verified_monthly_income, psychometric_integrity_score, unbanked_reason,
                device_fingerprint_status, enach_mandate_authorized, terms_agreed, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, b)

    # 3. Seed Corresponding Loans
    loans_data = [
        # Loan 1: Low Risk (Sunita)
        ("LN-2026-001", 1, 80000.0, 0.0, 12, 14.5, 0.24, "Business Expansion", 1, "MONTHLY", "PRO_RATA", "APPLIED", now),
        # Loan 2: Moderate Risk (Rahul) - Partially funded in syndicate
        ("LN-2026-002", 2, 60000.0, 35000.0, 12, 18.0, 0.38, "Inventory Purchase", 0, "MONTHLY", "PRO_RATA", "FUNDING", now),
        # Loan 3: High Risk (Mohammed)
        ("LN-2026-003", 3, 90000.0, 0.0, 18, 25.5, 0.54, "Debt Consolidation", 0, "MONTHLY", "LARGEST_CONTRIBUTION_FIRST", "APPLIED", now),
        # Loan 4: Prime Low Risk (Dr. Ananya) - Fully funded, Active repayment
        ("LN-2026-004", 4, 150000.0, 150000.0, 24, 13.0, 0.18, "Equipment Purchase", 1, "MONTHLY", "PRO_RATA", "ACTIVE", now),
        # Loan 5: Moderate Risk (Pooja)
        ("LN-2026-005", 5, 50000.0, 0.0, 12, 19.5, 0.35, "Working Capital", 0, "BI_MONTHLY", "PRO_RATA", "APPLIED", now),
        # Loan 6: Severe High Risk (Karan)
        ("LN-2026-006", 6, 40000.0, 0.0, 6, 28.0, 0.68, "Medical Emergency", 0, "MONTHLY", "PRO_RATA", "APPLIED", now),
        # Loan 7: Moderate Agricultural (Rameshwar)
        ("LN-2026-007", 7, 75000.0, 0.0, 18, 17.0, 0.31, "Inventory Purchase", 1, "CUSTOM_FIXED", "PRO_RATA", "APPLIED", now),
        # Loan 8: Anomaly Profile (David)
        ("LN-2026-008", 8, 120000.0, 0.0, 12, 24.0, 0.62, "Working Capital", 0, "FLEXIBLE_WINDOW", "PRO_RATA", "APPLIED", now)
    ]

    for ln in loans_data:
        cursor.execute("""
            INSERT INTO loans (loan_code, borrower_id, loan_amount, funded_amount, loan_term, interest_rate, dti_ratio, loan_purpose, has_cosigner, repayment_frequency, repayment_policy, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ln)

    # 4. Seed Funding Positions for Loan 2 (Partial syndicate) and Loan 4 (Fully funded syndicate)
    cursor.execute("""
        INSERT INTO funding_positions (loan_id, lender_id, lender_name, contribution_amount, share_pct, funded_at)
        VALUES (2, 1, 'Apex Credit Partners', 20000.0, 33.33, ?)
    """, (now,))
    cursor.execute("""
        INSERT INTO funding_positions (loan_id, lender_id, lender_name, contribution_amount, share_pct, funded_at)
        VALUES (2, 3, 'Vikramaditya Impact Fund', 15000.0, 25.0, ?)
    """, (now,))

    cursor.execute("""
        INSERT INTO funding_positions (loan_id, lender_id, lender_name, contribution_amount, share_pct, funded_at)
        VALUES (4, 1, 'Apex Credit Partners', 75000.0, 50.0, ?)
    """, (now,))
    cursor.execute("""
        INSERT INTO funding_positions (loan_id, lender_id, lender_name, contribution_amount, share_pct, funded_at)
        VALUES (4, 2, 'BluePeak Micro Capital', 50000.0, 33.33, ?)
    """, (now,))
    cursor.execute("""
        INSERT INTO funding_positions (loan_id, lender_id, lender_name, contribution_amount, share_pct, funded_at)
        VALUES (4, 3, 'Vikramaditya Impact Fund', 25000.0, 16.67, ?)
    """, (now,))

    # 5. Seed Initial Negotiation for Loan 1 (Sunita Sharma)
    history_sunita = [
        {
            "sender": "lender",
            "sender_name": "Apex Credit Partners",
            "rate": 15.0,
            "term": 12,
            "principal": 80000.0,
            "emi": 7222.0,
            "message": "Reviewed retail balance sheets. Can offer ₹80,000 at 15.0% for 12 months with eNACH auto-debit.",
            "timestamp": now
        },
        {
            "sender": "borrower",
            "sender_name": "Sunita Sharma",
            "rate": 14.0,
            "term": 12,
            "principal": 80000.0,
            "emi": 7184.0,
            "message": "Thank you for the prompt offer. Could we settle at 14.0% considering my consistent POS turnover?",
            "timestamp": now
        }
    ]
    cursor.execute("""
        INSERT INTO negotiations (loan_id, lender_id, current_principal, current_interest_rate, current_term, current_emi, status, history, mandate_registered, created_at, updated_at)
        VALUES (1, 1, 80000.0, 14.0, 12, 7184.0, 'OPEN', ?, 1, ?, ?)
    """, (json.dumps(history_sunita), now, now))

    conn.commit()
    print("Database successfully initialized and seeded with realistic micro-lending records.")

def calculate_emi(principal: float, annual_rate: float, term_months: int) -> float:
    """Calculates standard monthly EMI."""
    r = (annual_rate / 100.0) / 12.0
    if r > 0:
        factor = (1.0 + r) ** term_months
        emi = principal * (r * factor) / (factor - 1.0)
    else:
        emi = principal / term_months
    return round(emi, 2)

# --- User Management Helpers ---
def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)

def create_user(username: str, email: str, password: str, role: str = "lender") -> Dict[str, Any]:
    from riskora.backend.security import hash_password
    now = datetime.now(timezone.utc).isoformat()
    salt_hex, hash_hex = hash_password(password)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, email, hashed_password, salt, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (username, email, hash_hex, salt_hex, role, now)
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"id": user_id, "username": username, "email": email, "role": role, "created_at": now}

# --- Mock Lender Creation ---
def add_mock_lender(name: str, capital_pool: float, institution_type: str = "Private Individual", risk_tolerance: str = "BALANCED") -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    cursor.execute("SELECT COUNT(*) FROM lenders")
    count = cursor.fetchone()[0] + 1
    code = f"LEN-MOCK-{count:03d}"
    cursor.execute(
        "INSERT INTO lenders (lender_code, name, institution_type, total_committed, available_balance, risk_tolerance, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (code, name, institution_type, capital_pool, capital_pool, risk_tolerance, now)
    )
    lender_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {
        "id": lender_id,
        "lender_code": code,
        "name": name,
        "institution_type": institution_type,
        "total_committed": capital_pool,
        "available_balance": capital_pool,
        "risk_tolerance": risk_tolerance
    }

# --- Borrower Application Submission ---
def create_borrower_application(
    full_name: str,
    phone: str,
    city: str,
    annual_income: float,
    loan_amount: float,
    loan_term: int,
    interest_rate: float,
    loan_purpose: str,
    unbanked_reason: str,
    has_cosigner: int = 0
) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()

    cursor.execute("SELECT COUNT(*) FROM borrowers")
    b_count = cursor.fetchone()[0] + 1
    b_code = f"BR-IND-{100 + b_count}"

    monthly_inc = round(annual_income / 12.0, 2)
    cibil_sim = 670

    cursor.execute("""
        INSERT INTO borrowers (
            borrower_code, full_name, email, phone, city, age, education, employment_type, marital_status,
            annual_income, months_employed, credit_score, num_credit_lines, has_mortgage, has_dependents,
            is_identity_verified, bank_verified_monthly_income, psychometric_integrity_score, unbanked_reason,
            device_fingerprint_status, enach_mandate_authorized, terms_agreed, created_at
        ) VALUES (?, ?, ?, ?, ?, 32, 'Graduate', 'Self-Employed', 'Married', ?, 36, ?, 3, 0, 1, 1, ?, 85, ?, 'GENUINE_HUMAN', 1, 1, ?)
    """, (
        b_code, full_name, f"{full_name.lower().replace(' ', '.')}@example.com", phone, city,
        annual_income, cibil_sim, monthly_inc, unbanked_reason, now
    ))
    borrower_id = cursor.lastrowid

    cursor.execute("SELECT COUNT(*) FROM loans")
    l_count = cursor.fetchone()[0] + 1
    l_code = f"LN-2026-{100 + l_count}"

    dti_est = round(min(0.65, (loan_amount / max(annual_income, 1.0)) * 0.4), 2)

    cursor.execute("""
        INSERT INTO loans (
            loan_code, borrower_id, loan_amount, funded_amount, loan_term, interest_rate, dti_ratio,
            loan_purpose, has_cosigner, repayment_frequency, repayment_policy, status, created_at
        ) VALUES (?, ?, ?, 0.0, ?, ?, ?, ?, ?, 'MONTHLY', 'PRO_RATA', 'APPLIED', ?)
    """, (
        l_code, borrower_id, loan_amount, loan_term, interest_rate, dti_est,
        loan_purpose, has_cosigner, now
    ))
    loan_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return {
        "borrower_id": borrower_id,
        "loan_id": loan_id,
        "loan_code": l_code,
        "borrower_code": b_code,
        "status": "APPLIED",
        "message": "Loan application successfully posted to the verified marketplace."
    }

# --- Single Lender Negotiation Hall Helpers ---
def get_negotiation_by_loan_id(loan_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM negotiations WHERE loan_id = ?", (loan_id,))
    row = cursor.fetchone()

    if not row:
        # Check loan to initialize negotiation
        cursor.execute("SELECT * FROM loans WHERE id = ?", (loan_id,))
        loan = cursor.fetchone()
        if not loan:
            conn.close()
            return None
        now = datetime.now(timezone.utc).isoformat()
        emi = calculate_emi(loan['loan_amount'], loan['interest_rate'], loan['loan_term'])
        init_history = [{
            "sender": "system",
            "sender_name": "RiskOra Protocol",
            "rate": loan['interest_rate'],
            "term": loan['loan_term'],
            "principal": loan['loan_amount'],
            "emi": emi,
            "message": "Negotiation Hall initialized. Awaiting lender offer.",
            "timestamp": now
        }]
        cursor.execute("""
            INSERT INTO negotiations (loan_id, lender_id, current_principal, current_interest_rate, current_term, current_emi, status, history, mandate_registered, created_at, updated_at)
            VALUES (?, 1, ?, ?, ?, ?, 'OPEN', ?, 1, ?, ?)
        """, (loan_id, loan['loan_amount'], loan['interest_rate'], loan['loan_term'], emi, json.dumps(init_history), now, now))
        conn.commit()
        cursor.execute("SELECT * FROM negotiations WHERE loan_id = ?", (loan_id,))
        row = cursor.fetchone()

    conn.close()
    res = dict(row)
    res['history'] = json.loads(res['history'])
    return res

def add_negotiation_offer(
    loan_id: int,
    lender_id: int,
    proposed_principal: float,
    proposed_rate: float,
    proposed_term: int,
    sender_role: str,
    sender_name: str,
    message: str
) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()

    emi = calculate_emi(proposed_principal, proposed_rate, proposed_term)

    cursor.execute("SELECT * FROM negotiations WHERE loan_id = ?", (loan_id,))
    row = cursor.fetchone()
    if not row:
        history = []
    else:
        history = json.loads(row['history'])

    history.append({
        "sender": sender_role,
        "sender_name": sender_name,
        "rate": proposed_rate,
        "term": proposed_term,
        "principal": proposed_principal,
        "emi": emi,
        "message": message,
        "timestamp": now
    })

    if row:
        cursor.execute("""
            UPDATE negotiations
            SET lender_id = ?, current_principal = ?, current_interest_rate = ?, current_term = ?, current_emi = ?, history = ?, updated_at = ?
            WHERE loan_id = ?
        """, (lender_id, proposed_principal, proposed_rate, proposed_term, emi, json.dumps(history), now, loan_id))
    else:
        cursor.execute("""
            INSERT INTO negotiations (loan_id, lender_id, current_principal, current_interest_rate, current_term, current_emi, status, history, mandate_registered, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 'OPEN', ?, 1, ?, ?)
        """, (loan_id, lender_id, proposed_principal, proposed_rate, proposed_term, emi, json.dumps(history), now, now))

    conn.commit()
    conn.close()
    return {
        "loan_id": loan_id,
        "current_principal": proposed_principal,
        "current_interest_rate": proposed_rate,
        "current_term": proposed_term,
        "current_emi": emi,
        "history": history
    }

def accept_and_lock_negotiation(loan_id: int) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()

    cursor.execute("SELECT * FROM negotiations WHERE loan_id = ?", (loan_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError("No active negotiation found for this loan.")

    cursor.execute("""
        UPDATE negotiations
        SET status = 'ACCEPTED_AND_LOCKED', mandate_registered = 1, updated_at = ?
        WHERE loan_id = ?
    """, (now, loan_id))

    # Update loan contract variables
    cursor.execute("""
        UPDATE loans
        SET loan_amount = ?, interest_rate = ?, loan_term = ?, status = 'ACTIVE'
        WHERE id = ?
    """, (row['current_principal'], row['current_interest_rate'], row['current_term'], loan_id))

    # Register funding position for the single lender
    lender_id = row['lender_id'] or 1
    cursor.execute("SELECT name FROM lenders WHERE id = ?", (lender_id,))
    lender_row = cursor.fetchone()
    lender_name = lender_row['name'] if lender_row else "Apex Credit Partners"

    cursor.execute("""
        INSERT INTO funding_positions (loan_id, lender_id, lender_name, contribution_amount, share_pct, funded_at, status)
        VALUES (?, ?, ?, ?, 100.0, ?, 'COMMITTED')
    """, (loan_id, lender_id, lender_name, row['current_principal'], now))

    # Update funded amount
    cursor.execute("UPDATE loans SET funded_amount = loan_amount WHERE id = ?", (loan_id,))

    conn.commit()
    conn.close()
    return {
        "status": "ACCEPTED_AND_LOCKED",
        "message": "Loan terms locked. Contract frozen and eNACH mandate verified.",
        "contract": {
            "loan_id": loan_id,
            "principal": row['current_principal'],
            "interest_rate": row['current_interest_rate'],
            "tenor": row['current_term'],
            "monthly_emi": row['current_emi'],
            "lender_name": lender_name,
            "mandate_registered": True
        }
    }

# --- ORA Audit Log Helpers ---
def record_ora_audit(
    loan_id: int,
    ora_score: int,
    risk_grade: str,
    probability_of_default: float,
    verdict: str,
    vector_analysis: List[Dict[str, Any]],
    evidence_foundation: List[str]
) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()

    proof_str = f"{loan_id}:{ora_score}:{risk_grade}:{probability_of_default}:{now}"
    crypto_hash = hashlib.sha256(proof_str.encode('utf-8')).hexdigest()

    cursor.execute("""
        INSERT INTO ora_audit_logs (
            loan_id, ora_score, risk_grade, probability_of_default, verdict,
            cryptographic_hash, vector_analysis, evidence_foundation, assessed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        loan_id, ora_score, risk_grade, probability_of_default, verdict,
        crypto_hash, json.dumps(vector_analysis), json.dumps(evidence_foundation), now
    ))
    conn.commit()
    conn.close()
    return crypto_hash

def get_ora_audit(loan_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ora_audit_logs WHERE loan_id = ? ORDER BY id DESC LIMIT 1", (loan_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    res = dict(row)
    res['vector_analysis'] = json.loads(res['vector_analysis'])
    res['evidence_foundation'] = json.loads(res['evidence_foundation'])
    return res

if __name__ == "__main__":
    init_db()
