"""
CreditLens AI — Unified Kaggle GPU Training & Optuna Tuning Script

Tại sao không dùng SMOTE để xử lý mất cân bằng dữ liệu trong chấm điểm tín dụng?
1. Làm sai lệch phân phối tài chính thực tế: Dữ liệu tài chính dạng bảng có tính tương quan cao giữa các cột (ví dụ: Thu nhập cao tương ứng với Khoản vay lớn).
   SMOTE tạo ra các điểm dữ liệu mới bằng cách nội suy tuyến tính, điều này rất dễ tạo ra các ca giả lập phi thực tế (ví dụ: Thu nhập = 0 nhưng có Khoản vay = 10 tỷ).
2. Chi phí tính toán cực kỳ lớn: Tạo mẫu ảo cho hàng trăm ngàn dòng dữ liệu trên máy tính rất dễ gây tràn bộ nhớ (RAM).
3. Thiếu tính minh giải pháp lý (Auditability): Trong ngành ngân hàng, các quyết định tín dụng phải giải trình được trước pháp luật.
   Sử dụng scale_pos_weight chỉ điều chỉnh trọng số tổn thất (loss weights) của mô hình chứ không can thiệp tạo ra dữ liệu ảo, giúp mô hình minh bạch và an toàn khi kiểm toán.

Hướng dẫn chạy trên Kaggle:
1. Tạo mới 1 Kaggle Notebook.
2. Thêm Dataset "Home Credit Default Risk" vào notebook (Kaggle sẽ mount vào thư mục `../input/home-credit-default-risk`).
3. Bật cấu hình tăng tốc GPU T4 (Accelerator: GPU T4 x2 hoặc GPU T4).
4. Copy toàn bộ nội dung file này dán vào 1 ô (cell) trong Kaggle Notebook.
5. Chạy (Run) ô đó.
6. Sau khi chạy xong, tải 3 tệp kết quả trong mục output:
   - `xgb_model.json`
   - `feature_pipeline.pkl`
   - `reference_data.parquet`
   và ghi đè vào thư mục `data/` cục bộ trên máy của bạn.
"""

import os
import pandas as pd
import numpy as np
import xgboost as xgb
import optuna
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import LabelEncoder
import pickle

# =====================================================================
# PART 1: FEATURE ENGINEERING PIPELINE (From ml/feature_engineering.py)
# =====================================================================

