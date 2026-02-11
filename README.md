# Pokemon Gen 1 Battle Simulator

A Python implementation of the Pokemon Generation 1 battle system with accurate damage calculations, type effectiveness, status effects, and an interactive curses-based UI.

## Features

- **Interactive UI**
  - Curses-based Pokemon selection with real-time search
  - Move selection with preview panel showing stats and effects
  - Type-colored badges and stat bars
  - Keyboard navigation (arrow keys, search by typing)

- **Complete Gen 1 Pokemon Database**
  - All 151 Kanto Pokemon with accurate base stats
  - 164 Gen 1 moves with proper effects
  - Pokemon learnsets including level-up moves, TM moves, and evolution line moves
  - Move sources displayed in UI (TM in yellow, EVO in green)
  - No internet required - all data stored locally

- **Accurate Gen 1 Mechanics**
  - Original damage calculation formula
  - Gen 1 stat calculation with IVs (DVs) and level
  - Critical hit system based on Speed stat (Speed/512)
  - Random damage factor (217-255/255)
  - STAB (Same Type Attack Bonus) at 1.5x
  - Proper type effectiveness chart with all 15 Gen 1 types

- **Pokemon Stadium-Style Rulesets**
  - Standard (Level 50)
  - Poke Cup (Lv 50-55, sum ≤ 155, no Mew/Mewtwo)
  - Prime Cup (Level 100)
  - Little Cup (Level 5, basic Pokemon only)
  - Pika Cup (Lv 15-20, basic Pokemon only)
  - Petit Cup (Lv 25-30, height/weight restrictions)
  - Custom rulesets support

- **Battle Logging**
  - Individual battle log files for debugging
  - Human-readable `.log` files with turn-by-turn events
  - Machine-readable `.json` files for analysis
  - Logs saved to `logs/battles/` directory

- **Status Effects**
  - Burn: Reduces physical attack damage by 50%, deals 1/16 max HP damage per turn
  - Freeze: 20% chance to thaw each turn
  - Paralysis: 25% chance to prevent action
  - Poison: Deals 1/16 max HP damage per turn
  - Sleep: Lasts 1-7 turns
  - Confusion: 1-4 turns with self-damage chance

- **Advanced Move Effects**
  - Two-turn moves (Hyper Beam, Solar Beam, Dig, Fly)
  - Multi-hit moves (Fury Attack, Pin Missile)
  - HP drain moves (Absorb, Mega Drain, Leech Life)
  - Fixed damage moves (Dragon Rage, Sonic Boom)
  - OHKO moves (Guillotine, Horn Drill)
  - Recovery moves (Recover, Soft-Boiled, Rest)
  - Screen moves (Light Screen, Reflect)
  - Trapping moves (Wrap, Bind, Fire Spin)
  - Stat modification moves with -6 to +6 stages

- **Move Categories**
  - Physical moves use Attack vs Defense
  - Special moves use Special vs Special
  - Status moves for applying conditions

## Project Structure

```
PokemonGen1/
├── config.py              # Battle system constants
├── main.py                # Entry point and battle orchestration
├── data/
│   ├── pokemon.json       # All 151 Pokemon data
│   ├── moves.json         # All 164 Gen 1 moves with effects
│   ├── learnsets.json     # Pokemon move learnsets with sources (level-up/tm/evolution)
│   └── data_loader.py     # Data access layer with caching
├── models/
│   ├── enums.py           # Type, Status, and MoveCategory enums
│   ├── stats.py           # Stats dataclass
│   ├── move.py            # Move dataclass with PP tracking
│   ├── pokemon.py         # Pokemon class with HP and status management
│   ├── ivs.py             # Individual Values (Gen 1 DVs)
│   ├── ruleset.py         # Cup/Ruleset definitions (Stadium-style)
│   └── team.py            # Team management for multi-Pokemon battles
├── engine/
│   ├── battle.py          # Turn execution and battle flow
│   ├── battle_logger.py   # Individual battle logging to files
│   ├── damage.py          # Gen 1 damage calculation
│   ├── display.py         # Console UI with ANSI colors
│   ├── move_effects.py    # Special move mechanics
│   ├── stat_calculator.py # Gen 1 stat formulas with IVs/EVs
│   ├── stat_modifiers.py  # Stat stage modification system
│   ├── status.py          # Status effect application
│   ├── team_battle.py     # Multi-Pokemon battle engine
│   └── type_chart.py      # Type effectiveness chart
├── settings/
│   └── battle_config.py   # Battle modes and settings
├── ui/
│   └── selection.py       # Interactive Pokemon & move selection UI
└── scripts/
    └── fetch_gen1_data.py # One-time data fetcher from PokeAPI
```

