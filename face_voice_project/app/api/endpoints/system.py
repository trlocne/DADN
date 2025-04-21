from fastapi import APIRouter, HTTPException
from ...services.train_service import TrainService

router = APIRouter()
train_service = TrainService()

@router.post("/train")
async def train_model():
    try:
        if train_service.train_model():
            stats = train_service.get_training_stats()
            return {
                "message": "Training completed successfully",
                "stats": stats
            }
        raise HTTPException(status_code=500, detail="Training failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))