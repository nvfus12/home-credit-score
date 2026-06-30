import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "CreditLens AI"
    APP_VERSION: str = "v1.0.0"
    DEBUG: bool = True
    
    # Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    STATIC_DIR: str = os.path.join(BASE_DIR, "static")
    
    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{os.path.join(DATA_DIR, 'logs', 'inference_log.db')}"
    
    # ML Artifacts
    MODEL_PATH: str = os.path.join(DATA_DIR, "models", "xgb_model.json")
    PIPELINE_PATH: str = os.path.join(DATA_DIR, "models", "feature_pipeline.pkl")
    REFERENCE_DATA_PATH: str = os.path.join(DATA_DIR, "reference", "reference_data.parquet")
    
    # SHAP Configs
    SHAP_PLOT_DIR: str = os.path.join(STATIC_DIR, "assets", "shap_plots")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Ensure required folders exist
os.makedirs(os.path.join(settings.DATA_DIR, "models"), exist_ok=True)
os.makedirs(os.path.join(settings.DATA_DIR, "reference"), exist_ok=True)
os.makedirs(os.path.join(settings.DATA_DIR, "logs"), exist_ok=True)
os.makedirs(settings.SHAP_PLOT_DIR, exist_ok=True)
