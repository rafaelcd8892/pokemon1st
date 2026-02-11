"""Tests for Gen 1 damage calculation"""

import random
import pytest
from unittest.mock import patch

from models.enums import Type, MoveCategory
from engine.battle import execute_turn
from engine.damage import calculate_damage
import engine.damage as damage_module
from tests.conftest import create_test_pokemon, create_test_move


class TestDamageFormula:
    """Test the Gen 1 damage formula implementation"""

    def test_basic_damage_calculation(self):
        """Test that damage is calculated within expected range"""
        attacker = create_test_pokemon(
            name="Attacker",
            attack=100,
            speed=100,
        )
        defender = create_test_pokemon(
            name="Defender",
            defense=100,
        )
        move = create_test_move(power=50, category=MoveCategory.PHYSICAL)

        # Run multiple times to account for randomness
        damages = []
        for _ in range(100):
            damage, is_crit, effectiveness = calculate_damage(attacker, defender, move)
            damages.append(damage)

        # Damage should be in a reasonable range
        assert min(damages) > 0, "Damage should always be positive"
        assert max(damages) < 100, "Damage shouldn't exceed reasonable bounds for these stats"

    def test_higher_attack_more_damage(self):
        """Test that higher attack stat results in more damage"""
        defender = create_test_pokemon(defense=100)
        move = create_test_move(power=80, category=MoveCategory.PHYSICAL)

        weak_attacker = create_test_pokemon(attack=50, speed=50)
        strong_attacker = create_test_pokemon(attack=150, speed=50)

        # Average over multiple runs
        weak_damages = [calculate_damage(weak_attacker, defender, move)[0] for _ in range(50)]
        strong_damages = [calculate_damage(strong_attacker, defender, move)[0] for _ in range(50)]

        avg_weak = sum(weak_damages) / len(weak_damages)
        avg_strong = sum(strong_damages) / len(strong_damages)

        assert avg_strong > avg_weak, "Higher attack should deal more damage"

    def test_higher_defense_less_damage(self):
        """Test that higher defense stat results in less damage taken"""
        attacker = create_test_pokemon(attack=100, speed=50)
        move = create_test_move(power=80, category=MoveCategory.PHYSICAL)

        weak_defender = create_test_pokemon(defense=50)
        strong_defender = create_test_pokemon(defense=150)

        weak_damages = [calculate_damage(attacker, weak_defender, move)[0] for _ in range(50)]
        strong_damages = [calculate_damage(attacker, strong_defender, move)[0] for _ in range(50)]

        avg_vs_weak = sum(weak_damages) / len(weak_damages)
        avg_vs_strong = sum(strong_damages) / len(strong_damages)

        assert avg_vs_weak > avg_vs_strong, "Higher defense should reduce damage taken"

    def test_special_move_uses_special_stat(self):
        """Test that special moves use Special stat instead of Attack/Defense"""
        # High Attack, low Special attacker
        physical_attacker = create_test_pokemon(attack=150, special=50, speed=50)
        # High Special, low Attack attacker
        special_attacker = create_test_pokemon(attack=50, special=150, speed=50)

        defender = create_test_pokemon(defense=100, special=100)

        physical_move = create_test_move(power=80, category=MoveCategory.PHYSICAL)
        special_move = create_test_move(power=80, category=MoveCategory.SPECIAL, move_type=Type.FIRE)

        # Physical attacker should do more with physical move
        phys_with_phys = [calculate_damage(physical_attacker, defender, physical_move)[0] for _ in range(30)]
        spec_with_phys = [calculate_damage(special_attacker, defender, physical_move)[0] for _ in range(30)]

        # Special attacker should do more with special move
        phys_with_spec = [calculate_damage(physical_attacker, defender, special_move)[0] for _ in range(30)]
        spec_with_spec = [calculate_damage(special_attacker, defender, special_move)[0] for _ in range(30)]

        assert sum(phys_with_phys) > sum(spec_with_phys), "Physical attacker better with physical move"
        assert sum(spec_with_spec) > sum(phys_with_spec), "Special attacker better with special move"


