"""Trainer class system — style overlay for AI behavior.

The AI system has two axes:
  - **Difficulty** (AIDifficulty) — *how well* the AI plays
  - **Trainer style** (TrainerStyle / TrainerProfile) — *what* it prioritises

A TrainerProfile is a bag of numeric weights that AI classes read during
scoring.  This avoids N×M subclass explosion: 6 difficulties × 5 styles
= 6 classes + 5 data presets instead of 30 subclasses.

Example usage:
    ai = create_ai(AIDifficulty.COMPETITIVE, profile=TrainerProfile.offensive())
    # → CompetitiveAI that weights raw damage over status or defense
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Set

from models.enums import Type


class TrainerStyle(Enum):
    """High-level gameplay style archetypes."""

    BALANCED = "balanced"
    OFFENSIVE = "offensive"
    DEFENSIVE = "defensive"
    STATUS_FOCUSED = "status"
    TYPE_SPECIALIST = "type_specialist"


@dataclass
class TrainerProfile:
    """Numeric weights that bias AI scoring and team building.

    Weights are centered around 1.0 (neutral).  Values > 1.0 increase
    priority; values < 1.0 decrease it.  The AI multiplies its base
    scores by the relevant weight, so the final behavior is:

        effective_score = base_score * weight

    Team building weights
    ---------------------
    attack_weight        — preference for high-Attack Pokemon
    defense_weight       — preference for bulky Pokemon
    speed_weight         — preference for fast Pokemon
    status_move_weight   — likelihood of including status moves in movesets

    Battle behavior weights
    -----------------------
    switch_threshold     — how easily the AI switches out (lower = more eager)
    aggression           — multiplier on damage-based scores
    status_priority      — bonus for inflicting status conditions
    setup_priority       — bonus for stat-boosting moves when safe

    Type specialist
    ---------------
    specialist_types     — if non-empty, team building restricts to these types
    """

    style: TrainerStyle = TrainerStyle.BALANCED

    # Team building weights
    attack_weight: float = 1.0
    defense_weight: float = 1.0
    speed_weight: float = 1.0
    status_move_weight: float = 1.0

    # Battle behavior weights
    switch_threshold: float = 0.35
    aggression: float = 1.0
    status_priority: float = 1.0
    setup_priority: float = 1.0

    # Type specialist
    specialist_types: Set[Type] = field(default_factory=set)

    # ---- Factory methods for common presets --------------------------------

    @classmethod
    def balanced(cls) -> 'TrainerProfile':
        """Neutral profile — no bias in any direction."""
        return cls(style=TrainerStyle.BALANCED)

    @classmethod
    def offensive(cls) -> 'TrainerProfile':
        """High aggression, low switching, fast + strong Pokemon."""
        return cls(
            style=TrainerStyle.OFFENSIVE,
            attack_weight=1.5,
            defense_weight=0.6,
            speed_weight=1.3,
            status_move_weight=0.4,
            switch_threshold=0.50,   # harder to convince to switch
            aggression=1.4,
            status_priority=0.3,
            setup_priority=0.5,
        )

    @classmethod
    def defensive(cls) -> 'TrainerProfile':
        """Bulk over speed, eager to switch, values status."""
        return cls(
            style=TrainerStyle.DEFENSIVE,
            attack_weight=0.7,
            defense_weight=1.5,
            speed_weight=0.8,
            status_move_weight=1.3,
            switch_threshold=0.25,   # switches more readily
            aggression=0.7,
            status_priority=1.3,
            setup_priority=1.4,
        )

    @classmethod
    def status_focused(cls) -> 'TrainerProfile':
        """Prioritises status infliction and stat manipulation."""
        return cls(
            style=TrainerStyle.STATUS_FOCUSED,
            attack_weight=0.8,
            defense_weight=1.0,
            speed_weight=1.2,       # speed matters for status moves
            status_move_weight=1.8,
            switch_threshold=0.30,
            aggression=0.6,
            status_priority=1.8,
            setup_priority=1.5,
        )

    @classmethod
    def type_specialist(cls, types: Set[Type]) -> 'TrainerProfile':
        """Team restricted to specified types; otherwise balanced play."""
        return cls(
            style=TrainerStyle.TYPE_SPECIALIST,
            specialist_types=set(types),
        )
