"""Simple morphology descriptors (stdlib only)."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any


def _foreground_cells(grid: list[list[int]]) -> list[tuple[int, int]]:
    cells = []
    for y, row in enumerate(grid):
        for x, val in enumerate(row):
            if val:
                cells.append((x, y))
    return cells


def _connected_components(grid: list[list[int]]) -> int:
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen: set[tuple[int, int]] = set()
    count = 0
    for y in range(h):
        for x in range(w):
            if not grid[y][x] or (x, y) in seen:
                continue
            count += 1
            stack = [(x, y)]
            while stack:
                cx, cy = stack.pop()
                if (cx, cy) in seen or cy < 0 or cy >= h or cx < 0 or cx >= w or not grid[cy][cx]:
                    continue
                seen.add((cx, cy))
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    stack.append((nx, ny))
    return count


def _boundary_roughness(grid: list[list[int]]) -> float:
    cells = _foreground_cells(grid)
    if not cells:
        return 0.0
    perimeter = 0
    for x, y in cells:
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if ny < 0 or ny >= len(grid) or nx < 0 or nx >= len(grid[0]) or not grid[ny][nx]:
                perimeter += 1
    area = len(cells)
    return perimeter / max(area, 1)


def _degree_map(grid: list[list[int]]) -> dict[tuple[int, int], int]:
    degrees: dict[tuple[int, int], int] = {}
    for x, y in _foreground_cells(grid):
        deg = 0
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1), (x + 1, y + 1), (x - 1, y - 1), (x + 1, y - 1), (x - 1, y + 1)):
            if 0 <= ny < len(grid) and 0 <= nx < len(grid[0]) and grid[ny][nx]:
                deg += 1
        degrees[(x, y)] = deg
    return degrees


def _endpoints_and_branches(grid: list[list[int]]) -> tuple[int, int]:
    degrees = _degree_map(grid)
    endpoints = sum(1 for d in degrees.values() if d == 1)
    branchpoints = sum(1 for d in degrees.values() if d >= 3)
    return endpoints, branchpoints


def _skeleton_length_proxy(grid: list[list[int]]) -> float:
    return float(len(_foreground_cells(grid)))


def _fractal_dimension_proxy(grid: list[list[int]]) -> float:
    cells = _foreground_cells(grid)
    if not cells:
        return 0.0
    w = len(grid[0])
    h = len(grid)
    scales = [2, 4, 8]
    counts = []
    for scale in scales:
        if scale > min(w, h):
            continue
        occupied = set()
        for x, y in cells:
            occupied.add((x // scale, y // scale))
        counts.append(len(occupied))
    if len(counts) < 2:
        return 1.0
    ratios = []
    for i in range(1, len(counts)):
        if counts[i] > 0:
            ratios.append(math.log(counts[i - 1] / counts[i]) / math.log(scales[i] / scales[i - 1]))
    return round(sum(ratios) / len(ratios), 3) if ratios else 1.0


def source_hash(sample: dict[str, Any]) -> str:
    payload = json.dumps(sample.get("grid", []), sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def extract_descriptors(sample: dict[str, Any]) -> dict[str, Any]:
    grid = sample["grid"]
    h = len(grid)
    w = len(grid[0]) if h else 0
    fg = _foreground_cells(grid)
    endpoints, branchpoints = _endpoints_and_branches(grid)
    return {
        "sample_name": sample.get("name", "unknown"),
        "domain": sample.get("domain", "unknown"),
        "width": w,
        "height": h,
        "foreground_density": round(len(fg) / max(w * h, 1), 4),
        "connected_component_count": _connected_components(grid),
        "roughness_proxy": round(_boundary_roughness(grid), 4),
        "endpoint_count": endpoints,
        "branchpoint_count": branchpoints,
        "skeleton_length_proxy": _skeleton_length_proxy(grid),
        "fractal_dimension_proxy": _fractal_dimension_proxy(grid),
        "source_hash": source_hash(sample),
    }