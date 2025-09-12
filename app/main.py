from fastapi import FastAPI
from app.api.health import router as health_router
from app.api.routes.v1 import secure as secure_v1

def create_app() -> FastAPI:
    app = FastAPI(
        title="Chatbot",
        version="0.1.0",
        description="Production-shaped chatbot API. Minimal endpoints for v0.1.",
    )
    app.include_router(health_router, tags= ['health'])
    app.include_router(secure_v1.router, prefix = "/api/v1", tags= ['secure'])
    return app

app = create_app()
