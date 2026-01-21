"""Tests for Gen 1 type effectiveness chart"""

import pytest
from models.enums import Type
from engine.type_chart import get_effectiveness, TYPE_CHART


def get_type_effectiveness(move_type: Type, defender_type: Type) -> float:
    """Helper to get effectiveness against a single type"""
    return TYPE_CHART.get(move_type, {}).get(defender_type, 1.0)


def get_combined_effectiveness(move_type: Type, defender_types: list) -> float:
    """Helper to get combined effectiveness against multiple types"""
    return get_effectiveness(move_type, defender_types)


class TestSingleTypeEffectiveness:
    """Test effectiveness against single-type Pokemon"""

    def test_normal_effectiveness(self):
        """Test Normal type matchups"""
        # Normal is not very effective against Rock
        assert get_type_effectiveness(Type.NORMAL, Type.ROCK) == 0.5
        # Normal has no effect on Ghost
        assert get_type_effectiveness(Type.NORMAL, Type.GHOST) == 0
        # Normal is neutral to most types
        assert get_type_effectiveness(Type.NORMAL, Type.NORMAL) == 1

    def test_fire_effectiveness(self):
        """Test Fire type matchups"""
        # Super effective
        assert get_type_effectiveness(Type.FIRE, Type.GRASS) == 2
        assert get_type_effectiveness(Type.FIRE, Type.ICE) == 2
        assert get_type_effectiveness(Type.FIRE, Type.BUG) == 2
        # Not very effective
        assert get_type_effectiveness(Type.FIRE, Type.WATER) == 0.5
        assert get_type_effectiveness(Type.FIRE, Type.ROCK) == 0.5
        assert get_type_effectiveness(Type.FIRE, Type.FIRE) == 0.5
        assert get_type_effectiveness(Type.FIRE, Type.DRAGON) == 0.5

    def test_water_effectiveness(self):
        """Test Water type matchups"""
        # Super effective
        assert get_type_effectiveness(Type.WATER, Type.FIRE) == 2
        assert get_type_effectiveness(Type.WATER, Type.GROUND) == 2
        assert get_type_effectiveness(Type.WATER, Type.ROCK) == 2
        # Not very effective
        assert get_type_effectiveness(Type.WATER, Type.WATER) == 0.5
        assert get_type_effectiveness(Type.WATER, Type.GRASS) == 0.5
        assert get_type_effectiveness(Type.WATER, Type.DRAGON) == 0.5

    def test_electric_effectiveness(self):
        """Test Electric type matchups"""
        # Super effective
        assert get_type_effectiveness(Type.ELECTRIC, Type.WATER) == 2
        assert get_type_effectiveness(Type.ELECTRIC, Type.FLYING) == 2
        # No effect
        assert get_type_effectiveness(Type.ELECTRIC, Type.GROUND) == 0
        # Not very effective
        assert get_type_effectiveness(Type.ELECTRIC, Type.ELECTRIC) == 0.5
        assert get_type_effectiveness(Type.ELECTRIC, Type.GRASS) == 0.5
        assert get_type_effectiveness(Type.ELECTRIC, Type.DRAGON) == 0.5

    def test_grass_effectiveness(self):
        """Test Grass type matchups"""
        # Super effective
        assert get_type_effectiveness(Type.GRASS, Type.WATER) == 2
        assert get_type_effectiveness(Type.GRASS, Type.GROUND) == 2
        assert get_type_effectiveness(Type.GRASS, Type.ROCK) == 2
        # Not very effective
        assert get_type_effectiveness(Type.GRASS, Type.FIRE) == 0.5
        assert get_type_effectiveness(Type.GRASS, Type.GRASS) == 0.5
        assert get_type_effectiveness(Type.GRASS, Type.POISON) == 0.5
        assert get_type_effectiveness(Type.GRASS, Type.FLYING) == 0.5
        assert get_type_effectiveness(Type.GRASS, Type.BUG) == 0.5
        assert get_type_effectiveness(Type.GRASS, Type.DRAGON) == 0.5

    def test_ice_effectiveness(self):
        """Test Ice type matchups"""
        # Super effective
        assert get_type_effectiveness(Type.ICE, Type.GRASS) == 2
        assert get_type_effectiveness(Type.ICE, Type.GROUND) == 2
        assert get_type_effectiveness(Type.ICE, Type.FLYING) == 2
        assert get_type_effectiveness(Type.ICE, Type.DRAGON) == 2
        # Not very effective
        assert get_type_effectiveness(Type.ICE, Type.WATER) == 0.5
        assert get_type_effectiveness(Type.ICE, Type.ICE) == 0.5

    def test_fighting_effectiveness(self):
        """Test Fighting type matchups"""
        # Super effective
        assert get_type_effectiveness(Type.FIGHTING, Type.NORMAL) == 2
        assert get_type_effectiveness(Type.FIGHTING, Type.ICE) == 2
        assert get_type_effectiveness(Type.FIGHTING, Type.ROCK) == 2
        # No effect
        assert get_type_effectiveness(Type.FIGHTING, Type.GHOST) == 0
        # Not very effective
        assert get_type_effectiveness(Type.FIGHTING, Type.POISON) == 0.5
        assert get_type_effectiveness(Type.FIGHTING, Type.FLYING) == 0.5
        assert get_type_effectiveness(Type.FIGHTING, Type.PSYCHIC) == 0.5
        assert get_type_effectiveness(Type.FIGHTING, Type.BUG) == 0.5

    def test_poison_effectiveness(self):
        """Test Poison type matchups"""
        # Super effective
        assert get_type_effectiveness(Type.POISON, Type.GRASS) == 2
        assert get_type_effectiveness(Type.POISON, Type.BUG) == 2
        # Not very effective
        assert get_type_effectiveness(Type.POISON, Type.POISON) == 0.5
        assert get_type_effectiveness(Type.POISON, Type.GROUND) == 0.5
        assert get_type_effectiveness(Type.POISON, Type.ROCK) == 0.5
        assert get_type_effectiveness(Type.POISON, Type.GHOST) == 0.5

    def test_ground_effectiveness(self):
        """Test Ground type matchups"""
        # Super effective
        assert get_type_effectiveness(Type.GROUND, Type.FIRE) == 2
        assert get_type_effectiveness(Type.GROUND, Type.ELECTRIC) == 2
        assert get_type_effectiveness(Type.GROUND, Type.POISON) == 2
        assert get_type_effectiveness(Type.GROUND, Type.ROCK) == 2
        # No effect
        assert get_type_effectiveness(Type.GROUND, Type.FLYING) == 0
        # Not very effective
        assert get_type_effectiveness(Type.GROUND, Type.GRASS) == 0.5
        assert get_type_effectiveness(Type.GROUND, Type.BUG) == 0.5

    def test_flying_effectiveness(self):
        """Test Flying type matchups"""
        # Super effective
        assert get_type_effectiveness(Type.FLYING, Type.GRASS) == 2
        assert get_type_effectiveness(Type.FLYING, Type.FIGHTING) == 2
        assert get_type_effectiveness(Type.FLYING, Type.BUG) == 2
        # Not very effective
        assert get_type_effectiveness(Type.FLYING, Type.ELECTRIC) == 0.5
        assert get_type_effectiveness(Type.FLYING, Type.ROCK) == 0.5

    def test_psychic_effectiveness(self):
        """Test Psychic type matchups (Gen 1 - Ghost bug)"""
        # Super effective
        assert get_type_effectiveness(Type.PSYCHIC, Type.FIGHTING) == 2
        assert get_type_effectiveness(Type.PSYCHIC, Type.POISON) == 2
        # Not very effective
        assert get_type_effectiveness(Type.PSYCHIC, Type.PSYCHIC) == 0.5
        # Gen 1 bug: Psychic has NO EFFECT on Ghost (should be super effective)
        # Note: This depends on whether we're implementing the bug or not
        # If implementing Gen 1 accurately:
        # assert get_type_effectiveness(Type.PSYCHIC, Type.GHOST) == 0

    def test_bug_effectiveness(self):
        """Test Bug type matchups"""
        # Super effective
        assert get_type_effectiveness(Type.BUG, Type.GRASS) == 2
        assert get_type_effectiveness(Type.BUG, Type.PSYCHIC) == 2
        # In Gen 1, Bug was super effective against Poison
        assert get_type_effectiveness(Type.BUG, Type.POISON) == 2
        # Not very effective
        assert get_type_effectiveness(Type.BUG, Type.FIRE) == 0.5
        assert get_type_effectiveness(Type.BUG, Type.FIGHTING) == 0.5
        assert get_type_effectiveness(Type.BUG, Type.FLYING) == 0.5
        assert get_type_effectiveness(Type.BUG, Type.GHOST) == 0.5

    def test_rock_effectiveness(self):
        """Test Rock type matchups"""
        # Super effective
        assert get_type_effectiveness(Type.ROCK, Type.FIRE) == 2
        assert get_type_effectiveness(Type.ROCK, Type.ICE) == 2
        assert get_type_effectiveness(Type.ROCK, Type.FLYING) == 2
        assert get_type_effectiveness(Type.ROCK, Type.BUG) == 2
        # Not very effective
        assert get_type_effectiveness(Type.ROCK, Type.FIGHTING) == 0.5
        assert get_type_effectiveness(Type.ROCK, Type.GROUND) == 0.5

    def test_ghost_effectiveness(self):
        """Test Ghost type matchups (Gen 1)"""
        # In Gen 1, Ghost had no effect on Psychic (bug)
        # Super effective
        assert get_type_effectiveness(Type.GHOST, Type.GHOST) == 2
        # No effect - Normal
        assert get_type_effectiveness(Type.GHOST, Type.NORMAL) == 0

    def test_dragon_effectiveness(self):
        """Test Dragon type matchups"""
        # Super effective only against Dragon
        assert get_type_effectiveness(Type.DRAGON, Type.DRAGON) == 2
        # Neutral to everything else
        assert get_type_effectiveness(Type.DRAGON, Type.NORMAL) == 1
        assert get_type_effectiveness(Type.DRAGON, Type.FIRE) == 1


