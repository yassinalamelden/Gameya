"""Leash REST router. Person 1 mounts it, calls register_leash_errors and overrides the deps."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from ulid import ULID

from ..leash import LeashError

router = APIRouter(prefix="/api/v1", tags=["leash"])


@dataclass(frozen=True)
class Actor:
    user_id: str
    organiser_of: frozenset[str]


def get_db() -> Iterator[Session]:
    """Placeholder: Person 1 overrides this with the real session dependency."""
    raise NotImplementedError("get_db must be overridden when mounting the Leash router")


def get_actor() -> Actor:
    """Placeholder: Person 1 overrides this with the authenticated actor."""
    raise NotImplementedError("get_actor must be overridden when mounting the Leash router")


def _request_id(request: Request) -> str:
    return request.headers.get("X-Request-ID") or f"req_{ULID()}"


def _envelope(request: Request, exc: LeashError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.http_status,
        content={
            "error": {
                "code": exc.code.value,
                "message": exc.message,
                "details": exc.details,
                "request_id": _request_id(request),
            }
        },
    )


def register_leash_errors(app: FastAPI) -> None:
    async def _handler(request: Request, exc: Exception) -> JSONResponse:
        assert isinstance(exc, LeashError)
        return _envelope(request, exc)

    app.add_exception_handler(LeashError, _handler)
