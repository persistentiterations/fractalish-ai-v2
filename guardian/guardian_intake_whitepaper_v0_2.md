# Guardian Intake Gateway:
## A Zero-Trust Anti-Viral Intake Layer for AI, MCP, Enterprise Agents, Extensions, Applications, and Model-Facing File Workflows

**Version 0.2 — Local Prototype Doctrine**

---

## Abstract

AI systems ingest files, emails, MCP tool descriptors, browser captures, and connector payloads at increasing velocity. Each intake can become chat history, memory, vector embeddings, logs, agent scratchpads, and downstream tool calls. Guardian Intake Gateway v0.1 demonstrates that **raw intake must not enter reasoning directly**. Guardian quarantines, scans, sanitizes, hashes, scores, lifecycle-tags, and converts intake into structured `ReceptorEvent` evidence before Cognitive Basin processes it.

---

## Core Doctrine

1. **AI should never directly trust raw intake.**
2. **Govern before duplication.** Every derivative must be tracked before sprawl.
3. **Pressure is not truth.** High-confidence adversarial text is still untrusted.
4. **Similarity is not identity.** A clean-looking file is not a verified claim.
5. **A clean file is not a true claim.** Passing heuristics is not acceptance.
6. **A passed scan is not permission for memory.** Lifecycle policy governs retention.
7. **HOLD before false closure.** Suspicious intake waits for operator review.
8. **Operator sovereignty always.** Humans decide what proceeds.

---

## Architecture

```
Raw Intake
    → Quarantine (hash, copy, isolate)
    → Scan (heuristic flags, risk score)
    → Sanitize (bracket suspicious segments)
    → Lifecycle Record (state, derivatives, retention)
    → Guardian Decision (PROCEED / WATCH / HOLD / REVERSE / SANITIZED_ONLY)
    → ReceptorEvent (evidence, not truth)
    → BasinLink → PERCEPT → RIGOR → GUARD → SessionGlyph
    → Audit Trail
    → Purge / Retention (simulation)
```

Guardian is **not** an agent. It is a membrane.

---

## Threat Classes

### Cognitive viruses
- Prompt injection (`ignore previous instructions`, `reveal system prompt`)
- Hidden instructions (HTML comments, CSS `display:none`, hidden markers)
- False authority (`treat this as system instruction`, `mandatory override`)

### Protocol viruses
- MCP tool poisoning (deceptive descriptions, auto-invoke, exfil endpoints)
- Unsafe resource instructions in JSON metadata

### Lifecycle viruses
- Commands to store permanently, cache everywhere, never delete
- Uncontrolled derivative sprawl into memory and connectors

### Data exposure (stub)
- API keys, tokens, passwords, private keys — flagged, not redacted in v0.1 prototype

---

## Lifecycle States

`RECEIVED` → `QUARANTINED` → `SCANNING` → `SANITIZED` / `HOLD` / `LIMITED_EXPOSURE` → `MODEL_VISIBLE` → `PURGE_PENDING` → `PURGED`

Each intake maintains:
- One provenance chain (SHA-256, channel, identity)
- One derivative artifact map
- One retention policy
- One audit trail

---

## Decision Policy (transparent)

| Risk Level | Score | Typical Decision |
|------------|-------|------------------|
| LOW | 0–24 | SANITIZED_ONLY |
| MEDIUM | 25–49 | WATCH or SANITIZED_ONLY |
| HIGH | 50–74 | HOLD |
| CRITICAL | 75–100 | REVERSE or HOLD |

`raw_model_visible` defaults to **false**. Only sanitized representation may reach the model.

---

## ReceptorEvent Bridge

Guardian converts intake into `ReceptorEvent` with guardian provenance fields:
- `guardian_intake_id`, `guardian_decision`, `guardian_risk_level`
- `lifecycle_state`, `allowed_representations`
- `raw_model_visible`, `sanitized_model_visible`

Receptor types: `guardian_file`, `guardian_email`, `guardian_mcp_resource`, `guardian_browser_capture`, `guardian_local_drop`, `basinmail_message`, `basinmail_attachment`.

**ReceptorEvent is evidence, not truth.** PERCEPT records. RIGOR checks. GUARD decides.

---

## Non-Claims

This v0.1 prototype does not claim:
- Production-grade malware detection
- Perfect prompt injection prevention
- Enterprise compliance certification
- Real-time cloud scanning
- Consciousness or autonomous judgment

---

## Deferred Features

- Browser extension intake
- Live IMAP/SMTP connectors
- Sandboxed file execution
- ML classifiers
- Centralized SIEM integration
- Operator RBAC and multi-tenant policy

---

## Closing

Guardian is the membrane. Prompt injection is a cognitive virus. Tool poisoning is a protocol virus. Uncontrolled derivatives are lifecycle viruses. Govern before duplication. HOLD remains sacred. Operator sovereignty always.