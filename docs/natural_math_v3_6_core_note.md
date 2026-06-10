# Natural Math v3.6 Core Note

Natural Math v3.6 is the **trunk** process engine. v3.8 goal-directed behavior is experimental branch only.

## v3.6 includes

- Closed finite-energy system
- Looped update with local agency
- EXTEND / SENSE / RESTRICT operators
- Pressure, bifurcation, conflict resolution
- Strict equality handling
- 8 test oracles
- Finite termination theorem
- Local information theorem

## v3.6 excludes (do not merge into core)

- Gravity, light, nutrients, trails, reactivation, CONSERVE
- Selection, reproduction, open-system energy input
- Target-gradient, goal-directed waypoints, adaptation

## Invariants (must not weaken)

- No negative energy
- Finite support
- No co-location
- Parent DAG
- Closed-system energy non-increasing
- Pressure timing and termination bound
- Local information bound

## Verification

```bash
python examples/demo_natural_math_v3_6_core.py
python -m pytest tests/test_natural_math_v3_6_oracles.py -q
```

All 8 oracles must pass.