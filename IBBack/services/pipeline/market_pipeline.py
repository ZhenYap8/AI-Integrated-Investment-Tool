"""
Repeatable market screening pipeline.

Loads index universes (S&P 500, NASDAQ 100) and Yahoo Finance fundamentals on a
scheduled feed, then caches interpretable stock scores for the dashboard.
"""
from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from data.universe_extension import exchange_label, find_company, load_index_constituents, load_tickers
from services.analysis.company import CompanyAnalyzer
from services.analysis.thresholds import ThresholdManager
from services.pipeline.stock_scorer import StockScorer

UNIVERSE_PRESETS: Dict[str, Dict[str, Any]] = {
    "sp500": {"label": "S&P 500", "index": "S&P 500", "exchange": "US_OTHER", "defaultMax": 500},
    "nasdaq100": {"label": "NASDAQ 100", "index": "NASDAQ 100", "exchange": "US_NASDAQ", "defaultMax": 101},
    "nasdaq": {"label": "NASDAQ listed", "index": None, "exchange": "US_NASDAQ", "defaultMax": 200},
}

CACHE_PATH = os.getenv("SCREEN_CACHE_PATH", "/tmp/market_screen_cache.json")
CACHE_TTL_SECONDS = int(os.getenv("SCREEN_CACHE_TTL", str(12 * 3600)))
MAX_TICKERS = int(os.getenv("SCREEN_MAX_TICKERS", "500"))
DEFAULT_UNIVERSE = os.getenv("SCREEN_UNIVERSE", "sp500")
FETCH_DELAY_SECONDS = float(os.getenv("SCREEN_FETCH_DELAY", "0.12"))


class MarketPipeline:
    def __init__(self):
        self._lock = threading.Lock()
        self._refresh_lock = threading.Lock()
        self._analyzer = CompanyAnalyzer()
        self._scorer = StockScorer()
        self._run_config = {"universe": DEFAULT_UNIVERSE, "maxTickers": MAX_TICKERS}
        self._state: Dict[str, Any] = {
            "status": "idle",
            "updatedAt": None,
            "startedAt": None,
            "universe": DEFAULT_UNIVERSE,
            "universeLabel": UNIVERSE_PRESETS.get(DEFAULT_UNIVERSE, {}).get("label", DEFAULT_UNIVERSE),
            "maxTickers": MAX_TICKERS,
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
                "availableUniverses": [
                    {"id": k, "label": v["label"], "defaultMax": v["defaultMax"]}
                    for k, v in UNIVERSE_PRESETS.items()
                ],
            }

    def results(
        self,
        *,
        exchange: Optional[str] = None,
        min_score: Optional[float] = None,
        sort: str = "score",
        limit: int = 500,
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

        if sort == "ticker":
            items.sort(key=lambda x: (x.get("ticker") or ""))
        else:
            items.sort(key=lambda x: (x.get("compositeScore") or 0), reverse=True)

        return {
            "updatedAt": self._state.get("updatedAt"),
            "status": self._state.get("status"),
            "stale": self._is_stale(),
            "universe": self._state.get("universe"),
            "universeLabel": self._state.get("universeLabel"),
            "maxTickers": self._state.get("maxTickers"),
            "years": self._state.get("years", 5),
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

    def refresh_async(
        self,
        force: bool = False,
        *,
        max_tickers: Optional[int] = None,
        universe: Optional[str] = None,
    ) -> Dict[str, Any]:
        if max_tickers is not None:
            self._run_config["maxTickers"] = min(max(max_tickers, 10), 500)
        if universe is not None and universe in UNIVERSE_PRESETS:
            self._run_config["universe"] = universe

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

        max_tickers = self._run_config.get("maxTickers", MAX_TICKERS)
        universe = self._run_config.get("universe", DEFAULT_UNIVERSE)
        preset = UNIVERSE_PRESETS.get(universe, UNIVERSE_PRESETS["sp500"])

        try:
            with self._lock:
                if not force and self._state.get("status") == "running":
                    return self.status()
                self._state["status"] = "running"
                self._state["startedAt"] = _now_iso()
                self._state["error"] = None
                self._state["universe"] = universe
                self._state["universeLabel"] = preset["label"]
                self._state["maxTickers"] = max_tickers

            universe_entries = self._resolve_universe(universe, max_tickers)
            years = 5
            thresholds = ThresholdManager.DEFAULT_THRESHOLDS
            scored_items: List[Dict[str, Any]] = []
            errors = 0

            for entry in universe_entries:
                ticker = entry["value"]
                try:
                    import yfinance as yf

                    t = yf.Ticker(ticker)
                    info = getattr(t, "info", {}) or {}
                    metrics = self._analyzer._extract_all_metrics(t, years)
                    score = self._scorer.score(metrics, thresholds, years)
                    match = find_company(ticker, load_tickers(max_count=10000))
                    ex = entry.get("exchange") or (match.get("exchange") if match else preset["exchange"])

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
                "universe": universe,
                "universeLabel": preset["label"],
                "maxTickers": max_tickers,
                "years": years,
                "thresholds": thresholds,
                "items": scored_items,
                "stats": {
                    "total": len(universe_entries),
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

    def _resolve_universe(self, universe: str, max_tickers: int) -> List[Dict[str, str]]:
        preset = UNIVERSE_PRESETS.get(universe, UNIVERSE_PRESETS["sp500"])

        if preset.get("index"):
            items = load_index_constituents(
                preset["index"],
                exchange_id=preset["exchange"],
                max_count=max_tickers,
            )
            if items:
                return items

        # Fallback: NASDAQ / NYSE symbol directory (alphabetical slice — less ideal)
        return load_tickers(
            include_exchanges=[preset["exchange"]],
            max_count=max_tickers,
        )

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
