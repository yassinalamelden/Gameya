// CANONICAL TYPESCRIPT CONTRACT — owned by Person 5. Mirrors backend/app/schemas/contracts.py.
// Money travels as a string ("100.00") so no float ever touches it.

export type Money = string;
export type Locale = "en" | "ar-EG";
export type CycleUnit = "WEEK" | "MONTH";
export type ContributionStatus = "PENDING" | "PAID" | "LATE" | "FAILED" | "COVERED";
export type CycleStatus =
  | "OPEN" | "COLLECTING" | "GRACE" | "DEFAULT_HANDLED" | "READY" | "PAYING_OUT" | "PAID_OUT";

export interface CircleSpec {
  name: string;
  contribution_amount: Money;
  cycle_unit: CycleUnit;
  size_n: number;
  start_date: string;
  reserve_pct: string;
}

export interface MemberSnapshot {
  member_id: string;
  display_name: string;
  locale: Locale;
  slot_index?: number | null;
}

export interface LedgerRow {
  cycle_index: number;
  member_id: string;
  member_name: string;
  due_date: string;
  amount: Money;
  status: ContributionStatus;
  method: "SUBSCRIPTION" | "ORDER" | "INVOICE" | "RESERVE" | null;
  paypal_ref_id: string | null;
  paid_at: string | null;
  recipient: boolean;
}

export interface ReliabilityFactor { feature: string; contribution: number; label: string }
export interface ReliabilityScore { member_id: string; p_late: number; top_factors: ReliabilityFactor[] }

export interface CircleAgentTurn {
  reply: string;
  spec: CircleSpec | null;
  needs_confirmation: boolean;
  paypal_product_id: string | null;
  paypal_plan_id: string | null;
}

export interface CopilotAnswer { answer: string; locale: Locale; sources: string[] }

export interface GoldenCircle {
  spec: CircleSpec;
  members: MemberSnapshot[];
  ledger: LedgerRow[];
}
