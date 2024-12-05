import pytest
from hardoc.scoring.metrics import QualityMetrics

def test_calculate_part_number_score():
    metrics = QualityMetrics()
    # Test with good part numbers
    good_parts = ["RC0805FR-0710KL", "CL21B104KCFNNNE"]
    score = metrics.calculate_part_number_score(good_parts)
    assert score > 0.8
    
    # Test with generic part numbers
    generic_parts = ["R1", "C1"]
    score = metrics.calculate_part_number_score(generic_parts)
    assert score < 0.5

def test_calculate_overall_score():
    metrics = QualityMetrics()
    scores = {
        'part_number_quality': 0.8,
        'manufacturer_info': 0.7,
        'datasheet_links': 0.9,
        'alternative_parts': 0.5,
        'cost_info': 0.6
    }
    overall_score = metrics.calculate_overall_score(scores)
    assert 0 <= overall_score <= 1
