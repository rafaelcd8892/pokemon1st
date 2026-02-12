# Pokemon Gen 1 Battle Simulator

A faithful Python recreation of the Pokemon Generation 1 battle system. Every mechanic is implemented from the original formulas: damage calculation, critical hits, stat stages, status effects, type chart, and IVs/EVs. Comes with an interactive curses-based UI, full audit logging, and a batch battle runner for automated testing.

## Quick Start

```bash
# Interactive battle
python3 main.py

# Run 100 automated battles and validate every log
python scripts/batch_battle.py --battles 100 --format 3v3
```

## What's In the Box

### 151 Pokemon, 164 Moves, Zero Internet Required

All data is stored locally in JSON files. Every Kanto Pokemon with accurate base stats, every Gen 1 move with proper effects, and full learnsets including level-up, TM, and evolution-inherited moves.

### Authentic Gen 1 Mechanics

The damage formula, stat calculation, critical hit system, and every quirk are implemented from the original game:

```
damage = ((((2 * Level / 5 + 2) * Power * Attack / Defense) / 50) + 2)
         * STAB * Effectiveness * Random(217-255) / 255
```

- **Critical hits** use Speed/512 probability and ignore stat modifiers
- **Focus Energy bug** divides crit chance by 4 instead of increasing it
- **Stats** are calculated with the Gen 1 formula using IVs (0-15) and EVs (0-65535)
- **HP IV** is derived from the least significant bits of the other four IVs
- **Burn** halves physical attack damage, not the Attack stat
- **Freeze** does not thaw naturally (only Fire-type moves thaw)
- **Type chart** has all 15 Gen 1 types with Ghost/Psychic immunity bug

### Battle Modes

| Mode | Description |
|------|-------------|
| Player vs AI | You control your team against a random AI |
| Autobattle | AI controls both sides |
| Watch | Autobattle with longer delays for spectating |

### Battle Formats

| Format | Description |
|--------|-------------|
| 1v1 | Single Pokemon battle |
| 3v3 | Three Pokemon per side |
| 6v6 | Full team battle |

### Pokemon Stadium Rulesets

| Cup | Level | Team Size | Restrictions |
|-----|-------|-----------|--------------|
| Standard | 50 | 6 | None |
| Poke Cup | 50-55 | 3 | Level sum <= 155, no legendaries |
| Prime Cup | 100 | 6 | None |
| Little Cup | 5 | 3 | Basic Pokemon only |
| Pika Cup | 15-20 | 3 | Basic only, level sum <= 50 |
| Petit Cup | 25-30 | 3 | No legendaries |

### Move Mechanics

Every major Gen 1 move mechanic is implemented:

- Two-turn moves (Hyper Beam recharge, Dig/Fly invulnerability, Solar Beam charge)
- Multi-hit moves (Fury Attack 2-5 hits, Double Kick fixed 2 hits, Twineedle with poison)
- HP drain (Absorb, Mega Drain, Leech Life heal 50% of damage dealt)
- Fixed damage (Dragon Rage always 40, Sonic Boom always 20)
- OHKO moves (Horn Drill, Guillotine, Fissure)
- Self-destruct moves (Explosion halves target defense)
- Crash damage (High Jump Kick, Jump Kick on miss)
- Recovery (Recover, Soft-Boiled restore 50% HP; Rest fully heals + sleeps)
- Screens (Reflect halves physical, Light Screen halves special; crits bypass)
- Trapping (Wrap, Bind, Fire Spin prevent switching for 2-5 turns)
- Stat stages (-6 to +6 with Mist protection)
- Status moves (Thunder Wave, Toxic, Hypnosis, etc.)
- Multi-turn lock-in (Thrash, Petal Dance cause confusion after 2-3 turns)
- Rage (attack rises each time the user is hit)
- Transform, Disable, Metronome, Mirror Move, Counter

### Status Effects

| Status | Effect |
|--------|--------|
| Burn | 1/16 HP per turn, physical damage halved |
| Freeze | Cannot act, thaws only from Fire-type hit |
| Paralysis | 25% chance to skip turn |
| Poison | 1/16 HP per turn |
| Sleep | Lasts 1-7 turns, cannot act |
| Confusion | 1-4 turns, 50% chance to hit self |

