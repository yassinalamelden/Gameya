export type MemberId = string;
export type CircleId = string;

export type Environment = "local_test" | "sandbox" | "production";
export type Locale = "en" | "ar";
export type Role = "organiser" | "member";
export type BillingFrequency = "weekly" | "biweekly" | "monthly";

export type ContributionStatus =
  | "pending"
  | "invoiced"
  | "paid"
  | "covered"
  | "failed";

export type SubscriptionStatus =
  | "none"
  | "pending_approval"
  | "active"
  | "cancelled"
  | "suspended";

export type CycleStatus =
  | "upcoming"
  | "due"
  | "grace"
  | "ready"
  | "paid_out"
  | "failed";

export type PayoutStatus =
  | "pending"
  | "processing"
  | "paid_out"
  | "failed"
  | "unclaimed";

export type ContributionSource = "subscription" | "order" | "invoice" | "reserve";

export type MediationKind = "partial_now" | "swap" | "reserve_cover";

export type AgentName =
  | "circle_agent"
  | "smart_chase"
  | "mediation"
  | "copilot"
  | "swap_broker"
  | "needs_extractor"
  | "fair_order"
  | "stress_test";

export type ToolName =
  | "create_product"
  | "list_products"
  | "show_product_details"
  | "create_subscription_plan"
  | "list_subscription_plans"
  | "show_subscription_plan_details"
  | "create_subscription"
  | "show_subscription_details"
  | "update_subscription"
  | "cancel_subscription"
  | "create_invoice"
  | "send_invoice"
  | "send_invoice_reminder"
  | "generate_invoice_qr_code"
  | "create_order"
  | "get_order"
  | "pay_order"
  | "list_transactions";

export type ChatRole = "user" | "assistant" | "system";

export type SwapStatus = "proposed" | "accepted" | "declined" | "applied";

export type ChaseAction = "noop" | "nudge" | "invoice";

export type SanityStatus = "healthy" | "degraded" | "down";

export type NeedKind = "deadline" | "flexible";

export interface ToolCall {
  name: ToolName;
  arguments: Record<string, string | number | null>;
  result_summary: string | null;
}

export interface ChatMessage {
  role: ChatRole;
  content: string;
  created_at: string | null;
}

export interface RiskFactor {
  key: string;
  weight: number;
  description: string;
}

export interface ReliabilityScore {
  member_id: MemberId;
  p_late: number;
  top_factors: RiskFactor[];
}

export interface ReliabilityFeatures {
  member_id: MemberId;
  features: Record<string, number>;
}

export interface MemberSnapshot {
  member_id: MemberId;
  display_name: string;
  role: Role;
  subscription_status: SubscriptionStatus;
  contribution_status: ContributionStatus | null;
  days_late: number;
  p_late: number | null;
}

export interface CycleSnapshot {
  cycle_index: number;
  status: CycleStatus;
  due_date: string;
  amount_due: string;
  pot_total: string;
  recipient_id: MemberId | null;
  unpaid_members: MemberSnapshot[];
}

export interface CircleSpec {
  name: string;
  member_count: number;
  contribution_amount: string;
  currency: "USD";
  frequency: BillingFrequency;
  start_date: string;
  organiser_id: MemberId | null;
  purpose: string | null;
  confirmed: boolean;
}

export interface CircleSnapshot {
  circle_id: CircleId;
  spec: CircleSpec;
  members: MemberSnapshot[];
  cycles: CycleSnapshot[];
  current_cycle_index: number;
  reserve_pct: string;
}

export interface AgentDecision {
  decision_id: string;
  agent: AgentName;
  circle_id: CircleId | null;
  cycle_index: number | null;
  model: string;
  tool_calls: ToolCall[];
  rationale: string;
  created_at: string | null;
  human_approved: boolean;
}

export interface CircleAgentTurn {
  reply: string;
  spec: CircleSpec | null;
  tool_calls: ToolCall[];
  agent_decision: AgentDecision | null;
  needs_confirmation: boolean;
}

export interface NeedItem {
  kind: NeedKind;
  description: string;
  target_date: string | null;
  urgency: number;
  amount: string | null;
}

export interface NeedExtraction {
  member_id: MemberId;
  raw_text: string;
  locale: Locale;
  needs: NeedItem[];
  confidence: number;
}

export interface MemberProfile {
  member_id: MemberId;
  display_name: string;
  needs: NeedExtraction[];
  reliability: ReliabilityScore | null;
}

export interface SlotDate {
  slot_index: number;
  payout_date: string;
}

export interface SlotAssignment {
  member_id: MemberId;
  slot_index: number;
  explanation: string;
}

export interface OrderProposal {
  circle_id: CircleId;
  deterministic_seed: number;
  slots: SlotAssignment[];
}

export interface Viewer {
  viewer_id: MemberId;
  role: Role;
  circle_id: CircleId;
}

export interface CircleReadTools {
  circle_id: CircleId;
  allowed_queries: readonly string[];
}

