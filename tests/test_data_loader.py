"""Tests for data loader functionality"""

import pytest

from data.data_loader import (
    get_pokemon_data,
    get_move_data,
    get_pokemon_moves_gen1,
    get_pokemon_moves_with_source,
    get_kanto_pokemon_list,
    create_move,
    get_pokemon_weaknesses_resistances,
)
from models.move import Move
from models.enums import Type, MoveCategory, Status


class TestGetPokemonData:
    """Test Pokemon data retrieval"""

    def test_get_pokemon_by_name(self):
        """Test retrieving Pokemon by name"""
        data = get_pokemon_data("pikachu")

        assert data["name"] == "Pikachu"
        assert "Electric" in data["types"]

    def test_get_pokemon_by_name_case_insensitive(self):
        """Test that Pokemon lookup is case insensitive"""
        data1 = get_pokemon_data("PIKACHU")
        data2 = get_pokemon_data("pikachu")
        data3 = get_pokemon_data("Pikachu")

        assert data1["name"] == data2["name"] == data3["name"]

    def test_get_pokemon_by_id(self):
        """Test retrieving Pokemon by ID"""
        data = get_pokemon_data(25)  # Pikachu's ID

        assert data["name"] == "Pikachu"

    def test_get_pokemon_stats(self):
        """Test that Pokemon data includes stats"""
        data = get_pokemon_data("pikachu")

        assert "stats" in data
        assert "hp" in data["stats"]
        assert "attack" in data["stats"]
        assert "defense" in data["stats"]
        assert "special-attack" in data["stats"]
        assert "speed" in data["stats"]

    def test_get_pokemon_types(self):
        """Test that Pokemon data includes types"""
        data = get_pokemon_data("charizard")

        assert "types" in data
        assert len(data["types"]) == 2  # Fire/Flying
        assert "Fire" in data["types"]
        assert "Flying" in data["types"]

    def test_pokemon_not_found_raises(self):
        """Test that invalid Pokemon name raises ValueError"""
        with pytest.raises(ValueError, match="Pokemon not found"):
            get_pokemon_data("not_a_real_pokemon")

    def test_all_kanto_pokemon_loadable(self):
        """Test that all 151 Kanto Pokemon can be loaded"""
        pokemon_list = get_kanto_pokemon_list()

        assert len(pokemon_list) == 151

        for name in pokemon_list:
            data = get_pokemon_data(name)
            assert data is not None
            assert "name" in data
            assert "types" in data
            assert "stats" in data


class TestGetMoveData:
    """Test move data retrieval"""

    def test_get_move_by_name(self):
        """Test retrieving move by name"""
        data = get_move_data("thunderbolt")

        assert data["name"] == "Thunderbolt"
        assert data["type"] == "Electric"

    def test_get_move_with_hyphen(self):
        """Test retrieving move with hyphenated name"""
        data = get_move_data("thunder-wave")

        assert data["name"] == "Thunder Wave"

    def test_get_move_case_insensitive(self):
        """Test that move lookup is case insensitive"""
        data1 = get_move_data("THUNDERBOLT")
        data2 = get_move_data("thunderbolt")

        assert data1["name"] == data2["name"]

    def test_move_has_required_fields(self):
        """Test that move data includes all required fields"""
        data = get_move_data("thunderbolt")

        assert "name" in data
        assert "type" in data
        assert "category" in data
        assert "power" in data
        assert "accuracy" in data
        assert "pp" in data

    def test_status_move_has_effect(self):
        """Test that status moves have effect data"""
        data = get_move_data("thunder-wave")

        assert data["category"] == "Status"
        assert data["status_effect"] == "PARALYSIS"
        assert data["status_chance"] == 100

    def test_move_with_stat_changes(self):
        """Test that stat-modifying moves have stat_changes"""
        data = get_move_data("swords-dance")

        assert data["stat_changes"] is not None
        assert "ATTACK" in data["stat_changes"]
        assert data["stat_changes"]["ATTACK"] == 2
        assert data["target_self"] is True

    def test_move_not_found_raises(self):
        """Test that invalid move name raises ValueError"""
        with pytest.raises(ValueError, match="Move not found"):
            get_move_data("not_a_real_move")


class TestCreateMove:
    """Test Move object creation"""

    def test_create_move_returns_move_object(self):
        """Test that create_move returns a Move instance"""
        move = create_move("thunderbolt")

        assert isinstance(move, Move)
        assert move.name == "Thunderbolt"

    def test_create_move_sets_type(self):
        """Test that created move has correct type"""
        move = create_move("thunderbolt")

        assert move.type == Type.ELECTRIC

    def test_create_move_sets_category(self):
        """Test that created move has correct category"""
        move = create_move("thunderbolt")

        assert move.category == MoveCategory.SPECIAL

    def test_create_move_sets_stats(self):
        """Test that created move has correct power/accuracy/pp"""
        move = create_move("thunderbolt")

        # Thunderbolt: 90 power in Gen 1 (changed to 95 in later gens)
        assert move.power == 90
        assert move.accuracy == 100
        assert move.pp == 15
        assert move.max_pp == 15

    def test_create_move_with_status_effect(self):
        """Test that status moves have effect set"""
        move = create_move("thunder-wave")

        assert move.status_effect == Status.PARALYSIS
        assert move.status_chance == 100

    def test_create_move_with_stat_changes(self):
        """Test that stat-modifying moves have changes set"""
        from models.enums import StatType

        move = create_move("swords-dance")

        assert move.stat_changes is not None
        assert StatType.ATTACK in move.stat_changes
        assert move.stat_changes[StatType.ATTACK] == 2
        assert move.target_self is True


