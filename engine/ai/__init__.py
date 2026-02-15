"""AI system for Pokemon Gen 1 battle engine.

Public API:
    BattleAI        — abstract base class (strategy interface)
    AIDifficulty    — enum of difficulty tiers
    create_ai()     — factory function: difficulty -> BattleAI instance
    TrainerStyle    — enum of gameplay style archetypes
    TrainerProfile  — data overlay for style-biased AI scoring
"""

from engine.ai.base import BattleAI
from engine.ai.difficulty import AIDifficulty
from engine.ai.factory import create_ai
from engine.ai.trainer_class import TrainerStyle, TrainerProfile

__all__ = [
    "BattleAI",
    "AIDifficulty",
    "create_ai",
    "TrainerStyle",
    "TrainerProfile",
]
