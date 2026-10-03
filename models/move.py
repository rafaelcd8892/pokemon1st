from dataclasses import dataclass, field
from typing import Optional, Dict
from models.enums import Type, Status, MoveCategory, StatType

@dataclass
class Move:
    name: str
    type: Type
    category: MoveCategory
    power: int
    accuracy: int
    pp: int
    max_pp: int
    status_effect: Optional[Status] = None
    status_chance: int = 0
    # Stat changes: dict mapping StatType to stage change (-6 to +6)
    # target_self=True applies to user, False applies to target
    stat_changes: Dict[StatType, int] = field(default_factory=dict)
    target_self: bool = False  # True for moves like Swords Dance, False for Growl
    # Recoil: user takes damage_dealt // recoil_divisor (0 = no recoil)
    recoil_divisor: int = 0
    # Gen 1 mechanics data. Not yet read by the engine: each is enabled once its
    # policy is decided in docs/known_quirks.md.
    priority: int = 0                # Quick Attack +1, Counter -1
    high_crit: bool = False          # Slash, Karate Chop, Razor Leaf, Crabhammer
    flinch_chance: int = 0           # 0-100
    # Chance-based stat changes on damaging moves (e.g. Psychic: Special -1, 33%).
    # Separate from stat_changes, which always apply.
    secondary_stat_changes: Dict[StatType, int] = field(default_factory=dict)
    secondary_stat_chance: int = 0   # 0-100
    
    def has_pp(self) -> bool:
        return self.pp > 0
    
    def use(self):
        """Reduce PP al usar el movimiento"""
        if self.has_pp():
            self.pp -= 1

