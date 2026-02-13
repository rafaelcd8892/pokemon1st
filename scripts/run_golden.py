#!/usr/bin/env python3
"""Golden test runner — generate, update, and verify battle log baselines.

Usage:
    python scripts/run_golden.py                 # verify all baselines
    python scripts/run_golden.py --generate      # create missing baselines
    python scripts/run_golden.py --update        # regenerate all baselines
    python scripts/run_golden.py --scenario X    # run only scenario named X
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.golden_utils import (
    GOLDEN_DIR,
    compare_logs,
    discover_scenarios,
    golden_filename,
    load_scenario,
    normalize_log,
    run_scenario,
)


def _load_baseline(scenario: dict) -> dict | None:
    """Load an existing golden baseline, or return None."""
    path = GOLDEN_DIR / golden_filename(scenario)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_baseline(scenario: dict, log_data: dict) -> Path:
    """Save a normalized log as a golden baseline and return the path."""
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    path = GOLDEN_DIR / golden_filename(scenario)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2)
        f.write("\n")
    return path


def cmd_generate(scenarios: list[dict]) -> int:
    """Generate baselines for scenarios that don't already have one."""
    created = 0
    skipped = 0
    for scenario in scenarios:
        fname = golden_filename(scenario)
        if _load_baseline(scenario) is not None:
            print(f"  [EXISTS] {fname}")
            skipped += 1
            continue
        with tempfile.TemporaryDirectory() as tmp:
            log_data = run_scenario(scenario, Path(tmp))
        normalized = normalize_log(log_data)
        path = _save_baseline(scenario, normalized)
        print(f"  [CREATED] {fname}  ->  {path}")
        created += 1

    print(f"\nGenerated {created} baseline(s), {skipped} already existed.")
    return 0


def cmd_update(scenarios: list[dict]) -> int:
    """Regenerate all baselines unconditionally."""
    for scenario in scenarios:
        fname = golden_filename(scenario)
        with tempfile.TemporaryDirectory() as tmp:
            log_data = run_scenario(scenario, Path(tmp))
        normalized = normalize_log(log_data)
        path = _save_baseline(scenario, normalized)
        print(f"  [UPDATED] {fname}  ->  {path}")

    print(f"\nUpdated {len(scenarios)} baseline(s).")
    return 0


def cmd_verify(scenarios: list[dict]) -> int:
    """Verify each scenario against its stored baseline."""
    passed = 0
    failed = 0
    skipped = 0
    failure_details: list[tuple[str, list[str]]] = []

    print("Golden Test Verification")
    print("=" * 40)

    for scenario in scenarios:
        fname = golden_filename(scenario)
        baseline = _load_baseline(scenario)

        if baseline is None:
            print(f"  [SKIP] {fname} (no baseline)")
            skipped += 1
            continue

        with tempfile.TemporaryDirectory() as tmp:
            log_data = run_scenario(scenario, Path(tmp))
        actual = normalize_log(log_data)

        diffs = compare_logs(baseline, actual)
        if not diffs:
            print(f"  [PASS] {fname}")
            passed += 1
        else:
            print(f"  [FAIL] {fname}")
            for d in diffs[:10]:
                print(f"         {d}")
            if len(diffs) > 10:
                print(f"         ... and {len(diffs) - 10} more difference(s)")
            failed += 1
            failure_details.append((fname, diffs))

    print("=" * 40)
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped")

    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Golden test runner for battle log baselines"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--generate", action="store_true",
        help="Create baselines for scenarios that don't have one yet",
    )
    mode.add_argument(
        "--update", action="store_true",
        help="Regenerate all baselines (approve new output)",
    )
    parser.add_argument(
        "--scenario", type=str, default=None,
        help="Run only the scenario with this name",
    )
    args = parser.parse_args()

    # Discover and load scenarios
    scenario_paths = discover_scenarios()
    if not scenario_paths:
        print("No scenario files found in tests/scenarios/")
        return 1

    scenarios = [load_scenario(p) for p in scenario_paths]

    # Optional filter
    if args.scenario:
        scenarios = [s for s in scenarios if s["name"] == args.scenario]
        if not scenarios:
            print(f"No scenario named '{args.scenario}' found.")
            return 1

    # Dispatch
    if args.generate:
        return cmd_generate(scenarios)
    elif args.update:
        return cmd_update(scenarios)
    else:
        return cmd_verify(scenarios)


if __name__ == "__main__":
    raise SystemExit(main())
