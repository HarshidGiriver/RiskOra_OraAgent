# RISKORA : Data Dictionary & Ingestion Specification

## 1. Core Feature Specification

| Field Name | Type | Valid Range / Categories | Description | Default Alias Mapping |
| :--- | :--- | :--- | :--- | :--- |
| **Loan ID** | String | Alphanumeric (e.g. `RK-10001`) | Unique loan transaction identifier | `loan_id`, `id`, `account_no` |
| **Age** | Integer | 18 to 80 | Age of borrower in completed years | `age`, `borrower_age` |
| **Income** | Float | ₹10,000 to ₹50,000,000 | Stated annual borrower earnings | `income`, `annual_income`, `annual_inc`, `salary` |
| **Loan Amount** | Float | ₹5,000 to ₹500,000 | Total micro-loan principal requested | `loan_amount`, `loan_amnt`, `principal`, `amount` |
| **Credit Score** | Integer | 300 to 850 | Credit bureau creditworthiness score | `credit_score`, `fico`, `bureau_score`, `cibil` |
| **Months Employed** | Integer | 0 to 600 | Continuous employment tenure in months | `months_employed`, `emp_length_months`, `tenure` |
| **Number of Credit Lines** | Integer | 1 to 35 | Active or historical credit trade lines | `number_of_credit_lines`, `credit_lines`, `open_acc` |
| **Interest Rate** | Float | 8.0% to 48.0% | Annual Percentage Rate (APR) | `interest_rate`, `int_rate`, `apr`, `rate` |
| **Loan Term** | Integer | 3 to 60 months | Repayment duration in months | `loan_term`, `term`, `term_months`, `duration` |
| **DTI Ratio** | Float | 0.05 to 1.50 | Debt-to-Income obligation ratio | `dti_ratio`, `dti`, `debt_to_income` |
| **Education** | String | High School, Associate, Bachelor, Master, Doctorate | Highest completed educational level | `education`, `education_level`, `qualification` |
| **Employment Type** | String | Salaried, Self-Employed, Gig/Contract, Unemployed | Primary income generation sector | `employment_type`, `emp_type`, `occupation` |
| **Marital Status** | String | Single, Married, Divorced | Legal domestic status | `marital_status` |
| **Has Mortgage** | Binary | 0 or 1 | Real-estate home mortgage indicator | `has_mortgage`, `mortgage`, `home_ownership` |
| **Has Dependents** | Binary | 0 or 1 | Household financial dependents indicator | `has_dependents`, `dependents` |
| **Loan Purpose** | String | Business Expansion, Inventory Purchase, Equipment Purchase, Working Capital, Medical Emergency, Education, Debt Consolidation | Declared economic intent of loan | `loan_purpose`, `purpose` |
| **Has Co-Signer** | Binary | 0 or 1 | Enforceable secondary guarantor agreement | `has_co_signer`, `has_cosigner`, `cosigner`, `guarantor` |
| **Default** *(Supervision Only)* | Binary | 0 or 1 | 90+ day charge-off or default status *(Never fed as input feature)* | `default`, `loan_status_default`, `bad_loan` |

---

## 2. Engineered Ratios

| Derived Metric | Formula | Financial Significance |
| :--- | :--- | :--- |
| **Loan_to_Income** | $\frac{\text{Loan Amount}}{\max(\text{Income}, 1.0)}$ | Quantifies annual debt leverage taken in a single transaction. Values $>0.40$ heavily escalate loss exposure. |
| **Monthly Installment** | $P \cdot \frac{r(1+r)^n}{(1+r)^n - 1}$ | Baseline cash flow obligation required for debt servicing. |
| **Herfindahl Index (HHI)** | $\sum_{i=1}^M \left(\frac{C_i}{\sum C}\right)^2$ | Syndicate concentration index (0.0 = perfectly atomized, 1.0 = single-lender monopoly). |

---

## 3. Data Quality Engine Rules

1. **Completeness:** Verifies presence of all 16 required input fields. Missing attributes deduct 12 quality points each.
2. **Boundary Validation:**
   - Age $<18$ or $>80$: 15-point penalty.
   - Income $\le 0$: 25-point penalty.
   - Credit score $<300$ or $>850$: 20-point penalty.
   - DTI $<0.0$ or $>2.0$: 15-point penalty.
3. **Cross-Field Contradictions:**
   - Status = `Unemployed` with `Months Employed > 0`: 15-point penalty.
   - `Loan Amount > (3.5 * Income)`: 15-point leverage warning penalty.
4. **Grading Tiers:**
   - Score $\ge 88$: **PASS**
   - Score $65 - 87$: **ACCEPTABLE_WITH_WARNINGS**
   - Score $< 65$: **CRITICAL_DEFICIENCIES**
