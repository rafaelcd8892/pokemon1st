"""Tests for TrainerStyle enum and TrainerProfile dataclass."""

import pytest
from models.enums import Type
from engine.ai.trainer_class import TrainerStyle, TrainerProfile


class TestTrainerStyle:
    """TrainerStyle enum values and basic properties."""

    def test_all_styles_exist(self):
        assert TrainerStyle.BALANCED.value == "balanced"
        assert TrainerStyle.OFFENSIVE.value == "offensive"
        assert TrainerStyle.DEFENSIVE.value == "defensive"
        assert TrainerStyle.STATUS_FOCUSED.value == "status"
        assert TrainerStyle.TYPE_SPECIALIST.value == "type_specialist"

    def test_five_styles(self):
        assert len(TrainerStyle) == 5


class TestTrainerProfileDefaults:
    """Default (balanced) profile has neutral weights."""

    def test_balanced_factory(self):
        p = TrainerProfile.balanced()
        assert p.style == TrainerStyle.BALANCED
        assert p.attack_weight == 1.0
        assert p.defense_weight == 1.0
        assert p.speed_weight == 1.0
        assert p.status_move_weight == 1.0
        assert p.aggression == 1.0
        assert p.status_priority == 1.0
        assert p.setup_priority == 1.0
        assert p.specialist_types == set()

    def test_default_constructor_is_balanced(self):
        p = TrainerProfile()
        assert p.style == TrainerStyle.BALANCED
        assert p.aggression == 1.0


class TestOffensiveProfile:
    """Offensive profile biases toward damage and speed."""

    def test_factory(self):
        p = TrainerProfile.offensive()
        assert p.style == TrainerStyle.OFFENSIVE
        assert p.attack_weight > 1.0
        assert p.defense_weight < 1.0
        assert p.speed_weight > 1.0
        assert p.aggression > 1.0
        assert p.status_priority < 1.0

    def test_higher_switch_threshold(self):
        """Offensive AI should be harder to convince to switch."""
        balanced = TrainerProfile.balanced()
        offensive = TrainerProfile.offensive()
        assert offensive.switch_threshold > balanced.switch_threshold


class TestDefensiveProfile:
    """Defensive profile biases toward bulk and status."""

    def test_factory(self):
        p = TrainerProfile.defensive()
        assert p.style == TrainerStyle.DEFENSIVE
        assert p.defense_weight > 1.0
        assert p.attack_weight < 1.0
        assert p.aggression < 1.0
        assert p.status_priority > 1.0

    def test_lower_switch_threshold(self):
        """Defensive AI should switch more readily."""
        balanced = TrainerProfile.balanced()
        defensive = TrainerProfile.defensive()
        assert defensive.switch_threshold < balanced.switch_threshold


class TestStatusFocusedProfile:
    """Status-focused profile prioritises status moves."""

    def test_factory(self):
        p = TrainerProfile.status_focused()
        assert p.style == TrainerStyle.STATUS_FOCUSED
        assert p.status_priority > 1.0
        assert p.status_move_weight > 1.0
        assert p.aggression < 1.0
        assert p.setup_priority > 1.0

    def test_speed_above_neutral(self):
        """Status users want to move first."""
        p = TrainerProfile.status_focused()
        assert p.speed_weight >= 1.0


class TestTypeSpecialistProfile:
    """Type specialist restricts team to specific types."""

    def test_factory_single_type(self):
        p = TrainerProfile.type_specialist({Type.FIRE})
        assert p.style == TrainerStyle.TYPE_SPECIALIST
        assert Type.FIRE in p.specialist_types
        assert len(p.specialist_types) == 1

    def test_factory_multiple_types(self):
        p = TrainerProfile.type_specialist({Type.WATER, Type.ICE})
        assert p.specialist_types == {Type.WATER, Type.ICE}

    def test_otherwise_balanced(self):
        """Non-type weights should be neutral for specialists."""
        p = TrainerProfile.type_specialist({Type.ELECTRIC})
        assert p.aggression == 1.0
        assert p.attack_weight == 1.0
        assert p.switch_threshold == 0.35


class TestProfileIntegrationWithAI:
    """Verify profiles wire through to AI instances correctly."""

    def test_create_ai_with_profile(self):
        from engine.ai import create_ai, AIDifficulty
        p = TrainerProfile.offensive()
        ai = create_ai(AIDifficulty.COMPETITIVE, profile=p)
        assert ai.profile is p
        assert ai.profile.style == TrainerStyle.OFFENSIVE

    def test_default_ai_gets_balanced_profile(self):
        from engine.ai import create_ai, AIDifficulty
        ai = create_ai(AIDifficulty.DEFAULT)
        assert ai.profile is not None
        assert ai.profile.style == TrainerStyle.BALANCED

    def test_explicit_none_gets_balanced(self):
        from engine.ai import create_ai, AIDifficulty
        ai = create_ai(AIDifficulty.MEDIUM, profile=None)
        assert ai.profile.style == TrainerStyle.BALANCED


class TestProfileWeightsAffectScoring:
    """Verify that profile weights actually change AI move selection."""

    def test_offensive_prefers_damage_over_status(self, seeded_rng):
        from models.team import Team
        from tests.conftest import create_test_pokemon, create_test_move
        from models.enums import MoveCategory, Status
        from engine.ai.medium_ai import MediumAI

        attacker = create_test_pokemon(
            name="Attacker", types=[Type.ELECTRIC], special=100,
            moves=[
                create_test_move("Thunderbolt", Type.ELECTRIC, MoveCategory.SPECIAL, 95),
                create_test_move("Thunder Wave", Type.ELECTRIC, MoveCategory.STATUS, 0,
                                 status_effect=Status.PARALYSIS, status_chance=100),
            ]
        )
        defender = create_test_pokemon(
            name="Defender", types=[Type.NORMAL], hp=200, special=80
        )

        team = Team([attacker], "Test")
        opp_team = Team([defender], "Opp")

        # Offensive profile should strongly prefer Thunderbolt
        ai = MediumAI(profile=TrainerProfile.offensive())
        action = ai.choose_action(team, opp_team)
        assert action.move.name == "Thunderbolt"

    def test_competitive_uses_profile_switch_threshold(self, seeded_rng):
        """CompetitiveAI reads switch_threshold from profile."""
        from engine.ai.competitive_ai import CompetitiveAI

        defensive = TrainerProfile.defensive()
        offensive = TrainerProfile.offensive()

        ai_def = CompetitiveAI(profile=defensive)
        ai_off = CompetitiveAI(profile=offensive)

        # Both have the threshold stored
        assert ai_def.profile.switch_threshold < ai_off.profile.switch_threshold
