# Minimal Runtime Spec — Cognitive Basin Core v0.1

## Pipeline

`run_activation_event(event, basin_state) → decision_record`

| Stage | Input | Output |
|-------|-------|--------|
| PERCEPT | Raw event dict | Percept token (event_id, modality, source, confidence, provenance, …) |
| ATAL | Percept + prior ATAL | Updated pressure fields (coherence, uncertainty, threat, trust, …) |
| RIGOR | Event payload | List of RigorFinding (PASS / HOLD / REVERSE / WATCH) |
| CIRCUIT | Percept + RIGOR + GUARD | Memory nodes, scars, holds, open loops, recovery routes |
| GUARD | RIGOR findings | GuardResult (PROCEED / HOLD / REVERSE / WATCH) |
| SERA | Timing + counts | Cost record (runtime_ms, hold_count, contradiction_count, …) |
| SessionGlyph | Circuit + purpose | Carry-forward JSON with deterministic state_hash |

## Decision states

- **PROCEED** — Supported low-risk continuation
- **HOLD** — Missing evidence, contradiction, or overclaim; no forced closure
- **REVERSE** — Boundary violation; revert path
- **WATCH** — Mild uncertainty; reduced commitment

## Key data structures

- `basin_state` — activation_id, purpose, operator_constraints, atal, circuit
- `activation_event` — modality, source, claim, evidence, risk_level, provenance
- `session_glyph` — open_loops, unresolved_holds, contradiction_scars, recovery_routes, next_action, state_hash

## JSON outputs

Demos write decision records to `demo_outputs/` and `outputs/`. Schemas live in `schemas/`.