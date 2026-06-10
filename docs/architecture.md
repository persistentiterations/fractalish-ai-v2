# Architecture — Fractalish AI v0.1

## Product definition

Fractalish AI is a local-first activation runtime for process-aware AI: it reads form, preserves uncertainty, compares against baselines, and records its reasoning state.

## Core doctrine

Read form carefully. Preserve uncertainty. Compare before claiming.

## Runtime flow

```
Input event
  → PERCEPT   (what arrived, from where, with what confidence)
  → ATAL      (pressure fields — not truth decisions)
  → RIGOR     (support, source, contradiction, scope checks)
  → CIRCUIT   (memory routes, scars, open loops)
  → GUARD     (PROCEED / HOLD / REVERSE / WATCH)
  → SERA      (cost, waste, efficiency)
  → SessionGlyph (carry-forward JSON state)
```

## Module definitions

| Module | Role |
|--------|------|
| **PERCEPT** | Structured percept token: source, modality, confidence, provenance |
| **ATAL** | Pressure tracking: coherence, uncertainty, threat, trust, fatigue, etc. |
| **RIGOR** | Integrity analyzers producing PASS/HOLD/REVERSE/WATCH findings |
| **CIRCUIT** | In-memory graph: memory nodes, contradiction scars, recovery routes |
| **GUARD** | Ternary gate consolidating RIGOR into one activation decision |
| **SERA** | Runtime cost and waste metrics |
| **SessionGlyph** | Deterministic carry-forward export with state hash |
| **Natural Math** | Grid growth demo: memoryless baseline vs trail-memory behavior |
| **MCVA Gate** | Morphology descriptors + MCVA/HOLD/AMCVA classification |

## Package layout

```
fractalish_ai/
  core_runtime.py    # wires all spine modules
  percept.py atal.py rigor.py circuit.py guard.py sera.py session_glyph.py
  natural_math/      # engine, profiles, runner
  mcva/              # descriptors, gate, synthetic_examples
```

## Constraints (v0.1)

- Python standard library only
- JSON records on disk
- No network calls
- No external APIs
- Runs on modest local hardware