"""Tests for ruleset validation."""

import pytest
from models.ruleset import (
    Ruleset, CupType, BattleClauses,
    STANDARD_RULES, POKE_CUP_RULES, PRIME_CUP_RULES,
    LITTLE_CUP_RULES, PIKA_CUP_RULES, PETIT_CUP_RULES,
    BASIC_POKEMON, LEGENDARY_POKEMON,
    get_ruleset_by_name,
)
from models.pokemon import Pokemon
from models.stats import Stats
from models.enums import Type


def create_test_pokemon(name: str = "TestMon", level: int = 50) -> Pokemon:
    """Create a simple test Pokemon."""
    stats = Stats(hp=100, attack=100, defense=100, special=100, speed=100)
    return Pokemon(name, [Type.NORMAL], stats, [], level=level,
                  use_calculated_stats=False)  # Use legacy mode for simpler testing


class TestRulesetValidation:
    """Test ruleset validation logic."""

    def test_standard_rules_accepts_level_50(self):
        """Test that Standard rules accept level 50 Pokemon."""
        pokemon = create_test_pokemon(level=50)
        valid, msg = STANDARD_RULES.validate_pokemon(pokemon)
        assert valid
        assert msg == ""

    def test_standard_rules_accepts_level_100(self):
        """Test that Standard rules accept level 100 Pokemon."""
        pokemon = create_test_pokemon(level=100)
        valid, msg = STANDARD_RULES.validate_pokemon(pokemon)
        assert valid

    def test_poke_cup_level_limits(self):
        """Test Poke Cup level restrictions (50-55)."""
        # Level 50 - valid
        pokemon = create_test_pokemon(level=50)
        valid, _ = POKE_CUP_RULES.validate_pokemon(pokemon)
        assert valid

        # Level 55 - valid
        pokemon = create_test_pokemon(level=55)
        valid, _ = POKE_CUP_RULES.validate_pokemon(pokemon)
        assert valid

        # Level 49 - invalid (too low)
        pokemon = create_test_pokemon(level=49)
        valid, msg = POKE_CUP_RULES.validate_pokemon(pokemon)
        assert not valid
        assert "below minimum" in msg

        # Level 56 - invalid (too high)
        pokemon = create_test_pokemon(level=56)
        valid, msg = POKE_CUP_RULES.validate_pokemon(pokemon)
        assert not valid
        assert "exceeds maximum" in msg

    def test_banned_pokemon(self):
        """Test that banned Pokemon are rejected."""
        mewtwo = create_test_pokemon(name="Mewtwo", level=50)
        valid, msg = POKE_CUP_RULES.validate_pokemon(mewtwo)
        assert not valid
        assert "banned" in msg

        mew = create_test_pokemon(name="Mew", level=50)
        valid, msg = POKE_CUP_RULES.validate_pokemon(mew)
        assert not valid
        assert "banned" in msg

    def test_legendary_restriction(self):
        """Test legendary Pokemon restriction."""
        articuno = create_test_pokemon(name="Articuno", level=50)

        # Poke Cup doesn't allow legendaries
        valid, msg = POKE_CUP_RULES.validate_pokemon(articuno)
        assert not valid
        assert "legendary" in msg.lower()

        # Standard rules allow legendaries
        valid, _ = STANDARD_RULES.validate_pokemon(articuno)
        assert valid

    def test_little_cup_basic_pokemon_only(self):
        """Test Little Cup requires basic Pokemon."""
        # Pikachu is basic - valid
        pikachu = create_test_pokemon(name="Pikachu", level=5)
        valid, _ = LITTLE_CUP_RULES.validate_pokemon(pikachu)
        assert valid

        # Raichu is evolved - invalid
        raichu = create_test_pokemon(name="Raichu", level=5)
        valid, msg = LITTLE_CUP_RULES.validate_pokemon(raichu)
        assert not valid
        assert "basic" in msg.lower()

    def test_little_cup_level_restriction(self):
        """Test Little Cup level 5 restriction."""
        pikachu = create_test_pokemon(name="Pikachu", level=5)
        valid, _ = LITTLE_CUP_RULES.validate_pokemon(pikachu)
        assert valid

        # Level 6 - invalid
        pikachu = create_test_pokemon(name="Pikachu", level=6)
        valid, msg = LITTLE_CUP_RULES.validate_pokemon(pikachu)
        assert not valid


