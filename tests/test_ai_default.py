"""Tests for DefaultAI — must produce identical actions to get_random_ai_action.

This is the backward-compatibility test: given the same RNG seed,
DefaultAI.choose_action must return the exact same action as the
original get_random_ai_action function.
"""

import pytest
from models.enums import Type, MoveCategory
from models.team import Team
from tests.conftest import create_test_pokemon, create_test_move
from engine.rng import StandardRNG, set_rng, reset_rng
from engine.team_battle import get_random_ai_action, get_random_forced_switch
from engine.ai.default_ai import DefaultAI


@pytest.fixture(autouse=True)
def cleanup_rng():
    yield
    reset_rng()


def _make_team(active_hp_pct=1.0, team_size=3):
    """Create a team with configurable HP for switching tests."""
    moves = [
        create_test_move("Tackle", Type.NORMAL, MoveCategory.PHYSICAL, 40),
        create_test_move("Ember", Type.FIRE, MoveCategory.SPECIAL, 40),
    ]
    pokemon_list = []
    for i in range(team_size):
        poke = create_test_pokemon(
            name=f"Mon{i}", types=[Type.NORMAL], hp=100,
            attack=80, defense=80, special=80, speed=80,
            moves=[
                create_test_move(f"Move{i}A", Type.NORMAL, MoveCategory.PHYSICAL, 50),
                create_test_move(f"Move{i}B", Type.FIRE, MoveCategory.SPECIAL, 50),
            ]
        )
        if i == 0:
            poke.current_hp = int(poke.max_hp * active_hp_pct)
        pokemon_list.append(poke)
    return Team(pokemon_list, "TestTrainer")


class TestDefaultAIBackwardCompat:
    """Verify DefaultAI produces identical results to get_random_ai_action."""

    def test_same_action_full_hp(self):
        """At full HP, both should pick the same random move."""
        for seed in [1, 42, 123, 9999]:
            team = _make_team(active_hp_pct=1.0)
            opponent = _make_team()

            # Original function
            set_rng(StandardRNG(seed))
            original_action = get_random_ai_action(team, opponent)

            # Reset team state for DefaultAI
            team = _make_team(active_hp_pct=1.0)
            opponent = _make_team()

            set_rng(StandardRNG(seed))
            ai = DefaultAI()
            ai_action = ai.choose_action(team, opponent)

            assert original_action.action_type == ai_action.action_type, (
                f"Seed {seed}: action types differ"
            )
            if original_action.action_type == "attack":
                assert original_action.move.name == ai_action.move.name, (
                    f"Seed {seed}: move names differ"
                )
            else:
                assert original_action.switch_index == ai_action.switch_index, (
                    f"Seed {seed}: switch indices differ"
                )

    def test_same_action_low_hp(self):
        """At low HP, both should make the same switch/attack decision."""
        for seed in [1, 42, 123, 9999]:
            team = _make_team(active_hp_pct=0.2)  # 20% HP — triggers switch logic
            opponent = _make_team()

            set_rng(StandardRNG(seed))
            original_action = get_random_ai_action(team, opponent)

            team = _make_team(active_hp_pct=0.2)
            opponent = _make_team()

            set_rng(StandardRNG(seed))
            ai = DefaultAI()
            ai_action = ai.choose_action(team, opponent)

            assert original_action.action_type == ai_action.action_type, (
                f"Seed {seed}: action types differ at low HP"
            )
            if original_action.action_type == "switch":
                assert original_action.switch_index == ai_action.switch_index

    def test_forced_switch_same(self):
        """Forced switch should pick the same target."""
        for seed in [1, 42, 123]:
            team = _make_team(team_size=3)
            # Faint active Pokemon
            team.active_pokemon.current_hp = 0

            set_rng(StandardRNG(seed))
            original_idx = get_random_forced_switch(team)

            # Re-faint active
            team2 = _make_team(team_size=3)
            team2.active_pokemon.current_hp = 0

            set_rng(StandardRNG(seed))
            ai = DefaultAI()
            ai_idx = ai.choose_forced_switch(team2)

            assert original_idx == ai_idx, f"Seed {seed}: forced switch differs"


class TestDefaultAIBehavior:
    """Basic behavioral tests for DefaultAI."""

    def test_returns_attack_with_pp(self, seeded_rng):
        """With PP available, DefaultAI returns an attack action."""
        team = _make_team(active_hp_pct=1.0)
        opponent = _make_team()
        ai = DefaultAI()
        action = ai.choose_action(team, opponent)
        assert action.action_type == "attack"
        assert action.move is not None

    def test_struggle_when_no_pp(self, seeded_rng):
        """When all moves have 0 PP, falls back to first move (Struggle)."""
        team = _make_team(active_hp_pct=1.0)
        for m in team.active_pokemon.moves:
            m.pp = 0
        opponent = _make_team()
        ai = DefaultAI()
        action = ai.choose_action(team, opponent)
        assert action.action_type == "attack"
        assert action.move == team.active_pokemon.moves[0]

    def test_forced_switch_returns_none_when_no_options(self, seeded_rng):
        """Returns None when all other Pokemon are fainted."""
        team = _make_team(team_size=1)
        team.active_pokemon.current_hp = 0
        ai = DefaultAI()
        assert ai.choose_forced_switch(team) is None
