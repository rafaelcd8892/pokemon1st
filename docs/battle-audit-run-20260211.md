# Battle Audit Run - 2026-02-11

## Scope
- Implemented robustness fixes for logging/audit contract.
- Ran 6v6 audits and validated generated JSON logs.

## Fixes Implemented in This Iteration
1. Self-target normalization in move logs
- `Rest`, `Reflect`, `Substitute` (and other self-target utility moves) now log actor as target.

2. Duplicate charge move logging removed
- Charge-turn moves no longer emit duplicated `move` entries in the same turn.

3. Explicit move outcome support
- `move.details.result` added (default `resolved`, supports values like `charge_start`, `blocked_by_invulnerability`).

4. Faint causality improved
- Self-KO moves (`Explosion`, `Self Destruct`) now mark `self_faint=true` in move details.
- Validator accepts this as valid faint cause.

5. Switch audit robustness
- Post-switch HP snapshot is logged immediately after `switch`.
- Validator checks immediate post-switch HP instead of any HP in turn.

6. Legacy migration improvements
- Migrator fixes self-target moves, marks self-faint for self-KO moves, and deduplicates repeated move entries.

## 6v6 Audit Findings

### Run 1
- Battle ID: `battle_20260211_084317`
- Validator status: PASS (`No anomalies found`)
- Functional anomaly detected manually:
  - `Horn Drill` dealt normal damage (`1`) instead of OHKO semantics.
  - Evidence:
    - Log line: `logs/battles/battle_20260211_084317.log` (turn 6)
    - JSON event: `(turn=6, move='Horn Drill', damage=1)` in `logs/battles/battle_20260211_084317.json`
  - Root cause:
    - `OHKO_MOVES` recognized `Horn-Drill` but runtime move names are normalized to `Horn Drill`.

### Resolution Applied
- Updated OHKO recognition to accept both variants (`Horn-Drill`, `Horn Drill`) and include `Fissure` explicitly.
- Added regression test to guarantee `Horn Drill` uses OHKO path.

### Run 2 (post-fix validation)
- Battle ID: `battle_20260211_084453`
- Validator status: PASS (`No anomalies found`)
- OHKO anomaly recurrence: none detected in this run.

## Test Status
- Full suite after changes: `229 passed`.

## Remaining Gaps / Next Hardening Steps
1. Emit non-`resolved` `result` values for all fail/no-op paths
- Example: already-active screen/substitute, status blocked by immunity, etc.

2. Add an audit report command
- Generate per-log summary: turn count, move outcome distribution, anomaly counts, suspicious long battles.

3. Add deterministic 6v6 smoke in CI
- Seeded random battle to keep observability regressions reproducible.
