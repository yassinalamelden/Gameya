/**
 * Canonical cross-team contract types.
 * Currently holds the Leash types (Interface 3). Other teams' types will be
 * added alongside these. Money/Decimal values are strings; datetimes are ISO strings.
 */

export type GuardAction =
  | "RELEASE_POT_PAYOUT"
  | "SEND_CHASE_INVOICE"
  | "SEND_INVOICE_REMINDER"
  | "APPLY_SLOT_SWAP";

export type LeashDecision = "ALLOW" | "ASK" | "DENY";

export type LeashPreset = "HANDS_OFF" | "STANDARD" | "STRICT";

export interface LeashThresholds {
  email_change_window_days: number;
  reminder_min_gap_hours: number;
  max_reminders_per_cycle: number;
  swap_cooldown_hours: number;
  swap_near_payout_hours: number;
  high_risk_p_late: string;
}

export interface LeashPolicy {
  circle_id: string;
  version: number;
  preset: LeashPreset;
  thresholds: LeashThresholds;
  no_auto_chase_member_ids: string[];
}

export interface GuardResult {
  decision: LeashDecision;
  rule_ids: string[];
  reason: string;
  decision_id: string;
}

export interface LeashInboxRecipient {
  member_id: string;
  name: string;
  payout_email: string | null;
}

export type LeashSubjectType = "payout" | "chase_plan" | "swap";

export interface LeashInboxItem {
  decision_id: string;
  action: GuardAction;
  subject_type: LeashSubjectType;
  subject_id: string;
  cycle_index: number | null;
  recipient: LeashInboxRecipient | null;
  amount: string | null;
  rule_ids: string[];
  reason: string;
  created_at: string;
}

export interface LeashInbox {
  items: LeashInboxItem[];
}

export interface LeashDecisionRow {
  decision_id: string;
  circle_id: string;
  policy_version: number;
  action: GuardAction;
  subject_type: LeashSubjectType;
  subject_id: string;
  decision: LeashDecision;
  rule_ids: string[];
  amount: string | null;
  reason: string;
  actor: "leash" | "organiser";
  status: "FINAL" | "OPEN" | "APPROVED" | "REJECTED";
  created_at: string;
  resolved_at: string | null;
}

export interface LeashResolveRequest {
  note?: string | null;
}

export interface LeashResolveResponse {
  decision_id: string;
  approves: string;
  actor: "organiser";
  result: Record<string, unknown> | null;
}

export type LeashErrorCode =
  | "ORGANISER_ONLY"
  | "LEASH_DECISION_NOT_FOUND"
  | "LEASH_ALREADY_RESOLVED"
  | "LEASH_STALE_DECISION"
  | "LEASH_POLICY_INVALID"
  | "LEASH_DISABLED";

export interface LeashApiError {
  error: {
    code: LeashErrorCode;
    message: string;
    details: Record<string, unknown>;
    request_id: string;
  };
}
