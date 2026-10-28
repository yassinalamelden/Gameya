"""Canonical cross-team contract types.

Currently holds the Leash types (Interface 3). Other teams' types will be
added alongside these.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class GuardAction(str, Enum):
    RELEASE_POT_PAYOUT = "RELEASE_POT_PAYOUT"
    SEND_CHASE_INVOICE = "SEND_CHASE_INVOICE"
    SEND_INVOICE_REMINDER = "SEND_INVOICE_REMINDER"
    APPLY_SLOT_SWAP = "APPLY_SLOT_SWAP"


class LeashDecision(str, Enum):
    ALLOW = "ALLOW"
    ASK = "ASK"
    DENY = "DENY"


LeashPreset = Literal["HANDS_OFF", "STANDARD", "STRICT"]


class LeashThresholds(BaseModel):
    email_change_window_days: int = Field(7, ge=1, le=30)
    reminder_min_gap_hours: int = Field(48, ge=12, le=168)
    max_reminders_per_cycle: int = Field(3, ge=1, le=10)
    swap_cooldown_hours: int = Field(24, ge=0, le=168)
    swap_near_payout_hours: int = Field(48, ge=0, le=168)
    high_risk_p_late: Decimal = Field(Decimal("0.50"), ge=0, le=1)


class LeashPolicy(BaseModel):
    circle_id: str
    version: int
    preset: LeashPreset = "STANDARD"
    thresholds: LeashThresholds
    no_auto_chase_member_ids: list[str] = Field(default_factory=list)


class GuardResult(BaseModel):
    decision: LeashDecision
    rule_ids: list[str]
    reason: str = Field(max_length=200)
    decision_id: str


class LeashInboxRecipient(BaseModel):
    member_id: str
    name: str
    payout_email: str | None = None


class LeashInboxItem(BaseModel):
    decision_id: str
    action: GuardAction
    subject_type: Literal["payout", "chase_plan", "swap"]
    subject_id: str
    cycle_index: int | None = None
    recipient: LeashInboxRecipient | None = None
    amount: Decimal | None = None
    rule_ids: list[str]
    reason: str
    created_at: datetime


class LeashInbox(BaseModel):
    items: list[LeashInboxItem]


class LeashDecisionRow(BaseModel):
    decision_id: str
    circle_id: str
    policy_version: int
    action: GuardAction
    subject_type: Literal["payout", "chase_plan", "swap"]
    subject_id: str
    decision: LeashDecision
    rule_ids: list[str]
    amount: Decimal | None = None
    reason: str
    actor: Literal["leash", "organiser"]
    status: Literal["FINAL", "OPEN", "APPROVED", "REJECTED"]
    created_at: datetime
    resolved_at: datetime | None = None


class LeashResolveRequest(BaseModel):
    note: str | None = Field(None, max_length=200)


class LeashResolveResponse(BaseModel):
    decision_id: str
    approves: str
    actor: Literal["organiser"]
    result: dict[str, Any] | None = None


class LeashErrorCode(str, Enum):
    ORGANISER_ONLY = "ORGANISER_ONLY"
    LEASH_DECISION_NOT_FOUND = "LEASH_DECISION_NOT_FOUND"
    LEASH_ALREADY_RESOLVED = "LEASH_ALREADY_RESOLVED"
    LEASH_STALE_DECISION = "LEASH_STALE_DECISION"
    LEASH_POLICY_INVALID = "LEASH_POLICY_INVALID"
    LEASH_DISABLED = "LEASH_DISABLED"
