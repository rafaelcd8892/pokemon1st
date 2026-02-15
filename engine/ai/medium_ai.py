"""Medium AI — type-aware move selection with basic switching.

Uses the evaluator to score every legal move and picks the best one.
Adds basic switching logic: if all available moves are immune/resisted
*and* a teammate has super-effective coverage, switch to that teammate.

Forced switches prefer a Pokemon with type advantage over the opponent's
active Pokemon.
"""

from typing import Optional

from models.team import Team
from engine.team_battle import BattleAction
from engine.type_chart import get_effectiveness
from engine.rng import get_rng, RNGContext
from engine.ai.base import BattleAI
from engine.ai.evaluator import evaluate_all_moves, MoveScore


class MediumAI(BattleAI):
    """Type-aware AI with basic switching heuristics."""

    def choose_action(self, team: Team, opponent_team: Team) -> BattleAction:
        active = team.active_pokemon
        defender = opponent_team.active_pokemon
        legal_moves = self._get_legal_moves(team)

        if not legal_moves:
            return BattleAction.attack(active.moves[0])

        scored = evaluate_all_moves(active, defender, legal_moves)

        # Apply profile biases (aggression for damage, status_priority for status)
        if self.profile.aggression != 1.0 or self.profile.status_priority != 1.0:
            for ms in scored:
                if ms.estimated_damage > 0:
                    ms.score *= self.profile.aggression
                if ms.is_status and ms.has_status_effect:
                    ms.score *= self.profile.status_priority

        # Consider switching if current matchup is terrible
        switch_target = self._consider_switch(scored, team, defender)
        if switch_target is not None:
            return BattleAction.switch(switch_target)

        # Pick the highest-scored move.  On ties, RNG breaks it.
        best_score = scored[0].score
        tied = [s for s in scored if s.score == best_score]
        if len(tied) > 1:
            chosen = get_rng().choice(tied, RNGContext.AI_DECISION)
        else:
            chosen = tied[0]

        return BattleAction.attack(chosen.move)

    def choose_forced_switch(self, team: Team) -> Optional[int]:
        available = team.get_available_switches()
        if not available:
            return None

        # Prefer a Pokemon with type advantage over the opponent.
        # On forced switch we don't have direct access to opponent_team,
        # so fall back to random if we can't determine advantage.
        # (BattleAI.choose_forced_switch only receives the team.)
        return self._pick_best_switch(available)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _consider_switch(
        self, scored: list[MoveScore], team: Team, defender
    ) -> Optional[int]:
        """Return a switch index if the current matchup is hopeless."""
        if not team.can_switch():
            return None

        # If the best move scores poorly (all immune or very low damage),
        # look for a teammate with super-effective coverage.
        best = scored[0] if scored else None
        if best is None:
            return None

        # "Terrible matchup" heuristic: best estimated damage < 10 % of
        # defender HP *and* at least one move is immune.
        threshold = defender.max_hp * 0.10
        all_bad = best.estimated_damage < threshold
        any_immune = any(s.is_immune for s in scored)

        if not (all_bad and any_immune):
            return None

        # Search reserves for a Pokemon with at least one super-effective move
        available = team.get_available_switches()
        for idx, poke in available:
            for m in poke.moves:
                if m.has_pp():
                    eff = get_effectiveness(m.type, defender.types)
                    if eff >= 2.0:
                        return idx

        return None

    @staticmethod
    def _pick_best_switch(available: list[tuple[int, 'Pokemon']]) -> int:
        """Among available switches, pick the one with highest HP %."""
        best_idx = available[0][0]
        best_ratio = 0.0
        for idx, poke in available:
            ratio = poke.current_hp / poke.max_hp if poke.max_hp > 0 else 0.0
            if ratio > best_ratio:
                best_ratio = ratio
                best_idx = idx
        return best_idx
