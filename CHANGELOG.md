# Changelog

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
