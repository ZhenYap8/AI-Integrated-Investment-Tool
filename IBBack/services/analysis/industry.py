"""Industry analysis - simplified aggregation."""
import datetime as dt
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

from models.schemas2 import AnalyzeResponse, ValuationBlock, BulletItem, SourceItem, ScoreItem
from data.universe2 import INDUSTRY_MAP
from .base import BaseAnalyzer


class IndustryAnalyzer(BaseAnalyzer):
    """Analyzer for industry-level analysis."""
    
    def __init__(self):
        super().__init__()
        self.company_analyzer = None  # Will use CompanyAnalyzer if needed
    
    def analyze(self, industry: str, years: int, thresh: Dict[str, float], period=None) -> AnalyzeResponse:
        tickers = INDUSTRY_MAP.get(industry, [])
        if not tickers:
            return self._empty_response(industry)
        
        # Import CompanyAnalyzer here to avoid circular dependency
        from .company import CompanyAnalyzer
        company_analyzer = CompanyAnalyzer()
        
        # Parallel analysis - simplified
        companies = []
        with ThreadPoolExecutor(max_workers=min(3, len(tickers))) as executor:
            futures = {executor.submit(company_analyzer.analyze, t, years, thresh, period): t for t in tickers}
            for future in as_completed(futures):
                try:
                    companies.append(future.result(timeout=20))
                except Exception:
                    continue  # Skip failed companies
        
        # Quick aggregation
        scorecard = self._quick_scorecard(companies)
        
        return AnalyzeResponse(
            meta={"queryType": "industry", "industry": industry, "asOf": dt.date.today().isoformat()},
            scorecard=scorecard,
            valuation=ValuationBlock(),
            pros=[BulletItem(text="Secular growth trends in automation")],
            cons=[BulletItem(text="Valuation dispersion across peers")],
            risks=[BulletItem(text="Supply chain and capex sensitivity")],
            sources=[SourceItem(title=f"YF-{t}", url=f"https://finance.yahoo.com/quote/{t}") for t in tickers[:3]]
        )
    
    def _empty_response(self, industry: str) -> AnalyzeResponse:
        return AnalyzeResponse(
            meta={"queryType": "industry", "industry": industry, "asOf": dt.date.today().isoformat()},
            scorecard=[], valuation=ValuationBlock(), pros=[], cons=[], risks=[], sources=[]
        )
    
    def _quick_scorecard(self, companies: List[AnalyzeResponse]) -> List[ScoreItem]:
        """Quick scorecard aggregation."""
        if not companies:
            return []
        
        # Count green/red verdicts
        labels = ["Revenue growth", "Operating margin", "ROE"]
        scores = {label: {'green': 0, 'total': 0} for label in labels}
        
        for comp in companies:
            for item in comp.scorecard:
                if item.label in scores:
                    scores[item.label]['total'] += 1
                    if item.verdict == 'green':
                        scores[item.label]['green'] += 1
        
        # Build aggregated scorecard
        result = []
        for label, data in scores.items():
            if data['total'] > 0:
                pct = data['green'] / data['total']
                verdict = 'green' if pct >= 0.6 else ('amber' if pct >= 0.3 else 'red')
                result.append(ScoreItem(
                    id=label.lower().replace(' ', '_'),
                    label=label,
                    verdict=verdict,
                    detail=f"{data['green']}/{data['total']} companies pass"
                ))
        
        return result