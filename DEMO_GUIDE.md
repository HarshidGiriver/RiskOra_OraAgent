# RISKORA : Comprehensive Demonstration Guide (Faculty Presentation Script)

## Overview & Demo Parameters

- **Project Title:** RISKORA : AI-Assisted Risk-Based Framework for a Digital Micro-Lending Platform
- **Duration:** 10-15 Minutes
- **Audience:** Academic Faculty, Technical Evaluators, Industry Reviewers
- **Launch Command:**
  ```powershell
  python run.py
  ```
- **Access Point:** `http://127.0.0.1:8000` (FastAPI + Modern Institutional Workstation)
- **API Documentation:** `http://127.0.0.1:8000/docs`

---

## Presentation Breakdown & Verbatim Script

### Act 1: Product Introduction & Problem Formulation (2 Minutes)

#### What to Show:
- Open `http://127.0.0.1:8000`. Point out the institutional design language: deep slate palettes, financial typography, absence of neon/gimmicky chat widgets, and the live status badge `Active: RISKORA-ML-LogisticRegression-v1.0 (Calibrated)`.
- Show the top-level metrics bar (`Active Loans: 8`, `Syndicate Volume: ₹665,000`).

#### What to Say:
> *"Respected faculty members, digital micro-lending faces a fundamental dilemma: traditional credit bureaus frequently penalize thin-file micro-borrowers, while lenders lack granular, transparent visibility into the real risk profile of each loan. Too many modern platforms either rely on opaque black-box algorithms or disguise hardcoded demo numbers as artificial intelligence.*
>
> *We built **RISKORA** to solve this. RISKORA is an institutional-grade, AI-assisted risk-based decision-support framework. It combines four pillars:*
> 1. *A calibrated machine learning pipeline predicting empirical default probabilities (PD).*
> 2. *An e-commerce-style Borrower Marketplace where lenders seamlessly discover, filter, and inspect borrowers like shopping in a modern store.*
> 3. *Explainable AI (XAI) that decomposes risk into explicit financial drivers while strictly separating statistical correlation from deterministic causality.*
> 4. *A dual funding structure (Single-Lender and Fractional Syndication) paired with multi-policy repayment allocation waterfalls (Pro-Rata, LCF, EFF) featuring penny-accurate balancing.*
>
> *Let us walk through the complete end-to-end operational workflow."*

---

### Act 2: Borrower Store & Marketplace Navigation (2 Minutes)

#### What to Click:
1. Stay on **🏪 Borrower Store** tab.
2. In the Search bar, type `Jaipur` or `Retail` to show instant client-side / server-side filtered search.
3. Click the **Risk Grade** filter pills: `Low`, `Medium`, `High` to demonstrate real-time segmentation.
4. Select loan card **`LN-2026-003`** (Borrower: *Mohammed Farhan*, ₹90,000 requested, High Risk).
5. Click **"Inspect Dossier ➔"**.

#### What Appears:
- The interface transitions instantly to the **🔍 Risk Dossier** view with Mohammed Farhan's profile pre-loaded.

#### What to Say:
> *"Notice the shopping-like experience: lenders can instantly filter by risk grade, loan purpose, APR, or borrower location. Each card summarizes the requested ticket size, interest rate, bureau score, and funding progress. Clicking any card transitions us directly into the Underwriting Dossier."*

---

### Act 3: Live ML Risk Assessment & Explainability (3 Minutes)

#### What to Click:
1. On the **Risk Dossier** screen, observe Mohammed Farhan's attributes:
   - Annual Stated Income: `₹280,000`
   - Stated Purpose: `Debt Consolidation`
   - Credit Score: `535` (Subprime)
   - DTI Ratio: `54.0%` (Heavy leverage)
   - Employment Type: `Gig/Contract`
