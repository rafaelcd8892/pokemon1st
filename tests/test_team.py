"""Tests for Team model and team battle functionality"""

import pytest
from unittest.mock import patch

from models.team import Team
from models.enums import Type, Status, BattleFormat
from tests.conftest import create_test_pokemon, create_test_move


class TestTeamCreation:
    """Test Team initialization and validation"""

    def test_create_team_with_single_pokemon(self):
        """Test creating a team with one Pokemon"""
        pokemon = create_test_pokemon(name="Pikachu")
        team = Team([pokemon], "Trainer")

        assert team.size == 1
        assert team.active_pokemon == pokemon
        assert team.name == "Trainer"

    def test_create_team_with_multiple_pokemon(self):
        """Test creating a team with multiple Pokemon"""
        pokemon1 = create_test_pokemon(name="Pikachu")
        pokemon2 = create_test_pokemon(name="Charizard")
        pokemon3 = create_test_pokemon(name="Blastoise")

        team = Team([pokemon1, pokemon2, pokemon3], "Ash")

        assert team.size == 3
        assert team.active_pokemon == pokemon1

    def test_create_team_with_max_pokemon(self):
        """Test creating a full team of 6"""
        pokemon_list = [create_test_pokemon(name=f"Pokemon{i}") for i in range(6)]
        team = Team(pokemon_list)

        assert team.size == 6

    def test_empty_team_raises_error(self):
        """Test that empty team raises ValueError"""
        with pytest.raises(ValueError, match="Team must have 1-6 Pokemon"):
            Team([])

    def test_oversized_team_raises_error(self):
        """Test that team with more than 6 raises ValueError"""
        pokemon_list = [create_test_pokemon(name=f"Pokemon{i}") for i in range(7)]

        with pytest.raises(ValueError, match="Team must have 1-6 Pokemon"):
            Team(pokemon_list)


class TestTeamActiveManagement:
    """Test active Pokemon management"""

    def test_active_pokemon_is_first(self):
        """Test that first Pokemon is active by default"""
        pokemon1 = create_test_pokemon(name="First")
        pokemon2 = create_test_pokemon(name="Second")
        team = Team([pokemon1, pokemon2])

        assert team.active_pokemon.name == "First"

    def test_switch_pokemon(self):
        """Test switching to another Pokemon"""
        pokemon1 = create_test_pokemon(name="First")
        pokemon2 = create_test_pokemon(name="Second")
        team = Team([pokemon1, pokemon2])

        result = team.switch_pokemon(1)

        assert result is True
        assert team.active_pokemon.name == "Second"

    def test_switch_to_same_pokemon_fails(self):
        """Test that switching to current Pokemon fails"""
        pokemon1 = create_test_pokemon(name="First")
        pokemon2 = create_test_pokemon(name="Second")
        team = Team([pokemon1, pokemon2])

        result = team.switch_pokemon(0)

        assert result is False
        assert team.active_pokemon.name == "First"

    def test_switch_to_fainted_pokemon_fails(self):
        """Test that switching to fainted Pokemon fails"""
        pokemon1 = create_test_pokemon(name="First", hp=100)
        pokemon2 = create_test_pokemon(name="Fainted", hp=100)
        pokemon2.current_hp = 0

        team = Team([pokemon1, pokemon2])
        result = team.switch_pokemon(1)

        assert result is False
        assert team.active_pokemon.name == "First"

    def test_switch_to_invalid_index_fails(self):
        """Test that switching to invalid index fails"""
        pokemon1 = create_test_pokemon(name="First")
        team = Team([pokemon1])

        assert team.switch_pokemon(-1) is False
        assert team.switch_pokemon(5) is False

    def test_switch_resets_battle_effects(self):
        """Test that switching resets volatile effects"""
        pokemon1 = create_test_pokemon(name="First")
        pokemon2 = create_test_pokemon(name="Second")
        team = Team([pokemon1, pokemon2])

        # Add some volatile effects to first Pokemon
        pokemon1.confusion_turns = 3
        pokemon1.is_seeded = True

        team.switch_pokemon(1)

        # Effects should be reset
        assert pokemon1.confusion_turns == 0
        assert pokemon1.is_seeded is False


class TestTeamStatus:
    """Test team status queries"""

    def test_get_alive_pokemon(self):
        """Test getting list of alive Pokemon"""
        pokemon1 = create_test_pokemon(name="Alive1", hp=100)
        pokemon2 = create_test_pokemon(name="Fainted", hp=100)
        pokemon2.current_hp = 0
        pokemon3 = create_test_pokemon(name="Alive2", hp=100)

        team = Team([pokemon1, pokemon2, pokemon3])
        alive = team.get_alive_pokemon()

        assert len(alive) == 2
        assert pokemon1 in alive
        assert pokemon3 in alive
        assert pokemon2 not in alive

    def test_get_available_switches(self):
        """Test getting available switch options"""
        pokemon1 = create_test_pokemon(name="Active", hp=100)
        pokemon2 = create_test_pokemon(name="Available", hp=100)
        pokemon3 = create_test_pokemon(name="Fainted", hp=100)
        pokemon3.current_hp = 0

        team = Team([pokemon1, pokemon2, pokemon3])
        available = team.get_available_switches()

        assert len(available) == 1
        assert available[0] == (1, pokemon2)

    def test_can_switch_true(self):
        """Test can_switch returns True when switches available"""
        pokemon1 = create_test_pokemon(name="Active")
        pokemon2 = create_test_pokemon(name="Available")
        team = Team([pokemon1, pokemon2])

        assert team.can_switch() is True

    def test_can_switch_false_single_pokemon(self):
        """Test can_switch returns False with single Pokemon"""
        pokemon = create_test_pokemon(name="Only")
        team = Team([pokemon])

        assert team.can_switch() is False

    def test_can_switch_false_all_fainted(self):
        """Test can_switch returns False when others fainted"""
        pokemon1 = create_test_pokemon(name="Active", hp=100)
        pokemon2 = create_test_pokemon(name="Fainted", hp=100)
        pokemon2.current_hp = 0

        team = Team([pokemon1, pokemon2])
        assert team.can_switch() is False

    def test_is_defeated_false(self):
        """Test is_defeated returns False when Pokemon alive"""
        pokemon1 = create_test_pokemon(name="Alive")
        team = Team([pokemon1])

        assert team.is_defeated() is False

    def test_is_defeated_true(self):
        """Test is_defeated returns True when all fainted"""
        pokemon1 = create_test_pokemon(name="Fainted1", hp=100)
        pokemon2 = create_test_pokemon(name="Fainted2", hp=100)
        pokemon1.current_hp = 0
        pokemon2.current_hp = 0

        team = Team([pokemon1, pokemon2])
        assert team.is_defeated() is True


