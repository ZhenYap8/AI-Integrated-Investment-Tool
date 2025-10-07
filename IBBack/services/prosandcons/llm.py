from __future__ import annotations
import json, datetime as dt, requests
from typing import List, Optional
from .config import (
    OPENAI_API_KEY, OPENAI_API_BASE, OPENAI_MODEL,
    OPENAI_MAX_TOKENS, OPENAI_SEED, OPENAI_TIMEOUT,
)
try:
    from IBBack.models.schemas2 import Finding, Evidence
except Exception:
    try:
        from models.schemas2 import Finding, Evidence
    except Exception:
        # Minimal stubs if models unavailable
        class Finding:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        class Evidence:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

from .filters import (
    BANNED_PHRASES_RE, CAUSAL_CLUES_RE,
    numbers_consistent, dedup_keep_best
)

_SYSTEM_RULES = (
    "You are an equity analyst. Return a JSON OBJECT with key 'findings' (ARRAY).\n"
    "Each finding: item (2–3 sentences; explain mechanism + WHY IT MATTERS), factor [growth|margins|leverage|competition|guidance|legal_esg|other], "
    "direction 'pro'|'con', timeframe [near_term|multi_year|unspecified], materiality 0..1, evidence: [ {url, date:'YYYY-MM-DD', snippet<=300} ].\n"
    "Rules:\n"
    "- Forbidden boilerplate: 'Strong top-line growth', 'High operating margins', 'Solid ROE', 'robust fundamentals', 'leading position', 'poised to grow/benefit', 'strong balance sheet', 'healthy margins'.\n"
    "- Provide causal/company-specific reasoning with metrics (%, x, $, bps) or named catalysts/events.\n"
    "- Use ONLY the supplied Yahoo Finance snapshot + News abstracts; cite their URLs.\n"
    "- Rank by decision-useful materiality; mix pros and cons when both exist."
)

_DEF_MIN_LEN = 110  # slightly relaxed for recall


def _build_messages(context: str, max_items: int, focus: Optional[str]) -> list:
    if focus == 'cons':
        goal = f"Extract up to {max_items} CONS only (direction='con'), each 2–3 sentence causal, company-specific finding."
    else:
        goal = f"Extract up to {max_items} pros AND cons, each 2–3 sentence causal, company-specific finding."
    user = goal + "\nContext:\n" + context
    return [
        {"role": "system", "content": _SYSTEM_RULES},
        {"role": "user", "content": user},
    ]


def llm_findings(context: str, *, max_items: int = 8, focus: Optional[str] = None) -> List[Finding]:
    if not OPENAI_API_KEY:
        return []
    payload = {
        "model": OPENAI_MODEL,
        "messages": _build_messages(context, max_items, focus),
        "temperature": 0.1,
        "top_p": 0.2,
        "max_tokens": OPENAI_MAX_TOKENS,
        "seed": OPENAI_SEED,
        "response_format": {"type": "json_object"},
    }
    try:
        resp = requests.post(
            f"{OPENAI_API_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            data=json.dumps(payload),
            timeout=OPENAI_TIMEOUT,
        )
        resp.raise_for_status()
        raw_content = resp.json()["choices"][0]["message"]["content"]
        obj = json.loads(raw_content)
        raw_items = obj if isinstance(obj, list) else (obj.get("findings") or [])
    except Exception:
        return []

    out: List[Finding] = []
    for it in raw_items:
        try:
            item = (it.get("item") or "").strip()
            if not item or len(item) < _DEF_MIN_LEN:
                continue
            if BANNED_PHRASES_RE.search(item):
                continue
            if not CAUSAL_CLUES_RE.search(item):
                continue
            factor = (it.get("factor") or "other").strip()
            direction = (it.get("direction") or "con").strip()
            timeframe = (it.get("timeframe") or "unspecified").strip()
            mat = float(it.get("materiality", 0.5))
            evs = it.get("evidence") or []
            if not evs:
                continue
            ev_models: List[Evidence] = []
            for e in evs[:2]:
                url = (e.get("url") or "").strip()
                if not url:
                    continue
                date = (e.get("date") or dt.date.today().isoformat()).strip()
                snippet = (e.get("snippet") or "(see source)").strip()[:300]
                ev_models.append(Evidence(url=url, date=date, snippet=snippet))
            if not ev_models:
                continue
            if not numbers_consistent(item, [e.snippet for e in ev_models]):
                continue
            out.append(Finding(
                item=item,
                factor=factor,
                direction=direction if direction in ("pro","con") else "con",
                timeframe=timeframe or "unspecified",
                materiality=max(0.0, min(1.0, mat)),
                evidence=ev_models,
            ))
        except Exception:
            continue

    out = dedup_keep_best(out, threshold=0.70)
    return out[:max_items] if max_items else out

__all__ = ['llm_findings']