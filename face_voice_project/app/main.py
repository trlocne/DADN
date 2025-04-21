from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.endpoints import face, voice, user, system
from .core.config import settings

app = FastAPI(title="Face Voice Control API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(face.router, prefix="/face", tags=["face"])
app.include_router(voice.router, prefix="/voice", tags=["voice"])
app.include_router(user.router, prefix="/user", tags=["user"])
app.include_router(system.router, prefix="/system", tags=["system"])

@app.get("/")
async def root():
    return {"message": "Welcome to Face Voice Control API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )