import pytest
import pandas as pd
from pathlib import Path
from hardoc.parsers.bom_parser import BOMParser
from hardoc.analyzers.component_analyzer import ComponentAnalyzer
from hardoc.scoring.metrics import QualityMetrics
from hardoc.scoring.explanations import ScoreExplainer
from hardoc.exporters.json_exporter import JSONExporter
from hardoc.exporters.csv_exporter import CSVExporter

@pytest.fixture
def complex_bom_file(tmp_path):
    """Create a complex BOM file with various quality aspects."""
    bom_content = (
        "Reference,Value,Footprint,Manufacturer,MPN,Datasheet,Cost,Alternative\n"
        "R1,10k,0805,Yageo,RC0805FR-0710KL,http://example.com/ds1,0.10,RC0805FR-0710KP\n"
        "C1,100nF,0603,Samsung,CL10B104KB8NNNL,http://example.com/ds2,0.15,\n"
        "U1,ATmega328P,TQFP-32,Microchip,ATMEGA328P-AU,http://example.com/ds3,2.50,ATMEGA328P-PU\n"
        "D1,LED,0603,,,,0.05,\n"  # Incomplete component
        "Q1,2N7002,SOT-23,,,http://example.com/ds5,,\n"  # Partial information
    )
    bom_file = tmp_path / "complex_bom.csv"
    bom_file.write_text(bom_content)
    return bom_file

@pytest.fixture
def markdown_bom_file(tmp_path):
    """Create a BOM in markdown format."""
    bom_content = """
# Bill of Materials

| Reference | Value | Manufacturer | Cost |
|-----------|-------|--------------|------|
| R1 | 10k | Yageo | 0.10 |
| C1 | 100nF | Samsung | 0.15 |
| U1 | ATmega328P | Microchip | 2.50 |
"""
    bom_file = tmp_path / "bom.md"
    bom_file.write_text(bom_content)
    return bom_file

def test_full_workflow(complex_bom_file, tmp_path):
    """Test complete workflow from parsing to export."""
    # 1. Parse BOM
    parser = BOMParser()
    bom_data = parser.parse(complex_bom_file)
    assert isinstance(bom_data, pd.DataFrame)
    assert len(bom_data) == 5
    
    # 2. Analyze Components
    analyzer = ComponentAnalyzer()
    analysis_results = analyzer.analyze_component_quality(bom_data)
    assert 'overall_score' in analysis_results
    assert 'part_number_quality' in analysis_results
    
    # 3. Generate Explanations
    explainer = ScoreExplainer()
    explanation = explainer.explain_overall_score(analysis_results)
    assert explanation['overall_score'] == analysis_results['overall_score']
    
    # 4. Export Results
    # JSON Export
    json_path = tmp_path / "results.json"
    json_exporter = JSONExporter()
    json_exporter.export(explanation, str(json_path))
    assert json_path.exists()
    
    # CSV Export
    csv_path = tmp_path / "results.csv"
    csv_exporter = CSVExporter()
    csv_exporter.export(explanation, str(csv_path))
    assert csv_path.exists()

def test_multiple_format_workflow(complex_bom_file, markdown_bom_file):
    """Test workflow with different BOM formats."""
    parser = BOMParser()
    analyzer = ComponentAnalyzer()
    
    # Analyze CSV BOM
    csv_data = parser.parse(complex_bom_file)
    csv_analysis = analyzer.analyze_component_quality(csv_data)
    
    # Analyze Markdown BOM
    md_data = parser.parse(markdown_bom_file)
    md_analysis = analyzer.analyze_component_quality(md_data)
    
    # Compare analyses
    assert isinstance(csv_analysis['overall_score'], float)
    assert isinstance(md_analysis['overall_score'], float)
    # CSV should have better score due to more complete information
    assert csv_analysis['overall_score'] > md_analysis['overall_score']

def test_error_handling_workflow(tmp_path):
    """Test workflow error handling."""
    parser = BOMParser()
    analyzer = ComponentAnalyzer()
    explainer = ScoreExplainer()
    
    # Test with invalid file
    invalid_file = tmp_path / "invalid.csv"
    invalid_file.write_text("invalid,content")
    
    # Should handle parsing error gracefully
    data = parser.parse(invalid_file)
    if data is not None:  # If parser returns DataFrame with invalid data
        analysis = analyzer.analyze_component_quality(data)
        assert analysis['overall_score'] == 0.0
        
        explanation = explainer.explain_overall_score(analysis)
        assert explanation['category'] == 'inadequate'

def test_quality_threshold_workflow(complex_bom_file):
    """Test workflow with different quality thresholds."""
    parser = BOMParser()
    analyzer = ComponentAnalyzer()
    metrics = QualityMetrics()
    
    bom_data = parser.parse(complex_bom_file)
    analysis = analyzer.analyze_component_quality(bom_data)
    
    # Check against minimum requirements
    meets_minimum = metrics.meets_minimum_requirements(analysis)
    assert isinstance(meets_minimum, bool)
    
    # Check improvement potential
    potential = metrics.get_improvement_potential(analysis)
    assert len(potential) > 0
    assert all(p['potential_gain'] >= 0 for p in potential)

@pytest.mark.parametrize("file_content,expected_score_range", [
    # Complete, high-quality BOM
    ("Reference,Value,Manufacturer,MPN,Datasheet,Cost\n"
     "R1,10k,Yageo,RC0805,http://ex.com,0.10",
     (0.7, 1.0)),
    # Minimal BOM
    ("Reference,Value\nR1,10k",
     (0.0, 0.3)),
    # Medium quality BOM
    ("Reference,Value,Manufacturer\nR1,10k,Yageo",
     (0.3, 0.7)),
])
def test_parametrized_workflow(tmp_path, file_content, expected_score_range):
    """Test workflow with different quality levels of BOMs."""
    # Create test file
    test_file = tmp_path / "test_bom.csv"
    test_file.write_text(file_content)
    
    # Run workflow
    parser = BOMParser()
    analyzer = ComponentAnalyzer()
    
    bom_data = parser.parse(test_file)
    analysis = analyzer.analyze_component_quality(bom_data)
    
    # Check if score falls within expected range
    assert expected_score_range[0] <= analysis['overall_score'] <= expected_score_range[1]

def test_export_format_workflow(complex_bom_file, tmp_path):
    """Test workflow with different export formats."""
    # Run analysis
    parser = BOMParser()
    analyzer = ComponentAnalyzer()
    
    bom_data = parser.parse(complex_bom_file)
    analysis = analyzer.analyze_component_quality(bom_data)
    
    # Export in different formats
    exports = {}
    
    # JSON export
    json_exporter = JSONExporter()
    json_path = tmp_path / "results.json"
    json_exporter.export(analysis, str(json_path))
    
    # CSV export
    csv_exporter = CSVExporter()
    csv_path = tmp_path / "results.csv"
    csv_exporter.export(analysis, str(csv_path))
    
    # Verify exports
    assert json_path.exists()
    assert csv_path.exists()
    
    # Verify JSON content
    import json
    with open(json_path) as f:
        json_data = json.load(f)
        assert 'data' in json_data
        assert 'metadata' in json_data
    
    # Verify CSV content
    import pandas as pd
    csv_data = pd.read_csv(csv_path)
    assert not csv_data.empty