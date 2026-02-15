"""AI difficulty levels for battle."""

from enum import Enum


class AIDifficulty(Enum):
    """Difficulty tiers for battle AI.

    Each tier maps to a distinct BattleAI subclass with increasing
    sophistication.  The enum is independent of trainer *style*
    (offensive / defensive / etc.) which is handled by TrainerProfile.
    """
    DEFAULT = "default"                # Random (backward compat)
    EASY = "easy"                      # Avoids obviously bad moves
    MEDIUM = "medium"                  # Type-aware, prefers super-effective
    COMPETITIVE = "competitive"        # Full damage calc, KO prediction  (Phase 2)
    PREDICTIVE = "predictive"          # Heuristic opponent modeling       (Phase 2)
    MILLENNIUM_EYE = "millennium_eye"  # Cheat mode — sees opponent action (Phase 2)
