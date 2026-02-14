"""Tests for battle clause enforcement."""

import pytest
from models.enums import Status, Type, MoveCategory
from models.stats import Stats
from models.pokemon import Pokemon
from models.move import Move
from models.ruleset import BattleClauses
from engine.clauses import (
    check_sleep_clause, check_freeze_clause,
    check_ohko_clause, check_evasion_clause,
    check_move_clauses, check_status_clause,
    is_move_banned_by_clauses,
    OHKO_MOVES, EVASION_MOVES,
)


def make_pokemon(name: str = "TestMon", status: Status = Status.NONE,
                 alive: bool = True) -> Pokemon:
    """Create a minimal test Pokemon."""
    stats = Stats(hp=100, attack=100, defense=100, special=100, speed=100)
    p = Pokemon(name, [Type.NORMAL], stats, [], level=50, use_calculated_stats=False)
    p.status = status
    if not alive:
        p.current_hp = 0
    return p


def make_move(name: str, power: int = 0, move_type: Type = Type.NORMAL,
              category: MoveCategory = MoveCategory.STATUS) -> Move:
    """Create a minimal test Move."""
    return Move(name=name, type=move_type, category=category,
                power=power, accuracy=100, pp=10, max_pp=10)


class TestSleepClause:
    """Sleep Clause: only one opponent Pokemon may be asleep at a time."""

    def test_allows_first_sleep(self):
        """First sleep on a team should be allowed."""
        clauses = BattleClauses(sleep_clause=True)
        team = [make_pokemon("Mon1"), make_pokemon("Mon2")]
        allowed, reason = check_sleep_clause(team, clauses)
        assert allowed
        assert reason == ""

    def test_blocks_second_sleep(self):
        """Second sleep should be blocked when one is already asleep."""
        clauses = BattleClauses(sleep_clause=True)
        team = [make_pokemon("Mon1", status=Status.SLEEP), make_pokemon("Mon2")]
        allowed, reason = check_sleep_clause(team, clauses)
        assert not allowed
        assert "Sleep Clause" in reason

    def test_inactive_allows_multiple_sleep(self):
        """When sleep clause is off, multiple sleeps are allowed."""
        clauses = BattleClauses(sleep_clause=False)
        team = [make_pokemon("Mon1", status=Status.SLEEP), make_pokemon("Mon2")]
        allowed, _ = check_sleep_clause(team, clauses)
        assert allowed

    def test_fainted_pokemon_dont_count(self):
        """A fainted Pokemon's sleep status shouldn't block new sleeps."""
        clauses = BattleClauses(sleep_clause=True)
        team = [make_pokemon("Mon1", status=Status.SLEEP, alive=False),
                make_pokemon("Mon2")]
        allowed, _ = check_sleep_clause(team, clauses)
        assert allowed

    def test_check_status_clause_routes_sleep(self):
        """check_status_clause should route SLEEP to sleep clause."""
        clauses = BattleClauses(sleep_clause=True)
        team = [make_pokemon("Mon1", status=Status.SLEEP), make_pokemon("Mon2")]
        allowed, reason = check_status_clause(Status.SLEEP, team, clauses)
        assert not allowed
        assert "Sleep Clause" in reason


class TestFreezeClause:
    """Freeze Clause: only one opponent Pokemon may be frozen at a time."""

    def test_allows_first_freeze(self):
        """First freeze on a team should be allowed."""
        clauses = BattleClauses(freeze_clause=True)
        team = [make_pokemon("Mon1"), make_pokemon("Mon2")]
        allowed, _ = check_freeze_clause(team, clauses)
        assert allowed

    def test_blocks_second_freeze(self):
        """Second freeze should be blocked when one is already frozen."""
        clauses = BattleClauses(freeze_clause=True)
        team = [make_pokemon("Mon1", status=Status.FREEZE), make_pokemon("Mon2")]
        allowed, reason = check_freeze_clause(team, clauses)
        assert not allowed
        assert "Freeze Clause" in reason

    def test_inactive_allows_multiple_freeze(self):
        """When freeze clause is off, multiple freezes are allowed."""
        clauses = BattleClauses(freeze_clause=False)
        team = [make_pokemon("Mon1", status=Status.FREEZE), make_pokemon("Mon2")]
        allowed, _ = check_freeze_clause(team, clauses)
        assert allowed

    def test_fainted_pokemon_dont_count(self):
        """A fainted Pokemon's freeze status shouldn't block new freezes."""
        clauses = BattleClauses(freeze_clause=True)
        team = [make_pokemon("Mon1", status=Status.FREEZE, alive=False),
                make_pokemon("Mon2")]
        allowed, _ = check_freeze_clause(team, clauses)
        assert allowed

    def test_check_status_clause_routes_freeze(self):
        """check_status_clause should route FREEZE to freeze clause."""
        clauses = BattleClauses(freeze_clause=True)
        team = [make_pokemon("Mon1", status=Status.FREEZE), make_pokemon("Mon2")]
        allowed, reason = check_status_clause(Status.FREEZE, team, clauses)
        assert not allowed
        assert "Freeze Clause" in reason


