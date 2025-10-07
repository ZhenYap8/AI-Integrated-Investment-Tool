"""Threshold management for financial analysis."""
from typing import Dict


class ThresholdManager:
    """Manages financial analysis thresholds."""
    
    DEFAULT_THRESHOLDS: Dict[str, float] = {
        "rev_cagr_min": 0.05,
        "op_margin_min": 0.10,
        "nd_eq_max": 1.00,
        "interest_cover_min": 4.0,
        "roe_min": 0.10,
    }
    
    @classmethod
    def merge_thresholds(cls, overrides: Dict[str, float] | None) -> Dict[str, float]:
        out = dict(cls.DEFAULT_THRESHOLDS)
        if not overrides:
            return out
        for k, v in overrides.items():
            try:
                if k in out and isinstance(v, (int, float)):
                    out[k] = float(v)
            except Exception:
                continue
        return out
    
    @classmethod
    def from_params(cls, **kwargs) -> Dict[str, float]:
        overrides = {k: v for k, v in kwargs.items() if v is not None}
        return cls.merge_thresholds(overrides)