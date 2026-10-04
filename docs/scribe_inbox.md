# Scribe Inbox

## Pending Notes (append-only)

### AI & Trainer Style Selection in Custom Battle Config UI - 2026-02-15
- Date: 2026-02-15
- Type: changelog, brief
- Summary: Custom battle config form now has working AI difficulty and trainer style selectors. When autobattle mode is selected, both AIs are independently configurable. Batch battle runner gains --ai and --style CLI flags.
- Details:
  - `ui/menus.py` — replaced "Nivel de IA" and "Mecánicas" placeholders with 4 real fields: IA Oponente, Estilo Oponente, IA Jugador, Estilo Jugador
  - Player AI fields toggle between active (cycle) in autobattle mode and disabled (placeholder, "N/A") in Jugador vs IA mode
  - `_build_config_fields(mode_idx)` rebuilds field list on mode change for conditional visibility
  - `_config_to_settings()` maps form indices to AIDifficulty and TrainerStyle enums, passes all 4 to BattleSettings
  - AI display names in Spanish: Default, Fácil, Medio, Competitivo, Predictivo, Millennium Eye
  - Trainer style names in Spanish: Equilibrado, Ofensivo, Defensivo, Status (TYPE_SPECIALIST excluded — requires sub-menu)
  - `scripts/batch_battle.py` — added --ai and --style CLI flags, replaced get_random_ai_action with create_ai() instances
  - Batch runner backward compat preserved: default flags produce same behavior as before
- Files: ui/menus.py, scripts/batch_battle.py
- Tests: 449 total, all pass. 5 golden baselines unchanged

### AI System Phase 2 - 2026-02-15
- Date: 2026-02-15
- Type: changelog, brief
- Summary: Advanced AI tactics (Phase 2) with threat scoring, switch evaluation, and Millennium Eye predictive mode. 6 AI difficulties now available. All 414 tests pass, golden baselines unchanged.
- Details:
  - New modules: `engine/ai/competitive_ai.py` (threat-scoring AI), `engine/ai/predictive_ai.py` (look-ahead switching), `engine/ai/millennium_eye_ai.py` (future-sight AI with action revision hook)
  - Extended `engine/ai/evaluator.py` with 3 pure functions: `threat_score()`, `score_switch_target()`, `should_switch()`
  - Extended `engine/ai/base.py` with optional `revise_action()` hook for mid-turn decision revision
  - Updated `engine/ai/factory.py` to register all 6 AI difficulties: Easy, Medium, Default, Competitive, Predictive, MillenniumEye
  - `engine/team_battle.py` — new `on_actions_chosen` hook for Millennium Eye action revision support
  - `main.py` — wired action revision hook into battle flow
  - Tests: 4 new test files (test_ai_competitive.py, test_ai_predictive.py, test_ai_millennium_eye.py, test_ai_evaluator_advanced.py), updated test_ai_factory.py with Phase 2 AI types
