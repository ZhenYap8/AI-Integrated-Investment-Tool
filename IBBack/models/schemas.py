from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

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
    table: List[ValuationRow] = Field(default_factory=list)
    fairValue: Optional[float] = None
    currentPrice: Optional[float] = None
    upsidePct: Optional[float] = None  # percentage (e.g., 12.3 for +12.3%)

class ScoreItem(BaseModel):
    id: str
    label: str
    verdict: str           # "green" | "amber" | "red"
    detail: Optional[str] = None
    value: Optional[float] = None      # raw numeric (pct in 0–100 if unit=='pct')
    threshold: Optional[float] = None  # same unit as value
    unit: Optional[str] = None         # 'pct', 'x', etc.


class AnalyzeResponse(BaseModel):
    meta: Dict[str, Any]
    scorecard: List[ScoreItem] = Field(default_factory=list)
    valuation: ValuationBlock = Field(default_factory=ValuationBlock)
    pros: List[BulletItem] = Field(default_factory=list)
    cons: List[BulletItem] = Field(default_factory=list)
    risks: List[BulletItem] = Field(default_factory=list)
    sources: List[SourceItem] = Field(default_factory=list)
    prices: List[Dict[str, Any]] = Field(default_factory=list)  # Add this line
