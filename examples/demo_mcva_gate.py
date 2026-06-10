"""Demo: synthetic morphology samples through MCVA / HOLD / AMCVA gate."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fractalish_ai.mcva.gate import evaluate_gate
from fractalish_ai.mcva.synthetic_examples import all_samples

OUTPUT = ROOT / "outputs" / "demo_mcva"


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    samples = all_samples()
    baseline = samples[0]
    records = []

    print("Fractalish AI — MCVA Gate Demo")
    print()
    for sample in samples:
        record = evaluate_gate(sample, baseline={"source_hash": evaluate_gate(baseline).source_hash}).to_dict()
        records.append(record)
        print(f"{sample['name']}: {record['decision']} (confidence={record['confidence']})")
        if record.get("hold_reason"):
            print(f"  HOLD reason: {record['hold_reason']}")
        if record.get("amcva_reason"):
            print(f"  AMCVA reason: {record['amcva_reason']}")

    out_path = OUTPUT / "mcva_records.json"
    out_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print()
    print(f"Output: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())