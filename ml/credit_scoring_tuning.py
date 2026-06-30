"""
CreditLens AI — Hyperparameter Tuning & GPU Training Pipeline
Designed for execution on Kaggle Notebooks or Google Colab (with free T4 GPU).

This script uses Optuna to find optimal hyperparameters for XGBoost on the Home Credit dataset,
utilizes GPU-accelerated histogram tree method, and saves the final production-ready model.
"""

import os
import pandas as pd
import numpy as np
import xgboost as xgb
import optuna
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
import pickle

# Optuna logger settings
optuna.logging.set_verbosity(optuna.logging.WARNING)

def train_and_evaluate(params, X, y, cv):
    """Runs cross-validation training on GPU and returns average validation ROC-AUC."""
    auc_scores = []
    
    for train_idx, val_idx in cv.split(X, y):
        X_tr, y_tr = X.iloc[train_idx], y.iloc[train_idx]
        X_va, y_va = X.iloc[val_idx], y.iloc[val_idx]
        
        # Instantiate model with parameters
        model = xgb.XGBClassifier(**params)
        
        # Fit model
        model.fit(
            X_tr, y_tr,
            eval_set=[(X_va, y_va)],
            verbose=False
        )
        
        # Predict on validation fold
        preds_proba = model.predict_proba(X_va)[:, 1]
        fold_auc = roc_auc_score(y_va, preds_proba)
        auc_scores.append(fold_auc)
        
    return np.mean(auc_scores)

def objective(trial, X, y, cv, scale_pos_weight):
    """Optuna objective function to maximize cross-validation ROC-AUC."""
    # Define hyperparameter search space
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 100, 800, step=50),
        'max_depth': trial.suggest_int('max_depth', 3, 10),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.2, log=True),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
        'min_child_weight': trial.suggest_int('min_child_weight', 1, 20),
        'scale_pos_weight': scale_pos_weight, # Fixed to handle class imbalance
        'random_state': 42,
        'eval_metric': 'auc',
        'early_stopping_rounds': 30,
        
        # Activate GPU Acceleration on Kaggle/Colab
        # XGBoost v2.0+ uses 'device' parameter. Older versions use 'tree_method'
        'device': 'cuda', 
        'tree_method': 'hist' 
    }
    
    return train_and_evaluate(params, X, y, cv)

def main():
    # 1. Paths configuration (Kaggle dataset mounts to /kaggle/input/...)
    # Adjust paths if running locally or on Kaggle
    raw_dir = '../input/home-credit-default-risk' if os.path.exists('/kaggle') else 'home-credit-default-risk'
    
    app_path = os.path.join(raw_dir, 'application_train.csv')
    bureau_path = os.path.join(raw_dir, 'bureau.csv')
    prev_path = os.path.join(raw_dir, 'previous_application.csv')
    
    # Import FeaturePipeline from local file if uploaded to Kaggle
    # Otherwise, copy feature_engineering.py code directly to the notebook cell
    try:
        from ml.feature_engineering import FeaturePipeline
    except ImportError:
        # Fallback if executing as independent script on Kaggle
        from feature_engineering import FeaturePipeline

    print("--- Starting CreditLens AI Kaggle Training ---")
    if not os.path.exists(app_path):
        print(f"Error: Missing core data at {app_path}. Please check Kaggle input mount.")
        return

    # 2. Run feature engineering (using full dataset since we have high-end cloud CPU/GPU)
    print("Running feature engineering pipeline on full dataset...")
    pipeline = FeaturePipeline()
    X, y = pipeline.fit_transform_raw(
        app_path=app_path,
        bureau_path=bureau_path,
        prev_path=prev_path,
        sample_size=None # Train on full dataset
    )
    print(f"Full Dataset Features: {X.shape}, Labels: {y.shape}")

    # 3. Calculate class imbalance weight
    num_neg = np.sum(y == 0)
    num_pos = np.sum(y == 1)
    scale_pos_weight = num_neg / num_pos
    print(f"Calculated scale_pos_weight: {scale_pos_weight:.4f}")

    # 4. Setup Stratified Cross-Validation
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)

    # 5. Initialize Optuna Study
    print("Initializing Optuna study...")
    study = optuna.create_study(direction='maximize')
    
    # Run optimization study
    print("Running 30 Optuna trials on GPU...")
    study.optimize(
        lambda trial: objective(trial, X, y, cv, scale_pos_weight),
        n_trials=30
    )

    print("\n--- Optuna Study Completed ---")
    print(f"Best Trial Score (Validation ROC-AUC): {study.best_value:.4f}")
    print("Best Trial Hyperparameters:")
    for k, v in study.best_params.items():
        print(f"  {k}: {v}")
    print("--------------------------------\n")

    # 6. Train Final Production Model with Best Hyperparameters
    print("Training final production model on full dataset...")
    best_params = study.best_params
    best_params['scale_pos_weight'] = scale_pos_weight
    best_params['random_state'] = 42
    best_params['eval_metric'] = 'auc'
    best_params['device'] = 'cuda'
    best_params['tree_method'] = 'hist'

    final_model = xgb.XGBClassifier(**best_params)
    
    # Simple split to do early stopping validation on final fit
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.1, random_state=42, stratify=y
    )
    
    final_model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=50
    )

    # 7. Save Final Artifacts
    os.makedirs('output', exist_ok=True)
    model_out = 'output/xgb_model.json'
    pipeline_out = 'output/feature_pipeline.pkl'
    ref_out = 'output/reference_data.parquet'

    print(f"Saving final XGBoost model to {model_out}...")
    final_model.save_model(model_out)

    print(f"Saving feature pipeline to {pipeline_out}...")
    pipeline.save(pipeline_out)

    # Save reference test data (to be used for drift calculations)
    print(f"Saving baseline reference data to {ref_out}...")
    X_val['TARGET'] = y_val.values
    X_val.to_parquet(ref_out, index=False)

    print("Kaggle training pipeline completed! Please download the 'output' directory files.")

if __name__ == '__main__':
    from sklearn.model_selection import train_test_split
    main()
