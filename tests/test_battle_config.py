"""Tests for battle configuration and settings"""

import pytest
from settings.battle_config import (
    AIType, MovesetMode, BattleMode, BattleSettings
)


class TestBattleMode:
    """Tests for BattleMode enum"""

    def test_battle_modes_have_descriptions(self):
        """Test that all battle modes have descriptions"""
        for mode in BattleMode:
            assert hasattr(mode, 'description')
            assert len(mode.description) > 0

    def test_player_vs_ai_mode(self):
        """Test Player vs AI mode"""
        assert BattleMode.PLAYER_VS_AI.value == "pvai"

    def test_autobattle_mode(self):
        """Test Autobattle mode"""
        assert BattleMode.AUTOBATTLE.value == "auto"

    def test_watch_mode(self):
        """Test Watch mode"""
        assert BattleMode.WATCH.value == "watch"


class TestMovesetMode:
    """Tests for MovesetMode enum"""

    def test_moveset_modes_have_descriptions(self):
        """Test that all moveset modes have descriptions"""
        for mode in MovesetMode:
            assert hasattr(mode, 'description')
            assert len(mode.description) > 0

    def test_manual_mode(self):
        """Test Manual mode"""
        assert MovesetMode.MANUAL.value == "manual"

    def test_random_mode(self):
        """Test Random mode"""
        assert MovesetMode.RANDOM.value == "random"

    def test_preset_mode(self):
        """Test Preset mode"""
        assert MovesetMode.PRESET.value == "preset"

    def test_smart_random_mode(self):
        """Test Smart Random mode"""
        assert MovesetMode.SMART_RANDOM.value == "smart_random"


class TestBattleSettings:
    """Tests for BattleSettings dataclass"""

    def test_default_settings(self):
        """Test default settings creation"""
        settings = BattleSettings.default()
        assert settings.battle_mode == BattleMode.PLAYER_VS_AI
        assert settings.moveset_mode == MovesetMode.MANUAL
        assert settings.action_delay == 3.0

    def test_autobattle_settings(self):
        """Test autobattle settings creation"""
        settings = BattleSettings.for_autobattle()
        assert settings.battle_mode == BattleMode.AUTOBATTLE
        assert settings.moveset_mode == MovesetMode.RANDOM
        assert settings.action_delay == 3.0

    def test_watch_mode_settings(self):
        """Test watch mode settings creation"""
        settings = BattleSettings.for_watch_mode()
        assert settings.battle_mode == BattleMode.WATCH
        assert settings.moveset_mode == MovesetMode.SMART_RANDOM
        assert settings.action_delay == 4.0  # Longer delay for watch mode

    def test_is_autobattle_true(self):
        """Test is_autobattle returns True for autobattle modes"""
        autobattle = BattleSettings.for_autobattle()
        watch = BattleSettings.for_watch_mode()

        assert autobattle.is_autobattle() is True
        assert watch.is_autobattle() is True

    def test_is_autobattle_false(self):
        """Test is_autobattle returns False for player mode"""
        player = BattleSettings.default()
        assert player.is_autobattle() is False

    def test_custom_settings(self):
        """Test custom settings creation"""
        settings = BattleSettings(
            battle_mode=BattleMode.PLAYER_VS_AI,
            moveset_mode=MovesetMode.PRESET,
            action_delay=5.0
        )
        assert settings.battle_mode == BattleMode.PLAYER_VS_AI
        assert settings.moveset_mode == MovesetMode.PRESET
        assert settings.action_delay == 5.0


class TestAIType:
    """Tests for AIType enum"""

    def test_random_ai(self):
        """Test Random AI type exists"""
        assert AIType.RANDOM.value == "random"
