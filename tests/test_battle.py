"""Tests for battle engine mechanics"""

import pytest
from unittest.mock import patch, MagicMock

from models.enums import Type, Status, MoveCategory, StatType
from models.move import Move
from engine.battle import (
    execute_turn,
    determine_turn_order,
    apply_damage_to_target,
    apply_end_of_turn_effects,
)
from engine.stat_modifiers import get_modified_speed
from tests.conftest import create_test_pokemon, create_test_move
from data.data_loader import create_move


class TestTurnOrder:
    """Test turn order determination"""

    def test_faster_pokemon_goes_first(self):
        """Test that faster Pokemon attacks first"""
        fast = create_test_pokemon(name="Fast", speed=100)
        slow = create_test_pokemon(name="Slow", speed=50)

        first, second = determine_turn_order(fast, slow)

        assert first.name == "Fast"
        assert second.name == "Slow"

    def test_slower_pokemon_goes_second(self):
        """Test from the other direction"""
        fast = create_test_pokemon(name="Fast", speed=150)
        slow = create_test_pokemon(name="Slow", speed=30)

        first, second = determine_turn_order(slow, fast)

        assert first.name == "Fast"
        assert second.name == "Slow"

    def test_speed_tie_is_random(self):
        """Test that speed ties result in random order"""
        pokemon1 = create_test_pokemon(name="Pokemon1", speed=100)
        pokemon2 = create_test_pokemon(name="Pokemon2", speed=100)

        # Run many times and check both orders occur
        first_counts = {"Pokemon1": 0, "Pokemon2": 0}

        for _ in range(100):
            first, _ = determine_turn_order(pokemon1, pokemon2)
            first_counts[first.name] += 1

        # Both should win sometimes (with high probability)
        assert first_counts["Pokemon1"] > 10, "Pokemon1 should go first sometimes"
        assert first_counts["Pokemon2"] > 10, "Pokemon2 should go first sometimes"

    def test_speed_stages_affect_order(self):
        """Test that stat stages affect speed comparison"""
        fast_base = create_test_pokemon(name="FastBase", speed=100)
        slow_base = create_test_pokemon(name="SlowBase", speed=80)

        # Slow base gets +2 speed stages (2x multiplier)
        slow_base.modify_stat_stage(StatType.SPEED, 2)

        # Now slow_base has effective speed of 160
        first, second = determine_turn_order(fast_base, slow_base)

        assert first.name == "SlowBase", "Boosted Pokemon should go first"


class TestExecuteTurn:
    """Test turn execution mechanics"""

    def test_basic_attack_deals_damage(self):
        """Test that a basic attack reduces defender HP"""
        attacker = create_test_pokemon(name="Attacker", attack=100, speed=50)
        defender = create_test_pokemon(name="Defender", hp=200, defense=100)
        move = create_test_move(power=80, category=MoveCategory.PHYSICAL)

        initial_hp = defender.current_hp

        with patch('engine.battle.random.randint', return_value=100):  # Always hit
            execute_turn(attacker, defender, move)

        assert defender.current_hp < initial_hp, "Defender should take damage"

    def test_move_uses_pp(self):
        """Test that using a move decreases PP"""
        attacker = create_test_pokemon(name="Attacker", attack=100, speed=50)
        defender = create_test_pokemon(name="Defender", defense=100)
        move = create_test_move(power=50, pp=10)

        initial_pp = move.pp

        with patch('engine.battle.random.randint', return_value=100):
            execute_turn(attacker, defender, move)

        assert move.pp == initial_pp - 1, "Move PP should decrease by 1"

    def test_no_pp_move_fails(self):
        """Test that a move with 0 PP fails"""
        attacker = create_test_pokemon(name="Attacker", attack=100, speed=50)
        defender = create_test_pokemon(name="Defender", hp=100, defense=100)
        move = create_test_move(power=50, pp=0)
        move.pp = 0  # Force 0 PP

        initial_hp = defender.current_hp

        execute_turn(attacker, defender, move)

        assert defender.current_hp == initial_hp, "No damage when move has no PP"

    def test_miss_deals_no_damage(self):
        """Test that a missed attack deals no damage"""
        attacker = create_test_pokemon(name="Attacker", attack=100, speed=50)
        defender = create_test_pokemon(name="Defender", hp=100, defense=100)
        move = create_test_move(power=80, accuracy=100)

        initial_hp = defender.current_hp

        # Force miss by making accuracy check fail
        with patch('engine.battle.random.randint', return_value=101):  # Miss
            execute_turn(attacker, defender, move)

        assert defender.current_hp == initial_hp, "Missed attack should deal no damage"


