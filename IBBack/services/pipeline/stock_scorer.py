"""
Interpretable stock scoring from financial metrics.

Each of five fundamentals contributes up to 20 points (100 total).
Partial credit is awarded when a metric is close to its threshold.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from services.scorecard_service import ScorecardService

METRIC_WEIGHT = 20


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _grade(score: float) -> str:
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

        breakdown: List[Dict[str, Any]] = []
        total_points = 0.0
        max_points = 0.0

        for item in scorecard:
            metric_id = item["id"]
            raw_value = metrics.get(self._metrics_key(metric_id))
            points = _metric_points(metric_id, raw_value, thresholds)
            total_points += points
            max_points += METRIC_WEIGHT
            breakdown.append(
                {
                    "id": metric_id,
                    "label": item["label"],
                    "verdict": item["verdict"],
                    "value": item.get("value"),
                    "threshold": item.get("threshold"),
                    "unit": item.get("unit"),
                    "points": round(points, 1),
                    "maxPoints": METRIC_WEIGHT,
                }
            )

        greens = sum(1 for s in scorecard if s["verdict"] == "green")
        total = len(scorecard)
        composite = round((total_points / max_points) * 100, 1) if max_points else 0.0

        return {
            "compositeScore": composite,
            "grade": _grade(composite),
            "passRate": round((greens / total) * 100, 1) if total else 0.0,
            "greens": greens,
            "totalMetrics": total,
            "breakdown": breakdown,
            "scorecard": scorecard,
        }

    @staticmethod
    def _metrics_key(scorecard_id: str) -> str:
        return {
            "rev_cagr": "revenue_cagr",
            "op_margin": "operating_margin",
            "nd_eq": "net_debt_to_equity",
            "interest_cover": "interest_coverage",
            "roe": "roe",
        }.get(scorecard_id, scorecard_id)


def score_stock(metrics: Dict[str, Any], overrides: Optional[Dict[str, float]] = None, years: int = 5) -> Dict[str, Any]:
    return StockScorer().score(metrics, overrides, years)
