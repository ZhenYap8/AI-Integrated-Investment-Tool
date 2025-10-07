"""
Financial Analyzer - Main orchestrator for company and industry analysis.
Coordinates between specialized analyzers and provides a unified interface.
"""
from typing import Dict
from services.analysis.company import CompanyAnalyzer
from services.analysis.industry import IndustryAnalyzer
from models.schemas2 import AnalyzeResponse


class FinancialAnalyzer:
    """Main analyzer that coordinates company and industry analysis."""
    
    def __init__(self):
        self.company_analyzer = CompanyAnalyzer()
        self.industry_analyzer = IndustryAnalyzer()
    
    def analyze_company(self, ticker: str, years: int, thresh: Dict[str, float], period=None) -> AnalyzeResponse:
        """Analyze a single company using CompanyAnalyzer with scorecard_service."""
        return self.company_analyzer.analyze(ticker, years, thresh, period)
    
    def analyze_industry(self, industry: str, years: int, thresh: Dict[str, float], period=None) -> AnalyzeResponse:
        """Analyze an industry using IndustryAnalyzer."""
        return self.industry_analyzer.analyze(industry, years, thresh, period)