from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.database.models import InferenceLog
import datetime

class LogRepository:
    @staticmethod
    async def create_log(db: AsyncSession, log: InferenceLog) -> InferenceLog:
        db.add(log)
        await db.flush()
        return log

    @staticmethod
    async def get_history(db: AsyncSession, limit: int = 50, offset: int = 0, risk_grade: str = None):
        query = select(InferenceLog).order_by(desc(InferenceLog.timestamp))
        if risk_grade:
            query = query.where(InferenceLog.risk_grade == risk_grade)
        
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_stats(db: AsyncSession):
        # Total counts
        total_query = select(func.count(InferenceLog.id))
        total_res = await db.execute(total_query)
        total_count = total_res.scalar() or 0

        # Today's predictions
        today_start = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_query = select(func.count(InferenceLog.id)).where(InferenceLog.timestamp >= today_start)
        today_res = await db.execute(today_query)
        today_count = today_res.scalar() or 0

        # Avg Default Probability
        avg_prob_query = select(func.avg(InferenceLog.default_probability))
        avg_prob_res = await db.execute(avg_prob_query)
        avg_prob = avg_prob_res.scalar() or 0.0

        # Risk distribution
        dist_query = select(InferenceLog.risk_grade, func.count(InferenceLog.id)).group_by(InferenceLog.risk_grade)
        dist_res = await db.execute(dist_query)
        distribution = {row[0]: row[1] for row in dist_res.all()}

        # Ensure all grades are represented
        for grade in ["Excellent", "Good", "Fair", "Poor"]:
            distribution.setdefault(grade, 0)

        return {
            "total_predictions": total_count,
            "today_predictions": today_count,
            "avg_default_probability": float(avg_prob),
            "risk_distribution": distribution
        }

    @staticmethod
    async def get_all_logs_for_drift(db: AsyncSession):
        """Fetches all logged feature data as a list of dicts for drift analysis."""
        query = select(InferenceLog)
        result = await db.execute(query)
        logs = result.scalars().all()
        
        # Convert to dictionary format
        return [
            {
                "applicant_age": log.applicant_age,
                "income_total": log.income_total,
                "employment_years": log.employment_years,
                "loan_amount": log.loan_amount,
                "loan_annuity": log.loan_annuity,
                "goods_price": log.goods_price,
                "num_children": log.num_children,
                "NAME_EDUCATION_TYPE": log.education_type,  # Match uppercase for evidently
                "NAME_HOUSING_TYPE": log.housing_type,
                "bureau_loans_active": log.bureau_loans_active,
                "bureau_overdue_count": log.bureau_overdue_count,
                "prev_application_count": log.prev_application_count,
                "prev_approved_ratio": log.prev_approved_ratio,
                "EXT_SOURCE_1": log.external_source_1,
                "EXT_SOURCE_2": log.external_source_2,
                "EXT_SOURCE_3": log.external_source_3,
                "loan_to_income_ratio": log.loan_to_income_ratio,
                "annuity_to_income_ratio": log.annuity_to_income_ratio,
                "credit_to_goods_ratio": log.credit_to_goods_ratio,
                "TARGET": log.default_probability  # We map default prob as target prediction
            }
            for log in logs
        ]
