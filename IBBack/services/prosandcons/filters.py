from __future__ import annotations
import re, math
from typing import List

try:
    from IBBack.models.schemas2 import Finding
except Exception:
    try:
        from models.schemas2 import Finding
    except Exception:
        class Finding:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

# Regex patterns
BANNED_PHRASES_RE = re.compile(r"\b(strong top[- ]?line growth|high operating margins?|solid roe|robust fundamentals?|leading position|poised to (grow|benefit)|strong balance sheet|healthy margins?)\b", re.I)
CAUSAL_CLUES_RE = re.compile(r"\b(because|driven by|due to|as|after|therefore|which|leading to|resulting in)\b", re.I)
NUM_RE = re.compile(r"(?<![A-Za-z])(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%?")

def extract_numbers(text: str) -> List[str]:
    return [m.replace(',', '') for m in NUM_RE.findall(text or '')]

def numbers_consistent(item: str, snippets: List[str]) -> bool:
    nums_item = extract_numbers(item)
    if not nums_item:
        return True
    joined = ' '.join(snippets or [])
    nums_snip = set(extract_numbers(joined))
    if not nums_snip:  # allow if evidence has no numbers
        return True
    for n in nums_item:
        if n in nums_snip:
            return True
        try:
            if n.endswith('%'):
                ni = float(n[:-1])
                for s in nums_snip:
                    if s.endswith('%') and math.isclose(ni, float(s[:-1]), rel_tol=1e-3, abs_tol=1e-2):
                        return True
            else:
                for s in nums_snip:
                    if not s.endswith('%') and math.isclose(float(n), float(s), rel_tol=1e-3, abs_tol=1e-2):
                        return True
        except Exception:
            continue
    return False

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or '').strip().lower())

def _sim(a: str, b: str) -> float:
    sa, sb = set(_norm(a).split()), set(_norm(b).split())
    if not sa or not sb:
        return 0.0
    inter = len(sa & sb)
    union = len(sa | sb)
    return inter / union

def dedup_keep_best(items: List[Finding], threshold: float = 0.65) -> List[Finding]:
    kept: List[Finding] = []
    for f in sorted(items, key=lambda x: float(getattr(x, 'materiality', 0.5)), reverse=True):
        if any(_sim(f.item, g.item) >= threshold for g in kept):
            continue
        kept.append(f)
    return kept

__all__ = [
    'BANNED_PHRASES_RE','CAUSAL_CLUES_RE','numbers_consistent','dedup_keep_best'
]