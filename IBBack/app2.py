from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.requests import Request
from typing import Optional

from routers.api2 import router
from data.universe_extension import load_tickers, exchange_label

app = FastAPI(title="Investment Agent Backend", version="0.3.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    msg = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": msg, "details": msg})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error", "details": str(exc)})


@app.get("/")
async def root():
    return {"message": "Investment Agent Backend", "status": "running", "version": "0.3.0"}


app.include_router(router)


@app.get("/api/tickers")
async def api_tickers(
    max_count: int = Query(2000, ge=1, le=10000),
    exchange: Optional[str] = Query(None),
):
    try:
        include = [exchange] if exchange else None
        tickers = load_tickers(include_exchanges=include, max_count=max_count)
        return [
            {
                "label": t.get("label"),
                "value": t.get("value"),
                "exchange": t.get("exchange"),
                "exchangeLabel": exchange_label(t.get("exchange")),
                "type": t.get("type", "company"),
            }
            for t in tickers
        ]
    except Exception as e:
        print(f"[api_tickers] error: {e}")
        return []
