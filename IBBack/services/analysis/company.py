"""Individual company financial analysis - streamlined."""
import datetime as dt
from typing import Dict, Any, Tuple
from fastapi import HTTPException

from models.schemas2 import AnalyzeResponse, ValuationBlock, BulletItem, SourceItem, ScoreItem
from utils.finance2 import get_row, last_value, avg_last_n, split_first_last, ratio_safe, cagr, safe_pct, build_historical_roe
from services.scorecard_service import ScorecardService
from .base import BaseAnalyzer


class CompanyAnalyzer(BaseAnalyzer):
    """Streamlined company analyzer."""
    
    def __init__(self):
        super().__init__()
        self.scorecard_service = ScorecardService()
    
    def analyze(self, ticker: str, years: int, thresh: Dict[str, float], period=None) -> AnalyzeResponse:
        try:
            import yfinance as yf
            t = yf.Ticker(ticker)
            info = getattr(t, 'info', {}) or {}
            
            # Extract all data in one pass
            metrics = self._extract_all_metrics(t, years)
            
            # Build response components using scorecard_service
            scorecard = self.scorecard_service.build_scorecard(metrics, thresh, years)
            valuation = self._build_valuation(metrics, info)
            insights = self._generate_insights(metrics, info)
            
            return AnalyzeResponse(
                meta={"queryType": "company", "ticker": ticker, "asOf": dt.date.today().isoformat()},
                metrics=metrics,
                scorecard=scorecard,
                valuation=valuation,
                pros=insights['pros'],
                cons=insights['cons'], 
                risks=insights['risks'],
                sources=[SourceItem(title=f"Yahoo Finance – {ticker}", url=f"https://finance.yahoo.com/quote/{ticker}")],
                prices=build_historical_roe(metrics.get('net_income'), metrics.get('equity'), 5)
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Analysis failed for {ticker}: {e}")
    
    def _extract_all_metrics(self, ticker_obj, years: int) -> Dict[str, Any]:
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
        }
    
    def _build_valuation(self, metrics: Dict[str, Any], info: Dict[str, Any]) -> ValuationBlock:
        """Simplified valuation."""
        return ValuationBlock(table=[], fairValue=None, currentPrice=info.get('currentPrice'), upsidePct=None)
    
    def _generate_insights(self, metrics: Dict[str, Any], info: Dict[str, Any]) -> Dict[str, list]:
        """Generate insights efficiently."""
        pros, cons, risks = [], [], []
        
        if metrics.get('revenue_cagr', 0) > 0.10:
            pros.append(BulletItem(text=f"Strong growth (~{safe_pct(metrics['revenue_cagr'])} CAGR)"))
        if metrics.get('operating_margin', 0) > 0.20:
            pros.append(BulletItem(text=f"High margins (~{safe_pct(metrics['operating_margin'])})"))
            
        risks.append(BulletItem(text="Market volatility and sector cyclicality"))
        
        return {'pros': pros, 'cons': cons, 'risks': risks}