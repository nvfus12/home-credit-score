import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock
from app.main import app

@pytest.fixture
def client_with_mock_services():
    import pandas as pd
    import asyncio
    from app.database.connection import init_db
    
    # Initialize the database schema for the test
    asyncio.run(init_db())
    mock_scorer = MagicMock()
    mock_scorer.is_ready.return_value = True
    mock_scorer.predict.return_value = 0.15 # 15% default risk
    
    mock_df = pd.DataFrame([{
        'loan_to_income_ratio': 0.5,
        'annuity_to_income_ratio': 0.1,
        'credit_to_goods_ratio': 1.1
    }])
    mock_scorer.get_features_df.return_value = mock_df
    
    mock_explainer = MagicMock()
    mock_explainer.explain_and_plot.return_value = {
        "shap_plot_url": "/static/assets/shap_plots/pred_test.png",
        "top_risk_factors": [
            {
                "feature": "external_source_2",
                "display_name": "Điểm tín dụng đối tác 2",
                "shap_value": -0.05,
                "direction": "risk_decrease",
                "description": "Giảm rủi ro"
            }
        ],
        "total_features_analyzed": 15
    }
    
    from app.services.risk_classifier import RiskClassificationEngine
    app.state.scorer = mock_scorer
    app.state.explainer = mock_explainer
    app.state.classifier = RiskClassificationEngine()
    
    client = TestClient(app)
    yield client
    
    # Reset app state
    app.state.scorer = None
    app.state.explainer = None
    app.state.classifier = None

def test_api_predict_success(client_with_mock_services):
    payload = {
        "applicant_age": 35.5,
        "income_total": 45000000,
        "employment_years": 8.0,
        "loan_amount": 250000000,
        "loan_annuity": 15000000,
        "goods_price": 230000000,
        "num_children": 1,
        "education_type": "Higher education",
        "housing_type": "House / apartment",
        "bureau_loans_active": 2,
        "bureau_overdue_count": 0,
        "prev_application_count": 3,
        "prev_approved_ratio": 0.67,
        "external_source_1": 0.55,
        "external_source_2": 0.62,
        "external_source_3": 0.48
    }
    
    response = client_with_mock_services.post("/api/v1/predict", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "prediction_id" in data
    assert data["default_probability"] == 0.15
    assert data["credit_score"] == 768  # 850 - floor(0.15 * 550) = 850 - 82 = 768
    assert data["risk_grade"] == "Good"
    assert data["recommended_action"] == "APPROVE_WITH_CONDITIONS"
    assert "explanation" in data
    assert data["explanation"]["shap_plot_url"] == "/static/assets/shap_plots/pred_test.png"
    assert len(data["explanation"]["top_risk_factors"]) == 1

def test_api_predict_service_unavailable():
    # If scorer is not loaded
    app.state.scorer = None
    client = TestClient(app)
    
    response = client.post("/api/v1/predict", json={"applicant_age": 30, "income_total": 10000, "employment_years": 2, "loan_amount": 5000, "loan_annuity": 500, "goods_price": 5000})
    assert response.status_code == 503
    assert "detail" in response.json()