class FeaturePipeline:
    def __init__(self):
        self.label_encoders = {}
        self.categorical_cols = [
            'NAME_EDUCATION_TYPE', 
            'NAME_HOUSING_TYPE'
        ]
        self.feature_columns = []

    def fit_transform_raw(self, app_path, bureau_path, prev_path, sample_size=None):
        print("Loading application_train.csv...")
        app_df = pd.read_csv(app_path)
        if sample_size:
            app_df = app_df.sample(n=sample_size, random_state=42).reset_index(drop=True)

        # 1. Feature Engineering on Main Application
        app_df['applicant_age'] = -app_df['DAYS_BIRTH'] / 365.25
        
        # Handle Days Employed anomaly
        app_df['DAYS_EMPLOYED'] = app_df['DAYS_EMPLOYED'].replace(365243, np.nan)
        app_df['employment_years'] = -app_df['DAYS_EMPLOYED'] / 365.25
        app_df['employment_years'] = app_df['employment_years'].fillna(0)

        # Financial Ratios
        app_df['loan_to_income_ratio'] = app_df['AMT_CREDIT'] / (app_df['AMT_INCOME_TOTAL'] + 1)
        app_df['annuity_to_income_ratio'] = app_df['AMT_ANNUITY'] / (app_df['AMT_INCOME_TOTAL'] + 1)
        app_df['credit_to_goods_ratio'] = app_df['AMT_CREDIT'] / (app_df['AMT_GOODS_PRICE'] + 1)
        app_df['income_per_person'] = app_df['AMT_INCOME_TOTAL'] / (app_df['CNT_CHILDREN'] + 2)
        app_df['payment_rate'] = app_df['AMT_ANNUITY'] / (app_df['AMT_CREDIT'] + 1)

        # External Sources
        ext_sources = ['EXT_SOURCE_1', 'EXT_SOURCE_2', 'EXT_SOURCE_3']
        app_df['external_source_mean'] = app_df[ext_sources].mean(axis=1)
        app_df['external_source_std'] = app_df[ext_sources].std(axis=1).fillna(0)

        # 2. Aggregations on Bureau Data (CIC)
        if os.path.exists(bureau_path):
            print("Loading and aggregating bureau.csv...")
            bureau_df = pd.read_csv(bureau_path)
            bureau_df = bureau_df[bureau_df['SK_ID_CURR'].isin(app_df['SK_ID_CURR'])]

            bureau_df['is_active'] = (bureau_df['CREDIT_ACTIVE'] == 'Active').astype(int)
            bureau_df['AMT_CREDIT_SUM'] = pd.to_numeric(bureau_df['AMT_CREDIT_SUM'], errors='coerce').fillna(0)
            bureau_df['AMT_CREDIT_SUM_DEBT'] = pd.to_numeric(bureau_df['AMT_CREDIT_SUM_DEBT'], errors='coerce').fillna(0)

            bureau_agg = bureau_df.groupby('SK_ID_CURR').agg(
                bureau_loans_active=('is_active', 'sum'),
                bureau_overdue_count=('CREDIT_DAY_OVERDUE', lambda x: (x > 0).sum()),
                bureau_total_credit=('AMT_CREDIT_SUM', 'sum'),
                bureau_total_debt=('AMT_CREDIT_SUM_DEBT', 'sum')
            ).reset_index()

            bureau_agg['bureau_debt_to_credit_ratio'] = bureau_agg['bureau_total_debt'] / (bureau_agg['bureau_total_credit'] + 1)
            bureau_agg = bureau_agg.drop(columns=['bureau_total_credit', 'bureau_total_debt'])

            app_df = app_df.merge(bureau_agg, on='SK_ID_CURR', how='left')
        else:
            app_df['bureau_loans_active'] = 0
            app_df['bureau_overdue_count'] = 0
            app_df['bureau_debt_to_credit_ratio'] = 0.0

        app_df['bureau_loans_active'] = app_df['bureau_loans_active'].fillna(0)
        app_df['bureau_overdue_count'] = app_df['bureau_overdue_count'].fillna(0)
        app_df['bureau_debt_to_credit_ratio'] = app_df['bureau_debt_to_credit_ratio'].fillna(0.0)

        # 3. Aggregations on Previous Applications
        if os.path.exists(prev_path):
            print("Loading and aggregating previous_application.csv...")
            prev_df = pd.read_csv(prev_path)
            prev_df = prev_df[prev_df['SK_ID_CURR'].isin(app_df['SK_ID_CURR'])]

            prev_df['is_approved'] = (prev_df['NAME_CONTRACT_STATUS'] == 'Approved').astype(int)
            prev_agg = prev_df.groupby('SK_ID_CURR').agg(
                prev_application_count=('SK_ID_PREV', 'count'),
                prev_approved_sum=('is_approved', 'sum')
            ).reset_index()
            prev_agg['prev_approved_ratio'] = prev_agg['prev_approved_sum'] / (prev_agg['prev_application_count'] + 1e-5)
            prev_agg = prev_agg.drop(columns=['prev_approved_sum'])

            app_df = app_df.merge(prev_agg, on='SK_ID_CURR', how='left')
        else:
            app_df['prev_application_count'] = 0
            app_df['prev_approved_ratio'] = 0.0

        app_df['prev_application_count'] = app_df['prev_application_count'].fillna(0)
        app_df['prev_approved_ratio'] = app_df['prev_approved_ratio'].fillna(0.0)

        # 4. Handle Categorical Columns
        for col in self.categorical_cols:
            if col in app_df.columns:
                le = LabelEncoder()
                app_df[col] = app_df[col].fillna('Unknown')
                app_df[col] = le.fit_transform(app_df[col].astype(str))
                self.label_encoders[col] = le

        model_cols = [
            'applicant_age', 'income_total', 'employment_years', 
            'loan_amount', 'loan_annuity', 'goods_price', 
            'num_children', 'NAME_EDUCATION_TYPE', 'NAME_HOUSING_TYPE',
            'bureau_loans_active', 'bureau_overdue_count',
            'prev_application_count', 'prev_approved_ratio',
            'EXT_SOURCE_1', 'EXT_SOURCE_2', 'EXT_SOURCE_3',
            'loan_to_income_ratio', 'annuity_to_income_ratio', 
            'credit_to_goods_ratio', 'external_source_mean', 'external_source_std',
            'income_per_person', 'payment_rate', 'bureau_debt_to_credit_ratio'
        ]
        
        rename_map = {
            'AMT_INCOME_TOTAL': 'income_total',
            'AMT_CREDIT': 'loan_amount',
            'AMT_ANNUITY': 'loan_annuity',
            'AMT_GOODS_PRICE': 'goods_price',
            'CNT_CHILDREN': 'num_children',
            'EXT_SOURCE_1': 'EXT_SOURCE_1',
            'EXT_SOURCE_2': 'EXT_SOURCE_2',
            'EXT_SOURCE_3': 'EXT_SOURCE_3'
        }
        app_df = app_df.rename(columns=rename_map)
        self.feature_columns = model_cols
        
        target = app_df['TARGET'] if 'TARGET' in app_df.columns else None
        features_df = app_df[model_cols].copy()
        
        for col in features_df.columns:
            if col not in self.categorical_cols:
                features_df[col] = pd.to_numeric(features_df[col], errors='coerce')

        return features_df, target

    def transform_single(self, input_dict):
        df = pd.DataFrame([input_dict])
        df['applicant_age'] = float(df.get('applicant_age', [30])[0])
        df['income_total'] = float(df.get('income_total', [50000])[0])
        df['employment_years'] = float(df.get('employment_years', [2])[0])
        df['loan_amount'] = float(df.get('loan_amount', [100000])[0])
        df['loan_annuity'] = float(df.get('loan_annuity', [5000])[0])
        df['goods_price'] = float(df.get('goods_price', [100000])[0])
        df['num_children'] = int(df.get('num_children', [0])[0])
        
        for col in ['EXT_SOURCE_1', 'EXT_SOURCE_2', 'EXT_SOURCE_3']:
            val = df.get(col, [np.nan])[0]
            df[col] = float(val) if val is not None and not pd.isna(val) else np.nan

        df['loan_to_income_ratio'] = df['loan_amount'] / (df['income_total'] + 1)
        df['annuity_to_income_ratio'] = df['loan_annuity'] / (df['income_total'] + 1)
        df['credit_to_goods_ratio'] = df['loan_amount'] / (df['goods_price'] + 1)
        df['income_per_person'] = df['income_total'] / (df['num_children'] + 2)
        df['payment_rate'] = df['loan_annuity'] / (df['loan_amount'] + 1)
        
        ext_sources = [df['EXT_SOURCE_1'].iloc[0], df['EXT_SOURCE_2'].iloc[0], df['EXT_SOURCE_3'].iloc[0]]
        valid_ext = [x for x in ext_sources if not pd.isna(x)]
        df['external_source_mean'] = np.mean(valid_ext) if len(valid_ext) > 0 else np.nan
        df['external_source_std'] = np.std(valid_ext) if len(valid_ext) > 0 else 0.0

        df['bureau_loans_active'] = float(df.get('bureau_loans_active', [0])[0])
        df['bureau_overdue_count'] = float(df.get('bureau_overdue_count', [0])[0])
        df['bureau_debt_to_credit_ratio'] = float(df.get('bureau_debt_to_credit_ratio', [0.0])[0])
        df['prev_application_count'] = float(df.get('prev_application_count', [0])[0])
        df['prev_approved_ratio'] = float(df.get('prev_approved_ratio', [0.0])[0])

        for col in self.categorical_cols:
            val = str(df.get(col, ['Unknown'])[0])
            le = self.label_encoders.get(col)
            if le:
                if val not in le.classes_:
                    val = 'Unknown' if 'Unknown' in le.classes_ else le.classes_[0]
                df[col] = le.transform([val])[0]
            else:
                df[col] = 0

        return df[self.feature_columns]

    def save(self, path):
        with open(path, 'wb') as f:
            pickle.dump(self, f)


