from models.enums import Type, Status, StatType
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

        # Stat stages: -6 to +6 for each stat
        self.stat_stages = {
            StatType.ATTACK: 0,
            StatType.DEFENSE: 0,
            StatType.SPECIAL: 0,
            StatType.SPEED: 0,
            StatType.ACCURACY: 0,
            StatType.EVASION: 0
        }

        # Confusion tracking
        self.confusion_turns = 0
        
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
            elif status == Status.CONFUSION:
                self.confusion_turns = random.randint(1, 4)  # Gen1: 1-4 turns
            return True
        return False

    def modify_stat_stage(self, stat: StatType, stages: int) -> tuple[int, bool]:
        """
        Modifies a stat stage by the given amount.
        Returns: (actual_change, hit_limit)
        """
        old_stage = self.stat_stages[stat]
        new_stage = max(-6, min(6, old_stage + stages))
        actual_change = new_stage - old_stage
        hit_limit = (actual_change != stages)
        self.stat_stages[stat] = new_stage
        return actual_change, hit_limit

    def reset_stat_stages(self):
        """Resets all stat stages to 0"""
        for stat in self.stat_stages:
            self.stat_stages[stat] = 0

    def is_confused(self) -> bool:
        """Check if Pokemon is confused"""
        return self.confusion_turns > 0
    
    def get_hp_percentage(self) -> float:
        return (self.current_hp / self.max_hp) * 100

    def get_health_bar(self) -> str:
        """Returns a colored health bar display"""
        from engine.display import create_health_bar
        return create_health_bar(self.current_hp, self.max_hp)
