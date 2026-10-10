# RISKORA : Machine Learning & Risk Intelligence Pipeline Specification

## 1. Executive Summary

The RISKORA Machine Learning subsystem is an empirical, calibrated classification pipeline designed for imbalanced digital micro-lending default prediction. It replaces ad-hoc scorecards and black-box APIs with a reproducible, calibrated scikit-learn pipeline featuring full local explainability and strict target leakage prevention.

---

## 2. Feature Engineering & Preprocessing Architecture

```
Raw Loan Record (16 Fields)
     │
     ├── Numerical: Age, Income, Loan Amount, Credit Score, Months Employed,
     │              Number of Credit Lines, Interest Rate, Loan Term, DTI Ratio
     ├── Categorical: Education, Employment Type, Marital Status, Loan Purpose
     └── Binary: Has Mortgage, Has Dependents, Has Co-Signer
     │
     ▼
Domain Feature Engineering
     ├── Loan_to_Income = Loan Amount / max(Income, 1.0)
     └── DTI Interaction terms
     │
     ▼
Scikit-Learn ColumnTransformer
     ├── Numerical Pipeline:
     │     └── SimpleImputer(strategy='median') ➔ StandardScaler()
     ├── Categorical Pipeline:
     │     └── SimpleImputer(strategy='most_frequent') ➔ OneHotEncoder(handle_unknown='ignore')
     └── Binary Pipeline:
           └── SimpleImputer(strategy='most_frequent')
     │
     ▼
Calibrated Classifier Pipeline
     └── Sigmoid CalibratedClassifierCV (3-Fold Stratified Split)
```

---

## 3. Candidate Model Evaluation & Selection

The experiment pipeline compared three distinct classifier families on the stratified 75/25 train/holdout split:

| Model Architecture | Calibration | ROC-AUC | PR-AUC | Brier Score Loss | Recall ($\tau = 0.22$) | Selection Result |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Logistic Regression (L2, Balanced)** | Sigmoid CV | **0.8114** | **0.5172** | **0.1102** | **65.76%** | **CHAMPION SELECTED** |
| **Random Forest (80 Trees, Balanced)** | Sigmoid CV | 0.8087 | 0.5324 | 0.1094 | 63.42% | Challenger |
| **HistGradientBoosting (80 Iterations)** | Sigmoid CV | 0.8056 | 0.5405 | 0.1102 | 65.76% | Challenger |

### Model Selection Rationale
1. **Calibration & Ranking Quality:** Logistic Regression achieved the highest ROC-AUC (0.8114) and strong probability calibration (Brier score 0.1102).
2. **Monotonicity & Regulatory Auditability:** In financial micro-lending, monotonic stability is critical: as credit score drops or DTI rises, predicted risk must not fluctuate erratically due to tree leaf splits.
3. **Zero Inference Latency:** Executes inference in under 5 milliseconds on standard CPU hardware.

---

## 4. Probability Calibration Methodology

Raw outputs from tree models or uncalibrated classifiers often produce distorted probabilities under class imbalance. RISKORA applies **Sigmoid Probability Calibration (`CalibratedClassifierCV`)**:

$$P(y = 1 \mid f(x)) = \frac{1}{1 + \exp(A \cdot f(x) + B)}$$

Parameters $A$ and $B$ are estimated via maximum likelihood on cross-validated validation folds. This ensures that when RISKORA predicts a **15% default probability**, approximately **15 out of 100 borrowers** in that cohort actually default historically.

---

## 5. Risk Score & Band Mapping

To provide intuitive decision support, calibrated PD ($PD \in [0.015, 0.95]$) is scaled into an integer **Credit Risk Score (0–100)**:

$$\text{RiskScore} = \text{round}\left(\text{clip}\left(\frac{PD}{0.32} \times 100, 5, 99\right)\right)$$

### Decision Thresholds:
- **LOW RISK ($PD \le 8\%$):** Score 5–25. High creditworthiness. Single-lender funding eligible (up to 100% single ticket). Standard documentation.
- **MEDIUM RISK ($8\% < PD \le 22\%$):** Score 26–65. Moderate risk. Fractional syndication advised (max single ticket: 50%). Secondary document verification.
- **HIGH RISK ($PD > 22\%$):** Score 66–99. Elevated loss probability. Fractional syndication strictly advised (max single ticket: 25%). Enhanced verification and credit committee review.

---

## 6. Explainable AI (XAI) & Attribution Mathematics

Local feature contributions are calculated relative to population medians $\bar{x}$:
$$\Delta \text{Impact}_j = w_j \cdot (x_j - \bar{x}_j)$$

The system ranks the top 5 contributors by absolute magnitude and translates them into plain-language risk factors with explicit positive/negative impact indicators.

### Governance Statement on Causality
> **Methodology Notice:** All feature attributions quantify statistical correlations and marginal model sensitivities. They do **not** assert deterministic causality. RISKORA acts as an advisory decision-support tool to augment human underwriting expertise.
