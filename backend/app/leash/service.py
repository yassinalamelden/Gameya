"""Leash service: build facts, evaluate rules, log the decision. Never commits."""

from __future__ import annotations

import os
from decimal import Decimal
from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..schemas.contracts import GuardAction, GuardResult, LeashDecision, LeashErrorCode
from .facts import BaseFacts, ChaseInvoiceFacts, FactsProvider, PayoutFacts
from .guard import evaluate_rules
from .ids import new_id
from .models import LeashDecisionRecord
from .policy import get_active_policy
from .templates import render_reason

_DISABLED_VALUES = {"false", "0", "no"}
DISABLED_RULE = "LEASH_DISABLED"

_HTTP_STATUS: dict[LeashErrorCode, int] = {
    LeashErrorCode.ORGANISER_ONLY: 401,
    LeashErrorCode.LEASH_DECISION_NOT_FOUND: 404,
    LeashErrorCode.LEASH_ALREADY_RESOLVED: 409,
    LeashErrorCode.LEASH_STALE_DECISION: 409,
    LeashErrorCode.LEASH_POLICY_INVALID: 422,
    LeashErrorCode.LEASH_DISABLED: 503,
}


class LeashError(Exception):
    """A Leash failure the API layer maps to an HTTP error."""

    def __init__(
        self, code: LeashErrorCode, message: str, details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details: dict[str, Any] = details or {}

    @property
    def http_status(self) -> int:
        return _HTTP_STATUS[self.code]


class EngineResume(Protocol):
    def resume(
        self, db: Session, action: GuardAction, subject_id: str, approved_decision_id: str
    ) -> dict[str, Any]:
        """Re-run the held action after an owner approved it."""
        ...

    def cancel(self, db: Session, action: GuardAction, subject_id: str, decision_id: str) -> None:
        """Stop the held action after an owner rejected it."""
        ...


_facts: FactsProvider | None = None
_engine: EngineResume | None = None


def configure(facts: FactsProvider, engine: EngineResume) -> None:
    """Register the facts provider and engine adapter (called once at startup)."""
    global _facts, _engine
    _facts = facts
    _engine = engine


def get_facts_provider() -> FactsProvider:
    if _facts is None:
        raise RuntimeError("Leash is not configured: call configure() first")
    return _facts


def get_engine() -> EngineResume:
    if _engine is None:
        raise RuntimeError("Leash is not configured: call configure() first")
    return _engine


def leash_enabled() -> bool:
    return os.environ.get("LEASH_ENABLED", "true").strip().lower() not in _DISABLED_VALUES


def _amount(facts: BaseFacts) -> Decimal | None:
    if isinstance(facts, PayoutFacts):
        return facts.amount
    if isinstance(facts, ChaseInvoiceFacts):
        return facts.invoice_amount
    return None


def _result(row: LeashDecisionRecord) -> GuardResult:
    return GuardResult(
        decision=LeashDecision(row.decision),
        rule_ids=list(row.rule_ids_json),
        reason=row.reason,
        decision_id=row.id,
    )


def _approved_rule_ids(
    db: Session, action: GuardAction, subject_id: str, approved_decision_id: str
) -> list[str]:
    row = db.get(LeashDecisionRecord, approved_decision_id)
    if (
        row is None
        or row.action != action.value
        or row.subject_id != subject_id
        or row.status != "APPROVED"
    ):
        raise ValueError(
            f"decision {approved_decision_id} is not an approved decision for this subject"
        )
    already_used = db.scalars(
        select(LeashDecisionRecord.id)
        .where(
            LeashDecisionRecord.approves_id == approved_decision_id,
            LeashDecisionRecord.actor == "leash",
        )
        .limit(1)
    ).first()
    if already_used is not None:
        raise ValueError(f"decision {approved_decision_id} has already been used")
    return list(row.rule_ids_json)


def decide(
    db: Session,
    action: GuardAction,
    subject_id: str,
    approved_decision_id: str | None = None,
) -> GuardResult:
    """Guard one money action and log the outcome. Flushes only; the caller commits."""
    subject_type, facts = get_facts_provider().build(db, action, subject_id)

    if approved_decision_id is not None:
        facts.approved_rule_ids = _approved_rule_ids(db, action, subject_id, approved_decision_id)
    else:
        open_row = db.scalars(
            select(LeashDecisionRecord)
            .where(
                LeashDecisionRecord.action == action.value,
                LeashDecisionRecord.subject_id == subject_id,
                LeashDecisionRecord.status == "OPEN",
            )
            .order_by(LeashDecisionRecord.created_at.desc(), LeashDecisionRecord.id.desc())
        ).first()
        if open_row is not None:
            return _result(open_row)

    policy = get_active_policy(db, facts.circle_id)
    facts_json = facts.model_dump(mode="json")
    if leash_enabled():
        decision, rule_ids = evaluate_rules(policy, action, facts_json)
    else:
        decision, rule_ids = LeashDecision.ALLOW, [DISABLED_RULE]
    reason = render_reason(action, decision, rule_ids, facts)

    row = LeashDecisionRecord(
        id=new_id("lsd"),
        circle_id=facts.circle_id,
        policy_version=policy.version,
        action=action.value,
        subject_type=subject_type,
        subject_id=subject_id,
        decision=decision.value,
        rule_ids_json=rule_ids,
        facts_json=facts_json,
        amount=_amount(facts),
        reason=reason,
        actor="leash",
        status="OPEN" if decision is LeashDecision.ASK else "FINAL",
        approves_id=approved_decision_id,
    )
    db.add(row)
    db.flush()
    return _result(row)