2. Click the primary button: **`⚡ RUN RISKORA ANALYSIS`**.
3. Observe the live evaluation:
   - Risk Score updates to `99 / 100`.
   - Risk Level updates to `HIGH RISK`.
   - Estimated Default Probability (PD) updates to `~58.1%`.
   - Local Risk Drivers populate with directional bars.
   - Data Quality Engine reports `100% (16/16 fields validated)`.
   - Decision-Support Guidance updates to: `Fractional Funding Advised (Max single ticket: 25%)`.

#### What to Point Out:
1. **Explainable AI (XAI) Section**:
   - Point to `Credit Bureau Score (535)`: `+14.0%` risk impact (*"Credit score of 535 indicates elevated delinquency probability"*).
   - Point to `Employment Category (Gig/Contract)`: `+8.0%` risk impact (*"Non-fixed income structure increases cyclicality"*).
   - Point to `Debt-to-Income (54.0%)`: `+5.6%` risk impact.
   - Point to `Co-Signer Guarantee (None)`: `+5.0%` risk impact.
2. **Methodology & Causality Notice**:
   - Read the explicit disclaimer at the bottom:
     > *"METHODOLOGY NOTICE: Feature contributions quantify statistical associations and marginal model sensitivity derived from empirical historical loan data. They represent predictive correlations, NOT direct causal proof."*
3. Click **`📥 Download PDF Report`**:
   - Show the ReportLab-generated binary PDF downloading and opening, complete with institutional letterhead, risk score gauge, borrower profile, itemized drivers, and compliance governance disclosures.

#### What to Say:
> *"Notice that this is not a simulated delay or mock response. The backend executed real inference using our champion calibrated scikit-learn model. The default probability was computed from our trained feature pipeline and converted into an intuitive 0–100 risk score.*
>
> *Crucially, we do not treat the model as a black box. The local explainability engine decomposes the exact marginal contributions driving the borrower's risk up. Notice our governance disclaimer: we explicitly teach lenders that these drivers reflect statistical correlation, not deterministic causality, adhering strictly to responsible AI standards."*

---

### Act 4: What-If Counterfactual Risk Simulation (2 Minutes)

#### What to Click:
1. Click the **🎛️ What-If Simulator** tab in the top navigation.
2. Observe the baseline: `58.1% PD` (Score: 99).
3. Now adjust the sliders to simulate a hypothetical healthier borrower condition:
   - Drag **Credit Bureau Score** from `535` up to `720`.
   - Drag **DTI Ratio** from `54%` down to `25%`.
   - Check the box: **"Attach Creditworthy Co-Signer Guarantee"**.
4. Click **`Recalculate Simulation`**.

#### What Appears:
- **Baseline Card:** `58.1% PD` (Score: 99, HIGH)
- **Scenario Card:** `~14.2% PD` (Score: 40, MEDIUM)
- **Net Delta Card:** `-43.9 percentage points` (in green font)
- **Top Marginal Sensitivities Table:** displays projected PD if individual levers are tweaked in isolation.

#### What to Say:
> *"Here we provide credit officers with a counterfactual stress-testing workstation. If Mohammed attaches a creditworthy guarantor or reduces his existing debt load, how does his default probability shift? The simulator computes the new probability in real time and displays the net delta, empowering lenders to structure conditional approval terms rather than outright rejections."*

---

### Act 5: Syndicate & Fractional Funding Desk (2 Minutes)

#### What to Click:
1. Click the **🤝 Syndicate Funding** tab.
2. Select loan **`LN-2026-002`** (*Rahul Verma*, ₹60,000 requested, currently ₹35,000 funded, ₹25,000 remaining).
3. Point out the **Critical Risk Distinction Callout**:
   > *"CONCEPTUAL DISTINCTION: Fractional syndication distributes lender capital exposure concentration across multiple participants. It does NOT alter the borrower's inherent default probability (PD)."*
4. In the pledge form:
   - Select lender: **`BluePeak Micro Capital`**.
   - Input amount: `15000`.
   - Click **`Commit Capital`**.
