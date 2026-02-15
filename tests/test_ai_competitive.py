"""Tests for CompetitiveAI — KO priority, smart switching, status timing."""

import pytest
from models.enums import Type, MoveCategory, Status
from models.team import Team
from tests.conftest import create_test_pokemon, create_test_move
from engine.ai.competitive_ai import CompetitiveAI


class TestCompetitiveKOPriority:
    """CompetitiveAI should strongly prefer moves that can KO."""

    def test_picks_ko_move_over_stronger_non_ko(self, seeded_rng):
        """When one move can KO and another can't, prefer the KO move."""
        attacker = create_test_pokemon(
            name="Attacker", types=[Type.WATER], attack=100, special=100,
            moves=[
                # Stronger but can't KO the 15 HP defender
                create_test_move("Surf", Type.WATER, MoveCategory.SPECIAL, 95),
                # Weaker but still enough to KO
                create_test_move("Water Gun", Type.WATER, MoveCategory.SPECIAL, 40),
            ]
        )
        # Defender has very low HP — both moves can KO
        defender = create_test_pokemon(
            name="LowHP", types=[Type.FIRE], hp=100, special=80,
        )
        defender.current_hp = 15  # Both Water moves KO this

        team = Team([attacker], "Player")
        opponent = Team([defender], "Opponent")

        ai = CompetitiveAI()
        action = ai.choose_action(team, opponent)
        assert action.action_type == "attack"
        # Both can KO, but Surf does more damage → higher total score
        assert action.move.name == "Surf"

    def test_ko_preferred_over_status(self, seeded_rng):
        """Prefer KO move over status when opponent can be finished."""
        attacker = create_test_pokemon(
            name="Attacker", types=[Type.ELECTRIC], special=100,
            moves=[
                create_test_move("Thunderbolt", Type.ELECTRIC, MoveCategory.SPECIAL, 95),
                create_test_move("Thunder Wave", Type.ELECTRIC, MoveCategory.STATUS, 0,
                                 status_effect=Status.PARALYSIS, status_chance=100),
            ]
        )
        defender = create_test_pokemon(
            name="LowHP", types=[Type.WATER], hp=100, special=60,
        )
        defender.current_hp = 10

        team = Team([attacker], "Player")
        opponent = Team([defender], "Opponent")

        ai = CompetitiveAI()
        action = ai.choose_action(team, opponent)
        assert action.move.name == "Thunderbolt"


class TestCompetitiveSmartSwitching:
    """CompetitiveAI switching via should_switch()."""

    def test_switches_on_high_threat(self, seeded_rng):
        """Switch when heavily threatened and better matchup exists."""
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

        ai = CompetitiveAI()
        action = ai.choose_action(team, opponent_team)
        # Should switch to Rhydon (immune to Electric)
        assert action.action_type == "switch"
        assert action.switch_index == 1

    def test_no_switch_when_can_ko(self, seeded_rng):
        """Don't switch if we can KO the opponent this turn."""
        active = create_test_pokemon(
            name="Gyarados", types=[Type.WATER, Type.FLYING], hp=95, special=100,
            moves=[create_test_move("Surf", Type.WATER, MoveCategory.SPECIAL, 95)]
        )
        reserve = create_test_pokemon(
            name="Rhydon", types=[Type.GROUND, Type.ROCK], hp=105,
            moves=[create_test_move("Earthquake", Type.GROUND, MoveCategory.PHYSICAL, 100)]
        )
        opponent = create_test_pokemon(
            name="Jolteon", types=[Type.ELECTRIC], hp=65, special=110,
            moves=[create_test_move("Thunderbolt", Type.ELECTRIC, MoveCategory.SPECIAL, 95)]
        )
        opponent.current_hp = 10  # Can be KO'd by Surf

        team = Team([active, reserve], "Player")
        opponent_team = Team([opponent], "Opponent")

        ai = CompetitiveAI()
        action = ai.choose_action(team, opponent_team)
        # KO bonus should outweigh switching
        assert action.action_type == "attack"


