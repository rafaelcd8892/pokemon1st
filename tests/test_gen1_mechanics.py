"""Tests for Gen 1-specific battle mechanics fixes."""

import pytest
from unittest.mock import patch

from models.pokemon import Pokemon
from models.stats import Stats
from models.move import Move
from models.enums import Type, Status, MoveCategory, StatType
from engine.battle import (
    execute_turn, _execute_normal_attack, _check_accuracy,
    _handle_recharge_move, apply_damage_to_target,
)
from engine.damage import calculate_damage
from engine.status import apply_status_effects, apply_confusion_damage
from engine.stat_modifiers import (
    apply_stat_stage_to_stat, get_modified_speed, STAT_STAGE_FRACTIONS,
)
from engine.move_effects import execute_special_move
from tests.conftest import create_test_pokemon, create_test_move


# =============================================================================
# Fix 1: Immunity blocks status effects
# =============================================================================

class TestImmunityBlocksEffects:
    """Immunity (0x effectiveness) should prevent status effects and stat changes."""

    def test_thunder_wave_does_not_paralyze_ground_type(self):
        """Thunder Wave (Electric) should not paralyze a Ground-type Pokemon."""
        attacker = create_test_pokemon("Pikachu", types=[Type.ELECTRIC], speed=90)
        defender = create_test_pokemon("Sandshrew", types=[Type.GROUND], speed=40)

        thunder_wave = create_test_move(
            name="Thunder-Wave", move_type=Type.ELECTRIC,
            category=MoveCategory.STATUS, power=0, accuracy=100,
            status_effect=Status.PARALYSIS, status_chance=100,
        )

        with patch('engine.damage.calculate_critical_hit', return_value=False):
            _execute_normal_attack(attacker, defender, thunder_wave)

        assert defender.status == Status.NONE

    def test_normal_move_does_not_affect_ghost(self):
        """Normal-type move should not deal damage or apply effects to Ghost."""
        attacker = create_test_pokemon("Raticate", types=[Type.NORMAL], attack=80)
        defender = create_test_pokemon("Gengar", types=[Type.GHOST, Type.POISON], hp=120)

        body_slam = create_test_move(
            name="Body-Slam", move_type=Type.NORMAL,
            category=MoveCategory.PHYSICAL, power=85, accuracy=100,
            status_effect=Status.PARALYSIS, status_chance=30,
        )

        original_hp = defender.current_hp
        with patch('engine.damage.calculate_critical_hit', return_value=False):
            _execute_normal_attack(attacker, defender, body_slam)

        assert defender.current_hp == original_hp
        assert defender.status == Status.NONE


# =============================================================================
# Fix 2: Hyper Beam skips recharge on KO
# =============================================================================

class TestHyperBeamRecharge:
    """Hyper Beam should not require recharge if it KOs the target."""

    def test_hyper_beam_recharges_when_target_survives(self):
        """Hyper Beam should set must_recharge when target survives."""
        attacker = create_test_pokemon("Tauros", types=[Type.NORMAL], attack=100, speed=110)
        defender = create_test_pokemon("Snorlax", types=[Type.NORMAL], hp=500, defense=200)

        hyper_beam = create_test_move(
            name="Hyper-Beam", move_type=Type.NORMAL,
            category=MoveCategory.SPECIAL, power=150, accuracy=100,
        )
        attacker.moves = [hyper_beam]

        with patch('engine.damage.calculate_critical_hit', return_value=False):
            _handle_recharge_move(attacker, defender, hyper_beam, "RECHARGE|Hyper-Beam", None)

        assert defender.is_alive()
        assert attacker.must_recharge is True

    def test_hyper_beam_no_recharge_on_ko(self):
        """Hyper Beam should skip recharge when it KOs the target."""
        attacker = create_test_pokemon("Tauros", types=[Type.NORMAL], attack=200, speed=110)
        defender = create_test_pokemon("Weedle", types=[Type.BUG], hp=10, defense=10)

        hyper_beam = create_test_move(
            name="Hyper-Beam", move_type=Type.NORMAL,
            category=MoveCategory.SPECIAL, power=150, accuracy=100,
        )
        attacker.moves = [hyper_beam]

        with patch('engine.damage.calculate_critical_hit', return_value=False):
            _handle_recharge_move(attacker, defender, hyper_beam, "RECHARGE|Hyper-Beam", None)

        assert not defender.is_alive()
        assert attacker.must_recharge is False


