"""Gen 1 Individual Values (DVs) for Pokemon stats."""

import random
from dataclasses import dataclass


@dataclass
class IVs:
    """
    Gen 1 Individual Values (historically called DVs - Determinant Values).

    In Gen 1, each stat (except HP) has an IV ranging from 0-15.
    HP IV is derived from the other four IVs using a specific formula.

    Perfect IVs (all 15s) are used for competitive battles.
    Random IVs are used for wild Pokemon encounters.
    """
    attack: int = 15
    defense: int = 15
    special: int = 15
    speed: int = 15

    def __post_init__(self):
        """Validate IV ranges."""
        for stat_name in ['attack', 'defense', 'special', 'speed']:
            value = getattr(self, stat_name)
            if not 0 <= value <= 15:
                raise ValueError(f"{stat_name} IV must be between 0 and 15, got {value}")

    @property
    def hp(self) -> int:
        """
        HP IV is derived from other IVs in Gen 1.

        Formula: HP DV = (Attack & 1) << 3 | (Defense & 1) << 2 | (Speed & 1) << 1 | (Special & 1)

        This means HP IV is composed of the least significant bit of each other IV,
        resulting in a value from 0-15.
        """
        return ((self.attack & 1) << 3) | \
               ((self.defense & 1) << 2) | \
               ((self.speed & 1) << 1) | \
               (self.special & 1)

    @classmethod
    def random(cls) -> 'IVs':
        """Generate random IVs (0-15 for each stat)."""
        return cls(
            attack=random.randint(0, 15),
            defense=random.randint(0, 15),
            special=random.randint(0, 15),
            speed=random.randint(0, 15)
        )

    @classmethod
    def perfect(cls) -> 'IVs':
        """Create perfect IVs (all 15s)."""
        return cls(attack=15, defense=15, special=15, speed=15)

    @classmethod
    def zero(cls) -> 'IVs':
        """Create zero IVs (all 0s) - worst possible."""
        return cls(attack=0, defense=0, special=0, speed=0)

    def __repr__(self) -> str:
        return f"IVs(hp={self.hp}, atk={self.attack}, def={self.defense}, spe={self.speed}, spc={self.special})"
