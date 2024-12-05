import pytest
import pandas as pd
from hardoc.analyzers.component_analyzer import ComponentAnalyzer

@pytest.fixture
def sample_bom_data():
    """Create sample BOM data for testing."""
    return pd.DataFrame({
        'Reference': ['R1', 'C1', 'U1'],
        'Value': ['10k', '100nF', 'ATmega328P'],
        'Manufacturer': ['Yageo', 'Samsung', 'Microchip'],
        'Datasheet': [
            'http://example.com/ds1',
            'http://example.com/ds2',
            'http://example.com/ds3'
        ],
        'Cost': ['0.10', '0.15', '2.50'],
        'Alternative': ['RC0805FR-0710KL', '', 'ATMEGA328P-AU']
    })

def test_analyzer_init():
    """Test ComponentAnalyzer initialization."""
    analyzer = ComponentAnalyzer()
    assert analyzer is not None
    assert hasattr(analyzer, 'metrics')

def test_analyze_component_quality(sample_bom_data):
    """Test basic component quality analysis."""
    analyzer = ComponentAnalyzer()
    result = analyzer.analyze_component_quality(sample_bom_data)
    
    assert isinstance(result, dict)
    assert 'overall_score' in result
    assert 'part_number_quality' in result
    assert 'manufacturer_info' in result
    assert 'datasheet_links' in result
    assert 'alternative_parts' in result
    assert 'cost_info' in result

def test_analyze_part_numbers(sample_bom_data):
    """Test part number analysis."""
    analyzer = ComponentAnalyzer()
    result = analyzer._analyze_part_numbers(sample_bom_data)
    
    assert result['has_part_numbers'] is True
    assert result['score'] > 0
    assert 'specificity' in result

def test_analyze_manufacturer_info(sample_bom_data):
    """Test manufacturer information analysis."""
    analyzer = ComponentAnalyzer()
    result = analyzer._analyze_manufacturer_info(sample_bom_data)
    
    assert result['has_manufacturer_info'] is True
    assert result['components_with_mfg'] == 3
    assert result['score'] == 1.0

def test_analyze_datasheet_links(sample_bom_data):
    """Test datasheet link analysis."""
    analyzer = ComponentAnalyzer()
    result = analyzer._analyze_datasheet_links(sample_bom_data)
    
    assert result['has_datasheet_links'] is True
    assert result['total_links'] == 3
    assert result['valid_links'] == 3
    assert result['score'] == 1.0

def test_analyze_alternative_parts(sample_bom_data):
    """Test alternative parts analysis."""
    analyzer = ComponentAnalyzer()
    result = analyzer._analyze_alternative_parts(sample_bom_data)
    
    assert result['has_alternatives'] is True
    assert result['score'] > 0

def test_analyze_cost_info(sample_bom_data):
    """Test cost information analysis."""
    analyzer = ComponentAnalyzer()
    result = analyzer._analyze_cost_info(sample_bom_data)
    
    assert result['has_cost_info'] is True
    assert result['components_with_cost'] == 3
    assert result['has_currency'] is False

def test_empty_dataframe():
    """Test handling of empty DataFrame."""
    analyzer = ComponentAnalyzer()
    empty_df = pd.DataFrame()
    result = analyzer.analyze_component_quality(empty_df)
    
    assert result['overall_score'] == 0.0
    assert all(result[key]['score'] == 0.0 for key in [
        'part_number_quality', 'manufacturer_info', 
        'datasheet_links', 'alternative_parts', 'cost_info'
    ])

@pytest.mark.parametrize("test_data,expected_score", [
    (pd.DataFrame({'Reference': ['R1'], 'Value': ['10k']}), 0.0),
    (pd.DataFrame({'Reference': ['R1'], 'Manufacturer': ['Yageo']}), 0.0),
    (pd.DataFrame({'Reference': ['R1'], 'Cost': ['0.10']}), 0.0),
])
def test_minimal_data(test_data, expected_score):
    """Test analysis with minimal data."""
    analyzer = ComponentAnalyzer()
    result = analyzer.analyze_component_quality(test_data)
    assert result['overall_score'] == expected_score