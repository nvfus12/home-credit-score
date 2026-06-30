from fastapi import APIRouter, Request, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.database.repository import LogRepository
from app.schemas.monitoring_response import DriftReportResponse, SystemStatsResponse, RiskDistribution
import datetime

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])

@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    stats = await LogRepository.get_stats(db)
    
    # Calculate health status and alerts based on stats
    system_health = "OK"
    active_alerts = []
    
    # Simple threshold rules
    if stats["total_predictions"] > 0:
        poor_rate = stats["risk_distribution"].get("Poor", 0) / stats["total_predictions"]
        if poor_rate > 0.35:
            system_health = "WARNING"
            active_alerts.append("HIGH_DEFAULT_RATE_DETECTED")
            
    # Mock model train date
    trained_at = datetime.datetime.utcnow() - datetime.timedelta(days=14)

    return SystemStatsResponse(
        total_predictions=stats["total_predictions"],
        today_predictions=stats["today_predictions"],
        avg_default_probability=stats["avg_default_probability"],
        risk_distribution=RiskDistribution(
            Excellent=stats["risk_distribution"].get("Excellent", 0),
            Good=stats["risk_distribution"].get("Good", 0),
            Fair=stats["risk_distribution"].get("Fair", 0),
            Poor=stats["risk_distribution"].get("Poor", 0)
        ),
        model_version="v1.0.0",
        model_trained_at=trained_at,
        system_health=system_health,
        active_alerts=active_alerts
    )

@router.get("/drift-report", response_model=DriftReportResponse)
async def get_drift_report(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    drift_service = request.app.state.drift_monitor
    report = await drift_service.generate_drift_report(db)
    return report
