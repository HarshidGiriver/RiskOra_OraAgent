"""
RISKORA - Dataset Ingestion & Historical Validation Service
Provides robust CSV ingestion, intelligent column alias auto-mapping,
batch inference, dataset exploration (search, filter, sort, paginate),
and rigorous historical validation analytics (Confusion Matrix, ROC Curve, Risk-band Default Rates).
"""

import os
import io
import json
import sqlite3
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

from sklearn.metrics import (
    roc_auc_score, average_precision_score, confusion_matrix,
    roc_curve, precision_score, recall_score, f1_score
)

from riskora.ml.inference_engine import get_engine
from riskora.backend.database import get_db_connection

# Alias dictionary for flexible real-world CSV column mapping
COLUMN_ALIASES = {
    'loan_id': ['loan id', 'loan_id', 'id', 'loanid', 'account_no'],
    'age': ['age', 'borrower_age', 'dob_age'],
    'income': ['income_annum', 'income', 'annual_income', 'annual_inc', 'stated_income', 'salary'],
    'loan_amount': ['loan_amount', 'loan amount', 'loan_amnt', 'requested_amount', 'principal'],
    'credit_score': ['cibil_score', 'credit score', 'credit_score', 'fico', 'bureau_score', 'cibil'],
    'months_employed': ['months employed', 'months_employed', 'emp_length_months', 'tenure_months'],
    'number_of_credit_lines': ['number of credit lines', 'number_of_credit_lines', 'credit_lines', 'open_acc'],
    'interest_rate': ['interest rate', 'interest_rate', 'int_rate', 'apr', 'rate'],
    'loan_term': ['loan_term', 'loan term', 'term', 'term_months', 'duration'],
    'dti_ratio': ['dti ratio', 'dti_ratio', 'dti', 'debt_to_income'],
    'education': ['education', 'education_level', 'academic_qualification'],
    'employment_type': ['self_employed', 'employment type', 'employment_type', 'emp_type', 'occupation_type'],
    'marital_status': ['marital status', 'marital_status'],
    'has_mortgage': ['residential_assets_value', 'residential_assets', 'has mortgage', 'has_mortgage', 'mortgage'],
    'has_dependents': ['no_of_dependents', 'has dependents', 'has_dependents', 'dependents'],
    'loan_purpose': ['loan purpose', 'loan_purpose', 'purpose'],
    'has_co_signer': ['has co-signer', 'has_co_signer', 'cosigner', 'has_guarantor'],
    'commercial_assets': ['commercial_assets_value', 'commercial_assets'],
    'luxury_assets': ['luxury_assets_value', 'luxury_assets'],
    'bank_assets': ['bank_asset_value', 'bank_assets'],
    'default': ['loan_status', 'default', 'loan_status_default', 'is_default', 'bad_loan', 'delinquent']
}

def map_dataframe_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """Maps arbitrary incoming CSV headers to standardized Riskora feature names."""
    normalized_cols = {c.strip().lower(): c for c in df.columns}
    mapping = {}

    target_names = {
        'loan_id': 'Loan ID',
        'age': 'Age',
        'income': 'Income',
        'loan_amount': 'Loan Amount',
        'credit_score': 'Credit Score',
        'months_employed': 'Months Employed',
        'number_of_credit_lines': 'Number of Credit Lines',
        'interest_rate': 'Interest Rate',
        'loan_term': 'Loan Term',
        'dti_ratio': 'DTI Ratio',
        'education': 'Education',
        'employment_type': 'Employment Type',
        'marital_status': 'Marital Status',
        'has_mortgage': 'Has Mortgage',
        'has_dependents': 'Has Dependents',
        'loan_purpose': 'Loan Purpose',
        'has_co_signer': 'Has Co-Signer',
        'commercial_assets': 'commercial_assets_value',
        'luxury_assets': 'luxury_assets_value',
        'bank_assets': 'bank_asset_value',
        'default': 'Default'
    }

    rename_dict = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        standard_name = target_names[canonical]
        for alias in aliases:
            if alias in normalized_cols:
                raw_col = normalized_cols[alias]
                rename_dict[raw_col] = standard_name
                mapping[standard_name] = raw_col
                break

    mapped_df = df.rename(columns=rename_dict)
    return mapped_df, mapping

