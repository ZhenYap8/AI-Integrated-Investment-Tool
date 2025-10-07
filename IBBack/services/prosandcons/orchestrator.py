from __future__ import annotations
# Orchestrator: public entrypoint
from .config import OPENAI_API_KEY
from .context import build_context, get_yf_ticker_safe
from .llm import llm_findings
from .filters import dedup_keep_best
from .fallback import fallback_findings_from_yf
import datetime as dt

try:
    from IBBack.models.schemas2 import ProsConsResponse, Finding
except Exception:
    try:
        from models.schemas2 import ProsConsResponse, Finding
    except Exception:
        class ProsConsResponse:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        class Finding:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)


def analyze_proscons_ai_only(ticker: str, *, max_items: int = 8, period: str | None = None, years: int | None = None) -> ProsConsResponse:
    as_of = dt.date.today().isoformat()
    context = build_context(ticker)
    findings = llm_findings(context, max_items=max_items)

    # Cons top-up
    cons_needed = max(1, max_items // 3)
    cons_count = sum(1 for f in findings if f.direction == 'con')
    if cons_count < cons_needed:
        more_cons = llm_findings(context, max_items=max(4, max_items // 2), focus='cons')
        findings.extend(more_cons)
        findings = dedup_keep_best(findings, threshold=0.70)[:max_items]

    # Fallback if empty
    if not findings:
        info = getattr(get_yf_ticker_safe(ticker), 'info', {}) or {}
        findings = fallback_findings_from_yf(ticker, info)

    # Light balance
    pros = [f for f in findings if f.direction == 'pro']
    cons = [f for f in findings if f.direction == 'con']
    if pros and cons:
        half = max_items // 2
        findings = pros[:half] + cons[:half]
        if len(pros) < half:
            findings = pros + cons[:max_items - len(pros)]
        elif len(cons) < half:
            findings = pros[:max_items - len(cons)] + cons

    findings = findings[:max_items]
    return ProsConsResponse(company=ticker, asOf=as_of, findings=findings, fromAI=bool(OPENAI_API_KEY))
