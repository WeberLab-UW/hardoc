"""
CSV exporter for Hardoc analysis results.
Handles flattened output of analysis data in CSV format.
"""

import csv
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging
from pathlib import Path
import pandas as pd

class CSVExporter:
    """Exports analysis results to CSV format."""
    
    def __init__(self):
        """Initialize CSV exporter with logging."""
        self.logger = logging.getLogger(__name__)

    def export(self, data: Dict[str, Any], output_path: str) -> None:
        """
        Export analysis results to CSV.
        
        Args:
            data: Dictionary containing analysis results
            output_path: Path to save CSV file
        """
        try:
            # Flatten the data structure
            flattened_data = self._flatten_data(data)
            
            # Convert to DataFrame
            df = pd.DataFrame(flattened_data)
            
            # Save to CSV
            self._save_to_file(df, output_path)
            
        except Exception as e:
            self.logger.error(f"Error exporting to CSV: {e}")
            raise

    def _flatten_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Flatten nested data structure for CSV export.
        
        Args:
            data: Nested dictionary of analysis results
            
        Returns:
            List[Dict]: List of flattened dictionaries
        """
        flattened = []
        
        # Handle repository results
        if 'repositories' in data:
            for repo in data['repositories']:
                repo_data = self._flatten_repository_data(repo)
                flattened.extend(repo_data)
        else:
            # Single repository result
            flattened.extend(self._flatten_repository_data(data))
            
        return flattened

    def _flatten_repository_data(self, repo_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Flatten single repository data."""
        flattened = []
        
        # Basic repository info
        base_info = {
            'repository_name': repo_data.get('repository_name', ''),
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'hardoc_version': self._get_version()
        }
        
        # Handle BOM results
        if 'boms' in repo_data:
            for bom in repo_data['boms']:
                bom_entry = base_info.copy()
                bom_entry.update({
                    'bom_file': bom.get('file_path', ''),
                    'bom_format': bom.get('format', ''),
                    'total_components': bom.get('summary', {}).get('total_components', 0),
                })
                
                # Add quality scores
                if 'quality_analysis' in bom:
                    quality = bom['quality_analysis']
                    bom_entry.update({
                        'overall_score': quality.get('overall_score', 0),
                        'part_number_score': quality.get('part_number_quality', {}).get('score', 0),
                        'manufacturer_score': quality.get('manufacturer_info', {}).get('score', 0),
                        'datasheet_score': quality.get('datasheet_links', {}).get('score', 0),
                        'alternatives_score': quality.get('alternative_parts', {}).get('score', 0),
                        'cost_info_score': quality.get('cost_info', {}).get('score', 0)
                    })
                
                flattened.append(bom_entry)
                
        return flattened

    def _save_to_file(self, df: pd.DataFrame, output_path: str) -> None:
        """Save DataFrame to CSV file."""
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            df.to_csv(output_path, index=False)
            
            self.logger.info(f"Successfully exported CSV to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving CSV to {output_path}: {e}")
            raise

    @staticmethod
    def _get_version() -> str:
        """Get Hardoc package version."""
        try:
            from hardoc import __version__
            return __version__
        except ImportError:
            return "unknown"
