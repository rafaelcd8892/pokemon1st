"""Tests for generation-specific mechanics resolution."""

import pytest
import config
from models.enums import Type, MoveCategory
from models.move import Move
from engine.gen_mechanics import (
    get_effective_category,
    is_physical,
    PHYSICAL_TYPES,
)


def make_move(name: str = "TestMove", move_type: Type = Type.NORMAL,
              category: MoveCategory = MoveCategory.PHYSICAL,
              power: int = 50) -> Move:
    """Create a minimal test move."""
    return Move(name=name, type=move_type, category=category,
                power=power, accuracy=100, pp=10, max_pp=10)


class TestGen1PhysicalSpecialSplit:
    """In Gen 1, physical/special is determined by TYPE, not per-move."""

    @pytest.fixture(autouse=True)
    def set_gen1(self):
        """Ensure GENERATION is 1 for these tests."""
        original = config.GENERATION
        config.GENERATION = 1
        yield
        config.GENERATION = original

    def test_normal_is_physical(self):
        move = make_move(move_type=Type.NORMAL, category=MoveCategory.SPECIAL)
        assert is_physical(move)
        assert get_effective_category(move) == MoveCategory.PHYSICAL

    def test_fighting_is_physical(self):
        move = make_move(move_type=Type.FIGHTING, category=MoveCategory.SPECIAL)
        assert is_physical(move)

    def test_poison_is_physical(self):
        move = make_move(move_type=Type.POISON, category=MoveCategory.SPECIAL)
        assert is_physical(move)

    def test_ground_is_physical(self):
        move = make_move(move_type=Type.GROUND, category=MoveCategory.SPECIAL)
        assert is_physical(move)

    def test_flying_is_physical(self):
        move = make_move(move_type=Type.FLYING, category=MoveCategory.SPECIAL)
        assert is_physical(move)

    def test_bug_is_physical(self):
        move = make_move(move_type=Type.BUG, category=MoveCategory.SPECIAL)
        assert is_physical(move)

    def test_rock_is_physical(self):
        move = make_move(move_type=Type.ROCK, category=MoveCategory.SPECIAL)
        assert is_physical(move)

    def test_ghost_is_physical(self):
        move = make_move(move_type=Type.GHOST, category=MoveCategory.SPECIAL)
        assert is_physical(move)

    def test_water_is_special(self):
        move = make_move(move_type=Type.WATER, category=MoveCategory.PHYSICAL)
        assert not is_physical(move)
        assert get_effective_category(move) == MoveCategory.SPECIAL

    def test_fire_is_special(self):
        move = make_move(move_type=Type.FIRE, category=MoveCategory.PHYSICAL)
        assert not is_physical(move)

    def test_grass_is_special(self):
        move = make_move(move_type=Type.GRASS, category=MoveCategory.PHYSICAL)
        assert not is_physical(move)

    def test_ice_is_special(self):
        move = make_move(move_type=Type.ICE, category=MoveCategory.PHYSICAL)
        assert not is_physical(move)

    def test_electric_is_special(self):
        move = make_move(move_type=Type.ELECTRIC, category=MoveCategory.PHYSICAL)
        assert not is_physical(move)

    def test_psychic_is_special(self):
        move = make_move(move_type=Type.PSYCHIC, category=MoveCategory.PHYSICAL)
        assert not is_physical(move)

    def test_dragon_is_special(self):
        move = make_move(move_type=Type.DRAGON, category=MoveCategory.PHYSICAL)
        assert not is_physical(move)

    def test_status_always_returns_status(self):
        """STATUS moves should stay STATUS regardless of type."""
        move = make_move(move_type=Type.NORMAL, category=MoveCategory.STATUS, power=0)
        assert get_effective_category(move) == MoveCategory.STATUS
        assert not is_physical(move)

    def test_hyper_beam_is_physical_in_gen1(self):
        """Hyper Beam (Normal/Special in data) should resolve as Physical in Gen 1."""
        hyper_beam = make_move("Hyper Beam", move_type=Type.NORMAL,
                               category=MoveCategory.SPECIAL, power=150)
        assert is_physical(hyper_beam)

    def test_fire_punch_is_special_in_gen1(self):
        """Fire Punch (Fire/Physical in data) should resolve as Special in Gen 1."""
        fire_punch = make_move("Fire Punch", move_type=Type.FIRE,
                                category=MoveCategory.PHYSICAL, power=75)
        assert not is_physical(fire_punch)


class TestGen4PlusPerMoveSplit:
    """In Gen 4+, physical/special is determined per-move."""

    @pytest.fixture(autouse=True)
    def set_gen4(self):
        """Set GENERATION to 4 for these tests."""
        original = config.GENERATION
        config.GENERATION = 4
        yield
        config.GENERATION = original

    def test_hyper_beam_is_special_in_gen4(self):
        """Hyper Beam should use its per-move category (Special) in Gen 4+."""
        hyper_beam = make_move("Hyper Beam", move_type=Type.NORMAL,
                               category=MoveCategory.SPECIAL, power=150)
        assert not is_physical(hyper_beam)
        assert get_effective_category(hyper_beam) == MoveCategory.SPECIAL

    def test_fire_punch_is_physical_in_gen4(self):
        """Fire Punch should use its per-move category (Physical) in Gen 4+."""
        fire_punch = make_move("Fire Punch", move_type=Type.FIRE,
                                category=MoveCategory.PHYSICAL, power=75)
        assert is_physical(fire_punch)
        assert get_effective_category(fire_punch) == MoveCategory.PHYSICAL

    def test_status_still_status(self):
        """STATUS moves remain STATUS in all generations."""
        move = make_move(move_type=Type.FIRE, category=MoveCategory.STATUS, power=0)
        assert get_effective_category(move) == MoveCategory.STATUS


class TestPhysicalTypesSet:
    """Verify the PHYSICAL_TYPES set matches Gen 1 rules."""

    def test_all_physical_types_present(self):
        expected = {Type.NORMAL, Type.FIGHTING, Type.POISON, Type.GROUND,
                    Type.FLYING, Type.BUG, Type.ROCK, Type.GHOST}
        assert PHYSICAL_TYPES == expected

    def test_special_types_not_present(self):
        special_types = {Type.WATER, Type.FIRE, Type.GRASS, Type.ICE,
                         Type.ELECTRIC, Type.PSYCHIC, Type.DRAGON}
        for t in special_types:
            assert t not in PHYSICAL_TYPES
