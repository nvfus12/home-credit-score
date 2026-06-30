import os
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import classification_report, roc_curve, precision_recall_curve, auc
import matplotlib.pyplot as plt

def main():
    model_path = 'data/models/xgb_model.json'
    ref_path = 'data/reference/reference_data.parquet'

    if not os.path.exists(model_path) or not os.path.exists(ref_path):
        print("Error: Missing model or reference data. Run ml/train.py first.")
        return

    print("Loading model and reference test data...")
    model = xgb.XGBClassifier()
    model.load_model(model_path)

    ref_df = pd.read_parquet(ref_path)
    X_test = ref_df.drop(columns=['TARGET'])
    y_test = ref_df['TARGET']

    # Predict
    preds_proba = model.predict_proba(X_test)[:, 1]
    preds = (preds_proba >= 0.5).astype(int)

    # Performance
    print("\n--- Model Performance Report ---")
    print(classification_report(y_test, preds))

    # ROC Curve & PR Curve
    fpr, tpr, _ = roc_curve(y_test, preds_proba)
    roc_auc = auc(fpr, tpr)

    precision, recall, _ = precision_recall_curve(y_test, preds_proba)
    pr_auc = auc(recall, precision)

    print(f"ROC-AUC Score: {roc_auc:.4f}")
    print(f"PR-AUC Score:  {pr_auc:.4f}")
    print("--------------------------------\n")

if __name__ == '__main__':
    main()
