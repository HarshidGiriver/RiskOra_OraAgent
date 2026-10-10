# RISKORA : Relational Database Schema & Data Dictionary

## 1. Relational Topology (SQLite)

The RISKORA relational database is structured with strict foreign key constraints, cascading referential actions, and audit logs.

```mermaid
erDiagram
    BORROWERS ||--o{ LOANS : "applies for"
    LOANS ||--o| RISK_ASSESSMENTS : "evaluated by"
    LOANS ||--o{ FUNDING_POSITIONS : "syndicated across"
    LENDERS ||--o{ FUNDING_POSITIONS : "commits capital to"
    LOANS ||--o{ REPAYMENT_SCHEDULES : "amortized into"
    REPAYMENT_SCHEDULES ||--o{ REPAYMENT_TRANSACTIONS : "settled via"

    BORROWERS {
        int id PK
        string borrower_code UK
        string full_name
        string email
        string phone
        string city
        int age
        string education
        string employment_type
        string marital_status
        float annual_income
        int months_employed
        int credit_score
        int num_credit_lines
        int has_mortgage
        int has_dependents
        string created_at
    }

    LOANS {
        int id PK
        string loan_code UK
        int borrower_id FK
        float loan_amount
        float funded_amount
        int loan_term
        float interest_rate
        float dti_ratio
        string loan_purpose
        int has_cosigner
        string repayment_frequency
        string repayment_policy
        string status
        string created_at
        string analyzed_at
    }

    RISK_ASSESSMENTS {
        int id PK
        int loan_id FK, UK
        string assessed_at
        string model_version
        float probability_of_default
        int risk_score
        string risk_level
        string recommended_review_intensity
        int data_quality_score
        int anomaly_detected
        text raw_intelligence
    }

    LENDERS {
        int id PK
        string lender_code UK
        string name
        string institution_type
        float total_committed
        float available_balance
        string risk_tolerance
        string created_at
    }

    FUNDING_POSITIONS {
        int id PK
        int loan_id FK
        int lender_id FK
        string lender_name
        float contribution_amount
        float share_pct
        string funded_at
        string status
    }

    REPAYMENT_SCHEDULES {
        int id PK
        int loan_id FK
        int payment_number
        string due_date
        float scheduled_principal
        float scheduled_interest
        float scheduled_total
        float remaining_balance
        string status
    }

    REPAYMENT_TRANSACTIONS {
        int id PK
        int loan_id FK
        int schedule_id FK
        string payment_date
        float amount_paid
        float principal_allocated
        float interest_allocated
        string allocation_policy
        text allocation_breakdown
    }

    AUDIT_LOGS {
        int id PK
        string event_type
        string target_id
        string actor
        string details
        string timestamp
    }
```

---

## 2. Table Schemas & Constraints

### 2.1 Table: `borrowers`
Primary identity and demographic data of loan applicants.
- `id`: `INTEGER PRIMARY KEY AUTOINCREMENT`
- `borrower_code`: `TEXT UNIQUE NOT NULL` (e.g. `BR-101`)
- `full_name`: `TEXT NOT NULL`
- `email`: `TEXT`
- `phone`: `TEXT`
- `city`: `TEXT`
- `age`: `INTEGER NOT NULL CHECK(age >= 18 AND age <= 90)`
- `education`: `TEXT NOT NULL`
- `employment_type`: `TEXT NOT NULL`
- `marital_status`: `TEXT NOT NULL`
- `annual_income`: `REAL NOT NULL CHECK(annual_income > 0)`
- `months_employed`: `INTEGER NOT NULL CHECK(months_employed >= 0)`
- `credit_score`: `INTEGER NOT NULL CHECK(credit_score >= 300 AND credit_score <= 850)`
- `num_credit_lines`: `INTEGER NOT NULL CHECK(num_credit_lines >= 0)`
- `has_mortgage`: `INTEGER DEFAULT 0 CHECK(has_mortgage IN (0, 1))`
- `has_dependents`: `INTEGER DEFAULT 0 CHECK(has_dependents IN (0, 1))`
- `created_at`: `TEXT NOT NULL` (ISO-8601 UTC)

### 2.2 Table: `loans`
Micro-loan applications and current status lifecycle.
- `id`: `INTEGER PRIMARY KEY AUTOINCREMENT`
- `loan_code`: `TEXT UNIQUE NOT NULL` (e.g. `LN-2026-001`)
- `borrower_id`: `INTEGER NOT NULL REFERENCES borrowers(id) ON DELETE CASCADE`
- `loan_amount`: `REAL NOT NULL CHECK(loan_amount > 0)`
- `funded_amount`: `REAL DEFAULT 0.0 CHECK(funded_amount >= 0.0)`
- `loan_term`: `INTEGER NOT NULL CHECK(loan_term >= 1)`
- `interest_rate`: `REAL NOT NULL CHECK(interest_rate > 0.0)`
- `dti_ratio`: `REAL NOT NULL CHECK(dti_ratio >= 0.0)`
- `loan_purpose`: `TEXT NOT NULL`
- `has_cosigner`: `INTEGER DEFAULT 0 CHECK(has_cosigner IN (0, 1))`
- `repayment_frequency`: `TEXT DEFAULT 'MONTHLY'` (`MONTHLY`, `BI_MONTHLY`, `CUSTOM_FIXED`, `FLEXIBLE_WINDOW`)
- `repayment_policy`: `TEXT DEFAULT 'PRO_RATA'` (`PRO_RATA`, `LARGEST_CONTRIBUTION_FIRST`, `EARLIEST_FUNDING_FIRST`)
- `status`: `TEXT DEFAULT 'APPLIED'` (`APPLIED`, `ANALYZED`, `FUNDING`, `FULLY_FUNDED`, `ACTIVE`, `COMPLETED`, `DEFAULTED`)
- `created_at`: `TEXT NOT NULL`
- `analyzed_at`: `TEXT`