class DatasetManager:
    _instance = None
    _active_df: Optional[pd.DataFrame] = None
    _dataset_metadata: Dict[str, Any] = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = DatasetManager()
            cls._instance._load_default_benchmark()
        return cls._instance

    def _load_default_benchmark(self):
        kaggle_path = "riskora/data/loan_approval_dataset.csv"
        if os.path.exists(kaggle_path):
            df = pd.read_csv(kaggle_path)
            self.process_and_score_dataset(df, "loan_approval_dataset.csv")
            return
        benchmark_path = "riskora/data/microlending_benchmark.csv"
        if os.path.exists(benchmark_path):
            df = pd.read_csv(benchmark_path)
            self.process_and_score_dataset(df, "microlending_benchmark.csv")

    def process_and_score_dataset(self, raw_df: pd.DataFrame, filename: str) -> Dict[str, Any]:
        """
        Ingests, maps, validates, executes batch inference, and produces historical validation.
        STRICT TARGET LEAKAGE PREVENTION: 'Default' / 'loan_status' is NEVER fed into prediction!
        """
        clean_raw = raw_df.copy()
        clean_raw.columns = clean_raw.columns.str.strip()

        # Extract ground truth label before mapping if available
        default_label = None
        for col in clean_raw.columns:
            if col.lower() == 'loan_status':
                default_label = (clean_raw[col].astype(str).str.strip().str.lower() == 'rejected').astype(int)
                break
            elif col.lower() in ['default', 'is_default', 'bad_loan', 'loan_status_default']:
                default_label = pd.to_numeric(clean_raw[col], errors='coerce').fillna(0).astype(int)
                break

        mapped_df, mapping = map_dataframe_columns(clean_raw)
        if default_label is not None:
            mapped_df['Default'] = default_label

        if 'Loan ID' not in mapped_df.columns:
            mapped_df['Loan ID'] = [f"LN-DS-{1000 + i}" for i in range(len(mapped_df))]

        engine = get_engine()
        from riskora.ml.train_models import ALL_INPUT_FEATURES

        clean_inputs = []
        for _, row in mapped_df.iterrows():
            inc = float(row.get('Income') or row.get('income_annum') or 400000)
            amt = float(row.get('Loan Amount') or row.get('loan_amount') or 50000)
            term = int(row.get('Loan Term') or row.get('loan_term') or 12)
            cibil = float(row.get('Credit Score') or row.get('cibil_score') or 650)
            deps = int(row.get('Has Dependents') or row.get('no_of_dependents') or 1)

            res = float(row.get('residential_assets_value') or (float(row.get('Has Mortgage', 0) or 0) * 1500000) or 1200000)
            com = float(row.get('commercial_assets_value') or 600000)
            lux = float(row.get('luxury_assets_value') or 400000)
            bnk = float(row.get('bank_asset_value') or 300000)

            tot = res + com + lux + bnk
            asset_ratio = tot / max(amt, 1.0)
            lti = amt / max(inc, 1.0)

            edu = str(row.get('Education') or row.get('education') or 'Graduate').strip()
            self_emp_raw = str(row.get('Employment Type') or row.get('self_employed') or 'No').strip().lower()
            self_emp = 'Yes' if self_emp_raw in ['yes', 'self-employed', '1', 'true'] else 'No'

            clean_inputs.append({
                'income_annum': inc,
                'loan_amount': amt,
                'loan_term': term,
                'cibil_score': cibil,
                'no_of_dependents': deps,
                'residential_assets_value': res,
                'commercial_assets_value': com,
                'luxury_assets_value': lux,
                'bank_asset_value': bnk,
                'total_assets': tot,
                'asset_to_loan_ratio': asset_ratio,
                'loan_to_income': lti,
                'education': edu,
                'self_employed': self_emp
            })

        batch_df = pd.DataFrame(clean_inputs)
        probs = engine.pipeline.predict_proba(batch_df[ALL_INPUT_FEATURES])[:, 1]
        probs = np.clip(probs, 0.01, 0.98)

        risk_scores = np.clip(probs * 100.0, 5, 99).astype(int)

        thresholds = engine.model_card.get('risk_thresholds', {
            "low_risk_max_pd": 0.15,
            "medium_risk_max_pd": 0.40,
            "high_risk_min_pd": 0.40
        })

        risk_levels = []
        for p in probs:
            if p <= thresholds["low_risk_max_pd"]:
                risk_levels.append("LOW")
            elif p <= thresholds["medium_risk_max_pd"]:
                risk_levels.append("MEDIUM")
            else:
                risk_levels.append("HIGH")

        mapped_df['Riskora_PD'] = np.round(probs, 4)
        mapped_df['Riskora_Score'] = risk_scores
        mapped_df['Riskora_Level'] = risk_levels

        has_default_label = 'Default' in mapped_df.columns and not mapped_df['Default'].isna().all()

        validation_metrics = {}
        if has_default_label:
            y_true = mapped_df['Default'].dropna().astype(int).values
            y_prob = mapped_df.loc[mapped_df['Default'].dropna().index, 'Riskora_PD'].values
            y_pred_high = (mapped_df.loc[mapped_df['Default'].dropna().index, 'Riskora_Level'] == 'HIGH').astype(int)

            roc_auc = roc_auc_score(y_true, y_prob)
            pr_auc = average_precision_score(y_true, y_prob)
            cm = confusion_matrix(y_true, y_pred_high)

            # Risk-Band Default Rates (Demonstrates Monotonic Outcome Separation!)
            band_rates = {}
            for band in ['LOW', 'MEDIUM', 'HIGH']:
                subset = mapped_df[mapped_df['Riskora_Level'] == band]
                if len(subset) > 0 and 'Default' in subset.columns:
                    rate = subset['Default'].mean()
                    band_rates[band] = {
                        "count": len(subset),
                        "actual_default_rate": round(float(rate) * 100, 2),
                        "avg_predicted_pd": round(float(subset['Riskora_PD'].mean()) * 100, 2)
                    }

            # Downsampled ROC curve
            fpr, tpr, _ = roc_curve(y_true, y_prob)
            step = max(1, len(fpr) // 30)
            roc_pts = [
                {"fpr": round(float(fpr[i]), 4), "tpr": round(float(tpr[i]), 4)}
                for i in range(0, len(fpr), step)
            ]

            # High Risk Capture Rate (Defaulters identified in HIGH or MEDIUM risk)
            caught = mapped_df[
                (mapped_df['Default'] == 1) &
                (mapped_df['Riskora_Level'].isin(['HIGH', 'MEDIUM']))
            ]
            total_defaulters = max(1, (mapped_df['Default'] == 1).sum())
            high_medium_capture_rate = round((len(caught) / total_defaulters) * 100, 2)

            validation_metrics = {
                "has_ground_truth": True,
                "overall_default_rate": round(float(np.mean(y_true)) * 100, 2),
                "roc_auc": round(float(roc_auc), 4),
                "pr_auc": round(float(pr_auc), 4),
                "high_medium_capture_rate": high_medium_capture_rate,
                "confusion_matrix": {
                    "tn": int(cm[0, 0]),
                    "fp": int(cm[0, 1]),
                    "fn": int(cm[1, 0]),
                    "tp": int(cm[1, 1])
                },
                "risk_band_default_rates": band_rates,
                "roc_curve": roc_pts
            }
        else:
            validation_metrics = {
                "has_ground_truth": False,
                "message": "Dataset does not contain a historical 'Default' label. Risk scores were inferred objectively."
            }

        self._active_df = mapped_df
        self._dataset_metadata = {
            "filename": filename,
            "ingested_at": datetime.now(timezone.utc).isoformat(),
            "total_records": len(mapped_df),
            "column_mapping": mapping,
            "has_default_label": has_default_label,
            "validation_metrics": validation_metrics
        }

        return self._dataset_metadata

    def query_dataset(
        self,
        search: Optional[str] = None,
        risk_level: Optional[str] = None,
        min_score: Optional[int] = None,
        max_score: Optional[int] = None,
        sort_by: str = "Riskora_Score",
        sort_desc: bool = True,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Provides fast, memory-safe pagination, search, and filtering over dataset."""
        if self._active_df is None:
            return {"total": 0, "rows": [], "metadata": {}}

        df = self._active_df.copy()

        if search:
            s = search.strip().lower()
            mask = df['Loan ID'].astype(str).str.lower().str.contains(s)
            if 'Loan Purpose' in df.columns:
                mask = mask | df['Loan Purpose'].astype(str).str.lower().str.contains(s)
            df = df[mask]

        if risk_level and risk_level.upper() != "ALL":
            df = df[df['Riskora_Level'] == risk_level.upper()]

        if min_score is not None:
            df = df[df['Riskora_Score'] >= min_score]

        if max_score is not None:
            df = df[df['Riskora_Score'] <= max_score]

        total_rows = len(df)

        if sort_by in df.columns:
            df = df.sort_values(by=sort_by, ascending=not sort_desc)

        page_df = df.iloc[offset: offset + limit]

        # Convert to list of dicts with NaN replaced
        records = page_df.replace({np.nan: None}).to_dict(orient='records')

        return {
            "total": total_rows,
            "limit": limit,
            "offset": offset,
            "rows": records,
            "metadata": self._dataset_metadata
        }

def get_dataset_manager() -> DatasetManager:
    return DatasetManager.get_instance()