## Requirements

- Python 3.10+
- Terminal with curses support (macOS/Linux built-in, Windows needs windows-curses)

## Usage

Run the battle simulator:

```bash
python3 main.py
```

### Controls

**Pokemon Selection:**
- `↑/↓` - Navigate the list
- `Type` - Search by name
- `Backspace` - Clear search
- `Enter` - Select Pokemon
- `Esc` - Cancel

**Move Selection:**
- `↑/↓` - Navigate moves
- `Space` - Toggle move selection (select 4)
- `Enter` - Confirm selection
- `Esc` - Cancel

Move sources are indicated:
- **TM** (yellow) - Learnable via Technical Machine
- **EVO** (green) - Inherited from pre-evolution
- No tag - Learned by level-up

## Example Session

```
=== BATALLA POKÉMON GEN 1 ===

[Interactive Pokemon selection UI appears]
[Interactive move selection UI appears]

Tu Pokémon: Pikachu
Movimientos: thunderbolt, thunder-wave, quick-attack, agility

El rival será aleatorio...
Pokémon aleatorio: Blastoise | Movimientos: surf, ice-beam, skull-bash, withdraw

Presiona ENTER para comenzar la batalla...

=== BATALLA POKÉMON ===
Pikachu (HP: 95/95)
Blastoise (HP: 158/158)

--- Turno 1 ---

Pikachu usa Thunderbolt!
¡Es súper efectivo!
Blastoise recibe 89 de daño! (HP: 69/158)

Blastoise usa Surf!
Pikachu recibe 52 de daño! (HP: 43/95)
```

## Creating Custom Battles

```python
from data.data_loader import get_pokemon_data, create_move, create_pokemon_with_ruleset
from models.ivs import IVs
from models.ruleset import POKE_CUP_RULES, LITTLE_CUP_RULES

# Easy way: Use the factory function with a ruleset
moves = [create_move('thunderbolt'), create_move('thunder-wave'),
         create_move('quick-attack'), create_move('agility')]
pikachu = create_pokemon_with_ruleset('pikachu', moves, ruleset=POKE_CUP_RULES)

# With custom level and IVs
custom_ivs = IVs(attack=15, defense=12, special=15, speed=14)
pikachu_custom = create_pokemon_with_ruleset(
    'pikachu', moves,
    level=55,
    ivs=custom_ivs
)

# For Little Cup (level 5 battles)
pichu = create_pokemon_with_ruleset('pichu', moves, ruleset=LITTLE_CUP_RULES)
```

### Manual Pokemon Creation

```python
from models.pokemon import Pokemon
from models.stats import Stats
from models.ivs import IVs
from models.enums import Type

# Create Pokemon with Gen 1 stat calculation (default)
stats = Stats(hp=35, attack=55, defense=40, special=50, speed=90)
pikachu = Pokemon(
    name='Pikachu',
    types=[Type.ELECTRIC],
    stats=stats,  # These are species base stats
    moves=moves,
    level=50,
    ivs=IVs.perfect()  # Default: perfect IVs
)
# pikachu.base_stats now returns calculated stats based on level/IVs

# For testing/legacy mode (uses raw stats directly)
pikachu_legacy = Pokemon(
    name='Pikachu',
    types=[Type.ELECTRIC],
    stats=stats,
    moves=moves,
    level=50,
    use_calculated_stats=False
)
```

## Configuration

Adjust battle constants in `config.py`:

