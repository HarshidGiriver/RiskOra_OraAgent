# RISKORA : Automated Testing & Verification Guide

## 1. Testing Philosophy & Standards

The RISKORA test suite verifies critical financial computations, machine learning guarantees, syndicate constraints, and API contracts.

Testing standards enforced:
1. **Zero Penny Leakage:** All repayment allocations and amortization schedules must reconcile to the exact cent without rounding residue.
2. **Probability Bounds:** Calibrated Probability of Default ($PD$) must be strictly bounded in $(0.0, 1.0)$, and Risk Score strictly in $[0, 100]$.
3. **Idempotency & Isolation:** Test fixtures run with clean database state resets via `reset_db()` to prevent inter-test state contamination.
4. **End-to-End API Integration:** All REST endpoints must return validated schemas and appropriate HTTP status codes.

---

## 2. Test Suite Architecture

```text
riskora/tests/
├── test_ml_pipeline.py       # ML inference, score bounds, XAI, Data Quality, Anomaly tests
├── test_repayment_math.py    # Annuity amortization math & allocation waterfalls
├── test_funding_rules.py     # Syndicate pledge validation, limits, and HHI concentration
└── test_api_endpoints.py     # End-to-end FastAPI endpoint integration tests
```

---

## 3. Test Coverage Breakdown

### 3.1 ML Pipeline Tests (`test_ml_pipeline.py`)
- `test_inference_engine_prediction_bounds`: Asserts that loaded champion model outputs $PD \in (0, 1)$, Risk Score $\in [0, 100]$, assigns valid risk tier (`LOW`, `MEDIUM`, `HIGH`), and populates explainability drivers.
- `test_data_quality_engine_penalties`: Asserts that pristine records receive 100% Data Quality score and `PASS`, while contradictory records (e.g. Unemployed with $>0$ tenure) incur penalties and return `CRITICAL_DEFICIENCIES`.
- `test_anomaly_detection`: Asserts that normal records pass without alerts, while impossible profiles (e.g. Age 20 with 10 years tenure) trigger anomaly flags and `Enhanced Verification` intensity.

### 3.2 Repayment & Amortization Tests (`test_repayment_math.py`)
- `test_amortization_schedule_zero_balance_reconciliation`: Asserts that 12-month amortized micro-loans have positive principal and interest components in every period, total principal equals original loan amount, and terminal period balance settles to **exactly ₹0.00**.
- `test_repayment_allocation_waterfalls_zero_penny_leak`: Tests payment of ₹12,500.50 across a 3-lender syndicate under:
  1. `PRO_RATA` policy: Asserts $\sum \text{Payouts} == 12,500.50$.
  2. `LARGEST_CONTRIBUTION_FIRST` (LCF) waterfall: Asserts $\sum \text{Payouts} == 12,500.50$.
  3. `EARLIEST_FUNDING_FIRST` (EFF) waterfall: Asserts $\sum \text{Payouts} == 12,500.50$.

### 3.3 Funding & Syndicate Tests (`test_funding_rules.py`)
- `test_funding_pledge_and_overfunding_prevention`: Asserts that pledging capital updates loan funded amount and lender balance, and pledging more than remaining required capital raises `ValueError` ("exceeds remaining").
- `test_syndicate_concentration_hhi`: Asserts that Herfindahl-Hirschman concentration index is computed within $(0.0, 1.0)$ and attaches proper risk distinction disclosure.

### 3.4 API Integration Tests (`test_api_endpoints.py`)
- `test_api_health`: Verifies `/api/health` returns `200 OK` with active model identifier.
- `test_list_loans_and_filtering`: Verifies `/api/loans` with text search and risk filters.
- `test_real_ml_analysis_endpoint`: Verifies `POST /api/risk/analyze/1` triggers real inference and persists score.
- `test_what_if_simulation_endpoint`: Verifies `POST /api/simulation` calculates baseline, scenario, and net delta.
- `test_pdf_report_download`: Verifies `GET /api/reports/1/pdf` returns valid `application/pdf` binary stream.

---

## 4. How to Execute Tests

### Run Full Test Suite:
```powershell
python -m pytest riskora/tests -v
```

### Run Specific Test Modules:
```powershell
# Run ML tests
python -m pytest riskora/tests/test_ml_pipeline.py -v

# Run Repayment Math tests
python -m pytest riskora/tests/test_repayment_math.py -v

# Run Funding tests
python -m pytest riskora/tests/test_funding_rules.py -v

# Run API Integration tests
python -m pytest riskora/tests/test_api_endpoints.py -v
```

### Execution Results:
```text
============================= test session starts =============================
platform win32 -- Python 3.12.3, pytest-9.1.1, pluggy-1.6.0
collected 12 items

riskora/tests/test_api_endpoints.py::test_api_health PASSED              [  8%]
riskora/tests/test_api_endpoints.py::test_list_loans_and_filtering PASSED [ 16%]
riskora/tests/test_api_endpoints.py::test_real_ml_analysis_endpoint PASSED [ 25%]
riskora/tests/test_api_endpoints.py::test_what_if_simulation_endpoint PASSED [ 33%]
riskora/tests/test_api_endpoints.py::test_pdf_report_download PASSED     [ 41%]
riskora/tests/test_funding_rules.py::test_funding_pledge_and_overfunding_prevention PASSED [ 50%]
riskora/tests/test_funding_rules.py::test_syndicate_concentration_hhi PASSED [ 58%]
riskora/tests/test_ml_pipeline.py::test_inference_engine_prediction_bounds PASSED [ 66%]
riskora/tests/test_ml_pipeline.py::test_data_quality_engine_penalties PASSED [ 75%]
riskora/tests/test_ml_pipeline.py::test_anomaly_detection PASSED         [ 83%]
riskora/tests/test_repayment_math.py::test_amortization_schedule_zero_balance_reconciliation PASSED [ 91%]
riskora/tests/test_repayment_math.py::test_repayment_allocation_waterfalls_zero_penny_leak PASSED [100%]

======================= 12 passed in 13.63s =======================
```