class TestTeamValidation:
    """Test team-level validation."""

    def test_team_size_validation(self):
        """Test team size limits."""
        team = [create_test_pokemon(name=f"Mon{i}", level=50) for i in range(4)]

        # 4 Pokemon is fine for standard (max 6)
        valid, _ = STANDARD_RULES.validate_team(team)
        assert valid

        # But too many for Poke Cup (max 3)
        valid, msg = POKE_CUP_RULES.validate_team(team)
        assert not valid
        assert "exceed" in msg.lower()

    def test_level_sum_limit(self):
        """Test level sum restriction."""
        # Poke Cup: level sum <= 155 for 3 Pokemon
        # Three level 50 Pokemon = 150, valid
        team = [create_test_pokemon(name=f"Mon{i}", level=50) for i in range(3)]
        valid, _ = POKE_CUP_RULES.validate_team(team)
        assert valid

        # Three level 55 Pokemon = 165, invalid
        team = [create_test_pokemon(name=f"Mon{i}", level=55) for i in range(3)]
        valid, msg = POKE_CUP_RULES.validate_team(team)
        assert not valid
        assert "level sum" in msg.lower()

    def test_duplicate_pokemon_rejected(self):
        """Test that duplicate Pokemon are rejected."""
        team = [
            create_test_pokemon(name="Pikachu", level=50),
            create_test_pokemon(name="Pikachu", level=50),  # Duplicate
            create_test_pokemon(name="Charizard", level=50),
        ]

        valid, msg = STANDARD_RULES.validate_team(team)
        assert not valid
        assert "duplicate" in msg.lower()

    def test_empty_team_rejected(self):
        """Test that empty teams are rejected."""
        valid, msg = STANDARD_RULES.validate_team([])
        assert not valid


class TestPredefinedRulesets:
    """Test the predefined rulesets."""

    def test_standard_rules(self):
        """Test Standard rules configuration."""
        assert STANDARD_RULES.name == "Standard"
        assert STANDARD_RULES.default_level == 50
        assert STANDARD_RULES.max_level == 100
        assert STANDARD_RULES.max_team_size == 6

    def test_poke_cup_rules(self):
        """Test Poke Cup rules configuration."""
        assert POKE_CUP_RULES.name == "Poke Cup"
        assert POKE_CUP_RULES.min_level == 50
        assert POKE_CUP_RULES.max_level == 55
        assert POKE_CUP_RULES.level_sum_limit == 155
        assert POKE_CUP_RULES.max_team_size == 3
        assert "mew" in POKE_CUP_RULES.banned_pokemon
        assert "mewtwo" in POKE_CUP_RULES.banned_pokemon

    def test_prime_cup_rules(self):
        """Test Prime Cup rules configuration."""
        assert PRIME_CUP_RULES.name == "Prime Cup"
        assert PRIME_CUP_RULES.default_level == 100
        assert PRIME_CUP_RULES.max_team_size == 3

    def test_little_cup_rules(self):
        """Test Little Cup rules configuration."""
        assert LITTLE_CUP_RULES.name == "Little Cup"
        assert LITTLE_CUP_RULES.default_level == 5
        assert LITTLE_CUP_RULES.max_level == 5
        assert LITTLE_CUP_RULES.basic_pokemon_only
        assert not LITTLE_CUP_RULES.allow_legendaries

    def test_get_ruleset_by_name(self):
        """Test ruleset lookup by name."""
        ruleset = get_ruleset_by_name("Poke Cup")
        assert ruleset == POKE_CUP_RULES

        ruleset = get_ruleset_by_name("poke cup")  # Case insensitive
        assert ruleset == POKE_CUP_RULES

        ruleset = get_ruleset_by_name("NonExistent")
        assert ruleset is None


class TestRulesetDescription:
    """Test ruleset description generation."""

    def test_standard_description(self):
        """Test Standard rules description."""
        desc = STANDARD_RULES.get_description()
        assert "Standard" in desc
        assert "Level" in desc

    def test_poke_cup_description(self):
        """Test Poke Cup description."""
        desc = POKE_CUP_RULES.get_description()
        assert "Poke Cup" in desc
        assert "50-55" in desc or "Level" in desc
        assert "3v3" in desc or "3" in desc

    def test_little_cup_description(self):
        """Test Little Cup description."""
        desc = LITTLE_CUP_RULES.get_description()
        assert "Little Cup" in desc
        assert "Basic" in desc


class TestBasicPokemonList:
    """Test the BASIC_POKEMON set."""

    def test_starters_are_basic(self):
        """Test that starter Pokemon are in basic list."""
        assert "bulbasaur" in BASIC_POKEMON
        assert "charmander" in BASIC_POKEMON
        assert "squirtle" in BASIC_POKEMON

    def test_evolved_not_basic(self):
        """Test that evolved Pokemon are not in basic list."""
        assert "venusaur" not in BASIC_POKEMON
        assert "charizard" not in BASIC_POKEMON
        assert "blastoise" not in BASIC_POKEMON

    def test_single_stage_are_basic(self):
        """Test that single-stage Pokemon are in basic list."""
        assert "tauros" in BASIC_POKEMON
        assert "kangaskhan" in BASIC_POKEMON
        assert "pinsir" in BASIC_POKEMON


