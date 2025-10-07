from models.schemas import AnalyzeResponse, ValuationBlock, ValuationRow, BulletItem, SourceItem, ScoreItem
from utils.finance import get_yf_ticker, get_row, safe_pct, last_value
from services.metrics import (
    calculate_revenue_cagr,
    calculate_operating_margin,
    calculate_net_debt_to_equity,
    calculate_interest_coverage,
    calculate_roe,
)
from services.valuation import calculate_ev, calculate_ev_ebit, calculate_fair_value, calculate_upside
from services.roe import calculate_historical_roe
import pandas as pd
import datetime as dt
from typing import List, Dict, Optional
from fastapi import HTTPException

def analyze_company(ticker: str, years: int, thresh: Dict[str, float]) -> AnalyzeResponse:
    try:
        t = get_yf_ticker(ticker)

        # Price & info
        hist = t.history(period="max")
        if pd is not None and years and not getattr(hist, 'empty', True):
            cutoff = pd.Timestamp.today(tz=hist.index.tz) - pd.DateOffset(years=years)
            hist = hist.loc[hist.index >= cutoff]
        current_price = float(hist["Close"].iloc[-1]) if not hist.empty else None

        info = getattr(t, 'info', {}) or {}

        # Financial statements (annual)
        fin = getattr(t, 'financials', None)
        bs = getattr(t, 'balance_sheet', None)

        rev = get_row(fin, 'Total Revenue')
        op_income = get_row(fin, 'Operating Income')
        net_income = get_row(fin, 'Net Income')
        interest_exp = get_row(fin, 'Interest Expense')
        total_debt = get_row(bs, 'Total Debt')
        cash = get_row(bs, 'Cash And Cash Equivalents')
        equity = get_row(bs, 'Total Stockholder Equity')

        # Metrics
        rev_cagr = calculate_revenue_cagr(rev, years)
        op_margin = calculate_operating_margin(op_income, rev)
        nd_to_eq = calculate_net_debt_to_equity(total_debt, cash, equity)
        interest_cover = calculate_interest_coverage(op_income, interest_exp)
        roe = calculate_roe(net_income, equity)

        # Valuation
        market_cap = info.get('marketCap')
        shares_out = info.get('sharesOutstanding')
        ev = calculate_ev(market_cap, last_value(total_debt), last_value(cash))
        ev_ebit = calculate_ev_ebit(ev, last_value(op_income))
        fair_value = calculate_fair_value(ev, last_value(op_income), 15.0, last_value(total_debt), last_value(cash), shares_out, market_cap, current_price)
        upside_pct = calculate_upside(fair_value, current_price)

        # Scorecard
        scorecard = [
            # Revenue growth (CAGR)
            ScoreItem(
                id="rev_cagr",
                label="Revenue growth (CAGR)",
                value=rev_cagr * 100 if rev_cagr is not None else None,
                verdict="green" if rev_cagr and rev_cagr >= thresh["rev_cagr_min"] else "red",
                threshold=thresh["rev_cagr_min"] * 100,
                unit="pct",
            ),

            # Operating margin
            ScoreItem(
                id="op_margin",
                label="Operating margin",
                value=op_margin * 100 if op_margin is not None else None,
                verdict="green" if op_margin and op_margin >= thresh["op_margin_min"] else "red",
                threshold=thresh["op_margin_min"] * 100,
                unit="pct",
            ),

            # Net debt to equity
            ScoreItem(
                id="nd_eq",
                label="Net debt / Equity",
                value=nd_to_eq if nd_to_eq is not None else None,
                verdict="green" if nd_to_eq and nd_to_eq <= thresh["nd_eq_max"] else "red",
                threshold=thresh["nd_eq_max"],
                unit="x",
            ),

            # Interest coverage
            ScoreItem(
                id="int_cover",
                label="Interest coverage",
                value=interest_cover if interest_cover is not None else None,
                verdict="green" if interest_cover and interest_cover >= thresh["interest_cover_min"] else "red",
                threshold=thresh["interest_cover_min"],
                unit="x",
            ),

            # Return on Equity (ROE)
            ScoreItem(
                id="roe",
                label="Return on Equity (ROE)",
                value=roe * 100 if roe is not None else None,
                verdict="green" if roe and roe >= thresh["roe_min"] else "red",
                threshold=thresh["roe_min"] * 100,
                unit="pct",
            ),
        ]

        # Pros, cons, risks
        pros = []
        cons = []
        risks = []

        # Sources
        sources = [SourceItem(title=f"Yahoo Finance – {ticker}", url=f"https://finance.yahoo.com/quote/{ticker}")]

        # Historical ROE
        historical_roe = calculate_historical_roe(net_income, equity)

        return AnalyzeResponse(
            meta={"queryType": "company", "ticker": ticker, "asOf": dt.date.today().isoformat()},
            scorecard=scorecard,
            valuation=ValuationBlock(...),
            pros=pros,
            cons=cons,
            risks=risks,
            sources=sources,
            prices=historical_roe,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to analyze company {ticker}: {e}")