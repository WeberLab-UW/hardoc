from pathlib import Path
from typing import Optional

def read_file_contents(file_path: str) -> Optional[str]:
    """
    Read contents of a file safely.
    
    Args:
        file_path: Path to file to read
        
    Returns:
        Optional[str]: File contents or None if reading fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def find_files(directory: str, pattern: str) -> list:
    """
    Find files matching pattern in directory.
    
    Args:
        directory: Directory to search
        pattern: Glob pattern to match
        
    Returns:
        list: List of matching file paths
    """
    path = Path(directory)
    return list(path.rglob(pattern))