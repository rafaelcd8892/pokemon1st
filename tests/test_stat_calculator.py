"""Tests for Gen 1 stat calculation formulas."""

import pytest
from engine.stat_calculator import (
    calculate_hp,
    calculate_other_stat,
    calculate_stats,
    MAX_STAT_EV,
    ZERO_EV,
)
from models.stats import Stats
from models.ivs import IVs


class TestGen1StatFormulas:
    """Test the Gen 1 stat calculation formulas."""

    def test_hp_formula_level_100_max_ivs_max_evs(self):
        """Test HP at level 100 with max IVs and EVs."""
        # Base HP 100, IV 15, EV 65535, Level 100
        # HP = floor(((100 + 15) * 2 + floor(sqrt(65535) / 4)) * 100 / 100) + 100 + 10
        # HP = floor((115 * 2 + 63) * 1) + 110 = 230 + 63 + 110 = 403
        result = calculate_hp(100, 15, MAX_STAT_EV, 100)
        assert result == 403

    def test_hp_formula_level_50_max_ivs_max_evs(self):
        """Test HP at level 50 with max IVs and EVs."""
        # Base HP 100, IV 15, EV 65535, Level 50
        # HP = floor(((100 + 15) * 2 + 63) * 50 / 100) + 50 + 10
        # HP = floor(293 * 0.5) + 60 = 146 + 60 = 206
        result = calculate_hp(100, 15, MAX_STAT_EV, 50)
        assert result == 206

    def test_hp_formula_level_5_max_ivs_zero_evs(self):
        """Test HP at level 5 (Little Cup) with no EVs."""
        # Base HP 100, IV 15, EV 0, Level 5
        # HP = floor(((100 + 15) * 2 + 0) * 5 / 100) + 5 + 10
        # HP = floor(230 * 0.05) + 15 = 11 + 15 = 26
        result = calculate_hp(100, 15, ZERO_EV, 5)
        assert result == 26

    def test_other_stat_formula_level_100(self):
        """Test non-HP stat at level 100."""
        # Base 100, IV 15, EV 65535, Level 100
        # Stat = floor(((100 + 15) * 2 + 63) * 100 / 100) + 5
        # Stat = floor(293 * 1) + 5 = 293 + 5 = 298
        result = calculate_other_stat(100, 15, MAX_STAT_EV, 100)
        assert result == 298

    def test_other_stat_formula_level_50(self):
        """Test non-HP stat at level 50."""
        # Base 100, IV 15, EV 65535, Level 50
        # Stat = floor(((100 + 15) * 2 + 63) * 50 / 100) + 5
        # Stat = floor(293 * 0.5) + 5 = 146 + 5 = 151
        result = calculate_other_stat(100, 15, MAX_STAT_EV, 50)
        assert result == 151

    def test_other_stat_formula_level_5_zero_evs(self):
        """Test non-HP stat at level 5 with no EVs."""
        # Base 100, IV 15, EV 0, Level 5
        # Stat = floor(((100 + 15) * 2 + 0) * 5 / 100) + 5
        # Stat = floor(230 * 0.05) + 5 = 11 + 5 = 16
        result = calculate_other_stat(100, 15, ZERO_EV, 5)
        assert result == 16

    def test_pikachu_stats_level_50(self):
        """Test Pikachu's stats at level 50 (known reference values)."""
        # Pikachu base stats: HP 35, Atk 55, Def 40, Spc 50, Spe 90
        pikachu_base = Stats(hp=35, attack=55, defense=40, special=50, speed=90)
        ivs = IVs.perfect()

        stats = calculate_stats(pikachu_base, ivs, 50, use_max_evs=True)

        # With max IVs (15) and max EVs (65535) at level 50:
        # HP = floor(((35+15)*2 + 63) * 50/100) + 50 + 10 = floor(163*0.5) + 60 = 81 + 60 = 141
        assert stats.hp == 141

        # Atk = floor(((55+15)*2 + 63) * 50/100) + 5 = floor(203*0.5) + 5 = 101 + 5 = 106
        assert stats.attack == 106

    def test_level_scaling(self):
        """Test that stats scale correctly with level."""
        base_stats = Stats(hp=100, attack=100, defense=100, special=100, speed=100)
        ivs = IVs.perfect()

        stats_5 = calculate_stats(base_stats, ivs, 5)
        stats_50 = calculate_stats(base_stats, ivs, 50)
        stats_100 = calculate_stats(base_stats, ivs, 100)

        # Higher level should have higher stats
        assert stats_100.hp > stats_50.hp > stats_5.hp
        assert stats_100.attack > stats_50.attack > stats_5.attack
        assert stats_100.speed > stats_50.speed > stats_5.speed

    def test_iv_impact(self):
        """Test that IVs affect stats correctly."""
        base_stats = Stats(hp=100, attack=100, defense=100, special=100, speed=100)

        perfect_ivs = IVs.perfect()
        zero_ivs = IVs.zero()

        stats_perfect = calculate_stats(base_stats, perfect_ivs, 50)
        stats_zero = calculate_stats(base_stats, zero_ivs, 50)

        # Perfect IVs should give higher stats
        assert stats_perfect.attack > stats_zero.attack
        assert stats_perfect.defense > stats_zero.defense
        assert stats_perfect.speed > stats_zero.speed

    def test_ev_impact(self):
        """Test that EVs affect stats correctly."""
        base_stats = Stats(hp=100, attack=100, defense=100, special=100, speed=100)
        ivs = IVs.perfect()

        stats_max_ev = calculate_stats(base_stats, ivs, 50, use_max_evs=True)
        stats_zero_ev = calculate_stats(base_stats, ivs, 50, use_max_evs=False)

        # Max EVs should give higher stats
        assert stats_max_ev.hp > stats_zero_ev.hp
        assert stats_max_ev.attack > stats_zero_ev.attack