class TestCriticalHits:
    """Test critical hit mechanics"""

    def test_critical_hit_doubles_damage(self):
        """Test that critical hits approximately double damage"""
        attacker = create_test_pokemon(attack=100, speed=100)
        defender = create_test_pokemon(defense=100)
        move = create_test_move(power=80, category=MoveCategory.PHYSICAL)

        # Collect crit and non-crit damages
        crit_damages = []
        normal_damages = []

        for _ in range(200):
            damage, is_crit, _ = calculate_damage(attacker, defender, move)
            if is_crit:
                crit_damages.append(damage)
            else:
                normal_damages.append(damage)

        if crit_damages and normal_damages:
            avg_crit = sum(crit_damages) / len(crit_damages)
            avg_normal = sum(normal_damages) / len(normal_damages)

            # Crit should be roughly 2x (with some variance)
            ratio = avg_crit / avg_normal
            assert 1.5 < ratio < 2.5, f"Crit ratio should be ~2x, got {ratio:.2f}"

    def test_critical_ignores_reflect(self, monkeypatch):
        """Test that critical hits ignore Reflect in Gen 1"""
        monkeypatch.setattr(damage_module, "calculate_critical_hit", lambda attacker: True)
        monkeypatch.setattr(damage_module, "get_random_factor", lambda: 1.0)

        move = create_test_move(power=100, category=MoveCategory.PHYSICAL, accuracy=100)

        attacker_reflect = create_test_pokemon(attack=120, speed=10)
        defender_reflect = create_test_pokemon(defense=100)
        defender_reflect.has_reflect = True
        execute_turn(attacker_reflect, defender_reflect, move)
        damage_with_reflect = defender_reflect.max_hp - defender_reflect.current_hp

        attacker_no_reflect = create_test_pokemon(attack=120, speed=10)
        defender_no_reflect = create_test_pokemon(defense=100)
        move_no_reflect = create_test_move(power=100, category=MoveCategory.PHYSICAL, accuracy=100)
        execute_turn(attacker_no_reflect, defender_no_reflect, move_no_reflect)
        damage_without_reflect = defender_no_reflect.max_hp - defender_no_reflect.current_hp

        assert damage_with_reflect == damage_without_reflect, "Critical hits should ignore Reflect"

    def test_critical_ignores_light_screen(self, monkeypatch):
        """Test that critical hits ignore Light Screen in Gen 1"""
        monkeypatch.setattr(damage_module, "calculate_critical_hit", lambda attacker: True)
        monkeypatch.setattr(damage_module, "get_random_factor", lambda: 1.0)

        move = create_test_move(power=100, category=MoveCategory.SPECIAL, accuracy=100)

        attacker_screen = create_test_pokemon(special=120, speed=10)
        defender_screen = create_test_pokemon(special=100)
        defender_screen.has_light_screen = True
        execute_turn(attacker_screen, defender_screen, move)
        damage_with_screen = defender_screen.max_hp - defender_screen.current_hp

        attacker_no_screen = create_test_pokemon(special=120, speed=10)
        defender_no_screen = create_test_pokemon(special=100)
        move_no_screen = create_test_move(power=100, category=MoveCategory.SPECIAL, accuracy=100)
        execute_turn(attacker_no_screen, defender_no_screen, move_no_screen)
        damage_without_screen = defender_no_screen.max_hp - defender_no_screen.current_hp

        assert damage_with_screen == damage_without_screen, "Critical hits should ignore Light Screen"

    def test_higher_speed_more_crits(self):
        """Test that higher speed increases critical hit rate"""
        defender = create_test_pokemon(defense=100)
        move = create_test_move(power=50, category=MoveCategory.PHYSICAL)

        slow_attacker = create_test_pokemon(speed=30, attack=100)
        fast_attacker = create_test_pokemon(speed=200, attack=100)

        slow_crits = sum(1 for _ in range(500) if calculate_damage(slow_attacker, defender, move)[1])
        fast_crits = sum(1 for _ in range(500) if calculate_damage(fast_attacker, defender, move)[1])

        # Fast Pokemon should have noticeably more crits
        assert fast_crits > slow_crits, "Faster Pokemon should crit more often"


