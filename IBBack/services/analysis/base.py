"""Base analyzer class with shared utilities."""
from typing import Any, Optional

# yfinance period presets
ALLOWED_PERIODS = {"1d","5d","1mo","3mo","6m","6mo","1y","2y","3y","5y","10y","ytd","max"}


class BaseAnalyzer:
    """Base class for all analyzers with shared utilities."""
    
    def __init__(self):
        """Initialize base analyzer."""
        pass
    
    @staticmethod
    def normalize_period(s: Optional[str]) -> Optional[str]:
        if not s:
            return None
        val = str(s).strip().lower()
        if val == "all":
            val = "max"
        if val == "6m":
            val = "6mo"
        return val if val in ALLOWED_PERIODS else None

    @staticmethod
    def uses_quarterly_roe(period: Optional[str], years: Optional[int] = None) -> bool:
        """Quarterly ROE for short windows only; longer presets use annual filings."""
        p = BaseAnalyzer.normalize_period(period)
        return p in ("6mo", "1y")

    @staticmethod
    def resolve_chart_years(period: Optional[str], years: Optional[int] = None) -> Optional[int]:
        """Fiscal-year span for annual ROE chart filtering."""
        p = BaseAnalyzer.normalize_period(period)
        if p == "max":
            return None
        if years is not None:
            return years
        if p and p.endswith("y") and p[:-1].isdigit():
            return int(p[:-1])
        return 5

    @staticmethod
    def resolve_lookback_months(period: Optional[str], years: Optional[int] = None) -> Optional[int]:
        """Map UI period preset to months of ROE history for chart filtering."""
        p = BaseAnalyzer.normalize_period(period)
        if p == "6mo":
            return 6
        if p == "1y":
            return 12
        if p == "2y":
            return 24
        if p == "3y":
            return 36
        if p == "5y":
            return 60
        if p == "10y":
            return 120
        if p == "max":
            return None
        if years is not None:
            return years * 12
        return None

    @staticmethod
    def resolve_analysis_years(years: Optional[int], period: Optional[str]) -> Optional[int]:
        """Map UI period preset to fiscal-year lookback. None = all available history."""
        p = BaseAnalyzer.normalize_period(period)
        if p == "max":
            return None
        if p == "6mo":
            return 1  # scorecard metrics use ~1y when viewing 6m chart
        if years is not None:
            return years
        if p and p.endswith("y") and p[:-1].isdigit():
            return int(p[:-1])
        return 5
    
    def coalesce(self, *values: Any) -> Optional[Any]:
        """Return first non-None value."""
        for v in values:
            if v is not None:
                return v
        return None