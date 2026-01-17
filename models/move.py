from dataclasses import dataclass
from typing import Optional
from models.enums import Type, Status, MoveCategory

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
    
    def has_pp(self) -> bool:
        return self.pp > 0
    
    def use(self):
        """Reduce PP al usar el movimiento"""
        if self.has_pp():
            self.pp -= 1

