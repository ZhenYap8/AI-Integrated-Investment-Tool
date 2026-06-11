"""
Global ticker universe loader.

Aggregates US listings (NASDAQ Trader), optional CSV exchange files,
curated international symbols, and pytickersymbols index constituents.
"""
from __future__ import annotations

import csv
import json
import os
import re
import time
from typing import Dict, List, Optional

try:
    import requests  # type: ignore
except Exception:
    requests = None

# --------------------------------------------------------------------------- #
# Demo industries
# --------------------------------------------------------------------------- #
DEMO_INDUSTRIES = [
    {"label": "Robotics & Automation", "value": "Robotics", "type": "industry"},
    {"label": "Semiconductors (AI)", "value": "Semiconductors", "type": "industry"},
]
INDUSTRY_MAP = {
    "Robotics": ["ABB", "FANUY", "ROK", "ISRG", "TER", "CGNX", "IRBT"],
    "Semiconductors": ["NVDA", "AMD", "INTC", "TSM", "ASML", "AVGO"],
}

EXCHANGE_LABELS: Dict[str, str] = {
    "US_NASDAQ": "NASDAQ",
    "US_OTHER": "NYSE/AMEX",
    "TSX": "TSX",
    "LSE": "LSE",
    "ASX": "ASX",
    "HKEX": "HKEX",
    "TSE_JP": "TSE",
    "GLOBAL": "Global",
    "INDEX": "Index",
}

EXCHANGE_SOURCES = [
    {
        "id": "US_NASDAQ",
        "url": "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt",
        "local_file": False,
        "delimiter": "|",
        "symbol_key": "Symbol",
        "name_key": "Security Name",
        "suffix": "",
    },
    {
        "id": "US_OTHER",
        "url": "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt",
        "local_file": False,
        "delimiter": "|",
        "symbol_key": "ACT Symbol",
        "name_key": "Security Name",
        "suffix": "",
    },
    {
        "id": "TSX",
        "url": os.getenv("TSX_LIST_CSV"),
        "local_file": True,
        "delimiter": ",",
        "symbol_key": "Symbol",
        "name_key": "Name",
        "suffix": ".TO",
    },
    {
        "id": "LSE",
        "url": os.getenv("LSE_LIST_CSV"),
        "local_file": True,
        "delimiter": ",",
        "symbol_key": "Symbol",
        "name_key": "Name",
        "suffix": ".L",
    },
    {
        "id": "ASX",
        "url": os.getenv("ASX_LIST_CSV"),
        "local_file": True,
        "delimiter": ",",
        "symbol_key": "Symbol",
        "name_key": "Name",
        "suffix": ".AX",
    },
    {
        "id": "HKEX",
        "url": os.getenv("HK_LIST_CSV"),
        "local_file": True,
        "delimiter": ",",
        "symbol_key": "Symbol",
        "name_key": "Name",
        "suffix": ".HK",
    },
    {
        "id": "TSE_JP",
        "url": os.getenv("JP_LIST_CSV"),
        "local_file": True,
        "delimiter": ",",
        "symbol_key": "Symbol",
        "name_key": "Name",
        "suffix": ".T",
    },
]

# Curated international listings (yfinance-compatible symbols)
CURATED_GLOBAL = [
    ("ASML.AS", "ASML Holding", "EURONEXT"),
    ("SAP.DE", "SAP SE", "XETRA"),
    ("SIE.DE", "Siemens AG", "XETRA"),
    ("BP.L", "BP plc", "LSE"),
    ("SHEL.L", "Shell plc", "LSE"),
    ("HSBA.L", "HSBC Holdings", "LSE"),
    ("AZN.L", "AstraZeneca", "LSE"),
    ("ULVR.L", "Unilever", "LSE"),
    ("RIO.L", "Rio Tinto", "LSE"),
    ("BHP.AX", "BHP Group", "ASX"),
    ("CBA.AX", "Commonwealth Bank", "ASX"),
    ("CSL.AX", "CSL Limited", "ASX"),
    ("SHOP.TO", "Shopify", "TSX"),
    ("RY.TO", "Royal Bank of Canada", "TSX"),
    ("TD.TO", "Toronto-Dominion Bank", "TSX"),
    ("0700.HK", "Tencent Holdings", "HKEX"),
    ("9988.HK", "Alibaba Group", "HKEX"),
    ("2318.HK", "Ping An Insurance", "HKEX"),
    ("7203.T", "Toyota Motor", "TSE"),
    ("6758.T", "Sony Group", "TSE"),
    ("6861.T", "Keyence", "TSE"),
    ("TSM", "Taiwan Semiconductor", "US_ADR"),
    ("NVO", "Novo Nordisk ADR", "US_ADR"),
    ("TM", "Toyota Motor ADR", "US_ADR"),
    ("SONY", "Sony Group ADR", "US_ADR"),
    ("BABA", "Alibaba ADR", "US_ADR"),
    ("ABB", "ABB Ltd", "US_ADR"),
    ("FANUY", "Fanuc Corp", "US_OTC"),
]

