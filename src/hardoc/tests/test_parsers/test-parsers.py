from pathlib import Path
import pytest
from hardoc.parsers.bom_parser import BOMParser

def test_bom_parser_init():
    parser = BOMParser()
    assert parser is not None

def test_detect_bom_file():
    parser = BOMParser()
    # Test with various BOM filenames
    assert parser.is_bom_file("BOM.csv") is True
    assert parser.is_bom_file("bill_of_materials.xlsx") is True
    assert parser.is_bom_file("random_file.txt") is False

def test_parse_csv_bom(tmp_path):
    # Create a test CSV file
    bom_content = "Reference,Value,Footprint\nR1,10k,0805\nC1,100nF,0603"
    bom_file = tmp_path / "test_bom.csv"
    bom_file.write_text(bom_content)
    
    parser = BOMParser()
    result = parser.parse(str(bom_file))
    
    assert result is not None
    assert len(result) == 2
    assert result.iloc[0]["Reference"] == "R1"
