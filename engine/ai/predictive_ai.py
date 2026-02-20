"""Predictive AI — heuristic opponent modeling.

Extends CompetitiveAI's evaluation by predicting what the opponent is
likely to do, then weighing our actions against that prediction.

Key heuristic: model the opponent as a MediumAI-level player — they will
use their best type-effective move.  Then choose our action to counter
that predicted move, not just optimise against current state.

Examples of predictive behavior:
  - Opponent's Jolteon threatens our Gyarados → switch to Rhydon (immune)
  - Opponent likely to switch (bad matchup) → use a setup move
  - Opponent's best move is resisted by a teammate → switch preemptively
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
    threat_score,
    should_switch,
    score_switch_target,
    MoveScore,
)


class PredictiveAI(BattleAI):
    """AI that models the opponent's likely action and counters it."""

    def choose_action(self, team: Team, opponent_team: Team) -> BattleAction:
        active = team.active_pokemon
        defender = opponent_team.active_pokemon
        self._last_opponent_active = defender
        legal_moves = self._get_legal_moves(team)

        if not legal_moves:
            return BattleAction.attack(active.moves[0])

        # Step 1: Predict opponent's action
        predicted_move, predicted_damage = self._predict_opponent_move(
            defender, active
        )

        # Step 2: Score our moves with competitive-level evaluation
        scored = evaluate_all_moves(active, defender, legal_moves)

        # Step 3: Apply competitive bonuses (KO, status timing, setup)
        self._apply_ko_bonus(scored, defender)
        self._apply_predictive_adjustments(scored, active, defender, predicted_damage)

        scored.sort(key=lambda s: s.score, reverse=True)

        # Step 4: Predictive switching — consider switching if the
        # opponent's predicted move is very threatening.
        # BUT: never switch if we can KO the opponent this turn.
        can_ko = any(
            ms.estimated_damage >= defender.current_hp and not ms.is_immune
            for ms in scored
        )
        if not can_ko:
            switch_idx = self._predictive_switch(
                team, defender, predicted_move, predicted_damage
            )
            if switch_idx is not None:
                return BattleAction.switch(switch_idx)

        # Pick best move
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

        # Use scored switching if we remember opponent
        if hasattr(self, '_last_opponent_active') and self._last_opponent_active:
            return self._pick_best_switch_scored(
                available, self._last_opponent_active, team.active_pokemon
            )
        return self._pick_healthiest(available)

    # ------------------------------------------------------------------
    # Prediction engine
    # ------------------------------------------------------------------

    @staticmethod
    def _predict_opponent_move(
        opponent: Pokemon, our_active: Pokemon
    ) -> tuple[Optional['Move'], int]:
        """Predict the opponent's most likely move and its estimated damage.

        Models the opponent as picking their highest-damage move against
        our active Pokemon (i.e. a MediumAI-level opponent).

        Returns (best_move, estimated_damage).  best_move is None if the
        opponent has no usable moves.
        """
        best_move = None
        best_damage = 0

        for m in opponent.moves:
            if m.has_pp():
                dmg = estimate_damage(opponent, our_active, m)
                if dmg > best_damage:
                    best_damage = dmg
                    best_move = m

        return best_move, best_damage

    def _predictive_switch(
        self,
        team: Team,
        opponent_active: Pokemon,
        predicted_move,
        predicted_damage: int,
    ) -> Optional[int]:
        """Switch preemptively if the opponent's predicted move is dangerous.

        Unlike CompetitiveAI's reactive switching, this considers the
        *predicted* incoming damage, not just general threat level.
        """
        if not team.can_switch():
            return None

        active = team.active_pokemon

        # Only consider switching if predicted damage is serious
        # (> 40% of our HP)
        if active.max_hp <= 0:
            return None
        predicted_ratio = predicted_damage / active.max_hp
        if predicted_ratio < 0.40:
            return None

        # Find a switch-in that resists the predicted move type
        if predicted_move is None:
            return None

        from engine.type_chart import get_effectiveness

        available = team.get_available_switches()
        best_idx = None
        best_resist_score = 0.0

        for idx, candidate in available:
            # How well does the candidate resist the predicted move?
            eff = get_effectiveness(predicted_move.type, candidate.types)
            if eff >= 1.0:
                continue  # Doesn't resist — not helpful

            # Score: resistance quality + offensive potential
            resist_bonus = (1.0 - eff) * 50.0  # 0.5 eff → 25, 0.0 eff → 50
            offensive = score_switch_target(candidate, opponent_active, active)
            total = resist_bonus + offensive * 0.3

            if total > best_resist_score:
                best_resist_score = total
                best_idx = idx

        return best_idx

    # ------------------------------------------------------------------
    # Scoring adjustments
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_ko_bonus(scored: list[MoveScore], defender) -> None:
        """Same KO bonus as CompetitiveAI."""
        for ms in scored:
            if ms.estimated_damage >= defender.current_hp and not ms.is_immune:
                ms.score += 200.0
                if not ms.is_self_destruct:
                    ms.score += 50.0

    @staticmethod
    def _apply_predictive_adjustments(
        scored: list[MoveScore],
        active: Pokemon,
        defender: Pokemon,
        predicted_incoming: int,
    ) -> None:
        """Adjust scores based on predicted opponent action.

        If we expect to take heavy damage, prioritise immediate damage
        over setup.  If the opponent is weak and threatening, prioritise
        finishing moves.
        """
        if active.max_hp <= 0:
            return
        incoming_ratio = predicted_incoming / active.max_hp

        for ms in scored:
            # If we might faint next turn, devalue setup / status
            if incoming_ratio > 0.6:
                if ms.is_status:
                    ms.score *= 0.2  # Almost never set up when about to faint
                # Bonus for immediate damage — speed is critical
                if ms.estimated_damage > 0:
                    ms.score *= 1.3

            # Stat-boost bonus only if we're safe
            if ms.is_status and ms.move.stat_changes and ms.move.target_self:
                if incoming_ratio < 0.3:
                    ms.score += 35.0
                elif incoming_ratio > 0.5:
                    ms.score *= 0.2

    @staticmethod
    def _pick_best_switch_scored(available, opponent_active, own_active) -> int:
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
