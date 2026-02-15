"""Abstract base class for all battle AI implementations."""

from abc import ABC, abstractmethod
from typing import Optional

from models.team import Team
from models.move import Move
from engine.team_battle import BattleAction


class BattleAI(ABC):
    """Strategy interface that every AI difficulty must implement.

    Design notes:
    - *choose_action* and *choose_forced_switch* are the two decision
      points that TeamBattle's run_battle loop requires.
    - *notify_opponent_action* is a no-op hook; only Millennium Eye AI
      (Phase 2) overrides it to receive the opponent's chosen action
      before its own is finalised.
    - Shared helpers (_get_legal_moves) live here so subclasses stay DRY.
    """

    def __init__(self, clauses=None, profile=None):
        """
        Args:
            clauses: Optional BattleClauses for filtering banned moves.
            profile: Optional TrainerProfile for style-biased scoring.
                     Defaults to TrainerProfile.balanced() if None.
        """
        from engine.ai.trainer_class import TrainerProfile

        self.clauses = clauses
        self.profile = profile if profile is not None else TrainerProfile.balanced()

    # ------------------------------------------------------------------
    # Abstract decision points
    # ------------------------------------------------------------------

    @abstractmethod
    def choose_action(self, team: Team, opponent_team: Team) -> BattleAction:
        """Pick an action (attack or switch) for the current turn."""

    @abstractmethod
    def choose_forced_switch(self, team: Team) -> Optional[int]:
        """Pick a Pokemon index to switch to after a faint.

        Returns None if no switch is possible (team defeated).
        """

    # ------------------------------------------------------------------
    # Optional hooks
    # ------------------------------------------------------------------

    def notify_opponent_action(self, action: BattleAction) -> None:
        """Receive the opponent's chosen action before execution.

        Only meaningful for Millennium Eye AI. Default is no-op.
        """

    def revise_action(self) -> Optional[BattleAction]:
        """Revise the last chosen action after seeing opponent's choice.

        Called after notify_opponent_action.  Returns a replacement
        BattleAction, or None to keep the original.  Default is no-op.
        """
        return None

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _get_legal_moves(self, team: Team) -> list[Move]:
        """Return moves with PP, filtered by active clauses."""
        active = team.active_pokemon
        available = [m for m in active.moves if m.has_pp()]

        if self.clauses is not None:
            from engine.clauses import is_move_banned_by_clauses
            legal = [m for m in available if not is_move_banned_by_clauses(m, self.clauses)]
            if legal:
                return legal

        return available
