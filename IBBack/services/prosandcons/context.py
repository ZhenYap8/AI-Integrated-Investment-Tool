from __future__ import annotations
from typing import List, Optional
import datetime as dt, os, re

try:
    from IBBack.utils.finance2 import get_yf_ticker  # when run as package root
except Exception:
    try:
        from utils.finance2 import get_yf_ticker      # when working directory is backend root
    except Exception:
        def get_yf_ticker(symbol: str):  # fallback stub
            class _Dummy:
                info = {}
                news = []
                def history(self, period='1mo'):
                    import pandas as _pd
                    return _pd.DataFrame()
            return _Dummy()

try:
    import trafilatura  # type: ignore
except Exception:
    trafilatura = None

_ABSTRACT_MAX = 600

_DEF_NEWS_LIMIT = 6
_DEF_ABSTRACT_LIMIT = 5

def get_yf_ticker_safe(ticker: str):
    try:
        return get_yf_ticker(ticker)
    except Exception:
        class _Dummy:
            info = {}
            news = []
            def history(self, period='1mo'):
                import pandas as _pd
                return _pd.DataFrame()
        return _Dummy()

def _perf_series(t, period: str) -> Optional[float]:
    try:
        h = t.history(period=period)
        if getattr(h, 'empty', False) or len(h.index) < 2:
            return None
        first = float(h['Close'].iloc[0]); last = float(h['Close'].iloc[-1])
        if first <= 0: return None
        return (last/first - 1.0) * 100.0
    except Exception:
        return None

def _abstract(url: str) -> str:
    if trafilatura is None:
        return "(abstract unavailable)"
    try:
        downloaded = trafilatura.fetch_url(url, no_ssl=True, timeout=8)
        if not downloaded:
            return "(fetch failed)"
        text = trafilatura.extract(downloaded, include_comments=False, include_formatting=False) or ''
        text = re.sub(r"\s+", " ", text).strip()
        return text[:_ABSTRACT_MAX]
    except Exception:
        return "(abstract error)"

def build_context(ticker: str) -> str:
    t = get_yf_ticker_safe(ticker)
    info = getattr(t, 'info', {}) or {}
    lines: List[str] = []
    now = dt.datetime.utcnow().replace(microsecond=0).isoformat()+'Z'
    lines.append(f"AsOfUTC: {now}")
    name = info.get('longName') or info.get('shortName') or ticker
    lines.append(f"Company: {name} ({ticker})")
    q = f"https://finance.yahoo.com/quote/{ticker}"
    ks = f"https://finance.yahoo.com/quote/{ticker}/key-statistics"
    lines.append(f"Yahoo Finance pages: {q} ; {ks}")
    # Snapshot metrics
    snap = []
    for k,label in [
        ('currentPrice','price'), ('marketCap','marketCap'), ('trailingPE','trailingPE'), ('forwardPE','forwardPE'),
        ('beta','beta'), ('grossMargins','grossMargins'), ('operatingMargins','operatingMargins'), ('profitMargins','profitMargins'),
        ('freeCashflow','freeCashflow'), ('operatingCashflow','operatingCashflow')]:
        v = info.get(k)
        if v is None: continue
        try:
            if label.endswith('Margins') and isinstance(v,(int,float)):
                snap.append(f"{label}={v*100:.1f}%")
            elif label in ('trailingPE','forwardPE','beta') and isinstance(v,(int,float)):
                snap.append(f"{label}={v:.2f}")
            elif label in ('marketCap','freeCashflow','operatingCashflow') and isinstance(v,(int,float)):
                snap.append(f"{label}=${v:,.0f}")
            elif label=='price' and isinstance(v,(int,float)):
                snap.append(f"price=${v:,.2f}")
            else:
                snap.append(f"{label}={v}")
        except Exception:
            continue
    if snap:
        lines.append("Snapshot: "+"; ".join(snap[:12]))
    perf = {p:_perf_series(t,p) for p in ('1mo','3mo','6mo','1y')}
    pb = [f"{k.replace('mo','m')}={v:.1f}%" for k,v in perf.items() if isinstance(v,(int,float))]
    if pb:
        lines.append("Performance: "+", ".join(pb))
    news = getattr(t,'news',[]) or []
    if news:
        lines.append("Recent News:")
        for n in news[:_DEF_NEWS_LIMIT]:
            ts = n.get('providerPublishTime'); date = dt.datetime.utcfromtimestamp(ts).date().isoformat() if ts else ''
            title = (n.get('title','') or '')[:180]; url = n.get('link','') or ''
            lines.append(f"- {date} {title}: {url}")
        lines.append("News abstracts:")
        for n in news[:_DEF_ABSTRACT_LIMIT]:
            u = n.get('link','') or ''
            if not u: continue
            title = (n.get('title','') or '')[:140]
            lines.append(f"- {title}\n  URL: {u}\n  Abstract: {_abstract(u)}")
    return "\n".join(lines)

__all__ = ['build_context','get_yf_ticker_safe']