class TestOHKOClause:
    """OHKO Clause: bans Fissure, Guillotine, Horn Drill."""

    def test_blocks_fissure(self):
        clauses = BattleClauses(ohko_clause=True)
        move = make_move("Fissure")
        allowed, reason = check_ohko_clause(move, clauses)
        assert not allowed
        assert "Fissure" in reason

    def test_blocks_guillotine(self):
        clauses = BattleClauses(ohko_clause=True)
        move = make_move("Guillotine")
        allowed, reason = check_ohko_clause(move, clauses)
        assert not allowed
        assert "Guillotine" in reason

    def test_blocks_horn_drill(self):
        clauses = BattleClauses(ohko_clause=True)
        move = make_move("Horn Drill")
        allowed, reason = check_ohko_clause(move, clauses)
        assert not allowed
        assert "Horn Drill" in reason

    def test_allows_normal_moves(self):
        clauses = BattleClauses(ohko_clause=True)
        move = make_move("Tackle", power=40, category=MoveCategory.PHYSICAL)
        allowed, _ = check_ohko_clause(move, clauses)
        assert allowed

    def test_inactive_allows_ohko(self):
        clauses = BattleClauses(ohko_clause=False)
        move = make_move("Fissure")
        allowed, _ = check_ohko_clause(move, clauses)
        assert allowed


class TestEvasionClause:
    """Evasion Clause: bans Double Team and Minimize."""

    def test_blocks_double_team(self):
        clauses = BattleClauses(evasion_clause=True)
        move = make_move("Double Team")
        allowed, reason = check_evasion_clause(move, clauses)
        assert not allowed
        assert "Double Team" in reason

    def test_blocks_minimize(self):
        clauses = BattleClauses(evasion_clause=True)
        move = make_move("Minimize")
        allowed, reason = check_evasion_clause(move, clauses)
        assert not allowed
        assert "Minimize" in reason

    def test_allows_other_status_moves(self):
        clauses = BattleClauses(evasion_clause=True)
        move = make_move("Agility")
        allowed, _ = check_evasion_clause(move, clauses)
        assert allowed

    def test_inactive_allows_evasion(self):
        clauses = BattleClauses(evasion_clause=False)
        move = make_move("Double Team")
        allowed, _ = check_evasion_clause(move, clauses)
        assert allowed


class TestCombinedChecks:
    """Test combined clause checking functions."""

    def test_check_move_clauses_catches_ohko(self):
        clauses = BattleClauses(ohko_clause=True, evasion_clause=True)
        move = make_move("Fissure")
        allowed, reason = check_move_clauses(move, clauses)
        assert not allowed
        assert "OHKO" in reason

    def test_check_move_clauses_catches_evasion(self):
        clauses = BattleClauses(ohko_clause=True, evasion_clause=True)
        move = make_move("Double Team")
        allowed, reason = check_move_clauses(move, clauses)
        assert not allowed
        assert "Evasion" in reason

    def test_check_move_clauses_allows_normal(self):
        clauses = BattleClauses(ohko_clause=True, evasion_clause=True)
        move = make_move("Surf", power=95, category=MoveCategory.SPECIAL)
        allowed, _ = check_move_clauses(move, clauses)
        assert allowed

    def test_is_move_banned_helper(self):
        clauses = BattleClauses(ohko_clause=True)
        assert is_move_banned_by_clauses(make_move("Fissure"), clauses)
        assert not is_move_banned_by_clauses(make_move("Tackle"), clauses)

    def test_non_sleep_freeze_status_always_allowed(self):
        """Paralysis, poison, burn are never blocked by clauses."""
        clauses = BattleClauses(sleep_clause=True, freeze_clause=True)
        team = [make_pokemon("Mon1", status=Status.PARALYSIS)]
        allowed, _ = check_status_clause(Status.PARALYSIS, team, clauses)
        assert allowed

        allowed, _ = check_status_clause(Status.POISON, team, clauses)
        assert allowed

        allowed, _ = check_status_clause(Status.BURN, team, clauses)
        assert allowed


class TestBattleClausesDataclass:
    """Test the BattleClauses dataclass itself."""

    def test_defaults_all_off(self):
        clauses = BattleClauses()
        assert not clauses.sleep_clause
        assert not clauses.freeze_clause
        assert not clauses.ohko_clause
        assert not clauses.evasion_clause
        assert not clauses.any_active()
        assert clauses.get_active_list() == []

    def test_any_active(self):
        clauses = BattleClauses(sleep_clause=True)
        assert clauses.any_active()

    def test_get_active_list(self):
        clauses = BattleClauses(sleep_clause=True, ohko_clause=True)
        active = clauses.get_active_list()
        assert "Sleep Clause" in active
        assert "OHKO Clause" in active
        assert len(active) == 2

    def test_known_ohko_moves(self):
        """Verify the OHKO move set matches expected Gen 1 moves."""
        assert OHKO_MOVES == {"Fissure", "Guillotine", "Horn Drill"}

    def test_known_evasion_moves(self):
        """Verify the evasion move set matches expected Gen 1 moves."""
        assert EVASION_MOVES == {"Double Team", "Minimize"}
