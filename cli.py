import click
import logging
from pathlib import Path
from typing import List, Optional
from .analyzers.repo_analyzer import analyze_repo, analyze_repos
from .exporters.json_exporter import JSONExporter
from .exporters.csv_exporter import CSVExporter

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@click.group()
@click.version_option()
def cli():
    """Hardoc - Open Hardware Documentation Analyzer."""
    pass

@cli.command()
@click.argument('repo_url')
@click.option(
    '--output', '-o',
    type=click.Path(),
    help='Output file path for results'
)
@click.option(
    '--format', '-f',
    type=click.Choice(['json', 'csv']),
    default='json',
    help='Output format (default: json)'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose output'
)
def analyze(repo_url: str, output: Optional[str], format: str, verbose: bool):
    """Analyze a single repository."""
    try:
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
            
        click.echo(f"Analyzing repository: {repo_url}")
        results = analyze_repo(repo_url)
        
        if results:
            _export_results(results, output, format)
            _display_summary(results)
        else:
            click.echo("No results found.")
            
    except Exception as e:
        click.echo(f"Error analyzing repository: {e}", err=True)
        raise click.Abort()

@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option(
    '--output', '-o',
    type=click.Path(),
    help='Output file path for results'
)
@click.option(
    '--format', '-f',
    type=click.Choice(['json', 'csv']),
    default='json',
    help='Output format (default: json)'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose output'
)
def batch_analyze(input_file: str, output: Optional[str], format: str, verbose: bool):
    """Analyze multiple repositories from a file."""
    try:
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
            
        repos = _read_repo_list(input_file)
        click.echo(f"Analyzing {len(repos)} repositories...")
        
        results = analyze_repos(repos)
        if results:
            _export_results(results, output, format)
            _display_batch_summary(results)
        else:
            click.echo("No results found.")
            
    except Exception as e:
        click.echo(f"Error in batch analysis: {e}", err=True)
        raise click.Abort()

@cli.command()
@click.argument('results_file', type=click.Path(exists=True))
@click.option(
    '--format', '-f',
    type=click.Choice(['text', 'json', 'csv']),
    default='text',
    help='Output format (default: text)'
)
def summarize(results_file: str, format: str):
    """Generate a summary from existing results file."""
    try:
        results = _load_results(results_file)
        if format == 'text':
            _display_summary(results)
        else:
            _export_results(results, None, format)
            
    except Exception as e:
        click.echo(f"Error generating summary: {e}", err=True)
        raise click.Abort()

def _export_results(results: dict, output: Optional[str], format: str):
    """Export results in the specified format."""
    if format == 'json':
        exporter = JSONExporter()
        if output:
            exporter.export(results, output)
        else:
            click.echo(exporter.export(results))
    else:  # csv
        if not output:
            output = 'hardoc_results.csv'
        CSVExporter().export(results, output)
        click.echo(f"Results exported to {output}")

def _display_summary(results: dict):
    """Display a human-readable summary of results."""
    click.echo("\nAnalysis Summary:")
    click.echo("================")
    
    if 'overall_score' in results:
        click.echo(f"Overall Quality Score: {results['overall_score']:.2f}")
        
    if 'boms' in results:
        click.echo(f"\nBOMs Found: {len(results['boms'])}")
        for bom in results['boms']:
            click.echo(f"\nBOM: {bom['file_path']}")
            click.echo(f"Format: {bom['format']}")
            click.echo(f"Components: {bom['summary']['total_components']}")
            
            if 'quality_analysis' in bom:
                quality = bom['quality_analysis']
                click.echo("\nQuality Scores:")
                click.echo(f"- Overall: {quality['overall_score']:.2f}")
                click.echo(f"- Part Numbers: {quality['part_number_quality']['score']:.2f}")
                click.echo(f"- Manufacturer Info: {quality['manufacturer_info']['score']:.2f}")
                click.echo(f"- Datasheets: {quality['datasheet_links']['score']:.2f}")
                
                if quality.get('recommendations'):
                    click.echo("\nRecommendations:")
                    for rec in quality['recommendations']:
                        click.echo(f"- {rec}")

def _display_batch_summary(results: dict):
    """Display summary for batch analysis."""
    click.echo("\nBatch Analysis Summary:")
    click.echo("=====================")
    
    repositories = results.get('repositories', [])
    click.echo(f"Repositories Analyzed: {len(repositories)}")
    
    avg_score = sum(r.get('overall_score', 0) for r in repositories) / len(repositories)
    click.echo(f"Average Quality Score: {avg_score:.2f}")
    
    click.echo("\nRepository Overview:")
    for repo in repositories:
        click.echo(f"\n{repo['repository_name']}:")
        click.echo(f"- Score: {repo.get('overall_score', 0):.2f}")
        click.echo(f"- BOMs Found: {len(repo.get('boms', []))}")

def _read_repo_list(file_path: str) -> List[str]:
    """Read repository URLs from a file."""
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def _load_results(file_path: str) -> dict:
    """Load results from a file."""
    path = Path(file_path)
    if path.suffix == '.json':
        import json
        with open(path) as f:
            return json.load(f)
    elif path.suffix == '.csv':
        import pandas as pd
        return pd.read_csv(path).to_dict('records')
    else:
        raise click.BadParameter("Unsupported file format")

if __name__ == '__main__':
    cli()