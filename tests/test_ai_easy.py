"""Tests for EasyAI — avoids obviously bad moves."""

import pytest
from models.enums import Type, MoveCategory, Status
from models.team import Team
from tests.conftest import create_test_pokemon, create_test_move
from engine.ai.easy_ai import EasyAI


class TestEasyAIFiltering:
    """Verify EasyAI filters out bad move choices."""

    def test_never_picks_immune_move(self, seeded_rng):
        """EasyAI should never pick a move the target is immune to."""
        attacker = create_test_pokemon(
            name="Attacker", types=[Type.NORMAL], attack=100,
            moves=[
                create_test_move("Tackle", Type.NORMAL, MoveCategory.PHYSICAL, 40),
                create_test_move("Ember", Type.FIRE, MoveCategory.SPECIAL, 40),
            ]
        )
        defender = create_test_pokemon(
            name="Ghost", types=[Type.GHOST], defense=100,
        )
        team = Team([attacker], "Player")
        opponent = Team([defender], "Opponent")

        ai = EasyAI()
        # Run multiple times to verify consistency
        for _ in range(20):
            action = ai.choose_action(team, opponent)
            assert action.action_type == "attack"
            # Normal moves are immune vs Ghost, so should always pick Ember
            assert action.move.name == "Ember"

    def test_avoids_self_destruct_with_reserves(self, seeded_rng):
        """EasyAI should not use Self-Destruct when team has healthy reserves."""
        attacker = create_test_pokemon(
            name="Attacker", types=[Type.NORMAL], attack=100,
            moves=[
                create_test_move("Explosion", Type.NORMAL, MoveCategory.PHYSICAL, 250),
                create_test_move("Tackle", Type.NORMAL, MoveCategory.PHYSICAL, 40),
            ]
        )
        reserve = create_test_pokemon(name="Reserve", types=[Type.NORMAL])
        defender = create_test_pokemon(name="Defender", types=[Type.NORMAL])

        team = Team([attacker, reserve], "Player")
        opponent = Team([defender], "Opponent")

        ai = EasyAI()
        for _ in range(20):
            action = ai.choose_action(team, opponent)
            assert action.move.name == "Tackle"

    def test_allows_self_destruct_when_last_pokemon(self, seeded_rng):
        """EasyAI allows Self-Destruct when it's the last Pokemon (no reserves)."""
        attacker = create_test_pokemon(
            name="Attacker", types=[Type.NORMAL], attack=100,
            moves=[
                create_test_move("Explosion", Type.NORMAL, MoveCategory.PHYSICAL, 250),
                create_test_move("Tackle", Type.NORMAL, MoveCategory.PHYSICAL, 40),
            ]
        )
        defender = create_test_pokemon(name="Defender", types=[Type.NORMAL])

        team = Team([attacker], "Player")
        opponent = Team([defender], "Opponent")

        ai = EasyAI()
        # Should be able to pick either move now
        moves_chosen = set()
        for _ in range(50):
            action = ai.choose_action(team, opponent)
            moves_chosen.add(action.move.name)
        # Explosion should be in the pool
        assert "Explosion" in moves_chosen

    def test_falls_back_when_all_moves_bad(self, seeded_rng):
        """When all moves are filtered out, falls back to full legal list."""
        attacker = create_test_pokemon(
            name="Attacker", types=[Type.NORMAL], attack=100,
            moves=[
                create_test_move("Tackle", Type.NORMAL, MoveCategory.PHYSICAL, 40),
            ]
        )
        defender = create_test_pokemon(name="Ghost", types=[Type.GHOST])

        team = Team([attacker], "Player")
        opponent = Team([defender], "Opponent")

        ai = EasyAI()
        action = ai.choose_action(team, opponent)
        # Should still return an action even though Tackle is immune
        assert action.action_type == "attack"


class TestEasyAIForcedSwitch:
    """Verify EasyAI forced switch behavior."""

    def test_forced_switch_picks_available(self, seeded_rng):
        """Forced switch picks from available reserves."""
        fainted = create_test_pokemon(name="Fainted", types=[Type.NORMAL])
        fainted.current_hp = 0
        reserve = create_test_pokemon(name="Reserve", types=[Type.WATER])

        team = Team([fainted, reserve], "Player")
        ai = EasyAI()
        idx = ai.choose_forced_switch(team)
        assert idx == 1

    def test_forced_switch_none_when_all_fainted(self, seeded_rng):
        """Returns None when no Pokemon are available."""
        fainted = create_test_pokemon(name="Fainted", types=[Type.NORMAL])
        fainted.current_hp = 0

        team = Team([fainted], "Player")
        ai = EasyAI()
        assert ai.choose_forced_switch(team) is None
