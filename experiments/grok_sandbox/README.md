# Grok Sandbox — Maze Benchmark

Isolated experimental area. **Does not modify the v2 trunk.**

Maze-running is used here as a controlled benchmark for local decision-making, memory, revisits, traps, and constraint navigation. It is not a claim of general intelligence.

## What this tests

| Mode | Label |
|------|-------|
| `memoryless` | A — memoryless local search |
| `memory_enabled` | B — visited-cell memory |
| `v3_6_core_local` | C — v3.6-style local finite-energy (EXTEND/SENSE/RESTRICT/HOLD) |
| `attractor_bias` | D — experimental goal-field (uses goal position — NOT core) |
| `attractor_plus_memory` | E — attractor + memory (experimental) |
| `trail_stigmergy` | F — trail deposit/evaporation (experimental) |

**v3.6 trunk** (`fractalish_ai/natural_math/v3_6_core.py`) is unchanged. Maze mode C is a *local maze adaptation*, not a replacement for lattice core.

## Mazes

1. `easy_corridor`
2. `branching_dead_ends`
3. `trap_heavy`
4. `open_field_island` (optional)
5. `spiral` (optional)

## Commands

From repo root:

```bash
python experiments/grok_sandbox/maze/maze_runner.py
python experiments/grok_sandbox/benchmark/run_maze_benchmark.py
```

Dashboard (local only — no CDN, no external libraries):

```bash
cd experiments/grok_sandbox/dashboard
python -m http.server 8000
# open http://localhost:8000/index.html
```

The dashboard uses `fetch()` against local JSON when served by `python -m http.server`. Regenerate `maze_benchmark_summary.json` via the benchmark script before previewing.

## Outputs

**Committed examples (markdown summaries):**

- `outputs/maze_benchmark_summary.md`
- `outputs/grok_sandbox_report.md`
- `outputs/sample_maze_runs/` — small sample traces only

**Gitignored (regenerate locally):**

- `outputs/maze_runs/*.json` and `*.txt` (bulk per-run traces)
- `outputs/maze_benchmark_summary.json` and `.csv`
- `outputs/grok_sandbox_report.json`

## Benchmark interpretation (25 seeds per maze/mode)

- **Memory helped strongly** in easy corridor, branching dead ends, and open field island — fewer revisits and higher success on structured layouts.
- **Attractor-only** helped in easy/open layouts but **failed badly** in branching dead-end layouts (goal-field loops without memory).
- **Attractor-plus-memory** rescued some attractor-only failures by combining goal bias with revisit avoidance.
- **Trail/stigmergy** helped in some layouts (e.g. branching) but **harmed** in open-field-island (trails accumulate without clear payoff).
- **Spiral and trap-heavy** remained hard — several modes still show 0% success; this is honest benchmark signal, not a hidden failure.
- **Useful because it shows both success and failure** — modes can be compared without overclaiming general intelligence.

## Non-claims

Not AGI, consciousness, medical diagnosis, disaster prediction, or proof of intelligence.