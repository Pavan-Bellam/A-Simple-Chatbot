from fastapi import FastAPI
from app.api.health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Chatbot",
        version="0.1.0",
        description="Production-shaped chatbot API. Minimal endpoints for v0.1.",
    )
    app.include_router(health_router)
    return app
app = create_app()
