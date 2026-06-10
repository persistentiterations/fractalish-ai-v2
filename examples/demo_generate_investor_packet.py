"""Generate investor demo summary from local demo outputs."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_MD = ROOT / "outputs" / "investor_demo_summary.md"
OUTPUT_JSON = ROOT / "outputs" / "investor_demo_summary.json"

DEMOS = [
    ("demo_natural_math.py", ROOT / "outputs" / "demo_natural_math" / "natural_math_comparison.json"),
    ("demo_natural_math_v3_6_core.py", ROOT / "outputs" / "natural_math_v3_6_core_summary.json"),
    ("demo_mcva_gate.py", ROOT / "outputs" / "demo_mcva" / "mcva_records.json"),
    ("demo_full_runtime.py", ROOT / "outputs" / "demo_full_runtime" / "manifest.json"),
    ("demo_natural_math_attractor_bias.py", ROOT / "outputs" / "natural_math_attractor_bias_summary.json"),
    ("demo_natural_math_goal_directed_v3_8.py", ROOT / "outputs" / "natural_math_goal_directed_v3_8_summary.json"),
]


def _run(script: str) -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            [sys.executable, str(ROOT / "examples" / script)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=120,
        )
        ok = proc.returncode == 0
        return ok, (proc.stdout or "") + (proc.stderr or "")
    except Exception as exc:
        return False, str(exc)


def _load(path: Path) -> dict | list | None:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def main() -> int:
    ran: list[dict] = []
    for script, out_path in DEMOS:
        ok, log_tail = _run(script)
        ran.append({"script": script, "ok": ok, "output": str(out_path), "log_tail": log_tail.strip()[-500:]})

    nm = _load(ROOT / "outputs" / "demo_natural_math" / "natural_math_comparison.json")
    v36 = _load(ROOT / "outputs" / "natural_math_v3_6_core_summary.json")
    mcva = _load(ROOT / "outputs" / "demo_mcva" / "mcva_records.json")
    manifest = _load(ROOT / "outputs" / "demo_full_runtime" / "manifest.json")
    attractor = _load(ROOT / "outputs" / "natural_math_attractor_bias_summary.json")
    goal = _load(ROOT / "outputs" / "natural_math_goal_directed_v3_8_summary.json")
    decision = _load(ROOT / "outputs" / "demo_full_runtime" / "full_runtime_decision.json")

    sera = (decision or {}).get("sera_record", {}) if isinstance(decision, dict) else {}
    glyph_hash = (manifest or {}).get("session_glyph_hash", "n/a")

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "one_liner": (
            "Fractalish AI v0.1 demonstrates a local-first activation runtime that reads form, "
            "preserves uncertainty, compares against baselines, and records reasoning state."
        ),
        "demos_ran": ran,
        "natural_math_comparison": nm,
        "natural_math_v3_6_core": v36,
        "mcva_records": mcva,
        "full_runtime_manifest": manifest,
        "attractor_bias_experimental": attractor,
        "goal_directed_v3_8_experimental": goal,
        "sera_metrics": sera,
        "session_glyph_hash": glyph_hash,
        "non_claims": [
            "Not consciousness, AGI, or sentience",
            "Not medical diagnosis or disaster prediction",
            "Not proof of intelligence or model superiority",
            "v3.8 goal layer is experimental, not core",
        ],
        "funding_milestones": {
            "25k_50k": [
                "harden prototype",
                "package Android/offline demo",
                "improve Natural Math benchmarks",
                "add MCVA dataset registry",
                "create investor video",
            ],
            "100k_250k": [
                "build domain-specific morphology demos",
                "add phone/offline activation device",
                "expand SessionGlyph continuity",
                "create public dataset and sponsor-ready reports",
            ],
            "500k_plus": [
                "small engineering/research team",
                "edge-device build",
                "sensor integration",
                "MCVA atlas expansion",
                "safety/integrity runtime hardening",
            ],
        },
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = [
        "# Fractalish AI v0.1 — Investor Demo Summary",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        "## One-liner",
        summary["one_liner"],
        "",
        "## Demos executed",
    ]
    for item in ran:
        status = "OK" if item["ok"] else "FAIL/EXPERIMENTAL"
        lines.append(f"- `{item['script']}` — {status}")
    lines.extend(
        [
            "",
            "## Key results",
            f"- SessionGlyph hash: `{glyph_hash}`",
            f"- SERA runtime_ms: `{sera.get('runtime_ms', 'n/a')}`",
        ]
    )
    if nm:
        b = nm.get("baseline", {})
        m = nm.get("memory_enabled", {})
        lines.append(f"- Natural Math baseline revisits: {b.get('revisits')} (success={b.get('success')})")
        lines.append(f"- Natural Math memory revisits: {m.get('revisits')} (success={m.get('success')})")
    if v36:
        oracles = v36.get("oracle_results", {})
        passed = sum(1 for v in oracles.values() if v)
        lines.append(f"- v3.6 core oracles: {passed}/{len(oracles)} passed")
    if mcva:
        for rec in mcva[:4]:
            lines.append(f"- MCVA sample `{rec.get('descriptors', {}).get('sample_name')}`: {rec.get('decision')}")
    lines.extend(
        [
            "",
            "## Non-claims",
            *[f"- {c}" for c in summary["non_claims"]],
            "",
            "## Funding milestones",
            "### $25k–$50k",
            *[f"- {x}" for x in summary["funding_milestones"]["25k_50k"]],
            "### $100k–$250k",
            *[f"- {x}" for x in summary["funding_milestones"]["100k_250k"]],
            "### $500k+",
            *[f"- {x}" for x in summary["funding_milestones"]["500k_plus"]],
        ]
    )
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Investor packet written:\n  {OUTPUT_MD}\n  {OUTPUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())