# Investment Agent Backend Scaffold (FastAPI)
# -------------------------------------------------------------
# Endpoints:
#   GET /api/suggest?q=... -> autocomplete for companies/industries
#   GET /api/analyze?query=...&years=... -> analysis payload consumed by the frontend
#
# Notes:
# - Uses yfinance for prices/financials. Real production should use a robust data vendor.
# - Implements a minimal, explainable scorecard and a simple EV/EBIT fair value.
# - Hardened for edge-cases: safer math, optional data, cleaner errors, immutable defaults.
#
# Run: uvicorn app2:app --reload --port 8000

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Tuple
import math
import datetime as dt
import requests
import csv
from typing import Dict


try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
except Exception:  # pragma: no cover
    yf = None
    pd = None
    np = None

app = FastAPI(title="Investment Agent Backend Scaffold", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- Universe (Dynamic) -------------------- #
# Demo industries (keep as-is for aggregation)
DEMO_INDUSTRIES = [
    {"label": "Robotics & Automation", "value": "Robotics", "type": "industry"},
    {"label": "Semiconductors (AI)", "value": "Semiconductors", "type": "industry"},
]

# Industry → demo constituents (you can expand later)
INDUSTRY_MAP = {
    "Robotics": ["ABB", "FANUY", "ROK", "ISRG", "TER", "CGNX", "IRBT"],
    "Semiconductors": ["NVDA"],
}

# Load US tickers from NASDAQ Trader symbol directories (NASDAQ + NYSE/AMEX)
def load_us_tickers() -> List[Dict[str, str]]:
    tickers: List[Dict[str, str]] = []
    endpoints = [
        ("https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt", "Symbol", "Security Name"),
        ("https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt", "ACT Symbol", "Security Name"),
    ]
    for url, sym_key, name_key in endpoints:
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            lines = [ln for ln in resp.text.splitlines() if ln and "File Creation Time" not in ln]
            reader = csv.DictReader(lines, delimiter='|')
            for row in reader:
                symbol = (row.get(sym_key) or "").strip()
                name = (row.get(name_key) or "").strip()
                if not symbol or not name:
                    continue
                if symbol in {"Symbol", "ACT Symbol"}:
                    continue
                tickers.append({"label": f"{name} ({symbol})", "value": symbol, "type": "company"})
        except Exception:
            continue
    # De-dup
    seen, deduped = set(), []
    for it in tickers:
        if it["value"] in seen:
            continue
        seen.add(it["value"])
        deduped.append(it)
    # Fallback demo set
    if not deduped:
        deduped = [
            {"label": "NVIDIA (NVDA)", "value": "NVDA", "type": "company"},
            {"label": "ABB Ltd (ABB)", "value": "ABB", "type": "company"},
            {"label": "Fanuc (FANUY)", "value": "FANUY", "type": "company"},
        ]
    return deduped

# Warm the cache at startup
ALL_US_COMPANIES: List[Dict[str, str]] = load_us_tickers()
# -------------------- Schemas -------------------- #
class SuggestItem(BaseModel):
    type: str
    label: str
    value: str

class SourceItem(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None

class BulletItem(BaseModel):
    text: str
    source: Optional[str] = None

class ValuationRow(BaseModel):
    metric: str
    value: Any
    note: Optional[str] = None

class ValuationBlock(BaseModel):
    table: List[ValuationRow] = Field(default_factory=list)
    fairValue: Optional[float] = None
    currentPrice: Optional[float] = None
    upsidePct: Optional[float] = None  # percentage (e.g., 12.3 for +12.3%)

class ScoreItem(BaseModel):
    id: str
    label: str
    verdict: str           # "green" | "amber" | "red"
    detail: Optional[str] = None
    value: Optional[float] = None      # raw numeric (pct in 0–100 if unit=='pct')
    threshold: Optional[float] = None  # same unit as value
    unit: Optional[str] = None         # 'pct', 'x', etc.


class AnalyzeResponse(BaseModel):
    meta: Dict[str, Any]
    scorecard: List[ScoreItem] = Field(default_factory=list)
    valuation: ValuationBlock = Field(default_factory=ValuationBlock)
    pros: List[BulletItem] = Field(default_factory=list)
    cons: List[BulletItem] = Field(default_factory=list)
    risks: List[BulletItem] = Field(default_factory=list)
    sources: List[SourceItem] = Field(default_factory=list)

# -------------------- Helpers -------------------- #

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
    if df is None or name not in getattr(df, 'index', []):
        return None
    row = df.loc[name]
    series = row.dropna()
    return series[::-1] if hasattr(series, "__getitem__") else None  # oldest->newest


def add_series(a: Optional['pd.Series'], b: Optional['pd.Series']) -> Optional['pd.Series']:
    if a is None and b is None:
        return None
    if a is None:
        return b
    if b is None:
        return a
    return a.add(b, fill_value=0)


def last_value(series: Optional['pd.Series']) -> Optional[float]:
    try:
        if series is None or len(series) == 0:
            return None
        return float(series.iloc[-1])
    except Exception:
        return None
    
def avg_last_n(series: Optional['pd.Series'], n: int) -> Optional[float]:
    if series is None or n <= 0:
        return None
    s = series.dropna()
    if len(s) == 0:
        return None
    # series is oldest -> newest in your code; take the last n values
    tail = s.iloc[-n:]
    if len(tail) == 0:
        return None
    return float(tail.mean())



def split_first_last(series: Optional['pd.Series'], years: int) -> Tuple[Optional[float], Optional[float], Optional[int]]:
    if series is None or years is None or years <= 0:
        return None, None, None
    if len(series) < 2:
        return None, None, None
    n = min(years, len(series) - 1)
    try:
        first_val = float(series.iloc[-(n+1)])
        last_val = float(series.iloc[-1])
        return first_val, last_val, n
    except Exception:
        return None, None, None


def ratio_safe(num: Optional[float], den: Optional[float]) -> Optional[float]:
    try:
        if num is None or den is None or den == 0:
            return None
        return float(num) / float(den)
    except Exception:
        return None

from typing import Dict

# -------------------- Thresholds (defaults + overrides) -------------------- #
# One clean set of defaults used by the scorecard. Override per request.
DEFAULT_THRESHOLDS: Dict[str, float] = {
    # growth & profitability
    "rev_cagr_min": 0.05,      # 5%+
    "op_margin_min": 0.10,     # 10%+
    # leverage & coverage
    "nd_eq_max": 1.00,         # <= 1.0x
    "interest_cover_min": 4.0, # >= 4x
    # returns
    "roe_min": 0.10,           # >= 10%
}

def merge_thresholds(overrides: Dict[str, float] | None) -> Dict[str, float]:
    out = dict(DEFAULT_THRESHOLDS)
    if not overrides:
        return out
    for k, v in overrides.items():
        try:
            if k in out and isinstance(v, (int, float)):
                out[k] = float(v)
        except Exception:
            continue
    return out

def thresholds_from_params(
    *,
    rev_cagr_min: float | None = None,
    op_margin_min: float | None = None,
    nd_eq_max: float | None = None,
    interest_cover_min: float | None = None,
    roe_min: float | None = None,
) -> Dict[str, float]:
    overrides = {
        k: v for k, v in {
            "rev_cagr_min": rev_cagr_min,
            "op_margin_min": op_margin_min,
            "nd_eq_max": nd_eq_max,
            "interest_cover_min": interest_cover_min,
            "roe_min": roe_min,
        }.items() if v is not None
    }
    return merge_thresholds(overrides)



# -------------------- Core Analysis -------------------- #

def analyze_company(ticker: str, years: int, thresh: Dict[str, float]) -> AnalyzeResponse:
    try:
        t = get_yf_ticker(ticker)

        # Price & info
        hist = t.history(period="max")
        if pd is not None and years and not getattr(hist, 'empty', True):
            cutoff = pd.Timestamp.today(tz=hist.index.tz) - pd.DateOffset(years=years)
            hist = hist.loc[hist.index >= cutoff]
        current_price = float(hist["Close"].iloc[-1]) if getattr(hist, 'empty', True) is False else None

        info = getattr(t, 'info', {}) or {}

        # Financial statements (annual)
        fin = getattr(t, 'financials', None)
        bs = getattr(t, 'balance_sheet', None)
        # cf not used yet but kept for extension
        # cf = getattr(t, 'cashflow', None)

        rev = get_row(fin, 'Total Revenue')
        op_income = get_row(fin, 'Operating Income')
        net_income = get_row(fin, 'Net Income')
        interest_exp = get_row(fin, 'Interest Expense')

        total_debt = get_row(bs, 'Total Debt')
        if total_debt is None and bs is not None:
            total_debt = add_series(get_row(bs, 'Short Long Term Debt'), get_row(bs, 'Long Term Debt'))
     # ----- safe coalescing (no boolean 'or' on Series) -----
        cash = get_row(bs, 'Cash And Cash Equivalents')
        if cash is None:
            cash = get_row(bs, 'Cash And Cash Equivalents USD')
        if cash is None:
            cash = get_row(bs, 'Cash')

        equity = get_row(bs, 'Total Stockholder Equity')
        if equity is None:
            equity = get_row(bs, 'Total Equity Gross Minority Interest')
        # --------------------------------------------------------


        # Revenue CAGR (windowed)
        first_val, last_val, n_hist = split_first_last(rev, years)
        rev_cagr = cagr(first_val, last_val, n_hist)

        # Margins
        op_margin = ratio_safe(last_value(op_income), last_value(rev))

        # Leverage & coverage
        nd_to_eq = None
        nd = None
        if total_debt is not None and cash is not None:
            nd = last_value(total_debt) - last_value(cash) if (last_value(total_debt) is not None and last_value(cash) is not None) else None
        nd_to_eq = ratio_safe(nd, last_value(equity))

        interest_cover = None
        ebit_latest = last_value(op_income)
        interest_latest = abs(last_value(interest_exp)) if last_value(interest_exp) is not None else None
        if interest_latest is not None and interest_latest > 0:
            interest_cover = ratio_safe(ebit_latest, interest_latest)

        avg_equity_2y = avg_last_n(equity, 2)
        roe = ratio_safe(last_value(net_income), avg_equity_2y)

        # Valuation (simple EV/EBIT)
        market_cap = info.get('marketCap')
        shares_out = info.get('sharesOutstanding')
        total_debt_latest = last_value(total_debt)
        cash_latest = last_value(cash)

        ev = None
        if market_cap is not None and total_debt_latest is not None and cash_latest is not None:
            ev = float(market_cap) + float(total_debt_latest) - float(cash_latest)
        ev_ebit = (ev / ebit_latest) if (ev is not None and ebit_latest not in (None, 0)) else None

        peer_multiple = 15.0  # configurable
        fair_ev = (peer_multiple * ebit_latest) if ebit_latest is not None else None
        fair_equity = (fair_ev - (total_debt_latest or 0) + (cash_latest or 0)) if fair_ev is not None else None
        if fair_equity is None and shares_out and current_price:
            # fallback if EV path missing: approximate via price*shares (rarely needed)
            fair_equity = market_cap
        fair_value = (fair_equity / shares_out) if (fair_equity is not None and shares_out) else None

        upside_pct = ((fair_value / current_price - 1) * 100.0) if (fair_value is not None and current_price) else None

        # Scorecard thresholds (tweakable)
        def verdict(val: Optional[float], threshold: float, mode: str = '>=', fmt=lambda x: f"{x:.2f}") -> Tuple[str, str]:
            if val is None:
                return 'amber', 'Insufficient data'
            ok = (val >= threshold) if mode == '>=' else (val <= threshold)
            return ('green' if ok else 'red'), f"{fmt(val)} vs threshold {fmt(threshold)}"

        v1, d1 = verdict(rev_cagr,        thresh["rev_cagr_min"],    ">=", fmt=lambda x: f"{x*100:.1f}%")
        v2, d2 = verdict(op_margin,       thresh["op_margin_min"],    ">=", fmt=lambda x: f"{x*100:.1f}%")
        v3, d3 = verdict(nd_to_eq,        thresh["nd_eq_max"],        "<=", fmt=lambda x: f"{x:.2f}x")
        v4, d4 = verdict(interest_cover,  thresh["interest_cover_min"],">=", fmt=lambda x: f"{x:.1f}x")
        v5, d5 = verdict(roe,             thresh["roe_min"],          ">=", fmt=lambda x: f"{x*100:.1f}%")


        def mk_score(id_: str, label: str, val: Optional[float], thr: float, mode: str, unit: Optional[str] = None):
            # format fn for detail text
            fmt = (lambda x: f"{x*100:.1f}%") if unit == 'pct' else (lambda x: f"{x:.2f}x")
            v, d = verdict(val, thr, mode, fmt=fmt)
            # normalize value/threshold into human scale (pct 0–100)
            vnum = (val * 100.0) if (val is not None and unit == 'pct') else (val if val is not None else None)
            tnum = (thr * 100.0) if unit == 'pct' else thr
            return ScoreItem(id=id_, label=label, verdict=v, detail=d, value=vnum, threshold=tnum, unit=unit)


        scorecard = [
            mk_score("rev_cagr",   "Revenue growth (CAGR)", rev_cagr,         thresh["rev_cagr_min"],       '>=', unit='pct'),
            mk_score("op_margin",  "Operating margin",      op_margin,        thresh["op_margin_min"],      '>=', unit='pct'),
            mk_score("nd_eq",      "Net debt / Equity",     nd_to_eq,         thresh["nd_eq_max"],          '<=', unit='x'),
            mk_score("int_cover",  "Interest coverage",     interest_cover,   thresh["interest_cover_min"], '>=', unit='x'),
            mk_score("roe",        "ROE",                   roe,              thresh["roe_min"],            '>=', unit='pct'),
        ]


        # Pros/Cons/Risks (rule-based placeholders; replace with RAG-LM later)
        pros: List[BulletItem] = []
        cons: List[BulletItem] = []
        risks: List[BulletItem] = []

        if rev_cagr and rev_cagr > 0.10:
            pros.append(BulletItem(text=f"Strong top-line growth (~{safe_pct(rev_cagr)} CAGR)"))
        if op_margin and op_margin > 0.20:
            pros.append(BulletItem(text=f"High operating margins (~{safe_pct(op_margin)})"))
        if roe and roe > 0.15:
            pros.append(BulletItem(text=f"Solid ROE (~{safe_pct(roe)})"))

        if nd_to_eq and nd_to_eq > 1.0:
            cons.append(BulletItem(text=f"Leverage elevated (Net Debt/Equity ~{nd_to_eq:.2f}x)"))
        if interest_cover and interest_cover < 4.0:
            cons.append(BulletItem(text=f"Low interest coverage (~{interest_cover:.1f}x)"))

        risks.append(BulletItem(text="Cyclicality and capex sensitivity common in robotics/tech hardware"))
        if info.get('country') == 'China':
            risks.append(BulletItem(text="Geopolitical/export-control exposure"))

        # Valuation table
        val_table = [
            ValuationRow(metric="Current Price", value=f"${current_price:.2f}" if current_price is not None else "—"),
            ValuationRow(metric="EV/EBIT", value=f"{ev_ebit:.1f}x" if ev_ebit is not None else "—", note="EV = MarketCap + Debt – Cash"),
            ValuationRow(metric="Peer EV/EBIT (assumed)", value=f"{15.0:.1f}x", note="Adjust per sector"),
            ValuationRow(metric="Fair Value (per share)", value=f"${fair_value:.2f}" if fair_value is not None else "—"),
            ValuationRow(metric="Upside", value=f"{upside_pct:.1f}%" if upside_pct is not None else "—"),
        ]

        # Sources
        y_url = f"https://finance.yahoo.com/quote/{ticker}"
        sources = [SourceItem(title=f"Yahoo Finance – {ticker}", url=y_url)]

        return AnalyzeResponse(
            meta={"queryType": "company", "ticker": ticker, "asOf": dt.date.today().isoformat()},
            scorecard=scorecard,
            valuation=ValuationBlock(table=val_table, fairValue=fair_value, currentPrice=current_price, upsidePct=upside_pct),
            pros=pros,
            cons=cons,
            risks=risks,
            sources=sources,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to analyze company {ticker}: {e}")


def analyze_industry(industry: str, years: int, thresh: Dict[str, float]) -> AnalyzeResponse:
    tickers = INDUSTRY_MAP.get(industry, [])
    if not tickers:
        return AnalyzeResponse(
            meta={"queryType": "industry", "industry": industry, "asOf": dt.date.today().isoformat()},
            scorecard=[], valuation=ValuationBlock(), pros=[], cons=[], risks=[], sources=[]
        )

    comps = [analyze_company(t, years, thresh) for t in tickers]

    # Average scorecard (green=2, amber=1, red=0)
    def score_to_num(v: str) -> int:
        return {"green": 2, "amber": 1, "red": 0}.get(v, 1)

    labels = ["Revenue growth (CAGR)", "Operating margin", "Net debt / Equity", "Interest coverage", "ROE"]
    agg_scores: Dict[str, float] = {k: 0.0 for k in labels}
    counts: Dict[str, int] = {k: 0 for k in labels}

    for c in comps:
        for s in c.scorecard:
            if s.label in agg_scores:
                agg_scores[s.label] += score_to_num(s.verdict)
                counts[s.label] += 1

    scorecard: List[ScoreItem] = []
    for label in labels:
        if counts[label] == 0:
            continue
        avg = agg_scores[label] / counts[label]
        verdict = 'green' if avg >= 1.5 else ('amber' if avg >= 1.0 else 'red')
        scorecard.append(ScoreItem(id=label.lower().replace(' ', '_'), label=label, verdict=verdict, detail=f"Average score {avg:.2f}"))

    # Aggregate valuation (median upside among comps)
    upsides = [c.valuation.upsidePct for c in comps if c.valuation and c.valuation.upsidePct is not None]
    med_upside = float(np.median(upsides)) if upsides and np is not None else None

    sources: List[SourceItem] = [
        SourceItem(title=f"Yahoo Finance – {t}", url=f"https://finance.yahoo.com/quote/{t}") for t in tickers
    ]

    return AnalyzeResponse(
        meta={"queryType": "industry", "industry": industry, "asOf": dt.date.today().isoformat()},
        scorecard=scorecard,
        valuation=ValuationBlock(table=[ValuationRow(metric="Median Upside (peers)", value=f"{med_upside:.1f}%" if med_upside is not None else "—")], fairValue=None, currentPrice=None, upsidePct=med_upside),
        pros=[BulletItem(text="Secular growth in automation and AI adoption")],
        cons=[BulletItem(text="Valuation dispersion across sub-segments is high")],
        risks=[BulletItem(text="Capex cycles and supply chain constraints can impact orders")],
        sources=sources,
    )

# -------------------- API Routes -------------------- #

@app.get("/api/suggest", response_model=List[SuggestItem])
async def suggest(q: str = Query("")):
    ql = q.lower().strip()
    items = DEMO_INDUSTRIES + ALL_US_COMPANIES
    if not ql:
        return items[:8]
    out: List[Dict[str, str]] = []
    for it in items:
        text = (it.get("label", "") + " " + it.get("value", "")).lower()
        if ql in text:
            out.append(it)
    return out[:8]

@app.get("/api/analyze", response_model=AnalyzeResponse)
async def analyze(
    query: str = Query(...),
    years: int = Query(10, ge=1, le=10),
    # optional threshold overrides:
    rev_cagr_min: float | None = Query(None),
    op_margin_min: float | None = Query(None),
    nd_eq_max: float | None = Query(None),
    interest_cover_min: float | None = Query(None),
    roe_min: float | None = Query(None),
):
    thresh = thresholds_from_params(
        rev_cagr_min=rev_cagr_min,
        op_margin_min=op_margin_min,
        nd_eq_max=nd_eq_max,
        interest_cover_min=interest_cover_min,
        roe_min=roe_min,
    )

    val = (query or "").strip()

    # exact company match by symbol or label
    for c in ALL_US_COMPANIES:
        if val.upper() == c["value"] or val.lower() == c["label"].lower():
            return analyze_company(c["value"], years, thresh)

    # industry?
    for i in DEMO_INDUSTRIES:
        if val.lower() == i["value"].lower() or val.lower() == i["label"].lower():
            return analyze_industry(i["value"], years, thresh)

    # heuristic: looks like a ticker (short, no spaces)
    if len(val) <= 6 and " " not in val:
        return analyze_company(val.upper(), years, thresh)

    # fallback: treat as industry search
    return analyze_industry("Robotics", years, thresh)


# -------------------- Health -------------------- #

@app.get("/health")
async def health():
    return {"ok": True, "time": dt.datetime.utcnow().isoformat() + "Z"}
