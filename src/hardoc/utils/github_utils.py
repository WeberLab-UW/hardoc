import subprocess
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def clone_repository(repo_url: str, target_dir: str) -> Optional[Path]:
    """
    Clone a GitHub repository to target directory.
    
    Args:
        repo_url: URL of GitHub repository
        target_dir: Directory to clone into
        
    Returns:
        Optional[Path]: Path to cloned repository or None if cloning fails
    """
    try:
        # Create target directory if it doesn't exist
        Path(target_dir).mkdir(parents=True, exist_ok=True)
        
        # Clone repository
        subprocess.run(
            ['git', 'clone', repo_url, target_dir],
            check=True,
            capture_output=True,
            text=True
        )
        
        return Path(target_dir)
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to clone repository: {e.stderr}")
        return None
    except Exception as e:
        logger.error(f"Error cloning repository: {e}")
        return None

def fetch_repo_info(repo_url: str) -> dict:
    """
    Fetch basic information about a repository.
    
    Args:
        repo_url: URL of GitHub repository
        
    Returns:
        dict: Repository information
    """
    # Extract owner and repo name from URL
    parts = repo_url.rstrip('/').split('/')
    owner = parts[-2]
    repo = parts[-1]
    
    return {
        'name': repo,
        'owner': owner,
        'url': repo_url
    }