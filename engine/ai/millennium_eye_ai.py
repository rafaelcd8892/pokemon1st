"""Millennium Eye AI — cheat mode that sees the opponent's action.

Designed for unfair boss battles.  The AI receives the opponent's
chosen action (via notify_opponent_action) before execution starts,
then revises its own action to perfectly counter it.

Counter strategies:
  - Opponent attacks → switch to a Pokemon that resists the move type.
  - Opponent switches → use that free turn to set up (stat boost) or
    attack with the strongest available move.
  - Opponent uses status → switch to a Pokemon immune to that status
    or just attack.

Requires the TeamBattle loop to call the on_actions_chosen hook.
"""

from typing import Optional

from models.team import Team
from models.pokemon import Pokemon
from engine.team_battle import BattleAction
from engine.rng import get_rng, RNGContext
from engine.ai.base import BattleAI
from engine.ai.evaluator import (
    evaluate_all_moves,
    estimate_damage,
    score_switch_target,
    MoveScore,
)


class MillenniumEyeAI(BattleAI):
    """AI that sees the opponent's action before finalising its own."""

    def __init__(self, clauses=None, profile=None):
        super().__init__(clauses=clauses, profile=profile)
        self._pending_team: Optional[Team] = None
        self._pending_opponent_team: Optional[Team] = None
        self._tentative_action: Optional[BattleAction] = None
        self._opponent_action: Optional[BattleAction] = None

    def choose_action(self, team: Team, opponent_team: Team) -> BattleAction:
        """Return a tentative action (may be revised after seeing opponent's).

        Stores team references for use in revise_action().
        """
        self._pending_team = team
        self._pending_opponent_team = opponent_team
        self._opponent_action = None

        # Tentative: use competitive-level evaluation
        self._tentative_action = self._competitive_action(team, opponent_team)
        return self._tentative_action

    def notify_opponent_action(self, action: BattleAction) -> None:
        """Receive the opponent's chosen action."""
        self._opponent_action = action

    def revise_action(self) -> Optional[BattleAction]:
        """Revise our action based on the opponent's actual choice.

        Returns a new BattleAction if revision is warranted, or None
        to keep the tentative action.
        """
        if self._opponent_action is None:
            return None
        if self._pending_team is None or self._pending_opponent_team is None:
            return None

        team = self._pending_team
        opponent_team = self._pending_opponent_team
        active = team.active_pokemon
        defender = opponent_team.active_pokemon
        opp_action = self._opponent_action

        if opp_action.is_switch():
            # Opponent is switching — free turn to set up or attack hard
            return self._counter_switch(team, opponent_team)
        else:
            # Opponent is attacking — consider switching to a resist
            return self._counter_attack(team, opponent_team, opp_action)

    def choose_forced_switch(self, team: Team) -> Optional[int]:
        available = team.get_available_switches()
        if not available:
            return None

        # Best scored switch-in
        if self._pending_opponent_team:
            opp_active = self._pending_opponent_team.active_pokemon
            return self._pick_best_switch(available, opp_active, team.active_pokemon)

        return self._pick_healthiest(available)

    # ------------------------------------------------------------------
    # Counter strategies
    # ------------------------------------------------------------------

    def _counter_switch(self, team: Team, opponent_team: Team) -> Optional[BattleAction]:
        """Opponent is switching — exploit the free turn.

        Priority:
        1. If we have a stat-boost move and it's safe, use it.
        2. Otherwise, use our strongest attack (it will hit the incoming
           Pokemon, but we don't know who that is — just use best STAB).
        """
        active = team.active_pokemon
        defender = opponent_team.active_pokemon
        legal_moves = self._get_legal_moves(team)

        if not legal_moves:
            return None

        # Look for a setup move
        for m in legal_moves:
            if m.stat_changes and m.target_self and m.power == 0:
                return BattleAction.attack(m)

        # No setup available — just use best damaging move (keep tentative)
        return None

    def _counter_attack(
        self, team: Team, opponent_team: Team, opp_action: BattleAction
    ) -> Optional[BattleAction]:
        """Opponent is attacking — switch to a resist if threatened.

        Only switch if:
        - The incoming move deals significant damage to our active.
        - We have a teammate that resists the move type.
        """
        if opp_action.move is None:
            return None

        active = team.active_pokemon
        opp_move = opp_action.move

        # Estimate incoming damage
        opponent_active = opponent_team.active_pokemon
        incoming = estimate_damage(opponent_active, active, opp_move)

        if active.max_hp <= 0:
            return None

        # Only bother switching if damage is significant (> 30% HP)
        if incoming < active.max_hp * 0.30:
            return None

        if not team.can_switch():
            return None

        # Find best resist
        from engine.type_chart import get_effectiveness

        available = team.get_available_switches()
        best_idx = None
        best_score = 0.0

        for idx, candidate in available:
            eff = get_effectiveness(opp_move.type, candidate.types)
            if eff >= 1.0:
                continue  # No resistance

            # Score: resistance quality + general position
            resist_bonus = (1.0 - eff) * 60.0
            position = score_switch_target(candidate, opponent_active, active)
            total = resist_bonus + position * 0.2

            if total > best_score:
                best_score = total
                best_idx = idx

        if best_idx is not None:
            return BattleAction.switch(best_idx)

        # No good resist — check if we can KO first
        legal_moves = self._get_legal_moves(team)
        for m in legal_moves:
            dmg = estimate_damage(active, opponent_active, m)
            if dmg >= opponent_active.current_hp:
                return BattleAction.attack(m)

        return None  # Keep tentative action

    # ------------------------------------------------------------------
    # Competitive-level tentative action
    # ------------------------------------------------------------------

    def _competitive_action(self, team: Team, opponent_team: Team) -> BattleAction:
        """CompetitiveAI-level action as the tentative choice."""
        active = team.active_pokemon
        defender = opponent_team.active_pokemon
        legal_moves = self._get_legal_moves(team)

        if not legal_moves:
            return BattleAction.attack(active.moves[0])

        scored = evaluate_all_moves(active, defender, legal_moves)

        # KO bonus
        for ms in scored:
            if ms.estimated_damage >= defender.current_hp and not ms.is_immune:
                ms.score += 200.0
                if not ms.is_self_destruct:
                    ms.score += 50.0

        scored.sort(key=lambda s: s.score, reverse=True)

        best_score = scored[0].score
        tied = [s for s in scored if s.score == best_score]
        if len(tied) > 1:
            chosen = get_rng().choice(tied, RNGContext.AI_DECISION)
        else:
            chosen = tied[0]

        return BattleAction.attack(chosen.move)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _pick_best_switch(available, opponent_active, own_active) -> int:
        best_idx = available[0][0]
        best_score = -1.0
        for idx, poke in available:
            s = score_switch_target(poke, opponent_active, own_active)
            if s > best_score:
                best_score = s
                best_idx = idx
        return best_idx

    @staticmethod
    def _pick_healthiest(available) -> int:
        best_idx = available[0][0]
        best_ratio = 0.0
        for idx, poke in available:
            ratio = poke.current_hp / poke.max_hp if poke.max_hp > 0 else 0.0
            if ratio > best_ratio:
                best_ratio = ratio
                best_idx = idx
        return best_idx
