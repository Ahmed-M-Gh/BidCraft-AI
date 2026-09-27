from fastapi import APIRouter, Depends
from src.config import get_settings, Settings

base_route = APIRouter(
    prefix="/api/v1.0",
    tags=["Base-settings"]
)

@base_route.get("/")
async def get_info(app_info:Settings = Depends(get_settings)):
    return {
        "Name" : app_info.APP_NAME, 
        "Version" : app_info.APP_VERSION, 
    }