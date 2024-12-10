import pytest
import pandas as pd
from pathlib import Path
from hardoc.parsers.bom_parser import BOMParser

@pytest.fixture
def sample_csv_bom(tmp_path):
    """Create a sample CSV BOM file."""
    bom_content = (
        "Reference,Value,Footprint,Datasheet,Manufacturer\n"
        "R1,10k,0805,http://example.com/ds1,Yageo\n"
        "C1,100nF,0603,http://example.com/ds2,Samsung\n"
        "U1,ATmega328P,TQFP-32,http://example.com/ds3,Microchip"
    )
    bom_file = tmp_path / "test_bom.csv"
    bom_file.write_text(bom_content)
    return bom_file

@pytest.fixture
def sample_markdown_bom(tmp_path):
    """Create a sample Markdown BOM file."""
    bom_content = """
# Bill of Materials

| Reference | Value | Footprint | Manufacturer |
|-----------|-------|-----------|--------------|
| R1 | 10k | 0805 | Yageo |
| C1 | 100nF | 0603 | Samsung |
"""
    bom_file = tmp_path / "test_bom.md"
    bom_file.write_text(bom_content)
    return bom_file

def test_bom_parser_init():
    """Test BOMParser initialization."""
    parser = BOMParser()
    assert parser is not None
    assert hasattr(parser, 'bom_patterns')

def test_is_bom_file():
    """Test BOM file name detection."""
    parser = BOMParser()
    assert parser.is_bom_file("BOM.csv") is True
    assert parser.is_bom_file("bill_of_materials.xlsx") is True
    assert parser.is_bom_file("parts_list.txt") is True
    assert parser.is_bom_file("random_file.txt") is False

def test_parse_csv_bom(sample_csv_bom):
    """Test parsing CSV BOM file."""
    parser = BOMParser()
    result = parser.parse(sample_csv_bom)
    
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3
    assert list(result.columns) == ['Reference', 'Value', 'Footprint', 'Datasheet', 'Manufacturer']
    assert result.iloc[0]['Reference'] == 'R1'
    assert result.iloc[0]['Value'] == '10k'

def test_parse_markdown_bom(sample_markdown_bom):
    """Test parsing Markdown BOM file."""
    parser = BOMParser()
    result = parser.parse(sample_markdown_bom)
    
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2
    assert 'Reference' in result.columns
    assert 'Value' in result.columns

def test_parse_nonexistent_file():
    """Test handling of nonexistent files."""
    parser = BOMParser()
    result = parser.parse("nonexistent.csv")
    assert result is None

def test_find_boms_in_text():
    """Test finding BOMs in text content."""
    parser = BOMParser()
    content = """
# Project Documentation
## Bill of Materials
Reference,Value,Footprint
R1,10k,0805
C1,100nF,0603
"""
    boms = parser.find_boms_in_text(content)
    assert len(boms) > 0
    assert boms[0]['format'] in ['csv', 'markdown']

def test_parse_invalid_content():
    """Test handling of invalid content."""
    parser = BOMParser()
    content = "Not a BOM\nJust some text\n"
    assert parser.find_boms_in_text(content) == []

@pytest.mark.parametrize("filename,expected", [
    ("BOM.csv", True),
    ("bom.CSV", True),
    ("bill_of_materials.xlsx", True),
    ("parts-list.txt", True),
    ("readme.md", False),
    ("schematic.pdf", False),
])
def test_bom_file_patterns(filename, expected):
    """Test various BOM file patterns."""
    parser = BOMParser()
    assert parser.is_bom_file(filename) is expected