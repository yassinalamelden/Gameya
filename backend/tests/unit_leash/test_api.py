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


def test_get_policy_default_v1(db: Session) -> None:
    r = make_client(db, MEMBER).get("/api/v1/circles/c1/leash/policy")
    assert r.status_code == 200
    body = r.json()
    assert body["circle_id"] == "c1" and body["version"] == 1 and body["preset"] == "STANDARD"
    assert body["thresholds"]["reminder_min_gap_hours"] == 48
    assert body["no_auto_chase_member_ids"] == []
    # Lazily created v1 was committed, so it survives a rollback.
    db.rollback()
    assert make_client(db, MEMBER).get("/api/v1/circles/c1/leash/policy").json()["version"] == 1


def test_put_policy_bumps_version(db: Session) -> None:
    client = make_client(db, ORGANISER)
    client.get("/api/v1/circles/c1/leash/policy")
    r = client.put(
        "/api/v1/circles/c1/leash/policy",
        json={
            "circle_id": "ignored",
            "version": 99,
            "preset": "STRICT",
            "thresholds": {"reminder_min_gap_hours": 72},
            "no_auto_chase_member_ids": ["m_x"],
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["version"] == 2 and body["circle_id"] == "c1" and body["preset"] == "STRICT"
    assert body["thresholds"]["reminder_min_gap_hours"] == 72
    assert body["no_auto_chase_member_ids"] == ["m_x"]
    db.rollback()
    assert client.get("/api/v1/circles/c1/leash/policy").json()["version"] == 2


def test_put_policy_member_401_organiser_only(db: Session) -> None:
    r = make_client(db, MEMBER).put("/api/v1/circles/c1/leash/policy", json={"preset": "STRICT"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "ORGANISER_ONLY"


def test_put_policy_organiser_of_other_circle_401(db: Session) -> None:
    other = Actor(user_id="o2", organiser_of=frozenset({"c2"}))
    r = make_client(db, other).put("/api/v1/circles/c1/leash/policy", json={})
    assert r.status_code == 401


def test_put_policy_gap_11h_422_policy_invalid(db: Session) -> None:
    r = make_client(db, ORGANISER).put(
        "/api/v1/circles/c1/leash/policy",
        json={"preset": "STANDARD", "thresholds": {"reminder_min_gap_hours": 11}},
    )
    assert r.status_code == 422
    err = r.json()["error"]
    assert err["code"] == "LEASH_POLICY_INVALID"
    assert err["details"][0]["loc"] == ["thresholds", "reminder_min_gap_hours"]
    assert isinstance(err["details"][0]["msg"], str)


def test_put_policy_malformed_json_422(db: Session) -> None:
    r = make_client(db, ORGANISER).put(
        "/api/v1/circles/c1/leash/policy",
        content=b"{nope",
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 422 and r.json()["error"]["code"] == "LEASH_POLICY_INVALID"
