from fastapi import APIRouter, Request, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.loan_application import LoanApplication
from app.schemas.prediction_response import PredictionResponse, SHAPExplanation
from app.database.connection import get_db
from app.database.models import InferenceLog
from app.database.repository import LogRepository
import uuid
import datetime
import json

router = APIRouter(prefix="/predict", tags=["Prediction"])

@router.post("", response_model=PredictionResponse, status_code=status.HTTP_200_OK)
async def predict_credit_risk(
    application: LoanApplication,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    scorer = request.app.state.scorer
    explainer = request.app.state.explainer

    if not scorer or not scorer.is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not ready or artifacts are missing. Run ml/train.py first."
        )

    # 1. Generate prediction ID and timestamp
    pred_id = f"pred_{uuid.uuid4().hex[:8]}"
    now = datetime.datetime.utcnow()

    # Convert Pydantic request model to dictionary
    input_data = application.dict()

    # 2. Run prediction & classification (CPU Bound -> run in threadpool or direct)
    # Since XGBoost inference is very fast, running it directly is usually fine.
    try:
        default_prob = scorer.predict(input_data)
        classification = request.app.state.classifier.classify(default_prob)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference failed: {str(e)}"
        )

    # 3. Generate SHAP explanation
    try:
        explanation_data = explainer.explain_and_plot(pred_id, input_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SHAP explanation failed: {str(e)}"
        )

    # 4. Save to Database (Inference Logging)
    features_df = scorer.get_features_df(input_data)
    
    log = InferenceLog(
        id=pred_id,
        timestamp=now,
        # Raw features
        applicant_age=application.applicant_age,
        income_total=application.income_total,
        employment_years=application.employment_years,
        loan_amount=application.loan_amount,
        loan_annuity=application.loan_annuity,
        goods_price=application.goods_price,
        num_children=application.num_children,
        education_type=application.education_type,
        housing_type=application.housing_type,
        bureau_loans_active=application.bureau_loans_active,
        bureau_overdue_count=application.bureau_overdue_count,
        prev_application_count=application.prev_application_count,
        prev_approved_ratio=application.prev_approved_ratio,
        external_source_1=application.external_source_1,
        external_source_2=application.external_source_2,
        external_source_3=application.external_source_3,
        # Engineered features
        loan_to_income_ratio=float(features_df['loan_to_income_ratio'].iloc[0]),
        annuity_to_income_ratio=float(features_df['annuity_to_income_ratio'].iloc[0]),
        credit_to_goods_ratio=float(features_df['credit_to_goods_ratio'].iloc[0]),
        # Output
        default_probability=default_prob,
        credit_score=classification["credit_score"],
        risk_grade=classification["risk_grade"],
        recommended_action=classification["recommended_action"],
        # SHAP
        shap_plot_path=explanation_data["shap_plot_url"],
        top_risk_factors_json=json.dumps(explanation_data["top_risk_factors"])
    )

    try:
        await LogRepository.create_log(db, log)
    except Exception as e:
        # Logging to standard out but continuing to serve prediction
        print(f"Error saving inference log to DB: {e}")

    # 5. Return prediction response
    return PredictionResponse(
        prediction_id=pred_id,
        timestamp=now,
        default_probability=default_prob,
        credit_score=classification["credit_score"],
        risk_grade=classification["risk_grade"],
        risk_color=classification["risk_color"],
        recommended_action=classification["recommended_action"],
        action_description=classification["action_description"],
        explanation=SHAPExplanation(
            shap_plot_url=explanation_data["shap_plot_url"],
            top_risk_factors=explanation_data["top_risk_factors"],
            total_features_analyzed=explanation_data["total_features_analyzed"]
        )
    )
