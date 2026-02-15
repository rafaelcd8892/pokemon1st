"""Tests for PredictiveAI — predicts and counters opponent's likely action."""

import pytest
from models.enums import Type, MoveCategory, Status
from models.team import Team
from tests.conftest import create_test_pokemon, create_test_move
from engine.ai.predictive_ai import PredictiveAI


class TestPredictiveSwitching:
    """PredictiveAI should preemptively switch based on predicted threat."""

    def test_switches_to_resist_predicted_move(self, seeded_rng):
        """Switches to a resist when opponent's best move is very threatening."""
        # Active is Water/Flying — weak to Electric
        active = create_test_pokemon(
            name="Gyarados", types=[Type.WATER, Type.FLYING], hp=95, special=60,
            moves=[create_test_move("Surf", Type.WATER, MoveCategory.SPECIAL, 95)]
        )
        # Reserve is Ground — immune to Electric
        reserve = create_test_pokemon(
            name="Rhydon", types=[Type.GROUND, Type.ROCK], hp=105, attack=130, special=45,
            moves=[create_test_move("Earthquake", Type.GROUND, MoveCategory.PHYSICAL, 100)]
        )
        # Opponent has strong Electric move
        opponent = create_test_pokemon(
            name="Jolteon", types=[Type.ELECTRIC], special=110,
            moves=[create_test_move("Thunderbolt", Type.ELECTRIC, MoveCategory.SPECIAL, 95)]
        )

        team = Team([active, reserve], "Player")
        opponent_team = Team([opponent], "Opponent")

        ai = PredictiveAI()
        action = ai.choose_action(team, opponent_team)
        # Should preemptively switch to Rhydon
        assert action.action_type == "switch"
        assert action.switch_index == 1

    def test_attacks_when_not_threatened(self, seeded_rng):
        """Stays in and attacks when opponent's predicted move is weak."""
        active = create_test_pokemon(
            name="Snorlax", types=[Type.NORMAL], hp=160, defense=65, special=65,
            attack=110,
            moves=[create_test_move("Body Slam", Type.NORMAL, MoveCategory.PHYSICAL, 85)]
        )
        reserve = create_test_pokemon(
            name="Reserve", types=[Type.WATER], hp=80,
            moves=[create_test_move("Surf", Type.WATER, MoveCategory.SPECIAL, 95)]
        )
        opponent = create_test_pokemon(
            name="Oddish", types=[Type.GRASS, Type.POISON], special=75,
            moves=[create_test_move("Absorb", Type.GRASS, MoveCategory.SPECIAL, 20)]
        )

        team = Team([active, reserve], "Player")
        opponent_team = Team([opponent], "Opponent")

        ai = PredictiveAI()
        action = ai.choose_action(team, opponent_team)
        assert action.action_type == "attack"


class TestPredictiveKOPriority:
    """PredictiveAI should still prioritise KOs like CompetitiveAI."""

    def test_finishes_off_low_hp(self, seeded_rng):
        """Attacks to KO rather than switching even if threatened."""
        active = create_test_pokemon(
            name="Starmie", types=[Type.WATER, Type.PSYCHIC], special=100,
            moves=[create_test_move("Surf", Type.WATER, MoveCategory.SPECIAL, 95)]
        )
        reserve = create_test_pokemon(
            name="Reserve", types=[Type.GROUND], hp=100,
            moves=[create_test_move("Earthquake", Type.GROUND, MoveCategory.PHYSICAL, 100)]
        )
        opponent = create_test_pokemon(
            name="Jolteon", types=[Type.ELECTRIC], hp=65, special=110,
            moves=[create_test_move("Thunderbolt", Type.ELECTRIC, MoveCategory.SPECIAL, 95)]
        )
        opponent.current_hp = 5  # Can be KO'd

        team = Team([active, reserve], "Player")
        opponent_team = Team([opponent], "Opponent")

        ai = PredictiveAI()
        action = ai.choose_action(team, opponent_team)
        # KO bonus should override switching desire
        assert action.action_type == "attack"


class TestPredictiveUnderPressure:
    """PredictiveAI adjustments when expecting heavy damage."""

    def test_devalues_status_under_threat(self, seeded_rng):
        """Prefers damage over status when expecting to take heavy hit."""
        attacker = create_test_pokemon(
            name="Attacker", types=[Type.ELECTRIC], hp=60, special=100,
            moves=[
                create_test_move("Thunderbolt", Type.ELECTRIC, MoveCategory.SPECIAL, 95),
                create_test_move("Thunder Wave", Type.ELECTRIC, MoveCategory.STATUS, 0,
                                 status_effect=Status.PARALYSIS, status_chance=100),
            ]
        )
        # Opponent threatens heavy damage
        opponent = create_test_pokemon(
            name="Machamp", types=[Type.FIGHTING], attack=130,
            moves=[create_test_move("Submission", Type.FIGHTING, MoveCategory.PHYSICAL, 80)]
        )

        team = Team([attacker], "Player")
        opponent_team = Team([opponent], "Opponent")

        ai = PredictiveAI()
        action = ai.choose_action(team, opponent_team)
        # Under heavy threat, should prefer immediate damage
        assert action.move.name == "Thunderbolt"


class TestPredictiveForcedSwitch:
    """PredictiveAI forced switch behavior."""

    def test_forced_switch_picks_available(self, seeded_rng):
        fainted = create_test_pokemon(name="Fainted")
        fainted.current_hp = 0
        reserve = create_test_pokemon(name="Reserve", types=[Type.WATER])
        team = Team([fainted, reserve], "Player")

        ai = PredictiveAI()
        assert ai.choose_forced_switch(team) == 1

    def test_forced_switch_none_when_all_fainted(self, seeded_rng):
        fainted = create_test_pokemon(name="Fainted")
        fainted.current_hp = 0
        team = Team([fainted], "Player")

        ai = PredictiveAI()
        assert ai.choose_forced_switch(team) is None
