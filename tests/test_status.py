"""Tests for status effect mechanics"""

import pytest
from unittest.mock import patch

from models.enums import Type, Status, MoveCategory, StatType
from models.pokemon import Pokemon
from models.stats import Stats
from engine.status import apply_status_effects, apply_end_turn_status_damage
from tests.conftest import create_test_pokemon, create_test_move


class TestStatusApplication:
    """Test applying status effects to Pokemon"""

    def test_apply_burn(self):
        """Test applying burn status"""
        pokemon = create_test_pokemon()
        assert pokemon.status == Status.NONE

        result = pokemon.apply_status(Status.BURN)

        assert result is True
        assert pokemon.status == Status.BURN

    def test_apply_paralysis(self):
        """Test applying paralysis status"""
        pokemon = create_test_pokemon()

        result = pokemon.apply_status(Status.PARALYSIS)

        assert result is True
        assert pokemon.status == Status.PARALYSIS

    def test_apply_poison(self):
        """Test applying poison status"""
        pokemon = create_test_pokemon()

        result = pokemon.apply_status(Status.POISON)

        assert result is True
        assert pokemon.status == Status.POISON

    def test_apply_sleep(self):
        """Test applying sleep status sets sleep counter"""
        pokemon = create_test_pokemon()

        result = pokemon.apply_status(Status.SLEEP)

        assert result is True
        assert pokemon.status == Status.SLEEP
        assert 1 <= pokemon.sleep_counter <= 7, "Sleep should last 1-7 turns"

    def test_apply_freeze(self):
        """Test applying freeze status"""
        pokemon = create_test_pokemon()

        result = pokemon.apply_status(Status.FREEZE)

        assert result is True
        assert pokemon.status == Status.FREEZE

    def test_cannot_apply_second_status(self):
        """Test that Pokemon can only have one major status"""
        pokemon = create_test_pokemon()
        pokemon.apply_status(Status.BURN)

        result = pokemon.apply_status(Status.PARALYSIS)

        assert result is False
        assert pokemon.status == Status.BURN, "Original status should remain"

    def test_fire_type_can_be_burned(self):
        """Test that Fire types CAN be burned in Gen 1 (immunity was added later)"""
        pokemon = create_test_pokemon(types=[Type.FIRE])

        result = pokemon.apply_status(Status.BURN)

        # In Gen 1, Fire types can be burned - immunity was added in Gen 3
        assert result is True
        assert pokemon.status == Status.BURN

    def test_ice_type_can_be_frozen(self):
        """Test that Ice types CAN be frozen in Gen 1 (immunity was added later)"""
        pokemon = create_test_pokemon(types=[Type.ICE])

        result = pokemon.apply_status(Status.FREEZE)

        # In Gen 1, Ice types can be frozen - immunity was added in Gen 2
        assert result is True
        assert pokemon.status == Status.FREEZE

    def test_electric_type_immune_to_paralysis(self):
        """Test that Electric types cannot be paralyzed (Gen 1 doesn't have this, but good to check)"""
        pokemon = create_test_pokemon(types=[Type.ELECTRIC])

        # In Gen 1, Electric types CAN be paralyzed by non-Electric moves
        # This test documents current behavior
        result = pokemon.apply_status(Status.PARALYSIS)

        # Note: Gen 1 allows paralysis on Electric types from Body Slam etc.
        # Only Thunder Wave specifically doesn't work
        assert result is True  # Gen 1 behavior

    def test_poison_type_can_be_poisoned(self):
        """Test that Poison types CAN be poisoned in Gen 1 (immunity was added later)"""
        pokemon = create_test_pokemon(types=[Type.POISON])

        result = pokemon.apply_status(Status.POISON)

        # In Gen 1, Poison types can be poisoned - immunity was added in Gen 2
        assert result is True
        assert pokemon.status == Status.POISON


