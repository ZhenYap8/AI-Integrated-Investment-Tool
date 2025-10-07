"""
FastAPI entrypoint.
Run with either:
- uvicorn IBBack.app:app --reload --port 8000   # from repo root
- uvicorn app:app --reload --port 8000          # from IBBack/
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Robust import whether launched from repo root or IBBack/
try:
    from routers import analyze, suggest, health
except Exception:  # fallback when imported as a package
    from IBBack.routers import analyze, suggest, health

app = FastAPI(title="Investment Agent Backend", version="0.2.0")

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(analyze.router, prefix="/api")
app.include_router(suggest.router, prefix="/api")
app.include_router(health.router, prefix="/api")