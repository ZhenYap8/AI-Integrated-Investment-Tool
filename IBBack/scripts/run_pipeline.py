#!/usr/bin/env python3
"""Run the market screening pipeline locally."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.pipeline import get_pipeline  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run NASDAQ/Yahoo screening pipeline")
    parser.add_argument("--force", action="store_true", help="Force refresh even if cache is fresh")
    parser.add_argument("--json", action="store_true", help="Print full JSON output")
    args = parser.parse_args()

    pipeline = get_pipeline()
    result = pipeline.refresh(force=args.force)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        status = pipeline.status()
        print(f"Status: {status.get('status')}")
        print(f"Updated: {status.get('updatedAt')}")
        print(f"Scored: {status.get('stats', {}).get('scored', 0)} stocks")
        for item in (status.get("items") or [])[:10]:
            print(f"  {item.get('rank'):>2}. {item.get('ticker')}  score={item.get('compositeScore')}  grade={item.get('grade')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