class TestForceSwitch:
    """Test forced switch mechanics"""

    def test_force_switch_selects_first_available(self):
        """Test force switch picks first available Pokemon"""
        pokemon1 = create_test_pokemon(name="Fainted", hp=100)
        pokemon1.current_hp = 0
        pokemon2 = create_test_pokemon(name="Available1")
        pokemon3 = create_test_pokemon(name="Available2")

        team = Team([pokemon1, pokemon2, pokemon3])
        result = team.force_switch()

        assert result is True
        assert team.active_pokemon.name == "Available1"

    def test_force_switch_fails_when_all_fainted(self):
        """Test force switch returns False when all fainted"""
        pokemon1 = create_test_pokemon(name="Fainted1", hp=100)
        pokemon2 = create_test_pokemon(name="Fainted2", hp=100)
        pokemon1.current_hp = 0
        pokemon2.current_hp = 0

        team = Team([pokemon1, pokemon2])
        result = team.force_switch()

        assert result is False


class TestTeamStatusList:
    """Test team status reporting"""

    def test_get_pokemon_status_list(self):
        """Test getting status list for all Pokemon"""
        pokemon1 = create_test_pokemon(name="Active", hp=100)
        pokemon2 = create_test_pokemon(name="Hurt", hp=100)
        pokemon2.current_hp = 50
        pokemon2.status = Status.BURN

        team = Team([pokemon1, pokemon2])
        status_list = team.get_pokemon_status_list()

        assert len(status_list) == 2

        assert status_list[0]['name'] == "Active"
        assert status_list[0]['is_active'] is True
        assert status_list[0]['is_alive'] is True
        assert status_list[0]['hp'] == 100

        assert status_list[1]['name'] == "Hurt"
        assert status_list[1]['is_active'] is False
        assert status_list[1]['hp'] == 50
        assert status_list[1]['status'] == Status.BURN


class TestBattleFormat:
    """Test battle format enum"""

    def test_battle_format_single(self):
        """Test single battle format"""
        assert BattleFormat.SINGLE.team_size == 1
        assert "1v1" in BattleFormat.SINGLE.description

    def test_battle_format_triple(self):
        """Test triple battle format"""
        assert BattleFormat.TRIPLE.team_size == 3
        assert "3v3" in BattleFormat.TRIPLE.description

    def test_battle_format_full(self):
        """Test full battle format"""
        assert BattleFormat.FULL.team_size == 6
        assert "6v6" in BattleFormat.FULL.description


class TestTeamBattleIntegration:
    """Integration tests for team battles"""

    def test_create_team_battle(self):
        """Test creating a team battle"""
        from engine.team_battle import TeamBattle

        pokemon1 = create_test_pokemon(name="Player")
        pokemon2 = create_test_pokemon(name="Opponent")

        team1 = Team([pokemon1], "Player")
        team2 = Team([pokemon2], "CPU")

        battle = TeamBattle(team1, team2, BattleFormat.SINGLE)

        assert battle.team1 == team1
        assert battle.team2 == team2
        assert battle.turn_count == 0

    def test_battle_action_attack(self):
        """Test creating attack action"""
        from engine.team_battle import BattleAction

        move = create_test_move(name="Tackle")
        action = BattleAction.attack(move)

        assert action.action_type == "attack"
        assert action.move == move
        assert action.is_switch() is False

    def test_battle_action_switch(self):
        """Test creating switch action"""
        from engine.team_battle import BattleAction

        action = BattleAction.switch(2)

        assert action.action_type == "switch"
        assert action.switch_index == 2
        assert action.is_switch() is True

    def test_create_random_team(self):
        """Test random team creation"""
        from engine.team_battle import create_random_team

        team = create_random_team(3, "Random")

        assert team.size == 3
        assert team.name == "Random"
        for pokemon in team.pokemon:
            assert len(pokemon.moves) > 0

    def test_random_ai_action_returns_valid_action(self):
        """Test that AI action is valid"""
        from engine.team_battle import get_random_ai_action, BattleAction

        pokemon1 = create_test_pokemon(name="AI", hp=100)
        pokemon1.moves = [create_test_move(name="Tackle", pp=35)]
        team = Team([pokemon1], "AI")

        opponent = create_test_pokemon(name="Opponent")
        opp_team = Team([opponent], "Opp")

        action = get_random_ai_action(team, opp_team)

        assert isinstance(action, BattleAction)
        assert action.action_type in ("attack", "switch")
