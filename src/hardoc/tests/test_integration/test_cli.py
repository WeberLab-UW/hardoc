import pytest
from click.testing import CliRunner
from pathlib import Path
import json
import pandas as pd
from hardoc.cli import cli

@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()

@pytest.fixture
def sample_repo_with_bom(tmp_path):
    """Create a sample repository structure with BOM."""
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    
    # Create BOM file
    bom_content = (
        "Reference,Value,Manufacturer,Datasheet,Cost\n"
        "R1,10k,Yageo,http://example.com/ds1,0.10\n"
        "C1,100nF,Samsung,http://example.com/ds2,0.15\n"
    )
    (repo_dir / "BOM.csv").write_text(bom_content)
    
    # Create README
    readme_content = "# Test Project\n## License\nMIT\n"
    (repo_dir / "README.md").write_text(readme_content)
    
    return repo_dir

@pytest.fixture
def repo_list_file(tmp_path):
    """Create a file with list of repositories."""
    repo_list = tmp_path / "repos.txt"
    repo_list.write_text(
        "https://github.com/user1/repo1\n"
        "https://github.com/user2/repo2\n"
    )
    return repo_list

def test_analyze_command(runner, sample_repo_with_bom):
    """Test basic analyze command."""
    result = runner.invoke(cli, ['analyze', str(sample_repo_with_bom)])
    assert result.exit_code == 0
    assert 'Analysis Summary' in result.output
    assert 'Quality Score' in result.output

def test_analyze_with_json_output(runner, sample_repo_with_bom, tmp_path):
    """Test analyze command with JSON output."""
    output_file = tmp_path / "results.json"
    result = runner.invoke(cli, [
        'analyze',
        str(sample_repo_with_bom),
        '--output', str(output_file),
        '--format', 'json'
    ])
    
    assert result.exit_code == 0
    assert output_file.exists()
    
    # Verify JSON content
    with open(output_file) as f:
        data = json.load(f)
        assert 'metadata' in data
        assert 'data' in data

def test_analyze_with_csv_output(runner, sample_repo_with_bom, tmp_path):
    """Test analyze command with CSV output."""
    output_file = tmp_path / "results.csv"
    result = runner.invoke(cli, [
        'analyze',
        str(sample_repo_with_bom),
        '--output', str(output_file),
        '--format', 'csv'
    ])
    
    assert result.exit_code == 0
    assert output_file.exists()
    
    # Verify CSV content
    df = pd.read_csv(output_file)
    assert not df.empty

def test_batch_analyze(runner, repo_list_file, tmp_path):
    """Test batch analysis command."""
    output_file = tmp_path / "batch_results.json"
    result = runner.invoke(cli, [
        'batch-analyze',
        str(repo_list_file),
        '--output', str(output_file)
    ])
    
    assert result.exit_code == 0
    assert 'Analyzing' in result.output

def test_verbose_output(runner, sample_repo_with_bom):
    """Test verbose output option."""
    result = runner.invoke(cli, [
        'analyze',
        str(sample_repo_with_bom),
        '--verbose'
    ])
    
    assert result.exit_code == 0
    assert 'DEBUG' in result.output

def test_summarize_command(runner, tmp_path):
    """Test summarize command with existing results."""
    # Create sample results file
    results = {
        "metadata": {"timestamp": "2024-01-01"},
        "data": {
            "overall_score": 0.75,
            "categories": {
                "part_number_quality": {"score": 0.8}
            }
        }
    }
    
    results_file = tmp_path / "existing_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f)
    
    result = runner.invoke(cli, ['summarize', str(results_file)])
    assert result.exit_code == 0
    assert 'Score' in result.output

def test_error_handling(runner):
    """Test CLI error handling."""
    # Test with non-existent repository
    result = runner.invoke(cli, ['analyze', 'nonexistent/repo'])
    assert result.exit_code != 0
    assert 'Error' in result.output

def test_invalid_format(runner, sample_repo_with_bom):
    """Test invalid format specification."""
    result = runner.invoke(cli, [
        'analyze',
        str(sample_repo_with_bom),
        '--format', 'invalid'
    ])
    assert result.exit_code != 0

@pytest.mark.parametrize("command,args,expected_in_output", [
    ('analyze', ['--help'], 'Analyze a single repository'),
    ('batch-analyze', ['--help'], 'Analyze multiple repositories'),
    ('summarize', ['--help'], 'Generate a summary'),
])
def test_help_texts(runner, command, args, expected_in_output):
    """Test help text for different commands."""
    result = runner.invoke(cli, [command] + args)
    assert result.exit_code == 0
    assert expected_in_output in result.output

def test_version_command(runner):
    """Test version display."""
    result = runner.invoke(cli, ['--version'])
    assert result.exit_code == 0
    assert 'version' in result.output.lower()

@pytest.mark.integration
def test_full_cli_workflow(runner, sample_repo_with_bom, tmp_path):
    """Test complete CLI workflow."""
    # 1. Analyze repository
    json_output = tmp_path / "analysis.json"
    analyze_result = runner.invoke(cli, [
        'analyze',
        str(sample_repo_with_bom),
        '--output', str(json_output),
        '--format', 'json'
    ])
    assert analyze_result.exit_code == 0
    
    # 2. Generate summary
    summary_result = runner.invoke(cli, [
        'summarize',
        str(json_output)
    ])
    assert summary_result.exit_code == 0
    
    # 3. Export as CSV
    csv_output = tmp_path / "analysis.csv"
    export_result = runner.invoke(cli, [
        'analyze',
        str(sample_repo_with_bom),
        '--output', str(csv_output),
        '--format', 'csv'
    ])
    assert export_result.exit_code == 0
    
    # Verify all outputs exist and are valid
    assert json_output.exists()
    assert csv_output.exists()