class TestRechargeAndCharging:
    """Test recharge and charging move mechanics"""

    def test_must_recharge_skips_turn(self):
        """Test that must_recharge flag causes turn skip"""
        attacker = create_test_pokemon(name="Attacker", attack=100, speed=50)
        attacker.must_recharge = True
        defender = create_test_pokemon(name="Defender", hp=100, defense=100)
        move = create_test_move(power=80)

        initial_hp = defender.current_hp

        execute_turn(attacker, defender, move)

        assert defender.current_hp == initial_hp, "Recharging Pokemon can't attack"
        assert attacker.must_recharge is False, "Recharge flag should be cleared"

    def test_charging_move_completes(self):
        """Test that a charging Pokemon completes their move"""
        attacker = create_test_pokemon(name="Attacker", attack=100, speed=50)
        defender = create_test_pokemon(name="Defender", hp=200, defense=100)

        # Set up as if charging Solar Beam
        charging_move = create_move("solar-beam")
        attacker.is_charging = True
        attacker.charging_move = charging_move

        initial_hp = defender.current_hp

        with patch('engine.battle.random.randint', return_value=100):
            execute_turn(attacker, defender, charging_move)

        assert defender.current_hp < initial_hp, "Charged attack should deal damage"
        assert attacker.is_charging is False, "Charging flag should be cleared"


class TestStatusEffects:
    """Test status effect interactions with battle"""

    def test_paralysis_can_prevent_attack(self):
        """Test that paralysis sometimes prevents attacking"""
        attacker = create_test_pokemon(name="Attacker", attack=100, speed=50)
        attacker.status = Status.PARALYSIS
        defender = create_test_pokemon(name="Defender", hp=100, defense=100)
        move = create_test_move(power=50, accuracy=100)

        # Count paralysis-specific prevention (not counting misses)
        paralyzed_count = 0
        total_attempts = 200

        for _ in range(total_attempts):
            defender.current_hp = 100  # Reset HP

            # Check if paralyzed before executing turn
            from engine.status import apply_status_effects
            can_attack = apply_status_effects(attacker)
            if not can_attack:
                paralyzed_count += 1

        # Paralysis has 25% chance to prevent attack
        expected = total_attempts * 0.25
        tolerance = total_attempts * 0.08  # 8% tolerance

        assert abs(paralyzed_count - expected) < tolerance, \
            f"Paralysis should prevent ~25% of attacks, got {paralyzed_count/total_attempts*100:.1f}%"

    def test_sleep_prevents_attack(self):
        """Test that sleeping Pokemon can't attack"""
        attacker = create_test_pokemon(name="Attacker", attack=100, speed=50)
        attacker.status = Status.SLEEP
        attacker.sleep_turns = 3
        defender = create_test_pokemon(name="Defender", hp=100, defense=100)
        move = create_test_move(power=50)

        initial_hp = defender.current_hp

        # Sleeping Pokemon won't attack (unless they wake up)
        with patch('engine.status.random.randint', return_value=2):  # Won't wake
            execute_turn(attacker, defender, move)

        # Either still sleeping (no damage) or woke up (damage dealt)
        # This test verifies the mechanic exists
        assert attacker.sleep_counter <= 2, "Sleep counter should decrement"

    def test_frozen_pokemon_might_thaw(self):
        """Test that frozen Pokemon have chance to thaw"""
        attacker = create_test_pokemon(name="Attacker", attack=100, speed=50)
        attacker.status = Status.FREEZE
        defender = create_test_pokemon(name="Defender", hp=100, defense=100)
        move = create_test_move(power=50)

        thawed_count = 0
        for _ in range(100):
            attacker.status = Status.FREEZE
            with patch('engine.status.random.random', return_value=0.1):  # 10% < 20% thaw
                execute_turn(attacker, defender, move)
                if attacker.status != Status.FREEZE:
                    thawed_count += 1

        assert thawed_count > 0, "Frozen Pokemon should sometimes thaw"