# =============================================================================
# Fix 3: Explosion halves defense in damage formula
# =============================================================================

class TestExplosionDefenseHalving:
    """Explosion/Self-Destruct should halve defense, not double damage."""

    def test_defense_modifier_halves_defense(self):
        """Defense modifier 0.5 should produce different results than doubling damage."""
        attacker = create_test_pokemon("Golem", types=[Type.ROCK], attack=110)
        defender = create_test_pokemon("Chansey", types=[Type.NORMAL], defense=50)

        explosion = create_test_move(
            name="Explosion", move_type=Type.NORMAL,
            category=MoveCategory.PHYSICAL, power=170, accuracy=100,
        )

        # Calculate with defense_modifier=0.5
        with patch('engine.damage.calculate_critical_hit', return_value=False), \
             patch('engine.damage.get_random_factor', return_value=1.0):
            damage_halved_def, _, _ = calculate_damage(
                attacker, defender, explosion, defense_modifier=0.5
            )

        # Calculate normally and double
        with patch('engine.damage.calculate_critical_hit', return_value=False), \
             patch('engine.damage.get_random_factor', return_value=1.0):
            damage_normal, _, _ = calculate_damage(attacker, defender, explosion)
            damage_doubled = damage_normal * 2

        # They should be different due to integer math order of operations
        # Halving defense in the formula gives higher damage than doubling after
        assert damage_halved_def != damage_doubled


# =============================================================================
# Fix 4: Confusion damage uses stat stages
# =============================================================================

class TestConfusionStatStages:
    """Confusion self-damage should apply stat stage modifiers."""

    def test_confusion_damage_increases_with_attack_boost(self):
        """Higher attack stage should increase confusion damage."""
        pokemon = create_test_pokemon("Primeape", attack=105, defense=60)

        base_damage = apply_confusion_damage(pokemon)

        # Boost attack +2 (doubles attack)
        pokemon.modify_stat_stage(StatType.ATTACK, 2)
        boosted_damage = apply_confusion_damage(pokemon)

        assert boosted_damage > base_damage

    def test_confusion_damage_decreases_with_defense_boost(self):
        """Higher defense stage should decrease confusion damage."""
        pokemon = create_test_pokemon("Primeape", attack=105, defense=60)

        base_damage = apply_confusion_damage(pokemon)

        # Boost defense +2 (doubles defense)
        pokemon.modify_stat_stage(StatType.DEFENSE, 2)
        boosted_damage = apply_confusion_damage(pokemon)

        assert boosted_damage < base_damage


# =============================================================================
# Fix 5: Trapping moves prevent defender from acting
# =============================================================================

class TestTrappingPreventsAction:
    """Trapped Pokemon (Wrap, Bind, etc.) should not be able to act."""

    def test_trapped_pokemon_cannot_attack(self):
        """A trapped Pokemon should skip its turn."""
        attacker = create_test_pokemon("Rattata", types=[Type.NORMAL], attack=50)
        defender = create_test_pokemon("Pidgey", types=[Type.NORMAL], hp=100)

        tackle = create_test_move(
            name="Tackle", move_type=Type.NORMAL,
            category=MoveCategory.PHYSICAL, power=40, accuracy=100,
        )
        attacker.moves = [tackle]
        attacker.is_trapped = True
        attacker.trap_turns = 3

        original_hp = defender.current_hp
        execute_turn(attacker, defender, tackle)

        # Defender should not have taken any damage
        assert defender.current_hp == original_hp


# =============================================================================
# Fix 7: Paralysis quarters Speed
# =============================================================================

