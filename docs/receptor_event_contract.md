# ReceptorEvent Contract v0.1

ReceptorEvent is **structured intake, not truth**.

## Flow

```
InfinitySight / MNMVE / FieldNode / ReceptorCase
  → ReceptorEvent
  → BasinLink
  → to_percept_event()
  → PERCEPT (via core_runtime)
```

## Required fields

`receptor_id`, `receptor_type`, `event_id`, `timestamp`, `source`, `modality`, `raw_reference`, `raw_summary`, `normalized_payload`, `confidence`, `uncertainty`, `noise_estimate`, `provenance`, `domain_tags`, `privacy_scope`, `local_only`, `suggested_basin_tags`, `possible_claims`, `missing_context`, `receptor_notes`

## Receptor types

`human_note`, `file_drop`, `maze_trace`, `natural_math_run`, `morphology_trace`, `sensor_stub`, `multimodal_stub`, `infinitysight_token`

## Rules

- `to_percept_event()` outputs PERCEPT-compatible dict with `supported=False` by default
- ReceptorEvent must **not** set GUARD
- `possible_claims` are candidates for RIGOR — not accepted facts
- Must not bypass PERCEPT

## Vendor-neutral naming

Use Fractalish Field System / FieldNode / ReceptorCase naming. Never proprietary assistant or consciousness device labels.

## Implementation

`fractalish_ai/receptors.py`, `fractalish_ai/basin_link.py`. Schema: `schemas/receptor_event.schema.json`, `schemas/basin_link.schema.json`.