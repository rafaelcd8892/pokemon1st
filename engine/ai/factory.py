"""Factory function for creating AI instances."""

from engine.ai.difficulty import AIDifficulty
from engine.ai.base import BattleAI
from engine.ai.default_ai import DefaultAI
from engine.ai.easy_ai import EasyAI
from engine.ai.medium_ai import MediumAI
from engine.ai.competitive_ai import CompetitiveAI
from engine.ai.predictive_ai import PredictiveAI
from engine.ai.millennium_eye_ai import MillenniumEyeAI


_AI_CLASSES: dict[AIDifficulty, type[BattleAI]] = {
    AIDifficulty.DEFAULT: DefaultAI,
    AIDifficulty.EASY: EasyAI,
    AIDifficulty.MEDIUM: MediumAI,
    AIDifficulty.COMPETITIVE: CompetitiveAI,
    AIDifficulty.PREDICTIVE: PredictiveAI,
    AIDifficulty.MILLENNIUM_EYE: MillenniumEyeAI,
}


def create_ai(
    difficulty: AIDifficulty = AIDifficulty.DEFAULT,
    clauses=None,
    profile=None,
) -> BattleAI:
    """Create a BattleAI instance for the given difficulty.

    Args:
        difficulty: The AI difficulty tier.
        clauses: Optional BattleClauses for filtering banned moves.
        profile: Optional TrainerProfile for style-biased scoring (Phase 3).

    Returns:
        A ready-to-use BattleAI.

    Raises:
        ValueError: If the difficulty is not yet implemented.
    """
    cls = _AI_CLASSES.get(difficulty)
    if cls is None:
        raise ValueError(
            f"AI difficulty {difficulty.value!r} is not yet implemented. "
            f"Available: {[d.value for d in _AI_CLASSES]}"
        )
    return cls(clauses=clauses, profile=profile)
