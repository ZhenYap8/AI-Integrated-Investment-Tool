from __future__ import annotations
import os
from functools import lru_cache

# Embedded config (from proscons_config.py) for fallback if prosandcons unavailable
try:
    from dotenv import load_dotenv  # type: ignore
    _BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    for _p in (
        os.path.join(_BASE_DIR, '.env'),
        os.path.join(_BASE_DIR, '..', '.env'),
    ):
        if os.path.exists(_p):
            load_dotenv(_p)
            break
except Exception:
    pass

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

@lru_cache(maxsize=1)
def openai_enabled() -> bool:
    return bool(OPENAI_API_KEY)

# Main import - prefer prosandcons package
try:
    from .prosandcons import analyze_proscons_ai_only
except Exception as e:
    # Fallback warning if modular package fails
    def analyze_proscons_ai_only(*args, **kwargs):
        print(f"[proscons] ERROR: prosandcons package unavailable ({e})")
        # Return minimal response structure
        import datetime as dt
        class _Response:
            def __init__(self):
                self.company = args[0] if args else "UNKNOWN"
                self.asOf = dt.date.today().isoformat()
                self.findings = []
                self.fromAI = openai_enabled()
        return _Response()

__all__ = ["analyze_proscons_ai_only", "openai_enabled"]
