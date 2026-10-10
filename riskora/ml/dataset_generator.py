"""
RISKORA - Benchmark Dataset Generator
Generates realistic, statistically rigorous digital micro-lending datasets
with genuine default dynamics, non-linear relationships, multi-collinearities,
and realistic data quality flaws for testing.
"""

import numpy as np
import pandas as pd
import os
from typing import Tuple

def generate_microlending_dataset(
    n_samples: int = 6000,
    random_state: int = 42,
    include_anomalies: bool = True
) -> pd.DataFrame:
    """
    Generates a realistic digital micro-lending dataset.
    Target variable: 'Default' (0 = Repaid, 1 = Defaulted).
    Realistic default rate: ~13.5%.
    """
    np.random.seed(random_state)

    # 1. Base Demographic & Employment Features
    age = np.random.normal(loc=36, scale=10, size=n_samples).astype(int)
    age = np.clip(age, 19, 72)

    education_levels = ['High School', 'Associate', 'Bachelor', 'Master', 'Doctorate']
    education = np.random.choice(education_levels, size=n_samples, p=[0.35, 0.25, 0.28, 0.10, 0.02])

    employment_types = ['Salaried', 'Self-Employed', 'Gig/Contract', 'Unemployed']
    employment_type = np.random.choice(employment_types, size=n_samples, p=[0.55, 0.25, 0.15, 0.05])

    marital_statuses = ['Single', 'Married', 'Divorced']
    marital_status = np.random.choice(marital_statuses, size=n_samples, p=[0.38, 0.50, 0.12])

    has_dependents = np.random.choice([0, 1], size=n_samples, p=[0.45, 0.55])
    has_mortgage = np.random.choice([0, 1], size=n_samples, p=[0.70, 0.30])
    has_co_signer = np.random.choice([0, 1], size=n_samples, p=[0.82, 0.18])

    # 2. Financial Metrics (Income, Credit Score, Employment Duration)
    base_income = {
        'High School': 240000,
        'Associate': 340000,
        'Bachelor': 520000,
        'Master': 780000,
        'Doctorate': 1100000
    }
    income_multiplier = {
        'Salaried': 1.0,
        'Self-Employed': 1.1,
        'Gig/Contract': 0.75,
        'Unemployed': 0.25
    }

    income = np.zeros(n_samples)
    for i in range(n_samples):
        b = base_income[education[i]] * income_multiplier[employment_type[i]]
        inc = np.random.lognormal(mean=np.log(b), sigma=0.35)
        income[i] = round(inc, -2)

    income = np.clip(income, 50000, 3000000)

    # Months employed correlated with age
    max_possible_months = (age - 18) * 12
    months_employed = np.zeros(n_samples, dtype=int)
    for i in range(n_samples):
        if employment_type[i] == 'Unemployed':
            months_employed[i] = 0
        else:
            mean_months = min(max_possible_months[i], 48 + (age[i] - 25) * 3)
            mean_months = max(mean_months, 3)
            val = int(np.random.exponential(scale=mean_months))
            months_employed[i] = min(val, max_possible_months[i])

    # Credit Score (300 - 850)
    score_mean = 630 + (age - 35) * 1.5 + (np.log(income) - 12) * 18
    credit_score = np.random.normal(loc=score_mean, scale=55).astype(int)
    credit_score = np.clip(credit_score, 320, 840)

    # Number of credit lines (1 - 25)
    credit_lines = np.random.poisson(lam=4.5 + (credit_score - 500) / 70, size=n_samples)
    credit_lines = np.clip(credit_lines, 1, 24)

    # 3. Micro-Loan Parameters
    loan_purposes = [
        'Business Expansion', 'Inventory Purchase', 'Equipment Purchase',
        'Working Capital', 'Medical Emergency', 'Education', 'Debt Consolidation'
    ]
    loan_purpose = np.random.choice(loan_purposes, size=n_samples, p=[0.24, 0.22, 0.16, 0.14, 0.08, 0.08, 0.08])

    # Requested Loan Amount based on income and purpose
    loan_amount = np.zeros(n_samples)
    for i in range(n_samples):
        pct = np.random.uniform(0.08, 0.45)
        la = income[i] * pct
        la = round(la / 5000) * 5000
        loan_amount[i] = max(10000, min(la, 300000))

    # Loan term (months): 6, 12, 18, 24, 36
    loan_terms = [6, 12, 18, 24, 36]
    loan_term = np.random.choice(loan_terms, size=n_samples, p=[0.15, 0.45, 0.20, 0.15, 0.05])

    # Interest rate (%): 12.0% - 28.0% based on credit score risk
    base_interest = 24.0 - ((credit_score - 400) / 450) * 11.0 + np.random.normal(0, 1.2, n_samples)
    interest_rate = np.clip(base_interest, 11.5, 29.5)
    interest_rate = np.round(interest_rate, 2)

    # Debt-To-Income (DTI) ratio
    monthly_income = income / 12.0
    r = interest_rate / 100.0 / 12.0
    monthly_installment = loan_amount * (r * (1 + r)**loan_term) / ((1 + r)**loan_term - 1)
    existing_debt_ratio = np.random.uniform(0.05, 0.40, size=n_samples)
    existing_debt_ratio += has_mortgage * 0.12

    dti_ratio = existing_debt_ratio + (monthly_installment / monthly_income)
    dti_ratio = np.clip(dti_ratio, 0.08, 0.85)
    dti_ratio = np.round(dti_ratio, 3)

    # 4. Latent Default Probability Modeling (Log-Odds Formulation)
    loan_to_income = loan_amount / income

    z = (
        - 2.80                                              # baseline log-odds (~6% base)
        + 3.8 * (dti_ratio - 0.32)                          # DTI sensitivity
        - 0.012 * (credit_score - 640)                     # Credit score sensitivity
        + 1.8 * (loan_to_income - 0.22)                     # Loan-to-income sensitivity
        - 0.008 * np.minimum(months_employed, 60)          # Employment stability
        - 0.65 * has_co_signer                              # Co-signer protection
        + 0.40 * (employment_type == 'Gig/Contract')
        + 1.20 * (employment_type == 'Unemployed')
        + 0.08 * (interest_rate - 18.0)                     # Interest debt burden
        + 0.25 * (loan_term >= 24)                          # Longer duration exposure
        + 0.20 * (has_dependents == 1)
        - 0.15 * (has_mortgage == 1)                        # Property owners have slightly more stability
    )

    # Severe risk interaction
    severe_risk_interaction = ((credit_score < 580).astype(int) * (dti_ratio > 0.45).astype(int)) * 0.95
    z += severe_risk_interaction

    true_pd = 1.0 / (1.0 + np.exp(-z))
    true_pd = np.clip(true_pd, 0.01, 0.95)

    default = (np.random.uniform(0, 1, size=n_samples) < true_pd).astype(int)
    loan_ids = [f"RK-{10000 + i}" for i in range(n_samples)]

    df = pd.DataFrame({
        'Loan ID': loan_ids,
        'Age': age,
        'Income': income.astype(int),
        'Loan Amount': loan_amount.astype(int),
        'Credit Score': credit_score,
        'Months Employed': months_employed,
        'Number of Credit Lines': credit_lines,
        'Interest Rate': interest_rate,
        'Loan Term': loan_term,
        'DTI Ratio': dti_ratio,
        'Education': education,
        'Employment Type': employment_type,
        'Marital Status': marital_status,
        'Has Mortgage': has_mortgage,
        'Has Dependents': has_dependents,
        'Loan Purpose': loan_purpose,
        'Has Co-Signer': has_co_signer,
        'Default': default
    })

    if include_anomalies:
        dq_indices = np.random.choice(n_samples, size=int(n_samples * 0.02), replace=False)
        for idx in dq_indices[:len(dq_indices)//2]:
            df.loc[idx, 'Months Employed'] = np.nan
        for idx in dq_indices[len(dq_indices)//2:]:
            df.loc[idx, 'DTI Ratio'] = np.nan

    return df

def ensure_dataset_exists(output_path: str = "riskora/data/microlending_benchmark.csv") -> str:
    """Ensures benchmark dataset is generated and saved."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if not os.path.exists(output_path):
        print(f"Generating benchmark dataset at {output_path}...")
        df = generate_microlending_dataset(n_samples=6000, random_state=42)
        df.to_csv(output_path, index=False)
        print(f"Dataset successfully created: {len(df)} records, Default Rate: {df['Default'].mean():.2%}")
    return output_path

if __name__ == "__main__":
    path = ensure_dataset_exists()
    df = pd.read_csv(path)
    print("Dataset Summary:")
    print(df.info())
    print("\nTarget Distribution:")
    print(df['Default'].value_counts(normalize=True))
