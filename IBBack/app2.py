from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.requests import Request

from routers.api2 import router

app = FastAPI(title="Investment Agent Backend Scaffold", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure errors expose both `detail` and `details` for FE compatibility
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    msg = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": msg, "details": msg})

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error", "details": str(exc)})

# Add root route
@app.get("/")
async def root():
    return {"message": "Investment Agent Backend", "status": "running"}

# Mount API routes
app.include_router(router)