class TestCompetitiveStatusTiming:
    """CompetitiveAI should value status differently based on game phase."""

    def test_values_status_early(self, seeded_rng):
        """Status moves valued when opponent is healthy."""
        attacker = create_test_pokemon(
            name="Attacker", types=[Type.ELECTRIC], special=60,
            moves=[
                create_test_move("Scratch", Type.NORMAL, MoveCategory.PHYSICAL, 20),
                create_test_move("Thunder Wave", Type.ELECTRIC, MoveCategory.STATUS, 0,
                                 status_effect=Status.PARALYSIS, status_chance=100),
            ]
        )
        defender = create_test_pokemon(
            name="Healthy", types=[Type.NORMAL], hp=200, defense=200, special=200,
        )
        team = Team([attacker], "Player")
        opponent = Team([defender], "Opponent")

        ai = CompetitiveAI()
        action = ai.choose_action(team, opponent)
        # Against a very bulky opponent at full HP, status should be preferred
        assert action.move.name == "Thunder Wave"

    def test_devalues_status_when_already_statused(self, seeded_rng):
        """Status moves devalued when opponent already has a status."""
        attacker = create_test_pokemon(
            name="Attacker", types=[Type.ELECTRIC], special=100,
            moves=[
                create_test_move("Thunderbolt", Type.ELECTRIC, MoveCategory.SPECIAL, 95),
                create_test_move("Thunder Wave", Type.ELECTRIC, MoveCategory.STATUS, 0,
                                 status_effect=Status.PARALYSIS, status_chance=100),
            ]
        )
        defender = create_test_pokemon(
            name="AlreadyBurned", types=[Type.NORMAL], hp=100, special=60,
        )
        defender.status = Status.BURN

        team = Team([attacker], "Player")
        opponent = Team([defender], "Opponent")

        ai = CompetitiveAI()
        action = ai.choose_action(team, opponent)
        assert action.move.name == "Thunderbolt"


class TestCompetitiveSetupAwareness:
    """CompetitiveAI stat boost timing."""

    def test_boosts_when_safe(self, seeded_rng):
        """Uses stat boost when opponent can't threaten a KO."""
        attacker = create_test_pokemon(
            name="Attacker", types=[Type.NORMAL], hp=200, attack=100, defense=100,
            moves=[
                create_test_move("Scratch", Type.NORMAL, MoveCategory.PHYSICAL, 20),
                create_test_move("Swords Dance", Type.NORMAL, MoveCategory.STATUS, 0,
                                 pp=30),
            ]
        )
        # Give Swords Dance stat_changes
        attacker.moves[1].stat_changes = {__import__('models.enums', fromlist=['StatType']).StatType.ATTACK: 2}
        attacker.moves[1].target_self = True

        defender = create_test_pokemon(
            name="Weak", types=[Type.NORMAL], hp=50, attack=20, special=20,
            moves=[create_test_move("Splash", Type.NORMAL, MoveCategory.STATUS, 0)]
        )
        team = Team([attacker], "Player")
        opponent = Team([defender], "Opponent")

        ai = CompetitiveAI()
        action = ai.choose_action(team, opponent)
        assert action.move.name == "Swords Dance"


class TestCompetitiveForcedSwitch:
    """CompetitiveAI forced switch behavior."""

    def test_forced_switch_picks_available(self, seeded_rng):
        """Forced switch returns a valid index."""
        fainted = create_test_pokemon(name="Fainted", types=[Type.NORMAL])
        fainted.current_hp = 0
        reserve = create_test_pokemon(name="Reserve", types=[Type.WATER])

        team = Team([fainted, reserve], "Player")
        ai = CompetitiveAI()
        idx = ai.choose_forced_switch(team)
        assert idx == 1

    def test_forced_switch_none_when_all_fainted(self, seeded_rng):
        """Returns None when no reserves available."""
        fainted = create_test_pokemon(name="Fainted")
        fainted.current_hp = 0
        team = Team([fainted], "Player")
        ai = CompetitiveAI()
        assert ai.choose_forced_switch(team) is None
