"""Ticker data caching with TTL for financial analysis."""
import time
from typing import Dict, Tuple, Any

from utils.finance2 import get_yf_ticker


class TickerCache:
    """Manages ticker data caching with TTL."""
    
    def __init__(self, ttl_seconds: int = 300):
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._ttl = ttl_seconds
    
    def get(self, ticker: str):
        """Get cached ticker or fetch if expired/missing."""
        now = time.time()
        if ticker in self._cache:
            data, timestamp = self._cache[ticker]
            if now - timestamp < self._ttl:
                return data
        
        # Fetch and cache
        data = get_yf_ticker(ticker)
        self._cache[ticker] = (data, now)
        return data
    
    def cleanup(self, max_age_seconds: int = 600):
        """Remove stale entries to prevent memory bloat."""
        now = time.time()
        stale_keys = [
            k for k, (_, timestamp) in self._cache.items()
            if now - timestamp > max_age_seconds
        ]
        for k in stale_keys:
            del self._cache[k]