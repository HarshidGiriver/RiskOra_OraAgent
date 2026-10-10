# RISKORA : Model Card: RISKORA-ML-CalibratedRandomForest-v1.0

## 1. Model Details

- **Model Identifier:** `RISKORA-ML-LogisticRegression-v1.0`
- **Model Family:** Calibrated Linear Model for Credit Risk Default Prediction
- **Framework:** Scikit-Learn 1.9.x
- **Pipeline Architecture:**
  - `ColumnTransformer` with `SimpleImputer` (median for numerical, most frequent for categorical)
  - `StandardScaler` for continuous numerical ratios
  - `OneHotEncoder` with `handle_unknown='ignore'` for categorical attributes
  - Estimator: `LogisticRegression(class_weight='balanced', C=0.5, max_iter=500)`
  - Calibrator: `CalibratedClassifierCV(method='sigmoid', cv=3)`
- **Artifact Path:** `riskora/data/champion_model.joblib`
- **Metadata Path:** `riskora/data/model_card.json`
- **Release Date:** October 2026
- **License:** Proprietary / Financial Institutional License

---

## 2. Intended Use & Scope

### 2.1 Intended Use
- **Primary Intent:** Decision-support tool for institutional lenders, credit officers, and alternative finance syndicates evaluating digital micro-loans.
- **Outputs:** Continuous calibrated Probability of Default ($PD \in [0.015, 0.95]$), Credit Risk Score ($0 - 100$), Risk Band assignment (`LOW`, `MEDIUM`, `HIGH`), and local feature attribution drivers.

### 2.2 Out-of-Scope & Prohibited Uses
- **Autonomous Credit Decisioning:** The model is strictly **NOT** an autonomous decision-maker. It must never issue automated, unreviewed loan rejections without human underwriter concurrence.
- **Corporate / Sovereign Debt:** Calibrated specifically for digital unsecured and semi-secured micro-loans up to ₹500,000. It must not be applied to large corporate syndicated loans or mortgage portfolios without recalibration.
- **Unverified Profile Substitution:** Cannot be used as a substitute for institutional Know-Your-Customer (KYC) or statutory Anti-Money Laundering (AML) verification.

---

## 3. Training & Benchmark Dataset

- **Dataset Identifier:** `microlending_benchmark.csv`
- **Total Records:** 6,000 synthetic micro-lending records modeled on authentic empirical credit risk distributions.
- **Default Rate:** ~17.1% historical default frequency.
- **Feature Set:** 16 attributes spanning demographic stability (Age, Marital Status), economic capacity (Income, DTI Ratio, Employment Tenure), bureau history (Credit Bureau Score, Number of Credit Lines), and loan structure (Loan Amount, APR, Term, Purpose, Co-Signer).

---

## 4. Performance & Evaluation Metrics

Performance evaluated on an unseen holdout test split (1,500 records, 25% holdout):

| Metric | Holdout Value | Benchmark Significance |
| :--- | :--- | :--- |
| **ROC-AUC** | **0.8114** | Strong discriminative ability in ranking defaulters above non-defaulters. |
| **PR-AUC (Average Precision)** | **0.5172** | Substantial precision improvement over the 17.1% baseline default prevalence. |
| **Brier Score Loss** | **0.1102** | Indicates tight calibration between predicted probabilities and empirical outcomes. |
| **Cost-Weighted Recall ($\tau = 0.22$)** | **65.76%** | High capture rate of potential defaulters at an underwriting risk threshold. |
| **Cost-Weighted F1 Score ($\tau = 0.22$)** | **0.5280** | Balanced trade-off penalizing false negatives in credit underwriting. |

### Confusion Matrix (Test Set, $\tau = 0.22$):
- **True Negatives (TN):** 1,023 (Low/Medium risk correctly classified)
- **False Positives (FP):** 220 (Conservatively flagged for enhanced review)
- **False Negatives (FN):** 88 (Unpredicted defaults)
- **True Positives (TP):** 169 (Defaulters successfully identified)

---

## 5. Fairness, Bias, & Responsible AI Analysis

1. **Exclusion of Sensitive Attributes:**
   - Features such as caste, religion, race, gender, and sexual orientation are strictly excluded from the model pipeline.
2. **Mitigation of Age Disparities:**
   - Age is strictly validated for legal eligibility (18–80) and scaled with median imputation. Model attribution discloses that employment tenure and DTI, rather than raw age, dominate feature importance.
3. **Correlation vs. Causation Separation:**
   - Every risk dossier and PDF export explicitly communicates that feature contributions represent empirical statistical associations, not deterministic proof of cause.

---

## 6. Caveats & Limitations

- **Macroeconomic Sensitivity:** The model assumes steady-state macroeconomic conditions. Significant external shocks (e.g., severe inflation surges, sudden liquidity freezes) require macro stress-testing adjustments.
- **Alternative Data Expansion:** Future model iterations will incorporate cash flow transaction velocity (e.g. UPI flow data) to further enhance accuracy for thin-file borrowers.