class TestIVs:
    """Test the IVs dataclass."""

    def test_hp_iv_derived_all_15(self):
        """Test HP IV calculation with all 15s."""
        ivs = IVs(attack=15, defense=15, speed=15, special=15)
        # All LSBs are 1: 1111 = 15
        assert ivs.hp == 15

    def test_hp_iv_derived_all_0(self):
        """Test HP IV calculation with all 0s."""
        ivs = IVs(attack=0, defense=0, speed=0, special=0)
        # All LSBs are 0: 0000 = 0
        assert ivs.hp == 0

    def test_hp_iv_derived_mixed(self):
        """Test HP IV calculation with mixed values."""
        # Attack=1 (LSB=1), Defense=0 (LSB=0), Speed=1 (LSB=1), Special=0 (LSB=0)
        ivs = IVs(attack=1, defense=0, speed=1, special=0)
        # HP = 1*8 + 0*4 + 1*2 + 0*1 = 8 + 2 = 10
        assert ivs.hp == 10

    def test_random_ivs_in_range(self):
        """Test that random IVs are in valid range."""
        for _ in range(100):
            ivs = IVs.random()
            assert 0 <= ivs.attack <= 15
            assert 0 <= ivs.defense <= 15
            assert 0 <= ivs.special <= 15
            assert 0 <= ivs.speed <= 15
            assert 0 <= ivs.hp <= 15

    def test_perfect_ivs(self):
        """Test perfect IVs factory."""
        ivs = IVs.perfect()
        assert ivs.attack == 15
        assert ivs.defense == 15
        assert ivs.special == 15
        assert ivs.speed == 15
        assert ivs.hp == 15

    def test_zero_ivs(self):
        """Test zero IVs factory."""
        ivs = IVs.zero()
        assert ivs.attack == 0
        assert ivs.defense == 0
        assert ivs.special == 0
        assert ivs.speed == 0
        assert ivs.hp == 0

    def test_iv_validation(self):
        """Test that invalid IVs raise errors."""
        with pytest.raises(ValueError):
            IVs(attack=16, defense=15, special=15, speed=15)

        with pytest.raises(ValueError):
            IVs(attack=-1, defense=15, special=15, speed=15)


class TestPokemonStatCalculation:
    """Test stat calculation integration with Pokemon class."""

    def test_pokemon_uses_calculated_stats_by_default(self):
        """Test that Pokemon uses calculated stats by default."""
        from models.pokemon import Pokemon
        from models.enums import Type

        base_stats = Stats(hp=100, attack=100, defense=100, special=100, speed=100)
        pokemon = Pokemon("Test", [Type.NORMAL], base_stats, [], level=50)

        # base_stats property should return calculated stats, not species base
        assert pokemon.base_stats.hp != base_stats.hp  # Calculated HP will be different
        assert pokemon.species_base_stats.hp == base_stats.hp

    def test_pokemon_legacy_mode(self):
        """Test Pokemon with use_calculated_stats=False."""
        from models.pokemon import Pokemon
        from models.enums import Type

        base_stats = Stats(hp=100, attack=100, defense=100, special=100, speed=100)
        pokemon = Pokemon("Test", [Type.NORMAL], base_stats, [], level=50,
                         use_calculated_stats=False)

        # In legacy mode, base_stats should return the original stats
        assert pokemon.base_stats.hp == base_stats.hp

    def test_pokemon_level_affects_stats(self):
        """Test that Pokemon level affects calculated stats."""
        from models.pokemon import Pokemon
        from models.enums import Type

        base_stats = Stats(hp=100, attack=100, defense=100, special=100, speed=100)

        pokemon_50 = Pokemon("Test", [Type.NORMAL], base_stats, [], level=50)
        pokemon_100 = Pokemon("Test", [Type.NORMAL], base_stats, [], level=100)

        assert pokemon_100.base_stats.hp > pokemon_50.base_stats.hp
        assert pokemon_100.base_stats.attack > pokemon_50.base_stats.attack

    def test_pokemon_recalculate_stats(self):
        """Test recalculating stats after level change."""
        from models.pokemon import Pokemon
        from models.enums import Type

        base_stats = Stats(hp=100, attack=100, defense=100, special=100, speed=100)
        pokemon = Pokemon("Test", [Type.NORMAL], base_stats, [], level=50)

        old_hp = pokemon.base_stats.hp
        old_attack = pokemon.base_stats.attack

        # Level up
        pokemon.level = 51
        pokemon.recalculate_stats()

        assert pokemon.base_stats.hp > old_hp
        assert pokemon.base_stats.attack > old_attack
