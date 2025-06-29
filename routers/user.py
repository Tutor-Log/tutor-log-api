from fastapi import APIRouter, FastAPI

base_router = APIRouter()

# Health API
@base_router.get("/health")
def health_check():
    return {"status": "ok"}
