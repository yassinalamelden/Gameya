"""Smoke tests: the app boots, the sandbox guard holds, and fixtures match the canonical contract."""

import json
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import Settings
from app.main import app
from app.schemas.contracts import CircleSpec, LedgerRow

FIXTURES = Path(__file__).resolve().parents[3] / "shared" / "fixtures" / "json"


def test_health() -> None:
    r = TestClient(app).get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_live_paypal_url_is_refused() -> None:
    with pytest.raises(ValidationError):
        Settings(paypal_api_base_url="https://api-m.paypal.com")


def test_money_rejects_float_and_rounds_half_up() -> None:
    with pytest.raises(ValidationError):
        CircleSpec(name="x", contribution_amount=100.0, cycle_unit="MONTH", size_n=6, start_date="2026-11-01")
    spec = CircleSpec(
        name="x", contribution_amount="100.005", cycle_unit="MONTH", size_n=6, start_date="2026-11-01"
    )
    assert spec.contribution_amount == Decimal("100.01")


def test_golden_circle_fixture_matches_contract() -> None:
    data = json.loads((FIXTURES / "golden_circle.json").read_text(encoding="utf-8"))
    CircleSpec.model_validate(data["spec"])
    rows = [LedgerRow.model_validate(r) for r in data["ledger"]]
    assert sum(r.amount for r in rows if r.cycle_index == 1) == Decimal("600.00")
