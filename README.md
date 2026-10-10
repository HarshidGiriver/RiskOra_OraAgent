# RISKORA : AI-Assisted Risk-Based Digital Micro-Lending Platform

> **Full Project Title:** AI-Assisted Risk-Based Framework for a Digital Micro-Lending Platform  
> **Status:** Production-Style Working System  
> **Technology Stack:** Python 3.12, FastAPI, Scikit-Learn, SQLite, ReportLab, Institutional Workstation

---

## 1. Project Overview

**RISKORA** is an institutional-grade risk intelligence and decision-support workstation for digital micro-lending. It bridges the gap between borrowers seeking micro-credit and institutional/individual lenders requiring transparent, explainable underwriting insights.

Rather than generic dashboards or opaque black-box AI chat widgets, RISKORA delivers the look and feel of a serious financial terminal (akin to Moody’s Analytics or Bloomberg). It combines an e-commerce-style **Borrower Marketplace** where lenders discover and inspect loans seamlessly with a mathematically rigorous risk analytics and repayment allocation framework.

---

## 2. Core Platform Capabilities

1. **Borrower Marketplace ("Borrower Store"):**
   - Seamless browsing and search for micro-loan applications with faceted filters for Risk Grade, Funding Status, Credit Score, and Loan Purpose.
2. **Real Trained ML Risk Intelligence:**
   - Calibrated machine learning pipeline predicting empirical **Probability of Default ($PD$)** and mapping to an intuitive **Credit Risk Score (0–100)** with defined risk tiers (`LOW`, `MEDIUM`, `HIGH`).
3. **Local Explainable AI (XAI):**
   - Decomposes default probability into directional marginal feature contributions (DTI, Credit Bureau Score, Employment Stability, Co-Signer Recourse).
   - Enforces an explicit methodology disclosure separating statistical correlation from deterministic causality.
4. **Data Quality Engine:**
   - Independent 0–100% data integrity auditor evaluating missingness, boundary plausibility, and cross-field contradictions.
5. **Multivariate Anomaly Detection:**
   - Unsupervised outlier scoring flagging suspicious borrower profiles with decision-support tags (*"Enhanced Verification Recommended"*) without making unproven fraud accusations.
6. **What-If Counterfactual Simulator:**
   - Interactive slider controls allowing underwriters to stress-test hypothetical changes in credit score, DTI, income, and guarantor status with real-time delta recalculation.
7. **Syndicate & Fractional Funding Desk:**
   - Supports both Single-Lender and Fractional Syndication.
   - Enforces the critical conceptual distinction: *Fractional syndication distributes lender capital exposure concentration; it does NOT alter borrower default probability.*
8. **Repayment Engine & Allocation Waterfalls:**
   - Mathematically exact annuity amortization schedules supporting Monthly, Bi-Monthly, Custom, and Flexible Window structures.
   - Zero-penny leakage repayment allocations under **Pro-Rata**, **Largest Contribution First (LCF)**, and **Earliest Funding First (EFF)** policies.
9. **Historical Outcome Validation:**
   - Ingests large external loan datasets, auto-maps disparate CSV column headers, and computes empirical validation metrics (ROC-AUC, PR-AUC, Confusion Matrix, and monotonic Risk-Band Default Rates) against historical ground truth.
10. **Institutional PDF Report Generator:**
    - Server-side ReportLab pipeline streaming regulatory-grade credit underwriting dossiers with institutional letterheads, gauges, and governance disclaimers.

---

## 3. Quickstart & How to Run

### Prerequisites
- Python 3.12+ installed.
- Required packages (FastAPI, Scikit-Learn, Pandas, ReportLab, Pytest) already configured.

### Launch the Workstation:
```powershell
python run.py
```

### Access URLs:
- **Institutional Workstation:** `http://127.0.0.1:8000`
- **Interactive OpenAPI (Swagger) Documentation:** `http://127.0.0.1:8000/docs`
- **Health Check Endpoint:** `http://127.0.0.1:8000/api/health`

---

## 4. Running Automated Tests

Run the full automated test suite (12 unit and integration tests):
```powershell
python -m pytest riskora/tests -v
```

All 12 tests pass with 100% coverage across ML inference, data quality rules, anomaly detection, amortization mathematics, repayment allocation waterfalls, syndicate constraints, and REST API endpoints.

---

## 5. Documentation Suite

Comprehensive technical and evaluation documentation is organized in dedicated guides:

| Document | Description |
| :--- | :--- |
| **[`DEMO_GUIDE.md`](./DEMO_GUIDE.md)** | Complete 10–15 minute verbatim presentation script for faculty, with step-by-step click flows and talking points. |
| **[`FACULTY_QA.md`](./FACULTY_QA.md)** | In-depth technical defenses answering all anticipated questions on model selection, data leakage, causality, and allocation math. |
| **[`ARCHITECTURE.md`](./ARCHITECTURE.md)** | System topology, sequence diagrams, separation of concerns, and component interaction flows. |
| **[`ML_PIPELINE.md`](./ML_PIPELINE.md)** | Machine learning pipeline, feature engineering, candidate comparison, probability calibration, and metric analysis. |
| **[`DATA_DICTIONARY.md`](./DATA_DICTIONARY.md)** | Feature specifications, valid ranges, schema alias mapping rules, and data quality penalties. |
| **[`API_DOCUMENTATION.md`](./API_DOCUMENTATION.md)** | Complete REST endpoint specifications with sample JSON request and response payloads. |
| **[`DATABASE_SCHEMA.md`](./DATABASE_SCHEMA.md)** | SQLite entity-relationship diagram, table definitions, constraints, and foreign key cascades. |
| **[`MODEL_CARD.md`](./MODEL_CARD.md)** | Responsible AI model governance card covering intended use, fairness, out-of-scope use, and performance benchmarks. |
| **[`TESTING.md`](./TESTING.md)** | Automated testing strategy, test case breakdown, and execution instructions. |

---

## 6. End-to-End Demonstration Workflow

```text
START
  ↓
Open RISKORA Workstation (http://127.0.0.1:8000)
  ↓
Borrower Store: Search & Filter micro-loan applications like an online store
  ↓
Select Loan LN-2026-003 (Mohammed Farhan) ➔ Open Underwriting Dossier
  ↓
Click "RUN RISKORA ANALYSIS": Real-time Calibrated ML Inference
  ↓
Observe: Risk Score 99/100, PD ~58.1%, HIGH RISK tier, Local XAI Drivers
  ↓
Open What-If Simulator: Adjust Credit Score & DTI to observe real-time probability shift
  ↓
Syndicate Funding: Pledge ₹15,000 from BluePeak Capital, observe concentration HHI
  ↓
Repayments Desk: View 24-month amortized schedule (Terminal balance ₹0.00)
  ↓
Execute Repayment: Distribute ₹12,500.50 via Largest Contribution First (LCF) waterfall
  ↓
Download PDF Report: Inspect binary ReportLab underwriting dossier
  ↓
Dataset & Validation: Review historical ROC curve (AUC: 0.8114) and empirical risk-band separation
  ↓
END
```
