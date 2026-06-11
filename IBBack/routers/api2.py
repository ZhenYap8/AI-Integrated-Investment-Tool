from typing import List, Dict, Optional
from fastapi import APIRouter, Query, HTTPException
import datetime as dt

from models.schemas2 import SuggestItem, AnalyzeResponse, ProsConsResponse
from services.analyzer2 import analyze_company, analyze_industry, thresholds_from_params
from services.proscons import analyze_proscons_ai_only
from services.analysis.valuation_engine import ValuationEngine
from services.analysis.base import BaseAnalyzer
from data.universe_extension import (
    DEMO_INDUSTRIES,
    GLOBAL_TICKERS,
    find_company,
    suggest as universe_suggest,
    looks_like_ticker,
    normalize_ticker,
    exchange_label,
    load_tickers,
)
from services.scorecard_service import ScorecardService

router = APIRouter()


@router.get("/api/suggest", response_model=List[SuggestItem])
async def suggest(
    q: str = Query(""),
    exchange: Optional[str] = Query(None, description="Filter by exchange id, e.g. LSE, US_NASDAQ"),
    limit: int = Query(8, ge=1, le=50),
):
    items = universe_suggest(q, limit=limit * 3)
    if exchange:
        ex = exchange.upper()
        items = [
            it for it in items
            if it.get("exchange", "").upper() == ex or exchange_label(it.get("exchange")).upper() == ex
        ]
    return items[:limit]


@router.get("/api/analyze", response_model=AnalyzeResponse)
async def analyze(
    query: str = Query(...),
    years: Optional[int] = Query(None, ge=1, le=10),
    period: Optional[str] = Query(None),
    range_: Optional[str] = Query(None, alias="range"),
    rev_cagr_min: float | None = Query(None),
    op_margin_min: float | None = Query(None),
    nd_eq_max: float | None = Query(None),
    interest_cover_min: float | None = Query(None),
    roe_min: float | None = Query(None),
):
    period = (range_ or period)
    thresh = thresholds_from_params(
        rev_cagr_min=rev_cagr_min,
        op_margin_min=op_margin_min,
        nd_eq_max=nd_eq_max,
        interest_cover_min=interest_cover_min,
        roe_min=roe_min,
    )

    val = (query or "").strip()
    yrs = BaseAnalyzer.resolve_analysis_years(years, period)

    # Exact company match (global universe)
    match = find_company(val, GLOBAL_TICKERS)
    if match:
        return analyze_company(match["value"], yrs, thresh, period=period)

    # Industry match
    for i in DEMO_INDUSTRIES:
        if val.lower() == i["value"].lower() or val.lower() == i["label"].lower():
            return analyze_industry(i["value"], yrs, thresh, period=period)

    # Heuristic: looks like a ticker (supports .L, .TO, .HK, etc.)
    if looks_like_ticker(val):
        return analyze_company(normalize_ticker(val), yrs, thresh, period=period)

    # Partial industry name match
    for i in DEMO_INDUSTRIES:
        if val.lower() in i["label"].lower() or val.lower() in i["value"].lower():
            return analyze_industry(i["value"], yrs, thresh, period=period)

    raise HTTPException(
        status_code=404,
        detail=f"No match for '{val}'. Try a ticker (e.g. NVDA, BP.L, SHOP.TO) or industry name.",
    )


@router.get("/api/news")
async def news_feed(ticker: str = Query(...), limit: int = Query(12, ge=1, le=30)):
    """Preview aggregated headlines from Yahoo, Reuters, FT, Bloomberg, BBC, etc."""
    try:
        import yfinance as yf
        from services.prosandcons.news_sources import aggregate_news

        t = yf.Ticker(ticker)
        info = getattr(t, "info", {}) or {}
        name = info.get("longName") or info.get("shortName") or ticker
        articles = aggregate_news(ticker, name, ticker_obj=t, total_limit=limit)
        return {
            "ticker": ticker.upper(),
            "company": name,
            "count": len(articles),
            "articles": [
                {
                    "title": a.title,
                    "url": a.url,
                    "date": a.date,
                    "outlet": a.outlet,
                    "feed": a.feed,
                    "snippet": (a.snippet or "")[:300],
                }
                for a in articles
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"News fetch failed: {e}")


@router.get("/health")
async def health():
    return {"ok": True, "time": dt.datetime.utcnow().isoformat() + "Z"}


@router.get("/api/exchanges")
async def exchanges():
    """List supported exchange ids and labels."""
    from data.universe_extension import EXCHANGE_LABELS
    counts: Dict[str, int] = {}
    for t in load_tickers():
        ex = t.get("exchange", "UNKNOWN")
        counts[ex] = counts.get(ex, 0) + 1
    return {
        "exchanges": [
            {"id": k, "label": v, "count": counts.get(k, 0)}
            for k, v in EXCHANGE_LABELS.items()
        ]
    }


@router.post("/api/proscons/analyze", response_model=ProsConsResponse)
async def proscons_analyze(body: Dict[str, Optional[str | int]]):
    ticker = (body or {}).get("ticker")
    if not ticker or not isinstance(ticker, str):
        return ProsConsResponse(company="", asOf=dt.date.today().isoformat(), findings=[])
    max_items = body.get("max") if isinstance(body.get("max"), int) else 8
    period = body.get("period") if isinstance(body.get("period"), str) else None
    years = body.get("years") if isinstance(body.get("years"), int) else None
    return analyze_proscons_ai_only(ticker, max_items=max_items, period=period, years=years)


@router.post("/api/valuation")
async def valuation(request: Dict):
    try:
        ticker_symbol = request.get("ticker")
        metrics = request.get("metrics", {})
        overrides = request.get("overrides", {})

        if not ticker_symbol or not isinstance(ticker_symbol, str):
            raise HTTPException(status_code=400, detail="Missing or invalid 'ticker' in request body")

        engine = ValuationEngine()
        import yfinance as yf
        ticker = yf.Ticker(ticker_symbol)
        result = engine.calculate_valuation(ticker, metrics, overrides)

        return {"ticker": ticker_symbol.upper(), "valuation": result, "status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error performing valuation: {str(e)}")


@router.post("/api/scorecard")
async def scorecard(request: Dict):
    try:
        metrics = request.get("metrics")
        overrides = request.get("overrides", {})
        years = request.get("years", 5)

        if not metrics or not isinstance(metrics, dict):
            raise HTTPException(status_code=400, detail="Missing or invalid 'metrics' in request body")

        service = ScorecardService()
        scorecard_data = service.build_scorecard(metrics, overrides, years)
        return {"scorecard": scorecard_data, "status": "success", "count": len(scorecard_data)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error building scorecard: {str(e)}")
