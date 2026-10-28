"""REST-level tests for the Leash router, on a throwaway FastAPI app."""

import re
from collections.abc import Iterator

import pytest
from backend.app.api import leash as api
from backend.app.api.leash import Actor, get_actor, get_db, register_leash_errors
from backend.app.leash import LeashError
from backend.app.schemas.contracts import LeashErrorCode
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def make_client(db: Session, actor: Actor) -> TestClient:
    app = FastAPI()
    app.include_router(api.router)
    register_leash_errors(app)

    def _db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[get_actor] = lambda: actor
    return TestClient(app)


ORGANISER = Actor(user_id="org1", organiser_of=frozenset({"c1"}))
MEMBER = Actor(user_id="m1", organiser_of=frozenset())


def test_placeholders_raise() -> None:
    with pytest.raises(NotImplementedError):
        next(get_db())
    with pytest.raises(NotImplementedError):
        get_actor()


def test_error_envelope_uses_request_id_header(db: Session) -> None:
    client = make_client(db, ORGANISER)

    @client.app.get("/boom")  # type: ignore[attr-defined]
    def boom() -> None:
        raise LeashError(LeashErrorCode.LEASH_DISABLED, "off", {"k": 1})

    r = client.get("/boom", headers={"X-Request-ID": "abc"})
    assert r.status_code == 503
    assert r.json() == {
        "error": {
            "code": "LEASH_DISABLED",
            "message": "off",
            "details": {"k": 1},
            "request_id": "abc",
        }
    }


def test_error_envelope_generates_request_id(db: Session) -> None:
    client = make_client(db, ORGANISER)

    @client.app.get("/boom")  # type: ignore[attr-defined]
    def boom() -> None:
        raise LeashError(LeashErrorCode.ORGANISER_ONLY, "no")

    r = client.get("/boom")
    assert r.status_code == 401
    assert re.fullmatch(r"req_[0-9A-Z]{26}", r.json()["error"]["request_id"])
    assert r.json()["error"]["details"] == {}
