# Codebase Audit Report

Date: 2026-02-20
Repository: `PokemonGen1`
Audited by: Codex

## Scope
- Full repository review (engine, models, data loader, scripts, tests).
- Automated checks:
  - `pytest -q`
  - `python3 -m compileall -q .`
  - `python3 scripts/run_golden.py`
  - `python3 scripts/batch_battle.py --battles 50 --format 3v3 --seed 42`

## Overall Rating
`8/10`

Rationale:
- Strong baseline quality: fast test suite (`449 passed`), golden tests pass, deterministic battle outputs are stable.
- Main gaps are concentrated in clause correctness and audit/analysis identity handling (same-species-on-both-sides scenarios).

## Findings By Priority

### P1 (High)

1. Sleep Clause incorrectly blocks legal sleep when existing sleep is self-induced (Rest).
- File: `engine/clauses.py:21`
- Evidence:
  - Docstring says self-induced sleep should not count (`engine/clauses.py:25`).
  - Implementation blocks any alive sleeping Pokemon (`engine/clauses.py:38`).
- Impact:
  - Stadium-style clause enforcement is mechanically incorrect.
  - Can reject legal sleep moves in cup formats with Sleep Clause enabled.
- Repro:
```bash
python3 - <<'PY'
from models.ruleset import BattleClauses
from models.enums import Status, Type, MoveCategory
from models.pokemon import Pokemon
from models.stats import Stats
from models.move import Move
from engine.clauses import check_sleep_clause

m=Move('Tackle',Type.NORMAL,MoveCategory.PHYSICAL,40,100,35,35)
p1=Pokemon('RestMon',[Type.NORMAL],Stats(100,50,50,50,50),[m],use_calculated_stats=False)
p1.status=Status.SLEEP; p1.sleep_counter=2  # simulate Rest sleep
p2=Pokemon('AwakeMon',[Type.NORMAL],Stats(100,50,50,50,50),[m],use_calculated_stats=False)
print(check_sleep_clause([p1,p2], BattleClauses(sleep_clause=True)))
PY
```
Expected: `True`; Actual: `False`.

### P2 (Medium)

2. Battle summary merges same-species Pokemon across sides.
- File: `engine/battle_logger.py:531`
- Evidence:
  - Summary map is keyed only by `pokemon` name (`engine/battle_logger.py:533`, `engine/battle_logger.py:535`).
  - Both P1 and P2 `Pikachu` are aggregated into one row.
- Impact:
  - Post-battle analytics become incorrect in mirror matchups.
  - Damages auditability of per-Pokemon reports.

3. Log validator emits false warnings in same-name battles.
- File: `scripts/validate_battle_log.py:193`
- Evidence:
  - `prevented` set tracks only `pokemon` name (`scripts/validate_battle_log.py:195`, `scripts/validate_battle_log.py:198`).
  - During batch run, warning `prevented_but_attacked` appeared even though prevented and attacking entities were different sides with same species name.
- Impact:
  - Noise in anomaly reports.
  - Can hide real regressions by reducing signal quality.

4. Logger lifecycle is not exception-safe in battle loop.
- Files:
  - `engine/team_battle.py:426`
  - `engine/team_battle.py:433`
  - `engine/team_battle.py:440`
  - `engine/team_battle.py:474`
- Evidence:
  - `end_battle_log(...)` is called on normal exit paths only.
  - No `try/finally` guard in `run_battle`.
  - On callback exception, global logger remains active and not finalized.
- Impact:
  - Possible file handle/resource leak.
  - Potential global logger state bleed into subsequent battles.

### P3 (Low)

5. Disabled `BattleLogger` has incomplete object shape.
- File: `engine/battle_logger.py:59`
- Evidence:
  - `__init__` early-returns when `enabled=False`, so attributes like `battle_id`/`entries` are not initialized.
- Impact:
  - Consumers that inspect logger attributes can get `AttributeError`.
  - Creates inconsistent API behavior across enabled/disabled modes.

6. Forced-switch “remember opponent” path in AI is currently dead code.
- Files:
  - `engine/ai/competitive_ai.py:91`
  - `engine/ai/predictive_ai.py:88`
- Evidence:
  - `_last_opponent_active` is read but never assigned anywhere in `engine/ai/*`.
- Impact:
  - Intended smarter forced-switch behavior never activates.
  - AI falls back to healthiest-switch heuristic more often than intended.

## Validation Results
- `pytest -q`: `449 passed in 0.42s`
- `python3 -m compileall -q .`: pass
- `python3 scripts/run_golden.py`: 5/5 scenarios passed
- `python3 scripts/batch_battle.py --battles 50 --format 3v3 --seed 42`: no ERROR anomalies, WARN-only (`prevented_but_attacked`) attributable to name-collision validator logic

## Recommended Roadmap

### Phase 1: Correctness fixes (short-term, highest value)
1. Implement status-origin tracking for sleep (move-induced vs Rest/self-induced).
2. Fix Sleep Clause check to ignore self-induced sleep.
3. Add tests covering Sleep Clause + Rest interaction.

### Phase 2: Audit identity hardening
1. Use side-aware keys (`pokemon_side + pokemon`) in logger summary aggregation.
2. Update validator invariants to key actors by `(pokemon_side, pokemon)` consistently.
3. Add mirror-match golden/invariant tests (same species on both sides).

### Phase 3: Lifecycle and robustness
1. Wrap `TeamBattle.run_battle` loop with `try/finally` to always finalize logs.
2. Ensure logger object has stable attributes even when disabled.
3. Add regression test for exception path cleanup.

### Phase 4: AI behavior completeness
1. Either implement `_last_opponent_active` assignment in decision flow or remove dead branch.
2. Add targeted tests for forced-switch strategy behavior.