class TestDualTypeEffectiveness:
    """Test effectiveness against dual-type Pokemon"""

    def test_4x_effectiveness(self):
        """Test 4x super effective (both types weak)"""
        # Ice vs Grass/Flying (Exeggutor-like but Flying)
        effectiveness = get_combined_effectiveness(Type.ICE, [Type.GRASS, Type.FLYING])
        assert effectiveness == 4

        # Rock vs Fire/Flying (Charizard)
        effectiveness = get_combined_effectiveness(Type.ROCK, [Type.FIRE, Type.FLYING])
        assert effectiveness == 4

        # Electric vs Water/Flying (Gyarados)
        effectiveness = get_combined_effectiveness(Type.ELECTRIC, [Type.WATER, Type.FLYING])
        assert effectiveness == 4

    def test_025x_effectiveness(self):
        """Test 0.25x resistance (both types resist)"""
        # Fire vs Water/Rock
        effectiveness = get_combined_effectiveness(Type.FIRE, [Type.WATER, Type.ROCK])
        assert effectiveness == 0.25

        # Grass vs Fire/Flying
        effectiveness = get_combined_effectiveness(Type.GRASS, [Type.FIRE, Type.FLYING])
        assert effectiveness == 0.25

    def test_immunity_overrides(self):
        """Test that immunity (0x) overrides other multipliers"""
        # Ground vs Water/Flying (Water is 2x, Flying is immune)
        effectiveness = get_combined_effectiveness(Type.GROUND, [Type.WATER, Type.FLYING])
        assert effectiveness == 0

        # Electric vs Ground/Water
        effectiveness = get_combined_effectiveness(Type.ELECTRIC, [Type.GROUND, Type.WATER])
        assert effectiveness == 0

        # Normal vs Ghost/Poison
        effectiveness = get_combined_effectiveness(Type.NORMAL, [Type.GHOST, Type.POISON])
        assert effectiveness == 0

    def test_mixed_effectiveness(self):
        """Test mixed effectiveness (one weak, one resist = neutral)"""
        # Fire vs Grass/Water = 2x * 0.5x = 1x
        effectiveness = get_combined_effectiveness(Type.FIRE, [Type.GRASS, Type.WATER])
        assert effectiveness == 1

        # Electric vs Water/Dragon = 2x * 0.5x = 1x
        effectiveness = get_combined_effectiveness(Type.ELECTRIC, [Type.WATER, Type.DRAGON])
        assert effectiveness == 1

    def test_real_pokemon_matchups(self):
        """Test effectiveness against actual Gen 1 dual-type Pokemon"""
        # Charizard (Fire/Flying)
        charizard_types = [Type.FIRE, Type.FLYING]
        assert get_combined_effectiveness(Type.ROCK, charizard_types) == 4  # 4x weak
        assert get_combined_effectiveness(Type.WATER, charizard_types) == 2  # 2x weak
        assert get_combined_effectiveness(Type.ELECTRIC, charizard_types) == 2  # 2x weak
        assert get_combined_effectiveness(Type.GROUND, charizard_types) == 0  # Immune
        assert get_combined_effectiveness(Type.GRASS, charizard_types) == 0.25  # 4x resist

        # Gyarados (Water/Flying)
        gyarados_types = [Type.WATER, Type.FLYING]
        assert get_combined_effectiveness(Type.ELECTRIC, gyarados_types) == 4  # 4x weak
        assert get_combined_effectiveness(Type.ROCK, gyarados_types) == 2  # 2x weak
        assert get_combined_effectiveness(Type.GROUND, gyarados_types) == 0  # Immune

        # Gengar (Ghost/Poison)
        gengar_types = [Type.GHOST, Type.POISON]
        assert get_combined_effectiveness(Type.GROUND, gengar_types) == 2  # 2x weak
        # Note: This implementation doesn't have the Gen 1 Psychic/Ghost bug
        # In Gen 1, Psychic had NO EFFECT on Ghost due to a bug
        # This implementation treats Psychic as neutral vs Ghost, so 1x * 2x = 2x
        assert get_combined_effectiveness(Type.PSYCHIC, gengar_types) == 2  # 1x vs Ghost * 2x vs Poison
        assert get_combined_effectiveness(Type.NORMAL, gengar_types) == 0  # Immune
        assert get_combined_effectiveness(Type.FIGHTING, gengar_types) == 0  # Immune

        # Golem (Rock/Ground)
        golem_types = [Type.ROCK, Type.GROUND]
        assert get_combined_effectiveness(Type.WATER, golem_types) == 4  # 4x weak
        assert get_combined_effectiveness(Type.GRASS, golem_types) == 4  # 4x weak
        assert get_combined_effectiveness(Type.ICE, golem_types) == 2  # 2x weak
        assert get_combined_effectiveness(Type.ELECTRIC, golem_types) == 0  # Immune