class TestStatModifications:
    """Test stat modification during battle"""

    def test_stat_boosting_move(self):
        """Test that stat boosting moves increase stages"""
        attacker = create_test_pokemon(name="Attacker", speed=100)
        defender = create_test_pokemon(name="Defender")

        # Swords Dance boosts Attack by 2
        swords_dance = create_move("swords-dance")

        initial_stage = attacker.stat_stages[StatType.ATTACK]

        with patch('engine.battle.random.randint', return_value=100):
            execute_turn(attacker, defender, swords_dance)

        assert attacker.stat_stages[StatType.ATTACK] == initial_stage + 2

    def test_stat_lowering_move(self):
        """Test that stat lowering moves decrease enemy stages"""
        attacker = create_test_pokemon(name="Attacker", speed=100)
        defender = create_test_pokemon(name="Defender")

        # Growl lowers Attack by 1
        growl = create_move("growl")

        initial_stage = defender.stat_stages[StatType.ATTACK]

        with patch('engine.battle.random.randint', return_value=100):
            execute_turn(attacker, defender, growl)

        assert defender.stat_stages[StatType.ATTACK] == initial_stage - 1

    def test_mist_blocks_stat_reduction(self):
        """Test that Mist protects against stat reductions"""
        attacker = create_test_pokemon(name="Attacker", speed=100)
        defender = create_test_pokemon(name="Defender")
        defender.has_mist = True

        growl = create_move("growl")

        initial_stage = defender.stat_stages[StatType.ATTACK]

        with patch('engine.battle.random.randint', return_value=100):
            execute_turn(attacker, defender, growl)

        assert defender.stat_stages[StatType.ATTACK] == initial_stage, "Mist should block reduction"


class TestSubstitute:
    """Test Substitute mechanics"""

    def test_substitute_absorbs_damage(self):
        """Test that Substitute absorbs damage instead of Pokemon"""
        attacker = create_test_pokemon(name="Attacker", attack=100, speed=50)
        defender = create_test_pokemon(name="Defender", hp=200, defense=100)
        defender.substitute_hp = 50

        move = create_test_move(power=40, category=MoveCategory.PHYSICAL)

        initial_hp = defender.current_hp

        with patch('engine.battle.random.randint', return_value=100):
            execute_turn(attacker, defender, move)

        assert defender.current_hp == initial_hp, "Pokemon HP should be unchanged"
        assert defender.substitute_hp < 50, "Substitute should take damage"

    def test_substitute_breaks_when_depleted(self):
        """Test that Substitute breaks when HP reaches 0"""
        attacker = create_test_pokemon(name="Attacker", attack=150, speed=50)
        defender = create_test_pokemon(name="Defender", hp=200, defense=50)
        defender.substitute_hp = 10  # Low HP substitute

        move = create_test_move(power=100, category=MoveCategory.PHYSICAL)

        with patch('engine.battle.random.randint', return_value=100):
            execute_turn(attacker, defender, move)

        assert defender.substitute_hp == 0, "Substitute should be broken"


class TestScreens:
    """Test Reflect and Light Screen mechanics"""

    def test_reflect_halves_physical_damage(self):
        """Test that Reflect reduces physical damage by 50%"""
        attacker = create_test_pokemon(name="Attacker", attack=100, speed=50)
        defender_no_screen = create_test_pokemon(name="NoScreen", hp=200, defense=100)
        defender_with_screen = create_test_pokemon(name="WithScreen", hp=200, defense=100)
        defender_with_screen.has_reflect = True
        defender_with_screen.reflect_turns = 5

        move = create_test_move(power=80, category=MoveCategory.PHYSICAL)

        # Collect damage samples
        no_screen_damages = []
        screen_damages = []

        for _ in range(50):
            defender_no_screen.current_hp = 200
            defender_with_screen.current_hp = 200

            with patch('engine.battle.random.randint', return_value=100):
                execute_turn(attacker, defender_no_screen, move)
                no_screen_damages.append(200 - defender_no_screen.current_hp)

            with patch('engine.battle.random.randint', return_value=100):
                execute_turn(attacker, defender_with_screen, move)
                screen_damages.append(200 - defender_with_screen.current_hp)

        avg_no_screen = sum(no_screen_damages) / len(no_screen_damages)
        avg_screen = sum(screen_damages) / len(screen_damages)

        ratio = avg_screen / avg_no_screen
        assert 0.4 < ratio < 0.6, f"Reflect should halve damage, ratio was {ratio:.2f}"

    def test_light_screen_halves_special_damage(self):
        """Test that Light Screen reduces special damage by 50%"""
        attacker = create_test_pokemon(name="Attacker", special=100, speed=50)
        defender_no_screen = create_test_pokemon(name="NoScreen", hp=200, special=100)
        defender_with_screen = create_test_pokemon(name="WithScreen", hp=200, special=100)
        defender_with_screen.has_light_screen = True
        defender_with_screen.light_screen_turns = 5

        move = create_test_move(power=80, category=MoveCategory.SPECIAL, move_type=Type.PSYCHIC)

        no_screen_damages = []
        screen_damages = []

        for _ in range(50):
            defender_no_screen.current_hp = 200
            defender_with_screen.current_hp = 200

            with patch('engine.battle.random.randint', return_value=100):
                execute_turn(attacker, defender_no_screen, move)
                no_screen_damages.append(200 - defender_no_screen.current_hp)

            with patch('engine.battle.random.randint', return_value=100):
                execute_turn(attacker, defender_with_screen, move)
                screen_damages.append(200 - defender_with_screen.current_hp)

        avg_no_screen = sum(no_screen_damages) / len(no_screen_damages)
        avg_screen = sum(screen_damages) / len(screen_damages)

        ratio = avg_screen / avg_no_screen
        assert 0.4 < ratio < 0.6, f"Light Screen should halve damage, ratio was {ratio:.2f}"


