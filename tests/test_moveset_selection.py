"""Tests for moveset selection functionality"""

import pytest
from data.data_loader import (
    get_preset_moveset,
    get_random_moveset,
    get_smart_random_moveset,
    get_moveset_for_pokemon,
    get_pokemon_moves_gen1
)


class TestPresetMovesets:
    """Tests for preset moveset loading"""

    def test_get_preset_for_known_pokemon(self):
        """Test getting preset for a Pokemon with presets"""
        preset = get_preset_moveset("alakazam")
        assert preset is not None
        assert len(preset) == 4
        assert all(isinstance(m, str) for m in preset)

    def test_get_preset_for_unknown_pokemon(self):
        """Test getting preset for a Pokemon without presets returns None"""
        preset = get_preset_moveset("magikarp")
        assert preset is None

    def test_preset_competitive_variant(self):
        """Test getting competitive variant"""
        preset = get_preset_moveset("pikachu", "competitive")
        assert preset is not None
        assert "thunderbolt" in preset or "thunder-wave" in preset

    def test_preset_alternative_variant(self):
        """Test getting alternative variant"""
        preset = get_preset_moveset("alakazam", "alternative")
        assert preset is not None
        assert len(preset) == 4


class TestRandomMovesets:
    """Tests for random moveset generation"""

    def test_random_moveset_returns_four_moves(self):
        """Test that random moveset returns 4 moves"""
        moveset = get_random_moveset("pikachu")
        assert len(moveset) == 4

    def test_random_moveset_all_valid(self):
        """Test that all moves are valid for the Pokemon"""
        moveset = get_random_moveset("charizard")
        available = get_pokemon_moves_gen1("charizard")
        for move in moveset:
            assert move in available

    def test_random_moveset_handles_small_pools(self):
        """Test handling Pokemon with few moves"""
        # Magikarp only learns a few moves
        moveset = get_random_moveset("magikarp")
        assert len(moveset) <= 4
        assert len(moveset) > 0


class TestSmartRandomMovesets:
    """Tests for smart random moveset generation"""

    def test_smart_random_returns_four_moves(self):
        """Test that smart random returns 4 moves"""
        moveset = get_smart_random_moveset("charizard")
        assert len(moveset) == 4

    def test_smart_random_all_valid(self):
        """Test that all moves are valid for the Pokemon"""
        moveset = get_smart_random_moveset("venusaur")
        available = get_pokemon_moves_gen1("venusaur")
        for move in moveset:
            assert move in available

    def test_smart_random_has_variety(self):
        """Test that smart random generates diverse movesets"""
        # Run multiple times to check for variety
        movesets = [get_smart_random_moveset("mewtwo") for _ in range(10)]
        unique_movesets = [tuple(sorted(m)) for m in movesets]
        # Should have some variety
        assert len(set(unique_movesets)) >= 2


class TestMovesetForPokemon:
    """Tests for the unified get_moveset_for_pokemon function"""

    def test_random_mode(self):
        """Test random mode"""
        moveset = get_moveset_for_pokemon("pikachu", "random")
        assert len(moveset) == 4

    def test_preset_mode_with_preset(self):
        """Test preset mode for Pokemon with presets"""
        moveset = get_moveset_for_pokemon("alakazam", "preset")
        assert len(moveset) == 4

    def test_preset_mode_falls_back_to_smart(self):
        """Test preset mode falls back to smart random for Pokemon without presets"""
        moveset = get_moveset_for_pokemon("rattata", "preset")
        assert len(moveset) == 4

    def test_smart_random_mode(self):
        """Test smart_random mode"""
        moveset = get_moveset_for_pokemon("dragonite", "smart_random")
        assert len(moveset) == 4

    def test_default_to_random(self):
        """Test unknown mode defaults to random"""
        moveset = get_moveset_for_pokemon("pikachu", "unknown_mode")
        assert len(moveset) == 4
