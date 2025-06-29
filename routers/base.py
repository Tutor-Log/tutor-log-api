from fastapi import APIRouter

base = APIRouter()

# Health API
@base.get("/health")
def health_check():
    return {"status": "ok"}
