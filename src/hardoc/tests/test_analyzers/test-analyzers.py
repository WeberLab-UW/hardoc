import pytest
import pandas as pd
from hardoc.analyzers.component_analyzer import ComponentAnalyzer

def test_component_analyzer_init():
    analyzer = ComponentAnalyzer()
    assert analyzer is not None

def test_analyze_component_quality():
    analyzer = ComponentAnalyzer()
    # Create test BOM data
    data = {
        'Reference': ['R1', 'C1'],
        'Value': ['10k', '100nF'],
        'Manufacturer': ['Yageo', ''],
        'Datasheet': ['http://example.com/ds1', '']
    }
    df = pd.DataFrame(data)
    
    result = analyzer.analyze_component_quality(df)
    assert 'part_number_quality' in result
    assert 'manufacturer_info' in result
    assert 'datasheet_links' in result
    assert isinstance(result['overall_score'], float)
