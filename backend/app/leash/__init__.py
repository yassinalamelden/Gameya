"""Leash: deterministic money-action guard. Stub until Task 5."""

from sqlalchemy.orm import Session

from ..schemas.contracts import GuardAction, GuardResult, LeashDecision


def decide(
    db: Session | None,
    action: GuardAction,
    subject_id: str,
    approved_decision_id: str | None = None,
) -> GuardResult:
    return GuardResult(
        decision=LeashDecision.ALLOW,
        rule_ids=["STUB"],
        reason="Leash stub: allowed.",
        decision_id="lsd_stub",
    )
