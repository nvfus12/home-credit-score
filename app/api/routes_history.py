from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.database.repository import LogRepository
from typing import List, Optional
import json

router = APIRouter(prefix="/predictions", tags=["History"])

@router.get("/history")
async def get_prediction_history(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    risk_grade: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    offset = (page - 1) * limit
    logs = await LogRepository.get_history(db, limit=limit, offset=offset, risk_grade=risk_grade)

    # Format the DB rows into client-friendly dictionaries
    history_list = []
    for log in logs:
        try:
            top_factors = json.loads(log.top_risk_factors_json) if log.top_risk_factors_json else []
        except Exception:
            top_factors = []

        history_list.append({
            "prediction_id": log.id,
            "timestamp": log.timestamp.isoformat() + "Z",
            "applicant_name": f"Khách hàng {log.id[-4:]}",  # Simple mock name
            "applicant_age": log.applicant_age,
            "income_total": log.income_total,
            "loan_amount": log.loan_amount,
            "default_probability": log.default_probability,
            "credit_score": log.credit_score,
            "risk_grade": log.risk_grade,
            "recommended_action": log.recommended_action,
            "shap_plot_url": log.shap_plot_path,
            "top_risk_factors": top_factors
        })

    # Get quick count stats for pagination context
    stats = await LogRepository.get_stats(db)
    total_records = stats["total_predictions"]

    return {
        "page": page,
        "limit": limit,
        "total_records": total_records,
        "items": history_list
    }
