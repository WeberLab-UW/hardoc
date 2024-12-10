import pytest
from hardoc.scoring.metrics import QualityMetrics, ScoreWeights

@pytest.fixture
def metrics():
    """Create QualityMetrics instance for testing."""
    return QualityMetrics()

@pytest.fixture
def sample_scores():
    """Sample scores for testing."""
    return {
        'part_number_quality': 0.8,
        'manufacturer_info': 0.7,
        'datasheet_links': 0.9,
        'alternative_parts': 0.5,
        'cost_info': 0.6
    }

def test_quality_metrics_init():
    """Test QualityMetrics initialization."""
    metrics = QualityMetrics()
    assert isinstance(metrics.weights, ScoreWeights)
    assert metrics.weights.part_number_quality == 0.30
    assert metrics.weights.manufacturer_info == 0.20

def test_calculate_overall_score(metrics, sample_scores):
    """Test overall score calculation."""
    score = metrics.calculate_overall_score(sample_scores)
    assert 0 <= score <= 1
    # Manual calculation for verification
    expected = (
        0.8 * 0.30 +  # part_number
        0.7 * 0.20 +  # manufacturer
        0.9 * 0.20 +  # datasheet
        0.5 * 0.15 +  # alternatives
        0.6 * 0.15    # cost
    )
    assert abs(score - expected) < 0.01

def test_get_score_category(metrics):
    """Test score categorization."""
    assert metrics.get_score_category(0.95) == 'excellent'
    assert metrics.get_score_category(0.85) == 'good'
    assert metrics.get_score_category(0.65) == 'fair'
    assert metrics.get_score_category(0.35) == 'poor'
    assert metrics.get_score_category(0.15) == 'inadequate'

def test_normalize_score(metrics):
    """Test score normalization."""
    assert metrics.normalize_score(1.5) == 1.0
    assert metrics.normalize_score(-0.5) == 0.0
    assert metrics.normalize_score(0.75) == 0.75

def test_calculate_weighted_subscores(metrics, sample_scores):
    """Test weighted subscore calculation."""
    weighted_scores = metrics.calculate_weighted_subscores(sample_scores)
    
    assert 'part_number_quality' in weighted_scores
    assert 'raw_score' in weighted_scores['part_number_quality']
    assert 'weighted_score' in weighted_scores['part_number_quality']
    assert 'category' in weighted_scores['part_number_quality']
    
    # Verify weighted score calculation
    part_number = weighted_scores['part_number_quality']
    assert part_number['weighted_score'] == part_number['raw_score'] * part_number['weight']

def test_get_improvement_potential(metrics, sample_scores):
    """Test improvement potential calculation."""
    potential = metrics.get_improvement_potential(sample_scores)
    
    assert isinstance(potential, list)
    assert len(potential) > 0
    assert all(item['potential_gain'] >= 0 for item in potential)
    assert all(item['priority'] in ['high', 'medium', 'low'] for item in potential)
    
    # Verify sorting by potential gain
    gains = [item['potential_gain'] for item in potential]
    assert gains == sorted(gains, reverse=True)

def test_adjust_weights(metrics):
    """Test weight adjustment."""
    new_weights = {
        'part_number_quality': 0.25,
        'manufacturer_info': 0.25,
        'datasheet_links': 0.20,
        'alternative_parts': 0.15,
        'cost_info': 0.15
    }
    
    metrics.adjust_weights(new_weights)
    assert metrics.weights.part_number_quality == 0.25
    assert metrics.weights.manufacturer_info == 0.25

def test_invalid_weight_adjustment(metrics):
    """Test invalid weight adjustments."""
    with pytest.raises(ValueError):
        metrics.adjust_weights({'part_number_quality': 0.9})  # Sum > 1
        
    with pytest.raises(ValueError):
        metrics.adjust_weights({'invalid_category': 0.5})

def test_minimum_requirements(metrics):
    """Test minimum requirements check."""
    good_scores = {
        'part_number_quality': 0.7,
        'manufacturer_info': 0.6,
        'datasheet_links': 0.8,
        'alternative_parts': 0.4,
        'cost_info': 0.5
    }
    assert metrics.meets_minimum_requirements(good_scores)
    
    poor_scores = {
        'part_number_quality': 0.3,
        'manufacturer_info': 0.2,
        'datasheet_links': 0.4,
        'alternative_parts': 0.1,
        'cost_info': 0.2
    }
    assert not metrics.meets_minimum_requirements(poor_scores)

@pytest.mark.parametrize("scores,expected", [
    ({}, 0.0),  # Empty scores
    ({'invalid_category': 1.0}, 0.0),  # Invalid category
    ({'part_number_quality': None}, 0.0),  # None value
])
def test_edge_cases(metrics, scores, expected):
    """Test edge cases in score calculation."""
    assert metrics.calculate_overall_score(scores) == expected