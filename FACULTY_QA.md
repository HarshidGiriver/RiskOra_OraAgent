# RISKORA : Technical Evaluation & Faculty Q&A Guide

This document provides rigorous, mathematically and financially grounded answers to questions frequently posed by technical evaluators, academic faculty, and industry credit risk specialists.

---

### 1. Why AI/ML? Why not just use simple expert rules or credit score cutoffs?
**Answer:**
Traditional rule-based cutoffs (e.g., "Reject if Credit Score < 600 or DTI > 40%") suffer from severe limitations:
1. **Rigid Step-Functions & False Exclusions:** A borrower with a 595 credit score but a 10-year stable salaried job and a creditworthy co-signer is rejected under binary rules, despite exhibiting low empirical default risk.
2. **Failure to Capture Non-Linear Multi-Feature Interactions:** Credit risk is multivariate. A moderate DTI (35%) combined with volatile gig income and high loan-to-income represents significantly compounded risk that linear rule checklists fail to capture.
3. **Continuous Empirical Probabilities:** ML algorithms estimate a continuous Probability of Default ($PD \in [0, 1]$), allowing dynamic risk-adjusted pricing (APR), loan structuring, and fractional syndication limits rather than binary "Yes/No" answers.

---

### 2. What is the target variable, and how is it defined?
**Answer:**
The target variable is binary: `Default` $\in \{0, 1\}$.
- `Default = 1`: The borrower incurred severe delinquency (typically 90+ days past due or charge-off) during the loan term.
- `Default = 0`: The borrower fully repaid the loan under scheduled amortized terms.

---

### 3. How did you prevent Data Leakage between training and evaluation?
**Answer:**
We implemented strict safeguards across three layers:
1. **Target Feature Exclusion:** `Default` is strictly reserved as the supervision target $y$. It is stripped from the feature matrix $X$ prior to preprocessing and inference.
2. **Pre-Split Feature Engineering:** All transformers (median imputation via `SimpleImputer`, scaling via `StandardScaler`, and categorical encoding via `OneHotEncoder`) are fit **strictly** on the training fold (`X_train`) within a scikit-learn `Pipeline`. Test statistics are never exposed during fitting.
3. **Derived Ratio Leakage Prevention:** Engineered features (such as `Loan_to_Income` and `DTI Ratio`) use strictly pre-disbursement stated attributes, preventing post-origination state leakage.

---

### 4. Why this model architecture? How was the Champion Model selected?
**Answer:**
Rather than arbitrarily picking a complex model, we built a formal model comparison experiment pipeline evaluating three distinct classifier families on imbalanced micro-lending data:
1. **Logistic Regression** (L2 Regularized, Balanced Class Weights)
2. **Random Forest Classifier** (Ensemble of Decorrelated Decision Trees)
3. **HistGradientBoostingClassifier** (Gradient-Boosted Decision Trees)

Each candidate was calibrated using **Sigmoid CalibratedClassifierCV** with 3-fold cross-validation. Candidate performance on the holdout test set:
- **Logistic Regression:** ROC-AUC: **0.8114**, PR-AUC: **0.5172**, Brier Score: **0.1102**, Composite Score: **0.7564**
- **Random Forest:** ROC-AUC: **0.8087**, PR-AUC: **0.5324**, Brier Score: **0.1094**, Composite Score: **0.7540**
- **Gradient Boosting:** ROC-AUC: **0.8056**, PR-AUC: **0.5405**, Brier Score: **0.1102**, Composite Score: **0.7505**

**Why Calibrated Logistic Regression was chosen as Champion:**
- It achieved the highest ROC-AUC (0.8114) and strong probability calibration while maintaining **perfect linear interpretability and zero latency**. In regulated financial services (e.g., Fair Credit Reporting Act, RBI guidelines), linear scorecards provide verifiable monotonicity and auditable adverse action notices.

---

### 5. Why these evaluation metrics? Why not just report Accuracy?
**Answer:**
In credit risk datasets, class distribution is naturally imbalanced (~12–17% default rate). A naive "dummy" model that predicts zero defaults for every borrower achieves **83–88% accuracy**, yet is completely catastrophic for a lending institution because it catches **zero** bad loans.

Therefore, accuracy is actively misleading. We evaluate:
1. **ROC-AUC (Area Under Receiver Operating Characteristic):** Quantifies ranking ability (probability that a randomly chosen defaulter has a higher predicted risk score than a non-defaulter). Our model achieved **0.8114**.
2. **PR-AUC (Precision-Recall Area / Average Precision):** Evaluates minority class detection under severe imbalance without being inflated by true negatives. Our model achieved **0.5172**.
3. **Brier Score:** $\frac{1}{N}\sum (\hat{p}_i - y_i)^2$. Measures probability calibration accuracy (mean squared difference between predicted probability and actual binary outcome). Our model achieved **0.1102**.
4. **Cost-Weighted Business Recall:** At an underwriting cost threshold of $\tau = 0.22$ (reflecting that unpredicted default losses are ~4-5x costlier than rejected good applicants), the model captures **65.8% of historical defaults**.

---

