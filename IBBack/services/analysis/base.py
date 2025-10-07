"""Base analyzer class with shared utilities."""
from typing import Any, Optional

# yfinance period presets
ALLOWED_PERIODS = {"1d","5d","1mo","3mo","6mo","1y","2y","5y","10y","ytd","max"}


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
        return val if val in ALLOWED_PERIODS else None
    
    def coalesce(self, *values: Any) -> Optional[Any]:
        """Return first non-None value."""
        for v in values:
            if v is not None:
                return v
        return None