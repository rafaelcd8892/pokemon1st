from models.enums import Type, Status
from models.stats import Stats
from models.move import Move
import random

class Pokemon:
    def __init__(self, name: str, types: list[Type], stats: Stats, moves: list[Move], level: int = 50):
        self.name = name
        self.types = types
        self.level = level
        self.base_stats = stats
        self.current_hp = stats.hp
        self.max_hp = stats.hp
        self.status = Status.NONE
        self.moves = moves
        self.sleep_counter = 0
        
    def is_alive(self) -> bool:
        return self.current_hp > 0
    
    def take_damage(self, damage: int):
        self.current_hp = max(0, self.current_hp - damage)
        
    def apply_status(self, status: Status) -> bool:
        """Aplica un estado. Retorna True si fue exitoso"""
        if self.status == Status.NONE:
            self.status = status
            if status == Status.SLEEP:
                self.sleep_counter = random.randint(1, 7)
            return True
        return False
    
    def get_hp_percentage(self) -> float:
        return (self.current_hp / self.max_hp) * 100
