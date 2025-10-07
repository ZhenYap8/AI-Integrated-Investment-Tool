from fastapi import APIRouter, Query
from models.schemas import SuggestItem
from utils.data import load_us_tickers, DEMO_INDUSTRIES

router = APIRouter()

ALL_US_COMPANIES = load_us_tickers()

@router.get("/suggest", response_model=list[SuggestItem])
async def suggest(q: str = Query("")):
    ql = q.lower().strip()
    items = DEMO_INDUSTRIES + ALL_US_COMPANIES
    if not ql:
        return items[:8]
    return [it for it in items if ql in (it["label"] + " " + it["value"]).lower()][:8]