```python
CRIT_MULTIPLIER = 2              # Critical hit damage multiplier
STAB_MULTIPLIER = 1.5            # Same Type Attack Bonus
MIN_RANDOM_FACTOR = 217          # Minimum random damage factor
MAX_RANDOM_FACTOR = 255          # Maximum random damage factor
FREEZE_THAW_CHANCE = 0.2         # 20% chance to thaw per turn
PARALYSIS_FAIL_CHANCE = 0.25     # 25% chance to be fully paralyzed
```

## Gen 1 Battle Mechanics

### Damage Formula
```
damage = ((((2 * Level / 5 + 2) * Power * Attack / Defense) / 50) + 2)
         * STAB * Effectiveness * Random(217-255)/255
```

### Critical Hits
- Probability = BaseSpeed / 512
- Multiplies damage by 2
- Ignores stat modifiers (Gen 1 behavior)
- Ignores Reflect/Light Screen reductions
- Focus Energy uses the Gen 1 bug (crit chance divided by 4)

### Type Effectiveness
- Super effective: 2x damage
- Not very effective: 0.5x damage
- No effect: 0x damage
- Stacks for dual-type Pokemon (e.g., 4x, 0.25x)

### Stat Stages
- Range from -6 to +6
- Each stage modifies stat by specific multipliers
- Mist protects against enemy stat reductions

### End-of-Turn Status Damage
- Burn and poison damage are applied at the end of each turn

### Gen 1 Stat Calculation

Stats are calculated using the authentic Gen 1 formulas with IVs (called DVs in Gen 1):

**HP Formula:**
```
HP = floor(((Base + IV) * 2 + floor(sqrt(EV) / 4)) * Level / 100) + Level + 10
```

**Other Stats:**
```
Stat = floor(((Base + IV) * 2 + floor(sqrt(EV) / 4)) * Level / 100) + 5
```

**IVs (Individual Values):**
- Range: 0-15 for Attack, Defense, Speed, Special
- HP IV is derived from other IVs (Gen 1 mechanic)
- Perfect IVs (15 in all stats) used by default for competitive play

### Rulesets / Cups

The game supports Pokemon Stadium-style rulesets:

| Cup | Level Range | Team Size | Special Rules |
|-----|-------------|-----------|---------------|
| Standard | 50 | 6 | None |
| Poke Cup | 50-55 | 3 | Sum ≤ 155, no Mew/Mewtwo |
| Prime Cup | 100 | 6 | None |
| Little Cup | 5 | 6 | Basic Pokemon only |
| Pika Cup | 15-20 | 3 | Basic Pokemon only, sum ≤ 50 |
| Petit Cup | 25-30 | 3 | Height ≤ 2m, weight ≤ 20kg |

### Battle Logging

Detailed battle logs are automatically saved for debugging and analysis:

- **Location:** `logs/battles/`
- **Files per battle:**
  - `battle_YYYYMMDD_HHMMSS.log` - Human-readable turn-by-turn log
  - `battle_YYYYMMDD_HHMMSS.json` - Structured data for programmatic analysis

Example log entry:
```
=== TURN 5 ===
Pikachu used Thunderbolt on Blastoise
  -> 89 damage (Super effective!)
  Blastoise: 69/158 HP (43.7%)
```

## Roadmap

### Phase 1 — Testing & Observability
- Internal battle tester / headless runner for automated matchup validation
- Route battle output through the event bus (decouple from `print()`)
- Integration tests for full battle flows
- Audit remaining move edge cases

### Phase 2 — AI & Replayability
- Type-aware AI (considers matchups, switches on disadvantage)
- Battle replay from JSON logs
- Battle statistics dashboard (win rates, move usage, avg battle length)

### Phase 3 — Interface Expansion
- Web UI (Flask/FastAPI backend + frontend)
- Battle viewer / replay tool
- Multiplayer support (two humans over network)

### Phase 4 — Gen 2 Support
- Parameterize engine by generation
- Dark and Steel types, updated type chart
- Split Special into Special Attack / Special Defense
- Weather system (Rain, Sun, Sandstorm)
- Held items
- 100 new Pokemon and moves

### Phase 5 — Gen 3+
- Abilities system
- Natures
- Double battles
- Additional weather types and terrains

## License

MIT

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.
