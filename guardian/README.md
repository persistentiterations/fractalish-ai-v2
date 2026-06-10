# Guardian Intake Gateway v0.1

Guardian Intake Gateway is a **local-first, zero-trust intake membrane** for AI systems. Untrusted files, emails, MCP resources, browser captures, and local uploads do not enter reasoning directly — they pass through quarantine, scan, sanitize, lifecycle tagging, and ReceptorEvent bridging first.

## What it is

- A prototype intake layer between raw artifacts and Cognitive Basin / PERCEPT / RIGOR / GUARD
- Transparent heuristic scanners (prompt injection, hidden instructions, tool poisoning, DLP stubs)
- Lifecycle governance: one intake record, one provenance chain, one derivative map, one audit trail
- Local JSON outputs and a static dashboard — no cloud, no network, no model API

## What it is not

- Not a production malware scanner
- Not an agent or chatbot
- Not a model wrapper
- Not a claim of perfect safety
- Not a live email server, browser extension, or enterprise connector

## Why AI needs intake protection

Raw intake can carry prompt injection, hidden instructions, tool poisoning, and lifecycle sprawl commands. Without a membrane, these artifacts multiply into chat history, memory, vector stores, connector caches, logs, and agent scratchpads.

## Why lifecycle control matters

Secure intake is not only about blocking hostile files. It is about governing every derivative before the AI ecosystem duplicates it. Guardian tracks quarantine copies, sanitized text, scan reports, ReceptorEvents, decisions, lifecycle records, and audit entries — with a purge demo for retention simulation.

## Threat model (v0.1)

| Threat | Guardian response |
|--------|-------------------|
| Prompt injection | Flag, score, HOLD/REVERSE |
| Hidden instructions | Flag in HTML/CSS/comments |
| Tool poisoning (MCP) | Flag descriptor metadata |
| False authority claims | Flag, never treat as system instruction |
| DLP / secrets patterns | Flag (stub) |
| Lifecycle sprawl | Flag permanent-store commands |
| Raw model exposure | Default `raw_model_visible: false` |

## Intake channels

1. **Local file drop** — `guardian/samples/file_drop/`
2. **Email mock** — `.eml` parsed with stdlib `email`
3. **MCP resource** — JSON tool/resource descriptors
4. **Browser capture mock** — text simulating page + hidden prompts

## Commands

Run from repo root (`fractalish-ai/`):

```bash
python guardian/cli.py run-demo
python guardian/cli.py scan guardian/samples/file_drop/benign_note.txt
python guardian/cli.py scan guardian/samples/file_drop/prompt_injection.txt
python guardian/cli.py scan-email guardian/samples/email/session_upload.eml
python guardian/cli.py scan-mcp guardian/samples/mcp/poisoned_tool_descriptor.json
python guardian/cli.py purge-demo
```

## Output files

Generated under `guardian/outputs/` (gitignored):

| Directory | Contents |
|-----------|----------|
| `quarantine/` | Raw quarantine copies |
| `sanitized/` | Sanitized text + JSON metadata |
| `reports/` | Intake, scan, decision, basin summary |
| `receptor_events/` | ReceptorEvent JSON |
| `lifecycle/` | Lifecycle records with derivative map |
| `audit/` | Global + per-intake JSONL audit logs |
| `dashboard_summary.json` | Bundled summary for dashboard |

## Dashboard preview

```bash
python guardian/cli.py run-demo
cd guardian/dashboard
python -m http.server 8005
# open http://localhost:8005
```

The dashboard reads `../outputs/dashboard_summary.json`. A local server is required (browser CORS).

## Cognitive Basin integration

Guardian produces `ReceptorEvent` objects compatible with `fractalish_ai/receptors.py` and passes them through `BasinLink` / `receptor_event_to_decision_record`. GUARD receives risk level and missing context; suspicious intakes route to HOLD or WATCH. SessionGlyph continuity preserves activation context.

## Non-claims

- No production security guarantee
- No consciousness or AGI claims
- Heuristic detection only — not ML-based classification
- Purge demo affects generated outputs only, never source samples

## Deferred production features

- Live email ingestion, browser extension, enterprise connectors
- Real malware scanning, sandbox execution
- Auth, operator RBAC, centralized audit store
- Vector DB integration, cloud telemetry
- Model API calls for content classification

## Doctrine

Guardian is the membrane. Raw intake does not enter reasoning. Govern before duplication. A clean file is not a true claim. A passed scan is not permission for memory. HOLD remains sacred. Operator sovereignty always.