PYTICKER_INDICES = [
    ("S&P 500", "US_OTHER", ""),
    ("DOW Jones", "US_OTHER", ""),
    ("FTSE 100", "LSE", ".L"),
    ("DAX", "GLOBAL", ".DE"),
    ("CAC 40", "GLOBAL", ".PA"),
    ("Nikkei 225", "TSE_JP", ".T"),
    ("S&P/TSX Composite", "TSX", ".TO"),
    ("ASX 200", "ASX", ".AX"),
    ("Hang Seng", "HKEX", ".HK"),
]

CACHE_FILE = "/tmp/global_tickers_cache.json"
CACHE_TTL_SEC = 12 * 3600
_CACHE: Optional[List[Dict[str, str]]] = None

_TICKER_RE = re.compile(r"^[A-Z0-9][A-Z0-9.\-]{0,11}$", re.I)


def demo_companies() -> List[Dict[str, str]]:
    return [
        {"label": "NVIDIA (NVDA)", "value": "NVDA", "exchange": "US_NASDAQ", "type": "company"},
        {"label": "ABB Ltd (ABB)", "value": "ABB", "exchange": "US_OTHER", "type": "company"},
        {"label": "ASML Holding (ASML.AS)", "value": "ASML.AS", "exchange": "GLOBAL", "type": "company"},
        {"label": "BP plc (BP.L)", "value": "BP.L", "exchange": "LSE", "type": "company"},
    ]


def exchange_label(exchange_id: Optional[str]) -> str:
    if not exchange_id:
        return "Unknown"
    return EXCHANGE_LABELS.get(exchange_id, exchange_id.replace("_", " "))


def looks_like_ticker(val: str) -> bool:
    """Heuristic: ticker symbols are short, no spaces, alphanumeric + dot/dash."""
    v = (val or "").strip()
    if not v or " " in v or len(v) > 12:
        return False
    # Exclude industry names
    for ind in DEMO_INDUSTRIES:
        if v.lower() == ind["value"].lower() or v.lower() == ind["label"].lower():
            return False
    if not _TICKER_RE.match(v):
        return False
    # International tickers often have suffixes or digits (BP.L, 0700.HK)
    if "." in v or any(c.isdigit() for c in v):
        return True
    # US tickers: uppercase letters, typically 1–5 chars
    return v.isupper() and v.isalpha() and 1 <= len(v) <= 6


def normalize_ticker(val: str) -> str:
    return (val or "").strip().upper()


def _load_cache_file() -> Optional[List[Dict[str, str]]]:
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        if time.time() - os.path.getmtime(CACHE_FILE) > CACHE_TTL_SEC:
            return None
        with open(CACHE_FILE, "r") as fh:
            data = json.load(fh)
        if isinstance(data, list) and data:
            return data
    except Exception:
        return None
    return None


def _store_cache_file(data: List[Dict[str, str]]) -> None:
    try:
        with open(CACHE_FILE, "w") as fh:
            json.dump(data, fh)
    except Exception:
        pass


def _fetch_source(src: Dict) -> List[Dict[str, str]]:
    results: List[Dict[str, str]] = []
    url = src.get("url")
    if not url:
        return results

    try:
        if src.get("local_file"):
            if not os.path.exists(url):
                return results
            with open(url, "r", encoding="utf-8", errors="ignore") as fh:
                lines = fh.read().splitlines()
        else:
            if requests is None:
                return results
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            lines = resp.text.splitlines()

        lines = [ln for ln in lines if ln and "File Creation Time" not in ln]
        reader = csv.DictReader(lines, delimiter=src.get("delimiter", ","))

        for row in reader:
            sym_key = src["symbol_key"]
            name_key = src["name_key"]
            symbol = (row.get(sym_key) or "").strip()
            name = (row.get(name_key) or "").strip()
            if not symbol or not name:
                continue
            if symbol in {"Symbol", "ACT Symbol"}:
                continue
            if row.get("Test Issue", "").upper() == "Y":
                continue
            if row.get("ETF", "").upper() == "Y":
                continue
            if symbol.endswith(("W", ".W", "P")):
                continue

            full_symbol = symbol + src.get("suffix", "")
            results.append({
                "label": f"{name} ({full_symbol})",
                "value": full_symbol,
                "exchange": src["id"],
                "type": "company",
            })
    except Exception:
        return []

    return results


