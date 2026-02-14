"""
Generation-specific mechanics resolution.

This module sits between the move/Pokemon data and the battle engine,
resolving differences in game mechanics across generations.

Key difference handled:
  - Gen 1-3: Physical/Special split is determined by the move's TYPE.
  - Gen 4+:  Physical/Special split is per-move (stored in moves.json).

The data in moves.json uses the Gen 4+ per-move categories. This module
ensures the engine applies the correct rules for the active generation.
"""

import config
from models.enums import Type, MoveCategory
from models.move import Move


# In Gen 1-3, these types use Attack/Defense (physical stats).
# All other types use Special (special stats).
PHYSICAL_TYPES: set[Type] = {
    Type.NORMAL,
    Type.FIGHTING,
    Type.POISON,
    Type.GROUND,
    Type.FLYING,
    Type.BUG,
    Type.ROCK,
    Type.GHOST,
}


def get_effective_category(move: Move) -> MoveCategory:
    """
    Resolve the effective category of a move for the active generation.

    - STATUS moves always return STATUS (generation-independent).
    - Gen 1-3: PHYSICAL/SPECIAL determined by the move's type.
    - Gen 4+:  PHYSICAL/SPECIAL determined by the move's own category.

    This allows moves.json to store the modern per-move categories
    while the engine correctly applies Gen 1 type-based rules.
    """
    if move.category == MoveCategory.STATUS:
        return MoveCategory.STATUS

    if config.GENERATION <= 3:
        return MoveCategory.PHYSICAL if move.type in PHYSICAL_TYPES else MoveCategory.SPECIAL

    # Gen 4+: per-move category from data
    return move.category


def is_physical(move: Move) -> bool:
    """Check if a move uses physical stats (Attack/Defense) in the current generation."""
    return get_effective_category(move) == MoveCategory.PHYSICAL
