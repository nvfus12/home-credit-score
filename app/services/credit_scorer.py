import os
import sys
import xgboost as xgb
from app.config import settings
import ml.feature_engineering
from ml.feature_engineering import FeaturePipeline

# Alias to resolve pickle import path mismatch when loading
sys.modules['feature_engineering'] = ml.feature_engineering

class CreditScoringService:
    def __init__(self):
        self.model = None
        self.pipeline = None
        self.load_artifacts()

    def load_artifacts(self):
        """Loads XGBoost model and FeaturePipeline artifacts from disk."""
        if os.path.exists(settings.MODEL_PATH) and os.path.exists(settings.PIPELINE_PATH):
            try:
                print(f"Loading feature pipeline from {settings.PIPELINE_PATH}...")
                self.pipeline = FeaturePipeline.load(settings.PIPELINE_PATH)

                print(f"Loading XGBoost model from {settings.MODEL_PATH}...")
                self.model = xgb.XGBClassifier()
                self.model.load_model(settings.MODEL_PATH)
                print("ML Artifacts loaded successfully.")
            except Exception as e:
                print(f"Error loading ML artifacts: {e}")
                self.model = None
                self.pipeline = None
        else:
            print("Warning: ML Artifacts not found. Please run offline training first.")

    def is_ready(self) -> bool:
        return self.model is not None and self.pipeline is not None

    def predict(self, input_dict: dict) -> float:
        """
        Runs preprocess and inference.
        Returns the default probability (float in range [0, 1]).
        """
        if not self.is_ready():
            raise RuntimeError("Model service is not initialized or artifacts are missing.")

        # Transform single input dict to DataFrame
        features_df = self.pipeline.transform_single(input_dict)

        # Run inference
        # predict_proba returns [proba_neg, proba_pos]
        proba = self.model.predict_proba(features_df)[0, 1]
        
        return float(proba)

    def get_features_df(self, input_dict: dict):
        """Helper to get processed dataframe for SHAP calculations."""
        if not self.is_ready():
            raise RuntimeError("Pipeline is not loaded.")
        return self.pipeline.transform_single(input_dict)
