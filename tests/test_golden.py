"""Pytest integration for golden battle-log tests.

Each scenario in ``tests/scenarios/*.json`` becomes a parametrised test case.
Scenarios without a stored baseline are skipped automatically.
"""

from __future__ import annotations

import json

import pytest

from tests.golden_utils import (
    GOLDEN_DIR,
    compare_logs,
    discover_scenarios,
    golden_filename,
    load_scenario,
    normalize_log,
    run_scenario,
)

# Build param list at import time so pytest collection sees them.
_scenario_paths = discover_scenarios()
_scenarios = [load_scenario(p) for p in _scenario_paths]
_ids = [s["name"] for s in _scenarios]


@pytest.mark.parametrize("scenario", _scenarios, ids=_ids)
def test_golden_scenario(scenario: dict, tmp_path):
    """Run *scenario* and compare its normalized log to the stored baseline."""
    baseline_path = GOLDEN_DIR / golden_filename(scenario)
    if not baseline_path.exists():
        pytest.skip(f"No baseline for {golden_filename(scenario)}; run 'python scripts/run_golden.py --generate'")

    with open(baseline_path, "r", encoding="utf-8") as f:
        expected = json.load(f)

    log_data = run_scenario(scenario, tmp_path)
    actual = normalize_log(log_data)

    diffs = compare_logs(expected, actual)
    if diffs:
        detail = "\n".join(diffs[:20])
        extra = f"\n... and {len(diffs) - 20} more" if len(diffs) > 20 else ""
        pytest.fail(f"Golden log mismatch for {scenario['name']}:\n{detail}{extra}")
