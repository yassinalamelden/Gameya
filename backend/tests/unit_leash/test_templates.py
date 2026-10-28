"""Tests for template reasons."""

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from backend.app.leash.facts import PayoutFacts
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
