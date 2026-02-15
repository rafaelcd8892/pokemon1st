"""Easy AI — avoids obviously bad moves.

Filters out:
  - Moves the target is immune to
  - Self-Destruct when not desperate (team has other healthy Pokemon)
  - Disabled moves
Picks randomly from remaining legal moves. Never proactively switches.
"""

from typing import Optional

from models.team import Team
from models.move import Move
from engine.team_battle import BattleAction
from engine.type_chart import get_effectiveness
from engine.move_effects import SELF_DESTRUCT_MOVES
from engine.rng import get_rng, RNGContext
from engine.ai.base import BattleAI


class EasyAI(BattleAI):
    """One step above random — avoids the worst choices."""

    def choose_action(self, team: Team, opponent_team: Team) -> BattleAction:
        active = team.active_pokemon
        defender = opponent_team.active_pokemon
        legal_moves = self._get_legal_moves(team)

        if not legal_moves:
            return BattleAction.attack(active.moves[0])

        filtered = self._filter_bad_moves(legal_moves, active, defender, team)

        if not filtered:
            # All moves were bad — fall back to full legal list
            filtered = legal_moves

        move = get_rng().choice(filtered, RNGContext.AI_DECISION)
        return BattleAction.attack(move)

    def choose_forced_switch(self, team: Team) -> Optional[int]:
        available = team.get_available_switches()
        if available:
            return get_rng().choice(available, RNGContext.AI_DECISION)[0]
        return None

    # ------------------------------------------------------------------
    # Filtering helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _filter_bad_moves(
        moves: list[Move], attacker, defender, team: Team
    ) -> list[Move]:
        """Remove moves that are obviously terrible choices."""
        good: list[Move] = []
        for m in moves:
            # Skip disabled moves
            if hasattr(attacker, 'disabled_move') and attacker.disabled_move == m.name:
                continue

            # Skip moves the target is immune to (except status moves)
            from models.enums import MoveCategory
            if m.category != MoveCategory.STATUS:
                eff = get_effectiveness(m.type, defender.types)
                if eff == 0:
                    continue

            # Skip Self-Destruct/Explosion when team still has healthy reserves
            if m.name in SELF_DESTRUCT_MOVES:
                alive_reserves = sum(
                    1 for i, p in enumerate(team.pokemon)
                    if i != team.active_index and p.is_alive()
                )
                if alive_reserves > 0:
                    continue

            good.append(m)
        return good
