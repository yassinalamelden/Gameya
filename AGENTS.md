# AGENTS.md — Gam'eya (PayPal AI Hackathon)

Operating manual for AI coding agents in this repo. The authoritative plan is
`Paypal Gameya.docx` / `.pdf`, kept **outside** the repo in `../planning/` so Office
files are never committed. Cite it by section number (§) instead of guessing.

## 1. Product in one line
AI-run rotating savings circles (gam'eya / tanda / susu) on PayPal: Subscriptions + Orders v2
collect, Invoicing chases, **Payouts** distributes, verified Webhooks are the truth.
Principle: **AI advises. Deterministic code moves the money. Humans approve who gets paid.**

## 2. Deadlines (Africa/Cairo)
- Contracts + fixtures frozen: **Wed 28 Oct 20:00**
- Code complete: **Fri 30 Oct 22:00**
- Extended tasks (Stress-Test, Slot-Swap Broker), video, Devpost submit: **Sat 31 Oct 22:00**
  (Extended features are flag-gated and cut at Sat 14:00 if not green.)

## 3. Ownership — never cross lanes (plan §8)
| Owner | Exclusive write scope | Must NOT |
| --- | --- | --- |
| **P1** Backend & PayPal | `backend/app/{main,config}.py`, `db/`, `api/`, `domain/`, `services/paypal/`, `requirements.txt`, `tests/unit_paypal/` | put LLM calls in routes; let any AI path reach Payouts |
| **P2** AI agents | `backend/app/ai/{llm,guardrails,toolkit_adapter,circle_agent,smart_chase,mediation,copilot,swap_broker}.py`, `ai/prompts/`, `tests/unit_ai/` | DB sessions, FastAPI, Payouts, frontend |
| **P3** Fair-order & ML | `backend/app/ai/{needs_extractor,fair_order}.py`, `backend/app/ml/**`, `tests/unit_ml/` | PayPal calls; LLM choosing the order or computing money |
| **P4** Frontend & AG Grid | `frontend/**` except `src/types/` | PayPal or LLM calls from the browser |
| **P5** Integration & submission | `backend/app/schemas/contracts.py`, `frontend/src/types/contracts.ts`, `shared/**`, `scripts/`, `docs/`, root files, `.github/**`, `tests/integration/` | feature code in other lanes |

Changing either contract file needs a PR approved by P5 **and** every affected consumer.

## 4. Hard rules
- Money is `Decimal` quantised to 0.01 `ROUND_HALF_UP`; `float` is rejected by the `Money` type.
- Only `domain/circle_engine.py` may call the Payouts client. `sender_batch_id = gameya-{circle_id}-{cycle_index}`.
- `PayPal-Request-Id` on every POST; webhook `event_id` processed at most once.
- Every AI output is logged as an `AgentDecisionRecord`. Member free text is wrapped as `<untrusted_member_text>`.
- Agent Toolkit allow-lists per agent are in plan §13.2. The toolkit has **no** Payouts tool — keep it that way.
- The PayPal AI-Toolkit IDE plugin is a dev aid only; never on the runtime path.

## 5. Commands
```bash
# Backend (Python 3.11)
cd backend && pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload          # http://localhost:8000/api/v1/health
ruff check . && ruff format --check . && mypy app
pytest tests -m "not sandbox"          # sandbox-marked tests hit real PayPal
# Frontend
cd frontend && npm install && npm run dev   # VITE_USE_MOCKS=true by default
# Full stack
docker-compose up --build
```
CI order: **gitleaks → ruff → mypy → pytest → tsc/build**. Branches: `feat/p1-…`, `feat/p2-…`, `chore/p5-…`;
Conventional Commits; 1 review, 2-hour SLA.
