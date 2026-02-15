"""Tests for the AI factory function."""

import pytest
from engine.ai import create_ai, AIDifficulty, BattleAI
from engine.ai.default_ai import DefaultAI
from engine.ai.easy_ai import EasyAI
from engine.ai.medium_ai import MediumAI
from engine.ai.competitive_ai import CompetitiveAI
from engine.ai.predictive_ai import PredictiveAI
from engine.ai.millennium_eye_ai import MillenniumEyeAI


class TestCreateAI:
    """Tests for create_ai factory function."""

    def test_default_creates_default_ai(self):
        ai = create_ai(AIDifficulty.DEFAULT)
        assert isinstance(ai, DefaultAI)
        assert isinstance(ai, BattleAI)

    def test_easy_creates_easy_ai(self):
        ai = create_ai(AIDifficulty.EASY)
        assert isinstance(ai, EasyAI)

    def test_medium_creates_medium_ai(self):
        ai = create_ai(AIDifficulty.MEDIUM)
        assert isinstance(ai, MediumAI)

    def test_competitive_creates_competitive_ai(self):
        ai = create_ai(AIDifficulty.COMPETITIVE)
        assert isinstance(ai, CompetitiveAI)

    def test_predictive_creates_predictive_ai(self):
        ai = create_ai(AIDifficulty.PREDICTIVE)
        assert isinstance(ai, PredictiveAI)

    def test_millennium_eye_creates_millennium_eye_ai(self):
        ai = create_ai(AIDifficulty.MILLENNIUM_EYE)
        assert isinstance(ai, MillenniumEyeAI)

    def test_all_difficulties_registered(self):
        """Every AIDifficulty enum value can be created."""
        for difficulty in AIDifficulty:
            ai = create_ai(difficulty)
            assert isinstance(ai, BattleAI)

    def test_passes_clauses(self):
        """Clauses are passed through to the AI instance."""
        sentinel = object()
        ai = create_ai(AIDifficulty.DEFAULT, clauses=sentinel)
        assert ai.clauses is sentinel

    def test_passes_profile(self):
        """Profile is passed through to the AI instance."""
        sentinel = object()
        ai = create_ai(AIDifficulty.EASY, profile=sentinel)
        assert ai.profile is sentinel

    def test_default_difficulty_kwarg(self):
        """Calling with no arguments produces DefaultAI."""
        ai = create_ai()
        assert isinstance(ai, DefaultAI)
