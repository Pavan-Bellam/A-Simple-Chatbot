from pydantic import BaseModel
from datetime import datetime


class HealthResponse(BaseModel):
    status: str         # Current status of the service, e.g. "ok" or "ready"
    service: str        #name of the service, e.g 'redis', 'app' for the whole app
    time: datetime      # timestamp