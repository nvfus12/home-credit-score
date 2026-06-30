from sqlalchemy import Column, String, Float, Integer, DateTime
from app.database.connection import Base
import datetime

class InferenceLog(Base):
    __tablename__ = "inference_logs"

    id = Column(String, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Raw input features
    applicant_age = Column(Float)
    income_total = Column(Float)
    employment_years = Column(Float)
    loan_amount = Column(Float)
    loan_annuity = Column(Float)
    goods_price = Column(Float)
    num_children = Column(Integer)
    education_type = Column(String)
    housing_type = Column(String)
    bureau_loans_active = Column(Integer)
    bureau_overdue_count = Column(Integer)
    prev_application_count = Column(Integer)
    prev_approved_ratio = Column(Float)
    external_source_1 = Column(Float)
    external_source_2 = Column(Float)
    external_source_3 = Column(Float)

    # Engineered features
    loan_to_income_ratio = Column(Float)
    annuity_to_income_ratio = Column(Float)
    credit_to_goods_ratio = Column(Float)

    # Prediction outputs
    default_probability = Column(Float, nullable=False)
    credit_score = Column(Integer, nullable=False)
    risk_grade = Column(String, nullable=False)
    recommended_action = Column(String, nullable=False)

    # SHAP
    shap_plot_path = Column(String)
    top_risk_factors_json = Column(String)  # JSON-serialized list of risk factors
