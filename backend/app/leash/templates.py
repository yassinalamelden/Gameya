"""Template reasons for Leash decisions.

Pure: no I/O, no LLM. Every number in a reason comes from the facts (money,
or whole days / hours derived from fact datetimes).
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from decimal import Decimal

from ..schemas.contracts import LeashDecision
from .facts import BaseFacts, PayoutFacts


def _money(value: Decimal) -> str:
    return f"${value:.2f}"


def _when(now: datetime, then: datetime | None) -> str:
    if then is None:
        raise ValueError("missing timestamp for a {when} reason")
    days = max((now - then).days, 0)
    if days == 0:
        return "today"
    if days == 1:
        return "yesterday"
    return f"{days} days ago"


def _payout(f: BaseFacts) -> PayoutFacts:
    if not isinstance(f, PayoutFacts):
        raise TypeError("payout rule needs PayoutFacts")
    return f


def _po00(f: BaseFacts) -> str:
    p = _payout(f)
    return (
        f"Allowed: all payout checks clear (PO-00). "
        f"Releasing {_money(p.amount)} to {p.recipient_name}."
    )


def _po01(f: BaseFacts) -> str:
    p = _payout(f)
    n = p.recipient_name
    return (
        f"Held: {n}'s payout email changed {_when(p.now, p.payout_email_changed_at)} "
        f"(rule PO-01). Confirm it with {n} before releasing {_money(p.amount)}."
    )


def _po02(f: BaseFacts) -> str:
    p = _payout(f)
    return (
        f"Held: {p.recipient_name}'s payout email has never paid into this circle "
        f"(rule PO-02). Confirm it before releasing {_money(p.amount)}."
    )


def _po03(f: BaseFacts) -> str:
    p = _payout(f)
    return (
        f"Held: this pot used reserve cover (rule PO-03). "
        f"Review before releasing {_money(p.amount)} to {p.recipient_name}."
    )


def _po04(f: BaseFacts) -> str:
    p = _payout(f)
    return (
        f"Held: {p.recipient_name}'s slot changed by a swap "
        f"{_when(p.now, p.slot_swapped_at)} (rule PO-04). "
        f"Cooling-off before releasing {_money(p.amount)}."
    )


def _po05(f: BaseFacts) -> str:
    p = _payout(f)
    return (
        f"Held: {p.recipient_name} is the organiser (rule PO-05). Approval is logged for members."
    )


def _po06(f: BaseFacts) -> str:
    p = _payout(f)
    return (
        f"Held: {p.recipient_name} still has an unpaid contribution (rule PO-06). "
        f"Decide before releasing {_money(p.amount)}."
    )


_TEMPLATES: dict[str, Callable[[BaseFacts], str]] = {
    "PO-00": _po00,
    "PO-01": _po01,
    "PO-02": _po02,
    "PO-03": _po03,
    "PO-04": _po04,
    "PO-05": _po05,
    "PO-06": _po06,
}


def _render_one(rule_id: str, decision: LeashDecision, facts: BaseFacts) -> str:
    template = _TEMPLATES.get(rule_id)
    if template is None:
        raise ValueError(f"no reason template for rule id {rule_id!r}")
    return template(facts)
