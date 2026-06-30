import os
import argparse
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, f1_score
from feature_engineering import FeaturePipeline

def main():
    parser = argparse.ArgumentParser(description='Train baseline XGBoost model for CreditLens AI')
    parser.add_argument('--quick', action='store_true', help='Train on a small sample of data for speed')
    args = parser.parse_args()

    # Paths
    raw_dir = 'home-credit-default-risk'
    app_path = os.path.join(raw_dir, 'application_train.csv')
    bureau_path = os.path.join(raw_dir, 'bureau.csv')
    prev_path = os.path.join(raw_dir, 'previous_application.csv')

    model_dir = 'data/models'
    ref_dir = 'data/reference'
    os.makedirs(model_dir, exist_ok=True)
    os.makedirs(ref_dir, exist_ok=True)

    print("Checking raw files...")
    if not os.path.exists(app_path):
        raise FileNotFoundError(f"Missing core training data file: {app_path}")

    # Set sample size for quick training
    sample_size = 20000 if args.quick else 100000
    print(f"Starting feature engineering pipeline. Subsampling {sample_size} records...")

    # Initialize feature pipeline
    pipeline = FeaturePipeline()
    X, y = pipeline.fit_transform_raw(
        app_path=app_path,
        bureau_path=bureau_path,
        prev_path=prev_path,
        sample_size=sample_size
    )

    print(f"Features shape: {X.shape}, Target shape: {y.shape}")
    print(f"Target class distribution: {np.bincount(y)}")

    # Split into train & test
    # Using stratify because of heavy class imbalance (target=1 is rare)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Compute scale_pos_weight for handling imbalance
    num_neg = np.sum(y_train == 0)
    num_pos = np.sum(y_train == 1)
    scale_pos_weight = num_neg / num_pos
    print(f"Computed scale_pos_weight: {scale_pos_weight:.4f}")

    # Train XGBoost Model
    print("Training XGBoost Classifier...")
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.08,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        eval_metric='auc',
        early_stopping_rounds=10
    )

    # Fit Model
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=10
    )

    # Evaluate Model
    preds_proba = model.predict_proba(X_test)[:, 1]
    preds = (preds_proba >= 0.5).astype(int)

    auc_score = roc_auc_score(y_test, preds_proba)
    f1 = f1_score(y_test, preds)

    print("\n--- Evaluation Results ---")
    print(f"Test ROC-AUC Score: {auc_score:.4f}")
    print(f"Test F1 Score:       {f1:.4f}")
    print("---------------------------\n")

    # Save artifacts
    model_path = os.path.join(model_dir, 'xgb_model.json')
    pipeline_path = os.path.join(model_dir, 'feature_pipeline.pkl')
    reference_path = os.path.join(ref_dir, 'reference_data.parquet')

    print(f"Saving model to {model_path}...")
    model.save_model(model_path)

    print(f"Saving feature pipeline to {pipeline_path}...")
    pipeline.save(pipeline_path)

    # Save reference data (useful for Drift Monitoring later)
    # We save a subset of test features representing the reference distribution
    print(f"Saving reference dataset to {reference_path}...")
    ref_df = X_test.copy()
    ref_df['TARGET'] = y_test.values
    ref_df.to_parquet(reference_path, index=False)

    print("Phase 1: Training completed successfully!")

if __name__ == '__main__':
    main()
