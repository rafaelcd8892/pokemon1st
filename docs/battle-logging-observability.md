# Battle Logging Observability Notes

## Context
Recent battle logs in `logs/battles/` looked too shallow: mostly HP snapshots and faint events, without move-by-move detail.

Example symptom from recent files:
- `battle_20260211_074714.json` contained only `info`, `hp`, `faint` actions.
- No `move`, `miss`, `effect`, `status`, or `stat_change` entries.

## Root Cause
The code had two logger instances in team battles:

1. `engine/battle.py` logs detailed actions through the **global logger** returned by `get_battle_logger()`.
2. `engine/team_battle.py` created a **separate local logger** via `BattleLogger(...)`.

As a result:
- Detailed logs written by `engine/battle.py` were sent to the global logger (often `None` or a different instance).
- Team battle files only got entries explicitly written by `TeamBattle` (`hp`, `faint`, `info`, etc.).

## Fix Implemented
`TeamBattle` now starts logging through `start_battle_log(...)` so both modules share the same instance.

### Code-level change
- File: `engine/team_battle.py`
- Replaced:
  - `self.battle_logger = BattleLogger(enabled=enable_battle_log)`
- With:
  - `self.battle_logger = start_battle_log(enabled=enable_battle_log)`

Also, battle closure now uses `end_battle_log(...)` (global lifecycle) instead of calling `self.battle_logger.end_battle(...)` directly.

## Why This Matters
With a single logger instance:
- Move usage is recorded (`action_type: "move"`).
- Critical/effectiveness/miss data survives into the `.json` log.
- End-of-turn effects are traceable (`action_type: "effect"`).
- You can replay and debug battle outcomes from logs rather than console output.

## Regression Protection
Added integration coverage in:
- `tests/test_battle_integration_regressions.py`

Specifically:
- `test_team_battle_writes_detailed_move_entries`

This ensures `TeamBattle` logs include detailed move entries, preventing this split-logger regression from reappearing.

## Operational Checklist for Future Iterations
When touching battle logging, verify all items:

1. Only one active logger instance per battle.
2. `engine/battle.py` and `engine/team_battle.py` write to that same instance.
3. A sample `.json` file contains, at minimum:
   - `move`
   - `hp`
   - `faint`
4. If applicable, ensure presence of:
   - `miss`
   - `effect`
   - `status`
   - `stat_change`
5. Run:
   - `pytest -q tests/test_battle_integration_regressions.py`
   - `pytest -q`

## Recommended Next Hardening
1. Add a small log schema validator test to assert required keys per action type.
2. Include turn-phase markers (`start_turn`, `end_turn`) as explicit JSON entries for replay tooling.
3. Optionally add deterministic battle seeds to correlate runs and logs exactly.
