"""Battle configuration and settings"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from models.ruleset import Ruleset
    from models.enums import BattleFormat


from engine.ai.difficulty import AIDifficulty
from engine.ai.trainer_class import TrainerStyle


# Backward-compat alias — old code that imported AIType still works.
AIType = AIDifficulty


class MovesetMode(Enum):
    """How to select movesets for Pokemon"""
    MANUAL = ("manual", "Select each move manually")
    RANDOM = ("random", "Random moves from available pool")
    PRESET = ("preset", "Competitive/recommended movesets")
    SMART_RANDOM = ("smart_random", "Random but ensures STAB and variety")

    def __init__(self, value: str, description: str):
        self._value_ = value
        self.description = description


class BattleMode(Enum):
    """Battle interaction modes"""
    PLAYER_VS_AI = ("pvai", "Player vs AI - You control your team")
    AUTOBATTLE = ("auto", "Autobattle - AI controls both teams")
    WATCH = ("watch", "Watch Mode - Autobattle with longer delays")

    def __init__(self, value: str, description: str):
        self._value_ = value
        self.description = description


class TeamSelectMode(Enum):
    """How to select teams"""
    MANUAL = ("manual", "Elige tu equipo manualmente")
    RANDOM = ("random", "Equipo aleatorio")

    def __init__(self, value: str, description: str):
        self._value_ = value
        self.description = description


# Waiting time options for the config form
WAITING_TIME_OPTIONS = [
    (0.0, "Inmediato"),
    (3.0, "3 segundos"),
    (4.0, "4 segundos"),
]


def _get_default_ruleset():
    """Get default ruleset (lazy import to avoid circular imports)."""
    from models.ruleset import STANDARD_RULES
    return STANDARD_RULES


def _get_default_format():
    """Get default battle format (lazy import to avoid circular imports)."""
    from models.enums import BattleFormat
    return BattleFormat.TRIPLE


@dataclass
class BattleSettings:
    """Configuration for a battle session"""
    battle_mode: BattleMode = BattleMode.PLAYER_VS_AI
    player_ai_difficulty: AIDifficulty = AIDifficulty.DEFAULT  # Used when autobattle
    opponent_ai_difficulty: AIDifficulty = AIDifficulty.DEFAULT
    player_trainer_style: TrainerStyle = TrainerStyle.BALANCED
    opponent_trainer_style: TrainerStyle = TrainerStyle.BALANCED
    moveset_mode: MovesetMode = MovesetMode.MANUAL
    action_delay: float = 3.0  # Seconds between actions
    ruleset: Optional['Ruleset'] = field(default=None)
    battle_format: Optional['BattleFormat'] = field(default=None)
    team_select_mode: TeamSelectMode = TeamSelectMode.RANDOM

    def __post_init__(self):
        """Set default ruleset if not provided."""
        if self.ruleset is None:
            self.ruleset = _get_default_ruleset()
        if self.battle_format is None:
            self.battle_format = _get_default_format()

    @classmethod
    def quick_start(cls) -> 'BattleSettings':
        """Create settings for instant AI vs AI battle (Poke Cup 3v3)"""
        from models.ruleset import POKE_CUP_RULES
        from models.enums import BattleFormat
        return cls(
            battle_mode=BattleMode.AUTOBATTLE,
            moveset_mode=MovesetMode.SMART_RANDOM,
            action_delay=0.0,
            ruleset=POKE_CUP_RULES,
            battle_format=BattleFormat.TRIPLE,
            team_select_mode=TeamSelectMode.RANDOM,
        )

    @classmethod
    def for_cup(cls, ruleset: 'Ruleset') -> 'BattleSettings':
        """Create settings for a specific cup/ruleset"""
        return cls(
            ruleset=ruleset,
            moveset_mode=MovesetMode.SMART_RANDOM,
        )

    @classmethod
    def for_watch_mode(cls) -> 'BattleSettings':
        """Create settings optimized for watch mode"""
        return cls(
            battle_mode=BattleMode.WATCH,
            player_ai_difficulty=AIDifficulty.DEFAULT,
            opponent_ai_difficulty=AIDifficulty.DEFAULT,
            moveset_mode=MovesetMode.SMART_RANDOM,
            action_delay=4.0  # Longer delay for watching
        )

    @classmethod
    def for_autobattle(cls) -> 'BattleSettings':
        """Create settings for autobattle"""
        return cls(
            battle_mode=BattleMode.AUTOBATTLE,
            player_ai_difficulty=AIDifficulty.DEFAULT,
            opponent_ai_difficulty=AIDifficulty.DEFAULT,
            moveset_mode=MovesetMode.RANDOM,
            action_delay=3.0
        )

    @classmethod
    def default(cls) -> 'BattleSettings':
        """Create default player vs AI settings"""
        return cls(
            battle_mode=BattleMode.PLAYER_VS_AI,
            opponent_ai_difficulty=AIDifficulty.DEFAULT,
            moveset_mode=MovesetMode.MANUAL,
            action_delay=3.0
        )

    def is_autobattle(self) -> bool:
        """Check if this is an autobattle mode"""
        return self.battle_mode in (BattleMode.AUTOBATTLE, BattleMode.WATCH)