### 6. How is Probability of Default (PD) different from Credit Risk Score?
**Answer:**
- **Probability of Default ($PD \in [0.0, 1.0]$):** The empirical statistical likelihood that the borrower will fail to repay scheduled installments. It is a mathematical frequency.
- **Credit Risk Score (0 to 100):** A normalized, business-friendly representation where **higher indicates higher risk**.
  $$\text{Risk Score} = \text{round}\left(\text{clip}\left(\frac{PD}{0.32} \times 100, 5, 99\right)\right)$$
  - $PD \le 0.08$ $\implies$ **LOW RISK** (Score 5–25)
  - $0.08 < PD \le 0.22$ $\implies$ **MEDIUM RISK** (Score 26–65)
  - $PD > 0.22$ $\implies$ **HIGH RISK** (Score 66–99)

---

### 7. How are the Risk Drivers calculated? Does this imply Causality?
**Answer:**
Our Explainable AI (XAI) engine decomposes local feature contributions relative to empirical population benchmarks:
$$\Delta \text{Contribution}_j = w_j \cdot (x_j - \bar{x}_j)$$
where $w_j$ is the calibrated feature sensitivity and $\bar{x}_j$ is the portfolio baseline median.

**CRITICAL SCIENTIFIC DISTINCTION:**
Feature contributions represent **predictive statistical associations and marginal model sensitivities**. They do **NOT** prove deterministic causality. For example, having a "Gig/Contract" employment status correlates with higher default risk in historical observations, but forcing a gig worker to change contracts does not guarantee creditworthiness. RISKORA explicitly prints this methodology disclosure on all screens and PDF exports.

---

### 8. How does the Data Quality Engine differ from the Risk Engine?
**Answer:**
Data quality and credit risk are strictly separated orthogonal dimensions:
- A high-net-worth borrower can have **poor data quality** (e.g., missing employment tenure, unverified income documents, malformed pincode).
- A subprime borrower can have **impeccable data quality** (all 16 fields verified, consistent, and cleanly audited).

The Data Quality Engine checks:
1. Field completeness (16 required fields).
2. Plausible bounds (Age 18–80, Bureau Score 300–850, DTI 0.0–2.0).
3. Logical contradictions (e.g., Status = "Unemployed" yet Stated Tenure > 0, or Loan Amount > 350% of annual income).
It generates a 0–100% Data Quality Index with itemized warning checklists.

---

### 9. Can RISKORA detect fraud?
**Answer:**
RISKORA contains an **Anomaly Detection Engine** that flags multivariate profile anomalies (such as age vs. employment tenure impossibilities, extreme leverage ratios, or thin-file prime credit disconnects).

However, in financial compliance, an anomaly is **decision-support signal**, not a legal fraud accusation. RISKORA tags these records with **"Enhanced Verification Recommended"** or **"Credit Committee Review"**, prompting underwriters to request physical documentation rather than making unverified accusations.

---

### 10. Does Fractional Lending reduce borrower default risk?
**Answer:**
**NO.** And claiming it does is a critical financial fallacy.
- **Borrower Default Risk (PD):** An intrinsic characteristic of the borrower's cash flow, debt burden, and credit habits. A borrower with a 30% default probability will still default 30% of the time, regardless of whether 1 lender or 100 lenders funded the loan.
- **Lender Exposure Concentration:** The proportion of a single lender's capital exposed to that specific asset.

Fractional syndication distributes **capital loss severity across multiple lenders**, lowering individual portfolio concentration ($HHI$). RISKORA highlights this distinction prominently.

---

### 11. Why do you need Repayment Allocation Waterfalls? How do Pro-Rata, LCF, and EFF differ?
**Answer:**
When multiple lenders fund a single loan syndicate, repayment cash flows must be allocated deterministically:
1. **Pro-Rata (Default):** Every participant receives principal and interest strictly proportional to their funded commitment share ($\text{Share}_i = \frac{C_i}{\sum C}$).
2. **Largest Contribution First (LCF):** Anchor investors who took the largest capital exposure receive prioritized principal paydown waterfall until extinguished, providing risk-mitigating liquidity to lead underwriters.
3. **Earliest Funding First (EFF):** Time-priority waterfall rewarding early commitments by paying down their principal first.

RISKORA's repayment service executes these waterfalls with penny-accurate reconciliation to prevent rounding leaks.

---

### 12. How is the model retrained and monitored in production?
**Answer:**
1. **Performance Drift Monitoring:** Tracking the Brier score and ROC-AUC over 90-day vintage windows as loans mature.
2. **Feature Drift Monitoring:** Computing Population Stability Index (PSI) and Wasserstein distance on input features ($DTI$, $Credit Score$) to detect macroeconomic shifts.
3. **Champion-Challenger Shadow Deployment:** New retrained pipelines are deployed in shadow mode, receiving live inferences alongside the champion model before formal governance promotion.
4. **Model Card Versioning:** Every report stores the exact model artifact identifier (`RISKORA-ML-LogisticRegression-v1.0`).

---

### 13. What are the limitations of the current framework?
**Answer:**
1. **Macroeconomic Shocks:** Unsupervised and supervised ML models assume stationarity in underlying loss distributions. Severe systemic shocks (e.g., pandemic lockdowns, sudden interest rate spikes) require macroeconomic stress adjustments.
2. **Unbanked Thin-File Data:** In micro-lending, alternative data (utility bills, UPI transaction flows, mobile recharge frequency) can supplement traditional bureau scores.
3. **Decision-Support Mandate:** The system is explicitly designed to assist, not autonomously execute, credit decisions without human underwriting oversight.
