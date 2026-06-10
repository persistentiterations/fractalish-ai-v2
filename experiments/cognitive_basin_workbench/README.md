# Cognitive Basin Workbench

Local-only experimental workbench that makes Cognitive Basin routines **visible and runnable**.

This is a **behavioral reality engine** — a traceable, stateful, ternary-gated cognition simulator. **Not consciousness.** Not a chatbot. Not an agent army.

## What it is

A basin state machine demo: run controlled events through PERCEPT → ATAL → RIGOR → CIRCUIT → GUARD → SERA → SessionGlyph and inspect each layer update.

## What it is not

- Not consciousness, sentience, self-awareness, or inner experience
- Not personhood or autonomous selfhood
- Not AGI or proof of intelligence
- Not an LLM wrapper, API, cloud service, or agent framework

State discipline before scale. HOLD before false closure. Operator sovereignty always.

## Doctrine

Natural Math generates process. Fractalish reads the shape left by process. Cognitive Basin preserves reasoning state across process.

## Routines

| Routine | Role |
|---------|------|
| **PERCEPT** | Sensory/intake — structured event token |
| **ATAL** | Pressure/state fields — **pressure is not truth** |
| **RIGOR** | Logic, contradiction, source, scope, overclaim checks |
| **CIRCUIT** | Memory routes, contradiction scars, recovery routes, open loops |
| **GUARD** | PROCEED / HOLD / REVERSE / WATCH |
| **SERA** | Cost, waste, runtime, unsupported-claim accounting |
| **SessionGlyph** | Carry-forward continuity state |

## Scenarios

1. **False Continuity** — prior HOLD; continue as settled → HOLD
2. **Contradiction Scar** — conflicting sources → scar + HOLD
3. **Recovery Route** — reload SessionGlyph after interrupt
4. **Morphology Claim Check** — MCVA/HOLD/AMCVA + RIGOR support check
5. **Overclaim Block** — grand claims blocked
6. **Pressure vs Truth** — high ATAL pressure, weak evidence → HOLD/WATCH
7. **Similarity vs Identity** — similarity warning; **similarity is not identity**
8. **Natural Math Process Trace** — process summary through basin guard

## Run

From repo root:

```bash
python experiments/cognitive_basin_workbench/run_workbench.py
```

Or:

```bash
python examples/demo_cognitive_basin_workbench.py
```

## Dashboard (local only)

```bash
cd experiments/cognitive_basin_workbench/dashboard
python -m http.server 8001
```

Open `http://localhost:8001/` — loads `../outputs/workbench_summary.json` only from localhost.

No CDN. No external libraries. No telemetry.

## Outputs

Written to `experiments/cognitive_basin_workbench/outputs/`:

- `scenario_<name>.json` / `.md` per scenario
- `workbench_summary.json` / `.md` aggregate

## Relation to Natural Math and Fractalish

- **Natural Math** — process engine (scenario 8 feeds trace summaries)
- **Fractalish / MCVA** — morphology readout (scenario 4)
- **Cognitive Basin** — state, guard, continuity across all scenarios

v3.6 remains trunk. v3.8 remains experimental branch — not used here.

## Next steps

- Interactive single-event runner in dashboard
- Side-by-side stateless vs basin comparison view
- Export SessionGlyph diff between scenarios