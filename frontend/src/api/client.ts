// Typed API client. VITE_USE_MOCKS=true serves shared/fixtures with simulated latency.
import golden from "../../../shared/fixtures/json/golden_circle.json";
import type { GoldenCircle, LedgerRow } from "../types/contracts";

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS !== "false";
const BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error(`${r.status} ${path}`);
  return (await r.json()) as T;
}

export async function getLedger(circleId: string): Promise<LedgerRow[]> {
  if (USE_MOCKS) {
    await delay(400);
    return (golden as GoldenCircle).ledger;
  }
  return get<LedgerRow[]>(`/circles/${circleId}/ledger`);
}
