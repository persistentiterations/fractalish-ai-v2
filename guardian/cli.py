#!/usr/bin/env python3
"""Guardian Intake Gateway CLI — local-first, no network."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fractalish_ai.guardian.intake import GuardianGateway


def _print_result(result: dict) -> None:
    intake = result["intake"]
    scan = result["scan"]
    decision = result["decision"]
    lifecycle = result["lifecycle"]
    print(f"intake_id:      {intake.intake_id}")
    print(f"file:           {intake.file_name}")
    print(f"channel:        {intake.source_channel}")
    print(f"risk_score:     {scan.risk_score}")
    print(f"risk_level:     {scan.risk_level}")
    print(f"decision:       {decision.decision}")
    print(f"lifecycle:      {lifecycle.lifecycle_state}")
    print(f"raw_visible:    {scan.raw_model_visible}")
    print(f"sanitized_vis:  {scan.sanitized_model_visible}")
    if scan.prompt_injection_flags:
        print(f"prompt_flags:   {', '.join(scan.prompt_injection_flags)}")
    if scan.tool_poisoning_flags:
        print(f"tool_flags:     {', '.join(scan.tool_poisoning_flags)}")
    print(f"outputs:        {result['paths']['scan_report']}")


def cmd_scan(path: Path) -> int:
    gateway = GuardianGateway()
    result = gateway.scan_file(path)
    _print_result(result)
    gateway._rebuild_dashboard_summary()
    return 0


def cmd_scan_email(path: Path) -> int:
    gateway = GuardianGateway()
    result = gateway.scan_email(path)
    _print_result(result)
    gateway._rebuild_dashboard_summary()
    return 0


def cmd_scan_mcp(path: Path) -> int:
    gateway = GuardianGateway()
    result = gateway.scan_mcp(path)
    _print_result(result)
    gateway._rebuild_dashboard_summary()
    return 0


def cmd_run_demo() -> int:
    gateway = GuardianGateway()
    results = gateway.run_demo()
    print(f"Guardian demo complete — {len(results)} intakes processed.")
    for result in results:
        intake = result["intake"]
        decision = result["decision"]
        scan = result["scan"]
        print(f"  {intake.file_name:40s} {scan.risk_level:8s} {decision.decision}")
    summary = gateway.output_root / "dashboard_summary.json"
    print(f"Dashboard summary: {summary}")
    return 0


def cmd_purge_demo() -> int:
    gateway = GuardianGateway()
    report = gateway.purge_demo()
    print(json.dumps(report, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Guardian Intake Gateway v0.1")
    sub = parser.add_subparsers(dest="command", required=True)

    scan_p = sub.add_parser("scan", help="Scan a local file drop")
    scan_p.add_argument("path", type=Path)

    email_p = sub.add_parser("scan-email", help="Scan a mock .eml email intake")
    email_p.add_argument("path", type=Path)

    mcp_p = sub.add_parser("scan-mcp", help="Scan an MCP resource descriptor")
    mcp_p.add_argument("path", type=Path)

    sub.add_parser("run-demo", help="Scan all sample artifacts and build dashboard summary")
    sub.add_parser("purge-demo", help="Purge generated outputs for one intake (demo)")

    args = parser.parse_args(argv)
    if args.command == "scan":
        return cmd_scan(args.path)
    if args.command == "scan-email":
        return cmd_scan_email(args.path)
    if args.command == "scan-mcp":
        return cmd_scan_mcp(args.path)
    if args.command == "run-demo":
        return cmd_run_demo()
    if args.command == "purge-demo":
        return cmd_purge_demo()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())