export interface CopilotAnswer {
  answer: string;
  engine_facts_only: boolean;
  support_rows: string[];
  agent_decision: AgentDecision | null;
}

export interface ChasePlan {
  member_id: MemberId;
  cycle_index: number;
  action: ChaseAction;
  nudge_text: string | null;
  invoice_amount: string | null;
  invoice_note: string | null;
  agent_decision: AgentDecision | null;
}

export interface MediationOption {
  option_id: string;
  kind: MediationKind;
  description: string;
  amount: string | null;
  requires_approval: true;
  agent_decision: AgentDecision | null;
}

export interface SwapRequest {
  request_id: string;
  requester_id: MemberId;
  requester_slot_index: number;
  target_slot_index: number;
  reason: string;
}

export interface SwapProposal {
  proposal_id: string;
  swap_request: SwapRequest;
  counterpart_id: MemberId;
  counterpart_slot_index: number;
  draft_text: string;
  invariants_ok: boolean;
  status: SwapStatus;
  agent_decision: AgentDecision | null;
}

export interface ReserveOutcome {
  reserve_pct: string;
  completion_probability: number;
  expected_covered_cycles: number;
}

export interface StressTestResult {
  circle_id: CircleId;
  n_sims: number;
  seed: number;
  per_reserve: ReserveOutcome[];
  recommended_reserve_pct: string;
}

export interface AgentChatSession {
  session_id: string;
}

export interface Persona {
  persona_id: string;
  display_name: string;
  role: Role;
  sandbox_email: string | null;
  avatar: string | null;
}

export interface DemoLoginRequest {
  persona_id: string;
}

export interface DemoLoginResponse {
  persona: Persona;
  token: string | null;
}

export interface CircleAgentChatRequest {
  session_id: string | null;
  history: ChatMessage[];
  confirmed: boolean;
}

export interface CircleAgentChatResponse {
  session_id: string;
  turn: CircleAgentTurn;
}

export interface CreateCircleRequest {
  spec: CircleSpec;
}

export interface PayPalReferences {
  product_id: string | null;
  plan_id: string | null;
  webhook_id: string | null;
}

export interface CircleCreateResponse {
  circle: CircleSnapshot;
  paypal: PayPalReferences;
}

export interface JoinCircleRequest {
  member_id: MemberId;
}

export interface JoinCircleResponse {
  circle_id: CircleId;
  member_id: MemberId;
  subscription_id: string | null;
  approval_url: string | null;
}

export interface NeedSubmissionRequest {
  member_id: MemberId;
  raw_text: string;
  locale: Locale;
}

export interface OrderProposeRequest {
  deterministic_seed: number;
}

export interface OrderApprovalRequest {
  member_id: MemberId;
}

export interface StressTestRequest {
  reserve_pcts: string[];
  n_sims: number;
  seed: number;
}

export interface StressTestResponse {
  result: StressTestResult;
  explanation: string;
}

export interface CopilotQuestionRequest {
  member_id: MemberId;
  question: string;
}

export interface SwapCreateRequest {
  request: SwapRequest;
}

export interface SwapApprovalRequest {
  approver_id: MemberId;
}

export interface PayNowRequest {
  member_id: MemberId;
}

export interface PayNowResponse {
  cycle_index: number;
  member_id: MemberId;
  order_id: string | null;
  capture_id: string | null;
  status: ContributionStatus;
}

export interface MediationApproveRequest {
  approving_member_id: MemberId | null;
}

export interface LedgerRow {
  row_id: string;
  cycle_index: number;
  member_id: MemberId;
  member_name: string;
  amount: string;
  status: ContributionStatus;
  source: ContributionSource;
  paypal_reference: string | null;
  created_at: string | null;
}

export interface LedgerResponse {
  circle_id: CircleId;
  rows: LedgerRow[];
  payouts: PayoutRow[];
  contributions_total: string;
  paid_out_total: string;
}

export interface PayoutRow {
  payout_id: string;
  cycle_index: number;
  recipient_id: MemberId;
  batch_id: string;
  amount: string;
  status: PayoutStatus;
  created_at: string | null;
}

export interface AuditResponse {
  circle_id: CircleId;
  decisions: AgentDecision[];
}

export interface ReliabilityRow {
  member_id: MemberId;
  display_name: string;
  score: ReliabilityScore;
}

export interface ReliabilityResponse {
  circle_id: CircleId;
  rows: ReliabilityRow[];
}

export interface WebhookAcknowledgement {
  received: boolean;
  duplicate: boolean;
}

export interface FastForwardRequest {
  to_cycle_index: number;
}

export interface ResetDemoResponse {
  reset: boolean;
  circle_id: CircleId;
}

export interface HealthResponse {
  status: SanityStatus;
  environment: Environment;
  paypal: SanityStatus;
  llm: SanityStatus;
  database: SanityStatus;
  version: string;
}
