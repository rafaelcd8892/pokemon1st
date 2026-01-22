"""Battle configuration and settings"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from models.ruleset import Ruleset


class AIType(Enum):
    """Types of AI for battle"""
    RANDOM = "random"           # Picks random moves
    # Future AI types can be added here:
    # SMART = "smart"           # Type-aware, power-aware
    # COMPETITIVE = "competitive"  # Full strategy


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


def _get_default_ruleset():
    """Get default ruleset (lazy import to avoid circular imports)."""
    from models.ruleset import STANDARD_RULES
    return STANDARD_RULES


@dataclass
class BattleSettings:
    """Configuration for a battle session"""
    battle_mode: BattleMode = BattleMode.PLAYER_VS_AI
    player_ai_type: AIType = AIType.RANDOM  # Used when autobattle
    opponent_ai_type: AIType = AIType.RANDOM
    moveset_mode: MovesetMode = MovesetMode.MANUAL
    action_delay: float = 3.0  # Seconds between actions
    ruleset: Optional['Ruleset'] = field(default=None)

    def __post_init__(self):
        """Set default ruleset if not provided."""
        if self.ruleset is None:
            self.ruleset = _get_default_ruleset()

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
            player_ai_type=AIType.RANDOM,
            opponent_ai_type=AIType.RANDOM,
            moveset_mode=MovesetMode.SMART_RANDOM,
            action_delay=4.0  # Longer delay for watching
        )

    @classmethod
    def for_autobattle(cls) -> 'BattleSettings':
        """Create settings for autobattle"""
        return cls(
            battle_mode=BattleMode.AUTOBATTLE,
            player_ai_type=AIType.RANDOM,
            opponent_ai_type=AIType.RANDOM,
            moveset_mode=MovesetMode.RANDOM,
            action_delay=3.0
        )

    @classmethod
    def default(cls) -> 'BattleSettings':
        """Create default player vs AI settings"""
        return cls(
            battle_mode=BattleMode.PLAYER_VS_AI,
            opponent_ai_type=AIType.RANDOM,
            moveset_mode=MovesetMode.MANUAL,
            action_delay=3.0
        )

    def is_autobattle(self) -> bool:
        """Check if this is an autobattle mode"""
        return self.battle_mode in (BattleMode.AUTOBATTLE, BattleMode.WATCH)
