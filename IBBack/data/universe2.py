"""Backward-compatible re-export — use data.universe_extension for new code."""
from data.universe_extension import (  # noqa: F401
    ALL_US_COMPANIES,
    DEMO_INDUSTRIES,
    GLOBAL_TICKERS,
    INDUSTRY_MAP,
    find_company,
    load_tickers,
    load_us_tickers,
    looks_like_ticker,
    normalize_ticker,
    suggest,
)

__all__ = [
    "DEMO_INDUSTRIES",
    "INDUSTRY_MAP",
    "ALL_US_COMPANIES",
    "GLOBAL_TICKERS",
    "load_tickers",
    "load_us_tickers",
    "find_company",
    "suggest",
    "looks_like_ticker",
    "normalize_ticker",
]