- Files: engine/ai/*.py, engine/team_battle.py, main.py, tests/test_ai_*.py
- Tests: 414 total (35 new), all pass. 5 golden baselines unchanged

### AI System Phase 1 - 2026-02-15
- Date: 2026-02-15
- Type: changelog, map, brief
- Summary: New modular AI system (Phase 1) with 3 difficulty levels (Easy, Medium, Default). Replaced AIType enum with AIDifficulty. All 378 tests pass, golden baselines stable.
- Details:
  - New module: `engine/ai/` with base.py (BaseAI ABC), difficulty.py (AIDifficulty enum), evaluator.py (move evaluator for type effectiveness and damage), default_ai.py (tactical AI), easy_ai.py (random actions), medium_ai.py (semi-random), factory.py (create_ai factory), __init__.py
  - settings/battle_config.py: Replaced AIType enum with AIDifficulty. Added backward-compat alias AIType = AIDifficulty. Renamed fields: player_ai_type → player_ai_difficulty, opponent_ai_type → opponent_ai_difficulty
  - main.py: Integrated create_ai() into run_team_battle() flow. Both autobattle and player-vs-AI modes now use AI instances
  - Tests: 49 new tests in test_ai_evaluator.py, test_ai_default.py, test_ai_easy.py, test_ai_medium.py, test_ai_factory.py
  - No engine changes, no battle log format changes
- Files: engine/ai/*.py, settings/battle_config.py, main.py, tests/test_ai_*.py
- Tests: 378 total (49 new), all pass. 5 golden baselines unchanged

### AI System Phase 3 - 2026-02-15
- Date: 2026-02-15
- Type: changelog, map, brief
- Summary: Trainer class system (Phase 3) — 2-axis style overlay for AI behavior. TrainerStyle enum + TrainerProfile dataclass with weighted scoring. Profile-aware team builder. All 449 tests pass, golden baselines stable.
- Details:
  - New modules: `engine/ai/trainer_class.py` (TrainerStyle enum, TrainerProfile dataclass with factory presets), `engine/ai/team_builder.py` (profile-aware team building with weighted Pokemon selection and moveset biasing)
  - Modified `engine/ai/base.py` — defaults to TrainerProfile.balanced() when profile=None
  - Modified `engine/ai/competitive_ai.py` — reads profile.aggression, profile.status_priority, profile.setup_priority for scoring
  - Modified `engine/ai/medium_ai.py` — reads profile.aggression and profile.status_priority for scoring
  - Modified `engine/ai/__init__.py` — exports TrainerStyle, TrainerProfile
  - Modified `settings/battle_config.py` — added player_trainer_style, opponent_trainer_style fields
  - Modified `main.py` — wires TrainerProfile from settings into create_ai() and create_team_with_moveset()
  - Tests: 2 new test files (test_ai_trainer_class.py, test_ai_team_builder.py)
- Files: engine/ai/trainer_class.py, engine/ai/team_builder.py, engine/ai/base.py, engine/ai/competitive_ai.py, engine/ai/medium_ai.py, engine/ai/__init__.py, settings/battle_config.py, main.py
- Tests: 449 total (35 new), all pass. 5 golden baselines unchanged
### Local venv setup - 2026-10-02
- Date: 2026-10-02
- Type: readme
- Summary: Run commands in CLAUDE.md now use a project virtualenv (`.venv/`) instead of bare `pytest`/`python`.
- Details:
  - Homebrew Python 3.14 has no pytest and blocks global pip installs; repo has no requirements.txt/pyproject.
  - Setup: `python3 -m venv .venv && .venv/bin/pip install pytest`. `.venv` already gitignored.
  - README "how to run" section may need the same update.
- Files: CLAUDE.md
- Tests: 449 pass, 5 golden baselines unchanged (verified via .venv)

### Engine review findings - 2026-10-02
- Date: 2026-10-02
- Type: quirk, todo
- Summary: Deep review found confirmed mechanic bugs and missing Gen 1 mechanics. No code changed yet.
- Details:
  - Confirmed by repro: Explosion/Self-Destruct user survives on miss/semi-invulnerable target; Metronome/Mirror Move call execute_turn on real Move objects from both teams (drains their PP, re-runs status checks, drops clauses); confusion checked before sleep/freeze (asleep Pokemon hurts itself); 0 PP = turn does nothing (no Struggle); no recoil (Take Down, Double-Edge, Submission).
  - Missing Gen 1 mechanics: move priority (Quick Attack +1, Counter -1); high-crit moves (policy says Replicate); flinch; secondary stat drops (Psychic, Aurora Beam, Acid, Bubble...); Toxic = regular poison; type-based status immunities (Poison can't be poisoned, etc.).
  - Smaller: Counter only tracks damage from the normal-attack path; Rage only triggers there; Jump Kick crash is max_hp/8 (Gen 1: 1 HP); Fire Spin doesn't thaw; Metronome pool is on-field moves only.
  - Any fix changes golden logs -> needs approved baseline update.
- Files: engine/battle.py, engine/status.py, engine/damage.py, engine/move_effects.py, engine/team_battle.py
- Tests: repro script only (not committed)

### Explosion faints user on miss - 2026-10-02
- Date: 2026-10-02
- Type: changelog
- Summary: Explosion/Self-Destruct now faint the user when they miss or hit a Dig/Fly target (Gen 1 behavior). Previously the user survived.
- Details:
  - New helper `_faint_if_self_destruct` in engine/battle.py, called on the semi-invulnerable and accuracy-miss paths and reused by `_handle_self_destruct_move`.
  - Faint message is the existing "se debilitó por la explosión" line; no new log wording.
- Files: engine/battle.py, tests/test_gen1_mechanics.py
- Tests: 5 new (TestSelfDestructFaintsOnMiss), 454 pass, 5 golden baselines unchanged

### Metronome/Mirror Move use a copy of the called move - 2026-10-02
- Date: 2026-10-02
- Type: changelog
- Summary: Moves called by Metronome/Mirror Move no longer spend PP from the source Move (often the opponent's), no longer re-run status/recharge/trap/PP checks, and now respect OHKO/Evasion clauses.
- Details:
  - engine/battle.py: post-check logic of `execute_turn` extracted into `_resolve_move`. `_handle_metronome_mirror_move` resolves a `dataclasses.replace` copy through `_resolve_move` instead of recursing into `execute_turn`. Clauses/defender_team now passed through `_handle_special_move`.
  - Copy also fixes Metronome-called charge/multi-turn moves draining the source PP on later turns.
  - Console line for the called move unchanged ("X usa Y!").
- Files: engine/battle.py, tests/test_gen1_mechanics.py
- Tests: 5 new (TestCalledMovesUseCopies), 459 pass, 5 golden baselines unchanged, batch 100x 3v3: 0 errors
- Quirk found: charge moves (Solar Beam, etc.) spend 2 PP — `move.use()` runs again on the execution turn in `execute_turn`.

### Bugs 3-5 + follow-ups from engine review - 2026-10-02
- Date: 2026-10-02
- Type: changelog, quirk
- Summary: Status check order fixed, Struggle added, recoil added, charge/Thrash PP spent once, Thrash lock now ends, self-KO handled in the turn loop.
- Details:
  - engine/status.py: order is now sleep -> freeze -> confusion -> paralysis (asleep/frozen Pokemon no longer roll confusion or decrement it).
  - Struggle: `create_struggle()` in engine/move_effects.py (Normal, 50 power, physical). `execute_turn` substitutes it when no move has PP. ui/selection.py: "Attack" returns immediately when no PP (previously the player could get stuck in the move menu).
  - Recoil: `RECOIL_MOVES` (Take Down/Double Edge/Submission 1/4, Struggle 1/2), applied in `_execute_normal_attack` from actual damage dealt; 0 when a Substitute absorbs. New console line "recibe N de daño por retroceso" + `recoil` effect log entry.
  - PP: continuation turns of charge moves and Thrash/Petal Dance no longer spend PP (Solar Beam was costing 2).
  - Thrash lock: continuation turns used to re-enter the special handler and restart the lock, so it only ended when PP ran out. Continuation turns now skip special handling (`_resolve_move(is_continuation=...)`).
  - Turn loop (engine/team_battle.py): a Pokemon that faints from its own move is logged/handled immediately; the foe no longer attacks a fainted target; losing the last Pokemon to a self-KO ends the battle.
  - Explosion miss now logs a `self_destruct` effect so the faint has a logged cause (validator `faint_without_cause`).
  - Known validator false positive (pre-existing): `prevented_but_attacked` fires on mirror matches because it matches by name, not side.
- Files: engine/battle.py, engine/status.py, engine/move_effects.py, engine/team_battle.py, ui/selection.py, tests/test_gen1_mechanics.py, tests/test_battle_integration_regressions.py
- Tests: 476 pass (17 new in this batch), 5 golden baselines unchanged, batch 3v3 runs: 0 errors

### Move data fields (refactor item 1) - 2026-10-03
- Date: 2026-10-03
- Type: changelog, map, decision
- Summary: moves.json and Move gain Gen 1 mechanic fields: recoil_divisor (live), priority, high_crit, flinch_chance, secondary_stat_changes + secondary_stat_chance (data only, not yet read by the engine). No battle behavior change.
- Details:
  - Schema: new keys are optional and only present when non-default (23 moves edited). Gen 1 values: Quick Attack +1 / Counter -1 priority; Slash, Karate Chop, Razor Leaf, Crabhammer high crit; flinch 10% (Bite, Hyper Fang, Bone Club) / 30% (Stomp, Headbutt, Rolling Kick, Low Kick, Rock Slide); secondary -1 drops at 33% (85/256) for Psychic, Aurora Beam, Acid, Bubble, Bubble Beam, Constrict; recoil 1/4 for Take Down, Double-Edge, Submission.
  - Decision: chance-based stat drops live in `secondary_stat_changes`, separate from `stat_changes` (which the engine always applies), so adding data cannot silently enable a mechanic.
  - Recoil now read from `move.recoil_divisor`; `RECOIL_MOVES` name list removed. Struggle sets recoil_divisor=2.
  - Bug avoided: Transform move copies and the Transform snapshot/restore built Moves field by field, which would drop new fields (e.g. Double-Edge losing recoil after Ditto switches out). Both now use `dataclasses.replace`. `get_move_data` key whitelist extended for the same reason.
  - Next: enable each mechanic after its policy is set in docs/known_quirks.md (priority, high crit, flinch, secondary effects are TBD/Replicate there).
- Files: data/moves.json, models/move.py, data/data_loader.py, engine/move_effects.py, engine/battle.py, models/pokemon.py, tests/test_move_data_fields.py, tests/test_gen1_mechanics.py
- Tests: 507 pass (31 new), 5 golden baselines unchanged, batch 100x 3v3: 0 errors

### Decision: Gen 1 move priority - 2026-10-03
- Date: 2026-10-03
- Type: decision
- Summary: Move priority is ✅ Replicate. Turn order = switches, then priority, then modified Speed, then random tie-break. Quick Attack +1, Counter −1, all others 0.
- Details:
  - Context: priority was not implemented; Quick Attack and Counter went by Speed. `priority` field already in data/moves.json (refactor item 1), not yet read by the engine.
  - Options considered: (1) ignore priority (status quo); (2) replicate Gen 1 priority using the selected move; (3) replicate using the move that actually executes this turn (chosen).
  - Outcome (3): priority comes from the executing move: charge move 2nd turn, Thrash/Petal Dance lock, else the selected move. Recharge, trapped and Struggle turns are 0. Metronome/Mirror Move are 0; the called move's priority is ignored.
  - Log: new `turn_order` reason `"priority"` only when priority decides the order; `"speed"`, `"speed_tie_random"`, `"switch_priority"` unchanged. Validator rule `turn_order_speed_wrong` only checks reason `"speed"`, so it stays valid.
  - Follow-up: implement in engine/team_battle.py `get_turn_order` (it has both actions) + engine/battle.py `determine_turn_order`; unit tests for each rule above; golden baselines expected unchanged unless a golden battle uses Quick Attack/Counter (check before approving any update).
  - SCRIBE: add to docs/decisions.md.
- Files: docs/known_quirks.md
- Tests: none (no code change)

### Move priority implemented - 2026-10-03
- Date: 2026-10-03
- Type: changelog
- Summary: Turn order now uses Gen 1 move priority (Quick Attack +1, Counter −1) before Speed, per the 2026-10-03 priority decision.
- Details:
  - engine/battle.py: new pure `get_effective_priority(pokemon, chosen_move)`; `determine_turn_order` takes optional `move1`/`move2` (defaults keep old behavior) and logs reason `"priority"` when priority decides. Text log shows `[priority]`.
  - engine/team_battle.py: `get_turn_order` passes both chosen moves. Switches still go first.
  - Follow-up (todo): AI does not know about priority. engine/ai/evaluator.py (~line 244) compares Speed only, so the AI underrates Quick Attack and misjudges Counter.
- Files: engine/battle.py, engine/team_battle.py, tests/test_move_priority.py
- Tests: 525 pass (18 new), 5 golden baselines unchanged, batch 100x 3v3: 0 errors (53 priority-ordered turns logged)
