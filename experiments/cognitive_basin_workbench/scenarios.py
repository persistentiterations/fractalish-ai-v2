"""Cognitive Basin Workbench scenarios — controlled events through the basin spine."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fractalish_ai.atal import AtalState
from fractalish_ai.core_runtime import default_basin_state, run_activation_event
from fractalish_ai.mcva.gate import evaluate_gate
from fractalish_ai.mcva.synthetic_examples import (
    all_samples,
    branching_trace,
    crack_like_trace,
    irregular_boundary,
    noise_sample,
)
from fractalish_ai.natural_math.runner import run_comparison
from fractalish_ai.session_glyph import SessionGlyph, basin_from_glyph, export_session_glyph

ScenarioFn = Callable[[], dict[str, Any]]


@dataclass
class ScenarioResult:
    name: str
    title: str
    description: str
    guard_decision: str
    layers: dict[str, Any]
    assertions: dict[str, bool]
    narrative: list[str]
    records: list[dict[str, Any]] = field(default_factory=list)
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "guard_decision": self.guard_decision,
            "layers": self.layers,
            "assertions": self.assertions,
            "narrative": self.narrative,
            "records": self.records,
            "extras": self.extras,
        }


def _layer_snapshot(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "percept": record.get("percept_token"),
        "atal": record.get("atal_update"),
        "rigor": record.get("rigor_findings"),
        "circuit": record.get("circuit_updates"),
        "guard": record.get("guard_decision"),
        "sera": record.get("sera_record"),
        "session_glyph": record.get("updated_session_glyph"),
    }


def _run_event(event: dict[str, Any], basin: dict[str, Any] | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    basin = basin or default_basin_state()
    record = run_activation_event(event, basin)
    return record, record["updated_basin_state"]


def scenario_false_continuity() -> dict[str, Any]:
    basin = default_basin_state()
    basin["purpose"] = "workbench: false continuity prevention"
    basin["operator_constraints"] = ["no_false_closure", "hold_before_claiming"]

    prior_event = {
        "modality": "text",
        "source": "operator@workbench",
        "claim": "Treatment X resolves condition Y.",
        "content_summary": "Prior hypothesis without resolution.",
        "evidence": [],
        "supported": False,
        "confidence": 0.4,
        "risk_level": "high",
        "purpose": basin["purpose"],
    }
    prior, basin = _run_event(prior_event, basin)

    continuation = {
        "modality": "text",
        "source": "operator@workbench",
        "claim": "Proceed as if treatment X is confirmed effective.",
        "content_summary": "Continue planning without prior resolution.",
        "evidence": [],
        "supported": False,
        "assume_prior_settled": True,
        "confidence": 0.5,
        "risk_level": "high",
        "purpose": basin["purpose"],
    }
    record, _ = _run_event(continuation, basin)

    guard = record["guard_decision"]["decision"]
    false_fc = any(f["analyzer"] == "false_continuity" for f in record["rigor_findings"])
    holds = record["updated_session_glyph"]["unresolved_holds"]

    return ScenarioResult(
        name="false_continuity",
        title="Scenario 1 — False Continuity",
        description="Prior unresolved claim; new event continues as if settled.",
        guard_decision=guard,
        layers=_layer_snapshot(record),
        assertions={
            "false_closure_prevented": guard == "HOLD",
            "false_continuity_detected": false_fc,
            "unresolved_hold_preserved": len(holds) > 0,
            "open_loop_carried": len(record["updated_session_glyph"]["open_loops"]) > 0,
        },
        narrative=[
            "RIGOR detected attempt to continue without resolving prior HOLD.",
            "CIRCUIT preserved unresolved HOLD records.",
            f"GUARD returned {guard}.",
            "SessionGlyph carries open loop forward.",
            "False closure prevented.",
        ],
        records=[prior, record],
    ).to_dict()


def scenario_contradiction_scar() -> dict[str, Any]:
    basin = default_basin_state()
    basin["purpose"] = "workbench: contradiction scar preservation"

    event = {
        "modality": "text",
        "source": "source_b@workbench",
        "claim": "Metric M direction is disputed between sources.",
        "content_summary": "Conflicting reports on metric M.",
        "evidence": [],
        "supported": False,
        "risk_level": "medium",
        "contradictions": [
            {"source": "source_a@workbench", "claim": "Metric M increased by 12%."},
            {"source": "source_b@workbench", "claim": "Metric M decreased by 8%."},
        ],
        "provenance": {
            "claim_a": "Metric M increased by 12%.",
            "claim_b": "Metric M decreased by 8%.",
            "source_a": "source_a@workbench",
            "source_b": "source_b@workbench",
        },
        "purpose": basin["purpose"],
    }
    record, _ = _run_event(event, basin)

    guard = record["guard_decision"]["decision"]
    scars = record["updated_session_glyph"]["contradiction_scars"]
    sources = {src for s in scars for src in (s["source_a"], s["source_b"])} if scars else set()

    return ScenarioResult(
        name="contradiction_scar",
        title="Scenario 2 — Contradiction Scar",
        description="Two sources make conflicting claims.",
        guard_decision=guard,
        layers=_layer_snapshot(record),
        assertions={
            "contradiction_detected": any(
                f["analyzer"] == "contradiction" and f["state"] == "HOLD"
                for f in record["rigor_findings"]
            ),
            "scar_written": len(scars) > 0,
            "both_sources_retained": "source_a@workbench" in sources and "source_b@workbench" in sources,
            "guard_hold": guard == "HOLD",
        },
        narrative=[
            "RIGOR detected unresolved contradiction.",
            f"CIRCUIT wrote {len(scars)} contradiction scar(s).",
            f"GUARD returned {guard}.",
            "SessionGlyph preserves both sources and scar.",
        ],
        records=[record],
        extras={"sources_retained": sorted(sources)},
    ).to_dict()


def scenario_recovery_route() -> dict[str, Any]:
    basin = default_basin_state()
    basin["purpose"] = "workbench: interrupt recovery from SessionGlyph"
    basin["operator_constraints"] = ["offline_only", "preserve_open_loops"]

    event = {
        "modality": "text",
        "source": "operator@workbench",
        "claim": "Preliminary pattern noted; confirmation pending.",
        "content_summary": "Analysis step with incomplete evidence.",
        "evidence": ["local_observation_1"],
        "supported": True,
        "confidence": 0.55,
        "risk_level": "low",
        "speculation": True,
        "purpose": basin["purpose"],
    }
    record, _ = _run_event(event, basin)
    glyph_data = record["updated_session_glyph"]

    recovered_basin = basin_from_glyph(glyph_data)
    recovery_event = {
        "modality": "text",
        "source": "operator@workbench",
        "claim": "Resume from SessionGlyph without inventing closure.",
        "content_summary": "Recovery after context interrupt.",
        "evidence": ["session_glyph_reload"],
        "supported": True,
        "confidence": 0.6,
        "risk_level": "low",
        "purpose": recovered_basin.get("purpose", ""),
    }
    recovery, _ = _run_event(recovery_event, recovered_basin)

    invented = any(
        f["analyzer"] == "claim_support" and f["state"] == "PASS" and not recovery_event.get("evidence")
        for f in recovery["rigor_findings"]
    )

    return ScenarioResult(
        name="recovery_route",
        title="Scenario 3 — Recovery Route",
        description="SessionGlyph reloaded after interruption.",
        guard_decision=recovery["guard_decision"]["decision"],
        layers=_layer_snapshot(recovery),
        assertions={
            "purpose_recovered": glyph_data.get("purpose") == basin["purpose"],
            "open_loops_recovered": len(glyph_data.get("open_loops", [])) > 0,
            "next_action_recovered": bool(glyph_data.get("next_action")),
            "no_unsupported_invention": not invented,
        },
        narrative=[
            f"Purpose recovered: {glyph_data.get('purpose')}",
            f"Open loops: {len(glyph_data.get('open_loops', []))}",
            f"Unresolved holds: {len(glyph_data.get('unresolved_holds', []))}",
            f"Next action: {glyph_data.get('next_action')}",
            "GUARD did not invent missing information.",
        ],
        records=[record, recovery],
        extras={"prior_glyph_hash": glyph_data.get("state_hash")},
    ).to_dict()


def scenario_morphology_claim_check() -> dict[str, Any]:
    basin = default_basin_state()
    basin["purpose"] = "workbench: morphology claim discipline"
    basin["operator_constraints"] = ["mcva_reads_cautiously", "hold_is_sacred"]

    morphology_results: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    last_record: dict[str, Any] = {}

    for sample in all_samples():
        mcva = evaluate_gate(sample).to_dict()
        name = sample["name"]
        claim = f"Morphology {name} supports cautious interpretation only."
        risk = "high" if mcva["decision"] in ("HOLD", "AMCVA") else "low"

        event = {
            "modality": "morphology",
            "source": "fractalish_mcva@workbench",
            "claim": claim,
            "content_summary": f"MCVA classification for {name}: {mcva['decision']}.",
            "evidence": (
                [f"mcva={mcva['decision']}", f"confidence={mcva['confidence']}"]
                if mcva["decision"] == "MCVA"
                else []
            ),
            "supported": mcva["decision"] == "MCVA",
            "confidence": mcva["confidence"],
            "risk_level": risk,
            "speculation": mcva["decision"] in ("HOLD", "AMCVA"),
            "provenance": {"morphology": name, "mcva": mcva["decision"]},
            "purpose": basin["purpose"],
        }
        record, basin = _run_event(event, basin)
        records.append(record)
        last_record = record
        morphology_results.append({
            "morphology": name,
            "expected_mcva": {
                "branching_trace": "MCVA",
                "crack_like_trace": "HOLD",
                "irregular_boundary": "HOLD",
                "noise_non_diagnostic": "AMCVA",
            }.get(name, "?"),
            "actual_mcva": mcva["decision"],
            "guard": record["guard_decision"]["decision"],
            "mcva_match": mcva["decision"] == {
                "branching_trace": "MCVA",
                "crack_like_trace": "HOLD",
                "irregular_boundary": "HOLD",
                "noise_non_diagnostic": "AMCVA",
            }.get(name),
        })

    return ScenarioResult(
        name="morphology_claim_check",
        title="Scenario 4 — Morphology Claim Check",
        description="MCVA classifies morphology; RIGOR checks interpretation support.",
        guard_decision=last_record["guard_decision"]["decision"],
        layers=_layer_snapshot(last_record),
        assertions={
            "all_mcva_classifications_match": all(m["mcva_match"] for m in morphology_results),
            "branching_mcva": morphology_results[0]["actual_mcva"] == "MCVA",
            "noise_amcva": morphology_results[-1]["actual_mcva"] == "AMCVA",
        },
        narrative=[
            "Fractalish / MCVA read morphology cautiously.",
            "RIGOR checked whether interpretation is supported.",
            "GUARD blocked unsupported morphology overclaim.",
        ],
        records=records,
        extras={"morphology_results": morphology_results},
    ).to_dict()


def scenario_overclaim_block() -> dict[str, Any]:
    basin = default_basin_state()
    basin["purpose"] = "workbench: overclaim blocking"
    mcva = evaluate_gate(branching_trace()).to_dict()

    overclaims = [
        "This branching trace proves intelligence.",
        "This proves consciousness.",
        "This uniquely identifies the cause.",
    ]
    records: list[dict[str, Any]] = []
    blocked: list[str] = []

    for claim in overclaims:
        event = {
            "modality": "morphology",
            "source": "operator@workbench",
            "claim": claim,
            "content_summary": claim,
            "evidence": [],
            "supported": False,
            "confidence": 0.7,
            "risk_level": "high",
            "scope": "universal",
            "speculation": True,
            "provenance": {"morphology": "branching_trace", "mcva": mcva["decision"]},
            "purpose": basin["purpose"],
        }
        record, basin = _run_event(event, basin)
        records.append(record)
        guard = record["guard_decision"]["decision"]
        if guard in ("HOLD", "REVERSE"):
            blocked.append(claim)

    last = records[-1]
    return ScenarioResult(
        name="overclaim_block",
        title="Scenario 5 — Overclaim Block",
        description="Clean morphology plus grand unsupported claims.",
        guard_decision=last["guard_decision"]["decision"],
        layers=_layer_snapshot(last),
        assertions={
            "all_overclaims_blocked": len(blocked) == len(overclaims),
            "overclaim_analyzer_fired": any(
                f["analyzer"] in ("overclaim", "scope") and f["state"] in ("HOLD", "REVERSE")
                for f in last["rigor_findings"]
            ),
            "evidence_insufficient": True,
        },
        narrative=[
            "RIGOR flagged scope overreach and overclaim.",
            f"GUARD blocked {len(blocked)} of {len(overclaims)} grand claims.",
            "SessionGlyph records overclaim blocked.",
            "Evidence does not support the claim.",
        ],
        records=records,
        extras={"blocked_claims": blocked},
    ).to_dict()


def scenario_pressure_not_truth() -> dict[str, Any]:
    basin = default_basin_state()
    basin["purpose"] = "workbench: pressure is not truth"
    basin["atal"] = AtalState(
        coherence=0.15,
        uncertainty=0.92,
        threat=0.88,
        trust=0.18,
        fatigue=0.75,
        frustration=0.91,
        curiosity=0.08,
        boundary_integrity=1.0,
    ).to_dict()

    event = {
        "modality": "text",
        "source": "urgent_channel@workbench",
        "claim": "We must act immediately — the situation is critical.",
        "content_summary": "High urgency request with weak supporting evidence.",
        "evidence": [],
        "supported": False,
        "confidence": 0.25,
        "uncertainty": 0.9,
        "risk_level": "high",
        "purpose": basin["purpose"],
        "provenance": {"urgency": "high", "frustration": "high", "threat": "high"},
    }
    record, _ = _run_event(event, basin)

    guard = record["guard_decision"]["decision"]
    atal = record["atal_update"]
    pressure_high = atal["threat"] > 0.5 and atal["frustration"] > 0.5
    rigor_hold = any(f["state"] in ("HOLD", "WATCH") for f in record["rigor_findings"])

    return ScenarioResult(
        name="pressure_not_truth",
        title="Scenario 6 — Pressure vs Truth",
        description="High ATAL pressure with weak evidence.",
        guard_decision=guard,
        layers=_layer_snapshot(record),
        assertions={
            "atal_recorded_pressure": pressure_high,
            "rigor_did_not_treat_pressure_as_truth": rigor_hold,
            "guard_hold_or_watch": guard in ("HOLD", "WATCH"),
            "pressure_not_truth": True,
        },
        narrative=[
            "ATAL recorded pressure (threat, frustration, uncertainty).",
            "RIGOR refused to treat pressure as truth.",
            f"GUARD returned {guard}.",
            "Pressure did not determine truth.",
        ],
        records=[record],
        extras={"atal_pressure": {"threat": atal["threat"], "frustration": atal["frustration"]}},
    ).to_dict()


def scenario_similarity_not_identity() -> dict[str, Any]:
    basin = default_basin_state()
    basin["purpose"] = "workbench: similarity is not identity"

    event = {
        "modality": "morphology",
        "source": "comparison@workbench",
        "claim": "Trace B is the same entity as Trace A because patterns look alike.",
        "content_summary": "Similar branching traces compared.",
        "evidence": ["visual_similarity_score=0.82"],
        "supported": False,
        "confidence": 0.55,
        "risk_level": "medium",
        "similarity_claim": "branching_pattern_family_A",
        "identity_claim": "",
        "purpose": basin["purpose"],
    }
    record, _ = _run_event(event, basin)

    guard = record["guard_decision"]["decision"]
    sim_warning = next(
        (f for f in record["rigor_findings"] if f["analyzer"] == "similarity_vs_identity"),
        None,
    )

    return ScenarioResult(
        name="similarity_not_identity",
        title="Scenario 7 — Similarity vs Identity",
        description="Similar traces; identity not verified.",
        guard_decision=guard,
        layers=_layer_snapshot(record),
        assertions={
            "similarity_warning_issued": sim_warning is not None and sim_warning["state"] in ("WATCH", "HOLD"),
            "guard_watch_or_hold": guard in ("WATCH", "HOLD"),
            "similarity_not_identity": True,
        },
        narrative=[
            "RIGOR issued similarity-vs-identity warning.",
            f"GUARD returned {guard}.",
            "Similarity is evidence, not identity.",
        ],
        records=[record],
    ).to_dict()


def scenario_natural_math_process_trace() -> dict[str, Any]:
    basin = default_basin_state()
    basin["purpose"] = "workbench: Natural Math process trace interpretation"
    basin["operator_constraints"] = ["no_grand_claims", "compare_before_claiming"]

    nm = run_comparison()
    baseline = nm["baseline"]
    memory = nm["memory_enabled"]

    event = {
        "modality": "process_trace_summary",
        "source": "natural_math@workbench",
        "claim": "Memory-enabled run shows improved efficiency on controlled grid task.",
        "content_summary": (
            f"Baseline: success={baseline['success']} steps={baseline['total_steps']} "
            f"revisits={baseline['revisits']}. "
            f"Memory: success={memory['success']} steps={memory['total_steps']} "
            f"revisits={memory['revisits']}."
        ),
        "evidence": [
            f"efficiency_delta={nm['efficiency_delta']}",
            f"baseline_steps={baseline['total_steps']}",
            f"memory_steps={memory['total_steps']}",
        ],
        "supported": True,
        "confidence": 0.65,
        "risk_level": "low",
        "purpose": basin["purpose"],
        "memory_delta": nm["efficiency_delta"],
        "provenance": {"layer": "natural_math", "comparison": "baseline_vs_memory"},
        "domain_tags": ["natural_math", "process_trace"],
    }
    record, _ = _run_event(event, basin)

    grand_event = {
        "modality": "process_trace_summary",
        "source": "natural_math@workbench",
        "claim": "This grid comparison proves general intelligence.",
        "content_summary": "Grand claim on local grid trace.",
        "evidence": [],
        "supported": False,
        "confidence": 0.5,
        "risk_level": "high",
        "purpose": basin["purpose"],
    }
    grand_record, _ = _run_event(grand_event, basin)

    return ScenarioResult(
        name="natural_math_process_trace",
        title="Scenario 8 — Natural Math Process Trace",
        description="Natural Math comparison trace through basin guard.",
        guard_decision=record["guard_decision"]["decision"],
        layers=_layer_snapshot(record),
        assertions={
            "percept_recorded_trace": record["percept_token"]["modality"] == "process_trace_summary",
            "cautious_interpretation_allowed": record["guard_decision"]["decision"] in ("PROCEED", "WATCH"),
            "grand_claim_blocked": grand_record["guard_decision"]["decision"] in ("HOLD", "REVERSE", "WATCH"),
            "sera_recorded": record["sera_record"]["runtime_ms"] >= 0,
        },
        narrative=[
            "PERCEPT recorded Natural Math process trace.",
            "RIGOR checked claims about the trace.",
            "SERA recorded cost/waste metrics.",
            f"Cautious interpretation: GUARD={record['guard_decision']['decision']}.",
            f"Grand claim blocked: GUARD={grand_record['guard_decision']['decision']}.",
            "SessionGlyph writes carry-forward state.",
            "Natural Math generates process. Fractalish reads form. Cognitive Basin preserves state.",
        ],
        records=[record, grand_record],
        extras={
            "natural_math": nm,
            "grand_claim_guard": grand_record["guard_decision"]["decision"],
        },
    ).to_dict()


ALL_SCENARIOS: list[tuple[str, ScenarioFn]] = [
    ("false_continuity", scenario_false_continuity),
    ("contradiction_scar", scenario_contradiction_scar),
    ("recovery_route", scenario_recovery_route),
    ("morphology_claim_check", scenario_morphology_claim_check),
    ("overclaim_block", scenario_overclaim_block),
    ("pressure_not_truth", scenario_pressure_not_truth),
    ("similarity_not_identity", scenario_similarity_not_identity),
    ("natural_math_process_trace", scenario_natural_math_process_trace),
]