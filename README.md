# Gam'eya

**AI-run rotating savings circles on PayPal.**

Hundreds of millions of people save in rotating circles (*gam'eya* in Egypt, *tanda*, *susu*,
*chit fund*): N members pay a fixed amount every cycle and one member takes the whole pot.
They run on WhatsApp and trust, and break when someone pays late or disappears.
Gam'eya turns the circle into a PayPal-powered, AI-managed product.

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> **AI advises. Deterministic code moves the money. Humans approve anything that changes who gets paid.**

## AI components

| | Component | What it does |
| --- | --- | --- |
| 1 | Circle Agent | Organiser chats; agent creates the PayPal product + billing plan after confirmation. |
| 2 | Needs Extractor + Fair Order | Members describe needs (EN/AR); a deterministic solver picks the fairest payout order; AI explains it. |
| 3 | Smart Chase | Risk-aware nudges, then a PayPal invoice + reminder for late members. |
| 4 | Reliability Score | Explainable ML probability of paying late (no demographics). |
| 5 | Mediation Agent | Grace-period options (partial pay, swap, reserve) — always human-approved. |
| 6 | Circle Copilot | Ask anything about your circle in English or Egyptian Arabic (read-only). |
| 7 | Circle Stress-Test | Monte Carlo completion odds and a recommended reserve before launch. |
| 8 | Slot-Swap Broker | Matches and drafts payout-slot swaps; both members approve. |

## PayPal APIs

Catalog + Subscriptions (collect) · Orders v2 (catch-up) · Invoicing v2 (chase) · Payouts v1 (distribute) ·
Webhooks v1 (verified truth) · PayPal Agent Toolkit (agent actions).

## Getting started

```bash
cp .env.example .env        # fill in PayPal sandbox credentials + GEMINI_API_KEY
docker-compose up --build   # frontend :5173, backend :8000/api/v1/health
```

Local dev and team rules: see [AGENTS.md](AGENTS.md).

## For Judges

_Hosted URL, demo personas and sandbox buyer logins are added before submission (Sat 31 Oct 2026)._

## License

[MIT](LICENSE)
