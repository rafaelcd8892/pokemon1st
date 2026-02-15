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