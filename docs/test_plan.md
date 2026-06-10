# Test Plan — Fractalish AI v0.1

## Goal

Compare stateless prompt-style handling vs Fractalish activation runtime on the same bounded task.

## Demos as smoke tests

| Demo | Command | Expected |
|------|---------|----------|
| Activation | `python examples/demo_activation.py` | Guard PROCEED or WATCH; JSON written |
| Natural Math | `python examples/demo_natural_math.py` | Baseline vs memory comparison printed |
| MCVA Gate | `python examples/demo_mcva_gate.py` | 4 samples classified; JSON written |
| Full Runtime | `python examples/demo_full_runtime.py` | SessionGlyph + manifest written |
| False Continuity | `python examples/demo_1_false_continuity.py` | HOLD; false_continuity finding |
| Contradiction Scar | `python examples/demo_2_contradiction_scar.py` | Scar written; HOLD |
| Recovery Route | `python examples/demo_3_recovery_route.py` | Purpose/next_action recovered |
| Integrated | `python examples/demo_integrated_basin_morphology.py` | Three-layer summary written |
| v3.6 Oracles | `python -m pytest tests/test_natural_math_v3_6_oracles.py -q` | 8/8 pass |
| Unit tests | `python -m pytest -q` | guard, rigor, recovery pass |

## Comparison metrics

Run the same synthetic morphology + Natural Math task twice:

1. **Stateless mode** — treat outputs as isolated answers with no carry-forward
2. **Fractalish mode** — run `demo_full_runtime.py` and reload SessionGlyph

Measure:

- false closure rate (claims made without evidence)
- lost constraint rate (operator rules dropped)
- contradiction preservation (both sources retained)
- source retention (key_sources in SessionGlyph)
- HOLD accuracy (unsupported claims gated)
- recovery after interruption (glyph reload restores purpose)
- cost per valid continuation (SERA runtime_ms, hold_count)
- unsupported claim count

## v0.1 acceptance

- [ ] All four demos run without network
- [ ] HOLD appears as a real guard state
- [ ] MCVA ternary decisions exported as JSON
- [ ] SessionGlyph includes state_hash
- [ ] Natural Math shows measurable baseline vs memory delta
- [ ] No external dependencies beyond Python stdlib