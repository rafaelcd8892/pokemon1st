"""Default AI — bit-identical port of get_random_ai_action.

This exists so that every difficulty level, including "random", goes
through the BattleAI strategy interface.  The RNG call order is
intentionally preserved so seeded battles produce identical results.
"""

from typing import Optional

from logging_config import get_logger

from models.team import Team
from engine.team_battle import BattleAction
from engine.rng import get_rng, RNGContext
from engine.ai.base import BattleAI

logger = get_logger(__name__)


class DefaultAI(BattleAI):
    """Random AI — picks random moves, 30 % switch chance when low HP.

    Replicates the original ``get_random_ai_action`` / ``get_random_forced_switch``
    from ``engine/team_battle.py`` with the same RNG consumption order.
    """

    def choose_action(self, team: Team, opponent_team: Team) -> BattleAction:
        active = team.active_pokemon

        # 30 % chance to switch when HP < 30 %
        if team.can_switch() and active.current_hp < active.max_hp * 0.3:
            if get_rng().random(RNGContext.AI_DECISION) < 0.3:
                available = team.get_available_switches()
                switch_idx = get_rng().choice(available, RNGContext.AI_DECISION)[0]
                logger.debug(f"AI switching to index {switch_idx}")
                return BattleAction.switch(switch_idx)

        # Pick a random legal move
        available_moves = self._get_legal_moves(team)

        if available_moves:
            move = get_rng().choice(available_moves, RNGContext.AI_DECISION)
            return BattleAction.attack(move)

        # No moves with PP — Struggle fallback
        return BattleAction.attack(active.moves[0])

    def choose_forced_switch(self, team: Team) -> Optional[int]:
        available = team.get_available_switches()
        if available:
            return get_rng().choice(available, RNGContext.AI_DECISION)[0]
        return None
