from typing import Dict, List, Optional

DEFAULT_THRESHOLDS: Dict[str, float] = {
    # growth & profitability
    "rev_cagr_min": 0.05,      # 5%+
    "op_margin_min": 0.10,     # 10%+
    # leverage & coverage
    "nd_eq_max": 1.00,         # <= 1.0x
    "interest_cover_min": 4.0, # >= 4x
    # returns
    "roe_min": 0.10,           # >= 10%
}

def merge_thresholds(overrides: Dict[str, float] | None) -> Dict[str, float]:
    out = dict(DEFAULT_THRESHOLDS)
    if not overrides:
        return out
    for k, v in overrides.items():
        try:
            if k in out and isinstance(v, (int, float)):
                out[k] = float(v)
        except Exception:
            continue
    return out

def thresholds_from_params(
    *,
    rev_cagr_min: float | None = None,
    op_margin_min: float | None = None,
    nd_eq_max: float | None = None,
    interest_cover_min: float | None = None,
    roe_min: float | None = None,
) -> Dict[str, float]:
    overrides = {
        k: v for k, v in {
            "rev_cagr_min": rev_cagr_min,
            "op_margin_min": op_margin_min,
            "nd_eq_max": nd_eq_max,
            "interest_cover_min": interest_cover_min,
            "roe_min": roe_min,
        }.items() if v is not None
    }
    return merge_thresholds(overrides)