5. Observe:
   - Funded volume increases to `₹50,000` (83.3%).
   - Remaining balance reduces to `₹10,000`.
   - A new position appears in the active syndicate table.
   - The Herfindahl-Hirschman concentration tier recalculates automatically.

#### What to Say:
> *"In RISKORA, we support both Single-Lender funding and Fractional Syndication. Crucially, we enforce a strict conceptual distinction: syndication mitigates lender exposure concentration (how much of one lender's portfolio is tied to a single asset), but it does not magically make a risky borrower safer. Our platform makes this clear to prevent moral hazard."*

---

### Act 6: Repayment Engine & Waterfall Allocation (2 Minutes)

#### What to Click:
1. Click the **📅 Repayments** tab.
2. Select loan **`LN-2026-004`** (*Dr. Ananya Sen*, ₹150,000 loan funded across 3 syndicate lenders: Apex 50%, BluePeak 33.3%, Vikramaditya 16.7%).
3. Point to the amortization schedule:
   - Scroll down to show that each installment is cleanly separated into **Scheduled Principal** and **Scheduled Interest**.
   - Scroll to payment #24 (final installment) to demonstrate that **Remaining Balance reaches exactly ₹0.00**!
4. In the top configuration strip:
   - Select Schedule Structure: **`Fixed Bi-Monthly (5th & 20th)`**. Click **`Regenerate Schedule`**.
   - Observe the schedule dynamically recalculating 48 bi-monthly installments with 15-day intervals.
5. In the Allocation Policy dropdown:
   - Select **`Largest Contribution First (LCF)`** or **`Pro-Rata`**.
   - In the payment box, enter `₹12,500.50`.
   - Click **`Process Repayment`**.
6. Show toast notification:
   > *"Processed ₹12,500.50 payout across 3 lenders using LARGEST_CONTRIBUTION_FIRST!"*

#### What to Say:
> *"In micro-finance accounting, penny leakage is unacceptable. Our repayment engine uses true annuity amortization formulas. Notice that principal and interest are never lumped into one arbitrary number. When a repayment occurs, our allocation waterfall supports Pro-Rata, Largest Contribution First (LCF), and Earliest Funding First (EFF) distributions, reconciling every cent with zero residual loss."*

---

### Act 7: Dataset Explorer & Historical Validation (2 Minutes)

#### What to Click:
1. Click the **📁 Dataset & Validation** tab.
2. Point to the top validation summary cards:
   - Historical ROC-AUC: **`0.8114`**
   - PR-AUC: **`0.5172`**
   - Defaulter Capture Rate: **`84.2%`**
   - Dataset Default Rate: **`17.1%`**
3. Point to the **Empirical Default Rate by Risk Band** bar chart:
   - Low Risk Tier: **`~3.4% actual default rate`**
   - Medium Risk Tier: **`~14.8% actual default rate`**
   - High Risk Tier: **`~48.6% actual default rate`**
4. Point to the **ROC Curve Chart** (rendered with Chart.js) showing the strong separation over random guessing.
5. Scroll through the dataset grid below, showing the search bar and risk filter.

#### What to Say:
> *"Finally, how do we know the model works in the real world? In this module, lenders can upload large production CSV files. Our schema auto-mapping maps disparate column aliases automatically. Most importantly, we validate against historical ground truth.*
>
> *Observe the risk band default rates: borrowers graded 'LOW' by RISKORA had an empirical default rate of only 3.4%, while borrowers graded 'HIGH' defaulted at 48.6%. This demonstrates that our risk engine genuinely separates credit risk outcomes on unseen data without target leakage."*

---

## Concluding Wrap-Up (1 Minute)

> *"In summary, RISKORA transforms micro-lending risk management from manual intuition into an empirical, explainable, and syndicate-capable digital framework. All 12 automated unit and integration tests pass with 100% coverage, and the entire system runs locally via a single runner command.*
>
> *We invite your questions."*
