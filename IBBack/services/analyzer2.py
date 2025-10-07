"""Financial analysis service - refactored with modular components."""
from typing import Dict, Optional
from models.schemas2 import AnalyzeResponse
from services.analysis import FinancialAnalyzer
from services.analysis.thresholds import ThresholdManager

# Global analyzer instance
_analyzer = FinancialAnalyzer()

# Public API functions (maintain backward compatibility)
def analyze_company(ticker: str, years: int, thresh: Dict[str, float], period: Optional[str] = None) -> AnalyzeResponse:
    return _analyzer.analyze_company(ticker, years, thresh, period)

def analyze_industry(industry: str, years: int, thresh: Dict[str, float], period: Optional[str] = None) -> AnalyzeResponse:
    return _analyzer.analyze_industry(industry, years, thresh, period)

def cleanup_cache(max_age_seconds: int = 600):
    return _analyzer.cleanup_cache(max_age_seconds)

# Threshold management functions (backward compatibility)
def merge_thresholds(overrides: Dict[str, float] | None) -> Dict[str, float]:
    return ThresholdManager.merge_thresholds(overrides)

def thresholds_from_params(
    *,
    rev_cagr_min: float | None = None,
    op_margin_min: float | None = None,
    nd_eq_max: float | None = None,
    interest_cover_min: float | None = None,
    roe_min: float | None = None,
) -> Dict[str, float]:
    return ThresholdManager.from_params(
        rev_cagr_min=rev_cagr_min,
        op_margin_min=op_margin_min,
        nd_eq_max=nd_eq_max,
        interest_cover_min=interest_cover_min,
        roe_min=roe_min,
    )

# Export default thresholds for backward compatibility
DEFAULT_THRESHOLDS = ThresholdManager.DEFAULT_THRESHOLDS
