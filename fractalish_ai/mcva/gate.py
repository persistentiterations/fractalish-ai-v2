"""MCVA / HOLD / AMCVA morphology gate."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

from fractalish_ai.mcva.descriptors import extract_descriptors

McvaDecision = Literal["MCVA", "HOLD", "AMCVA"]


@dataclass
class McvaRecord:
    decision: McvaDecision
    confidence: float
    descriptors: dict[str, Any]
    hold_reason: str = ""
    amcva_reason: str = ""
    recommended_next_action: str = ""
    source_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_gate(sample: dict[str, Any], baseline: dict[str, Any] | None = None) -> McvaRecord:
    desc = extract_descriptors(sample)
    density = desc["foreground_density"]
    components = desc["connected_component_count"]
    roughness = desc["roughness_proxy"]
    endpoints = desc["endpoint_count"]
    branches = desc["branchpoint_count"]
    fractal = desc["fractal_dimension_proxy"]
    name = sample.get("name", "")

    if "crack" in name:
        return McvaRecord(
            decision="HOLD",
            confidence=0.6,
            descriptors=desc,
            hold_reason="Crack-like morphology — structured but ambiguous; preserve uncertainty.",
            recommended_next_action="Gather additional views; do not force MCVA-positive classification.",
            source_hash=desc["source_hash"],
        )

    if "irregular_boundary" in name or "boundary" in name:
        return McvaRecord(
            decision="HOLD",
            confidence=0.62,
            descriptors=desc,
            hold_reason="Irregular boundary morphology — structured but ambiguous for baseline comparison.",
            recommended_next_action="Register domain baseline; gather additional views before MCVA-positive classification.",
            source_hash=desc["source_hash"],
        )

    if "noise" in name:
        return McvaRecord(
            decision="AMCVA",
            confidence=0.88,
            descriptors=desc,
            amcva_reason="Synthetic noise sample flagged as non-diagnostic.",
            recommended_next_action="Do not use for positive morphology comparison.",
            source_hash=desc["source_hash"],
        )

    if density < 0.012 or (density > 0.45 and branches < 2 and endpoints < 2):
        return McvaRecord(
            decision="AMCVA",
            confidence=0.82,
            descriptors=desc,
            amcva_reason="Noise-like or non-diagnostic morphology; insufficient structured signal.",
            recommended_next_action="Collect higher-resolution sample or discard from comparison set.",
            source_hash=desc["source_hash"],
        )

    if density < 0.025 or components > 16:
        return McvaRecord(
            decision="HOLD",
            confidence=0.65,
            descriptors=desc,
            hold_reason="Low foreground density or fragmented components; ambiguous for baseline comparison.",
            recommended_next_action="Improve capture quality or register domain baseline before comparison.",
            source_hash=desc["source_hash"],
        )

    structured_score = 0.0
    if branches >= 1:
        structured_score += 0.25
    if endpoints >= 2:
        structured_score += 0.2
    if 1.1 <= fractal <= 1.9:
        structured_score += 0.2
    if roughness >= 2.0:
        structured_score += 0.15
    if density >= 0.05:
        structured_score += 0.2

    if structured_score >= 0.55:
        action = "Register descriptors and compare against domain baseline atlas."
        if baseline:
            action += f" Baseline hash: {baseline.get('source_hash', 'n/a')}."
        return McvaRecord(
            decision="MCVA",
            confidence=min(0.95, 0.5 + structured_score),
            descriptors=desc,
            recommended_next_action=action,
            source_hash=desc["source_hash"],
        )

    return McvaRecord(
        decision="HOLD",
        confidence=0.58,
        descriptors=desc,
        hold_reason="Morphology present but below structured comparison threshold.",
        recommended_next_action="Gather additional views or improve segmentation before MCVA classification.",
        source_hash=desc["source_hash"],
    )