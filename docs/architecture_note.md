# Architecture Note — Fractalish AI v0.1

Fractalish AI v0.1 is a local-first prototype for process-aware, morphology-aware, state-disciplined AI infrastructure. It integrates Natural Math as a local bounded process engine, Fractalish / MCVA as a morphology readout and uncertainty-preserving classification layer, and Cognitive Basin Core as a traceable, stateful, ternary-gated reasoning-state runtime.

Natural Math generates process. Fractalish reads the shape left by process. Cognitive Basin preserves reasoning state across process.

## Layer model

| Layer | Role | v0.1 status |
|-------|------|-------------|
| **Natural Math v3.6** | Closed-system process engine (growth, pressure, bifurcation) | Core trunk |
| **Fractalish / MCVA** | Morphology readout: MCVA / HOLD / AMCVA | Core readout |
| **Cognitive Basin Core** | PERCEPT → ATAL → RIGOR → CIRCUIT → GUARD → SERA → SessionGlyph | Core guard spine |

## Data flow

```
Process event (Natural Math trace, morphology sample, or text claim)
  → PERCEPT
  → ATAL (pressure only — not truth)
  → RIGOR (integrity analyzers)
  → CIRCUIT (memory routes, scars, open loops)
  → GUARD (PROCEED / HOLD / REVERSE / WATCH)
  → SERA (cost accounting)
  → SessionGlyph (carry-forward state)
```

Integrated path (`demo_integrated_basin_morphology.py`):

1. Natural Math runs a bounded grid comparison (process).
2. MCVA classifies morphology descriptors (form readout).
3. Cognitive Basin evaluates claims about the morphology with RIGOR and GUARD.

## Core vs experimental

**Core (trunk):**

- Natural Math v3.6 closed-system core and 8/8 oracles
- MCVA gate with conservative HOLD posture
- Cognitive Basin spine modules

**Experimental (branch — not default, not proof):**

- Natural Math v3.8 goal-directed layer (`experimental_goal_directed.py`)
- Attractor bias demos
- Maze benchmark sandbox (`experiments/grok_sandbox/`)

## Non-claims

This prototype is a traceable, stateful, ternary-gated cognition simulator. It is not consciousness, not an agent army, not a chatbot skin. State discipline before scale. HOLD before false closure. Operator sovereignty always.

See [non_claims.md](non_claims.md).