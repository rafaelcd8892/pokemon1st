"""Audit invariants for battle logs."""

from pathlib import Path

from engine.team_battle import BattleAction, TeamBattle
from models.enums import BattleFormat, MoveCategory, Type
from models.team import Team
from scripts.validate_battle_log import validate_log_data, validate_log_file
from tests.conftest import create_test_move, create_test_pokemon


def test_validate_log_detects_faint_without_cause():
    data = {
        "metadata": {"battle_id": "synthetic"},
        "entries": [
            {"turn": 1, "action_type": "turn_start", "pokemon": "", "details": {}, "message": ""},
            {
                "turn": 1,
                "action_type": "hp",
                "pokemon": "A",
                "details": {"current_hp": 0, "max_hp": 100},
                "message": "",
            },
            {"turn": 1, "action_type": "faint", "pokemon": "A", "details": {}, "message": ""},
            {"turn": 1, "action_type": "turn_end", "pokemon": "", "details": {}, "message": ""},
        ],
    }

    anomalies = validate_log_data(data)
    codes = {a["code"] for a in anomalies}
    assert "faint_without_cause" in codes


def test_validate_log_detects_invalid_self_target():
    data = {
        "metadata": {"battle_id": "synthetic-self-target"},
        "entries": [
            {"turn": 3, "action_type": "turn_start", "pokemon": "", "details": {}, "message": ""},
            {
                "turn": 3,
                "action_type": "move",
                "pokemon": "Zapdos",
                "target": "Snorlax",
                "details": {"move": "Agility", "damage": 0, "critical": False, "effectiveness": 1.0},
                "message": "",
            },
            {"turn": 3, "action_type": "turn_end", "pokemon": "", "details": {}, "message": ""},
        ],
    }

    anomalies = validate_log_data(data)
    codes = {a["code"] for a in anomalies}
    assert "invalid_self_target" in codes


def test_validate_log_accepts_self_faint_cause():
    data = {
        "metadata": {"battle_id": "synthetic-self-faint"},
        "entries": [
            {"turn": 1, "action_type": "turn_start", "pokemon": "", "details": {}, "message": ""},
            {
                "turn": 1,
                "action_type": "move",
                "pokemon": "Snorlax",
                "target": "Gengar",
                "details": {
                    "move": "Self Destruct",
                    "damage": 0,
                    "critical": False,
                    "effectiveness": 0,
                    "self_faint": True,
                },
                "message": "",
            },
            {"turn": 1, "action_type": "faint", "pokemon": "Snorlax", "details": {}, "message": ""},
            {"turn": 1, "action_type": "turn_end", "pokemon": "", "details": {}, "message": ""},
        ],
    }

    anomalies = validate_log_data(data)
    codes = {a["code"] for a in anomalies}
    assert "faint_without_cause" not in codes


def test_validate_log_detects_duplicate_move_event():
    move = {
        "turn": 2,
        "action_type": "move",
        "pokemon": "Gloom",
        "target": "Bulbasaur",
        "details": {"move": "Solar Beam", "damage": 0, "critical": False, "effectiveness": 1.0},
        "message": "",
    }
    data = {
        "metadata": {"battle_id": "synthetic-duplicate-move"},
        "entries": [
            {"turn": 2, "action_type": "turn_start", "pokemon": "", "details": {}, "message": ""},
            move,
            dict(move),
            {"turn": 2, "action_type": "turn_end", "pokemon": "", "details": {}, "message": ""},
        ],
    }

    anomalies = validate_log_data(data)
    codes = {a["code"] for a in anomalies}
    assert "duplicate_move_event" in codes


def test_generated_team_battle_satisfies_core_audit_invariants():
    tackle = create_test_move(
        name="Tackle",
        move_type=Type.NORMAL,
        category=MoveCategory.PHYSICAL,
        power=55,
        accuracy=100,
    )
    splash = create_test_move(
        name="Splash",
        move_type=Type.NORMAL,
        category=MoveCategory.STATUS,
        power=0,
        accuracy=100,
    )

    p1 = create_test_pokemon(name="MonA", moves=[tackle], attack=120, hp=130, speed=100)
    p2 = create_test_pokemon(name="MonB", moves=[splash], defense=60, hp=90, speed=20)

    battle = TeamBattle(
        Team([p1], "A"),
        Team([p2], "B"),
        battle_format=BattleFormat.SINGLE,
        action_delay=0,
        enable_battle_log=True,
    )

    battle.run_battle(
        get_player_action=lambda team, opp: BattleAction.attack(team.active_pokemon.moves[0]),
        get_opponent_action=lambda team, opp: BattleAction.attack(team.active_pokemon.moves[0]),
    )

    data = {
        "metadata": battle.battle_logger.metadata,
        "entries": [e.to_dict() for e in battle.battle_logger.entries],
    }
    anomalies = validate_log_data(data)
    errors = [a for a in anomalies if a["level"] == "ERROR"]

    assert not errors, f"Expected no audit errors, got: {errors}"


def test_validator_reports_errors_on_known_bad_log_file():
    log_file = Path("logs/battles/battle_20260211_075226.json.bak")
    if not log_file.exists():
        return

    _, anomalies = validate_log_file(log_file)
    errors = [a for a in anomalies if a["level"] == "ERROR"]

    assert errors, "Known bad log should produce audit errors"
