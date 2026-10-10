# RISKORA : REST API Documentation

The RISKORA API runs on FastAPI and conforms to the OpenAPI 3.1 standard. Interactive Swagger UI is available at `http://127.0.0.1:8000/docs`.

---

## 1. System & Health

### `GET /api/health`
Returns system status, active champion ML model, and calibration methodology.

**Response (200 OK):**
```json
{
  "status": "HEALTHY",
  "system": "RISKORA Production Engine",
  "active_model": "RISKORA-ML-LogisticRegression-v1.0",
  "version": "1.0.0",
  "calibration": "Sigmoid CalibratedClassifierCV (3-Fold)"
}
```

---

## 2. Borrower Marketplace & Catalog

### `GET /api/loans`
Queries loan catalog with faceted filters, search, sorting, and pagination.

**Query Parameters:**
- `search` (string, optional): Search across Loan ID, Borrower Name, City, or Purpose.
- `risk_level` (string, optional): `LOW`, `MEDIUM`, `HIGH`, `ALL`.
- `status` (string, optional): `APPLIED`, `ANALYZED`, `FUNDING`, `FULLY_FUNDED`, `ACTIVE`, `ALL`.
- `sort_by` (string, default: `id`): `loan_amount`, `credit_score`, `risk_score`, `probability_of_default`.
- `limit` (int, default: 50): Number of records per page.
- `offset` (int, default: 0): Pagination offset.

**Response (200 OK):**
```json
{
  "total": 8,
  "limit": 50,
  "offset": 0,
  "loans": [
    {
      "id": 1,
      "loan_code": "LN-2026-001",
      "borrower_name": "Sunita Sharma",
      "borrower_city": "Jaipur",
      "loan_amount": 80000.0,
      "funded_amount": 0.0,
      "funding_progress_pct": 0.0,
      "loan_term": 12,
      "interest_rate": 14.5,
      "loan_purpose": "Business Expansion",
      "status": "APPLIED",
      "risk_assessment": {
        "risk_score": 18,
        "risk_level": "LOW",
        "probability_of_default": 0.052,
        "data_quality_score": 100
      }
    }
  ]
}
```

### `GET /api/loans/{loan_id}`
Retrieves comprehensive loan dossier, borrower profile, and active syndicate positions.

---

## 3. Real ML Risk Assessment

### `POST /api/risk/analyze/{loan_id}`
Executes real-time calibrated ML inference, local explainability drivers, data quality audit, and anomaly detection on the specified loan.

**Response (200 OK):**
```json
{
  "loan_id": "LN-2026-003",
  "assessment_timestamp": "2026-10-08T04:26:08.520114+00:00",
  "model_version": "RISKORA-ML-LogisticRegression-v1.0",
  "probability_of_default": 0.5807,
  "probability_pct": 58.07,
  "risk_score": 99,
  "risk_level": "HIGH",
  "recommended_review_intensity": "Standard",
  "funding_recommendation": {
    "structure_advice": "Fractional Funding Advised",
    "max_single_ticket_pct": 25.0,
    "rationale": "High-risk profiles benefit from syndication to distribute lender portfolio exposure."
  },
  "risk_drivers": [
    {
      "feature": "Credit Bureau Score",
      "observed_value": "535",
      "benchmark_value": "640",
      "impact_direction": "INCREASES_RISK",
      "impact_pct": 14.0,
      "description": "Credit score of 535 indicates elevated historical delinquency probability."
    }
  ],
  "data_quality": {
    "quality_score": 100,
    "available_fields": 16,
    "total_fields": 16,
    "missing_fields": [],
    "warnings": [],
    "validation_status": "PASS"
  },
  "anomaly_analysis": {
    "anomaly_detected": false,
    "anomaly_score": 0.0,
    "anomaly_flags": [],
    "recommended_review_intensity": "Standard"
  },
  "methodology_disclaimer": "METHODOLOGY NOTICE: Feature contributions quantify statistical associations and marginal model sensitivity derived from empirical historical loan data. They represent predictive correlations, NOT direct causal proof."
}
```

---

## 4. Syndicate & Fractional Funding

### `POST /api/funding/pledge/{loan_id}`
Pledges lender capital to a loan syndicate.

**Request Body:**
```json
{
  "lender_id": 2,
  "contribution_amount": 15000.0
}
```

**Response (200 OK):**
```json
{
  "loan_id": 2,
  "requested_amount": 60000.0,
  "funded_amount": 50000.0,
  "remaining_amount": 10000.0,
  "funding_progress_pct": 83.3,
  "funding_status": "FUNDING",
  "positions_count": 3,
  "concentration_metrics": {
    "hhi_index": 0.3556,
    "concentration_tier": "MODERATE",
    "risk_distinction_notice": "CONCEPTUAL DISTINCTION: Fractional syndication distributes lender capital exposure concentration across multiple participants. It does NOT alter the borrower's inherent default probability (PD)."
  }
}
```

---

## 5. Repayment & Allocation

### `GET /api/repayments/schedule/{loan_id}`
Retrieves existing amortized repayment schedule separating principal and interest with zero-balance final settlement.

### `POST /api/repayments/execute/{loan_id}`
Processes a repayment installment and allocates cash flows across syndicate participants under specified waterfall policy (`PRO_RATA`, `LARGEST_CONTRIBUTION_FIRST`, `EARLIEST_FUNDING_FIRST`).

**Request Body:**
```json
{
  "amount_paid": 12500.50,
  "allocation_policy": "LARGEST_CONTRIBUTION_FIRST"
}
```

---

## 6. What-If Simulation

### `POST /api/simulation`
Computes counterfactual credit risk scenarios.

**Request Body:**
```json
{
  "loan_id": 1,
  "credit_score": 740,
  "annual_income": 650000.0,
  "loan_amount": 80000.0,
  "dti_ratio": 0.22,
  "loan_term": 12,
  "months_employed": 72,
  "has_cosigner": 1
}
```

**Response (200 OK):**
```json
{
  "baseline": { "probability_pct": 5.2, "risk_score": 18, "risk_level": "LOW" },
  "scenario": { "probability_pct": 3.1, "risk_score": 10, "risk_level": "LOW" },
  "pd_delta_pct_points": -2.1,
  "score_delta": -8,
  "key_sensitivities": [
    {
      "lever": "Attach Creditworthy Co-Signer Guarantee",
      "projected_pd": 2.8,
      "impact_pct_points": -0.3
    }
  ]
}
```

---

## 7. Report Generation

### `GET /api/reports/{loan_id}/pdf`
Generates and streams a regulatory-grade PDF report generated dynamically via ReportLab.
