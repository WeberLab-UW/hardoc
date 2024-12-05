from typing import Dict, List, Optional
import pandas as pd
import re
from urllib.parse import urlparse
import logging
from ..scoring.metrics import QualityMetrics

class ComponentAnalyzer:
    """Analyzer for evaluating component documentation quality in BOMs."""
    
    def __init__(self):
        """Initialize ComponentAnalyzer with quality metrics and patterns."""
        self.metrics = QualityMetrics()
        self.logger = logging.getLogger(__name__)
        
        # Patterns for component analysis
        self.patterns = {
            'manufacturer_pn': r'^[A-Z0-9\-]{4,}$',  # Basic manufacturer part number
            'generic_component': r'^[a-zA-Z]+\d+$',   # Generic components like 'R1', 'C1'
            'value_spec': r'\d+(\.\d+)?\s*(k|M|u|n|p|m|μ)?(Ω|F|H|V|A)'  # Value specifications
        }
        
        # Common column indicators
        self.column_indicators = {
            'manufacturer': ['manufacturer', 'mfg', 'vendor', 'supplier', 'brand'],
            'datasheet': ['datasheet', 'documentation', 'spec', 'link'],
            'cost': ['cost', 'price', 'unit cost'],
            'alternatives': ['alternative', 'substitute', 'replacement']
        }

    def analyze_component_quality(self, df: pd.DataFrame) -> Dict:
        """
        Analyze component documentation quality from a BOM DataFrame.
        
        Args:
            df: DataFrame containing BOM data
            
        Returns:
            Dict containing quality analysis results and scores
        """
        try:
            analysis = {
                'part_number_quality': self._analyze_part_numbers(df),
                'manufacturer_info': self._analyze_manufacturer_info(df),
                'datasheet_links': self._analyze_datasheet_links(df),
                'alternative_parts': self._analyze_alternative_parts(df),
                'cost_info': self._analyze_cost_info(df)
            }
            
            # Calculate overall score
            analysis['overall_score'] = self.metrics.calculate_overall_score(
                {k: v['score'] for k, v in analysis.items() if k != 'overall_score'}
            )
            
            # Generate recommendations
            analysis['recommendations'] = self._generate_recommendations(analysis)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing components: {e}")
            return self._generate_error_analysis()

    def _analyze_part_numbers(self, df: pd.DataFrame) -> Dict:
        """Analyze quality and specificity of part numbers."""
        total_components = len(df)
        part_number_cols = self._find_columns(df, ['part', 'number', 'pn', 'mpn'])
        
        results = {
            'has_part_numbers': bool(part_number_cols),
            'total_components': total_components,
            'specific_parts': 0,
            'generic_parts': 0,
            'value_only_parts': 0,
            'empty_parts': 0,
            'specificity': 'unknown',
            'score': 0.0
        }
        
        if not part_number_cols:
            return results
            
        for col in part_number_cols:
            for value in df[col].dropna():
                value_str = str(value)
                if re.match(self.patterns['manufacturer_pn'], value_str):
                    results['specific_parts'] += 1
                elif re.match(self.patterns['generic_component'], value_str):
                    results['generic_parts'] += 1
                elif re.match(self.patterns['value_spec'], value_str):
                    results['value_only_parts'] += 1
                    
        results['empty_parts'] = total_components - (
            results['specific_parts'] + results['generic_parts'] + 
            results['value_only_parts']
        )
        
        # Calculate specificity score
        if total_components > 0:
            specificity_score = (results['specific_parts'] / total_components) * 100
            results['score'] = specificity_score / 100
            if specificity_score > 80:
                results['specificity'] = 'high'
            elif specificity_score > 50:
                results['specificity'] = 'medium'
            else:
                results['specificity'] = 'low'
                
        return results

    def _analyze_manufacturer_info(self, df: pd.DataFrame) -> Dict:
        """Analyze presence and quality of manufacturer information."""
        mfg_cols = self._find_columns(df, self.column_indicators['manufacturer'])
        total_components = len(df)
        
        results = {
            'has_manufacturer_info': bool(mfg_cols),
            'manufacturer_columns': mfg_cols,
            'components_with_mfg': 0,
            'score': 0.0
        }
        
        if mfg_cols and total_components > 0:
            components_with_mfg = 0
            for col in mfg_cols:
                components_with_mfg += df[col].notna().sum()
            results['components_with_mfg'] = components_with_mfg
            results['score'] = min(components_with_mfg / total_components, 1.0)
            
        return results

    def _analyze_datasheet_links(self, df: pd.DataFrame) -> Dict:
        """Analyze presence and validity of datasheet links."""
        ds_cols = self._find_columns(df, self.column_indicators['datasheet'])
        
        results = {
            'has_datasheet_links': False,
            'total_links': 0,
            'valid_links': 0,
            'broken_links': 0,
            'score': 0.0
        }
        
        if not ds_cols:
            return results
            
        results['has_datasheet_links'] = True
        
        for col in ds_cols:
            for value in df[col].dropna():
                if isinstance(value, str) and ('http' in value or 'www' in value):
                    results['total_links'] += 1
                    if self._is_valid_url(value):
                        results['valid_links'] += 1
                    else:
                        results['broken_links'] += 1
                        
        if results['total_links'] > 0:
            results['score'] = results['valid_links'] / results['total_links']
            
        return results

    def _analyze_alternative_parts(self, df: pd.DataFrame) -> Dict:
        """Analyze presence of alternative part suggestions."""
        alt_cols = self._find_columns(df, self.column_indicators['alternatives'])
        total_components = len(df)
        
        results = {
            'has_alternatives': bool(alt_cols),
            'components_with_alternatives': 0,
            'score': 0.0
        }
        
        if alt_cols and total_components > 0:
            for col in alt_cols:
                results['components_with_alternatives'] += df[col].notna().sum()
            results['score'] = min(
                results['components_with_alternatives'] / total_components, 
                1.0
            )
            
        return results

    def _analyze_cost_info(self, df: pd.DataFrame) -> Dict:
        """Analyze presence and quality of cost information."""
        cost_cols = self._find_columns(df, self.column_indicators['cost'])
        total_components = len(df)
        
        results = {
            'has_cost_info': bool(cost_cols),
            'components_with_cost': 0,
            'has_currency': False,
            'score': 0.0
        }
        
        if cost_cols and total_components > 0:
            for col in cost_cols:
                components_with_cost = df[col].notna().sum()
                results['components_with_cost'] = components_with_cost
                # Check for currency symbols in string representation
                results['has_currency'] = any(
                    df[col].astype(str).str.contains(r'[$€£¥]')
                )
                results['score'] = min(components_with_cost / total_components, 1.0)
                
        return results

    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """Generate improvement recommendations based on analysis results."""
        recommendations = []
        
        if analysis['part_number_quality']['score'] < 0.8:
            recommendations.append(
                "Improve part number specificity by using manufacturer part numbers"
            )
            
        if analysis['manufacturer_info']['score'] < 0.8:
            recommendations.append("Add manufacturer information for components")
            
        if not analysis['datasheet_links']['has_datasheet_links']:
            recommendations.append("Include datasheet links for components")
        elif analysis['datasheet_links']['broken_links'] > 0:
            recommendations.append("Fix broken datasheet links")
            
        if not analysis['alternative_parts']['has_alternatives']:
            recommendations.append("Consider adding alternative part suggestions")
            
        if not analysis['cost_info']['has_cost_info']:
            recommendations.append("Add cost information for better project planning")
            
        return recommendations

    @staticmethod
    def _find_columns(df: pd.DataFrame, keywords: List[str]) -> List[str]:
        """Find columns matching keywords."""
        matched_cols = []
        for col in df.columns:
            if any(keyword.lower() in col.lower() for keyword in keywords):
                matched_cols.append(col)
        return matched_cols

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """Basic URL validation."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    @staticmethod
    def _generate_error_analysis() -> Dict:
        """Generate an error state analysis result."""
        return {
            'overall_score': 0.0,
            'part_number_quality': {'score': 0.0, 'error': True},
            'manufacturer_info': {'score': 0.0, 'error': True},
            'datasheet_links': {'score': 0.0, 'error': True},
            'alternative_parts': {'score': 0.0, 'error': True},
            'cost_info': {'score': 0.0, 'error': True},
            'recommendations': ['Error analyzing components']
        }