class TestParalysisSpeed:
    """Paralysis should quarter the Speed stat for turn order."""

    def test_paralysis_quarters_speed(self):
        """Paralyzed Pokemon should have 1/4 speed."""
        pokemon = create_test_pokemon("Jolteon", speed=130)

        normal_speed = get_modified_speed(pokemon)
        pokemon.status = Status.PARALYSIS
        para_speed = get_modified_speed(pokemon)

        assert para_speed == normal_speed // 4

    def test_paralyzed_speed_minimum_1(self):
        """Paralyzed Pokemon speed should never be 0."""
        pokemon = create_test_pokemon("Slowpoke", speed=3)
        pokemon.status = Status.PARALYSIS

        speed = get_modified_speed(pokemon)
        assert speed >= 1


# =============================================================================
# Fix 8: Counter only works against Normal/Fighting
# =============================================================================

class TestCounterTypeRestriction:
    """Counter should only work against Normal and Fighting type moves."""

    def test_counter_works_against_normal(self):
        """Counter should return 2x damage from Normal-type moves."""
        attacker = create_test_pokemon("Chansey", types=[Type.NORMAL])
        defender = create_test_pokemon("Tauros", types=[Type.NORMAL])

        counter = create_test_move(
            name="Counter", move_type=Type.FIGHTING,
            category=MoveCategory.PHYSICAL, power=0, accuracy=100,
        )

        attacker.last_damage_taken = 50
        attacker.last_damage_physical = True
        attacker.last_damage_move_type = Type.NORMAL

        damage, message = execute_special_move(attacker, defender, counter)
        assert damage == 100  # 2x of 50

    def test_counter_works_against_fighting(self):
        """Counter should return 2x damage from Fighting-type moves."""
        attacker = create_test_pokemon("Chansey", types=[Type.NORMAL])
        defender = create_test_pokemon("Machamp", types=[Type.FIGHTING])

        counter = create_test_move(
            name="Counter", move_type=Type.FIGHTING,
            category=MoveCategory.PHYSICAL, power=0, accuracy=100,
        )

        attacker.last_damage_taken = 80
        attacker.last_damage_physical = True
        attacker.last_damage_move_type = Type.FIGHTING

        damage, message = execute_special_move(attacker, defender, counter)
        assert damage == 160  # 2x of 80

    def test_counter_fails_against_other_types(self):
        """Counter should fail against non-Normal/Fighting type moves."""
        attacker = create_test_pokemon("Chansey", types=[Type.NORMAL])
        defender = create_test_pokemon("Alakazam", types=[Type.PSYCHIC])

        counter = create_test_move(
            name="Counter", move_type=Type.FIGHTING,
            category=MoveCategory.PHYSICAL, power=0, accuracy=100,
        )

        attacker.last_damage_taken = 50
        attacker.last_damage_physical = True
        attacker.last_damage_move_type = Type.PSYCHIC

        damage, message = execute_special_move(attacker, defender, counter)
        assert damage == 0
        assert "falló" in message


# =============================================================================
# Fix 9: Substitute HP is exact 25%
# =============================================================================

class TestSubstituteHP:
    """Substitute HP should be exactly 25% of max HP (no +1)."""

    def test_substitute_hp_is_25_percent(self):
        """Substitute HP should equal floor(max_hp / 4)."""
        pokemon = create_test_pokemon("Alakazam", hp=200)
        opponent = create_test_pokemon("Rival", hp=100)

        substitute = create_test_move(
            name="Substitute", move_type=Type.NORMAL,
            category=MoveCategory.STATUS, power=0, accuracy=100,
        )

        execute_special_move(pokemon, opponent, substitute)

        expected_hp = pokemon.max_hp // 4  # 50, not 51
        assert pokemon.substitute_hp == expected_hp


# =============================================================================
# Fix 10: Stat stage integer math
# =============================================================================

