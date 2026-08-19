"""
Interpretable stock scoring from financial metrics.

Each of five fundamentals contributes up to 20 points (100 total).
Missing metrics count as 0 — prevents partial-data stocks from scoring 100/A.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from services.scorecard_service import ScorecardService

METRIC_WEIGHT = 20
EXPECTED_METRICS = 5
MIN_METRICS_FOR_GRADE = 3

METRIC_SPECS = [
    ("rev_cagr", "revenue_cagr", "Revenue CAGR"),
    ("op_margin", "operating_margin", "Operating Margin"),
    ("nd_eq", "net_debt_to_equity", "Net Debt / Equity"),
    ("interest_cover", "interest_coverage", "Interest Coverage"),
    ("roe", "roe", "Return on Equity (ROE)"),
]


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _grade(score: float, metrics_available: int) -> str:
    if metrics_available < MIN_METRICS_FOR_GRADE:
        return "—"
    if score >= 80:
        return "A"
    if score >= 60:
        return "B"
    if score >= 40:
        return "C"
    if score >= 20:
        return "D"
    return "F"


def _metric_points(metric_id: str, value: Optional[float], thresholds: Dict[str, float]) -> float:
    if value is None:
        return 0.0

    if metric_id == "rev_cagr":
        target = thresholds["rev_cagr_min"]
        if target <= 0:
            return METRIC_WEIGHT if value >= 0 else 0.0
        return METRIC_WEIGHT * _clamp(value / target)

    if metric_id == "op_margin":
        target = thresholds["op_margin_min"]
        if target <= 0:
            return METRIC_WEIGHT if value >= 0 else 0.0
        return METRIC_WEIGHT * _clamp(value / target)

    if metric_id == "nd_eq":
        cap = thresholds["nd_eq_max"]
        if value <= cap:
            return float(METRIC_WEIGHT)
        if value <= 0:
            return float(METRIC_WEIGHT)
        return METRIC_WEIGHT * _clamp(cap / value)

    if metric_id == "interest_cover":
        target = thresholds["interest_cover_min"]
        if target <= 0:
            return float(METRIC_WEIGHT)
        return METRIC_WEIGHT * _clamp(value / target)

    if metric_id == "roe":
        target = thresholds["roe_min"]
        if target <= 0:
            return METRIC_WEIGHT if value >= 0 else 0.0
        return METRIC_WEIGHT * _clamp(value / target)

    return 0.0


class StockScorer:
    """Turn raw metrics into a 0–100 composite score with per-metric breakdown."""

    def __init__(self):
        self.scorecard_service = ScorecardService()

    def score(
        self,
        metrics: Dict[str, Any],
        overrides: Optional[Dict[str, float]] = None,
        years: int = 5,
    ) -> Dict[str, Any]:
        thresholds = {**self.scorecard_service.default_thresholds, **(overrides or {})}
        scorecard = self.scorecard_service.build_scorecard(metrics, overrides, years)
        scorecard_by_id = {item["id"]: item for item in scorecard}

        breakdown: List[Dict[str, Any]] = []
        total_points = 0.0
        metrics_available = 0
        greens = 0

        for metric_id, metrics_key, fallback_label in METRIC_SPECS:
            raw_value = metrics.get(metrics_key)
            item = scorecard_by_id.get(metric_id)
            points = _metric_points(metric_id, raw_value, thresholds)
            total_points += points

            if raw_value is not None:
                metrics_available += 1
                verdict = item["verdict"] if item else ("green" if points >= METRIC_WEIGHT else "red")
                if verdict == "green":
                    greens += 1
            else:
                verdict = "missing"

            breakdown.append(
                {
                    "id": metric_id,
                    "label": item["label"] if item else fallback_label,
                    "verdict": verdict,
                    "value": item.get("value") if item else None,
                    "threshold": item.get("threshold") if item else None,
                    "unit": item.get("unit") if item else None,
                    "points": round(points, 1),
                    "maxPoints": METRIC_WEIGHT,
                }
            )

        max_points = EXPECTED_METRICS * METRIC_WEIGHT
        composite = round((total_points / max_points) * 100, 1)
        coverage = round((metrics_available / EXPECTED_METRICS) * 100, 1)

        return {
            "compositeScore": composite,
            "grade": _grade(composite, metrics_available),
            "passRate": round((greens / EXPECTED_METRICS) * 100, 1),
            "greens": greens,
            "totalMetrics": EXPECTED_METRICS,
            "metricsAvailable": metrics_available,
            "dataCoverage": coverage,
            "breakdown": breakdown,
            "scorecard": scorecard,
        }


def score_stock(metrics: Dict[str, Any], overrides: Optional[Dict[str, float]] = None, years: int = 5) -> Dict[str, Any]:
    return StockScorer().score(metrics, overrides, years)
