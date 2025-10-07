from __future__ import annotations
import datetime as dt
from typing import List

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

__all__ = ['fallback_findings_from_yf']