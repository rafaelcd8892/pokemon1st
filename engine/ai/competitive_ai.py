"""Competitive AI — full damage calculation with strategic depth.

Uses the evaluator for every legal move, then applies layered heuristics:
  - KO priority: if a move can knock out, strongly prefer it.
  - Status timing: value inflicting status early, devalue when opponent
    is already weakened.
  - Stat setup: boost moves valued when safe (opponent can't KO this turn).
  - Smart switching via should_switch() — not just "all moves are immune"
    but "incoming threat is high and a better matchup exists".
"""

from typing import Optional

from models.team import Team
from engine.team_battle import BattleAction
from engine.rng import get_rng, RNGContext
from engine.ai.base import BattleAI
from engine.ai.evaluator import (
    evaluate_all_moves,
    estimate_damage,
    threat_score,
    should_switch,
    score_switch_target,
    MoveScore,
)


class CompetitiveAI(BattleAI):
    """Strategic AI with damage calc, KO detection, and smart switching."""

    def choose_action(self, team: Team, opponent_team: Team) -> BattleAction:
        active = team.active_pokemon
        defender = opponent_team.active_pokemon
        self._last_opponent_active = defender
        legal_moves = self._get_legal_moves(team)

        if not legal_moves:
            return BattleAction.attack(active.moves[0])

        # Score every legal move with base evaluator
        scored = evaluate_all_moves(active, defender, legal_moves)

        # Apply profile-driven aggression scaling
        aggression = self.profile.aggression
        if aggression != 1.0:
            for ms in scored:
                if ms.estimated_damage > 0:
                    ms.score *= aggression

        # Apply competitive-level adjustments
        self._apply_ko_bonus(scored, defender)
        self._apply_status_timing(scored, defender, self.profile.status_priority)
        self._apply_setup_bonus(scored, active, defender, self.profile.setup_priority)

        # Re-sort after adjustments
        scored.sort(key=lambda s: s.score, reverse=True)

        # Consider smart switching
        switch_threshold = 0.35
        if self.profile and hasattr(self.profile, 'switch_threshold'):
            switch_threshold = self.profile.switch_threshold

        do_switch, switch_idx = should_switch(team, defender, switch_threshold)
        if do_switch and switch_idx is not None:
            # Only switch if the best switch-in scores meaningfully better
            # than our best available move
            best_move_score = scored[0].score if scored else 0.0
            switch_candidate = team.pokemon[switch_idx]
            switch_sc = score_switch_target(switch_candidate, defender, active)
            # Compare: switch score vs best move score (normalized)
            if switch_sc > best_move_score * 0.6:
                return BattleAction.switch(switch_idx)

        # Pick best move; break ties with RNG
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

        # Use score_switch_target if we remember the opponent.
        # On forced switch we don't receive opponent_team, so use the
        # stored reference if available, else pick healthiest.
        if hasattr(self, '_last_opponent_active') and self._last_opponent_active:
            return self._pick_best_switch_scored(available, self._last_opponent_active, team.active_pokemon)

        return self._pick_healthiest(available)

    # ------------------------------------------------------------------
    # Competitive heuristics
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_ko_bonus(scored: list[MoveScore], defender) -> None:
        """Massive bonus for moves that can KO the opponent."""
        for ms in scored:
            if ms.estimated_damage >= defender.current_hp and not ms.is_immune:
                ms.score += 200.0
                # Extra bonus for KO without self-destruct
                if not ms.is_self_destruct:
                    ms.score += 50.0

    @staticmethod
    def _apply_status_timing(
        scored: list[MoveScore], defender, status_priority: float = 1.0
    ) -> None:
        """Adjust status move value based on game phase.

        Status moves are most valuable when the opponent is healthy and
        has no existing condition.  They lose value as the opponent
        weakens (prefer raw damage to finish).

        The *status_priority* weight (from TrainerProfile) scales the
        final status score — higher values make status moves more
        attractive relative to damage moves.
        """
        defender_hp_ratio = defender.current_hp / defender.max_hp if defender.max_hp > 0 else 0.0

        for ms in scored:
            if ms.has_status_effect and ms.is_status:
                if defender.status != 'None' and hasattr(defender, 'status'):
                    from models.enums import Status
                    if defender.status != Status.NONE:
                        # Already statused — status moves are near-worthless
                        ms.score *= 0.1
                        continue
                # Scale value by opponent's remaining HP
                # Full HP → full bonus; 30% HP → 30% of bonus
                ms.score *= max(0.3, defender_hp_ratio)
                # Apply profile status priority
                ms.score *= status_priority

    @staticmethod
    def _apply_setup_bonus(
        scored: list[MoveScore], active, defender, setup_priority: float = 1.0
    ) -> None:
        """Bonus for stat-boosting moves when safe to set up.

        "Safe" means the opponent's best move can't KO us this turn.
        The *setup_priority* weight (from TrainerProfile) scales the
        setup bonus.
        """
        incoming_threat = threat_score(defender, active)

        for ms in scored:
            if ms.is_status and ms.move.stat_changes and ms.move.target_self:
                if incoming_threat < 0.5:
                    # Safe to boost — scale bonus by how safe we are
                    safety_factor = 1.0 - incoming_threat
                    ms.score += 40.0 * safety_factor * setup_priority
                else:
                    # Dangerous — don't waste a turn boosting
                    ms.score *= 0.3

    @staticmethod
    def _pick_best_switch_scored(available, opponent_active, own_active) -> int:
        """Pick the best switch-in using score_switch_target."""
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
        """Fallback: pick the Pokemon with the most HP remaining."""
        best_idx = available[0][0]
        best_ratio = 0.0
        for idx, poke in available:
            ratio = poke.current_hp / poke.max_hp if poke.max_hp > 0 else 0.0
            if ratio > best_ratio:
                best_ratio = ratio
                best_idx = idx
        return best_idx
