from fastapi import APIRouter, Query
from models.schemas import AnalyzeResponse
from services.company import analyze_company
from services.industry import analyze_industry
from services.thresholds import thresholds_from_params
from utils.data import DEMO_INDUSTRIES, ALL_US_COMPANIES

router = APIRouter()

@router.get("/api/analyze", response_model=AnalyzeResponse)
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