class TestTypeEffectiveness:
    """Test type effectiveness calculations"""

    def test_super_effective_doubles_damage(self):
        """Test that super effective moves deal 2x damage"""
        attacker = create_test_pokemon(types=[Type.ELECTRIC], attack=100, special=100, speed=50)
        water_defender = create_test_pokemon(types=[Type.WATER], defense=100, special=100)
        normal_defender = create_test_pokemon(types=[Type.NORMAL], defense=100, special=100)

        electric_move = create_test_move(
            name="Thunderbolt",
            move_type=Type.ELECTRIC,
            power=95,
            category=MoveCategory.SPECIAL
        )

        # Compare damage vs Water (2x) and Normal (1x) with crit/random noise removed.
        with patch.object(damage_module, "calculate_critical_hit", return_value=False), \
             patch.object(damage_module, "get_random_factor", return_value=1.0):
            vs_water = [calculate_damage(attacker, water_defender, electric_move)[0] for _ in range(50)]
            vs_normal = [calculate_damage(attacker, normal_defender, electric_move)[0] for _ in range(50)]

        avg_vs_water = sum(vs_water) / len(vs_water)
        avg_vs_normal = sum(vs_normal) / len(vs_normal)

        ratio = avg_vs_water / avg_vs_normal
        assert 1.8 < ratio < 2.2, f"Super effective should be ~2x, got {ratio:.2f}"

    def test_not_very_effective_halves_damage(self):
        """Test that not very effective moves deal 0.5x damage"""
        attacker = create_test_pokemon(types=[Type.FIRE], attack=100, special=100, speed=50)
        water_defender = create_test_pokemon(types=[Type.WATER], defense=100, special=100)
        grass_defender = create_test_pokemon(types=[Type.GRASS], defense=100, special=100)

        fire_move = create_test_move(
            name="Flamethrower",
            move_type=Type.FIRE,
            power=95,
            category=MoveCategory.SPECIAL
        )

        # Compare damage vs Water (0.5x) and Grass (2x) with crit/random noise removed.
        with patch.object(damage_module, "calculate_critical_hit", return_value=False), \
             patch.object(damage_module, "get_random_factor", return_value=1.0):
            vs_water = [calculate_damage(attacker, water_defender, fire_move)[0] for _ in range(50)]
            vs_grass = [calculate_damage(attacker, grass_defender, fire_move)[0] for _ in range(50)]

        avg_vs_water = sum(vs_water) / len(vs_water)
        avg_vs_grass = sum(vs_grass) / len(vs_grass)

        ratio = avg_vs_grass / avg_vs_water
        assert 3.5 < ratio < 4.5, f"2x vs 0.5x should be ~4x difference, got {ratio:.2f}"

    def test_immunity_deals_zero_damage(self):
        """Test that immune types take no damage"""
        attacker = create_test_pokemon(types=[Type.NORMAL], attack=100, speed=50)
        ghost_defender = create_test_pokemon(types=[Type.GHOST], defense=100)

        normal_move = create_test_move(
            name="Tackle",
            move_type=Type.NORMAL,
            power=40,
            category=MoveCategory.PHYSICAL
        )

        damage, _, effectiveness = calculate_damage(attacker, ghost_defender, normal_move)

        assert damage == 0, "Normal moves should deal 0 damage to Ghost types"
        assert effectiveness == 0, "Effectiveness should be 0 for immunity"

    def test_ground_immune_to_electric(self):
        """Test Ground immunity to Electric"""
        attacker = create_test_pokemon(types=[Type.ELECTRIC], special=100, speed=50)
        ground_defender = create_test_pokemon(types=[Type.GROUND], special=100)

        electric_move = create_test_move(
            name="Thunderbolt",
            move_type=Type.ELECTRIC,
            power=95,
            category=MoveCategory.SPECIAL
        )

        damage, _, effectiveness = calculate_damage(attacker, ground_defender, electric_move)

        assert damage == 0, "Electric moves should deal 0 damage to Ground types"
        assert effectiveness == 0, "Effectiveness should be 0 for immunity"


class TestSTAB:
    """Test Same Type Attack Bonus"""

    def test_stab_increases_damage(self):
        """Test that STAB adds 50% damage"""
        random.seed(0)
        # Fire type using Fire move (STAB)
        fire_pokemon = create_test_pokemon(types=[Type.FIRE], attack=100, special=100, speed=10)
        # Normal type using Fire move (no STAB)
        normal_pokemon = create_test_pokemon(types=[Type.NORMAL], attack=100, special=100, speed=10)

        defender = create_test_pokemon(defense=100, special=100)

        fire_move = create_test_move(
            name="Flamethrower",
            move_type=Type.FIRE,
            power=95,
            category=MoveCategory.SPECIAL
        )

        target_samples = 200
        with_stab = []
        without_stab = []

        while len(with_stab) < target_samples:
            damage, is_crit, _ = calculate_damage(fire_pokemon, defender, fire_move)
            if not is_crit:
                with_stab.append(damage)

        while len(without_stab) < target_samples:
            damage, is_crit, _ = calculate_damage(normal_pokemon, defender, fire_move)
            if not is_crit:
                without_stab.append(damage)

        avg_with = sum(with_stab) / len(with_stab)
        avg_without = sum(without_stab) / len(without_stab)

        ratio = avg_with / avg_without
        assert 1.4 < ratio < 1.6, f"STAB should be ~1.5x, got {ratio:.2f}"


class TestDamageRange:
    """Test the random damage factor (217-255)/255"""

    def test_damage_has_variance(self):
        """Test that damage varies due to random factor"""
        attacker = create_test_pokemon(attack=100, speed=50)
        defender = create_test_pokemon(defense=100)
        move = create_test_move(power=80, category=MoveCategory.PHYSICAL)

        damages = set()
        for _ in range(100):
            damage, is_crit, _ = calculate_damage(attacker, defender, move)
            if not is_crit:  # Exclude crits for cleaner variance check
                damages.add(damage)

        # Should have multiple different damage values
        assert len(damages) > 1, "Damage should vary due to random factor"

    def test_damage_within_gen1_range(self):
        """Test that damage variance matches Gen 1 range (217-255)/255 ≈ 85-100%"""
        attacker = create_test_pokemon(attack=100, speed=10)  # Low speed = fewer crits
        defender = create_test_pokemon(defense=100)
        move = create_test_move(power=100, category=MoveCategory.PHYSICAL)

        non_crit_damages = []
        for _ in range(500):
            damage, is_crit, _ = calculate_damage(attacker, defender, move)
            if not is_crit:
                non_crit_damages.append(damage)

        if non_crit_damages:
            min_dmg = min(non_crit_damages)
            max_dmg = max(non_crit_damages)

            # The ratio should be approximately 217/255 ≈ 0.85
            if max_dmg > 0:
                ratio = min_dmg / max_dmg
                assert 0.80 < ratio < 0.90, f"Damage ratio should be ~0.85, got {ratio:.2f}"
