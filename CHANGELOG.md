# Changelog

## [Unreleased] - 2026-02-14

### Fixed

#### Gen 1 Physical/Special Split (`engine/gen_mechanics.py`)
In Gen 1, the physical/special split is determined by the move's **type**, not per-move.
The data in `moves.json` uses the modern Gen 4+ per-move categories (e.g., Hyper Beam = Special),
which caused 18 damaging moves to use incorrect stats for damage calculation. For example,
Hyper Beam hit against Alakazam's Special (186) instead of Defense (96), dealing ~41 damage
instead of the correct ~122.

New module `engine/gen_mechanics.py` resolves the effective category based on `config.GENERATION`:
- **Gen 1-3**: Physical/Special derived from the move's type (Physical types: Normal, Fighting, Poison, Ground, Flying, Bug, Rock, Ghost)
- **Gen 4+**: Per-move category from `moves.json` is used directly

This is a **scalable** design — when adding future generation support, the data doesn't need to change, only `config.GENERATION`. Golden test baselines regenerated to reflect corrected damage values.

**Affected moves (18)**: Hyper Beam, Razor Wind, Sonic Boom, Swift, Tri-Attack, Gust, Acid, Sludge, Smog, Night Shade (were Special, now correctly Physical), Clamp, Crabhammer, Waterfall, Razor Leaf, Vine Whip, Fire Punch, Ice Punch, Thunder Punch (were Physical, now correctly Special).

#### Bite Type (`data/moves.json`)
Changed Bite's type from DARK to NORMAL. Dark type did not exist in Gen 1.

#### Team Selection Scroll Bug (`ui/selection.py`)
The `select_team_curses` function was missing scroll_offset management in its UP/DOWN key handlers. When scrolling past the visible area, the list no longer scrolled with the selection, making items invisible. Added scroll tracking matching the working `select_pokemon_curses` implementation.

### Added

