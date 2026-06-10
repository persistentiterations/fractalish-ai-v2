# Grok Sandbox Report

## What was built
Local ASCII maze benchmark comparing 6 decision modes across 5 mazes and 25 seeds.

## How to run
- `python experiments/grok_sandbox/benchmark/run_maze_benchmark.py`
- `python experiments/grok_sandbox/maze/maze_runner.py`
- `cd experiments/grok_sandbox/dashboard && python -m http.server 8000`

## Strongest result
- easy_corridor / attractor_bias: success_rate=1.0

## Weakest result
- open_field_island / v3_6_core_local: success_rate=0.0

## Merge recommendation
**partial_merge** — Partially merge: maze benchmark harness and v3.6-local mode reporting into trunk examples; keep attractor/trail modes in experiments/ only.

Maze-running is a controlled benchmark for local decision-making, memory, revisits, traps, and constraint navigation. It is not a claim of general intelligence.