# =====================================================================
# PART 2: OPTUNA TUNING & GPU TRAINING LOOP (5-Fold CV & Regularization)
# =====================================================================

optuna.logging.set_verbosity(optuna.logging.WARNING)

def train_and_evaluate(params, X, y, cv):
    auc_scores = []
    train_losses = []
    val_losses = []
    for train_idx, val_idx in cv.split(X, y):
        X_tr, y_tr = X.iloc[train_idx], y.iloc[train_idx]
        X_va, y_va = X.iloc[val_idx], y.iloc[val_idx]
        
        model = xgb.XGBClassifier(**params)
        model.fit(
            X_tr, y_tr,
            eval_set=[(X_tr, y_tr), (X_va, y_va)],
            verbose=False
        )
        
        # Extract losses
        evals = model.evals_result()
        best_iter = model.best_iteration if hasattr(model, 'best_iteration') and model.best_iteration is not None else len(evals['validation_0']['logloss']) - 1
        
        train_losses.append(evals['validation_0']['logloss'][best_iter])
        val_losses.append(evals['validation_1']['logloss'][best_iter])
        
        preds_proba = model.predict_proba(X_va)[:, 1]
        auc_scores.append(roc_auc_score(y_va, preds_proba))
        
    return np.mean(auc_scores), np.mean(train_losses), np.mean(val_losses)

