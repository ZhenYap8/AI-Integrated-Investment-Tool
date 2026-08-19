"""
Repeatable market screening pipeline.

Loads the NASDAQ / Yahoo Finance universe, computes fundamentals on a
scheduled feed, and caches interpretable stock scores for the dashboard.
"""
from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from data.universe_extension import exchange_label, find_company, load_tickers
from services.analysis.company import CompanyAnalyzer
from services.analysis.thresholds import ThresholdManager
from services.pipeline.stock_scorer import StockScorer

# Liquid NASDAQ names — reliable Yahoo Finance coverage on free tier
DEFAULT_SCREEN_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA", "AVGO", "COST",
    "NFLX", "AMD", "ADBE", "PEP", "CSCO", "INTC", "CMCSA", "QCOM", "TXN", "AMGN",
    "INTU", "ISRG", "BKNG", "VRTX", "ADP", "GILD", "MU", "LRCX", "REGN", "PANW",
    "SNPS", "CDNS", "KLAC", "MRVL", "CRWD", "FTNT", "ORLY", "MNST", "PCAR", "DXCM",
    "MELI", "ABNB", "PYPL", "SBUX", "MDLZ", "MAR", "ADSK", "WDAY", "TEAM", "ZS",
]

CACHE_PATH = os.getenv("SCREEN_CACHE_PATH", "/tmp/market_screen_cache.json")
CACHE_TTL_SECONDS = int(os.getenv("SCREEN_CACHE_TTL", str(12 * 3600)))
MAX_TICKERS = int(os.getenv("SCREEN_MAX_TICKERS", "50"))
FETCH_DELAY_SECONDS = float(os.getenv("SCREEN_FETCH_DELAY", "0.15"))


