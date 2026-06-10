"""FractalMemoryMap — retrieval topology over CIRCUIT (not vector search)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

RelationType = Literal[
    "semantic",
    "causal",
    "temporal",
    "project",
    "contradiction",
    "recovery",
    "analogy",
    "operator",
    "morphology",
]

RELATION_TYPES: tuple[str, ...] = (
    "semantic",
    "causal",
    "temporal",
    "project",
    "contradiction",
    "recovery",
    "analogy",
    "operator",
    "morphology",
)


@dataclass
class FractalMemoryNode:
    node_id: str
    label: str
    glyph_id: str = ""
    salience: float = 0.5
    current_distance_from_center: float = 1.0
    replay_score: float = 0.0
    contradiction_score: float = 0.0
    uncertainty_score: float = 0.5
    domain_tags: list[str] = field(default_factory=list)
    source: str = ""
    links: list[str] = field(default_factory=list)
    hold_flag: bool = False
    fog_region: bool = False
    blocked: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FractalMemoryLink:
    source_node: str
    target_node: str
    relation_type: str
    strength: float = 0.5
    replay_validated: bool = False
    blocked: bool = False
    hold_flag: bool = False
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class FractalMemoryMap:
    """Multi-scale retrieval fabric over memory topology."""

    def __init__(self, center_node_id: str | None = None) -> None:
        self.center_node_id = center_node_id
        self.nodes: dict[str, FractalMemoryNode] = {}
        self.links: list[FractalMemoryLink] = []
        self.hold_regions: set[str] = set()

    def add_node(self, node: FractalMemoryNode) -> FractalMemoryNode:
        self.nodes[node.node_id] = node
        if self.center_node_id is None:
            self.center_node_id = node.node_id
        return node

    def add_link(self, link: FractalMemoryLink) -> FractalMemoryLink:
        if link.source_node not in self.nodes or link.target_node not in self.nodes:
            raise ValueError("Both link endpoints must exist as nodes.")
        self.links.append(link)
        src = self.nodes[link.source_node]
        tgt = self.nodes[link.target_node]
        if link.target_node not in src.links:
            src.links.append(link.target_node)
        if link.source_node not in tgt.links:
            tgt.links.append(link.source_node)
        return link

    def mark_hold_region(self, node_id: str) -> None:
        if node_id not in self.nodes:
            raise ValueError(f"Unknown node: {node_id}")
        node = self.nodes[node_id]
        node.hold_flag = True
        node.fog_region = True
        self.hold_regions.add(node_id)

    def add_contradiction_link(
        self,
        source_node: str,
        target_node: str,
        *,
        strength: float = 0.9,
        notes: str = "",
    ) -> FractalMemoryLink:
        for nid in (source_node, target_node):
            if nid in self.nodes:
                self.nodes[nid].contradiction_score = max(
                    self.nodes[nid].contradiction_score, strength
                )
        return self.add_link(
            FractalMemoryLink(
                source_node=source_node,
                target_node=target_node,
                relation_type="contradiction",
                strength=strength,
                replay_validated=False,
                blocked=False,
                hold_flag=False,
                notes=notes or "contradiction link — both endpoints preserved",
            )
        )

    def add_recovery_route(
        self,
        source_node: str,
        target_node: str,
        *,
        replay_validated: bool = True,
        notes: str = "",
    ) -> FractalMemoryLink:
        return self.add_link(
            FractalMemoryLink(
                source_node=source_node,
                target_node=target_node,
                relation_type="recovery",
                strength=0.8,
                replay_validated=replay_validated,
                blocked=False,
                hold_flag=False,
                notes=notes or "recovery route",
            )
        )

    def _attractor_score(self, node: FractalMemoryNode) -> float:
        """Transparent ranking — not vector search."""
        if node.hold_flag or node.fog_region or node.blocked:
            return -1.0
        if node.node_id in self.hold_regions:
            return -1.0
        distance_penalty = min(1.0, node.current_distance_from_center) * 0.25
        uncertainty_penalty = node.uncertainty_score * 0.2
        contradiction_penalty = node.contradiction_score * 0.15
        replay_bonus = node.replay_score * 0.35
        salience_bonus = node.salience * 0.45
        return salience_bonus + replay_bonus - distance_penalty - uncertainty_penalty - contradiction_penalty

    def nearest_active_attractors(self, limit: int = 5) -> list[dict[str, Any]]:
        """Rank nodes by transparent score. HOLD/fog nodes excluded."""
        ranked: list[tuple[float, FractalMemoryNode]] = []
        for node in self.nodes.values():
            score = self._attractor_score(node)
            if score < 0:
                continue
            ranked.append((score, node))
        ranked.sort(key=lambda x: x[0], reverse=True)
        return [
            {"node_id": n.node_id, "label": n.label, "attractor_score": round(s, 4), "node": n.to_dict()}
            for s, n in ranked[:limit]
        ]

    def to_dict(self) -> dict[str, Any]:
        return {
            "center_node_id": self.center_node_id,
            "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
            "links": [lnk.to_dict() for lnk in self.links],
            "hold_regions": sorted(self.hold_regions),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FractalMemoryMap:
        fmm = cls(center_node_id=data.get("center_node_id"))
        for nid, ndata in data.get("nodes", {}).items():
            fmm.add_node(FractalMemoryNode(**ndata))
        for ldata in data.get("links", []):
            fmm.links.append(FractalMemoryLink(**ldata))
            src = fmm.nodes[ldata["source_node"]]
            tgt = fmm.nodes[ldata["target_node"]]
            if ldata["target_node"] not in src.links:
                src.links.append(ldata["target_node"])
            if ldata["source_node"] not in tgt.links:
                tgt.links.append(ldata["source_node"])
        fmm.hold_regions = set(data.get("hold_regions", []))
        return fmm