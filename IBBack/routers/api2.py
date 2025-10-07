from typing import List, Dict, Optional
from fastapi import APIRouter, Query, HTTPException
import datetime as dt

from models.schemas2 import SuggestItem, AnalyzeResponse, ProsConsResponse
from services.analyzer2 import analyze_company, analyze_industry, thresholds_from_params
from services.proscons import analyze_proscons_ai_only
from services.analysis.valuation_engine import ValuationEngine
from data.universe2 import DEMO_INDUSTRIES, ALL_US_COMPANIES
from services.scorecard_service import ScorecardService

router = APIRouter()

@router.get("/api/suggest", response_model=List[SuggestItem])
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


@router.get("/api/analyze", response_model=AnalyzeResponse)
async def analyze(
    query: str = Query(...),
    years: Optional[int] = Query(None, ge=1, le=10),
    period: Optional[str] = Query(None),
    range_: Optional[str] = Query(None, alias="range"),
    # optional threshold overrides
    rev_cagr_min: float | None = Query(None),
    op_margin_min: float | None = Query(None),
    nd_eq_max: float | None = Query(None),
    interest_cover_min: float | None = Query(None),
    roe_min: float | None = Query(None),
):
    # yfinance-style period support; range alias matches FE/industry parlance
    period = (range_ or period)
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
            result = analyze_company(c["value"], years or 5, thresh, period=period)
            print(f"[Analyze API] Company result metrics: {result.metrics if hasattr(result, 'metrics') else 'NO METRICS'}")
            return result

    # industry?
    for i in DEMO_INDUSTRIES:
        if val.lower() == i["value"].lower() or val.lower() == i["label"].lower():
            result = analyze_industry(i["value"], years or 5, thresh, period=period)
            print(f"[Analyze API] Industry result metrics: {result.metrics if hasattr(result, 'metrics') else 'NO METRICS'}")
            return result

    # heuristic: looks like a ticker (short, no spaces)
    if len(val) <= 6 and " " not in val:
        result = analyze_company(val.upper(), years or 5, thresh, period=period)
        print(f"[Analyze API] Ticker result metrics: {result.metrics if hasattr(result, 'metrics') else 'NO METRICS'}")
        return result

    # fallback: treat as industry search
    result = analyze_industry("Robotics", years or 5, thresh, period=period)
    print(f"[Analyze API] Fallback result metrics: {result.metrics if hasattr(result, 'metrics') else 'NO METRICS'}")
    return result


@router.get("/health")
async def health():
    return {"ok": True, "time": dt.datetime.utcnow().isoformat() + "Z"}


# Pros & Cons (findings) - minimal add-on
@router.post("/api/proscons/analyze", response_model=ProsConsResponse)
async def proscons_analyze(
    body: Dict[str, Optional[str | int]]
):
    ticker = (body or {}).get("ticker")
    if not ticker or not isinstance(ticker, str):
        return ProsConsResponse(company="", asOf=dt.date.today().isoformat(), findings=[])
    max_items = body.get("max") if isinstance(body.get("max"), int) else 8
    period = body.get("period") if isinstance(body.get("period"), str) else None
    years = body.get("years") if isinstance(body.get("years"), int) else None
    return analyze_proscons_ai_only(ticker, max_items=max_items, period=period, years=years)

@router.post("/api/valuation")
async def valuation(request: Dict):
    """
    Perform valuation analysis using the ValuationEngine.
    
    Request body should contain:
        ticker: Stock ticker symbol (string)
        metrics: Dictionary of financial metrics (optional)
        overrides: Dictionary of assumptions/overrides (optional)
    
    Returns:
        Valuation results including fair value and upside percentage
    """
    try:
        ticker_symbol = request.get('ticker')
        metrics = request.get('metrics', {})
        overrides = request.get('overrides', {})
        
        if not ticker_symbol or not isinstance(ticker_symbol, str):
            raise HTTPException(
                status_code=400, 
                detail="Missing or invalid 'ticker' in request body"
            )
        
        engine = ValuationEngine()
        import yfinance as yf
        ticker = yf.Ticker(ticker_symbol)
        
        result = engine.calculate_valuation(ticker, metrics, overrides)
        
        return {
            "ticker": ticker_symbol.upper(),
            "valuation": result,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error performing valuation: {str(e)}"
        )
    

@router.post("/api/scorecard")
async def scorecard(request: Dict):
    """
    Build a financial scorecard based on provided metrics and thresholds.
    """
    try:
        print(f"[Scorecard API] ========== REQUEST START ==========")
        print(f"[Scorecard API] Full request body: {request}")
        
        metrics = request.get('metrics')
        overrides = request.get('overrides', {})
        years = request.get('years', 5)
        
        print(f"[Scorecard API] Extracted metrics: {metrics}")
        print(f"[Scorecard API] Extracted overrides: {overrides}")
        print(f"[Scorecard API] Extracted years: {years}")
        
        if not metrics or not isinstance(metrics, dict):
            print(f"[Scorecard API] ERROR: Invalid metrics - type: {type(metrics)}, value: {metrics}")
            raise HTTPException(
                status_code=400, 
                detail="Missing or invalid 'metrics' in request body"
            )
        
        if len(metrics) == 0:
            print(f"[Scorecard API] WARNING: Empty metrics dictionary")
        
        service = ScorecardService()
        scorecard_data = service.build_scorecard(metrics, overrides, years)
        
        print(f"[Scorecard API] Generated {len(scorecard_data)} scorecard items")
        for idx, item in enumerate(scorecard_data):
            print(f"[Scorecard API] Item {idx+1}: {item['label']} = {item['value']}{item['unit']} (verdict: {item['verdict']})")
        
        response = {
            "scorecard": scorecard_data,
            "status": "success",
            "count": len(scorecard_data)
        }
        print(f"[Scorecard API] ========== REQUEST END (SUCCESS) ==========")
        return response
        
    except HTTPException:
        print(f"[Scorecard API] ========== REQUEST END (HTTP ERROR) ==========")
        raise
    except Exception as e:
        print(f"[Scorecard API] ========== REQUEST END (ERROR) ==========")
        print(f"[Scorecard API] Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error building scorecard: {str(e)}"
        )
