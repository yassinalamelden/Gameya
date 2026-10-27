"""FastAPI entrypoint (Person 1). Routers are added under /api/v1 as lanes land."""

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings

settings = get_settings()

app = FastAPI(title="Gam'eya API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)

api = APIRouter(prefix="/api/v1")


@api.get("/health")
def health() -> dict[str, object]:
    return {"status": "ok", "demo_mode": settings.demo_mode, "paypal": settings.paypal_api_base_url}


app.include_router(api)
