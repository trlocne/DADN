from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List
from ...services.user_service import UserService
from ...services.train_service import TrainService

router = APIRouter()
user_service = UserService()
train_service = TrainService()

@router.get("/list")
async def get_users():
    try:
        users = user_service.get_users()
        return {"users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-faces")
async def upload_faces(name: str, files: List[UploadFile] = File(...)):
    try:
        if len(files) != 5:
            raise HTTPException(status_code=400, detail="Exactly 5 images are required")
        
        saved_files = []
        for file in files:
            if not file.content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail=f"File {file.filename} is not an image")
            
            content = await file.read()
            filepath = user_service.save_user_image(name, content, file.filename)
            saved_files.append(filepath)
        
        return {
            "message": f"Successfully saved {len(saved_files)} images for {name}",
            "saved_files": saved_files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete/{name}")
async def delete_user(name: str):
    try:
        if user_service.delete_user(name):
            if user_service.get_users():
                train_service.train_model()
            return {"message": f"Successfully deleted user {name}"}
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/capture-photos/{name}")
async def capture_photos_endpoint(name: str):
    try:
        user_service.capture_photos(name)
        return {"message": f"Photo capture completed. Photos saved for {name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/clear")
async def clear_users():
    try:
        if user_service.clear_all_users():
            return {"message": "Successfully cleared all user data"}
        raise HTTPException(status_code=500, detail="Failed to clear user data")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))