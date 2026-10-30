"""CANONICAL INTERFACE CONTRACT — owned by Person 5 (plan §7.4).

Every lane builds against these shapes. Changes need a PR approved by Person 5
plus every affected consumer; mirror each change in frontend/src/types/contracts.ts.

Money is always Decimal quantised to 0.01 (ROUND_HALF_UP); floats are rejected.
"""

from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, BeforeValidator, Field

CENT = Decimal("0.01")


def _reject_float(v: object) -> object:
    if isinstance(v, float):
        # Pydantic only turns ValueError into a validation error.
        raise ValueError("floats are not allowed for money; send a string or Decimal")  # noqa: TRY004
    return v


def _quantise(v: Decimal) -> Decimal:
    if not v.is_finite():
        raise ValueError("money must be a finite amount")
    try:
        return v.quantize(CENT, rounding=ROUND_HALF_UP)
    except InvalidOperation:  # e.g. 1e30: too many digits to hold in cents
        raise ValueError("money amount is too large") from None


Money = Annotated[Decimal, BeforeValidator(_reject_float), AfterValidator(_quantise)]


def _positive(v: Decimal) -> Decimal:
    if v <= 0:  # runs after rounding, so 0.001 (-> 0.00) is rejected too
        raise ValueError("amount must be at least 0.01")
    return v


PositiveMoney = Annotated[Money, AfterValidator(_positive)]
Locale = Literal["en", "ar-EG"]
MemberId = str


class _Strict(BaseModel):
    model_config = {"extra": "forbid"}


# ---------- enums ----------
class CycleUnit(StrEnum):
    WEEK = "WEEK"
    MONTH = "MONTH"


class NeedCategory(StrEnum):
    WEDDING = "WEDDING"
    EDUCATION = "EDUCATION"
    MEDICAL = "MEDICAL"
    HOUSING = "HOUSING"
    BUSINESS = "BUSINESS"
    TRAVEL = "TRAVEL"
    OTHER = "OTHER"


# ---------- snapshots passed into AI functions (read-only views built by Person 1) ----------
class CircleSnapshot(_Strict):
    circle_id: str
    name: str
    contribution_amount: PositiveMoney
    currency: Literal["USD"] = "USD"
    cycle_unit: CycleUnit
    size_n: int = Field(ge=2, le=24)
    start_date: date
    reserve_pct: Decimal = Decimal(0)


class MemberSnapshot(_Strict):
    member_id: MemberId
    display_name: str
    locale: Locale = "en"
    slot_index: int | None = None


# ---------- REQ-AI-02 Needs + Fair Order (Person 3) ----------
class NeedExtraction(_Strict):
    category: NeedCategory
    target_date: date | None
    amount_needed: Money | None
    urgency: int = Field(ge=1, le=5)
    flexibility: Literal["low", "medium", "high"]
    confidence: float = Field(ge=0, le=1)
    raw_month_hint: str | None = None  # the date phrase we matched, for debugging


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
    cost: float  # optimiser cost, not money


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
