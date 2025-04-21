from fastapi import APIRouter, HTTPException
from ...services.face_service import FaceRecognitionFactory

router = APIRouter()

@router.get("/detect")
async def face_detect():
    try:
        face_service = FaceRecognitionFactory.create_face_recognition()
        if not face_service.initialize():
            raise HTTPException(status_code=500, detail="Failed to initialize camera")
            
        detected_name = face_service.run_detection()
        return {"message": detected_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
