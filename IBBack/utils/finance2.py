import math
from typing import Optional, Tuple, List, Dict, Any, TYPE_CHECKING
from fastapi import HTTPException

if TYPE_CHECKING:
    import pandas as pd
    import yfinance as yf
else:
    try:
        import yfinance as yf  # type: ignore
        import pandas as pd  # type: ignore
    except Exception:
        yf = None  # type: ignore
        pd = None  # type: ignore


def require_deps() -> None:
    if yf is None or pd is None:
        raise HTTPException(status_code=500, detail="Dependencies missing: install yfinance and pandas")


def cagr(first: Optional[float], last: Optional[float], years: Optional[float]) -> Optional[float]:
    try:
        if first is None or last is None or years is None or first <= 0 or years <= 0:
            return None
        return (last / first) ** (1 / years) - 1
    except Exception:
        return None


def safe_pct(x: Optional[float]) -> str:
    return f"{x*100:.1f}%" if isinstance(x, (int, float)) and not (x is None or math.isnan(x)) else "—"


def get_yf_ticker(ticker: str):
    require_deps()
    return yf.Ticker(ticker)


def get_row(df: Optional['pd.DataFrame'], name: str) -> Optional['pd.Series']:
    if df is None:
        return None
    if not hasattr(df, 'index') or name not in df.index:
        return None
    row: 'pd.Series' = df.loc[name]
    series: 'pd.Series' = row.dropna()
    return series[::-1] if hasattr(series, "__getitem__") else None


def add_series(a: Optional['pd.Series'], b: Optional['pd.Series']) -> Optional['pd.Series']:
    if a is None and b is None:
        return None
    if a is None:
        return b
    if b is None:
        return a
    result: 'pd.Series' = a.add(b, fill_value=0)
    return result


def last_value(series: Optional['pd.Series']) -> Optional[float]:
    try:
        if series is None or len(series) == 0:
            return None
        val: float = float(series.iloc[-1])
        return val
    except Exception:
        return None


def avg_last_n(series: Optional['pd.Series'], n: int) -> Optional[float]:
    if series is None or n <= 0:
        return None
    s: 'pd.Series' = series.dropna()
    if len(s) == 0:
        return None
    tail: 'pd.Series' = s.iloc[-n:]
    if len(tail) == 0:
        return None
    avg: float = float(tail.mean())
    return avg


def split_first_last(series: Optional['pd.Series'], years: int) -> Tuple[Optional[float], Optional[float], Optional[int]]:
    if series is None or years is None or years <= 0:
        return None, None, None
    if len(series) < 2:
        return None, None, None
    n: int = min(years, len(series) - 1)
    try:
        first_val: float = float(series.iloc[-(n+1)])
        last_val: float = float(series.iloc[-1])
        return first_val, last_val, n
    except Exception:
        return None, None, None


def ratio_safe(num: Optional[float], den: Optional[float]) -> Optional[float]:
    try:
        if num is None or den is None or den == 0:
            return None
        result: float = float(num) / float(den)
        return result
    except Exception:
        return None


def build_historical_roe(net_income: Optional['pd.Series'], equity: Optional['pd.Series'], years: Optional[int] = None) -> List[Dict[str, Any]]:
    if net_income is None or equity is None:
        return []
    try:
        ni: 'pd.Series' = net_income.dropna()
        eq: 'pd.Series' = equity.dropna()
        common: List[Any] = sorted([d for d in ni.index if d in eq.index])
        if len(common) < 2:
            return []
        items: List[Dict[str, Any]] = []
        for i in range(1, len(common)):
            d: Any = common[i]
            prev: Any = common[i - 1]
            try:
                ni_val: Optional[float] = float(ni.get(d)) if d in ni.index else None
                eq_prev: Optional[float] = float(eq.get(prev)) if prev in eq.index else None
                eq_cur: Optional[float] = float(eq.get(d)) if d in eq.index else None
                if ni_val is None or eq_prev is None or eq_cur is None:
                    continue
                avg_eq: float = (eq_prev + eq_cur) / 2.0
                if avg_eq == 0 or math.isnan(avg_eq):
                    continue
                roe_pct: float = (ni_val / avg_eq) * 100.0
                items.append({"_ts": d, "roe": roe_pct, "y": roe_pct})
            except Exception:
                continue
        if years and items:
            last_ts: Any = items[-1]["_ts"]
            try:
                import pandas as pd_import
                cutoff: Any = last_ts - pd_import.DateOffset(years=years)
                items = [it for it in items if it["_ts"] >= cutoff]
            except Exception:
                pass
        out: List[Dict[str, Any]] = [{"date": (ts.isoformat() if hasattr(ts, "isoformat") else str(ts)), "roe": it["roe"], "y": it["y"]} for it in items for ts in [it["_ts"]]]
        return out
    except Exception:
        return []
