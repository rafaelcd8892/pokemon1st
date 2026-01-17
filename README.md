# Pokemon Gen 1 Battle Simulator

A Python implementation of the Pokemon Generation 1 battle system with accurate damage calculations, type effectiveness, and status effects.

## Features

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

- **Move Categories**
  - Physical moves use Attack vs Defense
  - Special moves use Special vs Special
  - Status moves for applying conditions

## Project Structure

```
PokemonGen1/
├── config.py              # Battle system constants
├── main.py                # Entry point and battle orchestration
├── models/
│   ├── enums.py          # Type, Status, and MoveCategory enums
│   ├── stats.py          # Stats dataclass
│   ├── move.py           # Move dataclass with PP tracking
│   └── pokemon.py        # Pokemon class with HP and status management
└── engine/
    ├── battle.py         # Turn execution and battle flow
    ├── damage.py         # Gen 1 damage calculation
    ├── status.py         # Status effect application
    └── type_chart.py     # Type effectiveness chart
```

## Requirements

- Python 3.10+

## Usage

Run the example battle:

```bash
python main.py
```

This will simulate a battle between Pikachu and Blastoise with random move selection.

## Example Output

```
=== BATALLA POKÉMON ===
Pikachu (HP: 95/95)
Blastoise (HP: 158/158)

--- Turno 1 ---

Pikachu usa Thunderbolt!
¡Es súper efectivo!
Blastoise recibe 45 de daño! (HP: 113/158)

Blastoise usa Surf!
Pikachu recibe 52 de daño! (HP: 43/95)

...
```

## Creating Custom Battles

```python
from models.pokemon import Pokemon
from models.move import Move
from models.stats import Stats
from models.enums import Type, MoveCategory
from engine.battle import execute_turn, determine_turn_order

# Create a move
tackle = Move("Tackle", Type.NORMAL, MoveCategory.PHYSICAL, 40, 100, 35, 35)

# Create a Pokemon
bulbasaur = Pokemon(
    "Bulbasaur",
    [Type.GRASS, Type.POISON],
    Stats(hp=90, attack=82, defense=83, special=100, speed=80),
    [tackle],
    level=50
)

# Run a battle
from main import run_battle
run_battle(pokemon1, pokemon2, max_turns=20)
```

## Configuration

Adjust battle constants in [config.py](config.py):

```python
CRIT_MULTIPLIER = 2              # Critical hit damage multiplier
STAB_MULTIPLIER = 1.5            # Same Type Attack Bonus
MIN_RANDOM_FACTOR = 217          # Minimum random damage factor
MAX_RANDOM_FACTOR = 255          # Maximum random damage factor
FREEZE_THAW_CHANCE = 0.2         # 20% chance to thaw per turn
PARALYSIS_FAIL_CHANCE = 0.25     # 25% chance to be fully paralyzed
```

## Gen 1 Battle Mechanics Implemented

### Damage Formula
```
damage = ((((2 * Level / 5 + 2) * Power * Attack / Defense) / 50) + 2)
         * STAB * Effectiveness * Random(217-255)/255
```

### Critical Hits
- Probability = BaseSpeed / 512
- Multiplies attack stat by 2
- Ignores stat modifiers (Gen 1 behavior)

### Type Effectiveness
- Super effective: 2x damage
- Not very effective: 0.5x damage
- No effect: 0x damage
- Stacks for dual-type Pokemon (e.g., 4x, 0.25x)

## Known Limitations

- No stat modifications (buffs/debuffs)
- No move priority system
- No confusion or flinch mechanics
- No multi-turn moves
- Random move selection only (no AI)

## License

MIT

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.
