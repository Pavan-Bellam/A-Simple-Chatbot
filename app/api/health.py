from fastapi import APIRouter
from app.schemas.health import HealthResponse
from datetime import datetime,  timezone
router = APIRouter()

@router.get(
    '/health',
    summary = 'liveness check',
    description= "returns 200 when the app is alive",
    response_model= HealthResponse
)
def health():
    return HealthResponse(status='ok', service='app', time=datetime.now(timezone.utc))