class TestGetPokemonMoves:
    """Test Pokemon learnset retrieval"""

    def test_get_pokemon_moves_returns_list(self):
        """Test that get_pokemon_moves_gen1 returns a list"""
        moves = get_pokemon_moves_gen1("pikachu")

        assert isinstance(moves, list)
        assert len(moves) > 0

    def test_pokemon_has_expected_moves(self):
        """Test that Pokemon have expected signature moves"""
        pikachu_moves = get_pokemon_moves_gen1("pikachu")

        # Pikachu should learn Thunderbolt
        assert any("thunder" in m.lower() for m in pikachu_moves)

    def test_get_moves_with_source(self):
        """Test that get_pokemon_moves_with_source returns dict with sources"""
        moves = get_pokemon_moves_with_source("pikachu")

        assert isinstance(moves, dict)
        assert len(moves) > 0

        # Check that all values are valid sources
        valid_sources = {"level-up", "tm", "evolution"}
        for move_name, source in moves.items():
            assert source in valid_sources, f"Invalid source {source} for {move_name}"

    def test_evolved_pokemon_has_evolution_moves(self):
        """Test that evolved Pokemon have moves from pre-evolutions"""
        # Raichu should have evolution moves from Pikachu
        moves = get_pokemon_moves_with_source("raichu")

        evolution_moves = [m for m, s in moves.items() if s == "evolution"]

        assert len(evolution_moves) > 0, "Raichu should have evolution moves from Pikachu"

    def test_tm_moves_are_marked(self):
        """Test that TM moves are properly marked"""
        moves = get_pokemon_moves_with_source("pikachu")

        tm_moves = [m for m, s in moves.items() if s == "tm"]

        assert len(tm_moves) > 0, "Pokemon should have TM moves available"


class TestGetKantoPokemonList:
    """Test Kanto Pokemon list retrieval"""

    def test_returns_151_pokemon(self):
        """Test that list contains all 151 Kanto Pokemon"""
        pokemon_list = get_kanto_pokemon_list()

        assert len(pokemon_list) == 151

    def test_list_is_lowercase(self):
        """Test that all names are lowercase"""
        pokemon_list = get_kanto_pokemon_list()

        for name in pokemon_list:
            assert name == name.lower()

    def test_contains_starters(self):
        """Test that list contains starter Pokemon"""
        pokemon_list = get_kanto_pokemon_list()

        assert "bulbasaur" in pokemon_list
        assert "charmander" in pokemon_list
        assert "squirtle" in pokemon_list

    def test_contains_legendaries(self):
        """Test that list contains legendary Pokemon"""
        pokemon_list = get_kanto_pokemon_list()

        assert "articuno" in pokemon_list
        assert "zapdos" in pokemon_list
        assert "moltres" in pokemon_list
        assert "mewtwo" in pokemon_list
        assert "mew" in pokemon_list


class TestWeaknessesResistances:
    """Test type effectiveness calculation"""

    def test_fire_weak_to_water(self):
        """Test that Fire type is weak to Water"""
        result = get_pokemon_weaknesses_resistances(["Fire"])

        # Function returns capitalized type names
        assert "Water" in result["weaknesses"]

    def test_fire_resists_grass(self):
        """Test that Fire type resists Grass"""
        result = get_pokemon_weaknesses_resistances(["Fire"])

        # Function returns capitalized type names
        assert "Grass" in result["resistances"]

    def test_dual_type_4x_weakness(self):
        """Test that dual types can have 4x weaknesses"""
        # Charizard (Fire/Flying) is 4x weak to Rock
        result = get_pokemon_weaknesses_resistances(["Fire", "Flying"])

        # Function returns capitalized type names
        assert "Rock" in result["weaknesses"]

    def test_ground_immune_to_electric(self):
        """Test that Ground type is immune to Electric"""
        result = get_pokemon_weaknesses_resistances(["Ground"])

        # Function returns capitalized type names
        assert "Electric" in result["immunities"]

    def test_ghost_immune_to_normal(self):
        """Test that Ghost type is immune to Normal"""
        result = get_pokemon_weaknesses_resistances(["Ghost"])

        # Function returns capitalized type names
        assert "Normal" in result["immunities"]

    def test_normal_immune_to_ghost(self):
        """Test that Normal type is immune to Ghost (Gen 1)"""
        result = get_pokemon_weaknesses_resistances(["Normal"])

        # Function returns capitalized type names
        assert "Ghost" in result["immunities"]


class TestDataCaching:
    """Test that data is properly cached"""

    def test_pokemon_data_cached(self):
        """Test that repeated Pokemon lookups use cache"""
        # First call loads from file
        data1 = get_pokemon_data("pikachu")

        # Second call should use cache (same result)
        data2 = get_pokemon_data("pikachu")

        assert data1 == data2

    def test_move_data_cached(self):
        """Test that repeated move lookups use cache"""
        data1 = get_move_data("thunderbolt")
        data2 = get_move_data("thunderbolt")

        assert data1 == data2
