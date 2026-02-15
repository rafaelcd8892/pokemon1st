"""Tests for MillenniumEyeAI — cheat mode that sees opponent's action."""

import pytest
from models.enums import Type, MoveCategory, Status
from models.team import Team
from tests.conftest import create_test_pokemon, create_test_move
from engine.team_battle import BattleAction
from engine.ai.millennium_eye_ai import MillenniumEyeAI


class TestMillenniumEyeRevision:
    """The core mechanic: revise action after seeing opponent's choice."""

    def test_switches_to_resist_on_attack(self, seeded_rng):
        """When opponent attacks with Electric, switch to Ground type."""
        active = create_test_pokemon(
            name="Gyarados", types=[Type.WATER, Type.FLYING], hp=95, special=60,
            moves=[create_test_move("Surf", Type.WATER, MoveCategory.SPECIAL, 95)]
        )
        reserve = create_test_pokemon(
            name="Rhydon", types=[Type.GROUND, Type.ROCK], hp=105, attack=130, special=45,
            moves=[create_test_move("Earthquake", Type.GROUND, MoveCategory.PHYSICAL, 100)]
        )
        opponent = create_test_pokemon(
            name="Jolteon", types=[Type.ELECTRIC], special=110,
            moves=[create_test_move("Thunderbolt", Type.ELECTRIC, MoveCategory.SPECIAL, 95)]
        )

        team = Team([active, reserve], "Player")
        opponent_team = Team([opponent], "Opponent")

        ai = MillenniumEyeAI()

        # Phase 1: get tentative action
        tentative = ai.choose_action(team, opponent_team)

        # Phase 2: notify of opponent's attack
        opp_action = BattleAction.attack(opponent.moves[0])
        ai.notify_opponent_action(opp_action)

        # Phase 3: revise
        revised = ai.revise_action()
        assert revised is not None
        assert revised.action_type == "switch"
        assert revised.switch_index == 1  # Rhydon

    def test_uses_setup_on_opponent_switch(self, seeded_rng):
        """When opponent switches, use a stat-boost move if available."""
        from models.enums import StatType

        active = create_test_pokemon(
            name="Snorlax", types=[Type.NORMAL], hp=160, attack=110,
            moves=[
                create_test_move("Body Slam", Type.NORMAL, MoveCategory.PHYSICAL, 85),
                create_test_move("Amnesia", Type.PSYCHIC, MoveCategory.STATUS, 0, pp=20),
            ]
        )
        # Give Amnesia stat_changes + target_self
        active.moves[1].stat_changes = {StatType.SPECIAL: 2}
        active.moves[1].target_self = True

        opponent = create_test_pokemon(
            name="Opponent", types=[Type.WATER],
            moves=[create_test_move("Surf", Type.WATER, MoveCategory.SPECIAL, 95)]
        )

        team = Team([active], "Player")
        opponent_team = Team([opponent], "Opponent")

        ai = MillenniumEyeAI()

        tentative = ai.choose_action(team, opponent_team)

        # Opponent switches — free turn
        opp_action = BattleAction.switch(1)
        ai.notify_opponent_action(opp_action)

        revised = ai.revise_action()
        assert revised is not None
        assert revised.action_type == "attack"
        assert revised.move.name == "Amnesia"

    def test_no_revision_without_notification(self, seeded_rng):
        """Without notify_opponent_action, revise_action returns None."""
        active = create_test_pokemon(
            name="Mon", types=[Type.NORMAL],
            moves=[create_test_move("Tackle", Type.NORMAL, MoveCategory.PHYSICAL, 40)]
        )
        opponent = create_test_pokemon(
            name="Opponent", types=[Type.NORMAL],
            moves=[create_test_move("Tackle", Type.NORMAL, MoveCategory.PHYSICAL, 40)]
        )

        team = Team([active], "Player")
        opponent_team = Team([opponent], "Opponent")

        ai = MillenniumEyeAI()
        ai.choose_action(team, opponent_team)
        # No notify called
        assert ai.revise_action() is None

    def test_no_revision_when_attack_is_weak(self, seeded_rng):
        """Don't bother switching if opponent's attack is weak."""
        active = create_test_pokemon(
            name="Snorlax", types=[Type.NORMAL], hp=160, defense=65,
            moves=[create_test_move("Body Slam", Type.NORMAL, MoveCategory.PHYSICAL, 85)]
        )
        opponent = create_test_pokemon(
            name="Oddish", types=[Type.GRASS], special=75,
            moves=[create_test_move("Absorb", Type.GRASS, MoveCategory.SPECIAL, 20)]
        )

        team = Team([active], "Player")
        opponent_team = Team([opponent], "Opponent")

        ai = MillenniumEyeAI()
        ai.choose_action(team, opponent_team)

        opp_action = BattleAction.attack(opponent.moves[0])
        ai.notify_opponent_action(opp_action)

        # Absorb does minimal damage to Snorlax — no switch needed
        revised = ai.revise_action()
        assert revised is None


class TestMillenniumEyeTentativeAction:
    """The tentative action uses competitive-level evaluation."""

    def test_tentative_is_valid(self, seeded_rng):
        """Tentative action should be a valid attack or switch."""
        active = create_test_pokemon(
            name="Starmie", types=[Type.WATER, Type.PSYCHIC], special=100,
            moves=[
                create_test_move("Surf", Type.WATER, MoveCategory.SPECIAL, 95),
                create_test_move("Psychic", Type.PSYCHIC, MoveCategory.SPECIAL, 90),
            ]
        )
        opponent = create_test_pokemon(
            name="Arcanine", types=[Type.FIRE], special=80,
            moves=[create_test_move("Flamethrower", Type.FIRE, MoveCategory.SPECIAL, 95)]
        )

        team = Team([active], "Player")
        opponent_team = Team([opponent], "Opponent")

        ai = MillenniumEyeAI()
        action = ai.choose_action(team, opponent_team)
        assert action.action_type == "attack"
        # Should pick Surf (super-effective vs Fire)
        assert action.move.name == "Surf"


class TestMillenniumEyeForcedSwitch:
    """Forced switch behavior."""

    def test_forced_switch_available(self, seeded_rng):
        fainted = create_test_pokemon(name="Fainted")
        fainted.current_hp = 0
        reserve = create_test_pokemon(name="Reserve", types=[Type.WATER])
        team = Team([fainted, reserve], "Player")

        ai = MillenniumEyeAI()
        assert ai.choose_forced_switch(team) == 1

    def test_forced_switch_none(self, seeded_rng):
        fainted = create_test_pokemon(name="Fainted")
        fainted.current_hp = 0
        team = Team([fainted], "Player")

        ai = MillenniumEyeAI()
        assert ai.choose_forced_switch(team) is None
