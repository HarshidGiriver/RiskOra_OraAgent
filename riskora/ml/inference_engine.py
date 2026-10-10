"""
RISKORA - Real-Time Inference Engine
Loads calibrated champion ML model trained on the Kaggle Loan Approval dataset,
executes real inference, and assembles comprehensive risk intelligence.
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from riskora.ml.train_models import (
    ALL_INPUT_FEATURES, engineer_kaggle_features, train_and_evaluate_models
)
from riskora.ml.data_quality import assess_data_quality
from riskora.ml.anomaly_detector import detect_anomalies
from riskora.ml.explainability import generate_risk_drivers, CAUSALITY_DISCLOSURE

MODEL_ARTIFACT_PATH = "riskora/data/champion_model.joblib"
MODEL_CARD_PATH = "riskora/data/model_card.json"

class RiskoraInferenceEngine:
    _instance = None

    def __init__(self):
        self.pipeline = None
        self.model_card = {}
        self._ensure_model_ready()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = RiskoraInferenceEngine()
        return cls._instance

    def _ensure_model_ready(self):
        """Ensures champion model exists or triggers training."""
        if not os.path.exists(MODEL_ARTIFACT_PATH) or not os.path.exists(MODEL_CARD_PATH):
            print("Champion model artifact not found. Initializing training pipeline...", flush=True)
            self.model_card = train_and_evaluate_models()
        else:
            with open(MODEL_CARD_PATH, "r") as f:
                self.model_card = json.load(f)

        self.pipeline = joblib.load(MODEL_ARTIFACT_PATH)
        print(f"Riskora Inference Engine ready. Active Model: {self.model_card.get('model_name')}", flush=True)

    def analyze_loan(self, loan_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes real ML inference and full risk intelligence pipeline on a single loan.
        """
        # 1. Evaluate Data Quality
        dq_results = assess_data_quality(loan_record)

        # 2. Evaluate Multivariate Anomalies
        anomaly_results = detect_anomalies(loan_record)

        # 3. Format input for Kaggle ML model
        income = float(loan_record.get('income_annum') or loan_record.get('Income') or 400000)
        loan_amt = float(loan_record.get('loan_amount') or loan_record.get('Loan Amount') or 50000)
        loan_term = int(loan_record.get('loan_term') or loan_record.get('Loan Term') or 12)
        cibil = float(loan_record.get('cibil_score') or loan_record.get('Credit Score') or 650)
        deps = int(loan_record.get('no_of_dependents') or loan_record.get('Has Dependents') or 1)

        res_assets = float(loan_record.get('residential_assets_value') or (loan_record.get('has_mortgage', 0) * 1500000) or 1200000)
        com_assets = float(loan_record.get('commercial_assets_value') or 600000)
        lux_assets = float(loan_record.get('luxury_assets_value') or 400000)
        bnk_assets = float(loan_record.get('bank_asset_value') or 300000)

        total_assets = res_assets + com_assets + lux_assets + bnk_assets
        asset_ratio = total_assets / max(loan_amt, 1.0)
        loan_to_income = loan_amt / max(income, 1.0)

        clean_dict = {
            'income_annum': income,
            'loan_amount': loan_amt,
            'loan_term': loan_term,
            'cibil_score': cibil,
            'no_of_dependents': deps,
            'residential_assets_value': res_assets,
            'commercial_assets_value': com_assets,
            'luxury_assets_value': lux_assets,
            'bank_asset_value': bnk_assets,
            'total_assets': total_assets,
            'asset_to_loan_ratio': asset_ratio,
            'loan_to_income': loan_to_income,
            'education': str(loan_record.get('education') or 'Graduate').strip(),
            'self_employed': str(loan_record.get('self_employed') or ('Yes' if loan_record.get('Employment Type') == 'Self-Employed' else 'No')).strip()
        }

        input_df = pd.DataFrame([clean_dict])

        # 4. Real Calibrated ML Inference
        prob_default = float(self.pipeline.predict_proba(input_df[ALL_INPUT_FEATURES])[0, 1])
        prob_default = min(0.98, max(0.01, prob_default))

        # 5. Determine Calibrated Risk Score & Band
        # Risk Score is 0 - 100 where higher indicates higher risk
        risk_score = int(round(np.clip(prob_default * 100.0, 5, 99)))

        thresholds = self.model_card.get('risk_thresholds', {
            "low_risk_max_pd": 0.15,
            "medium_risk_max_pd": 0.40,
            "high_risk_min_pd": 0.40
        })

        if prob_default <= thresholds["low_risk_max_pd"]:
            risk_level = "LOW"
            recommended_max_exposure = 1.00
        elif prob_default <= thresholds["medium_risk_max_pd"]:
            risk_level = "MEDIUM"
            recommended_max_exposure = 0.50
        else:
            risk_level = "HIGH"
            recommended_max_exposure = 0.25

        # 6. Generate Explainability Drivers
        risk_drivers = generate_risk_drivers(clean_dict, prob_default)

        # 7. Formulate Final Intelligence Package
        timestamp_str = datetime.now(timezone.utc).isoformat()

        return {
            "loan_id": str(loan_record.get("Loan ID") or loan_record.get("loan_id", "UNKNOWN")),
            "assessment_timestamp": timestamp_str,
            "model_version": self.model_card.get("model_name", "RISKORA-ML-RandomForest-v1.0"),
            "probability_of_default": round(prob_default, 4),
            "probability_pct": round(prob_default * 100.0, 2),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "recommended_review_intensity": anomaly_results["recommended_review_intensity"],
            "funding_recommendation": {
                "structure_advice": "Fractional Funding Advised" if risk_level in ["MEDIUM", "HIGH"] else "Single-Lender or Fractional",
                "max_single_ticket_pct": round(recommended_max_exposure * 100, 0),
                "rationale": "High-risk profiles benefit from syndication to distribute lender portfolio exposure."
            },
            "risk_drivers": risk_drivers,
            "data_quality": dq_results,
            "anomaly_analysis": anomaly_results,
            "methodology_disclaimer": CAUSALITY_DISCLOSURE
        }

def get_engine() -> RiskoraInferenceEngine:
    return RiskoraInferenceEngine.get_instance()
