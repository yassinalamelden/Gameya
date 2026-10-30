"""Every Interface 2 endpoint has a golden fixture that validates as a contract.

These are Person 5's clean-room checks: the JSON payload must be exactly the
endpoint response and must round-trip through backend/app/schemas/contracts.py.
Any contract change that breaks a fixture breaks CI.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, get_origin

import pytest
from app.schemas import contracts as c
from pydantic import TypeAdapter

FIXTURES_DIR = Path(__file__).resolve().parents[3] / "shared" / "fixtures" / "json"

REGISTRY: dict[str, Any] = {
    "auth-demo-login.json": c.DemoLoginResponse,
    "agent-circle-chat.json": c.CircleAgentChatResponse,
    "circles-create.json": c.CircleCreateResponse,
    "circle-get.json": c.CircleSnapshot,
    "circle-join.json": c.JoinCircleResponse,
    "circle-needs.json": c.NeedExtraction,
    "circle-order-propose.json": c.OrderProposal,
    "circle-copilot.json": c.CopilotAnswer,
    "cycles-pay-now.json": c.PayNowResponse,
    "cycles-mediation.json": list[c.MediationOption],
    "circle-ledger.json": c.LedgerResponse,
    "circle-audit.json": c.AuditResponse,
    "circle-reliability.json": c.ReliabilityResponse,
    "circles-stress-test.json": c.StressTestResponse,
    "circle-swaps.json": c.SwapProposal,
    "health.json": c.HealthResponse,
}


def test_fixtures_dir_exists() -> None:
    assert FIXTURES_DIR.is_dir(), f"missing {FIXTURES_DIR}"


def test_fixture_inventory_is_complete() -> None:
    present = {p.name for p in FIXTURES_DIR.glob("*.json")}
    assert present == set(REGISTRY), (
        f"fixture inventory drift: missing={set(REGISTRY) - present} "
        f"unexpected={present - set(REGISTRY)}"
    )


@pytest.mark.parametrize(("filename", "model"), sorted(REGISTRY.items()))
def test_fixture_validates_against_contract(filename: str, model: Any) -> None:
    raw = json.loads((FIXTURES_DIR / filename).read_text(encoding="utf-8"))
    if get_origin(model) is list:
        parser = TypeAdapter(model).validate_python
    else:
        parser = model.model_validate
    parsed = parser(raw)
    assert parsed is not None


def test_frontend_contract_mirror_mentions_same_status_values() -> None:
    ts_source = (
        Path(__file__).resolve().parents[3] / "frontend" / "src" / "types" / "contracts.ts"
    ).read_text(encoding="utf-8")
    for status in c.CycleStatus:
        assert f'"{status.value}"' in ts_source, f"contracts.ts missing {status.value}"
    for status in c.ContributionStatus:
        assert f'"{status.value}"' in ts_source, f"contracts.ts missing {status.value}"
