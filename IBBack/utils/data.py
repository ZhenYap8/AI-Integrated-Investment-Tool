import requests
import csv
from typing import List, Dict

DEMO_INDUSTRIES = [
    {"label": "Robotics & Automation", "value": "Robotics", "type": "industry"},
    {"label": "Semiconductors (AI)", "value": "Semiconductors", "type": "industry"},
]

# Industry → demo constituents (you can expand later)
INDUSTRY_MAP = {
    "Robotics": ["ABB", "FANUY", "ROK", "ISRG", "TER", "CGNX", "IRBT"],
    "Semiconductors": ["NVDA"],
}

def load_us_tickers() -> List[Dict[str, str]]:
    """
    Load US tickers from NASDAQ and other exchanges.

    Returns:
        A list of dictionaries containing ticker information with the format:
        [{"label": "Company Name (Symbol)", "value": "Symbol", "type": "company"}]
    """
    tickers: List[Dict[str, str]] = []
    endpoints = [
        {
            "url": "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt",
            "symbol_key": "Symbol",
            "name_key": "Security Name",
        },
        {
            "url": "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt",
            "symbol_key": "ACT Symbol",
            "name_key": "Security Name",
        },
    ]

    for endpoint in endpoints:
        try:
            # Fetch data from the endpoint
            resp = requests.get(endpoint["url"], timeout=10)
            resp.raise_for_status()

            # Parse the response
            lines = [
                line for line in resp.text.splitlines()
                if line and "File Creation Time" not in line
            ]
            reader = csv.DictReader(lines, delimiter="|")
            for row in reader:
                symbol = (row.get(endpoint["symbol_key"]) or "").strip()
                name = (row.get(endpoint["name_key"]) or "").strip()

                # Skip invalid or header rows
                if not symbol or not name or symbol in {"Symbol", "ACT Symbol"}:
                    continue

                tickers.append({
                    "label": f"{name} ({symbol})",
                    "value": symbol,
                    "type": "company",
                })
        except Exception as e:
            # Log the error (optional) and continue with the next endpoint
            print(f"Error fetching tickers from {endpoint['url']}: {e}")
            continue

    # Remove duplicates
    seen = set()
    deduped = []
    for ticker in tickers:
        if ticker["value"] not in seen:
            seen.add(ticker["value"])
            deduped.append(ticker)

    # Fallback demo set if no tickers were loaded
    if not deduped:
        deduped = [
            {"label": "NVIDIA (NVDA)", "value": "NVDA", "type": "company"},
            {"label": "ABB Ltd (ABB)", "value": "ABB", "type": "company"},
            {"label": "Fanuc (FANUY)", "value": "FANUY", "type": "company"},
        ]

    return deduped

ALL_US_COMPANIES: List[Dict[str, str]] = load_us_tickers()
