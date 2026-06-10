# Layer Collapse Tests v0.1

Mandatory tests that prove layers do not flatten into each other.

## Rules tested

| # | Rule | Test |
|---|------|------|
| 1 | MCVA cannot directly force GUARD=PROCEED | `test_mcva_cannot_short_circuit_guard` |
| 2 | ATAL pressure cannot make a claim true | `test_atal_pressure_cannot_set_claim_supported` |
| 3 | Similarity cannot become identity without evidence | `test_similarity_does_not_create_identity_link` |
| 4 | ReceptorEvent cannot bypass PERCEPT | `test_receptor_event_converts_to_percept` |
| 5 | FractalMemoryMap cannot erase contradiction scars | `test_fractal_memory_map_adds_contradiction_link` + scar preservation |

## Additional contract tests

- `test_receptor_event_does_not_set_guard`
- `test_basin_link_preserves_activation_id`
- `test_hold_region_not_returned_as_clean_attractor`
- `test_replay_validated_route_ranks_above_unvalidated_route`

## Run

```bash
python -m pytest tests/test_layer_collapse.py tests/test_fractal_memory_map.py tests/test_receptor_event_contract.py -q
```

Failure of any layer-collapse test blocks the next build round (Field App, visualization, Atlas builder).