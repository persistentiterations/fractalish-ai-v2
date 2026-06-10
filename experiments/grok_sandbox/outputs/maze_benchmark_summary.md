# Maze Benchmark Summary

Generated: 2026-06-10T17:48:45.206390+00:00

Maze-running is a controlled benchmark for local decision-making, memory, revisits, traps, and constraint navigation. It is not a claim of general intelligence.

## Aggregate Results

| Maze | Mode | Success Rate | Mean Steps | Mean Revisits | Mean Efficiency |
|------|------|--------------|------------|-----------------|-----------------|
| branching_dead_ends | attractor_bias | 0% | 67 | 63 | 0.0002 |
| branching_dead_ends | attractor_plus_memory | 100% | 12 | 0 | 0.6127 |
| branching_dead_ends | memory_enabled | 100% | 12 | 0 | 0.6127 |
| branching_dead_ends | memoryless | 8% | 66.28 | 54.28 | 0.0004 |
| branching_dead_ends | trail_stigmergy | 100% | 12 | 0 | 0.6127 |
| branching_dead_ends | v3_6_core_local | 100% | 12 | 0 | 0.6127 |
| easy_corridor | attractor_bias | 100% | 8 | 0 | 1.0081 |
| easy_corridor | attractor_plus_memory | 100% | 8 | 0 | 1.0081 |
| easy_corridor | memory_enabled | 100% | 8 | 0 | 1.0081 |
| easy_corridor | memoryless | 52% | 43.6 | 35.8 | 0.1075 |
| easy_corridor | trail_stigmergy | 100% | 8 | 0 | 1.0081 |
| easy_corridor | v3_6_core_local | 100% | 8 | 0 | 1.0081 |
| open_field_island | attractor_bias | 100% | 12 | 0 | 0.6127 |
| open_field_island | attractor_plus_memory | 100% | 12 | 0 | 0.6127 |
| open_field_island | memory_enabled | 100% | 12 | 0 | 0.6127 |
| open_field_island | memoryless | 4% | 66.4 | 50.64 | 0.0004 |
| open_field_island | trail_stigmergy | 0% | 148 | 0 | 0.0068 |
| open_field_island | v3_6_core_local | 0% | 311 | 0 | 0.0032 |
| spiral | attractor_bias | 0% | 67 | 59 | 0.0002 |
| spiral | attractor_plus_memory | 0% | 127 | 0 | 0.0079 |
| spiral | memory_enabled | 0% | 128 | 0 | 0.0078 |
| spiral | memoryless | 0% | 67 | 55.68 | 0.0003 |
| spiral | trail_stigmergy | 0% | 128 | 0 | 0.0078 |
| spiral | v3_6_core_local | 0% | 121 | 0 | 0.0083 |
| trap_heavy | attractor_bias | 0% | 67 | 65 | 0.0002 |
| trap_heavy | attractor_plus_memory | 0% | 121 | 2 | 0.0028 |
| trap_heavy | memory_enabled | 0% | 166 | 0 | 0.006 |
| trap_heavy | memoryless | 0% | 67 | 55.92 | 0.0003 |
| trap_heavy | trail_stigmergy | 0% | 128 | 0 | 0.0078 |
| trap_heavy | v3_6_core_local | 0% | 121 | 0 | 0.0083 |

## Best mode per maze

- **open_field_island**: `attractor_bias`
- **trap_heavy**: `v3_6_core_local`
- **spiral**: `v3_6_core_local`
- **branching_dead_ends**: `attractor_plus_memory`
- **easy_corridor**: `attractor_bias`

## Interpretation

- **memory**: Memory reduced revisits in several runs; success gains depend on maze layout. Helped: 14 cases; harmed: 1 cases.
- **attractor_bias**: Attractor-bias uses experimental goal-field (nonlocal goal knowledge). Helped: 7 cases; harmed: 1 cases. May help easy corridors but can trap in trap-heavy mazes.
- **v3_6_core**: v3.6 core mode uses local neighbor sensing only — no global goal coordinates.
