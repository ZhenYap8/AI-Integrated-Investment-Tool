#!/usr/bin/env python3
import os, sys, json, argparse, datetime as dt
from typing import Any

# Ensure project root on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import requests  # noqa: E402

# Import after path fix
from IBBack.services.proscons import analyze_proscons_ai_only  # noqa: E402


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Run AI pros/cons and detect OpenAI API usage")
    ap.add_argument("ticker", help="Ticker symbol, e.g., AAPL")
    ap.add_argument("--max_items", type=int, default=8)
    ap.add_argument("--years", type=int, default=5)
    ap.add_argument("--period", default=None)
    ap.add_argument("--openai_base", default=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"))
    args = ap.parse_args(argv)

    # Wrap requests.post to count OpenAI chat/completions calls
    post_orig = requests.post
    call_count = {"total": 0, "openai": 0, "urls": []}

    def post_wrap(url: str, *p: Any, **kw: Any):
        call_count["total"] += 1
        call_count["urls"].append(url)
        if url.startswith(args.openai_base.rstrip("/") + "/chat/completions"):
            call_count["openai"] += 1
        return post_orig(url, *p, **kw)

    requests.post = post_wrap  # type: ignore

    summary = {
        "ticker": args.ticker,
        "timestamp": dt.datetime.utcnow().isoformat() + "Z",
        "env": {
            "OPENAI_API_KEY_set": bool(os.getenv("OPENAI_API_KEY")),
            "OPENAI_API_BASE": os.getenv("OPENAI_API_BASE", ""),
            "OPENAI_MODEL": os.getenv("OPENAI_MODEL", ""),
        },
        "openai_calls": 0,
        "findings": 0,
        "pros": 0,
        "cons": 0,
        "sample_evidence": [],
    }

    try:
        resp = analyze_proscons_ai_only(args.ticker, max_items=args.max_items, period=args.period, years=args.years)
        # Count
        f = getattr(resp, "findings", []) or []
        pros = [x for x in f if getattr(x, "direction", "") == "pro"]
        cons = [x for x in f if getattr(x, "direction", "") == "con"]
        summary["findings"] = len(f)
        summary["pros"] = len(pros)
        summary["cons"] = len(cons)
        # Sample evidence URLs
        urls = []
        for x in f[:6]:
            for e in getattr(x, "evidence", [])[:1]:
                u = getattr(e, "url", None)
                if u:
                    urls.append(u)
        summary["sample_evidence"] = urls
    except Exception as ex:
        summary["error"] = str(ex)
    finally:
        summary["openai_calls"] = call_count["openai"]
        # Restore
        requests.post = post_orig  # type: ignore

    print(json.dumps(summary, indent=2))
    # Exit nonzero if no findings and no OpenAI calls (helps CI)
    if summary.get("findings", 0) == 0 and summary.get("openai_calls", 0) == 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
