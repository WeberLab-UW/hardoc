from typing import Dict, List, Optional
from dataclasses import dataclass
from .metrics import QualityMetrics

@dataclass
class ScoreExplanation:
    """Container for score explanation details."""
    score: float
    category: str
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    impact: str

class ScoreExplainer:
    """Generates human-readable explanations for quality scores."""
    
    def __init__(self):
        """Initialize ScoreExplainer with metrics and explanation templates."""
        self.metrics = QualityMetrics()
        
        self.impact_levels = {
            'critical': 'Has major impact on project reproducibility',
            'high': 'Significantly affects project usability',
            'medium': 'Moderately impacts project quality',
            'low': 'Minor impact on overall quality'
        }
        
        self.explanation_templates = {
            'part_number_quality': {
                'high': "Part numbers are specific and well-documented",
                'medium': "Most parts have identifiable numbers",
                'low': "Many parts lack specific identification",
                'impact': 'critical'
            },
            'manufacturer_info': {
                'high': "Manufacturer information is complete",
                'medium': "Basic manufacturer details provided",
                'low': "Limited manufacturer information",
                'impact': 'high'
            },
            'datasheet_links': {
                'high': "Comprehensive datasheet coverage",
                'medium': "Most critical components have datasheets",
                'low': "Missing many important datasheets",
                'impact': 'high'
            },
            'alternative_parts': {
                'high': "Good alternative parts coverage",
                'medium': "Some alternative parts listed",
                'low': "Few or no alternative parts",
                'impact': 'medium'
            },
            'cost_info': {
                'high': "Detailed cost information available",
                'medium': "Basic cost information provided",
                'low': "Limited or no cost information",
                'impact': 'medium'
            }
        }

    def explain_score(self, category: str, score: float) -> ScoreExplanation:
        """
        Generate detailed explanation for a category score.
        
        Args:
            category: Score category to explain
            score: Numeric score to explain
            
        Returns:
            ScoreExplanation: Detailed explanation of the score
        """
        templates = self.explanation_templates.get(category, {})
        score_category = self.metrics.get_score_category(score)
        
        strengths = []
        weaknesses = []
        recommendations = []
        
        # Determine strengths and weaknesses
        if score >= 0.75:
            strengths.append(templates.get('high', 'Good quality'))
        elif score >= 0.5:
            strengths.append(templates.get('medium', 'Acceptable quality'))
            weaknesses.append("Room for improvement")
        else:
            weaknesses.append(templates.get('low', 'Needs improvement'))
        
        # Generate recommendations
        recommendations.extend(self._generate_category_recommendations(category, score))
        
        return ScoreExplanation(
            score=score,
            category=score_category,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            impact=templates.get('impact', 'medium')
        )

    def explain_overall_score(self, scores: Dict[str, float]) -> Dict:
        """
        Generate comprehensive explanation for overall quality score.
        
        Args:
            scores: Dictionary of scores by category
            
        Returns:
            Dict: Detailed explanation of overall quality
        """
        overall_score = self.metrics.calculate_overall_score(scores)
        explanations = {
            'overall_score': overall_score,
            'category': self.metrics.get_score_category(overall_score),
            'summary': self._generate_summary(scores),
            'categories': {},
            'key_improvements': [],
            'quick_wins': []
        }
        
        # Generate category-specific explanations
        for category, score in scores.items():
            explanations['categories'][category] = self.explain_score(category, score)
        
        # Identify key improvements needed
        improvement_potential = self.metrics.get_improvement_potential(scores)
        for improvement in improvement_potential:
            if improvement['priority'] == 'high':
                explanations['key_improvements'].append(
                    f"Focus on improving {improvement['category']} "
                    f"(potential gain: {improvement['potential_gain']:.2f})"
                )
            elif improvement['priority'] == 'medium':
                explanations['quick_wins'].append(
                    f"Consider enhancing {improvement['category']}"
                )
        
        return explanations

    def _generate_category_recommendations(self, category: str, score: float) -> List[str]:
        """Generate specific recommendations for a category."""
        recommendations = []
        
        if category == 'part_number_quality':
            if score < 0.8:
                recommendations.append("Use manufacturer part numbers where possible")
                recommendations.append("Avoid generic descriptors")
            if score < 0.5:
                recommendations.append("Add detailed part specifications")
                
        elif category == 'manufacturer_info':
            if score < 0.7:
                recommendations.append("Include manufacturer names for all components")
                recommendations.append("Add manufacturer contact or ordering information")
                
        elif category == 'datasheet_links':
            if score < 0.9:
                recommendations.append("Provide datasheet links for all components")
            if score < 0.5:
                recommendations.append("Verify and update broken datasheet links")
                
        elif category == 'alternative_parts':
            if score < 0.6:
                recommendations.append("List alternative parts for critical components")
                recommendations.append("Include cross-reference information")
                
        elif category == 'cost_info':
            if score < 0.7:
                recommendations.append("Add unit costs for components")
                recommendations.append("Include currency information")
        
        return recommendations

    def _generate_summary(self, scores: Dict[str, float]) -> str:
        """Generate an overall summary of documentation quality."""
        overall_score = self.metrics.calculate_overall_score(scores)
        meets_minimum = self.metrics.meets_minimum_requirements(scores)
        
        if overall_score >= 0.9:
            return "Excellent documentation quality with comprehensive component information"
        elif overall_score >= 0.75:
            return "Good documentation quality with some room for improvement"
        elif overall_score >= 0.5:
            if meets_minimum:
                return "Acceptable documentation with several areas needing improvement"
            else:
                return "Documentation meets basic needs but requires significant enhancement"
        else:
            return "Documentation needs substantial improvement for project reproducibility"

    def get_impact_explanation(self, category: str) -> str:
        """Get explanation of category's impact on project quality."""
        template = self.explanation_templates.get(category, {})
        impact_level = template.get('impact', 'medium')
        return self.impact_levels.get(impact_level, 'Affects project quality')