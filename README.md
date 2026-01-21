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
  - 147 Gen 1 moves with proper effects
  - Pokemon learnsets from Red/Blue/Yellow
  - No internet required - all data stored locally

- **Accurate Gen 1 Mechanics**
  - Original damage calculation formula
  - Critical hit system based on Speed stat (Speed/512)
  - Random damage factor (217-255/255)
  - STAB (Same Type Attack Bonus) at 1.5x
  - Proper type effectiveness chart with all 15 Gen 1 types

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
│   ├── moves.json         # All Gen 1 moves with effects
│   ├── learnsets.json     # Pokemon move learnsets
│   └── data_loader.py     # Data access layer with caching
├── models/
│   ├── enums.py           # Type, Status, and MoveCategory enums
│   ├── stats.py           # Stats dataclass
│   ├── move.py            # Move dataclass with PP tracking
│   └── pokemon.py         # Pokemon class with HP and status management
├── engine/
│   ├── battle.py          # Turn execution and battle flow
│   ├── damage.py          # Gen 1 damage calculation
│   ├── display.py         # Console UI with ANSI colors
│   ├── move_effects.py    # Special move mechanics
│   ├── stat_modifiers.py  # Stat stage modification system
│   ├── status.py          # Status effect application
│   └── type_chart.py      # Type effectiveness chart
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
from data.data_loader import get_pokemon_data, get_pokemon_moves_gen1, create_move
from models.pokemon import Pokemon
from models.stats import Stats
from models.enums import Type
from main import run_battle

# Load a Pokemon from the database
poke_data = get_pokemon_data('pikachu')

# Create moves
moves = [create_move('thunderbolt'), create_move('thunder-wave'),
         create_move('quick-attack'), create_move('agility')]

# Create the Pokemon
stats = Stats(
    hp=poke_data['stats']['hp'],
    attack=poke_data['stats']['attack'],
    defense=poke_data['stats']['defense'],
    special=poke_data['stats']['special-attack'],
    speed=poke_data['stats']['speed']
)
types = [Type[t.upper()] for t in poke_data['types']]
pikachu = Pokemon(poke_data['name'], types, stats, moves, level=50)

# Create opponent and run battle
# ... create opponent similarly ...
run_battle(pikachu, opponent, max_turns=50)
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

### Type Effectiveness
- Super effective: 2x damage
- Not very effective: 0.5x damage
- No effect: 0x damage
- Stacks for dual-type Pokemon (e.g., 4x, 0.25x)

### Stat Stages
- Range from -6 to +6
- Each stage modifies stat by specific multipliers
- Mist protects against enemy stat reductions

## License

MIT

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.
