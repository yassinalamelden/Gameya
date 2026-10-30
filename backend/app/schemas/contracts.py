"""Canonical shared interface contracts for Gam'eya.

Frozen per the engineering plan (Section 7.4). Owned by Person 5; any change
requires a PR approved by Person 5 and every affected consumer.

Interface 1 = typed Python models passed between the AI/ML packages and the
backend. Interface 2 = REST request/response shapes served under /api/v1/*.

Money is Decimal with 2 decimal places, ROUND_HALF_UP; float is banned on
financial paths.
"""

from __future__ import annotations

from datetime import date, datetime  # noqa: TC003
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum
from typing import Annotated, Literal, NewType

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

MemberId = NewType("MemberId", str)
CircleId = NewType("CircleId", str)
CycleIndex = NewType("CycleIndex", int)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def quantize_amount(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


Money = Annotated[
    Decimal,
    Field(max_digits=12, decimal_places=2, ge=Decimal("0.00")),
]


class Environment(StrEnum):
    LOCAL_TEST = "local_test"
    SANDBOX = "sandbox"
    PRODUCTION = "production"


class Locale(StrEnum):
    EN = "en"
    AR = "ar"


class Role(StrEnum):
    ORGANISER = "organiser"
    MEMBER = "member"


class BillingFrequency(StrEnum):
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"


class ContributionStatus(StrEnum):
    PENDING = "pending"
    INVOICED = "invoiced"
    PAID = "paid"
    COVERED = "covered"
    FAILED = "failed"


class SubscriptionStatus(StrEnum):
    NONE = "none"
    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"


class CycleStatus(StrEnum):
    UPCOMING = "upcoming"
    DUE = "due"
    GRACE = "grace"
    READY = "ready"
    PAID_OUT = "paid_out"
    FAILED = "failed"


class PayoutStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    PAID_OUT = "paid_out"
    FAILED = "failed"
    UNCLAIMED = "unclaimed"


class ContributionSource(StrEnum):
    SUBSCRIPTION = "subscription"
    ORDER = "order"
    INVOICE = "invoice"
    RESERVE = "reserve"


class MediationKind(StrEnum):
    PARTIAL_NOW = "partial_now"
    SWAP = "swap"
    RESERVE_COVER = "reserve_cover"


class AgentName(StrEnum):
    CIRCLE_AGENT = "circle_agent"
    SMART_CHASE = "smart_chase"
    MEDIATION = "mediation"
    COPILOT = "copilot"
    SWAP_BROKER = "swap_broker"
    NEEDS_EXTRACTOR = "needs_extractor"
    FAIR_ORDER = "fair_order"
    STRESS_TEST = "stress_test"


class ToolName(StrEnum):
    CREATE_PRODUCT = "create_product"
    LIST_PRODUCTS = "list_products"
    SHOW_PRODUCT_DETAILS = "show_product_details"
    CREATE_SUBSCRIPTION_PLAN = "create_subscription_plan"
    LIST_SUBSCRIPTION_PLANS = "list_subscription_plans"
    SHOW_SUBSCRIPTION_PLAN_DETAILS = "show_subscription_plan_details"
    CREATE_SUBSCRIPTION = "create_subscription"
    SHOW_SUBSCRIPTION_DETAILS = "show_subscription_details"
    UPDATE_SUBSCRIPTION = "update_subscription"
    CANCEL_SUBSCRIPTION = "cancel_subscription"
    CREATE_INVOICE = "create_invoice"
    SEND_INVOICE = "send_invoice"
    SEND_INVOICE_REMINDER = "send_invoice_reminder"
    GENERATE_INVOICE_QR_CODE = "generate_invoice_qr_code"
    CREATE_ORDER = "create_order"
    GET_ORDER = "get_order"
    PAY_ORDER = "pay_order"
    LIST_TRANSACTIONS = "list_transactions"


class ChatRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class SwapStatus(StrEnum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    APPLIED = "applied"


class ChaseAction(StrEnum):
    NOOP = "noop"
    NUDGE = "nudge"
    INVOICE = "invoice"


class SanityStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


class ToolCall(StrictModel):
    """An executed or proposed Agent Toolkit tool call, for the audit log."""

    name: ToolName
    arguments: dict[str, str | int | Decimal | None] = Field(default_factory=dict)
    result_summary: str | None = None


class ChatMessage(StrictModel):
    role: ChatRole
    content: str = Field(min_length=1, max_length=4000)
    created_at: datetime | None = None


class RiskFactor(StrictModel):
    key: str = Field(max_length=64)
    weight: float = Field(ge=-1.0, le=1.0)
    description: str = Field(max_length=200)


class ReliabilityScore(StrictModel):
    """Explainable P(late next cycle). Never framed as a credit score."""

    member_id: MemberId
    p_late: float = Field(ge=0.0, le=1.0)
    top_factors: list[RiskFactor] = Field(max_length=3, default_factory=list)


class ReliabilityFeatures(StrictModel):
    member_id: MemberId
    features: dict[str, float]


class MemberSnapshot(StrictModel):
    member_id: MemberId
    display_name: str
    role: Role = Role.MEMBER
    subscription_status: SubscriptionStatus = SubscriptionStatus.NONE
    contribution_status: ContributionStatus | None = None
    days_late: int = Field(default=0, ge=0)
    p_late: float | None = Field(default=None, ge=0.0, le=1.0)


class CycleSnapshot(StrictModel):
    cycle_index: int = Field(ge=0)
    status: CycleStatus = CycleStatus.UPCOMING
    due_date: date
    amount_due: Money
    pot_total: Money
    recipient_id: MemberId | None = None
    unpaid_members: list[MemberSnapshot] = Field(default_factory=list)


class CircleSpec(StrictModel):
    """The typed result of the Circle Agent's slot-filling conversation."""

    name: str = Field(min_length=1, max_length=80)
    member_count: int = Field(ge=2, le=12)
    contribution_amount: Money
    currency: Literal["USD"] = "USD"
    frequency: BillingFrequency = BillingFrequency.MONTHLY
    start_date: date
    organiser_id: MemberId | None = None
    purpose: str | None = Field(default=None, max_length=500)
    confirmed: bool = False


class CircleSnapshot(StrictModel):
    circle_id: CircleId
    spec: CircleSpec
    members: list[MemberSnapshot]
    cycles: list[CycleSnapshot]
    current_cycle_index: int = Field(ge=0, default=0)
    reserve_pct: Decimal = Field(default=Decimal("0.00"), ge=0, le=Decimal("0.20"))


class AgentDecision(StrictModel):
    """One audit row per AI decision; nothing executes without approval."""

    decision_id: str
    agent: AgentName
    circle_id: CircleId | None = None
    cycle_index: int | None = None
    model: str
    tool_calls: list[ToolCall] = Field(default_factory=list)
    rationale: str
    created_at: datetime | None = None
    human_approved: bool = False


class CircleAgentTurn(StrictModel):
    reply: str
    spec: CircleSpec | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list, max_length=5)
    agent_decision: AgentDecision | None = None
    needs_confirmation: bool = False


class NeedItem(StrictModel):
    kind: Literal["deadline", "flexible"]
    description: str = Field(max_length=300)
    target_date: date | None = None
    urgency: int = Field(ge=1, le=5)
    amount: Money | None = None


class NeedExtraction(StrictModel):
    member_id: MemberId
    raw_text: str = Field(max_length=1000)
    locale: Locale
    needs: list[NeedItem] = Field(min_length=1, max_length=5)
    confidence: float = Field(ge=0.0, le=1.0)


class MemberProfile(StrictModel):
    member_id: MemberId
    display_name: str
    needs: list[NeedExtraction] = Field(default_factory=list)
    reliability: ReliabilityScore | None = None


class SlotDate(StrictModel):
    slot_index: int = Field(ge=0)
    payout_date: date


class SlotAssignment(StrictModel):
    member_id: MemberId
    slot_index: int = Field(ge=0)
    explanation: str = Field(max_length=500)


class OrderProposal(StrictModel):
    """Deterministic Hungarian-optimiser output; the LLM never picks the order."""

    circle_id: CircleId
    deterministic_seed: int
    slots: list[SlotAssignment] = Field(min_length=2)


class Viewer(StrictModel):
    viewer_id: MemberId
    role: Role
    circle_id: CircleId


class CircleReadTools(StrictModel):
    """SELECT-only ledger reads scoped to the viewer's own circle."""

    circle_id: CircleId
    allowed_queries: tuple[str, ...] = (
        "circle_summary",
        "cycle_status",
        "own_contribution_status",
        "upcoming_payout_date",
        "unpaid_members",
    )


class CopilotAnswer(StrictModel):
    answer: str
    engine_facts_only: bool = Field(default=True)
    support_rows: list[str] = Field(default_factory=list, max_length=10)
    agent_decision: AgentDecision | None = None


class ChasePlan(StrictModel):
    member_id: MemberId
    cycle_index: int = Field(ge=0)
    action: ChaseAction
    nudge_text: str | None = Field(default=None, max_length=1000)
    invoice_amount: Money | None = None
    invoice_note: str | None = Field(default=None, max_length=1000)
    agent_decision: AgentDecision | None = None

    @model_validator(mode="after")
    def _shape(self) -> ChasePlan:
        if self.action is ChaseAction.NUDGE and not self.nudge_text:
            raise ValueError("nudge action requires nudge_text")
        if self.action is ChaseAction.INVOICE:
            if self.invoice_amount is None:
                raise ValueError("invoice action requires invoice_amount")
            if self.invoice_note is None:
                raise ValueError("invoice action requires invoice_note")
        return self

    def assert_within_contribution(self, contribution_amount: Decimal) -> None:
        """Guarantee an invoice never exceeds the circle contribution amount."""
        if self.invoice_amount is None:
            return
        if quantize_amount(self.invoice_amount) > quantize_amount(contribution_amount):
            raise ValueError(
                f"invoice_amount {self.invoice_amount} exceeds contribution {contribution_amount}"
            )


class MediationOption(StrictModel):
    option_id: str
    kind: MediationKind
    description: str = Field(max_length=500)
    amount: Money | None = None
    requires_approval: bool = Field(default=True, frozen=True)
    agent_decision: AgentDecision | None = None


class SwapRequest(StrictModel):
    request_id: str
    requester_id: MemberId
    requester_slot_index: int = Field(ge=0)
    target_slot_index: int = Field(ge=0)
    reason: str = Field(max_length=500)


class SwapProposal(StrictModel):
    """Drafted swap; applied by the engine only after both members approve."""

    proposal_id: str
    swap_request: SwapRequest
    counterpart_id: MemberId
    counterpart_slot_index: int = Field(ge=0)
    draft_text: str = Field(max_length=1000)
    invariants_ok: bool = True
    status: SwapStatus = SwapStatus.PROPOSED
    agent_decision: AgentDecision | None = None


class ReserveOutcome(StrictModel):
    reserve_pct: Decimal
    completion_probability: float = Field(ge=0.0, le=1.0)
    expected_covered_cycles: float = Field(ge=0.0)


class StressTestResult(StrictModel):
    """Monte Carlo completion odds per reserve percentage; seeded, deterministic."""

    circle_id: CircleId
    n_sims: int = Field(default=10_000, ge=1)
    seed: int = 42
    per_reserve: list[ReserveOutcome] = Field(min_length=1)
    recommended_reserve_pct: Decimal


class AgentChatSession(StrictModel):
    session_id: str


class Persona(StrictModel):
    persona_id: str
    display_name: str
    role: Role
    sandbox_email: str | None = None
    avatar: str | None = Field(default=None, max_length=8)


class DemoLoginRequest(StrictModel):
    persona_id: str


class DemoLoginResponse(StrictModel):
    persona: Persona
    token: str | None = None


class CircleAgentChatRequest(StrictModel):
    session_id: str | None = None
    history: list[ChatMessage] = Field(min_length=1, max_length=40)
    confirmed: bool = False


class CircleAgentChatResponse(StrictModel):
    session_id: str
    turn: CircleAgentTurn


class CreateCircleRequest(StrictModel):
    spec: CircleSpec

    @model_validator(mode="after")
    def _must_be_confirmed(self) -> CreateCircleRequest:
        if not self.spec.confirmed:
            raise ValueError("circle creation requires a confirmed CircleSpec")
        return self


class PayPalReferences(StrictModel):
    product_id: str | None = None
    plan_id: str | None = None
    webhook_id: str | None = None


class CircleCreateResponse(StrictModel):
    circle: CircleSnapshot
    paypal: PayPalReferences


class JoinCircleRequest(StrictModel):
    member_id: MemberId


class JoinCircleResponse(StrictModel):
    circle_id: CircleId
    member_id: MemberId
    subscription_id: str | None = None
    approval_url: HttpUrl | None = None


class NeedSubmissionRequest(StrictModel):
    member_id: MemberId
    raw_text: str = Field(min_length=1, max_length=1000)
    locale: Locale


class OrderProposeRequest(StrictModel):
    deterministic_seed: int = 42


class OrderApprovalRequest(StrictModel):
    member_id: MemberId


class StressTestRequest(StrictModel):
    reserve_pcts: list[Decimal] = Field(
        min_length=1,
        max_length=11,
        default_factory=lambda: [Decimal(i) for i in range(0, 11)],
    )
    n_sims: int = Field(default=10_000, ge=1, le=1_000_000)
    seed: int = 42


class StressTestResponse(StrictModel):
    result: StressTestResult
    explanation: str


class CopilotQuestionRequest(StrictModel):
    member_id: MemberId
    question: str = Field(min_length=1, max_length=500)


class SwapCreateRequest(StrictModel):
    request: SwapRequest


class SwapApprovalRequest(StrictModel):
    approver_id: MemberId


class PayNowRequest(StrictModel):
    member_id: MemberId


class PayNowResponse(StrictModel):
    cycle_index: int
    member_id: MemberId
    order_id: str | None = None
    capture_id: str | None = None
    status: ContributionStatus = ContributionStatus.PENDING


class MediationApproveRequest(StrictModel):
    approving_member_id: MemberId | None = None


class LedgerRow(StrictModel):
    row_id: str
    cycle_index: int = Field(ge=0)
    member_id: MemberId
    member_name: str
    amount: Money
    status: ContributionStatus
    source: ContributionSource
    paypal_reference: str | None = None
    created_at: datetime | None = None


class LedgerResponse(StrictModel):
    circle_id: CircleId
    rows: list[LedgerRow]
    payouts: list[PayoutRow]
    contributions_total: Money
    paid_out_total: Money


class PayoutRow(StrictModel):
    payout_id: str
    cycle_index: int
    recipient_id: MemberId
    batch_id: str
    amount: Money
    status: PayoutStatus
    created_at: datetime | None = None


class AuditResponse(StrictModel):
    circle_id: CircleId
    decisions: list[AgentDecision]


class ReliabilityRow(StrictModel):
    member_id: MemberId
    display_name: str
    score: ReliabilityScore


class ReliabilityResponse(StrictModel):
    circle_id: CircleId
    rows: list[ReliabilityRow]


class WebhookAcknowledgement(StrictModel):
    received: bool
    duplicate: bool = False


class FastForwardRequest(StrictModel):
    to_cycle_index: int = Field(ge=0)


class ResetDemoResponse(StrictModel):
    reset: bool
    circle_id: CircleId


class HealthResponse(StrictModel):
    status: SanityStatus
    environment: Environment
    paypal: SanityStatus
    llm: SanityStatus
    database: SanityStatus
    version: str
