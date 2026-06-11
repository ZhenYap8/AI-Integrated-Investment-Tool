from __future__ import annotations
import datetime as dt
import re
from typing import List, Optional

try:
    from IBBack.models.schemas2 import Finding, Evidence
except Exception:
    try:
        from models.schemas2 import Finding, Evidence
    except Exception:
        class Finding:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        class Evidence:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

try:
    from .news_sources import aggregate_news
except Exception:
    from services.prosandcons.news_sources import aggregate_news

_CON_RE = re.compile(
    r"\b(layoff|lawsuit|decline|fall|drop|cut|miss|warn|investigation|probe|recall|"
    r"sanction|slump|tumble|plunge|loss|debt|downgrade|fine|ban|hack|breach)\b", re.I
)
_PRO_RE = re.compile(
    r"\b(deal|partnership|launch|record|growth|beat|raise|expand|win|approve|surge|"
    r"contract|invest|partners|alliance|milestone|breakthrough)\b", re.I
)

_DEF_PRO_M_OP_MARGIN = 0.20
_DEF_CON_P_LOW_MARGIN = 0.05
_DEF_CON_HIGH_PE = 35
_DEF_CON_HIGH_BETA = 1.3

def _fmt_pct(x):
    try:
        return f"{float(x)*100:.1f}%"
    except Exception:
        return "—"

def fallback_findings_from_yf(ticker: str, info: dict) -> List[Finding]:
    findings: List[Finding] = []
    ks_url = f"https://finance.yahoo.com/quote/{ticker}/key-statistics"
    today = dt.date.today().isoformat()

    op_m = info.get('operatingMargins')
    pr_m = info.get('profitMargins')
    fpe = info.get('forwardPE')
    tpe = info.get('trailingPE')
    beta = info.get('beta')
    fcf = info.get('freeCashflow')
    ocf = info.get('operatingCashflow')

    # Pros
    if isinstance(op_m, (int,float)) and op_m >= _DEF_PRO_M_OP_MARGIN:
        findings.append(Finding(
            item=(f"Operating margins of {_fmt_pct(op_m)} indicate strong operating leverage, which supports reinvestment and cushions pricing cycles because higher margins generally translate to robust free cash generation."),
            factor="margins", direction="pro", timeframe="near_term", materiality=0.6,
            evidence=[Evidence(url=ks_url, date=today, snippet=f"OperatingMargins: {_fmt_pct(op_m)}")] ))
    if isinstance(fpe,(int,float)) and isinstance(tpe,(int,float)) and fpe < tpe:
        findings.append(Finding(
            item=(f"Forward P/E {fpe:.1f} below trailing {tpe:.1f} signals expected earnings growth; this matters because valuation risk moderates when future earnings expand relative to the current multiple."),
            factor="growth", direction="pro", timeframe="near_term", materiality=0.5,
            evidence=[Evidence(url=ks_url, date=today, snippet=f"ForwardPE: {fpe:.1f}; TrailingPE: {tpe:.1f}")] ))

    # Cons
    if isinstance(pr_m,(int,float)) and pr_m < _DEF_CON_P_LOW_MARGIN:
        findings.append(Finding(
            item=(f"Profit margins of {_fmt_pct(pr_m)} are thin, limiting buffer against cost inflation; this can matter because sustained low net margins constrain internally funded growth and may pressure valuation."),
            factor="margins", direction="con", timeframe="near_term", materiality=0.6,
            evidence=[Evidence(url=ks_url, date=today, snippet=f"ProfitMargins: {_fmt_pct(pr_m)}")] ))
    if isinstance(beta,(int,float)) and beta > _DEF_CON_HIGH_BETA:
        findings.append(Finding(
            item=(f"Beta of {beta:.2f} implies higher volatility than the market; this elevates drawdown risk because macro or sentiment shocks can disproportionately impact equity value."),
            factor="other", direction="con", timeframe="near_term", materiality=0.4,
            evidence=[Evidence(url=ks_url, date=today, snippet=f"Beta: {beta:.2f}")] ))
    if isinstance(tpe,(int,float)) and tpe > _DEF_CON_HIGH_PE:
        findings.append(Finding(
            item=(f"Trailing P/E {tpe:.1f} screens elevated versus broad benchmarks; this increases de‑rating risk because any slowdown in growth or guidance cut can compress multiples."),
            factor="valuation", direction="con", timeframe="near_term", materiality=0.5,
            evidence=[Evidence(url=ks_url, date=today, snippet=f"TrailingPE: {tpe:.1f}")] ))
    if isinstance(fcf,(int,float)) and fcf < 0 and isinstance(ocf,(int,float)) and ocf <= 0:
        findings.append(Finding(
            item=(f"Negative free and operating cash flow signal funding pressure; this matters because prolonged cash deficits can force external financing or curtail strategic investment."),
            factor="leverage", direction="con", timeframe="near_term", materiality=0.6,
            evidence=[Evidence(url=ks_url, date=today, snippet=f"FCF: {fcf:,.0f}; OCF: {ocf:,.0f}")] ))

    if not any(f.direction=='con' for f in findings):
        findings.append(Finding(
            item=("Limited structured evidence surfaced; investors should monitor valuation resilience versus guidance because disappointment could trigger multiple compression."),
            factor="guidance", direction="con", timeframe="near_term", materiality=0.3,
            evidence=[Evidence(url=ks_url, date=today, snippet="See Yahoo Key Statistics page for latest metrics.")] ))

    return findings[:6]


def _headline_to_finding(article, direction: str) -> Finding:
    snippet = (article.snippet or article.title or "")[:300]
    item = (
        f"{article.outlet} ({article.date}): {article.title}. "
        f"This matters because recent coverage from major outlets can shift investor expectations "
        f"and price action ahead of the next earnings update."
    )
    if snippet and snippet != article.title:
        item = (
            f"{article.outlet}: {article.title} — {snippet[:160]}. "
            f"Investors should weigh this headline against fundamentals because news flow often "
            f"moves sentiment before financials fully reflect the story."
        )
    return Finding(
        item=item[:420],
        factor="other",
        direction=direction,
        timeframe="near_term",
        materiality=0.55,
        evidence=[Evidence(
            url=article.url,
            date=article.date or dt.date.today().isoformat(),
            snippet=snippet,
            source=article.outlet,
        )],
    )


def fallback_findings_from_news(
    ticker: str,
    company_name: str,
    ticker_obj=None,
    max_items: int = 8,
) -> List[Finding]:
    """Build findings from Reuters, Bloomberg, BBC, CNBC, etc. when AI is unavailable."""
    articles = aggregate_news(ticker, company_name, ticker_obj=ticker_obj, total_limit=max_items + 4)
    if not articles:
        return []

    pros: List[Finding] = []
    cons: List[Finding] = []
    neutral: List[Finding] = []

    for a in articles:
        blob = f"{a.title} {a.snippet or ''}"
        if _CON_RE.search(blob):
            cons.append(_headline_to_finding(a, "con"))
        elif _PRO_RE.search(blob):
            pros.append(_headline_to_finding(a, "pro"))
        else:
            neutral.append(_headline_to_finding(a, "pro" if len(pros) <= len(cons) else "con"))

    findings: List[Finding] = []
    half = max(1, max_items // 2)
    findings.extend(pros[:half])
    findings.extend(cons[:half])
    if len(findings) < max_items:
        for f in neutral:
            if f not in findings and len(findings) < max_items:
                findings.append(f)
    return findings[:max_items]


__all__ = ['fallback_findings_from_yf', 'fallback_findings_from_news']