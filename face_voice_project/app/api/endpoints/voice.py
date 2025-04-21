from fastapi import APIRouter, HTTPException
from ...services.voice_service import start_listening, stop_listening

router = APIRouter()

@router.get("/listen")
async def start():
    start_listening()
    return {"message": "Bắt đầu lắng nghe"}

@router.get("/stop_listen")
async def stop():
    stop_listening()
    return {"message": "Đã dừng lắng nghe"}