"""Mula API application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai_assistant.routes import router as assistant_router
from app.financial_planning.routes import router as financial_router
from app.transactions.routes import router as transactions_router
from app.users.routes import router as auth_router
from core.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Local development stays zero-config. Production schema changes should be
    # applied explicitly before deploying the API.
    if settings.app_env.lower() == "development":
        from core.database import create_tables

        await create_tables()
    yield


app = FastAPI(
    title="Mula API",
    description="Personal finance API for Mula.",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(transactions_router, prefix="/api/v1/transactions")
app.include_router(financial_router, prefix="/api/v1/financial")
app.include_router(assistant_router, prefix="/api/v1/assistant")


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "mula-api"}
