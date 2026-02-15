# CLAUDE.md

## Project Identity
Pokemon Gen 1 Battle engine. Modular. Looking to step by step increase.

## Invariants (do not violate)
1. Battle log output must remain stable (format + wording), unless ticket says otherwise.
2. Engine must be deterministic when a seed is provided.
3. Mechanics code should be testable without running full battles (unit tests preferred).
4. Prefer minimal diffs and isolated changes.

## Repo map
- Entrypoint(s): `main.py` (interactive battle)
- Battle orchestration: `engine/team_battle.py` (multi-Pokemon battle engine + AI)
- Turn resolution: `engine/battle.py` (turn execution and combat mechanics)
- Damage calculation: `engine/damage.py` (damage formula + DamageBreakdown audit)
- Gen mechanics: `engine/gen_mechanics.py` (generation-specific P/S split resolution)
- Status effects: `engine/status.py` (status effect processing)
- Move effects: `engine/move_effects.py` (special move mechanics)
- Stat modifiers: `engine/stat_modifiers.py` (stat stage system)
- Stat calculator: `engine/stat_calculator.py` (Gen 1 stat formulas with IVs/EVs/level)
- Type chart: `engine/type_chart.py` (15-type effectiveness matrix)
- RNG / seeding: `engine/rng.py` (modular BattleRNG system with global accessors)
- Log formatting: `engine/battle_logger.py` (dual-format .log + .json)
- Event bus: `engine/events/bus.py` (pub/sub), `engine/events/types.py` (56 event dataclasses)
- Event handlers: `engine/events/handlers/cli.py`, `engine/events/handlers/log_bridge.py`, `engine/events/handlers/buffer.py` (buffered event storage for curses UI)
- Display: `engine/display.py` (ANSI color console output)
- Models: `models/` (pokemon, move, stats, enums, ivs, team, ruleset)
- AI system: `engine/ai/` (base.py, difficulty.py, evaluator.py, default_ai.py, easy_ai.py, medium_ai.py, competitive_ai.py, predictive_ai.py, millennium_eye_ai.py, trainer_class.py, team_builder.py, factory.py)
  - `engine/ai/trainer_class.py` — TrainerStyle enum + TrainerProfile dataclass (style overlay)
  - `engine/ai/team_builder.py` — profile-biased team building (weighted Pokemon/moveset selection)
- Settings: `settings/battle_config.py` (BattleMode, MovesetMode, BattleSettings, AIDifficulty, TeamSelectMode)
- UI: `ui/selection.py` (curses Pokemon/move/ruleset selection), `ui/menus.py` (main menu navigation, custom battle config form)
- Data: `data/` (pokemon.json, moves.json, learnsets.json, preset_movesets.json, data_loader.py)
- Tests: `tests/` (unit, integration, golden, audit)

## How to run locally
- Run an interactive battle:
  - `python3 main.py`
- Run tests:
  - `pytest -q`
- Run golden tests:
  - `python scripts/run_golden.py`
- Run batch battles (100 automated with validation):
  - `python scripts/batch_battle.py --battles 100 --format 3v3`
- Validate a battle log:
  - `python scripts/validate_battle_log.py logs/battles/<file>.json`

## Data / configuration
- Pokémon stats source: `data/pokemon.json` (151 Kanto Pokémon with base stats)
- Moves data source: `data/moves.json` (164 Gen 1 moves with effects)
- Learnsets: `data/learnsets.json` (level-up, TM, evolution-inherited)
- Preset movesets: `data/preset_movesets.json` (competitive moveset presets)
- Type chart source: `engine/type_chart.py` (15-type effectiveness matrix, hardcoded)
- Data loader: `data/data_loader.py` (access layer with caching)

## "Where to start reading"
If you need to understand the engine quickly:
1. Entry point: `main.py` (interactive battle setup and UI)
2. Battle loop: `engine/team_battle.py` (multi-Pokemon battle orchestration, AI actions, switching)
3. Turn resolver: `engine/battle.py` (turn execution, move resolution, combat mechanics)
4. Damage calc: `engine/damage.py` (Gen 1 damage formula, DamageBreakdown audit struct)
5. Status effects: `engine/status.py` (burn, freeze, paralysis, poison, sleep, confusion)
6. Move effects: `engine/move_effects.py` (two-turn, multi-hit, drain, fixed damage, OHKO, etc.)
7. Log formatter: `engine/battle_logger.py` (dual .log + .json output)

## Known “hot spots”
Areas that frequently cause subtle bugs:
- Rounding / integer truncation
- Crit mechanics (Gen 1)
- Multi-turn moves / partial trapping
- Status + turn order interactions
- 1/256 quirks (if enabled)

## Change Policy
- Small, localized changes only
- No large refactors unless requested
- If broader edits are needed → explain first

## Definition of Done
- Tests added/updated
- Tests pass
- Golden outputs unchanged
- Validation commands run
- Document changes in README.md and CHANGELOG.md including dates and changes done

## Failure Modes to Avoid
- Log formatting changes
- Nondeterministic randomness
- Unnecessary abstractions

## Coding Preferences
- Prefer pure functions
- Readability > cleverness
- Isolate mechanics from I/O

## Documentation Protocol

The file docs/scribe_inbox.md is the canonical staging area for documentation updates.

Operational Rules:

1. Agents and coordinator MUST append durable notes to docs/scribe_inbox.md
2. SCRIBE is the ONLY agent allowed to process and clear the inbox
3. Notes must be concise and structured
4. Do NOT directly modify README / CHANGELOG / PROJECT_MAP / DECISIONS
   unless acting as SCRIBE

When significant events occur, append an entry to docs/scribe_inbox.md.

Significant events include:

- Behavior changes
- Structural changes
- Durable decisions
- Validation milestones
- Newly discovered hot spots / quirks
- Important constraints or invariants

Inbox entries must follow this structure:

- Date:
- Type: decision | changelog | map | brief | readme | quirk | todo
- Summary:
- Details:
- Files:
- Tests: