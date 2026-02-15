"""Tests for engine/ai/evaluator.py — pure evaluation functions.

These tests require no RNG setup because the evaluator never calls RNG.
"""

import pytest
from models.enums import Type, MoveCategory, Status
from tests.conftest import create_test_pokemon, create_test_move
from engine.ai.evaluator import estimate_damage, evaluate_move, evaluate_all_moves


class TestEstimateDamage:
    """Tests for estimate_damage — the core damage estimation function."""

    def test_status_move_returns_zero(self):
        """STATUS moves always return 0 estimated damage."""
        attacker = create_test_pokemon(types=[Type.NORMAL])
        defender = create_test_pokemon(types=[Type.NORMAL])
        status_move = create_test_move(
            name="Thunder Wave", move_type=Type.ELECTRIC,
            category=MoveCategory.STATUS, power=0,
        )
        assert estimate_damage(attacker, defender, status_move) == 0

    def test_physical_move_basic(self):
        """Basic physical damage estimation returns positive value."""
        attacker = create_test_pokemon(attack=100, types=[Type.NORMAL])
        defender = create_test_pokemon(defense=100, types=[Type.NORMAL])
        move = create_test_move(
            name="Tackle", move_type=Type.NORMAL,
            category=MoveCategory.PHYSICAL, power=40,
        )
        damage = estimate_damage(attacker, defender, move)
        assert damage > 0

    def test_stab_bonus(self):
        """STAB (Same Type Attack Bonus) increases damage."""
        attacker_stab = create_test_pokemon(attack=100, types=[Type.FIRE])
        attacker_no_stab = create_test_pokemon(attack=100, types=[Type.WATER])
        defender = create_test_pokemon(defense=100, types=[Type.NORMAL])
        fire_move = create_test_move(
            name="Ember", move_type=Type.FIRE,
            category=MoveCategory.SPECIAL, power=40,
        )
        damage_stab = estimate_damage(attacker_stab, defender, fire_move)
        damage_no_stab = estimate_damage(attacker_no_stab, defender, fire_move)
        assert damage_stab > damage_no_stab

    def test_super_effective(self):
        """Super effective moves deal more damage than neutral."""
        attacker = create_test_pokemon(attack=100, types=[Type.WATER])
        defender_neutral = create_test_pokemon(defense=100, types=[Type.NORMAL])
        defender_weak = create_test_pokemon(defense=100, types=[Type.FIRE])
        water_move = create_test_move(
            name="Surf", move_type=Type.WATER,
            category=MoveCategory.SPECIAL, power=95,
        )
        damage_neutral = estimate_damage(attacker, defender_neutral, water_move)
        damage_super = estimate_damage(attacker, defender_weak, water_move)
        assert damage_super > damage_neutral

    def test_immune_returns_zero(self):
        """Immune matchups return 0 damage."""
        attacker = create_test_pokemon(types=[Type.NORMAL])
        defender = create_test_pokemon(types=[Type.GHOST])
        normal_move = create_test_move(
            name="Tackle", move_type=Type.NORMAL,
            category=MoveCategory.PHYSICAL, power=40,
        )
        assert estimate_damage(attacker, defender, normal_move) == 0

    def test_fixed_damage_move(self):
        """Dragon Rage always returns 40."""
        attacker = create_test_pokemon(types=[Type.DRAGON])
        defender = create_test_pokemon(types=[Type.NORMAL])
        dragon_rage = create_test_move(
            name="Dragon Rage", move_type=Type.DRAGON,
            category=MoveCategory.SPECIAL, power=1,
        )
        assert estimate_damage(attacker, defender, dragon_rage) == 40

    def test_fixed_damage_immune(self):
        """Fixed damage moves return 0 on immune types (Dragon Rage vs Dragon type is not immune, but Sonic Boom vs Ghost)."""
        attacker = create_test_pokemon(types=[Type.NORMAL])
        defender = create_test_pokemon(types=[Type.GHOST])
        sonic_boom = create_test_move(
            name="Sonic Boom", move_type=Type.NORMAL,
            category=MoveCategory.SPECIAL, power=1,
        )
        assert estimate_damage(attacker, defender, sonic_boom) == 0

    def test_level_damage_move(self):
        """Night Shade deals damage equal to user's level."""
        attacker = create_test_pokemon(types=[Type.GHOST], level=50)
        defender = create_test_pokemon(types=[Type.NORMAL])
        night_shade = create_test_move(
            name="Night Shade", move_type=Type.GHOST,
            category=MoveCategory.SPECIAL, power=1,
        )
        # Ghost vs Normal is immune in Gen 1
        assert estimate_damage(attacker, defender, night_shade) == 0

    def test_level_damage_move_non_immune(self):
        """Seismic Toss deals damage equal to user's level."""
        attacker = create_test_pokemon(types=[Type.FIGHTING], level=50)
        defender = create_test_pokemon(types=[Type.NORMAL])
        seismic_toss = create_test_move(
            name="Seismic Toss", move_type=Type.FIGHTING,
            category=MoveCategory.PHYSICAL, power=1,
        )
        assert estimate_damage(attacker, defender, seismic_toss) == 50

    def test_burn_halves_physical(self):
        """Burned attacker deals half physical damage."""
        attacker_normal = create_test_pokemon(attack=100, types=[Type.NORMAL])
        attacker_burned = create_test_pokemon(attack=100, types=[Type.NORMAL])
        attacker_burned.status = Status.BURN
        defender = create_test_pokemon(defense=100, types=[Type.NORMAL])
        move = create_test_move(
            name="Tackle", move_type=Type.NORMAL,
            category=MoveCategory.PHYSICAL, power=50,
        )
        damage_normal = estimate_damage(attacker_normal, defender, move)
        damage_burned = estimate_damage(attacker_burned, defender, move)
        assert damage_burned < damage_normal
        # Should be approximately half
        assert damage_burned == int(damage_normal * 0.5)

    def test_minimum_one_damage(self):
        """Non-immune hits always deal at least 1 damage."""
        attacker = create_test_pokemon(attack=1, types=[Type.NORMAL])
        defender = create_test_pokemon(defense=255, types=[Type.NORMAL])
        weak_move = create_test_move(
            name="Scratch", move_type=Type.NORMAL,
            category=MoveCategory.PHYSICAL, power=10,
        )
        assert estimate_damage(attacker, defender, weak_move) >= 1


class TestEvaluateMove:
    """Tests for evaluate_move — single move scoring."""

    def test_immune_move_flagged(self):
        """Immune moves have is_immune=True and score 0."""
        attacker = create_test_pokemon(types=[Type.NORMAL])
        defender = create_test_pokemon(types=[Type.GHOST])
        move = create_test_move(
            name="Tackle", move_type=Type.NORMAL,
            category=MoveCategory.PHYSICAL, power=40,
        )
        result = evaluate_move(attacker, defender, move)
        assert result.is_immune is True
        assert result.estimated_damage == 0

    def test_status_move_flagged(self):
        """Status moves have is_status=True."""
        attacker = create_test_pokemon(types=[Type.ELECTRIC])
        defender = create_test_pokemon(types=[Type.NORMAL])
        move = create_test_move(
            name="Thunder Wave", move_type=Type.ELECTRIC,
            category=MoveCategory.STATUS, power=0,
            status_effect=Status.PARALYSIS, status_chance=100,
        )
        result = evaluate_move(attacker, defender, move)
        assert result.is_status is True
        assert result.has_status_effect is True

    def test_status_bonus_when_no_condition(self):
        """Status moves get a bonus when defender has no status."""
        attacker = create_test_pokemon(types=[Type.ELECTRIC])
        defender = create_test_pokemon(types=[Type.NORMAL])
        move = create_test_move(
            name="Thunder Wave", move_type=Type.ELECTRIC,
            category=MoveCategory.STATUS, power=0,
            status_effect=Status.PARALYSIS, status_chance=100,
        )
        result = evaluate_move(attacker, defender, move)
        assert result.score > 0  # Got bonus because defender has no status

    def test_no_status_bonus_when_already_statused(self):
        """Status moves get no bonus when defender already has a status."""
        attacker = create_test_pokemon(types=[Type.ELECTRIC])
        defender = create_test_pokemon(types=[Type.NORMAL])
        defender.status = Status.BURN
        move = create_test_move(
            name="Thunder Wave", move_type=Type.ELECTRIC,
            category=MoveCategory.STATUS, power=0,
            status_effect=Status.PARALYSIS, status_chance=100,
        )
        result = evaluate_move(attacker, defender, move)
        # Score should be 0 — no damage, no bonus
        assert result.score == 0.0

    def test_super_effective_bonus(self):
        """Super-effective moves get a score multiplier."""
        attacker = create_test_pokemon(attack=100, types=[Type.WATER])
        defender = create_test_pokemon(defense=100, types=[Type.FIRE])
        move = create_test_move(
            name="Surf", move_type=Type.WATER,
            category=MoveCategory.SPECIAL, power=95,
        )
        result = evaluate_move(attacker, defender, move)
        assert result.effectiveness >= 2.0
        # Score should include the 1.2x bonus
        base_est = float(result.estimated_damage)
        assert result.score >= base_est

    def test_self_destruct_penalty(self):
        """Self-Destruct moves get a score penalty."""
        attacker = create_test_pokemon(attack=100, types=[Type.NORMAL])
        defender = create_test_pokemon(defense=100, types=[Type.NORMAL])
        explosion = create_test_move(
            name="Explosion", move_type=Type.NORMAL,
            category=MoveCategory.PHYSICAL, power=250,
        )
        result = evaluate_move(attacker, defender, explosion)
        assert result.is_self_destruct is True
        # Score should be penalized (0.5x)
        assert result.score < result.estimated_damage


class TestEvaluateAllMoves:
    """Tests for evaluate_all_moves — batch scoring sorted best-first."""

    def test_sorted_best_first(self):
        """Returned list is sorted by descending score."""
        attacker = create_test_pokemon(attack=100, types=[Type.WATER])
        defender = create_test_pokemon(defense=80, types=[Type.FIRE])
        moves = [
            create_test_move("Splash", Type.NORMAL, MoveCategory.STATUS, 0),
            create_test_move("Surf", Type.WATER, MoveCategory.SPECIAL, 95),
            create_test_move("Tackle", Type.NORMAL, MoveCategory.PHYSICAL, 40),
        ]
        results = evaluate_all_moves(attacker, defender, moves)
        assert len(results) == 3
        for i in range(len(results) - 1):
            assert results[i].score >= results[i + 1].score

    def test_super_effective_ranked_first(self):
        """Super-effective move should rank above neutral/resisted."""
        attacker = create_test_pokemon(attack=100, types=[Type.WATER])
        defender = create_test_pokemon(defense=80, types=[Type.FIRE])
        moves = [
            create_test_move("Tackle", Type.NORMAL, MoveCategory.PHYSICAL, 40),
            create_test_move("Surf", Type.WATER, MoveCategory.SPECIAL, 95),
        ]
        results = evaluate_all_moves(attacker, defender, moves)
        assert results[0].move.name == "Surf"
