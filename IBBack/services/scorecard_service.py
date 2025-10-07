"""
Scorecard Service - Generates verdict-based scorecard from financial metrics.

This service takes financial metrics and compares them against configurable
thresholds to produce a scorecard with green/red/amber verdicts.
"""

class ScorecardService:
    """Service for generating financial metric scorecards with verdicts."""
    
    def __init__(self):
        """Initialize the scorecard service with default thresholds."""
        self.default_thresholds = {
            'rev_cagr_min': 0.05,      # 5%
            'op_margin_min': 0.10,     # 10%
            'nd_eq_max': 1.0,          # 1.0x
            'interest_cover_min': 4.0, # 4.0x
            'roe_min': 0.10            # 10%
        }
    
    def build_scorecard(self, metrics: dict, overrides: dict = None, years: int = 5):
        """
        Build a scorecard with verdicts based on financial metrics and thresholds.
        
        Args:
            metrics: Dictionary of financial metrics from the analyzer
            overrides: Optional dictionary of threshold overrides
            years: Number of years for CAGR calculation (default 5)
            
        Returns:
            List of scorecard items with verdicts
        """
        if overrides is None:
            overrides = {}
        
        # Merge overrides with defaults
        thresholds = {**self.default_thresholds, **overrides}
        
        scorecard = []
        
        # Build scorecard items for each metric
        if metrics.get('revenue_cagr') is not None:
            scorecard.append(self._build_revenue_cagr_item(metrics['revenue_cagr'], thresholds, years))
        
        if metrics.get('operating_margin') is not None:
            scorecard.append(self._build_operating_margin_item(metrics['operating_margin'], thresholds))
        
        if metrics.get('net_debt_to_equity') is not None:
            scorecard.append(self._build_net_debt_equity_item(metrics['net_debt_to_equity'], thresholds))
        
        if metrics.get('interest_coverage') is not None:
            scorecard.append(self._build_interest_coverage_item(metrics['interest_coverage'], thresholds))
        
        if metrics.get('roe') is not None:
            scorecard.append(self._build_roe_item(metrics['roe'], thresholds))
        
        return scorecard
    
    def _build_revenue_cagr_item(self, value: float, thresholds: dict, years: int):
        """Build revenue CAGR scorecard item."""
        value_pct = value * 100
        threshold_pct = thresholds['rev_cagr_min'] * 100
        verdict = 'green' if value >= thresholds['rev_cagr_min'] else 'red'
        
        return {
            'id': 'rev_cagr',
            'label': f'Revenue CAGR ({years}y)',
            'value': round(value_pct, 1),
            'threshold': round(threshold_pct, 1),
            'unit': '%',
            'verdict': verdict,
            'detail': f'Actual: {value_pct:.1f}% vs Target: {threshold_pct:.1f}%'
        }
    
    def _build_operating_margin_item(self, value: float, thresholds: dict):
        """Build operating margin scorecard item."""
        value_pct = value * 100
        threshold_pct = thresholds['op_margin_min'] * 100
        verdict = 'green' if value >= thresholds['op_margin_min'] else 'red'
        
        return {
            'id': 'op_margin',
            'label': 'Operating Margin',
            'value': round(value_pct, 1),
            'threshold': round(threshold_pct, 1),
            'unit': '%',
            'verdict': verdict,
            'detail': f'Actual: {value_pct:.1f}% vs Target: {threshold_pct:.1f}%'
        }
    
    def _build_net_debt_equity_item(self, value: float, thresholds: dict):
        """Build net debt to equity scorecard item."""
        verdict = 'green' if value <= thresholds['nd_eq_max'] else 'red'
        
        return {
            'id': 'nd_eq',
            'label': 'Net Debt / Equity',
            'value': round(value, 2),
            'threshold': round(thresholds['nd_eq_max'], 2),
            'unit': 'x',
            'verdict': verdict,
            'detail': f'Actual: {value:.2f}x vs Max: {thresholds["nd_eq_max"]:.2f}x'
        }
    
    def _build_interest_coverage_item(self, value: float, thresholds: dict):
        """Build interest coverage scorecard item."""
        verdict = 'green' if value >= thresholds['interest_cover_min'] else 'red'
        
        return {
            'id': 'interest_cover',
            'label': 'Interest Coverage',
            'value': round(value, 1),
            'threshold': round(thresholds['interest_cover_min'], 1),
            'unit': 'x',
            'verdict': verdict,
            'detail': f'Actual: {value:.1f}x vs Min: {thresholds["interest_cover_min"]:.1f}x'
        }
    
    def _build_roe_item(self, value: float, thresholds: dict):
        """Build ROE scorecard item."""
        value_pct = value * 100
        threshold_pct = thresholds['roe_min'] * 100
        verdict = 'green' if value >= thresholds['roe_min'] else 'red'
        
        return {
            'id': 'roe',
            'label': 'Return on Equity (ROE)',
            'value': round(value_pct, 1),
            'threshold': round(threshold_pct, 1),
            'unit': '%',
            'verdict': verdict,
            'detail': f'Actual: {value_pct:.1f}% vs Target: {threshold_pct:.1f}%'
        }


# Convenience function for backward compatibility
def build_scorecard(metrics: dict, overrides: dict = None, years: int = 5):
    """
    Build a scorecard using the ScorecardService.
    This is a convenience function that maintains backward compatibility.
    """
    service = ScorecardService()
    return service.build_scorecard(metrics, overrides, years)