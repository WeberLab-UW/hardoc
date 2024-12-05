from typing import Dict, List, Optional, Union
import pandas as pd
import re
from pathlib import Path
import logging
from ..utils.file_utils import read_file_contents

class BOMParser:
    """Parser for Bill of Materials (BOM) files and content."""
    
    def __init__(self):
        """Initialize BOM parser with format detection patterns."""
        self.bom_patterns = {
            'file': [
                r'(?i)^bom[._-]?.*\.(csv|xlsx?|txt|md)$',
                r'(?i)^bill[._-]?of[._-]?materials.*\.(csv|xlsx?|txt|md)$',
                r'(?i)^parts[._-]?list.*\.(csv|xlsx?|txt|md)$'
            ],
            'content': [
                r'(?i)bill\s+of\s+materials',
                r'(?i)\bBOM\b',
                r'(?i)parts\s+list',
                r'(?i)component\s+list'
            ],
            'table': {
                'markdown': r'\|(?:[^|]*\|){2,}',
                'csv': r'^[^,]+,(?:[^,]*,){2,}[^,]+$',
                'space_separated': r'^\S+\s+\S+\s+\S+.*$'
            }
        }
        self.logger = logging.getLogger(__name__)

    def is_bom_file(self, filename: str) -> bool:
        """
        Check if a filename matches common BOM naming patterns.
        
        Args:
            filename: Name of the file to check
            
        Returns:
            bool: True if filename matches BOM patterns
        """
        return any(re.match(pattern, filename) for pattern in self.bom_patterns['file'])

    def parse(self, file_path: Union[str, Path]) -> Optional[pd.DataFrame]:
        """
        Parse a BOM file into a pandas DataFrame.
        
        Args:
            file_path: Path to the BOM file
            
        Returns:
            Optional[pd.DataFrame]: Parsed BOM data or None if parsing fails
        """
        file_path = Path(file_path)
        try:
            if not file_path.exists():
                self.logger.error(f"File not found: {file_path}")
                return None

            ext = file_path.suffix.lower()
            if ext == '.csv':
                return pd.read_csv(file_path)
            elif ext in ['.xlsx', '.xls']:
                return pd.read_excel(file_path)
            elif ext == '.md':
                return self._parse_markdown(file_path)
            else:
                content = read_file_contents(file_path)
                return self._parse_text_content(content)
                
        except Exception as e:
            self.logger.error(f"Error parsing {file_path}: {e}")
            return None

    def find_boms_in_text(self, content: str) -> List[Dict]:
        """
        Find potential BOMs embedded in text content.
        
        Args:
            content: Text content to search
            
        Returns:
            List[Dict]: List of dictionaries containing BOM information
        """
        boms = []
        has_bom_marker = any(re.search(pattern, content) 
                           for pattern in self.bom_patterns['content'])
        
        if has_bom_marker:
            # Look for table structures
            for format_name, pattern in self.bom_patterns['table'].items():
                matches = re.finditer(pattern, content, re.MULTILINE)
                for match in matches:
                    boms.append({
                        'format': format_name,
                        'start': match.start(),
                        'end': match.end(),
                        'content': match.group()
                    })
        
        return boms

    def _parse_markdown(self, file_path: Path) -> Optional[pd.DataFrame]:
        """
        Parse markdown file for BOM tables.
        
        Args:
            file_path: Path to markdown file
            
        Returns:
            Optional[pd.DataFrame]: Parsed BOM data or None if no valid tables found
        """
        content = read_file_contents(file_path)
        # Find markdown tables
        tables = re.findall(self.bom_patterns['table']['markdown'], content, re.MULTILINE)
        
        if not tables:
            return None
            
        # Convert the first valid table to DataFrame
        try:
            # Split into lines and clean up
            lines = tables[0].strip().split('\n')
            # Extract headers
            headers = [h.strip() for h in lines[0].split('|')[1:-1]]
            # Extract data
            data = []
            for line in lines[2:]:  # Skip header separator line
                row = [cell.strip() for cell in line.split('|')[1:-1]]
                data.append(row)
                
            return pd.DataFrame(data, columns=headers)
            
        except Exception as e:
            self.logger.error(f"Error parsing markdown table: {e}")
            return None

    def _parse_text_content(self, content: str) -> Optional[pd.DataFrame]:
        """
        Parse text content for BOM data.
        
        Args:
            content: Text content to parse
            
        Returns:
            Optional[pd.DataFrame]: Parsed BOM data or None if no valid data found
        """
        boms = self.find_boms_in_text(content)
        if not boms:
            return None
            
        # Try to parse the first BOM found
        bom = boms[0]
        try:
            if bom['format'] == 'csv':
                return pd.read_csv(pd.StringIO(bom['content']))
            elif bom['format'] == 'markdown':
                return self._parse_markdown_content(bom['content'])
            # Add more format handlers as needed
            
        except Exception as e:
            self.logger.error(f"Error parsing embedded BOM: {e}")
            return None

    @staticmethod
    def validate_bom_data(df: pd.DataFrame) -> bool:
        """
        Validate that DataFrame contains required BOM fields.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            bool: True if DataFrame contains minimum required fields
        """
        required_columns = {'reference', 'value', 'quantity'}
        return any(col.lower() in df.columns.str.lower() for col in required_columns)