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
    
    def has_pp(self) -> bool:
        return self.pp > 0
    
    def use(self):
        """Reduce PP al usar el movimiento"""
        if self.has_pp():
            self.pp -= 1