class MarketPipeline:
    def __init__(self):
        self._lock = threading.Lock()
        self._refresh_lock = threading.Lock()
        self._analyzer = CompanyAnalyzer()
        self._scorer = StockScorer()
        self._state: Dict[str, Any] = {
            "status": "idle",
            "updatedAt": None,
            "startedAt": None,
            "exchange": "US_NASDAQ",
            "years": 5,
            "thresholds": ThresholdManager.DEFAULT_THRESHOLDS,
            "items": [],
            "stats": {"total": 0, "scored": 0, "errors": 0},
            "error": None,
        }
        self._load_cache()

    def status(self) -> Dict[str, Any]:
        with self._lock:
            stale = self._is_stale_unlocked()
            return {
                **self._state,
                "stale": stale,
                "cachePath": CACHE_PATH,
                "cacheTtlHours": round(CACHE_TTL_SECONDS / 3600, 1),
            }

    def results(
        self,
        *,
        exchange: Optional[str] = None,
        min_score: Optional[float] = None,
        sort: str = "score",
        limit: int = 100,
    ) -> Dict[str, Any]:
        self.ensure_fresh()
        with self._lock:
            items = list(self._state.get("items") or [])

        if exchange:
            ex = exchange.upper()
            items = [
                it for it in items
                if (it.get("exchange") or "").upper() == ex
                or (it.get("exchangeLabel") or "").upper() == ex
            ]

        if min_score is not None:
            items = [it for it in items if (it.get("compositeScore") or 0) >= min_score]

        reverse = sort != "ticker"
        if sort == "ticker":
            items.sort(key=lambda x: (x.get("ticker") or ""))
        elif sort == "grade":
            items.sort(key=lambda x: (x.get("compositeScore") or 0), reverse=True)
        else:
            items.sort(key=lambda x: (x.get("compositeScore") or 0), reverse=reverse)

        return {
            "updatedAt": self._state.get("updatedAt"),
            "status": self._state.get("status"),
            "stale": self._is_stale(),
            "exchange": self._state.get("exchange"),
            "years": self._state.get("years"),
            "count": len(items[:limit]),
            "items": items[:limit],
        }

    def ensure_fresh(self) -> None:
        with self._lock:
            needs_refresh = (
                not self._state.get("items")
                or (self._is_stale_unlocked() and self._state.get("status") != "running")
            )
        if needs_refresh:
            self.refresh_async()

    def refresh_async(self, force: bool = False) -> Dict[str, Any]:
        if not force and self._state.get("status") == "running":
            return self.status()

        def _run():
            self.refresh(force=force)

        thread = threading.Thread(target=_run, daemon=True, name="market-pipeline")
        thread.start()
        return self.status()

    def refresh(self, force: bool = False) -> Dict[str, Any]:
        if not self._refresh_lock.acquire(blocking=False):
            return self.status()

        try:
            with self._lock:
                if not force and self._state.get("status") == "running":
                    return self.status()
                self._state["status"] = "running"
                self._state["startedAt"] = _now_iso()
                self._state["error"] = None

            universe = self._resolve_universe()
            years = 5
            thresholds = ThresholdManager.DEFAULT_THRESHOLDS
            scored_items: List[Dict[str, Any]] = []
            errors = 0

            for entry in universe:
                ticker = entry["value"]
                try:
                    import yfinance as yf

                    t = yf.Ticker(ticker)
                    info = getattr(t, "info", {}) or {}
                    metrics = self._analyzer._extract_all_metrics(t, years)
                    score = self._scorer.score(metrics, thresholds, years)
                    match = find_company(ticker, load_tickers(max_count=10000))
                    ex = entry.get("exchange") or (match.get("exchange") if match else "US_NASDAQ")

                    scored_items.append(
                        {
                            "ticker": ticker.upper(),
                            "companyName": info.get("longName") or info.get("shortName") or entry.get("label") or ticker,
                            "exchange": ex,
                            "exchangeLabel": exchange_label(ex),
                            "sector": info.get("sector"),
                            "industry": info.get("industry"),
                            "compositeScore": score["compositeScore"],
                            "grade": score["grade"],
                            "passRate": score["passRate"],
                            "greens": score["greens"],
                            "totalMetrics": score["totalMetrics"],
                            "breakdown": score["breakdown"],
                            "scorecard": score["scorecard"],
                            "metrics": {
                                k: v for k, v in metrics.items()
                                if k in {
                                    "revenue_cagr", "operating_margin", "net_debt_to_equity",
                                    "interest_coverage", "roe", "history_years",
                                } and v is not None
                            },
                        }
                    )
                except Exception as exc:
                    errors += 1
                    print(f"[pipeline] {ticker}: {exc}")
                time.sleep(FETCH_DELAY_SECONDS)

            scored_items.sort(key=lambda x: x.get("compositeScore") or 0, reverse=True)
            for idx, item in enumerate(scored_items, start=1):
                item["rank"] = idx

            payload = {
                "status": "ready",
                "updatedAt": _now_iso(),
                "startedAt": self._state.get("startedAt"),
                "exchange": "US_NASDAQ",
                "years": years,
                "thresholds": thresholds,
                "items": scored_items,
                "stats": {
                    "total": len(universe),
                    "scored": len(scored_items),
                    "errors": errors,
                },
                "error": None,
            }

            with self._lock:
                self._state = payload
            self._save_cache(payload)
            return self.status()
        except Exception as exc:
            with self._lock:
                self._state["status"] = "error"
                self._state["error"] = str(exc)
            return self.status()
        finally:
            self._refresh_lock.release()

    def _resolve_universe(self) -> List[Dict[str, str]]:
        nasdaq = load_tickers(include_exchanges=["US_NASDAQ"], max_count=MAX_TICKERS * 3)
        if nasdaq:
            # Prefer well-known liquid names when present in NASDAQ feed
            by_symbol = {t["value"].upper(): t for t in nasdaq}
            ordered: List[Dict[str, str]] = []
            for sym in DEFAULT_SCREEN_TICKERS:
                if sym in by_symbol:
                    ordered.append(by_symbol[sym])
                if len(ordered) >= MAX_TICKERS:
                    break
            if len(ordered) < MAX_TICKERS:
                for t in nasdaq:
                    if t["value"].upper() not in {x["value"].upper() for x in ordered}:
                        ordered.append(t)
                    if len(ordered) >= MAX_TICKERS:
                        break
            return ordered[:MAX_TICKERS]

        return [
            {"label": sym, "value": sym, "exchange": "US_NASDAQ", "type": "company"}
            for sym in DEFAULT_SCREEN_TICKERS[:MAX_TICKERS]
        ]

    def _is_stale(self) -> bool:
        with self._lock:
            return self._is_stale_unlocked()

    def _is_stale_unlocked(self) -> bool:
        updated = self._state.get("updatedAt")
        if not updated:
            return True
        try:
            ts = datetime.fromisoformat(updated.replace("Z", "+00:00"))
            age = (datetime.now(timezone.utc) - ts).total_seconds()
            return age > CACHE_TTL_SECONDS
        except Exception:
            return True

    def _load_cache(self) -> None:
        try:
            if not os.path.exists(CACHE_PATH):
                return
            with open(CACHE_PATH, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, dict) and data.get("items") is not None:
                with self._lock:
                    self._state.update(data)
                    if self._state.get("status") == "running":
                        self._state["status"] = "ready"
        except Exception as exc:
            print(f"[pipeline] cache load failed: {exc}")

    def _save_cache(self, payload: Dict[str, Any]) -> None:
        try:
            os.makedirs(os.path.dirname(CACHE_PATH) or ".", exist_ok=True)
            with open(CACHE_PATH, "w", encoding="utf-8") as fh:
                json.dump(payload, fh)
        except Exception as exc:
            print(f"[pipeline] cache save failed: {exc}")


_pipeline: Optional[MarketPipeline] = None


def get_pipeline() -> MarketPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = MarketPipeline()
    return _pipeline


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
