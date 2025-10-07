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
    upsidePct: Optional[float] = None

class ScoreItem(BaseModel):
    id: str
    label: str
    verdict: str
    detail: Optional[str] = None
    value: Optional[float] = None
    threshold: Optional[float] = None
    unit: Optional[str] = None

class AnalyzeResponse(BaseModel):
    meta: Dict[str, Any]
    scorecard: List[ScoreItem] = Field(default_factory=list)
    valuation: ValuationBlock = Field(default_factory=ValuationBlock)
    pros: List[BulletItem] = Field(default_factory=list)
    cons: List[BulletItem] = Field(default_factory=list)
    risks: List[BulletItem] = Field(default_factory=list)
    sources: List[SourceItem] = Field(default_factory=list)
    prices: List[Dict[str, Any]] = Field(default_factory=list)

# Pros & Cons findings schema (non-breaking addition)
class Evidence(BaseModel):
    url: str
    date: str  # YYYY-MM-DD
    snippet: str

class Finding(BaseModel):
    item: str
    factor: str  # growth|margins|leverage|competition|moat|guidance|legal_esg|other
    direction: str  # pro|con
    timeframe: str  # near_term|1y|multi_year|unspecified
    materiality: float  # 0..1
    evidence: List[Evidence]

class ProsConsResponse(BaseModel):
    company: str
    asOf: str
    findings: List[Finding]
    fromAI: bool = False