## Battle Logging & Audit System

Every battle produces dual-format logs in `logs/battles/` (or `logs/batch/` for batch runs):

- **`.log`** file -- human-readable turn-by-turn narrative
- **`.json`** file -- machine-readable structured data for analysis

### What the Logs Capture

Every log entry includes full context for auditing:

- **Damage breakdowns** -- every formula input (power, attack/defense stats, stat stages, STAB, effectiveness, random roll 217-255, burn modifier, crit) so any damage number can be independently verified
- **State snapshots** -- full Pokemon state at the start of every turn (HP, status, stat stages, volatile effects like confusion, screens, substitute, traps)
- **Turn order reasoning** -- speed values and reason (speed, speed tie, switch priority)
- **Move prevention context** -- explicit reasons when a Pokemon can't act (frozen, asleep, paralyzed, confused self-hit, disabled, recharging, trapped)
- **Per-Pokemon battle summary** -- damage dealt/taken, residual damage, moves used, crits landed, times fainted

### Event Bus

The engine emits 56 typed events covering every battle mechanic (screen reduction, substitute blocked, trap damage, mist protection, etc.) through a global event bus. Events are bridged to the logger via `LogBridgeHandler`, ensuring nothing is invisible.

### Log Validator

```bash
# Validate a single battle log
python scripts/validate_battle_log.py logs/battles/battle_20260212_075856.json
```

Checks 10 invariants: turn boundaries, HP ranges, self-target consistency, switch-into-fainted prevention, duplicate move detection, faint causality, damage breakdown consistency, turn order speed correctness, state snapshot presence, and move prevention conflicts.

## Batch Battle Simulator

Run hundreds of battles automatically, validate every log, and surface anomalies:

```bash
# Basic run
python scripts/batch_battle.py --battles 100 --format 3v3

# With reproducible seed
python scripts/batch_battle.py --battles 100 --format 6v6 --seed 42

# Stop on first error
python scripts/batch_battle.py --battles 200 --stop-on-error

# All options
python scripts/batch_battle.py \
  --battles 100 \
  --format 3v3 \
  --moveset smart_random \
  --seed 42 \
  --output-dir logs/batch/ \
  --verbose
```

Output:
```
Running 100 battles (3v3, smart_random movesets)
Logs: logs/batch
Base seed: 42

  [  1/100] battle_20260212_084258_198853 turns= 16 winner=Team 1       OK
  [  2/100] battle_20260212_084258_209302 turns= 28 winner=Team 1       OK
  ...

============================================================
  BATCH BATTLE REPORT
============================================================

  Battles run:     100
  Total time:      1.0s (0.01s per battle)
  Average turns:   21.1

  --- Win Distribution ---
  Team 1         51 ( 51.0%) #########################
  Team 2         49 ( 49.0%) ########################

  --- Validation ---
  Errors:   0
  Warnings: 0

============================================================
```

Exits with code 1 if any ERROR-level anomalies are found. Logs go to `logs/batch/` by default.

## Project Structure

