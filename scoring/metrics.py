from typing import Dict, List, Union
import logging
from dataclasses import dataclass

@dataclass
class ScoreWeights:
    """Weights for different components in quality scoring."""
    part_number_quality: float = 0.30
    manufacturer_info: float = 0.20
    datasheet_links: float = 0.20
    alternative_parts: float = 0.15
    cost_info: float = 0.15

class QualityMetrics:
    """Calculate and manage quality metrics for documentation analysis."""
    
    def __init__(self):
        """Initialize QualityMetrics with default weights."""
        self.weights = ScoreWeights()
        self.logger = logging.getLogger(__name__)
        
        # Scoring thresholds
        self.thresholds = {
            'excellent': 0.90,
            'good': 0.75,
            'fair': 0.50,
            'poor': 0.25
        }

    def calculate_overall_score(self, scores: Dict[str, float]) -> float:
        """
        Calculate weighted overall quality score.
        
        Args:
            scores: Dictionary of individual scores by category
            
        Returns:
            float: Weighted overall score between 0 and 1
        """
        try:
            weighted_sum = 0.0
            total_weight = 0.0
            
            for category, score in scores.items():
                if hasattr(self.weights, category):
                    weight = getattr(self.weights, category)
                    weighted_sum += score * weight
                    total_weight += weight
            
            if total_weight > 0:
                return round(weighted_sum / total_weight, 2)
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating overall score: {e}")
            return 0.0

    def get_score_category(self, score: float) -> str:
        """
        Get categorical rating for a numeric score.
        
        Args:
            score: Numeric score between 0 and 1
            
        Returns:
            str: Category label for the score
        """
        if score >= self.thresholds['excellent']:
            return 'excellent'
        elif score >= self.thresholds['good']:
            return 'good'
        elif score >= self.thresholds['fair']:
            return 'fair'
        elif score >= self.thresholds['poor']:
            return 'poor'
        return 'inadequate'

    def normalize_score(self, score: float) -> float:
        """
        Normalize a score to ensure it's between 0 and 1.
        
        Args:
            score: Raw score to normalize
            
        Returns:
            float: Normalized score between 0 and 1
        """
        return max(0.0, min(1.0, score))

    def calculate_weighted_subscores(self, scores: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        """
        Calculate weighted subscores for each category.
        
        Args:
            scores: Dictionary of raw scores by category
            
        Returns:
            Dict: Categories with their raw and weighted scores
        """
        weighted_scores = {}
        for category, score in scores.items():
            if hasattr(self.weights, category):
                weight = getattr(self.weights, category)
                weighted_scores[category] = {
                    'raw_score': score,
                    'weighted_score': score * weight,
                    'weight': weight,
                    'category': self.get_score_category(score)
                }
        return weighted_scores

    def get_improvement_potential(self, scores: Dict[str, float]) -> List[Dict[str, Union[str, float]]]:
        """
        Identify areas with the most potential for improvement.
        
        Args:
            scores: Dictionary of scores by category
            
        Returns:
            List: Categories sorted by improvement potential
        """
        potential_improvements = []
        weighted_scores = self.calculate_weighted_subscores(scores)
        
        for category, details in weighted_scores.items():
            improvement_potential = (1.0 - details['raw_score']) * details['weight']
            potential_improvements.append({
                'category': category,
                'current_score': details['raw_score'],
                'potential_gain': improvement_potential,
                'priority': 'high' if improvement_potential > 0.15 else 'medium' if improvement_potential > 0.05 else 'low'
            })
        
        # Sort by potential gain (highest first)
        return sorted(potential_improvements, key=lambda x: x['potential_gain'], reverse=True)

    def adjust_weights(self, new_weights: Dict[str, float]) -> None:
        """
        Adjust scoring weights for different categories.
        
        Args:
            new_weights: Dictionary of new weights to apply
            
        Raises:
            ValueError: If weights don't sum to 1.0 or invalid category
        """
        # Validate new weights
        total = sum(new_weights.values())
        if not (0.99 <= total <= 1.01):  # Allow for small floating-point differences
            raise ValueError(f"Weights must sum to 1.0 (got {total})")
        
        # Update weights if valid
        for category, weight in new_weights.items():
            if hasattr(self.weights, category):
                setattr(self.weights, category, weight)
            else:
                raise ValueError(f"Invalid category: {category}")

    def get_minimum_requirements(self) -> Dict[str, float]:
        """
        Get minimum score requirements for each category.
        
        Returns:
            Dict: Minimum required scores by category
        """
        return {
            'part_number_quality': 0.6,  # Must have specific part numbers
            'manufacturer_info': 0.5,    # Basic manufacturer information
            'datasheet_links': 0.7,      # Most components should have datasheets
            'alternative_parts': 0.3,     # Some alternative parts recommended
            'cost_info': 0.4             # Basic cost information
        }

    def meets_minimum_requirements(self, scores: Dict[str, float]) -> bool:
        """
        Check if scores meet minimum requirements.
        
        Args:
            scores: Dictionary of scores by category
            
        Returns:
            bool: True if minimum requirements are met
        """
        minimums = self.get_minimum_requirements()
        return all(
            scores.get(category, 0) >= min_score
            for category, min_score in minimums.items()
        )