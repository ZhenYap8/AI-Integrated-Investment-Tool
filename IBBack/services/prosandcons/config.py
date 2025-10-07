from __future__ import annotations
import os
from functools import lru_cache

try:
    from dotenv import load_dotenv  # type: ignore
    _BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    for _cand in (
        os.path.join(_BASE, '.env'),
        os.path.join(_BASE, '..', '.env'),
    ):
        if os.path.exists(_cand):
            load_dotenv(_cand)
            break
except Exception:
    pass

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_API_BASE = (os.getenv('OPENAI_API_BASE') or 'https://api.openai.com/v1').rstrip('/')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4.1')
OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', '2200'))
OPENAI_SEED = int(os.getenv('OPENAI_SEED', '7'))
OPENAI_TIMEOUT = int(os.getenv('OPENAI_TIMEOUT', '45'))

@lru_cache(maxsize=1)
def openai_enabled() -> bool:
    return bool(OPENAI_API_KEY)

__all__ = [
    'OPENAI_API_KEY','OPENAI_API_BASE','OPENAI_MODEL','OPENAI_MAX_TOKENS','OPENAI_SEED','OPENAI_TIMEOUT','openai_enabled'
]
