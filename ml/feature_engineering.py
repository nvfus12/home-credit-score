import pandas as pd
import numpy as np
import os
import pickle
from sklearn.preprocessing import LabelEncoder

class FeaturePipeline:
    def __init__(self):
        self.label_encoders = {}
        self.categorical_cols = [
            'NAME_EDUCATION_TYPE', 
            'NAME_HOUSING_TYPE'
        ]
        self.feature_columns = []

    def fit_transform_raw(self, app_path, bureau_path, prev_path, sample_size=None):
        """
        Loads raw Kaggle CSV files, performs aggregations and feature engineering,
        fits preprocessing objects (LabelEncoders), and returns the training DataFrame.
        """
        print("Loading application_train.csv...")
        app_df = pd.read_csv(app_path)
        if sample_size:
            app_df = app_df.sample(n=sample_size, random_state=42).reset_index(drop=True)

        # 1. Feature Engineering on Main Application
        app_df['applicant_age'] = -app_df['DAYS_BIRTH'] / 365.25
        
        # Handle Days Employed anomaly (365243 represents unemployed)
        app_df['DAYS_EMPLOYED'] = app_df['DAYS_EMPLOYED'].replace(365243, np.nan)
        app_df['employment_years'] = -app_df['DAYS_EMPLOYED'] / 365.25
        app_df['employment_years'] = app_df['employment_years'].fillna(0)

        # Financial Ratios
        app_df['loan_to_income_ratio'] = app_df['AMT_CREDIT'] / (app_df['AMT_INCOME_TOTAL'] + 1)
        app_df['annuity_to_income_ratio'] = app_df['AMT_ANNUITY'] / (app_df['AMT_INCOME_TOTAL'] + 1)
        app_df['credit_to_goods_ratio'] = app_df['AMT_CREDIT'] / (app_df['AMT_GOODS_PRICE'] + 1)
        app_df['income_per_person'] = app_df['AMT_INCOME_TOTAL'] / (app_df['CNT_CHILDREN'] + 2)
        app_df['payment_rate'] = app_df['AMT_ANNUITY'] / (app_df['AMT_CREDIT'] + 1)

        # External Sources aggregations
        ext_sources = ['EXT_SOURCE_1', 'EXT_SOURCE_2', 'EXT_SOURCE_3']
        app_df['external_source_mean'] = app_df[ext_sources].mean(axis=1)
        app_df['external_source_std'] = app_df[ext_sources].std(axis=1).fillna(0)

        # 2. Aggregations on Bureau Data (CIC history)
        if os.path.exists(bureau_path):
            print("Loading and aggregating bureau.csv...")
            bureau_df = pd.read_csv(bureau_path)
            
            # Filter bureau to matching clients to save memory in subsample mode
            bureau_df = bureau_df[bureau_df['SK_ID_CURR'].isin(app_df['SK_ID_CURR'])]

            # Aggregate Active Loans count and debt ratios
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
            print("Bureau file not found, initializing empty columns...")
            app_df['bureau_loans_active'] = 0
            app_df['bureau_overdue_count'] = 0
            app_df['bureau_debt_to_credit_ratio'] = 0.0

        # Fill NaNs for bureau aggregates
        app_df['bureau_loans_active'] = app_df['bureau_loans_active'].fillna(0)
        app_df['bureau_overdue_count'] = app_df['bureau_overdue_count'].fillna(0)
        app_df['bureau_debt_to_credit_ratio'] = app_df['bureau_debt_to_credit_ratio'].fillna(0.0)

        # 3. Aggregations on Previous Application Data
        if os.path.exists(prev_path):
            print("Loading and aggregating previous_application.csv...")
            prev_df = pd.read_csv(prev_path)
            
            # Filter prev applications to matching clients
            prev_df = prev_df[prev_df['SK_ID_CURR'].isin(app_df['SK_ID_CURR'])]

            # Aggregate count and approval ratio
            prev_df['is_approved'] = (prev_df['NAME_CONTRACT_STATUS'] == 'Approved').astype(int)
            prev_agg = prev_df.groupby('SK_ID_CURR').agg(
                prev_application_count=('SK_ID_PREV', 'count'),
                prev_approved_sum=('is_approved', 'sum')
            ).reset_index()
            prev_agg['prev_approved_ratio'] = prev_agg['prev_approved_sum'] / (prev_agg['prev_application_count'] + 1e-5)
            prev_agg = prev_agg.drop(columns=['prev_approved_sum'])

            app_df = app_df.merge(prev_agg, on='SK_ID_CURR', how='left')
        else:
            print("Previous application file not found, initializing empty columns...")
            app_df['prev_application_count'] = 0
            app_df['prev_approved_ratio'] = 0.0

        # Fill NaNs for previous application aggregates
        app_df['prev_application_count'] = app_df['prev_application_count'].fillna(0)
        app_df['prev_approved_ratio'] = app_df['prev_approved_ratio'].fillna(0.0)

        # 4. Handle Categorical Columns with Label Encoding
        for col in self.categorical_cols:
            if col in app_df.columns:
                le = LabelEncoder()
                app_df[col] = app_df[col].fillna('Unknown')
                app_df[col] = le.fit_transform(app_df[col].astype(str))
                self.label_encoders[col] = le

        # Select columns to train on
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
        
        # Rename incoming columns to match training features if they differ in casing/naming
        rename_map = {
            'AMT_INCOME_TOTAL': 'income_total',
            'AMT_CREDIT': 'loan_amount',
            'AMT_ANNUITY': 'loan_annuity',
            'AMT_GOODS_PRICE': 'goods_price',
            'CNT_CHILDREN': 'num_children',
            'NAME_EDUCATION_TYPE': 'NAME_EDUCATION_TYPE',
            'NAME_HOUSING_TYPE': 'NAME_HOUSING_TYPE',
            'EXT_SOURCE_1': 'EXT_SOURCE_1',
            'EXT_SOURCE_2': 'EXT_SOURCE_2',
            'EXT_SOURCE_3': 'EXT_SOURCE_3'
        }
        app_df = app_df.rename(columns=rename_map)

        # Set up final list of features
        self.feature_columns = model_cols
        
        # Return cleaned features dataframe and target labels
        target = app_df['TARGET'] if 'TARGET' in app_df.columns else None
        
        # Filter app_df to only model columns
        features_df = app_df[model_cols].copy()
        
        # Fill missing numeric values with median or default NaN representation for XGBoost
        # XGBoost handles NaNs natively, but it's good to ensure no strings or infinities exist
        for col in features_df.columns:
            if col not in self.categorical_cols:
                features_df[col] = pd.to_numeric(features_df[col], errors='coerce')

        return features_df, target

    def transform_single(self, input_dict):
        """
        Transforms a single raw customer dictionary input (from API request) 
        into a 1-row pandas DataFrame matching the model's expected features.
        """
        # Map API keys to model columns
        mapped_dict = input_dict.copy()
        
        key_mapping = {
            'education_type': 'NAME_EDUCATION_TYPE',
            'housing_type': 'NAME_HOUSING_TYPE',
            'external_source_1': 'EXT_SOURCE_1',
            'external_source_2': 'EXT_SOURCE_2',
            'external_source_3': 'EXT_SOURCE_3'
        }
        
        for api_key, model_key in key_mapping.items():
            if api_key in mapped_dict:
                mapped_dict[model_key] = mapped_dict.pop(api_key)

        # Create single-row DataFrame
        df = pd.DataFrame([mapped_dict])

        # Preprocess features
        df['applicant_age'] = float(df.get('applicant_age', [30])[0])
        df['income_total'] = float(df.get('income_total', [50000])[0])
        df['employment_years'] = float(df.get('employment_years', [2])[0])
        df['loan_amount'] = float(df.get('loan_amount', [100000])[0])
        df['loan_annuity'] = float(df.get('loan_annuity', [5000])[0])
        df['goods_price'] = float(df.get('goods_price', [100000])[0])
        df['num_children'] = int(df.get('num_children', [0])[0])
        
        # Fill external sources
        for col in ['EXT_SOURCE_1', 'EXT_SOURCE_2', 'EXT_SOURCE_3']:
            val = df.get(col, [np.nan])[0]
            df[col] = float(val) if val is not None and not pd.isna(val) else np.nan

        # Financial ratios
        df['loan_to_income_ratio'] = df['loan_amount'] / (df['income_total'] + 1)
        df['annuity_to_income_ratio'] = df['loan_annuity'] / (df['income_total'] + 1)
        df['credit_to_goods_ratio'] = df['loan_amount'] / (df['goods_price'] + 1)
        df['income_per_person'] = df['income_total'] / (df['num_children'] + 2)
        df['payment_rate'] = df['loan_annuity'] / (df['loan_amount'] + 1)
        
        # Aggregated external sources
        ext_sources = [df['EXT_SOURCE_1'].iloc[0], df['EXT_SOURCE_2'].iloc[0], df['EXT_SOURCE_3'].iloc[0]]
        valid_ext = [x for x in ext_sources if not pd.isna(x)]
        df['external_source_mean'] = np.mean(valid_ext) if len(valid_ext) > 0 else np.nan
        df['external_source_std'] = np.std(valid_ext) if len(valid_ext) > 0 else 0.0

        # Aggregated historical features
        df['bureau_loans_active'] = float(df.get('bureau_loans_active', [0])[0])
        df['bureau_overdue_count'] = float(df.get('bureau_overdue_count', [0])[0])
        df['bureau_debt_to_credit_ratio'] = float(df.get('bureau_debt_to_credit_ratio', [0.0])[0])
        df['prev_application_count'] = float(df.get('prev_application_count', [0])[0])
        df['prev_approved_ratio'] = float(df.get('prev_approved_ratio', [0.0])[0])

        # Categorical processing
        for col in self.categorical_cols:
            val = str(df.get(col, ['Unknown'])[0])
            le = self.label_encoders.get(col)
            if le:
                # If category is unseen, map to 'Unknown' or nearest category
                if val not in le.classes_:
                    val = 'Unknown' if 'Unknown' in le.classes_ else le.classes_[0]
                df[col] = le.transform([val])[0]
            else:
                df[col] = 0

        # Order columns exactly as expected by the model
        return df[self.feature_columns]

    def save(self, path):
        with open(path, 'wb') as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path):
        import pickle
        
        class CustomUnpickler(pickle.Unpickler):
            def find_class(self, module, name):
                if name == 'FeaturePipeline':
                    from ml.feature_engineering import FeaturePipeline
                    return FeaturePipeline
                # Handle old module paths
                if module == '__main__' or module == 'feature_engineering':
                    module = 'ml.feature_engineering'
                try:
                    return super().find_class(module, name)
                except ModuleNotFoundError:
                    if name == 'FeaturePipeline':
                        from ml.feature_engineering import FeaturePipeline
                        return FeaturePipeline
                    raise
                    
        with open(path, 'rb') as f:
            return CustomUnpickler(f).load()
