import os
import re
from github import Github, GithubException
import pandas as pd
from pathlib import Path
import logging
import base64
from typing import Dict, List, Optional, Tuple
import markdown
from bs4 import BeautifulSoup
from io import StringIO, BytesIO
import chardet
import xlrd
import openpyxl
import warnings
import json
from datetime import datetime

def load_repositories(file_path: str) -> List[str]:
    """Load repository URLs from file."""
    try:
        with open(file_path, 'r') as f:
            # Strip whitespace and filter empty lines
            repos = [line.strip() for line in f if line.strip()]
        logging.info(f"Loaded {len(repos)} repositories from {file_path}")
        return repos
    except Exception as e:
        logging.error(f"Error loading repositories from {file_path}: {e}")
        return []

class BOMPatternAnalyzer:
    def __init__(self, token: str):
        self.github = Github(token)
        self.logger = logging.getLogger(__name__)
        self.bom_paths = [
            '/bom/', '/hardware/', '/production/', 
            '/fabrication/', '/manufacturing/', '/docs/',
            '/assembly/', '/pcb/', '/electronics/'
        ]
        # Common BOM file patterns
        self.bom_file_patterns = [
            r'bom[^/]*\.(?:csv|xlsx?|ods)$',
            r'bill.*materials[^/]*\.(?:csv|xlsx?|ods)$',
            r'.*-bom[^/]*\.(?:csv|xlsx?|ods)$',
            r'.*_bom[^/]*\.(?:csv|xlsx?|ods)$',
            r'assembly.*\.(?:csv|xlsx?|ods)$',
            r'parts.*list[^/]*\.(?:csv|xlsx?|ods)$'
        ]
        # Standard column name mappings
        self.column_mappings = {
            'reference': ['reference', 'designator', 'refdes', 'ref', 'refs', 'reference designator'],
            'value': ['value', 'component', 'part', 'description', 'comment'],
            'footprint': ['footprint', 'package', 'pcb footprint', 'smd', 'housing'],
            'quantity': ['quantity', 'qty', 'count', 'amount'],
            'manufacturer': ['manufacturer', 'mfg', 'vendor', 'supplier', 'producer'],
            'part_number': ['part number', 'part#', 'pn', 'mpn', 'manufacturer part', 'supplier part']
        }

    def _is_potential_bom(self, file_content) -> bool:
        """Enhanced check for potential BOM files."""
        name_lower = file_content.path.lower()
        
        # Skip binary and irrelevant files
        if self._is_binary_file(name_lower):
            return False
            
        # Check path patterns
        if any(path in name_lower for path in self.bom_paths):
            return True
            
        # Check file name patterns
        if any(re.search(pattern, name_lower, re.IGNORECASE) for pattern in self.bom_file_patterns):
            return True
            
        # Check content for BOM-like patterns in documentation files
        if name_lower.endswith(('.md', '.txt')):
            try:
                content = self._decode_content(base64.b64decode(file_content.content))
                if content:
                    # Look for BOM indicators in content
                    bom_indicators = [
                        r'bill\s+of\s+materials',
                        r'parts?\s+list',
                        r'components?\s+list',
                        r'bom\s+table',
                        r'\|\s*ref(?:erence|des)?\s*\|',  # Markdown table headers
                        r'\|\s*(?:part|value)\s*\|'
                    ]
                    return any(re.search(pattern, content.lower()) for pattern in bom_indicators)
            except:
                return False
                
        return False

    def _standardize_column_names(self, columns: List[str]) -> Dict[str, str]:
        """Map varied column names to standard names."""
        standardized = {}
        for col in columns:
            col_lower = col.lower().strip()
            for std_name, variations in self.column_mappings.items():
                if any(variation in col_lower for variation in variations):
                    standardized[col] = std_name
                    break
        return standardized

    def _analyze_spreadsheet_file(self, content: bytes, path: str) -> Optional[Dict]:
        """Analyze Excel/ODS spreadsheet files."""
        try:
            if path.endswith('.xlsx'):
                wb = openpyxl.load_workbook(BytesIO(content), data_only=True)
                sheet = wb.active
                headers = [str(cell.value) for cell in next(sheet.rows) if cell.value]
                rows = list(sheet.iter_rows(min_row=2, values_only=True))
            elif path.endswith('.ods'):
                # Handle ODS files
                pass
            elif path.endswith('.xls'):
                wb = xlrd.open_workbook(file_contents=content)
                sheet = wb.sheet_by_index(0)
                headers = [str(cell.value) for cell in sheet.row(0) if cell.value]
                rows = [sheet.row_values(i) for i in range(1, sheet.nrows)]
            
            # Standardize column names
            std_columns = self._standardize_column_names(headers)
            
            # Analyze content quality
            component_count = len(rows)
            has_part_numbers = any('part_number' in col for col in std_columns.values())
            has_quantities = any('quantity' in col for col in std_columns.values())
            
            return {
                'type': 'spreadsheet',
                'path': path,
                'format': path.split('.')[-1],
                'columns': headers,
                'standardized_columns': std_columns,
                'row_count': component_count,
                'has_part_numbers': has_part_numbers,
                'has_quantities': has_quantities,
                'sample_rows': rows[:3] if rows else []
            }
        except Exception as e:
            self.logger.error(f"Error analyzing spreadsheet {path}: {e}")
            return None

    def _analyze_csv_bom(self, content: str, path: str) -> Optional[Dict]:
        """Enhanced CSV BOM analysis with better error handling and format detection."""
        try:
            # Try different CSV parsing options
            df = None
            for sep in [',', ';', '\t', '|']:
                try:
                    df = pd.read_csv(StringIO(content), sep=sep)
                    if len(df.columns) > 1:  # Valid CSV should have multiple columns
                        break
                except:
                    continue
                    
            if df is None or len(df.columns) <= 1:
                return None
                
            # Standardize column names
            std_columns = self._standardize_column_names(list(df.columns))
            
            return {
                'type': 'csv',
                'path': path,
                'columns': list(df.columns),
                'standardized_columns': std_columns,
                'row_count': len(df),
                'has_part_numbers': any('part_number' in col for col in std_columns.values()),
                'has_quantities': any('quantity' in col for col in std_columns.values()),
                'sample_rows': df.head(3).to_dict('records'),
                'separator': sep
            }
        except Exception as e:
            self.logger.error(f"Error analyzing CSV {path}: {e}")
            return None

    def _analyze_markdown_bom(self, content: str, path: str) -> Optional[Dict]:
        """Enhanced markdown BOM table analysis."""
        try:
            html = markdown.markdown(content)
            soup = BeautifulSoup(html, 'html.parser')
            tables = soup.find_all('table')
            
            bom_tables = []
            for table in tables:
                headers = [th.text.strip() for th in table.find_all('th')]
                if self._is_likely_bom_table(headers):
                    rows = []
                    for row in table.find_all('tr')[1:]:  # Skip header row
                        cells = [td.text.strip() for td in row.find_all('td')]
                        if cells:
                            rows.append(cells)
                            
                    std_columns = self._standardize_column_names(headers)
                    
                    bom_tables.append({
                        'headers': headers,
                        'standardized_columns': std_columns,
                        'row_count': len(rows),
                        'has_part_numbers': any('part_number' in col for col in std_columns.values()),
                        'has_quantities': any('quantity' in col for col in std_columns.values()),
                        'sample_rows': rows[:3]
                    })
                    
            if bom_tables:
                return {
                    'type': 'markdown',
                    'path': path,
                    'tables': bom_tables
                }
                    
        except Exception as e:
            self.logger.error(f"Error analyzing markdown {path}: {e}")
            return None
            
    def _is_likely_bom_table(self, headers: List[str]) -> bool:
        """Enhanced check for BOM-like tables."""
        headers_lower = [h.lower() for h in headers]
        headers_text = ' '.join(headers_lower)
        
        # Must have at least one reference/designator column
        has_reference = any(variation in headers_text 
                          for variation in self.column_mappings['reference'])
        
        # Must have at least one value/component column
        has_value = any(variation in headers_text 
                       for variation in self.column_mappings['value'])
        
        # Should have some additional common BOM columns
        other_indicators = ['quantity', 'footprint', 'manufacturer', 'part']
        has_other = any(indicator in headers_text for indicator in other_indicators)
        
        return has_reference and has_value and has_other