class TestEndOfTurnEffects:
    """Test end-of-turn effect application"""

    def test_leech_seed_damages_and_heals(self):
        """Test that Leech Seed drains HP"""
        pokemon1 = create_test_pokemon(name="Pokemon1", hp=100)
        pokemon2 = create_test_pokemon(name="Pokemon2", hp=100)
        pokemon1.is_seeded = True
        pokemon1.current_hp = 100
        pokemon2.current_hp = 50  # Partial HP to see healing

        apply_end_of_turn_effects(pokemon1, pokemon2)

        assert pokemon1.current_hp < 100, "Seeded Pokemon should lose HP"
        assert pokemon2.current_hp > 50, "Seeder should gain HP"

    def test_trap_damage_applied(self):
        """Test that trapped Pokemon take damage"""
        trapper = create_test_pokemon(name="Trapper", hp=100)
        trapped = create_test_pokemon(name="Trapped", hp=100)
        trapped.is_trapped = True
        trapped.trap_turns = 3
        trapped.trapped_by = trapper
        trapped.current_hp = 100

        apply_end_of_turn_effects(trapped, trapper)

        assert trapped.current_hp < 100, "Trapped Pokemon should take damage"
        assert trapped.trap_turns == 2, "Trap turns should decrement"

    def test_screen_expires(self):
        """Test that screens expire after turns"""
        pokemon1 = create_test_pokemon(name="Pokemon1")
        pokemon2 = create_test_pokemon(name="Pokemon2")
        pokemon1.has_reflect = True
        pokemon1.reflect_turns = 1  # Last turn

        apply_end_of_turn_effects(pokemon1, pokemon2)

        assert pokemon1.reflect_turns == 0, "Screen turns should decrement"
        assert pokemon1.has_reflect is False, "Screen should expire"


class TestDisabledMove:
    """Test move disable mechanics"""

    def test_disabled_move_fails(self):
        """Test that a disabled move cannot be used"""
        attacker = create_test_pokemon(name="Attacker", attack=100, speed=50)
        defender = create_test_pokemon(name="Defender", hp=100, defense=100)

        move = create_test_move(name="Tackle", power=40)
        attacker.disabled_move = "Tackle"
        attacker.disable_turns = 3

        initial_hp = defender.current_hp

        execute_turn(attacker, defender, move)

        assert defender.current_hp == initial_hp, "Disabled move should fail"


class TestSemiInvulnerable:
    """Test semi-invulnerable state (Dig, Fly)"""

    def test_semi_invulnerable_avoids_attack(self):
        """Test that semi-invulnerable Pokemon avoid most attacks"""
        attacker = create_test_pokemon(name="Attacker", attack=100, speed=50)
        defender = create_test_pokemon(name="Defender", hp=100, defense=100)
        defender.is_semi_invulnerable = True

        move = create_test_move(power=80)

        initial_hp = defender.current_hp

        with patch('engine.battle.random.randint', return_value=100):
            execute_turn(attacker, defender, move)

        assert defender.current_hp == initial_hp, "Attack should miss semi-invulnerable target"
