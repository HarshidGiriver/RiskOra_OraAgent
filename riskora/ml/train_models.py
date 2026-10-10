"""
RISKORA - Multi-Model Training, Calibration, Evaluation, and Selection Pipeline
Trained directly on the Kaggle Loan Approval Prediction Dataset (4,269 records).
Applies probability calibration, feature attribution, and generates model cards.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import (
    roc_auc_score, average_precision_score, brier_score_loss,
    f1_score, precision_score, recall_score, confusion_matrix,
    roc_curve, accuracy_score
)

KAGGLE_DATASET_PATH = "riskora/data/loan_approval_dataset.csv"

NUMERICAL_FEATURES = [
    'income_annum', 'loan_amount', 'loan_term', 'cibil_score',
    'no_of_dependents', 'residential_assets_value', 'commercial_assets_value',
    'luxury_assets_value', 'bank_asset_value', 'total_assets',
    'asset_to_loan_ratio', 'loan_to_income'
]

CATEGORICAL_FEATURES = [
    'education', 'self_employed'
]

ALL_INPUT_FEATURES = NUMERICAL_FEATURES + CATEGORICAL_FEATURES

def engineer_kaggle_features(df: pd.DataFrame) -> pd.DataFrame:
    """Preprocesses and engineers leverage and asset coverage ratios from Kaggle data."""
    data = df.copy()
    data.columns = data.columns.str.strip()

    # Asset totals
    res_val = data['residential_assets_value'] if 'residential_assets_value' in data else 0
    com_val = data['commercial_assets_value'] if 'commercial_assets_value' in data else 0
    lux_val = data['luxury_assets_value'] if 'luxury_assets_value' in data else 0
    bnk_val = data['bank_asset_value'] if 'bank_asset_value' in data else 0

    data['total_assets'] = res_val + com_val + lux_val + bnk_val
    data['asset_to_loan_ratio'] = data['total_assets'] / np.maximum(data['loan_amount'], 1.0)
    data['loan_to_income'] = data['loan_amount'] / np.maximum(data['income_annum'], 1.0)

    # Encode target: Rejected = 1 (Risk / Default proxy), Approved = 0 (Repaid / Creditworthy)
    if 'loan_status' in data.columns:
        data['Default'] = (data['loan_status'].astype(str).str.strip().str.lower() == 'rejected').astype(int)

    # Categorical normalization
    if 'education' in data.columns:
        data['education'] = data['education'].astype(str).str.strip()
    if 'self_employed' in data.columns:
        data['self_employed'] = data['self_employed'].astype(str).str.strip()

    return data

def build_preprocessor() -> ColumnTransformer:
    """Builds scikit-learn column transformer for numeric and categorical inputs."""
    numeric_pipe = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])

    categorical_pipe = Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])

    return ColumnTransformer(
        transformers=[
            ('num', numeric_pipe, NUMERICAL_FEATURES),
            ('cat', categorical_pipe, CATEGORICAL_FEATURES)
        ],
        remainder='drop'
    )

def train_and_evaluate_models(dataset_path: str = KAGGLE_DATASET_PATH) -> Dict[str, Any]:
    """Runs end-to-end model comparison, calibration, and selection on Kaggle dataset."""
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset not found at {dataset_path}!")

    print(f"Loading Kaggle dataset from {dataset_path}...", flush=True)
    raw_df = pd.read_csv(dataset_path)
    df = engineer_kaggle_features(raw_df)

    X = df[ALL_INPUT_FEATURES]
    y = df['Default'].values

    # Stratified Train/Test Split (75% Train/Val, 25% Holdout Test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    print(f"Dataset Size: {len(df)} records. Training: {len(X_train)}, Test: {len(X_test)}", flush=True)
    print(f"Empirical Rejection / Default Rate: {np.mean(y):.2%}", flush=True)

    # Define Candidate Classifiers
    candidates = {
        "Logistic Regression": LogisticRegression(
            class_weight='balanced',
            C=1.0,
            max_iter=500,
            random_state=42
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            min_samples_leaf=4,
            class_weight='balanced',
            random_state=42,
            n_jobs=1
        ),
        "Gradient Boosting": HistGradientBoostingClassifier(
            max_iter=100,
            max_depth=6,
            min_samples_leaf=20,
            class_weight='balanced',
            random_state=42
        )
    }

    results = {}
    best_score = -1.0
    champion_name = None
    champion_pipeline = None

    preprocessor = build_preprocessor()

    for name, clf in candidates.items():
        print(f"\n--- Training Candidate: {name} ---", flush=True)
        base_pipe = Pipeline([
            ('preprocessor', preprocessor),
            ('clf', clf)
        ])

        # Calibrate probabilities using 3-fold cross validation
        calibrated_clf = CalibratedClassifierCV(
            estimator=base_pipe,
            method='sigmoid',
            cv=3
        )

        calibrated_clf.fit(X_train, y_train)

        # Predict probabilities on unseen holdout test set
        y_prob = calibrated_clf.predict_proba(X_test)[:, 1]

        roc_auc = roc_auc_score(y_test, y_prob)
        pr_auc = average_precision_score(y_test, y_prob)
        brier = brier_score_loss(y_test, y_prob)

        # Business threshold at 0.35 (standard credit loss balancing)
        business_threshold = 0.35
        y_pred_biz = (y_prob >= business_threshold).astype(int)
        cm = confusion_matrix(y_test, y_pred_biz)

        prob_true, prob_pred = calibration_curve(y_test, y_prob, n_bins=8)
        fpr, tpr, _ = roc_curve(y_test, y_prob)

        step = max(1, len(fpr) // 30)
        roc_points = [
            {"fpr": round(float(fpr[i]), 4), "tpr": round(float(tpr[i]), 4)}
            for i in range(0, len(fpr), step)
        ]

        metrics = {
            "roc_auc": round(float(roc_auc), 4),
            "pr_auc": round(float(pr_auc), 4),
            "brier_score": round(float(brier), 4),
            "accuracy": round(float(accuracy_score(y_test, y_pred_biz)), 4),
            "precision_biz": round(float(precision_score(y_test, y_pred_biz, zero_division=0)), 4),
            "recall_biz": round(float(recall_score(y_test, y_pred_biz)), 4),
            "f1_biz": round(float(f1_score(y_test, y_pred_biz)), 4),
            "business_threshold": business_threshold,
            "confusion_matrix": {
                "tn": int(cm[0, 0]),
                "fp": int(cm[0, 1]),
                "fn": int(cm[1, 0]),
                "tp": int(cm[1, 1])
            },
            "calibration_curve": [
                {"pred": round(float(p), 4), "true": round(float(t), 4)}
                for p, t in zip(prob_pred, prob_true)
            ],
            "roc_curve": roc_points
        }

        print(f"Results for {name}:", flush=True)
        print(f"  ROC-AUC: {metrics['roc_auc']} | PR-AUC: {metrics['pr_auc']} | Brier Score: {metrics['brier_score']} | Accuracy: {metrics['accuracy']:.2%}", flush=True)

        results[name] = metrics

        composite = roc_auc - (brier * 0.5)
        if composite > best_score:
            best_score = composite
            champion_name = name
            champion_pipeline = calibrated_clf

    print(f"\n==========================================", flush=True)
    print(f"CHAMPION MODEL SELECTED: {champion_name} (Composite Score: {best_score:.4f})", flush=True)
    print(f"==========================================", flush=True)

    # Fit uncalibrated base pipeline for direct feature importances
    base_model = candidates[champion_name]
    fitted_base_pipe = Pipeline([
        ('preprocessor', preprocessor),
        ('clf', base_model)
    ])
    fitted_base_pipe.fit(X_train, y_train)

    feature_importance_list = []
    try:
        ohe = fitted_base_pipe.named_steps['preprocessor'].named_transformers_['cat'].named_steps['encoder']
        cat_feature_names = list(ohe.get_feature_names_out(CATEGORICAL_FEATURES))
        feature_names = NUMERICAL_FEATURES + cat_feature_names

        clf_step = fitted_base_pipe.named_steps['clf']
        if hasattr(clf_step, 'feature_importances_'):
            importances = clf_step.feature_importances_
        elif hasattr(clf_step, 'coef_'):
            importances = np.abs(clf_step.coef_[0])
        else:
            importances = np.ones(len(feature_names)) / len(feature_names)

        high_level_importances = {}
        for fname, imp in zip(feature_names, importances):
            root_name = fname
            for cat in CATEGORICAL_FEATURES:
                if fname.startswith(f"{cat}_"):
                    root_name = cat
                    break
            high_level_importances[root_name] = high_level_importances.get(root_name, 0.0) + imp

        total_imp = sum(high_level_importances.values()) or 1.0
        feature_importance_list = [
            {"feature": k, "importance": round(float(v / total_imp), 4)}
            for k, v in sorted(high_level_importances.items(), key=lambda x: x[1], reverse=True)
        ]
    except Exception as e:
        print(f"Warning computing feature importances: {e}")

    # Persist artifacts
    os.makedirs("riskora/data", exist_ok=True)
    joblib.dump(champion_pipeline, "riskora/data/champion_model.joblib")
    joblib.dump(fitted_base_pipe, "riskora/data/base_feature_model.joblib")

    model_card = {
        "model_name": f"RISKORA-ML-{champion_name.replace(' ', '')}-v1.0",
        "champion_architecture": champion_name,
        "version": "1.0.0",
        "dataset_name": "Kaggle Loan Approval Prediction Dataset (architsharma01)",
        "total_training_records": len(df),
        "calibration_method": "Sigmoid CalibratedClassifierCV (3-Fold)",
        "evaluation_metrics": results,
        "feature_importances": feature_importance_list,
        "input_features": ALL_INPUT_FEATURES,
        "risk_thresholds": {
            "low_risk_max_pd": 0.15,
            "medium_risk_max_pd": 0.40,
            "high_risk_min_pd": 0.40
        },
        "score_mapping": {
            "description": "Risk Score (0 - 100). Higher score indicates higher probability of default/rejection.",
            "formula": "RiskScore = round(clip(PD * 100 / 0.50, 0, 100))"
        }
    }

    with open("riskora/data/model_card.json", "w") as f:
        json.dump(model_card, f, indent=2)

    print("Model Card written to riskora/data/model_card.json", flush=True)
    return model_card

if __name__ == "__main__":
    train_and_evaluate_models()