class TestStatStageIntegerMath:
    """Stat stage multipliers should use integer division for accuracy."""

    def test_stage_minus1_uses_integer_division(self):
        """Stage -1 should use 2/3 with integer division, not float 0.66."""
        # With float 0.66: 100 * 0.66 = 66.0 -> int(66.0) = 66
        # With integer 100 * 2 // 3 = 200 // 3 = 66
        # Same result for 100, but test with a value where they differ
        result = apply_stat_stage_to_stat(101, -1)
        # 101 * 2 // 3 = 202 // 3 = 67
        # float: int(101 * 0.66) = int(66.66) = 66
        assert result == 67  # Integer math gives 67, not 66

    def test_stage_minus5_uses_integer_division(self):
        """Stage -5 should use 2/7 with integer division."""
        result = apply_stat_stage_to_stat(100, -5)
        # 100 * 2 // 7 = 200 // 7 = 28
        # float: int(100 * 0.286) = int(28.6) = 28
        assert result == 28

    def test_all_fractions_are_defined(self):
        """All 13 stat stages should have fraction entries."""
        for stage in range(-6, 7):
            assert stage in STAT_STAGE_FRACTIONS
            num, den = STAT_STAGE_FRACTIONS[stage]
            assert den > 0


# =============================================================================
# Fix 11: Freeze requires Fire move to thaw
# =============================================================================

class TestFreezeThawMechanic:
    """Frozen Pokemon should only thaw from Fire-type moves, not randomly."""

    def test_frozen_pokemon_stays_frozen(self):
        """Frozen Pokemon should remain frozen on their turn (no random thaw)."""
        pokemon = create_test_pokemon("Lapras", types=[Type.WATER, Type.ICE])
        pokemon.status = Status.FREEZE

        # Call apply_status_effects many times - should never thaw
        for _ in range(50):
            can_attack = apply_status_effects(pokemon)
            assert can_attack is False
            assert pokemon.status == Status.FREEZE

    def test_fire_move_thaws_frozen_target(self):
        """Fire-type move hitting a frozen target should thaw it."""
        attacker = create_test_pokemon("Charizard", types=[Type.FIRE], attack=100)
        defender = create_test_pokemon("Lapras", types=[Type.WATER, Type.ICE], hp=300, defense=80)
        defender.status = Status.FREEZE

        flamethrower = create_test_move(
            name="Flamethrower", move_type=Type.FIRE,
            category=MoveCategory.SPECIAL, power=95, accuracy=100,
        )

        with patch('engine.damage.calculate_critical_hit', return_value=False):
            _execute_normal_attack(attacker, defender, flamethrower)

        assert defender.status == Status.NONE


# =============================================================================
# Fix 12: Sleep wake-up turn is lost
# =============================================================================

class TestSleepWakeUp:
    """Pokemon should not be able to attack on the turn they wake from sleep."""

    def test_pokemon_cannot_attack_on_wake_up_turn(self):
        """When sleep counter reaches 0, the Pokemon wakes but cannot act."""
        pokemon = create_test_pokemon("Snorlax")
        pokemon.status = Status.SLEEP
        pokemon.sleep_counter = 1  # Will reach 0 this turn

        can_attack = apply_status_effects(pokemon)

        assert pokemon.status == Status.NONE  # Woke up
        assert can_attack is False  # But cannot act this turn

    def test_pokemon_still_sleeps_with_counter_above_zero(self):
        """Pokemon with sleep counter > 1 should remain asleep."""
        pokemon = create_test_pokemon("Snorlax")
        pokemon.status = Status.SLEEP
        pokemon.sleep_counter = 3

        can_attack = apply_status_effects(pokemon)

        assert pokemon.status == Status.SLEEP
        assert can_attack is False
        assert pokemon.sleep_counter == 2


# =============================================================================
# Fix 13: Always-hit moves (accuracy=0)
# =============================================================================

class TestAlwaysHitMoves:
    """Moves with accuracy=0 should always hit."""

    def test_accuracy_zero_always_hits(self):
        """A move with accuracy 0 should never miss."""
        attacker = create_test_pokemon("Eevee")
        defender = create_test_pokemon("Pidgey")

        swift = create_test_move(
            name="Swift", move_type=Type.NORMAL,
            category=MoveCategory.SPECIAL, power=60, accuracy=0,
        )

        # Should always return True (hit)
        for _ in range(100):
            assert _check_accuracy(attacker, defender, swift) is True
