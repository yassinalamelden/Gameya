"""CANONICAL INTERFACE CONTRACT — owned by Person 5 (plan §7.4).

Every lane builds against these shapes. Changes need a PR approved by Person 5
plus every affected consumer; mirror each change in frontend/src/types/contracts.ts.

Money is always Decimal quantised to 0.01 (ROUND_HALF_UP); floats are rejected.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, BeforeValidator, Field

CENT = Decimal("0.01")


def _reject_float(v: object) -> object:
    if isinstance(v, float):
        raise ValueError("floats are not allowed for money; send a string or Decimal")
    return v


def _quantise(v: Decimal) -> Decimal:
    return v.quantize(CENT, rounding=ROUND_HALF_UP)


Money = Annotated[Decimal, BeforeValidator(_reject_float), AfterValidator(_quantise)]
Locale = Literal["en", "ar-EG"]
MemberId = str


class _Strict(BaseModel):
    model_config = {"extra": "forbid"}


# ---------- enums ----------
class CycleUnit(StrEnum):
    WEEK = "WEEK"
    MONTH = "MONTH"


class CircleStatus(StrEnum):
    DRAFT = "DRAFT"
    RECRUITING = "RECRUITING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class CycleStatus(StrEnum):
    OPEN = "OPEN"
    COLLECTING = "COLLECTING"
    GRACE = "GRACE"
    DEFAULT_HANDLED = "DEFAULT_HANDLED"
    READY = "READY"
    PAYING_OUT = "PAYING_OUT"
    PAID_OUT = "PAID_OUT"


class ContributionStatus(StrEnum):
    PENDING = "PENDING"
    PAID = "PAID"
    LATE = "LATE"
    FAILED = "FAILED"
    COVERED = "COVERED"


class NeedCategory(StrEnum):
    WEDDING = "WEDDING"
    EDUCATION = "EDUCATION"
    MEDICAL = "MEDICAL"
    HOUSING = "HOUSING"
    BUSINESS = "BUSINESS"
    TRAVEL = "TRAVEL"
    OTHER = "OTHER"


class MediationKind(StrEnum):
    PARTIAL_NOW = "PARTIAL_NOW"
    SWAP = "SWAP"
    RESERVE_COVER = "RESERVE_COVER"


class AgentName(StrEnum):
    CIRCLE = "CIRCLE"
    NEEDS = "NEEDS"
    FAIR_ORDER = "FAIR_ORDER"
    CHASE = "CHASE"
    MEDIATION = "MEDIATION"
    COPILOT = "COPILOT"
    STRESS_TEST = "STRESS_TEST"
    SWAP_BROKER = "SWAP_BROKER"


# ---------- snapshots passed into AI functions (read-only views built by Person 1) ----------
class CircleSnapshot(_Strict):
    circle_id: str
    name: str
    contribution_amount: Money
    currency: Literal["USD"] = "USD"
    cycle_unit: CycleUnit
    size_n: int = Field(ge=2, le=24)
    start_date: date
    reserve_pct: Decimal = Decimal("0")


class MemberSnapshot(_Strict):
    member_id: MemberId
    display_name: str
    locale: Locale = "en"
    slot_index: int | None = None


class CycleSnapshot(_Strict):
    cycle_id: str
    circle: CircleSnapshot
    index_k: int
    due_date: date
    status: CycleStatus
    recipient_member_id: MemberId | None = None


class Viewer(_Strict):
    member_id: MemberId
    circle_id: str
    is_organiser: bool = False
    locale: Locale = "en"


# ---------- REQ-AI-01 Circle Agent (Person 2) ----------
class ChatMessage(_Strict):
    role: Literal["user", "assistant"]
    content: str


class CircleSpec(_Strict):
    name: str
    contribution_amount: Money = Field(gt=0, le=Decimal("5000"))
    cycle_unit: CycleUnit
    size_n: int = Field(ge=2, le=24)
    start_date: date
    reserve_pct: Decimal = Field(default=Decimal("0"), ge=0, le=Decimal("10"))


class CircleAgentTurn(_Strict):
    reply: str
    spec: CircleSpec | None = None
    needs_confirmation: bool = False
    paypal_product_id: str | None = None
    paypal_plan_id: str | None = None


# ---------- REQ-AI-02 Needs + Fair Order (Person 3) ----------
class NeedExtraction(_Strict):
    category: NeedCategory
    target_date: date | None
    amount_needed: Money | None
    urgency: int = Field(ge=1, le=5)
    flexibility: Literal["low", "medium", "high"]
    confidence: float = Field(ge=0, le=1)


class MemberProfile(_Strict):
    member: MemberSnapshot
    need: NeedExtraction | None
    reliability_p_late: float = Field(ge=0, le=1)


class SlotDate(_Strict):
    slot_index: int
    payout_date: date


class SlotAssignment(_Strict):
    member_id: MemberId
    slot_index: int
    payout_date: date
    cost: float


class OrderProposal(_Strict):
    assignments: list[SlotAssignment]
    seed: int
    explanations: dict[MemberId, str] = Field(default_factory=dict)


# ---------- REQ-AI-04 Reliability (Person 3) ----------
class ReliabilityFeatures(_Strict):
    on_time_ratio: float = Field(ge=0, le=1)
    avg_days_late: float = Field(ge=0)
    cycles_completed: int = Field(ge=0)
    failed_payments: int = Field(ge=0)
    invoices_needed: int = Field(ge=0)
    circles_completed: int = Field(ge=0)
    account_age_days: int = Field(ge=0)


class ReliabilityFactor(_Strict):
    feature: str
    contribution: float
    label: str


class ReliabilityScore(_Strict):
    member_id: MemberId
    p_late: float = Field(ge=0, le=1)
    top_factors: list[ReliabilityFactor] = Field(max_length=3)


# ---------- REQ-AI-03 Smart Chase / REQ-AI-05 Mediation (Person 2) ----------
class ChasePlan(_Strict):
    member_id: MemberId
    nudge_text: str = Field(max_length=600)
    create_invoice: bool
    invoice_amount: Money | None = None  # engine validates <= contribution_amount
    invoice_note: str | None = Field(default=None, max_length=1500)


class MediationOption(_Strict):
    option_id: str
    kind: MediationKind
    summary: str
    amount_now: Money | None = None
    swap_with_member_id: MemberId | None = None
    requires_approval_from: list[MemberId]


# ---------- REQ-AI-06 Copilot (Person 2) ----------
class CopilotAnswer(_Strict):
    answer: str
    locale: Locale
    sources: list[str] = Field(default_factory=list)  # ledger row ids used


# ---------- REQ-AI-07 Stress-Test (Person 3) ----------
class ReservePoint(_Strict):
    reserve_pct: Decimal
    completion_probability: float = Field(ge=0, le=1)
    expected_shortfall: Money


class StressTestResult(_Strict):
    n_sims: int
    seed: int
    points: list[ReservePoint]
    recommended_reserve_pct: Decimal
    explanation: str | None = None


# ---------- REQ-AI-08 Slot-Swap Broker (Person 2) ----------
class SwapRequest(_Strict):
    requester_id: MemberId
    wanted_slot_index: int
    reason_text: str = Field(max_length=500)


class SwapProposal(_Strict):
    swap_id: str
    requester_id: MemberId
    counterparty_id: MemberId
    from_slot_index: int
    to_slot_index: int
    message: str
    approvals: list[MemberId] = Field(default_factory=list)


# ---------- REQ-AI-09 audit log ----------
class AgentDecisionRecord(_Strict):
    agent: AgentName
    circle_id: str
    input_summary: str
    output_json: dict[str, object]
    rationale: str
    model: str
    tools_called: list[str] = Field(default_factory=list)
    requires_approval: bool = False
    created_at: datetime


# ---------- Interface 2 read models for AG Grid ----------
class LedgerRow(_Strict):
    cycle_index: int
    member_id: MemberId
    member_name: str
    due_date: date
    amount: Money
    status: ContributionStatus
    method: Literal["SUBSCRIPTION", "ORDER", "INVOICE", "RESERVE"] | None
    paypal_ref_id: str | None
    paid_at: datetime | None
    recipient: bool = False
