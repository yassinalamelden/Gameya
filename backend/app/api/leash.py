"""Leash REST router. Person 1 mounts it, calls register_leash_errors and overrides the deps."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.orm import Session
from ulid import ULID

from ..leash import LeashError
from ..leash.policy import get_active_policy, save_policy
from ..schemas.contracts import LeashErrorCode, LeashPolicy, LeashPreset, LeashThresholds

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


DbDep = Annotated[Session, Depends(get_db)]
ActorDep = Annotated[Actor, Depends(get_actor)]


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


def _require_organiser(actor: Actor, circle_id: str) -> None:
    if circle_id not in actor.organiser_of:
        raise LeashError(
            LeashErrorCode.ORGANISER_ONLY,
            "Only the circle organiser can do this.",
            {"circle_id": circle_id},
        )


class _PolicyPayload(BaseModel):
    """PUT body: a LeashPolicy minus the server-controlled circle_id and version."""

    preset: LeashPreset = "STANDARD"
    thresholds: LeashThresholds = Field(default_factory=LeashThresholds)
    no_auto_chase_member_ids: list[str] = Field(default_factory=list)


def _invalid_policy(errors: list[dict[str, Any]]) -> LeashError:
    # The envelope allows details to be a list; LeashError types it as a dict, so cast.
    return LeashError(
        LeashErrorCode.LEASH_POLICY_INVALID,
        "The Leash policy is invalid.",
        cast("dict[str, Any]", errors),
    )


@router.get("/circles/{cid}/leash/policy", response_model=LeashPolicy)
def get_policy(cid: str, db: DbDep, _actor: ActorDep) -> LeashPolicy:
    policy = get_active_policy(db, cid)
    db.commit()  # persist a lazily created v1
    return policy


@router.put("/circles/{cid}/leash/policy", response_model=LeashPolicy)
async def put_policy(
    cid: str,
    request: Request,
    db: DbDep,
    actor: ActorDep,
) -> LeashPolicy:
    _require_organiser(actor, cid)
    try:
        raw = await request.json()
    except ValueError as exc:
        raise _invalid_policy([{"loc": [], "msg": "Request body is not valid JSON."}]) from exc
    try:
        payload = _PolicyPayload.model_validate(raw)
    except ValidationError as exc:
        raise _invalid_policy(
            [{"loc": list(e["loc"]), "msg": e["msg"]} for e in exc.errors()]
        ) from exc
    policy = save_policy(
        db, cid, payload.preset, payload.thresholds, payload.no_auto_chase_member_ids
    )
    db.commit()
    return policy
