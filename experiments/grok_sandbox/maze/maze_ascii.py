"""ASCII maze parsing and path visualization."""

from __future__ import annotations

from dataclasses import dataclass


WALL = "#"
OPEN = "."
START = "S"
GOAL = "G"
PATH = "*"
VISITED = "o"
DEAD = "x"


@dataclass
class MazeGrid:
    name: str
    rows: list[str]
    width: int
    height: int
    start: tuple[int, int]
    goal: tuple[int, int]
    walls: set[tuple[int, int]]

    def in_bounds(self, pos: tuple[int, int]) -> bool:
        x, y = pos
        return 0 <= x < self.width and 0 <= y < self.height

    def is_open(self, pos: tuple[int, int]) -> bool:
        return pos not in self.walls and self.in_bounds(pos)

    def neighbors(self, pos: tuple[int, int]) -> list[tuple[int, int]]:
        x, y = pos
        candidates = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        return [c for c in candidates if self.is_open(c)]


def parse_maze(name: str, ascii_text: str) -> MazeGrid:
    lines = [line.rstrip("\n") for line in ascii_text.strip().splitlines() if line.strip()]
    height = len(lines)
    width = max(len(line) for line in lines)
    walls: set[tuple[int, int]] = set()
    start = (0, 0)
    goal = (0, 0)
    normalized: list[str] = []

    for y, line in enumerate(lines):
        padded = line.ljust(width)
        normalized.append(padded)
        for x, ch in enumerate(padded):
            if ch == WALL:
                walls.add((x, y))
            elif ch == START:
                start = (x, y)
            elif ch == GOAL:
                goal = (x, y)

    return MazeGrid(name=name, rows=normalized, width=width, height=height, start=start, goal=goal, walls=walls)


def render_path(
    maze: MazeGrid,
    path: list[tuple[int, int]],
    visited: set[tuple[int, int]],
    dead_ends: set[tuple[int, int]] | None = None,
) -> str:
    dead_ends = dead_ends or set()
    path_set = set(path)
    lines: list[str] = []
    for y, row in enumerate(maze.rows):
        chars: list[str] = []
        for x, ch in enumerate(row):
            pos = (x, y)
            if pos == maze.start:
                chars.append(START)
            elif pos == maze.goal:
                chars.append(GOAL)
            elif pos in path_set:
                chars.append(PATH)
            elif pos in dead_ends:
                chars.append(DEAD)
            elif pos in visited:
                chars.append(VISITED)
            elif ch == WALL:
                chars.append(WALL)
            else:
                chars.append(OPEN)
        lines.append("".join(chars))
    return "\n".join(lines)