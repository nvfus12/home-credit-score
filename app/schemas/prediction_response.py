from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime

class RiskFactor(BaseModel):
    feature: str
    display_name: str
    shap_value: float
    direction: str
    description: str

class SHAPExplanation(BaseModel):
    shap_plot_url: str
    top_risk_factors: List[RiskFactor]
    total_features_analyzed: int

class PredictionResponse(BaseModel):
    prediction_id: str
    timestamp: datetime
    default_probability: float
    credit_score: int
    risk_grade: str
    risk_color: str
    recommended_action: str
    action_description: str
    explanation: SHAPExplanation
