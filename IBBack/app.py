# Investment Agent Backend Scaffold (FastAPI) - Archived Version
# -------------------------------------------------------------
# Endpoints:
#   GET /api/suggest?q=... -> autocomplete for companies/industries
#   GET /api/analyze?query=...&years=... -> analysis payload consumed by the frontend
#
# Notes:
# - Uses yfinance for prices/financials. Real production should use a robust data vendor.
# - Implements a minimal, explainable scorecard and a simple EV/EBIT fair value.
# - Keeps the design modular inside one file for quick start; refactor into modules later.
#
# Run: uvicorn app:app --reload --port 8000

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import math
import datetime as dt

try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
except Exception as e:
    yf = None
    pd = None
    np = None

app = FastAPI(title="Investment Agent Backend Scaffold", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- Demo Universe -------------------- #
DEMO_COMPANIES = [
    {"label": "NVIDIA (NVDA)", "value": "NVDA", "type": "company"},
    {"label": "ABB Ltd (ABB)", "value": "ABB", "type": "company"},
    {"label": "Fanuc (FANUY)", "value": "FANUY", "type": "company"},
    {"label": "Rockwell Automation (ROK)", "value": "ROK", "type": "company"},
    {"label": "Intuitive Surgical (ISRG)", "value": "ISRG", "type": "company"},
    {"label": "Teradyne (TER)", "value": "TER", "type": "company"},
    {"label": "Cognex (CGNX)", "value": "CGNX", "type": "company"},
    {"label": "iRobot (IRBT)", "value": "IRBT", "type": "company"},
]

DEMO_INDUSTRIES = [
    {"label": "Robotics & Automation", "value": "Robotics", "type": "industry"},
    {"label": "Semiconductors (AI)", "value": "Semiconductors", "type": "industry"},
]

# Map industries to constituent tickers for demo aggregation
INDUSTRY_MAP = {
    "Robotics": ["ABB", "FANUY", "ROK", "ISRG", "TER", "CGNX", "IRBT"],
    "Semiconductors": ["NVDA"],
}

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
    table: List[ValuationRow] = []
    fairValue: Optional[float] = None
    currentPrice: Optional[float] = None
    upsidePct: Optional[float] = None

class ScoreItem(BaseModel):
    id: str
    label: str
    verdict: str
    detail: Optional[str] = None

class AnalyzeResponse(BaseModel):
    meta: Dict[str, Any]
    scorecard: List[ScoreItem]
    valuation: ValuationBlock
    pros: List[BulletItem] = []
    cons: List[BulletItem] = []
    risks: List[BulletItem] = []
    sources: List[SourceItem] = []

# -------------------- Helpers -------------------- #

def cagr(first: float, last: float, years: float) -> Optional[float]:
    try:
        if first is None or last is None or first <= 0 or years <= 0:
            return None
        return (last / first) ** (1 / years) - 1
    except Exception:
        return None


def safe_pct(x: Optional[float]) -> str:
    return f"{x*100:.1f}%" if isinstance(x, (int, float)) and not math.isnan(x) else "—"


def get_yf_ticker(ticker: str):
    if yf is None:
        raise RuntimeError("yfinance not installed")
    return yf.Ticker(ticker)


def latest_series_value(df: Optional['pd.DataFrame'], row_name: str) -> Optional[float]:
    if df is None or row_name not in getattr(df, 'index', []):
        return None
    row = df.loc[row_name]
    if isinstance(row, pd.Series) and len(row) > 0:
        return float(row.dropna().iloc[0]) if not row.dropna().empty else None
    return None


def first_last_in_window(series: 'pd.Series') -> (Optional[float], Optional[float]):
    s = series.dropna()
    if s.empty:
        return None, None
    return float(s.iloc[0]), float(s.iloc[-1])


# -------------------- Core Analysis -------------------- #

def analyze_company(ticker: str, years: int) -> AnalyzeResponse:
    t = get_yf_ticker(ticker)

    # Price & info
    hist = t.history(period="max")
    if years:
        cutoff = pd.Timestamp.today(tz=hist.index.tz) - pd.DateOffset(years=years)
        hist = hist.loc[hist.index >= cutoff]
    current_price = float(hist["Close"].iloc[-1]) if not hist.empty else None

    info = getattr(t, 'info', {}) or {}

    # Financial statements (annual)
    fin = getattr(t, 'financials', None)
    bs = getattr(t, 'balance_sheet', None)
    cf = getattr(t, 'cashflow', None)

    # Align by columns (dates). Convert to ascending order for readability
    def get_row(df, name):
        if df is None or name not in getattr(df, 'index', []):
            return None
        row = df.loc[name]
        # yfinance columns are dates (most-recent first). Reverse for time order.
        return row.dropna()[::-1]

    rev = get_row(fin, 'Total Revenue')
    op_income = get_row(fin, 'Operating Income')
    net_income = get_row(fin, 'Net Income')
    interest_exp = get_row(fin, 'Interest Expense')

    total_debt = get_row(bs, 'Total Debt') or (get_row(bs, 'Short Long Term Debt') + get_row(bs, 'Long Term Debt') if bs is not None else None)
    cash = get_row(bs, 'Cash And Cash Equivalents') or get_row(bs, 'Cash And Cash Equivalents USD') or get_row(bs, 'Cash')
    equity = get_row(bs, 'Total Stockholder Equity') or get_row(bs, 'Total Equity Gross Minority Interest')

    # Metrics window
    n_years_hist = min(years, len(rev) - 1) if isinstance(rev, pd.Series) and len(rev) > 1 else None

    # Revenue CAGR
    rev_cagr = None
    if isinstance(rev, pd.Series) and n_years_hist and n_years_hist > 0:
        first_val = float(rev.iloc[-(n_years_hist+1)])
        last_val = float(rev.iloc[-1])
        rev_cagr = cagr(first_val, last_val, n_years_hist)

    # Margins
    op_margin = None
    if isinstance(op_income, pd.Series) and isinstance(rev, pd.Series) and len(op_income) and len(rev):
        try:
            op_margin = float(op_income.iloc[-1]) / float(rev.iloc[-1]) if float(rev.iloc[-1]) != 0 else None
        except Exception:
            op_margin = None

    # Leverage & coverage
    nd_to_eq = None
    if isinstance(total_debt, pd.Series) and isinstance(cash, pd.Series) and isinstance(equity, pd.Series):
        try:
            nd = float(total_debt.iloc[-1]) - float(cash.iloc[-1])
            eq = float(equity.iloc[-1])
            nd_to_eq = nd / eq if eq != 0 else None
        except Exception:
            nd_to_eq = None

    interest_cover = None
    if isinstance(op_income, pd.Series) and isinstance(interest_exp, pd.Series):
        try:
            ebit = float(op_income.iloc[-1])
            interest = abs(float(interest_exp.iloc[-1]))
            interest_cover = (ebit / interest) if interest > 0 else None
        except Exception:
            interest_cover = None

    # ROE
    roe = None
    if isinstance(net_income, pd.Series) and isinstance(equity, pd.Series):
        try:
            roe = float(net_income.iloc[-1]) / float(equity.iloc[-1]) if float(equity.iloc[-1]) != 0 else None
        except Exception:
            roe = None

    # Valuation (simple EV/EBIT model)
    market_cap = info.get('marketCap')
    shares_out = info.get('sharesOutstanding')
    total_debt_latest = float(total_debt.iloc[-1]) if isinstance(total_debt, pd.Series) and len(total_debt) else None
    cash_latest = float(cash.iloc[-1]) if isinstance(cash, pd.Series) and len(cash) else None
    ebit_latest = float(op_income.iloc[-1]) if isinstance(op_income, pd.Series) and len(op_income) else None

    ev = None
    if market_cap is not None and total_debt_latest is not None and cash_latest is not None:
        ev = float(market_cap) + total_debt_latest - cash_latest

    ev_ebit = (ev / ebit_latest) if ev and ebit_latest and ebit_latest != 0 else None

    # Fair value via peer multiple (configurable). Default 15x EV/EBIT.
    peer_multiple = 15.0
    fair_ev = (peer_multiple * ebit_latest) if ebit_latest else None
    fair_equity = (fair_ev - (total_debt_latest or 0) + (cash_latest or 0)) if fair_ev is not None else None
    fair_value = (fair_equity / shares_out) if (fair_equity and shares_out) else None

    upside = None
    if fair_value and current_price:
        upside = (fair_value / current_price) - 1

    # Scorecard thresholds (tweak to profile)
    def verdict(val: Optional[float], threshold: float, mode: str = '>=', fmt=lambda x: f"{x:.2f}"):
        if val is None:
            return 'amber', 'Insufficient data'
        ok = (val >= threshold) if mode == '>=' else (val <= threshold)
        return ('green' if ok else 'red'), f"{fmt(val)} vs threshold {fmt(threshold)}"

    v1, d1 = verdict(rev_cagr, 0.05, '>=', fmt=lambda x: f"{x*100:.1f}%")
    v2, d2 = verdict(op_margin, 0.10, '>=', fmt=lambda x: f"{x*100:.1f}%")
    v3, d3 = verdict(nd_to_eq, 1.0, '<=', fmt=lambda x: f"{x:.2f}x")
    v4, d4 = verdict(interest_cover, 4.0, '>=', fmt=lambda x: f"{x:.1f}x")
    v5, d5 = verdict(roe, 0.10, '>=', fmt=lambda x: f"{x*100:.1f}%")

    scorecard = [
        ScoreItem(id="rev_cagr", label="Revenue growth (CAGR)", verdict=v1, detail=d1),
        ScoreItem(id="op_margin", label="Operating margin", verdict=v2, detail=d2),
        ScoreItem(id="nd_eq", label="Net debt / Equity", verdict=v3, detail=d3),
        ScoreItem(id="int_cover", label="Interest coverage", verdict=v4, detail=d4),
        ScoreItem(id="roe", label="ROE", verdict=v5, detail=d5),
    ]

    # Pros/Cons/Risks (rule-based placeholders; replace with RAG-LM later)
    pros: List[BulletItem] = []
    cons: List[BulletItem] = []
    risks: List[BulletItem] = []

    if rev_cagr and rev_cagr > 0.10:
        pros.append(BulletItem(text=f"Strong top-line growth (~{safe_pct(rev_cagr)} CAGR)", source=None))
    if op_margin and op_margin > 0.20:
        pros.append(BulletItem(text=f"High operating margins (~{safe_pct(op_margin)})", source=None))
    if roe and roe > 0.15:
        pros.append(BulletItem(text=f"Solid ROE (~{safe_pct(roe)})", source=None))

    if nd_to_eq and nd_to_eq > 1.0:
        cons.append(BulletItem(text=f"Leverage elevated (Net Debt/Equity ~{nd_to_eq:.2f}x)", source=None))
    if interest_cover and interest_cover < 4.0:
        cons.append(BulletItem(text=f"Low interest coverage (~{interest_cover:.1f}x)", source=None))

    risks.append(BulletItem(text="Cyclicality and capital expenditure sensitivity typical for robotics/tech hardware", source=None))
    if info.get('country') == 'China':
        risks.append(BulletItem(text="Geopolitical and export-control risk exposure", source=None))

    # Valuation table
    val_table = [
        ValuationRow(metric="Current Price", value=f"${current_price:.2f}" if current_price else "—"),
        ValuationRow(metric="EV/EBIT", value=f"{ev_ebit:.1f}x" if ev_ebit else "—", note="Simple EV incl. total debt – cash"),
        ValuationRow(metric="Peer EV/EBIT (assumed)", value=f"{peer_multiple:.1f}x", note="Adjust per sector"),
        ValuationRow(metric="Fair Value (per share)", value=f"${fair_value:.2f}" if fair_value else "—"),
        ValuationRow(metric="Upside", value=f"{(upside*100):.1f}%" if upside is not None else "—"),
    ]

    # Sources
    y_url = f"https://finance.yahoo.com/quote/{ticker}"
    sources = [SourceItem(title=f"Yahoo Finance – {ticker}", url=y_url)]

    return AnalyzeResponse(
        meta={"queryType": "company", "ticker": ticker, "asOf": dt.date.today().isoformat()},
        scorecard=scorecard,
        valuation=ValuationBlock(table=val_table, fairValue=fair_value, currentPrice=current_price, upsidePct=(upside*100 if upside is not None else None)),
        pros=pros,
        cons=cons,
        risks=risks,
        sources=sources,
    )


def analyze_industry(industry: str, years: int) -> AnalyzeResponse:
    tickers = INDUSTRY_MAP.get(industry, [])
    if not tickers:
        return AnalyzeResponse(
            meta={"queryType": "industry", "industry": industry, "asOf": dt.date.today().isoformat()},
            scorecard=[], valuation=ValuationBlock(), pros=[], cons=[], risks=[], sources=[]
        )

    # Aggregate by averaging company metrics (very simple; replace with weighted aggregation later)
    comps = [analyze_company(t, years) for t in tickers]

    # Average the numeric bits we care about from scorecard if possible (green=2, amber=1, red=0)
    def score_to_num(v):
        return {"green": 2, "amber": 1, "red": 0}.get(v, 1)

    labels = ["Revenue growth (CAGR)", "Operating margin", "Net debt / Equity", "Interest coverage", "ROE"]
    agg_scores: Dict[str, float] = {k: 0.0 for k in labels}
    counts: Dict[str, int] = {k: 0 for k in labels}

    for c in comps:
        for s in c.scorecard:
            if s.label in agg_scores:
                agg_scores[s.label] += score_to_num(s.verdict)
                counts[s.label] += 1

    scorecard = []
    for label in labels:
        if counts[label] == 0:
            continue
        avg = agg_scores[label] / counts[label]
        verdict = 'green' if avg >= 1.5 else ('amber' if avg >= 1.0 else 'red')
        scorecard.append(ScoreItem(id=label.lower().replace(' ', '_'), label=label, verdict=verdict, detail=f"Average score {avg:.2f}"))

    # Aggregate valuation (median upside among comps)
    upsides = [c.valuation.upsidePct for c in comps if c.valuation and c.valuation.upsidePct is not None]
    med_upside = float(np.median(upsides)) if upsides and np is not None else None

    sources = []
    for t in tickers:
        sources.append(SourceItem(title=f"Yahoo Finance – {t}", url=f"https://finance.yahoo.com/quote/{t}"))

    return AnalyzeResponse(
        meta={"queryType": "industry", "industry": industry, "asOf": dt.date.today().isoformat()},
        scorecard=scorecard,
        valuation=ValuationBlock(table=[ValuationRow(metric="Median Upside (peers)", value=f"{med_upside:.1f}%" if med_upside is not None else "—")], fairValue=None, currentPrice=None, upsidePct=med_upside),
        pros=[BulletItem(text="Secular growth in automation and AI adoption", source=None)],
        cons=[BulletItem(text="Valuation dispersion across sub-segments is high", source=None)],
        risks=[BulletItem(text="Capex cycles and supply chain constraints can impact orders", source=None)],
        sources=sources,
    )

# -------------------- API Routes -------------------- #

@app.get("/api/suggest", response_model=List[SuggestItem])
async def suggest(q: str = Query("")):
    ql = q.lower().strip()
    items = DEMO_INDUSTRIES + DEMO_COMPANIES
    if not ql:
        return items[:8]
    out = []
    for it in items:
        text = (it["label"] + " " + it["value"]).lower()
        if ql in text:
            out.append(it)
    return out[:8]

@app.get("/api/analyze", response_model=AnalyzeResponse)
async def analyze(query: str = Query(...), years: int = Query(10, ge=1, le=10)):
    # decide company vs industry
    val = query.strip()
    is_company = any(val.upper() == c["value"] or val.lower() in c["label"].lower() for c in DEMO_COMPANIES)
    is_industry = any(val.lower() == i["value"].lower() or val.lower() in i["label"].lower() for i in DEMO_INDUSTRIES)

    if is_company:
        # find exact ticker
        for c in DEMO_COMPANIES:
            if val.upper() == c["value"] or val.lower() == c["label"].lower():
                return analyze_company(c["value"], years)
        # fallback: treat as ticker
        return analyze_company(val.upper(), years)

    if is_industry:
        # pick canonical industry key
        for i in DEMO_INDUSTRIES:
            if val.lower() == i["value"].lower() or val.lower() == i["label"].lower():
                return analyze_industry(i["value"], years)
        return analyze_industry(val, years)

    # default heuristic: if it looks like a ticker (<=5 chars, no spaces) treat as company
    if len(val) <= 6 and " " not in val:
        return analyze_company(val.upper(), years)

    # otherwise, treat as industry keyword
    return analyze_industry("Robotics", years)

# -------------------- Health -------------------- #

@app.get("/health")
async def health():
    return {"ok": True, "time": dt.datetime.utcnow().isoformat() + "Z"}
