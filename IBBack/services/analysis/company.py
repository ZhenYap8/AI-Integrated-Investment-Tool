"""Individual company financial analysis - streamlined."""
import datetime as dt
from typing import Dict, Any, Tuple, Optional
from fastapi import HTTPException

from models.schemas2 import AnalyzeResponse, ValuationBlock, BulletItem, SourceItem, ScoreItem
from utils.finance2 import get_row, last_value, avg_last_n, split_first_last, ratio_safe, cagr, safe_pct, build_historical_roe_for_ticker
from services.scorecard_service import ScorecardService
from data.universe_extension import find_company, GLOBAL_TICKERS
from .base import BaseAnalyzer


class CompanyAnalyzer(BaseAnalyzer):
    """Streamlined company analyzer."""
    
    def __init__(self):
        super().__init__()
        self.scorecard_service = ScorecardService()
    
    def analyze(self, ticker: str, years: Optional[int], thresh: Dict[str, float], period=None) -> AnalyzeResponse:
        try:
            import yfinance as yf
            t = yf.Ticker(ticker)
            info = getattr(t, 'info', {}) or {}

            lookback = self.resolve_analysis_years(years, period)
            metrics = self._extract_all_metrics(t, lookback)
            scorecard_years = lookback or metrics.get('history_years') or 5

            scorecard = self.scorecard_service.build_scorecard(metrics, thresh, scorecard_years)
            valuation = self._build_valuation(metrics, info)
            insights = self._generate_insights(metrics, info)
            match = find_company(ticker, GLOBAL_TICKERS)
            exchange = match.get("exchange") if match else self._infer_exchange(ticker)
            company_name = info.get("longName") or info.get("shortName") or ticker
            roe_prices, roe_granularity = build_historical_roe_for_ticker(
                t, period=period, years=lookback, coalesce=self.coalesce
            )

            return AnalyzeResponse(
                meta={
                    "queryType": "company",
                    "ticker": ticker,
                    "companyName": company_name,
                    "exchange": exchange,
                    "sector": info.get("sector"),
                    "industry": info.get("industry"),
                    "asOf": dt.date.today().isoformat(),
                    "roeGranularity": roe_granularity,
                    "historyWindow": period or (f"{lookback}y" if lookback else "max"),
                },
                metrics=metrics,
                scorecard=scorecard,
                valuation=valuation,
                pros=insights['pros'],
                cons=insights['cons'], 
                risks=insights['risks'],
                sources=[SourceItem(title=f"Yahoo Finance – {ticker}", url=f"https://finance.yahoo.com/quote/{ticker}")],
                prices=roe_prices
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Analysis failed for {ticker}: {e}")

    @staticmethod
    def _infer_exchange(ticker: str) -> str:
        """Guess exchange from yfinance suffix."""
        suffix_map = {
            ".L": "LSE", ".TO": "TSX", ".AX": "ASX", ".HK": "HKEX",
            ".T": "TSE_JP", ".DE": "GLOBAL", ".PA": "GLOBAL", ".AS": "GLOBAL",
        }
        for suffix, ex in suffix_map.items():
            if ticker.upper().endswith(suffix):
                return ex
        return "US_OTHER"
    
    def _extract_all_metrics(self, ticker_obj, years: Optional[int]) -> Dict[str, Any]:
        """Extract and calculate all metrics in one efficient pass."""
        fin = getattr(ticker_obj, 'financials', None)
        bs = getattr(ticker_obj, 'balance_sheet', None)
        
        # Core data extraction
        revenue = get_row(fin, 'Total Revenue')
        operating_income = get_row(fin, 'Operating Income')
        net_income = get_row(fin, 'Net Income')
        interest_expense = get_row(fin, 'Interest Expense')
        total_debt = get_row(bs, 'Total Debt')
        cash = get_row(bs, 'Cash And Cash Equivalents')
        equity = self.coalesce(get_row(bs, 'Total Stockholder Equity'), get_row(bs, 'Total Equity Gross Minority Interest'))
        
        # Calculate all metrics at once
        first_rev, last_rev, n_hist = split_first_last(revenue, years)
        last_net_debt = last_value(total_debt) - last_value(cash) if total_debt is not None and cash is not None else None
        last_equity_val = last_value(equity)
        
        return {
            'revenue_cagr': cagr(first_rev, last_rev, n_hist),
            'operating_margin': ratio_safe(last_value(operating_income), last_value(revenue)),
            'net_debt_to_equity': ratio_safe(last_net_debt, last_equity_val) if last_net_debt is not None else None,
            'interest_coverage': ratio_safe(last_value(operating_income), abs(last_value(interest_expense))) if interest_expense is not None else None,
            'roe': ratio_safe(last_value(net_income), avg_last_n(equity, 2)),
            'net_income': net_income,
            'equity': equity,
            'history_years': n_hist,
        }
    
    def _build_valuation(self, metrics: Dict[str, Any], info: Dict[str, Any]) -> ValuationBlock:
        """Simplified valuation."""
        return ValuationBlock(table=[], fairValue=None, currentPrice=info.get('currentPrice'), upsidePct=None)
    
    def _generate_insights(self, metrics: Dict[str, Any], info: Dict[str, Any]) -> Dict[str, list]:
        """Rule-based insights with varied phrasing — used as fallback when AI is unavailable."""
        pros, cons, risks = [], [], []

        cagr = metrics.get('revenue_cagr')
        margin = metrics.get('operating_margin')
        nd_eq = metrics.get('net_debt_to_equity')
        coverage = metrics.get('interest_coverage')
        roe = metrics.get('roe')
        sector = info.get('sector') or info.get('industry') or 'the sector'

        if cagr is not None:
            if cagr >= 0.15:
                pros.append(BulletItem(text=f"Revenue compounding at {safe_pct(cagr)} annually — well above typical {sector} peers."))
            elif cagr >= 0.05:
                pros.append(BulletItem(text=f"Steady top-line expansion ({safe_pct(cagr)} CAGR) supports reinvestment capacity."))
            elif cagr < 0:
                cons.append(BulletItem(text=f"Contracting revenue ({safe_pct(cagr)} CAGR) may signal share loss or cyclical headwinds."))

        if margin is not None:
            if margin >= 0.20:
                pros.append(BulletItem(text=f"Operating margin of {safe_pct(margin)} provides pricing power and buffers cost inflation."))
            elif margin < 0.08:
                cons.append(BulletItem(text=f"Thin operating margin ({safe_pct(margin)}) limits room for error on costs or pricing."))

        if nd_eq is not None:
            if nd_eq <= 0.3:
                pros.append(BulletItem(text=f"Conservative leverage (net debt/equity {nd_eq:.2f}x) reduces refinancing risk."))
            elif nd_eq > 1.5:
                cons.append(BulletItem(text=f"Elevated leverage ({nd_eq:.2f}x net debt/equity) amplifies sensitivity to rate moves."))

        if coverage is not None:
            if coverage >= 8:
                pros.append(BulletItem(text=f"Interest coverage of {coverage:.1f}x comfortably services debt obligations."))
            elif coverage < 3:
                cons.append(BulletItem(text=f"Interest coverage of {coverage:.1f}x is tight — earnings dips could strain debt service."))

        if roe is not None:
            if roe >= 0.18:
                pros.append(BulletItem(text=f"ROE of {safe_pct(roe)} indicates efficient capital deployment."))
            elif roe < 0.05:
                cons.append(BulletItem(text=f"Low ROE ({safe_pct(roe)}) suggests capital may be better deployed elsewhere."))

        beta = info.get('beta')
        if isinstance(beta, (int, float)) and beta > 1.4:
            risks.append(BulletItem(text=f"Beta of {beta:.2f} implies above-market volatility — size positions accordingly."))
        else:
            risks.append(BulletItem(text=f"Macro shifts and {sector} cyclicality remain key swing factors for the equity."))

        return {'pros': pros, 'cons': cons, 'risks': risks}