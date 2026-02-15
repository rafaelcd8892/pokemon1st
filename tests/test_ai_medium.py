"""Tests for MediumAI — type-aware scoring and basic switching."""

import pytest
from models.enums import Type, MoveCategory, Status
from models.team import Team
from tests.conftest import create_test_pokemon, create_test_move
from engine.ai.medium_ai import MediumAI


class TestMediumAIMoveSelection:
    """Verify MediumAI picks super-effective / high-damage moves."""

    def test_picks_super_effective_over_neutral(self, seeded_rng):
        """MediumAI should prefer a super-effective move over a neutral one."""
        attacker = create_test_pokemon(
            name="Attacker", types=[Type.WATER], attack=100, special=100,
            moves=[
                create_test_move("Tackle", Type.NORMAL, MoveCategory.PHYSICAL, 40),
                create_test_move("Surf", Type.WATER, MoveCategory.SPECIAL, 95),
            ]
        )
        defender = create_test_pokemon(
            name="Fire Mon", types=[Type.FIRE], defense=80, special=80,
        )
        team = Team([attacker], "Player")
        opponent = Team([defender], "Opponent")

        ai = MediumAI()
        action = ai.choose_action(team, opponent)
        assert action.action_type == "attack"
        assert action.move.name == "Surf"

    def test_picks_high_power_when_same_type(self, seeded_rng):
        """Between two moves of similar effectiveness, prefer higher power."""
        attacker = create_test_pokemon(
            name="Attacker", types=[Type.NORMAL], attack=100,
            moves=[
                create_test_move("Tackle", Type.NORMAL, MoveCategory.PHYSICAL, 40),
                create_test_move("Body Slam", Type.NORMAL, MoveCategory.PHYSICAL, 85),
            ]
        )
        defender = create_test_pokemon(
            name="Defender", types=[Type.NORMAL], defense=80,
        )
        team = Team([attacker], "Player")
        opponent = Team([defender], "Opponent")

        ai = MediumAI()
        action = ai.choose_action(team, opponent)
        assert action.move.name == "Body Slam"

    def test_avoids_immune_move(self, seeded_rng):
        """MediumAI should not pick a move the target is immune to."""
        attacker = create_test_pokemon(
            name="Attacker", types=[Type.NORMAL], attack=100,
            moves=[
                create_test_move("Tackle", Type.NORMAL, MoveCategory.PHYSICAL, 40),
                create_test_move("Ember", Type.FIRE, MoveCategory.SPECIAL, 40),
            ]
        )
        defender = create_test_pokemon(
            name="Ghost", types=[Type.GHOST], defense=80,
        )
        team = Team([attacker], "Player")
        opponent = Team([defender], "Opponent")

        ai = MediumAI()
        action = ai.choose_action(team, opponent)
        assert action.move.name == "Ember"

    def test_considers_status_moves(self, seeded_rng):
        """MediumAI values status moves when opponent has no status."""
        attacker = create_test_pokemon(
            name="Attacker", types=[Type.ELECTRIC], special=100,
            moves=[
                # Low-power attack
                create_test_move("Scratch", Type.NORMAL, MoveCategory.PHYSICAL, 20, pp=35),
                # Status move with high value
                create_test_move("Thunder Wave", Type.ELECTRIC, MoveCategory.STATUS, 0,
                                 pp=20, status_effect=Status.PARALYSIS, status_chance=100),
            ]
        )
        defender = create_test_pokemon(
            name="Defender", types=[Type.NORMAL], defense=200, special=200,
        )
        team = Team([attacker], "Player")
        opponent = Team([defender], "Opponent")

        ai = MediumAI()
        action = ai.choose_action(team, opponent)
        # Thunder Wave should score higher than Scratch vs a very bulky target
        assert action.move.name == "Thunder Wave"


class TestMediumAISwitching:
    """Verify MediumAI switching heuristics."""

    def test_switches_on_bad_matchup(self, seeded_rng):
        """MediumAI switches when all moves are bad and a teammate has coverage."""
        # Normal type attacker vs Ghost — Tackle is immune
        attacker = create_test_pokemon(
            name="NormalMon", types=[Type.NORMAL], attack=100,
            moves=[
                create_test_move("Tackle", Type.NORMAL, MoveCategory.PHYSICAL, 40),
            ]
        )
        # Reserve with super-effective move
        reserve = create_test_pokemon(
            name="DarkHitter", types=[Type.GHOST], attack=100,
            moves=[
                create_test_move("Lick", Type.GHOST, MoveCategory.PHYSICAL, 20),
            ]
        )
        defender = create_test_pokemon(
            name="Ghost", types=[Type.GHOST], defense=80, hp=100,
        )

        team = Team([attacker, reserve], "Player")
        opponent = Team([defender], "Opponent")

        ai = MediumAI()
        action = ai.choose_action(team, opponent)
        assert action.action_type == "switch"
        assert action.switch_index == 1

    def test_no_switch_when_good_moves_available(self, seeded_rng):
        """MediumAI should not switch when it has good offensive options."""
        attacker = create_test_pokemon(
            name="WaterMon", types=[Type.WATER], special=100,
            moves=[
                create_test_move("Surf", Type.WATER, MoveCategory.SPECIAL, 95),
            ]
        )
        reserve = create_test_pokemon(name="Reserve", types=[Type.NORMAL])
        defender = create_test_pokemon(
            name="FireMon", types=[Type.FIRE], defense=80,
        )

        team = Team([attacker, reserve], "Player")
        opponent = Team([defender], "Opponent")

        ai = MediumAI()
        action = ai.choose_action(team, opponent)
        assert action.action_type == "attack"


class TestMediumAIForcedSwitch:
    """Verify MediumAI forced switch prefers healthy Pokemon."""

    def test_prefers_healthiest_pokemon(self, seeded_rng):
        """Forced switch should pick the Pokemon with the highest HP %."""
        fainted = create_test_pokemon(name="Fainted", types=[Type.NORMAL])
        fainted.current_hp = 0

        low_hp = create_test_pokemon(name="LowHP", types=[Type.WATER], hp=100)
        low_hp.current_hp = 20  # 20%

        high_hp = create_test_pokemon(name="HighHP", types=[Type.FIRE], hp=100)
        high_hp.current_hp = 90  # 90%

        team = Team([fainted, low_hp, high_hp], "Player")
        ai = MediumAI()
        idx = ai.choose_forced_switch(team)
        assert idx == 2  # HighHP

    def test_forced_switch_returns_none_when_all_fainted(self, seeded_rng):
        """Returns None when no reserves are available."""
        fainted = create_test_pokemon(name="Fainted", types=[Type.NORMAL])
        fainted.current_hp = 0

        team = Team([fainted], "Player")
        ai = MediumAI()
        assert ai.choose_forced_switch(team) is None
