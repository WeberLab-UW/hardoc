import logging
import tempfile
from pathlib import Path
from typing import List, Dict, Optional
import shutil

from ..parsers.bom_parser import BOMParser
from ..analyzers.component_analyzer import ComponentAnalyzer
from ..utils.github_utils import clone_repository

class RepoAnalyzer:
    """Analyzer for hardware repositories."""
    
    def __init__(self):
        """Initialize repository analyzer."""
        self.bom_parser = BOMParser()
        self.component_analyzer = ComponentAnalyzer()
        self.logger = logging.getLogger(__name__)
        
    def analyze_repo(self, repo_url: str) -> Dict:
        """
        Analyze a single repository.
        
        Args:
            repo_url: URL of the GitHub repository
            
        Returns:
            Dict containing analysis results
        """
        try:
            # Create temporary directory for repository
            with tempfile.TemporaryDirectory() as temp_dir:
                self.logger.info(f"Analyzing repository: {repo_url}")
                
                # Clone repository
                repo_path = clone_repository(repo_url, temp_dir)
                if not repo_path:
                    return self._generate_error_result(repo_url, "Failed to clone repository")
                
                # Find and analyze BOMs
                return self._analyze_repo_contents(repo_url, repo_path)
                
        except Exception as e:
            self.logger.error(f"Error analyzing repository {repo_url}: {e}")
            return self._generate_error_result(repo_url, str(e))
    
    def _analyze_repo_contents(self, repo_url: str, repo_path: Path) -> Dict:
        """Analyze contents of a repository."""
        results = {
            'repository_url': repo_url,
            'repository_name': repo_url.split('/')[-1],
            'boms_found': 0,
            'boms': [],
            'overall_score': 0.0,
        }
        
        # Find all potential BOM files
        bom_files = self._find_bom_files(repo_path)
        results['boms_found'] = len(bom_files)
        
        if not bom_files:
            self.logger.warning(f"No BOMs found in {repo_url}")
            return results
            
        # Analyze each BOM
        total_score = 0.0
        for bom_file in bom_files:
            bom_analysis = self._analyze_bom(bom_file)
            if bom_analysis:
                results['boms'].append(bom_analysis)
                total_score += bom_analysis.get('quality_analysis', {}).get('overall_score', 0)
        
        # Calculate overall repository score
        if results['boms']:
            results['overall_score'] = total_score / len(results['boms'])
        
        return results
    
    def _find_bom_files(self, repo_path: Path) -> List[Path]:
        """Find all BOM files in repository."""
        bom_files = []
        for file_path in repo_path.rglob('*'):
            if file_path.is_file() and self.bom_parser.is_bom_file(file_path.name):
                bom_files.append(file_path)
        return bom_files
    
    def _analyze_bom(self, bom_path: Path) -> Optional[Dict]:
        """Analyze a single BOM file."""
        try:
            # Parse BOM
            bom_data = self.bom_parser.parse(str(bom_path))
            if bom_data is None:
                return None
                
            # Analyze components
            quality_analysis = self.component_analyzer.analyze_component_quality(bom_data)
            
            return {
                'file_path': str(bom_path.relative_to(bom_path.parent.parent)),
                'format': bom_path.suffix[1:],
                'quality_analysis': quality_analysis,
                'summary': {
                    'total_components': len(bom_data),
                    'unique_components': len(bom_data.drop_duplicates())
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing BOM {bom_path}: {e}")
            return None
    
    @staticmethod
    def _generate_error_result(repo_url: str, error_message: str) -> Dict:
        """Generate error result for failed analysis."""
        return {
            'repository_url': repo_url,
            'repository_name': repo_url.split('/')[-1],
            'error': error_message,
            'boms_found': 0,
            'boms': [],
            'overall_score': 0.0
        }

def analyze_repo(repo_url: str) -> Dict:
    """
    Convenience function for analyzing a single repository.
    
    Args:
        repo_url: URL of the GitHub repository
        
    Returns:
        Dict containing analysis results
    """
    analyzer = RepoAnalyzer()
    return analyzer.analyze_repo(repo_url)

def analyze_repos(repo_urls: List[str]) -> Dict:
    """
    Analyze multiple repositories.
    
    Args:
        repo_urls: List of repository URLs
        
    Returns:
        Dict containing analysis results for all repositories
    """
    analyzer = RepoAnalyzer()
    results = {
        'repositories': [],
        'total_repositories': len(repo_urls),
        'successful_analyses': 0,
        'failed_analyses': 0
    }
    
    for repo_url in repo_urls:
        repo_result = analyzer.analyze_repo(repo_url)
        results['repositories'].append(repo_result)
        
        if 'error' in repo_result:
            results['failed_analyses'] += 1
        else:
            results['successful_analyses'] += 1
    
    return results