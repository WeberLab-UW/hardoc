import sys
from pathlib import Path
import logging

# Add the parent directory to Python path to import local hardoc package
sys.path.append(str(Path(__file__).parent.parent / "src"))

from hardoc.analyzers.repo_analyzer import analyze_repos
from hardoc.exporters.json_exporter import JSONExporter
from hardoc.exporters.csv_exporter import CSVExporter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# List of GitHub repositories to analyze
repositories = [
    "https://github.com/0xCB-dev/0xcb-1337",
    "https://github.com/google/skywater-pdk",
    # ... add your 20 repository URLs here
]

def main():
    # Run analysis
    logging.info(f"Starting analysis of {len(repositories)} repositories...")
    
    try:
        results = analyze_repos(repositories)
        
        # Export results to JSON
        json_exporter = JSONExporter()
        json_exporter.export(results, "analysis_results.json")
        logging.info("Exported JSON results to analysis_results.json")
        
        # Export results to CSV
        csv_exporter = CSVExporter()
        csv_exporter.export(results, "analysis_results.csv")
        logging.info("Exported CSV results to analysis_results.csv")
        
        # Print summary
        print("\nAnalysis Summary:")
        print(f"Repositories analyzed: {len(repositories)}")
        if 'repositories' in results:
            for repo in results['repositories']:
                print(f"\nRepository: {repo['repository_name']}")
                print(f"Overall Score: {repo.get('overall_score', 'N/A')}")
                print(f"BOMs found: {len(repo.get('boms', []))}")
                
    except Exception as e:
        logging.error(f"Error during analysis: {e}")
        raise

if __name__ == "__main__":
    main()