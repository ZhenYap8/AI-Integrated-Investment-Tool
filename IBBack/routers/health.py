from fastapi import APIRouter
import datetime as dt

router = APIRouter()

@router.get("/health")
async def health():
    return {"ok": True, "time": dt.datetime.utcnow().isoformat() + "Z"}