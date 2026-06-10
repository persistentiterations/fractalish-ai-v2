# FractalMemoryMap Contract v0.1

FractalMemoryMap is the **retrieval topology over CIRCUIT**. Canonical layer — not optional.

## Relationship to CIRCUIT

| CIRCUIT | FractalMemoryMap |
|---------|------------------|
| Stores scars, holds, routes, nodes | Organizes them for navigable retrieval |
| Writes on each activation | Ranks and links for replay and recovery |

## Node fields

`node_id`, `label`, `glyph_id`, `salience`, `current_distance_from_center`, `replay_score`, `contradiction_score`, `uncertainty_score`, `domain_tags`, `source`, `links`, `hold_flag`, `fog_region`, `blocked`

## Link relation types

`semantic`, `causal`, `temporal`, `project`, `contradiction`, `recovery`, `analogy`, `operator`, `morphology`

## Attractor ranking

`nearest_active_attractors()` uses a **transparent score**:

```
score = salience*0.45 + replay_score*0.35
      - distance*0.25 - uncertainty*0.2 - contradiction*0.15
```

HOLD/fog/blocked nodes return score &lt; 0 and are **excluded**.

Not vector search. Not embedding distance.

## Non-goals

- Vector nearest-neighbor retrieval
- Flat chat memory
- Erasing contradiction scars on merge
- Proof of consciousness

## Implementation

`fractalish_ai/fractal_memory_map.py` — minimal v0.1. Schema: `schemas/fractal_memory_map.schema.json`.