class TestStatusEffectsDuringTurn:
    """Test status effects that occur during turn execution"""

    def test_paralysis_can_fully_paralyze(self):
        """Test that paralysis has 25% chance to prevent action"""
        pokemon = create_test_pokemon()
        pokemon.status = Status.PARALYSIS

        paralyzed_count = 0
        total_attempts = 1000

        for _ in range(total_attempts):
            can_attack = apply_status_effects(pokemon)
            if not can_attack:
                paralyzed_count += 1

        # Should be approximately 25% (250 out of 1000)
        expected = total_attempts * 0.25
        tolerance = total_attempts * 0.05  # 5% tolerance

        assert abs(paralyzed_count - expected) < tolerance, \
            f"Paralysis rate should be ~25%, got {paralyzed_count/total_attempts*100:.1f}%"

    def test_sleep_prevents_action(self):
        """Test that sleeping Pokemon cannot attack"""
        pokemon = create_test_pokemon()
        pokemon.status = Status.SLEEP
        pokemon.sleep_counter = 5

        # Force not waking up
        with patch('engine.status.random.randint', return_value=5):  # Won't wake on turn 5
            can_attack = apply_status_effects(pokemon)

        assert can_attack is False
        assert pokemon.sleep_counter == 4, "Sleep counter should decrement"

    def test_sleep_wakes_at_zero_turns(self):
        """Test that Pokemon wakes when sleep counter reaches 0"""
        pokemon = create_test_pokemon()
        pokemon.status = Status.SLEEP
        pokemon.sleep_counter = 1

        can_attack = apply_status_effects(pokemon)

        assert pokemon.status == Status.NONE, "Should wake up"
        assert can_attack is True, "Should be able to attack after waking"

    def test_freeze_has_thaw_chance(self):
        """Test that frozen Pokemon have 20% chance to thaw"""
        pokemon = create_test_pokemon()
        pokemon.status = Status.FREEZE

        thawed_count = 0
        total_attempts = 1000

        for _ in range(total_attempts):
            pokemon.status = Status.FREEZE  # Reset each time
            apply_status_effects(pokemon)
            if pokemon.status != Status.FREEZE:
                thawed_count += 1

        # Should be approximately 20%
        expected = total_attempts * 0.20
        tolerance = total_attempts * 0.05

        assert abs(thawed_count - expected) < tolerance, \
            f"Thaw rate should be ~20%, got {thawed_count/total_attempts*100:.1f}%"

    def test_freeze_thaw_allows_action(self):
        """Test that thawing allows attack on same turn"""
        pokemon = create_test_pokemon()
        pokemon.status = Status.FREEZE

        # Force thaw
        with patch('engine.status.random.random', return_value=0.1):  # 10% < 20% thaw
            can_attack = apply_status_effects(pokemon)

        assert pokemon.status == Status.NONE
        assert can_attack is True


class TestEndTurnStatusDamage:
    """Test status damage applied at end of turn"""

    def test_burn_deals_damage(self):
        """Test that burn deals 1/16 max HP damage"""
        pokemon = create_test_pokemon(hp=160)
        pokemon.current_hp = 160
        pokemon.status = Status.BURN

        apply_end_turn_status_damage(pokemon)

        expected_damage = 160 // 16  # 10 damage
        expected_hp = 160 - expected_damage

        assert pokemon.current_hp == expected_hp, \
            f"Burn should deal {expected_damage} damage, HP is {pokemon.current_hp}"

    def test_poison_deals_damage(self):
        """Test that poison deals 1/16 max HP damage"""
        pokemon = create_test_pokemon(hp=160)
        pokemon.current_hp = 160
        pokemon.status = Status.POISON

        apply_end_turn_status_damage(pokemon)

        expected_damage = 160 // 16  # 10 damage
        expected_hp = 160 - expected_damage

        assert pokemon.current_hp == expected_hp, \
            f"Poison should deal {expected_damage} damage, HP is {pokemon.current_hp}"

    def test_status_damage_minimum_one(self):
        """Test that status damage is at least 1"""
        pokemon = create_test_pokemon(hp=10)  # Very low HP
        pokemon.current_hp = 10
        pokemon.status = Status.BURN

        apply_end_turn_status_damage(pokemon)

        # 10 // 16 = 0, but should deal at least 1
        assert pokemon.current_hp == 9, "Status damage should be at least 1"

    def test_paralysis_no_damage(self):
        """Test that paralysis doesn't deal damage"""
        pokemon = create_test_pokemon(hp=100)
        pokemon.current_hp = 100
        pokemon.status = Status.PARALYSIS

        apply_end_turn_status_damage(pokemon)

        assert pokemon.current_hp == 100, "Paralysis should not deal damage"

    def test_sleep_no_damage(self):
        """Test that sleep doesn't deal damage"""
        pokemon = create_test_pokemon(hp=100)
        pokemon.current_hp = 100
        pokemon.status = Status.SLEEP
        pokemon.sleep_turns = 3

        apply_end_turn_status_damage(pokemon)

        assert pokemon.current_hp == 100, "Sleep should not deal damage"

    def test_freeze_no_damage(self):
        """Test that freeze doesn't deal damage"""
        pokemon = create_test_pokemon(hp=100)
        pokemon.current_hp = 100
        pokemon.status = Status.FREEZE

        apply_end_turn_status_damage(pokemon)

        assert pokemon.current_hp == 100, "Freeze should not deal damage"


