"""
Shared pytest fixtures for Hardoc tests.
"""
import pytest
import pandas as pd
from pathlib import Path

@pytest.fixture
def sample_bom_df():
    """Create a sample BOM DataFrame for testing."""
    data = {
        'Reference': ['R1', 'C1', 'U1'],
        'Value': ['10k', '100nF', 'ATmega328P'],
        'Manufacturer': ['Yageo', 'Samsung', 'Microchip'],
        'Datasheet': [
            'http://example.com/ds1',
            'http://example.com/ds2',
            'http://example.com/ds3'
        ],
        'Cost': [0.10, 0.15, 2.50]
    }
    return pd.DataFrame(data)

@pytest.fixture
def test_repo_path(tmp_path):
    """Create a test repository structure."""
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    
    # Create some test files
    (repo_dir / "BOM.csv").write_text("Reference,Value\nR1,10k\n")
    (repo_dir / "README.md").write_text("# Test Project\n")
    
    return repo_dir
