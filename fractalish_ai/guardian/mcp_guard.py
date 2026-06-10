"""MCP resource / tool descriptor intake guard."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fractalish_ai.guardian.scanners import scan_mcp_descriptor


def load_mcp_resource(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def scan_mcp_file(path: Path) -> dict[str, Any]:
    data = load_mcp_resource(path)
    flags = scan_mcp_descriptor(data)
    flags["resource_name"] = data.get("name", path.stem)
    return flags