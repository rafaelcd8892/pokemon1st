"""Tests for Gen 1 move data fields loaded from data/moves.json."""

import json
from pathlib import Path

import pytest

from data.data_loader import create_move
from engine.move_effects import create_struggle, execute_special_move
from models.enums import StatType
from tests.conftest import create_test_pokemon


MOVES_JSON = Path(__file__).resolve().parent.parent / "data" / "moves.json"


class TestLoadedFields:

    @pytest.mark.parametrize("slug,priority", [
        ("quick-attack", 1), ("counter", -1), ("tackle", 0),
    ])
    def test_priority(self, slug, priority):
        assert create_move(slug).priority == priority

    @pytest.mark.parametrize("slug", ["slash", "karate-chop", "razor-leaf", "crabhammer"])
    def test_high_crit_moves(self, slug):
        assert create_move(slug).high_crit is True

    def test_regular_move_is_not_high_crit(self):
        assert create_move("tackle").high_crit is False

    @pytest.mark.parametrize("slug,chance", [
        ("bite", 10), ("hyper-fang", 10), ("bone-club", 10),
        ("stomp", 30), ("headbutt", 30), ("rolling-kick", 30), ("low-kick", 30), ("rock-slide", 30),
    ])
    def test_flinch_chance(self, slug, chance):
        assert create_move(slug).flinch_chance == chance

    @pytest.mark.parametrize("slug,stat", [
        ("psychic", StatType.SPECIAL), ("aurora-beam", StatType.ATTACK), ("acid", StatType.DEFENSE),
        ("bubble", StatType.SPEED), ("bubble-beam", StatType.SPEED), ("constrict", StatType.SPEED),
    ])
    def test_secondary_stat_drop(self, slug, stat):
        move = create_move(slug)
        assert move.secondary_stat_changes == {stat: -1}
        assert move.secondary_stat_chance == 33
        assert move.stat_changes == {}  # must not be applied unconditionally

    @pytest.mark.parametrize("slug", ["take-down", "double-edge", "submission"])
    def test_recoil_divisor(self, slug):
        assert create_move(slug).recoil_divisor == 4

    def test_struggle_recoil_divisor(self):
        assert create_struggle().recoil_divisor == 2

    def test_defaults_for_plain_move(self):
        move = create_move("tackle")
        assert (move.priority, move.high_crit, move.flinch_chance, move.recoil_divisor) == (0, False, 0, 0)
        assert move.secondary_stat_changes == {}
        assert move.secondary_stat_chance == 0


class TestDataIntegrity:

    def test_only_known_keys(self):
        allowed = {
            "name", "type", "category", "power", "accuracy", "pp", "status_effect",
            "status_chance", "stat_changes", "target_self", "recoil_divisor", "priority",
            "high_crit", "flinch_chance", "secondary_stat_changes", "secondary_stat_chance",
        }
        for move in json.loads(MOVES_JSON.read_text())["moves"]:
            assert set(move) <= allowed, move["name"]

    def test_secondary_chance_set_with_secondary_changes(self):
        for move in json.loads(MOVES_JSON.read_text())["moves"]:
            has_changes = bool(move.get("secondary_stat_changes"))
            has_chance = move.get("secondary_stat_chance", 0) > 0
            assert has_changes == has_chance, move["name"]


class TestCopiesKeepFields:
    """Move copies (Transform, snapshot/restore) must keep the new fields."""

    def test_transform_copies_keep_fields(self, seeded_rng):
        attacker = create_test_pokemon("Ditto", moves=[create_move("transform")])
        defender = create_test_pokemon("Tauros", moves=[create_move("double-edge"), create_move("quick-attack")])

        execute_special_move(attacker, defender, attacker.moves[0])

        by_name = {m.name: m for m in attacker.moves}
        assert by_name["Double Edge"].recoil_divisor == 4
        assert by_name["Quick Attack"].priority == 1
        assert by_name["Double Edge"].pp == 5

    def test_restore_after_transform_keeps_fields(self, seeded_rng):
        ditto = create_test_pokemon("Ditto", moves=[create_move("transform"), create_move("double-edge")])
        foe = create_test_pokemon("Tauros", moves=[create_move("tackle")])

        execute_special_move(ditto, foe, ditto.moves[0])
        ditto.restore_transform_state()

        by_name = {m.name: m for m in ditto.moves}
        assert by_name["Double Edge"].recoil_divisor == 4
