"""Synthetic morphology samples for MCVA gate demo."""

from __future__ import annotations

from typing import Any


def _blank(w: int, h: int) -> list[list[int]]:
    return [[0 for _ in range(w)] for _ in range(h)]


def branching_trace(width: int = 32, height: int = 32) -> dict[str, Any]:
    grid = _blank(width, height)
    x, y = width // 2, height - 2
    grid[y][x] = 1
    directions = [(0, -1), (-1, 0), (1, 0)]
    for i in range(18):
        dx, dy = directions[i % 3]
        x += dx
        y += dy
        if 0 <= x < width and 0 <= y < height:
            grid[y][x] = 1
        if i == 6:
            x2, y2 = x, y
            for _ in range(8):
                x2 -= 1
                y2 -= 1
                if 0 <= x2 < width and 0 <= y2 < height:
                    grid[y2][x2] = 1
        if i == 12:
            x3, y3 = x, y
            for _ in range(6):
                x3 += 1
                y3 -= 1
                if 0 <= x3 < width and 0 <= y3 < height:
                    grid[y3][x3] = 1
    return {"name": "branching_trace", "grid": grid, "domain": "synthetic_branching"}


def crack_like_trace(width: int = 32, height: int = 32) -> dict[str, Any]:
    grid = _blank(width, height)
    x = width // 3
    for y in range(2, height - 2):
        grid[y][x] = 1
        if y % 4 == 0 and x + 1 < width:
            grid[y][x + 1] = 1
        if y % 7 == 0 and x - 1 >= 0:
            grid[y][x - 1] = 1
    return {"name": "crack_like_trace", "grid": grid, "domain": "synthetic_crack"}


def irregular_boundary(width: int = 32, height: int = 32) -> dict[str, Any]:
    grid = _blank(width, height)
    for x in range(4, width - 4):
        base = height // 2 + (1 if x % 3 == 0 else 0)
        for y in range(base, min(height - 2, base + 3)):
            grid[y][x] = 1
    return {"name": "irregular_boundary", "grid": grid, "domain": "synthetic_boundary"}


def noise_sample(width: int = 32, height: int = 32, seed: int = 13) -> dict[str, Any]:
    import random

    rng = random.Random(seed)
    grid = _blank(width, height)
    for y in range(height):
        for x in range(width):
            if rng.random() < 0.08:
                grid[y][x] = 1
    return {"name": "noise_non_diagnostic", "grid": grid, "domain": "synthetic_noise"}


def all_samples() -> list[dict[str, Any]]:
    return [
        branching_trace(),
        crack_like_trace(),
        irregular_boundary(),
        noise_sample(),
    ]