#### Battle Clause Enforcement (`engine/clauses.py`)
New module with pure functions for enforcing Pokemon Stadium battle clauses:
- **Sleep Clause**: Blocks putting a second opponent Pokemon to sleep (fainted Pokemon don't count)
- **Freeze Clause**: Blocks freezing a second opponent Pokemon (fainted Pokemon don't count)
- **OHKO Clause**: Bans Fissure, Guillotine, and Horn Drill
- **Evasion Clause**: Bans Double Team and Minimize

Clauses are enforced at correct points matching the original games: OHKO/Evasion block before move execution, Sleep/Freeze block at status application time (move still deals damage). AI automatically filters banned moves from its selection.

#### Ruleset Integration into Battle Flow (`main.py`)
Replaced the battle format selection with a ruleset selection menu. The game flow is now:
1. Select ruleset (predefined cup or custom)
2. Select battle mode (Player vs AI, Autobattle, Watch)
3. Select moveset mode
4. Team selection (filtered by ruleset restrictions)
5. Battle with clause enforcement

Battle format is derived from the ruleset's `max_team_size` (1→1v1, 2-3→3v3, 4-6→6v6).

#### Ruleset Selection Menu (`ui/selection.py`)
Curses-based menu showing all predefined Pokemon Stadium cups with descriptions:
- Standard, Poke Cup, Prime Cup, Little Cup, Pika Cup, Petit Cup
- "Custom..." option opens a full ruleset editor

#### Custom Ruleset Editor (`ui/selection.py`)
Form-based editor for creating custom rulesets with configurable:
- Level range (min/max/default), team size, level sum limit
- Legendary and basic-only restrictions
- Individual clause toggles (Sleep, Freeze, OHKO, Evasion)

#### Pokemon Height & Weight Data (`data/pokemon.json`)
Added official Pokedex height (meters) and weight (kilograms) for all 151 Kanto Pokemon. Used by Petit Cup for physical restriction filtering.

#### BattleClauses Dataclass (`models/ruleset.py`)
New dataclass grouping clause toggles with `any_active()` and `get_active_list()` helpers. Added to `Ruleset` along with `max_height_m` and `max_weight_kg` fields. All predefined cups updated with accurate Pokemon Stadium clauses.

#### Physical Validation (`models/ruleset.py`)
`validate_pokemon_physical(name, height, weight)` method on `Ruleset` for height/weight enforcement (Petit Cup).

#### Pokemon Filtering by Ruleset (`ui/selection.py`)
`filter_pokemon_by_ruleset()` filters the Pokemon pool by banned list, legendary restrictions, basic-only rules, and height/weight limits.

#### Clause and Ruleset Tests (`tests/test_clauses.py`, `tests/test_ruleset.py`)
43 new tests covering all clause enforcement functions, BattleClauses dataclass, predefined ruleset clause configuration, and Petit Cup physical restrictions. Total test count: 277.

### Changed

#### Battle Engine Clause Threading (`engine/battle.py`, `engine/team_battle.py`)
- `execute_turn()` accepts optional `clauses` and `defender_team` parameters
- `TeamBattle` accepts optional `clauses` in constructor, threads to turn execution
- `get_random_ai_action()` accepts optional `clauses` to filter banned moves
- `_apply_move_status_effect()` checks sleep/freeze clauses before applying status

#### Data Loader Physical Data (`data/data_loader.py`)
- `get_pokemon_data()` now includes `height` and `weight` in returned dict
- New `get_pokemon_physical_data()` helper for direct height/weight lookup

---

## [Unreleased] - 2026-02-11

### Fixed

#### Critical: Move Name Mismatch (`engine/move_effects.py`)
All multi-word move names in the special move registry used hyphens (e.g., `"Leech-Seed"`) while the data loader (`data_loader.py`) converts them to spaces (`"Leech Seed"`). This caused `is_special_move()` to return `False` for every multi-word move, meaning they were incorrectly handled as normal attacks instead of triggering their special effects.

**Affected moves:** Dragon Rage, Sonic Boom, Mega Drain, Leech Life, Dream Eater, Self Destruct, High Jump Kick, Jump Kick, Hyper Beam, Solar Beam, Skull Bash, Sky Attack, Razor Wind, Petal Dance, Fire Spin, Fury Attack, Fury Swipes, Pin Missile, Spike Cannon, Comet Punch, Double Slap, Double Kick, Night Shade, Seismic Toss, Soft Boiled, Light Screen, Super Fang, Leech Seed, Focus Energy, Mirror Move.

**Symptoms before fix:**
- Leech Seed dealt damage instead of seeding
- Skull Bash attacked immediately without charging
- Hyper Beam had no recharge turn
- Dragon Rage used stats instead of fixed 40 damage
- Multi-hit moves hit once instead of 2-5 times

#### Wing Attack Base Power (`data/moves.json`)
Changed Wing Attack power from 60 to 35 (correct Gen 1 value).

#### Crash Damage Move Names (`engine/battle.py`)
Updated `"High-Jump-Kick"` / `"Jump-Kick"` string comparisons in `_check_accuracy` to use spaces, matching the data loader's naming convention.

### Improved

#### Battle Logger: Actual Effectiveness & Critical Hits (`engine/battle.py`)
Previously, `team_battle.py` logged all moves with `effectiveness=1.0` and `is_critical=False` because it didn't have access to these values. Logging now happens inside `battle.py` where the actual damage calculation occurs, so battle logs now contain accurate effectiveness multipliers and critical hit flags.

#### Battle Logger: Miss Logging (`engine/battle.py`)
Added `log_miss()` calls in `_check_accuracy` so missed moves are now recorded in battle logs.

#### Battle Logger: End-of-Turn Effects (`engine/battle.py`, `engine/status.py`)
Added logging for:
- Leech Seed drain damage
- Trapping move damage (Wrap, Bind, etc.)
- Burn damage per turn
- Poison damage per turn

#### Duplicate Faint Entries (`engine/team_battle.py`)
In multi-Pokemon battles, a Pokemon that fainted from a direct attack would be logged as fainted twice: once after the attack and again in the end-of-turn faint check. Now tracks which Pokemon fainted during actions and skips them in the end-of-turn check.

#### Duplicate Move Logging (`engine/team_battle.py`)
Removed the redundant `log_move()` call from `team_battle.py:execute_action` since move logging now happens inside `battle.py` with accurate data.
