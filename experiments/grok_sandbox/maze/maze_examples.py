"""Built-in ASCII mazes for sandbox benchmark."""

from __future__ import annotations

MAZES: dict[str, str] = {
    "easy_corridor": """
###########
#S.......G#
###########
""".strip(),
    "branching_dead_ends": """
###########
#S..#....G#
#.#.#.#####
#.#...#...#
#.#####.#.#
#.......#.#
###########
""".strip(),
    "trap_heavy": """
#############
#S.#.#.#...G#
#.#.#.#.###.#
#...#...#.#.#
###.#####.#.#
#...#...#.#.#
#.###.#.#.#.#
#.....#...#.#
#############""".strip(),
    "open_field_island": """
###############
#S...........G#
#..#######....#
#..#.....#....#
#..#..#..#....#
#..#..#..#....#
#..#.....#....#
#..#######....#
###############""".strip(),
    "spiral": """
#############
#S#.......#.#
#.#.#####.#.#
#.#.#...#.#.#
#.#.#.#.#.#.#
#...#.#.#...#
#####.#.#####
#.....#....G#
#############
""".strip(),
}


def list_maze_names() -> list[str]:
    return list(MAZES.keys())


def get_maze(name: str) -> str:
    if name not in MAZES:
        raise KeyError(f"Unknown maze: {name}")
    return MAZES[name]