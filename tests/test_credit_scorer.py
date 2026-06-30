import pytest
from unittest.mock import MagicMock, patch
from app.services.credit_scorer import CreditScoringService

def test_credit_scorer_not_ready():
    # If no files exist, is_ready() should return False
    scorer = CreditScoringService()
    # Force artifacts not found
    scorer.model = None
    scorer.pipeline = None
    assert not scorer.is_ready()
    
    with pytest.raises(RuntimeError):
        scorer.predict({"applicant_age": 30})

@patch('app.services.credit_scorer.FeaturePipeline')
@patch('xgboost.XGBClassifier')
def test_credit_scorer_ready_predict(mock_xgb_class, mock_pipeline_class):
    import numpy as np
    # Mock model and pipeline
    mock_model = MagicMock()
    mock_model.predict_proba.return_value = np.array([[0.8, 0.2]]) # 20% default proba
    
    mock_pipeline = MagicMock()
    mock_pipeline.transform_single.return_value = MagicMock() # Mock DataFrame
    
    scorer = CreditScoringService()
    scorer.model = mock_model
    scorer.pipeline = mock_pipeline
    
    assert scorer.is_ready()
    
    proba = scorer.predict({"applicant_age": 35})
    assert proba == 0.2
    mock_model.predict_proba.assert_called_once()
    mock_pipeline.transform_single.assert_called_once_with({"applicant_age": 35})