def _load_curated_global() -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for symbol, name, exchange in CURATED_GLOBAL:
        out.append({
            "label": f"{name} ({symbol})",
            "value": symbol,
            "exchange": exchange if exchange in EXCHANGE_LABELS else "GLOBAL",
            "type": "company",
        })
    return out


def _load_pytickers() -> List[Dict[str, str]]:
    try:
        import pytickersymbols  # type: ignore
    except Exception:
        return []

    pts = pytickersymbols.PyTickerSymbols()
    out: List[Dict[str, str]] = []
    seen: set[str] = set()

    for index_name, exchange_id, suffix in PYTICKER_INDICES:
        try:
            stocks = pts.get_stocks_by_index(index_name) or []
        except Exception:
            continue
        for stock in stocks:
            try:
                name = stock.get("name") or ""
                symbols = stock.get("symbols") or []
                yahoo = None
                for sym in symbols:
                    if sym.get("symbol"):
                        yahoo = sym["symbol"]
                        break
                if not yahoo:
                    continue
                if suffix and not yahoo.endswith(suffix) and "." not in yahoo:
                    yahoo = yahoo + suffix
                yahoo = yahoo.upper()
                if yahoo in seen:
                    continue
                seen.add(yahoo)
                out.append({
                    "label": f"{name} ({yahoo})",
                    "value": yahoo,
                    "exchange": exchange_id,
                    "type": "company",
                })
            except Exception:
                continue
    return out


def _dedupe(items: List[Dict[str, str]]) -> List[Dict[str, str]]:
    seen: set[str] = set()
    deduped: List[Dict[str, str]] = []
    for item in items:
        v = item["value"]
        if v in seen:
            continue
        seen.add(v)
        deduped.append(item)
    return deduped


def load_tickers(
    include_exchanges: Optional[List[str]] = None,
    max_count: Optional[int] = None,
    include_pytickers: bool = True,
) -> List[Dict[str, str]]:
    global _CACHE
    if _CACHE is None:
        cached = _load_cache_file()
        if cached:
            _CACHE = cached
        else:
            collected: List[Dict[str, str]] = []
            for src in EXCHANGE_SOURCES:
                collected.extend(_fetch_source(src))
            collected.extend(_load_curated_global())
            if include_pytickers:
                collected.extend(_load_pytickers())
            _CACHE = _dedupe(collected) or demo_companies()
            _store_cache_file(_CACHE)

    data = _CACHE
    if include_exchanges:
        data = [d for d in data if d.get("exchange") in include_exchanges]
    if max_count:
        data = data[:max_count]
    return data


def load_us_tickers() -> List[Dict[str, str]]:
    return load_tickers(include_exchanges=["US_NASDAQ", "US_OTHER"])


def find_company(query: str, tickers: Optional[List[Dict[str, str]]] = None) -> Optional[Dict[str, str]]:
    """Exact match by symbol or label."""
    val = (query or "").strip()
    if not val:
        return None
    pool = tickers or load_tickers()
    val_upper = val.upper()
    val_lower = val.lower()
    for c in pool:
        if val_upper == c["value"].upper() or val_lower == c.get("label", "").lower():
            return c
    return None


def suggest(query: str, limit: int = 8) -> List[Dict[str, str]]:
    """Substring search across industries + global tickers."""
    ql = (query or "").lower().strip()
    items = DEMO_INDUSTRIES + load_tickers()
    if not ql:
        return items[:limit]
    out: List[Dict[str, str]] = []
    for it in items:
        text = (it.get("label", "") + " " + it.get("value", "") + " " + exchange_label(it.get("exchange"))).lower()
        if ql in text:
            out.append(it)
        if len(out) >= limit:
            break
    return out


ALL_US_COMPANIES: List[Dict[str, str]] = load_us_tickers()
GLOBAL_TICKERS: List[Dict[str, str]] = load_tickers()

__all__ = [
    "DEMO_INDUSTRIES",
    "INDUSTRY_MAP",
    "EXCHANGE_LABELS",
    "load_tickers",
    "load_us_tickers",
    "find_company",
    "suggest",
    "looks_like_ticker",
    "normalize_ticker",
    "exchange_label",
    "ALL_US_COMPANIES",
    "GLOBAL_TICKERS",
]