```
PokemonGen1/
├── main.py                          # Interactive battle entry point
├── config.py                        # Battle system constants
├── logging_config.py                # Logging setup
│
├── data/
│   ├── pokemon.json                 # 151 Pokemon with base stats
│   ├── moves.json                   # 164 moves with effects
│   ├── learnsets.json               # Move learnsets (level-up/TM/evolution)
│   ├── preset_movesets.json         # Competitive moveset presets
│   └── data_loader.py              # Data access layer with caching
│
├── models/
│   ├── enums.py                     # Type, Status, MoveCategory, BattleFormat
│   ├── stats.py                     # Stats dataclass (hp/atk/def/spc/spe)
│   ├── move.py                      # Move with PP tracking and stat changes
│   ├── pokemon.py                   # Pokemon with full battle state
│   ├── ivs.py                       # Gen 1 Individual Values (DVs)
│   ├── ruleset.py                   # Stadium cup definitions
│   └── team.py                      # Team management
│
├── engine/
│   ├── battle.py                    # Turn execution and combat mechanics
│   ├── damage.py                    # Damage formula + DamageBreakdown audit
│   ├── status.py                    # Status effect processing
│   ├── move_effects.py              # Special move mechanics
│   ├── stat_modifiers.py            # Stat stage system
│   ├── stat_calculator.py           # Gen 1 stat formulas (IVs/EVs/level)
│   ├── type_chart.py                # 15-type effectiveness matrix
│   ├── team_battle.py               # Multi-Pokemon battle engine + AI
│   ├── battle_logger.py             # Dual-format battle logging
│   ├── display.py                   # ANSI color console output
│   └── events/
│       ├── types.py                 # 56 typed battle event dataclasses
│       ├── bus.py                   # Global event bus (pub/sub)
│       └── handlers/
│           ├── cli.py               # CLI event handler
│           └── log_bridge.py        # Event bus -> battle logger bridge
│
├── settings/
│   └── battle_config.py             # BattleMode, MovesetMode, BattleSettings
│
├── ui/
│   └── selection.py                 # Curses-based Pokemon/move selection UI
│
├── scripts/
│   ├── batch_battle.py              # Batch battle runner + auto-validation
│   ├── validate_battle_log.py       # Log invariant checker (10 rules)
│   ├── migrate_battle_logs.py       # Log format migration tool
│   └── fetch_gen1_data.py           # One-time PokeAPI data fetcher
│
├── tests/                           # 229 tests
│   ├── test_gen1_mechanics.py       # Core mechanic tests
│   ├── test_damage.py               # Damage calculation tests
│   ├── test_battle_audit_invariants.py  # Log validation tests
│   ├── test_battle_integration_regressions.py
│   ├── test_type_chart.py
│   ├── test_stat_calculator.py
│   ├── test_ruleset.py
│   ├── test_events.py
│   ├── test_battle_config.py
│   ├── test_moveset_selection.py
│   └── test_selection.py
│
└── logs/
    ├── battles/                     # Interactive battle logs
    └── batch/                       # Batch battle logs
```

## Programmatic Usage

### Create Pokemon with Rulesets

```python
from data.data_loader import create_move, create_pokemon_with_ruleset
from models.ruleset import POKE_CUP_RULES, LITTLE_CUP_RULES
from models.ivs import IVs

moves = [create_move('thunderbolt'), create_move('thunder-wave'),
         create_move('quick-attack'), create_move('agility')]

# Standard competitive Pokemon
pikachu = create_pokemon_with_ruleset('pikachu', moves)

# With custom IVs and level
pikachu = create_pokemon_with_ruleset(
    'pikachu', moves, level=55,
    ivs=IVs(attack=15, defense=12, special=15, speed=14)
)

# Little Cup (level 5)
pikachu_lc = create_pokemon_with_ruleset('pikachu', moves, ruleset=LITTLE_CUP_RULES)
```

### Run a Battle Programmatically

```python
from models.team import Team
from models.enums import BattleFormat
from engine.team_battle import TeamBattle, get_random_ai_action, get_random_forced_switch

team1 = Team([pikachu], "Player")
team2 = Team([blastoise], "Opponent")

battle = TeamBattle(team1, team2, battle_format=BattleFormat.SINGLE, action_delay=0)
winner = battle.run_battle(
    get_player_action=get_random_ai_action,
    get_opponent_action=get_random_ai_action,
    get_forced_switch=get_random_forced_switch,
)
print(f"Winner: {winner.name if winner else 'Draw'}")
```

## Requirements

- Python 3.10+
- No external dependencies for core engine
- Terminal with curses support for interactive UI (macOS/Linux built-in)

## Tests

```bash
python -m pytest tests/ -v
```

229 tests covering damage calculation, type effectiveness, stat calculation, Gen 1 mechanics, battle audit invariants, rulesets, moveset selection, and event bus.

## Roadmap

### Next Up
- Type-aware AI (picks moves by effectiveness, switches on disadvantage)
- Deterministic replay (seeded RNG per battle, replay from JSON logs)
- Mechanics profile system (toggle Gen 1 quirks: Toxic counter reset, 1/256 miss, sleep clause)

### Future
- Gen 2 support (Dark/Steel types, Special split, weather, held items)
- Web UI for battles
- Smarter AI (damage estimation, minimax search)
- Franchise re-skinning support (configurable data packs)

## License

MIT
