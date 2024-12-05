"""
JSON exporter for Hardoc analysis results.
Handles structured output of analysis data in JSON format.
"""

import json
from typing import Any, Dict, Optional
from datetime import datetime
import logging
from pathlib import Path

class JSONExporter:
    """Exports analysis results to JSON format."""
    
    def __init__(self):
        """Initialize JSON exporter with logging."""
        self.logger = logging.getLogger(__name__)

    def export(self, data: Dict[str, Any], output_path: Optional[str] = None) -> Optional[str]:
        """
        Export analysis results to JSON.
        
        Args:
            data: Dictionary containing analysis results
            output_path: Optional path to save JSON file
            
        Returns:
            Optional[str]: JSON string if no output_path, None if saved to file
        """
        try:
            # Add metadata
            export_data = {
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "hardoc_version": self._get_version(),
                    "export_type": "json"
                },
                "data": data
            }
            
            # Convert to JSON
            json_str = json.dumps(export_data, indent=2)
            
            if output_path:
                self._save_to_file(json_str, output_path)
                return None
            return json_str
            
        except Exception as e:
            self.logger.error(f"Error exporting to JSON: {e}")
            raise

    def _save_to_file(self, json_str: str, output_path: str) -> None:
        """Save JSON string to file."""
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
                
            self.logger.info(f"Successfully exported JSON to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving JSON to {output_path}: {e}")
            raise

    @staticmethod
    def _get_version() -> str:
        """Get Hardoc package version."""
        try:
            from hardoc import __version__
            return __version__
        except ImportError:
            return "unknown"
