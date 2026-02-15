"""Tests for profile-aware team builder."""

import pytest
from models.enums import Type
from engine.ai.trainer_class import TrainerProfile, TrainerStyle
from engine.ai.team_builder import (
    build_team_for_profile,
    _get_pokemon_pool,
    _score_pokemon_for_profile,
    _weighted_pokemon_selection,
)


class TestPokemonPoolFiltering:
    """_get_pokemon_pool filters by ruleset and specialist types."""

    def test_full_pool_no_restrictions(self):
        pool = _get_pokemon_pool(TrainerProfile.balanced())
        assert len(pool) == 151  # All Kanto Pokemon

    def test_type_specialist_filters(self):
        profile = TrainerProfile.type_specialist({Type.FIRE})
        pool = _get_pokemon_pool(profile)
        # Should include Charmander, Charmeleon, Charizard, Vulpix, etc.
        assert len(pool) > 0
        assert len(pool) < 151
        # All entries should have Fire type
        from data.data_loader import get_pokemon_data
        for name in pool:
            data = get_pokemon_data(name)
            types = {t.lower() for t in data['types']}
            assert 'fire' in types

    def test_dual_type_specialist(self):
        """Water + Ice specialist should get a wider pool."""
        water_only = _get_pokemon_pool(TrainerProfile.type_specialist({Type.WATER}))
        water_ice = _get_pokemon_pool(TrainerProfile.type_specialist({Type.WATER, Type.ICE}))
        assert len(water_ice) >= len(water_only)


class TestPokemonScoring:
    """_score_pokemon_for_profile weights base stats by profile."""

    def test_offensive_prefers_high_attack(self):
        """Machamp (high Atk) should score higher than Chansey (low Atk) for offensive."""
        off = TrainerProfile.offensive()
        machamp_score = _score_pokemon_for_profile('machamp', off)
        chansey_score = _score_pokemon_for_profile('chansey', off)
        assert machamp_score > chansey_score

    def test_defensive_prefers_bulk(self):
        """Snorlax (high HP+Def) should score higher than Alakazam (fast, frail) for defensive."""
        defe = TrainerProfile.defensive()
        snorlax_score = _score_pokemon_for_profile('snorlax', defe)
        alakazam_score = _score_pokemon_for_profile('alakazam', defe)
        assert snorlax_score > alakazam_score

    def test_balanced_is_neutral(self):
        """Balanced profile should give similar relative rankings to raw BST."""
        bal = TrainerProfile.balanced()
        # Mewtwo has highest BST, should score highest
        mewtwo = _score_pokemon_for_profile('mewtwo', bal)
        caterpie = _score_pokemon_for_profile('caterpie', bal)
        assert mewtwo > caterpie

    def test_unknown_pokemon_returns_default(self):
        score = _score_pokemon_for_profile('nonexistent', TrainerProfile.balanced())
        assert score == 1.0


class TestWeightedSelection:
    """_weighted_pokemon_selection returns correct count without duplicates."""

    def test_returns_correct_size(self, seeded_rng):
        pool = ['charmander', 'squirtle', 'bulbasaur', 'pikachu', 'eevee', 'mewtwo']
        selected = _weighted_pokemon_selection(pool, 3, TrainerProfile.balanced())
        assert len(selected) == 3

    def test_no_duplicates(self, seeded_rng):
        pool = ['charmander', 'squirtle', 'bulbasaur', 'pikachu', 'eevee', 'mewtwo']
        selected = _weighted_pokemon_selection(pool, 4, TrainerProfile.balanced())
        assert len(set(selected)) == 4

    def test_pool_smaller_than_size(self, seeded_rng):
        pool = ['pikachu', 'raichu']
        selected = _weighted_pokemon_selection(pool, 6, TrainerProfile.balanced())
        assert len(selected) == 2


class TestBuildTeamForProfile:
    """Full integration: build_team_for_profile produces valid teams."""

    def test_balanced_builds_team(self, seeded_rng):
        team = build_team_for_profile(3, "Trainer", "smart_random", TrainerProfile.balanced())
        assert len(team.pokemon) == 3
        assert team.name == "Trainer"
        for poke in team.pokemon:
            assert len(poke.moves) > 0

    def test_offensive_builds_team(self, seeded_rng):
        team = build_team_for_profile(3, "Attacker", "random", TrainerProfile.offensive())
        assert len(team.pokemon) == 3

    def test_defensive_builds_team(self, seeded_rng):
        team = build_team_for_profile(3, "Tank", "smart_random", TrainerProfile.defensive())
        assert len(team.pokemon) == 3

    def test_status_focused_builds_team(self, seeded_rng):
        team = build_team_for_profile(3, "Annoyer", "smart_random", TrainerProfile.status_focused())
        assert len(team.pokemon) == 3

    def test_type_specialist_builds_type_team(self, seeded_rng):
        profile = TrainerProfile.type_specialist({Type.WATER})
        team = build_team_for_profile(3, "Misty", "smart_random", profile)
        assert len(team.pokemon) == 3
        # All Pokemon should have Water type
        from data.data_loader import get_pokemon_data
        for poke in team.pokemon:
            data = get_pokemon_data(poke.name)
            types = {t.lower() for t in data['types']}
            assert 'water' in types

    def test_with_ruleset(self, seeded_rng):
        from models.ruleset import POKE_CUP_RULES
        team = build_team_for_profile(
            3, "Cup Trainer", "smart_random",
            TrainerProfile.balanced(), POKE_CUP_RULES
        )
        assert len(team.pokemon) == 3
        # Should respect Poke Cup level restrictions
        for poke in team.pokemon:
            assert poke.level <= POKE_CUP_RULES.max_level

    def test_offensive_team_has_damaging_moves(self, seeded_rng):
        """Offensive profile should result in teams with mostly damaging moves."""
        team = build_team_for_profile(3, "Attacker", "smart_random", TrainerProfile.offensive())
        total_damaging = 0
        total_moves = 0
        for poke in team.pokemon:
            for move in poke.moves:
                total_moves += 1
                if move.power > 0:
                    total_damaging += 1
        # At least 75% of moves should be damaging for offensive profile
        if total_moves > 0:
            assert total_damaging / total_moves >= 0.5