### 2.3 Table: `risk_assessments`
Stores immutable ML inference records, scores, and explainability packages.
- `id`: `INTEGER PRIMARY KEY AUTOINCREMENT`
- `loan_id`: `INTEGER UNIQUE NOT NULL REFERENCES loans(id) ON DELETE CASCADE`
- `assessed_at`: `TEXT NOT NULL`
- `model_version`: `TEXT NOT NULL`
- `probability_of_default`: `REAL NOT NULL CHECK(probability_of_default >= 0.0 AND probability_of_default <= 1.0)`
- `risk_score`: `INTEGER NOT NULL CHECK(risk_score >= 0 AND risk_score <= 100)`
- `risk_level`: `TEXT NOT NULL` (`LOW`, `MEDIUM`, `HIGH`)
- `recommended_review_intensity`: `TEXT NOT NULL` (`Standard`, `Enhanced Verification`, `Credit Committee Review`)
- `data_quality_score`: `INTEGER NOT NULL CHECK(data_quality_score >= 0 AND data_quality_score <= 100)`
- `anomaly_detected`: `INTEGER NOT NULL CHECK(anomaly_detected IN (0, 1))`
- `raw_intelligence`: `TEXT NOT NULL` (Full JSON payload of XAI drivers, anomaly checks, and recommendations)

### 2.4 Table: `funding_positions`
Tracks committed capital positions within loan syndicates.
- `id`: `INTEGER PRIMARY KEY AUTOINCREMENT`
- `loan_id`: `INTEGER NOT NULL REFERENCES loans(id) ON DELETE CASCADE`
- `lender_id`: `INTEGER NOT NULL REFERENCES lenders(id) ON DELETE CASCADE`
- `lender_name`: `TEXT NOT NULL`
- `contribution_amount`: `REAL NOT NULL CHECK(contribution_amount > 0)`
- `share_pct`: `REAL NOT NULL`
- `funded_at`: `TEXT NOT NULL`
- `status`: `TEXT DEFAULT 'COMMITTED'`

### 2.5 Table: `repayment_schedules`
Contains mathematically exact amortized schedules.
- `id`: `INTEGER PRIMARY KEY AUTOINCREMENT`
- `loan_id`: `INTEGER NOT NULL REFERENCES loans(id) ON DELETE CASCADE`
- `payment_number`: `INTEGER NOT NULL`
- `due_date`: `TEXT NOT NULL`
- `scheduled_principal`: `REAL NOT NULL`
- `scheduled_interest`: `REAL NOT NULL`
- `scheduled_total`: `REAL NOT NULL`
- `remaining_balance`: `REAL NOT NULL`
- `status`: `TEXT DEFAULT 'PENDING'` (`PENDING`, `PAID`, `PARTIAL`, `OVERDUE`)

### 2.6 Table: `repayment_transactions`
Auditable logs of executed borrower repayments with allocation breakdowns.
- `id`: `INTEGER PRIMARY KEY AUTOINCREMENT`
- `loan_id`: `INTEGER NOT NULL REFERENCES loans(id) ON DELETE CASCADE`
- `schedule_id`: `INTEGER REFERENCES repayment_schedules(id)`
- `payment_date`: `TEXT NOT NULL`
- `amount_paid`: `REAL NOT NULL CHECK(amount_paid > 0)`
- `principal_allocated`: `REAL NOT NULL`
- `interest_allocated`: `REAL NOT NULL`
- `allocation_policy`: `TEXT NOT NULL`
- `allocation_breakdown`: `TEXT NOT NULL` (JSON array of payouts per syndicate lender)

### 2.7 Table: `lenders`
Institutional and private capital providers.
- `id`: `INTEGER PRIMARY KEY AUTOINCREMENT`
- `lender_code`: `TEXT UNIQUE NOT NULL`
- `name`: `TEXT NOT NULL`
- `institution_type`: `TEXT DEFAULT 'Private Syndicate'`
- `total_committed`: `REAL DEFAULT 1000000.0`
- `available_balance`: `REAL DEFAULT 750000.0`
- `risk_tolerance`: `TEXT DEFAULT 'BALANCED'`
- `created_at`: `TEXT NOT NULL`

### 2.8 Table: `audit_logs`
System activity audit trail.
- `id`: `INTEGER PRIMARY KEY AUTOINCREMENT`
- `event_type`: `TEXT NOT NULL`
- `target_id`: `TEXT NOT NULL`
- `actor`: `TEXT NOT NULL`
- `details`: `TEXT NOT NULL`
- `timestamp`: `TEXT NOT NULL`