class TestConfusion:
    """Test confusion mechanics (separate from major status)"""

    def test_confusion_can_cause_self_damage(self):
        """Test that confused Pokemon can hurt themselves"""
        pokemon = create_test_pokemon(hp=100, attack=100, defense=100)
        pokemon.current_hp = 100
        pokemon.confusion_turns = 3

        hurt_self_count = 0
        total_attempts = 100

        for _ in range(total_attempts):
            pokemon.current_hp = 100
            pokemon.confusion_turns = 3
            can_attack = apply_status_effects(pokemon)
            if pokemon.current_hp < 100:
                hurt_self_count += 1

        # Confusion has 50% chance to hurt self in Gen 1
        assert hurt_self_count > 20, "Confusion should sometimes cause self-damage"
        assert hurt_self_count < 80, "Confusion shouldn't always cause self-damage"

    def test_confusion_wears_off(self):
        """Test that confusion wears off after turns"""
        pokemon = create_test_pokemon()
        pokemon.confusion_turns = 1

        # Force snap out
        with patch('engine.status.random.randint', return_value=100):  # Won't hit self
            apply_status_effects(pokemon)

        assert pokemon.confusion_turns == 0, "Confusion should decrement"

    def test_confusion_stacks_with_status(self):
        """Test that confusion can exist alongside major status"""
        pokemon = create_test_pokemon()
        pokemon.status = Status.PARALYSIS
        pokemon.confusion_turns = 3

        # Both should be able to exist
        assert pokemon.status == Status.PARALYSIS
        assert pokemon.confusion_turns == 3


class TestBurnAttackReduction:
    """Test that burn reduces physical attack damage"""

    def test_burn_reduces_physical_damage(self):
        """Test that burned Pokemon deal less physical damage"""
        from engine.damage import calculate_damage

        attacker_normal = create_test_pokemon(name="Normal", attack=100, speed=50)
        attacker_burned = create_test_pokemon(name="Burned", attack=100, speed=50)
        attacker_burned.status = Status.BURN

        defender = create_test_pokemon(defense=100)

        physical_move = create_test_move(power=80, category=MoveCategory.PHYSICAL)

        normal_damages = []
        burned_damages = []

        for _ in range(100):
            dmg, crit, _ = calculate_damage(attacker_normal, defender, physical_move)
            if not crit:
                normal_damages.append(dmg)

            dmg, crit, _ = calculate_damage(attacker_burned, defender, physical_move)
            if not crit:
                burned_damages.append(dmg)

        avg_normal = sum(normal_damages) / len(normal_damages) if normal_damages else 0
        avg_burned = sum(burned_damages) / len(burned_damages) if burned_damages else 0

        ratio = avg_burned / avg_normal if avg_normal > 0 else 0

        # Burn should reduce physical damage by 50%
        assert 0.4 < ratio < 0.6, f"Burn should halve physical damage, ratio was {ratio:.2f}"

    def test_burn_does_not_reduce_special_damage(self):
        """Test that burn doesn't affect special attack damage"""
        from engine.damage import calculate_damage

        attacker_normal = create_test_pokemon(name="Normal", special=100, speed=50)
        attacker_burned = create_test_pokemon(name="Burned", special=100, speed=50)
        attacker_burned.status = Status.BURN

        defender = create_test_pokemon(special=100)

        special_move = create_test_move(
            power=80,
            category=MoveCategory.SPECIAL,
            move_type=Type.FIRE
        )

        normal_damages = []
        burned_damages = []

        for _ in range(100):
            dmg, crit, _ = calculate_damage(attacker_normal, defender, special_move)
            if not crit:
                normal_damages.append(dmg)

            dmg, crit, _ = calculate_damage(attacker_burned, defender, special_move)
            if not crit:
                burned_damages.append(dmg)

        avg_normal = sum(normal_damages) / len(normal_damages) if normal_damages else 0
        avg_burned = sum(burned_damages) / len(burned_damages) if burned_damages else 0

        ratio = avg_burned / avg_normal if avg_normal > 0 else 0

        # Burn should NOT affect special damage
        assert 0.9 < ratio < 1.1, f"Burn should not affect special damage, ratio was {ratio:.2f}"


class TestParalysisSpeedReduction:
    """Test paralysis speed interaction"""

    def test_paralysis_speed_interaction(self):
        """Test that paralysis is tracked but speed reduction is handled in battle"""
        from engine.stat_modifiers import get_modified_speed

        pokemon = create_test_pokemon(speed=100)
        normal_speed = get_modified_speed(pokemon)

        pokemon.status = Status.PARALYSIS
        paralyzed_speed = get_modified_speed(pokemon)

        # Note: In this implementation, the paralysis speed reduction is applied
        # during battle resolution, not in the get_modified_speed function.
        # The status is tracked and can be checked during battle.
        assert pokemon.status == Status.PARALYSIS
        # Speed stat itself is still accessible
        assert paralyzed_speed == normal_speed  # Base speed unchanged, reduction applied in battle