def objective(trial, X, y, cv, scale_pos_weight):
    # Dynamic early stopping and regularization params
    learning_rate = trial.suggest_float('learning_rate', 0.01, 0.2, log=True)
    
    # Smaller learning rates require longer training and longer early stopping wait times
    early_stopping_rounds = max(30, int(1.5 / learning_rate))

    params = {
        'n_estimators': trial.suggest_int('n_estimators', 200, 3000, step=50),
        'max_depth': trial.suggest_int('max_depth', 3, 10),
        'learning_rate': learning_rate,
        'subsample': trial.suggest_float('subsample', 0.3, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.3, 1.0),
        'min_child_weight': trial.suggest_int('min_child_weight', 1, 20),
        
        # New regularization parameters
        'gamma': trial.suggest_float('gamma', 1e-3, 10.0, log=True),
        'reg_lambda': trial.suggest_float('reg_lambda', 1e-3, 10.0, log=True),
        'reg_alpha': trial.suggest_float('reg_alpha', 1e-3, 10.0, log=True),
        
        'scale_pos_weight': scale_pos_weight,
        'random_state': 42,
        'eval_metric': ['logloss', 'auc'],
        'early_stopping_rounds': early_stopping_rounds,
        
        # GPU Speedup Configuration
        'device': 'cuda', 
        'tree_method': 'hist' 
    }
    
    mean_auc, train_loss, val_loss = train_and_evaluate(params, X, y, cv)
    
    # Draw custom text progress bar (Total 50 trials)
    total_trials = 50
    bar_length = 20
    filled_len = int(round(bar_length * (trial.number + 1) / total_trials))
    bar = '█' * filled_len + '-' * (bar_length - filled_len)
    pct = f"{((trial.number + 1) / total_trials) * 100:.0f}%"
    
    print(f"Trial {trial.number+1:02d}/{total_trials} | [{bar}] {pct} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Mean CV ROC-AUC: {mean_auc:.4f}")
    return mean_auc

def main():
    raw_dir = '/kaggle/input/competitions/home-credit-default-risk' if os.path.exists('/kaggle') else 'home-credit-default-risk'
    
    app_path = os.path.join(raw_dir, 'application_train.csv')
    bureau_path = os.path.join(raw_dir, 'bureau.csv')
    prev_path = os.path.join(raw_dir, 'previous_application.csv')
    
    print("--- Starting CreditLens AI Unified Kaggle GPU Training ---")
    if not os.path.exists(app_path):
        print(f"Error: Missing core data at {app_path}. Did you add the Home Credit dataset to Kaggle Notebook?")
        return

    # 1. Feature Engineering
    pipeline = FeaturePipeline()
    X, y = pipeline.fit_transform_raw(
        app_path=app_path,
        bureau_path=bureau_path,
        prev_path=prev_path,
        sample_size=None # Train on full 300,000 dataset
    )
    print(f"Engineered Dataset Shape: {X.shape}")

    # 2. Imbalance Calculation
    num_neg = np.sum(y == 0)
    num_pos = np.sum(y == 1)
    scale_pos_weight = num_neg / num_pos
    print(f"Class imbalance weight (scale_pos_weight): {scale_pos_weight:.4f}")

    # 3. Optuna Optimization (50 trials, 5-Fold Stratified CV)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    study = optuna.create_study(direction='maximize')
    
    print("Running 50 Optuna trials with GPU acceleration (5-Fold CV)...")
    study.optimize(
        lambda trial: objective(trial, X, y, cv, scale_pos_weight),
        n_trials=50
    )

    print("\n--- Optuna Study Completed ---")
    print(f"Best 5-Fold CV ROC-AUC: {study.best_value:.4f}")
    print("Best parameters found:")
    for k, v in study.best_params.items():
        print(f"  {k}: {v}")
    print("--------------------------------\n")

    # 4. Train Final Production Model
    print("Training final model on full dataset...")
    best_params = study.best_params
    best_params['scale_pos_weight'] = scale_pos_weight
    best_params['random_state'] = 42
    best_params['eval_metric'] = 'auc'
    best_params['device'] = 'cuda'
    best_params['tree_method'] = 'hist'
    
    # Calculate optimal early stopping dynamically for final training
    learning_rate = best_params['learning_rate']
    best_params['early_stopping_rounds'] = max(30, int(1.5 / learning_rate))

    final_model = xgb.XGBClassifier(**best_params)
    
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.1, random_state=42, stratify=y
    )
    
    final_model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=50
    )

    # 5. Save outputs in Kaggle working directory
    out_dir = '/kaggle/working' if os.path.exists('/kaggle') else 'output'
    os.makedirs(out_dir, exist_ok=True)
    model_out = os.path.join(out_dir, 'xgb_model.json')
    pipeline_out = os.path.join(out_dir, 'feature_pipeline.pkl')
    ref_out = os.path.join(out_dir, 'reference_data.parquet')

    print(f"Saving artifacts to output/ directory...")
    final_model.save_model(model_out)
    pipeline.save(pipeline_out)
    
    X_val['TARGET'] = y_val.values
    X_val.to_parquet(ref_out, index=False)

    print("\nAll done! Please check the output/ folder in Kaggle and download the files.")

if __name__ == '__main__':
    main()
