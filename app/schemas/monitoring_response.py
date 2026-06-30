from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime

class DriftedFeature(BaseModel):
    feature: str
    psi: float
    status: str
    alert: str

class TargetDrift(BaseModel):
    predicted_default_rate_reference: float
    predicted_default_rate_current: float
    status: str

class DriftReportResponse(BaseModel):
    report_generated_at: datetime
    total_predictions_since_deploy: int
    dataset_drift_detected: bool
    drift_share: float
    drifted_features: List[DriftedFeature]
    target_drift: TargetDrift
    evidently_html_report_url: str
    recommendation: str

class RiskDistribution(BaseModel):
    Excellent: int
    Good: int
    Fair: int
    Poor: int

class SystemStatsResponse(BaseModel):
    total_predictions: int
    today_predictions: int
    avg_default_probability: float
    risk_distribution: RiskDistribution
    model_version: str
    model_trained_at: datetime
    system_health: str
    active_alerts: List[str]
