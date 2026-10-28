"""Tests for template reasons."""

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from backend.app.leash.facts import (
    ChaseInvoiceFacts,
    PayoutFacts,
    ReminderFacts,
    SwapFacts,
)
from backend.app.leash.templates import _render_one
from backend.app.schemas.contracts import LeashDecision

NOW = datetime(2026, 10, 28, 12, 0, tzinfo=UTC)
ALLOW, ASK, DENY = LeashDecision.ALLOW, LeashDecision.ASK, LeashDecision.DENY


def payout(name: str = "Amina", **kw: Any) -> PayoutFacts:
    data: dict[str, Any] = {
        "now": NOW,
        "circle_id": "c1",
        "payout_id": "p1",
        "amount": "600.00",
        "recipient_member_id": "m1",
        "recipient_name": name,
        "recipient_payout_email": "a@x.com",
        "payout_email_changed_at": NOW - timedelta(days=1),
        "payer_emails": ["a@x.com"],
        "reserve_cover_used": False,
        "slot_swapped_at": NOW - timedelta(days=3, hours=2),
        "recipient_is_organiser": False,
        "recipient_has_unpaid": False,
    }
    return PayoutFacts(**(data | kw))


def test_po01_amina_yesterday() -> None:
    assert _render_one("PO-01", ASK, payout()) == (
        "Held: Amina's payout email changed yesterday (rule PO-01). "
        "Confirm it with Amina before releasing $600.00."
    )


def test_po00_copy() -> None:
    assert _render_one("PO-00", ALLOW, payout()) == (
        "Allowed: all payout checks clear (PO-00). Releasing $600.00 to Amina."
    )


def test_when_phrases() -> None:
    today = payout(payout_email_changed_at=NOW)
    assert "changed today" in _render_one("PO-01", ASK, today)
    old = payout(payout_email_changed_at=NOW - timedelta(days=5, hours=23))
    assert "changed 5 days ago" in _render_one("PO-01", ASK, old)
    assert "swap 3 days ago" in _render_one("PO-04", ASK, payout())


def test_missing_timestamp_raises() -> None:
    with pytest.raises(ValueError, match="timestamp"):
        _render_one("PO-01", ASK, payout(payout_email_changed_at=None))
    with pytest.raises(ValueError, match="timestamp"):
        _render_one("PO-04", ASK, payout(slot_swapped_at=None))


def test_unknown_rule_id_raises() -> None:
    with pytest.raises(ValueError, match="PO-99"):
        _render_one("PO-99", ASK, payout())


def chase(name: str = "Omar") -> ChaseInvoiceFacts:
    return ChaseInvoiceFacts(
        now=NOW,
        circle_id="c1",
        member_id="m2",
        member_name=name,
        invoice_amount="100.00",
        unpaid_amount="90.00",
        due_at=NOW - timedelta(days=8),
        open_invoice_count=0,
        no_auto_chase=False,
    )


def reminder(name: str = "Omar") -> ReminderFacts:
    return ReminderFacts(
        now=NOW, circle_id="c1", member_id="m2", member_name=name, reminders_sent_this_cycle=1
    )


def swap(name: str = "Omar") -> SwapFacts:
    return SwapFacts(
        now=NOW,
        circle_id="c1",
        member_a_name=name,
        member_b_name=name + "b",
        slot_a_payout_at=NOW + timedelta(days=9),
        slot_b_payout_at=NOW + timedelta(hours=30, minutes=40),
        moved_earlier_member_name=name,
        moved_earlier_p_late="0.60",
    )


def test_chase_reminder_swap_copy() -> None:
    assert _render_one("G-01", ALLOW, chase()) == (
        "Allowed: invoice for Omar's unpaid $100.00 (rule G-01)."
    )
    assert _render_one("G-04", DENY, chase()) == (
        "Denied: invoice $100.00 does not match unpaid $90.00 (rule G-04)."
    )
    assert _render_one("DEFAULT-ASK", ASK, chase()) == (
        "Waiting: no rule allows this invoice to Omar yet. Approve to send."
    )
    assert _render_one("G-05", ALLOW, reminder()) == "Allowed: reminder to Omar (rule G-05)."
    assert _render_one("G-05", DENY, reminder()) == (
        "Denied: reminder to Omar too soon or limit reached (rule G-05)."
    )
    assert _render_one("S-00", ALLOW, swap()) == (
        "Allowed: swap between Omar and Omarb (rule S-00)."
    )
    assert _render_one("S-01", ASK, swap()) == (
        "Waiting: a swapped slot pays out within 31 h (rule S-01)."
    )
    assert _render_one("S-02", ASK, swap()) == (
        "Waiting: swap moves high-risk Omar earlier (rule S-02)."
    )


def test_no_upcoming_payout_raises() -> None:
    past = swap().model_copy(
        update={
            "slot_a_payout_at": NOW - timedelta(hours=1),
            "slot_b_payout_at": NOW - timedelta(hours=2),
        }
    )
    with pytest.raises(ValueError, match="upcoming"):
        _render_one("S-01", ASK, past)
