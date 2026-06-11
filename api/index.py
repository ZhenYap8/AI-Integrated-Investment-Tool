"""
Vercel serverless entrypoint — exposes the FastAPI app from IBBack.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IBBACK = ROOT / "IBBack"
if str(IBBACK) not in sys.path:
    sys.path.insert(0, str(IBBACK))

os.environ.setdefault("VERCEL", "1")

from app2 import app  # noqa: E402  (Vercel ASGI entry)

__all__ = ["app"]
