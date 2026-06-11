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
    from .news_sources import aggregate_news, format_news_for_context
except Exception:
    from services.prosandcons.news_sources import aggregate_news, format_news_for_context

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

    # Multi-source news: Yahoo + Google News (Reuters, FT, Bloomberg, BBC, CNBC, WSJ…) + optional NewsAPI
    articles = aggregate_news(ticker, name, ticker_obj=t)
    if articles:
        lines.extend(format_news_for_context(articles))
    else:
        lines.append("Recent News: (no headlines fetched)")

    return "\n".join(lines)

__all__ = ['build_context','get_yf_ticker_safe']