def analyze_repositories(repo_urls: List[str], github_token: str) -> Dict:
    """Analyze BOM patterns across multiple repositories."""
    analyzer = BOMPatternAnalyzer(github_token)
    results = []
    
    for repo_url in repo_urls:
        try:
            result = analyzer.analyze_repository(repo_url)
            results.append(result)
            logging.info(f"Analyzed {repo_url}: found {result['bom_count']} BOMs")
        except Exception as e:
            logging.error(f"Error analyzing {repo_url}: {e}")
            
    return {
        'total_repos': len(repo_urls),
        'repos_with_boms': sum(1 for r in results if r['bom_count'] > 0),
        'total_boms_found': sum(r['bom_count'] for r in results),
        'detailed_results': results,
        'analysis_time': datetime.now().isoformat()
    }

def clean_repo_url(url: str) -> str:
    """Clean repository URL to standard format."""
    url = re.sub(r'/tree/.*$', '', url)
    return url.rstrip('/')

def save_results(results: Dict, output_file: str):
    """Save analysis results to file."""
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

def main():
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Get GitHub token from environment variable
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        logging.error("Please set the GITHUB_TOKEN environment variable")
        return

    # Load repositories from file
    repo_file = "repositories.txt"  # You can make this a command line argument
    try:
        repositories = load_repositories(repo_file)
        if not repositories:
            logging.error("No repositories loaded. Exiting.")
            return
    except Exception as e:
        logging.error(f"Failed to load repositories: {e}")
        return

    # Clean repository URLs
    clean_repos = [clean_repo_url(url) for url in repositories]
    clean_repos = list(dict.fromkeys(clean_repos))
    
    logging.info(f"Starting analysis of {len(clean_repos)} repositories")
    
    # Run analysis
    results = analyze_repositories(clean_repos, github_token)
    
    # Save detailed results
    output_file = f"bom_analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_results(results, output_file)
    
    # Print summary
    print("\nAnalysis Summary:")
    print(f"Total repositories analyzed: {results['total_repos']}")
    print(f"Repositories with BOMs: {results['repos_with_boms']}")
    print(f"Total BOMs found: {results['total_boms_found']}")
    print(f"Results saved to: {output_file}\n")
    
    # Print detailed patterns found
    print("BOM Patterns Found:")
    for repo in results['detailed_results']:
        if repo['bom_count'] > 0:
            print(f"\nRepository: {repo['repo_url']}")
            for pattern in repo['patterns']:
                print(f"- Type: {pattern['type']}")
                print(f"  Location: {pattern['path']}")
                if pattern['type'] == 'csv':
                    print(f"  Columns: {', '.join(pattern['columns'])}")
                elif pattern['type'] == 'markdown':
                    for table in pattern['tables']:
                        print(f"  Table Headers: {', '.join(table['headers'])}")

if __name__ == "__main__":
    main()
