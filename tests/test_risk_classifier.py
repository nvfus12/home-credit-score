import pytest
from app.services.risk_classifier import RiskClassificationEngine

def test_risk_classification_excellent():
    # Probability 5% (Excellent)
    result = RiskClassificationEngine.classify(0.05)
    assert result["risk_grade"] == "Excellent"
    assert result["recommended_action"] == "AUTO_APPROVE"
    assert result["credit_score"] >= 750
    assert result["risk_color"] == "#10b981"

def test_risk_classification_good():
    # Probability 20% (Good)
    result = RiskClassificationEngine.classify(0.20)
    assert result["risk_grade"] == "Good"
    assert result["recommended_action"] == "APPROVE_WITH_CONDITIONS"
    assert 650 <= result["credit_score"] < 750

def test_risk_classification_fair():
    # Probability 40% (Fair)
    result = RiskClassificationEngine.classify(0.40)
    assert result["risk_grade"] == "Fair"
    assert result["recommended_action"] == "MANUAL_REVIEW"
    assert 500 <= result["credit_score"] < 650

def test_risk_classification_poor():
    # Probability 75% (Poor)
    result = RiskClassificationEngine.classify(0.75)
    assert result["risk_grade"] == "Poor"
    assert result["recommended_action"] == "REJECT"
    assert result["credit_score"] < 500
    assert result["risk_color"] == "#ef4444"

def test_risk_classification_bounds():
    # Test boundary limits
    result_low = RiskClassificationEngine.classify(-0.1)
    assert result_low["default_probability"] == 0.0
    
    result_high = RiskClassificationEngine.classify(1.5)
    assert result_high["default_probability"] == 1.0
