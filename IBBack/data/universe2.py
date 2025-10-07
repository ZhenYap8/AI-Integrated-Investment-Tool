import csv
from typing import List, Dict

# requests is optional; fall back to demo tickers if unavailable
try:
    import requests
except Exception:
    requests = None

# Demo industries (keep as-is for aggregation)
DEMO_INDUSTRIES = [
    {"label": "Robotics & Automation", "value": "Robotics", "type": "industry"},
    {"label": "Semiconductors (AI)", "value": "Semiconductors", "type": "industry"},
]

# Industry → demo constituents (you can expand later)
INDUSTRY_MAP = {
    "Robotics": ["ABB", "FANUY", "ROK", "ISRG", "TER", "CGNX", "IRBT"],
    "Semiconductors": ["NVDA"],
}


def demo_companies() -> List[Dict[str, str]]:
    return [
        {"label": "NVIDIA (NVDA)", "value": "NVDA", "type": "company"},
        {"label": "ABB Ltd (ABB)", "value": "ABB", "type": "company"},
        {"label": "Fanuc (FANUY)", "value": "FANUY", "type": "company"},
    ]


def load_us_tickers() -> List[Dict[str, str]]:
    if requests is None:
        return demo_companies()
    tickers: List[Dict[str, str]] = []
    endpoints = [
        ("https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt", "Symbol", "Security Name"),
        ("https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt", "ACT Symbol", "Security Name"),
    ]
    for url, sym_key, name_key in endpoints:
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            lines = [ln for ln in resp.text.splitlines() if ln and "File Creation Time" not in ln]
            reader = csv.DictReader(lines, delimiter='|')
            for row in reader:
                symbol = (row.get(sym_key) or "").strip()
                name = (row.get(name_key) or "").strip()
                if not symbol or not name:
                    continue
                if symbol in {"Symbol", "ACT Symbol"}:
                    continue
                tickers.append({"label": f"{name} ({symbol})", "value": symbol, "type": "company"})
        except Exception:
            continue
    # De-dup
    seen, deduped = set(), []
    for it in tickers:
        if it["value"] in seen:
            continue
        seen.add(it["value"])
        deduped.append(it)
    return deduped or demo_companies()


ALL_US_COMPANIES: List[Dict[str, str]] = load_us_tickers()
