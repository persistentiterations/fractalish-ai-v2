# Cognitive Basin Core Note

Cognitive Basin Core preserves reasoning state across process. It is the guard and continuity layer — not a chatbot, not an agent army.

## Modules

**PERCEPT** — Structured percept token from incoming events (source, modality, confidence, provenance).

**ATAL** — Pressure fields (coherence, uncertainty, threat, trust, fatigue, frustration, curiosity, boundary_integrity). ATAL does not decide truth; it records pressure.

**RIGOR** — Integrity analyzers: claim support, source presence, contradiction, scope, speculation, similarity-vs-identity, overclaim, false continuity.

**CIRCUIT** — In-memory JSON graph: memory nodes, contradiction scars, recovery routes, trust channels, open loops, unresolved HOLD records.

**GUARD** — Ternary gate consolidating RIGOR into PROCEED / HOLD / REVERSE / WATCH.

**SERA** — Cost and waste: runtime_ms, hold_count, reverse_count, unsupported_claim_count, contradiction_count.

**SessionGlyph** — Carry-forward export with activation_id, purpose, operator_constraints, open_loops, unresolved_holds, contradiction_scars, recovery_routes, key_sources, next_action, state_hash.

## Demo scenarios

1. **False continuity** — Prior unresolved HOLD + attempt to continue as settled → HOLD
2. **Contradiction scar** — Conflicting sources → scar written, both retained, HOLD
3. **Recovery route** — Reload SessionGlyph after interrupt → purpose, open loops, next action recovered

HOLD is sacred. Operator sovereignty always.