class TestLegendaryPokemonList:
    """Test the LEGENDARY_POKEMON set."""

    def test_legendary_birds(self):
        """Test legendary birds are in the list."""
        assert "articuno" in LEGENDARY_POKEMON
        assert "zapdos" in LEGENDARY_POKEMON
        assert "moltres" in LEGENDARY_POKEMON

    def test_mewtwo_mew(self):
        """Test Mewtwo and Mew are legendary."""
        assert "mewtwo" in LEGENDARY_POKEMON
        assert "mew" in LEGENDARY_POKEMON

    def test_non_legendary_not_included(self):
        """Test regular Pokemon are not legendary."""
        assert "pikachu" not in LEGENDARY_POKEMON
        assert "charizard" not in LEGENDARY_POKEMON


class TestBattleClausesOnRulesets:
    """Test battle clauses on predefined rulesets."""

    def test_standard_has_no_clauses(self):
        """Standard rules should have no clauses active."""
        assert not STANDARD_RULES.clauses.any_active()

    def test_prime_cup_has_no_clauses(self):
        """Prime Cup should have no clauses active."""
        assert not PRIME_CUP_RULES.clauses.any_active()

    def test_poke_cup_has_sleep_freeze_clauses(self):
        """Poke Cup should have sleep and freeze clauses."""
        assert POKE_CUP_RULES.clauses.sleep_clause
        assert POKE_CUP_RULES.clauses.freeze_clause
        assert not POKE_CUP_RULES.clauses.ohko_clause
        assert not POKE_CUP_RULES.clauses.evasion_clause

    def test_little_cup_has_sleep_freeze_clauses(self):
        """Little Cup should have sleep and freeze clauses."""
        assert LITTLE_CUP_RULES.clauses.sleep_clause
        assert LITTLE_CUP_RULES.clauses.freeze_clause

    def test_pika_cup_has_sleep_freeze_clauses(self):
        """Pika Cup should have sleep and freeze clauses."""
        assert PIKA_CUP_RULES.clauses.sleep_clause
        assert PIKA_CUP_RULES.clauses.freeze_clause

    def test_petit_cup_has_sleep_freeze_clauses(self):
        """Petit Cup should have sleep and freeze clauses."""
        assert PETIT_CUP_RULES.clauses.sleep_clause
        assert PETIT_CUP_RULES.clauses.freeze_clause


class TestPetitCupPhysicalRestrictions:
    """Test Petit Cup height/weight restrictions."""

    def test_petit_cup_has_height_limit(self):
        """Petit Cup should have a max height."""
        assert PETIT_CUP_RULES.max_height_m == 2.0

    def test_petit_cup_has_weight_limit(self):
        """Petit Cup should have a max weight."""
        assert PETIT_CUP_RULES.max_weight_kg == 20.0

    def test_validate_pokemon_physical_accepts_small(self):
        """Small Pokemon should pass physical validation."""
        valid, _ = PETIT_CUP_RULES.validate_pokemon_physical("Pikachu", 0.4, 6.0)
        assert valid

    def test_validate_pokemon_physical_rejects_tall(self):
        """Pokemon exceeding height limit should be rejected."""
        valid, msg = PETIT_CUP_RULES.validate_pokemon_physical("Onix", 8.8, 210.0)
        assert not valid
        assert "height" in msg

    def test_validate_pokemon_physical_rejects_heavy(self):
        """Pokemon exceeding weight limit should be rejected."""
        valid, msg = PETIT_CUP_RULES.validate_pokemon_physical("Snorlax", 2.1, 460.0)
        assert not valid
        # Could fail on either height or weight — Snorlax exceeds both
        assert "height" in msg or "weight" in msg

    def test_no_physical_limits_on_standard(self):
        """Standard rules should have no physical restrictions."""
        assert STANDARD_RULES.max_height_m is None
        assert STANDARD_RULES.max_weight_kg is None
        # Should always pass
        valid, _ = STANDARD_RULES.validate_pokemon_physical("Onix", 8.8, 210.0)
        assert valid

    def test_petit_cup_description_includes_limits(self):
        """Petit Cup description should mention height/weight limits."""
        desc = PETIT_CUP_RULES.get_description()
        assert "Height" in desc or "height" in desc
        assert "Weight" in desc or "weight" in desc

    def test_poke_cup_description_includes_clauses(self):
        """Poke Cup description should mention active clauses."""
        desc = POKE_CUP_RULES.get_description()
        assert "Sleep Clause" in desc
        assert "Freeze Clause" in desc
