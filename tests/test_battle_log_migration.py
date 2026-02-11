"""Tests for legacy battle log migration."""

from scripts.migrate_battle_logs import migrate_log_data
from scripts.validate_battle_log import validate_log_data


def test_migration_adds_turn_markers_and_causal_effect_for_legacy_faint():
    legacy = {
        "metadata": {"battle_id": "legacy"},
        "entries": [
            {"turn": 1, "action_type": "switch", "pokemon": "Exeggcute", "details": {}, "message": ""},
            {
                "turn": 1,
                "action_type": "hp",
                "pokemon": "Exeggcute",
                "details": {"current_hp": 0, "max_hp": 100},
                "message": "",
            },
            {"turn": 1, "action_type": "faint", "pokemon": "Exeggcute", "details": {}, "message": ""},
        ],
    }

    migrated = migrate_log_data(legacy)
    anomalies = validate_log_data(migrated)
    errors = [a for a in anomalies if a["level"] == "ERROR"]

    assert not errors
    assert migrated["metadata"]["audit_migrated"] is True


def test_migration_fixes_self_target_move_target():
    legacy = {
        "metadata": {"battle_id": "legacy2"},
        "entries": [
            {"turn": 1, "action_type": "turn_start", "pokemon": "", "details": {}, "message": ""},
            {
                "turn": 1,
                "action_type": "move",
                "pokemon": "Zapdos",
                "target": "Snorlax",
                "details": {"move": "Agility", "damage": 0, "critical": False, "effectiveness": 1.0},
                "message": "",
            },
            {"turn": 1, "action_type": "turn_end", "pokemon": "", "details": {}, "message": ""},
        ],
    }

    migrated = migrate_log_data(legacy)
    move = [e for e in migrated["entries"] if e["action_type"] == "move"][0]
    assert move["target"] == "Zapdos"


def test_migration_deduplicates_repeated_move_events():
    legacy = {
        "metadata": {"battle_id": "legacy-dup"},
        "entries": [
            {"turn": 4, "action_type": "turn_start", "pokemon": "", "details": {}, "message": ""},
            {
                "turn": 4,
                "action_type": "move",
                "pokemon": "Sandshrew",
                "target": "Bulbasaur",
                "details": {"move": "Dig", "damage": 0, "critical": False, "effectiveness": 1.0},
                "message": "",
            },
            {
                "turn": 4,
                "action_type": "move",
                "pokemon": "Sandshrew",
                "target": "Bulbasaur",
                "details": {"move": "Dig", "damage": 0, "critical": False, "effectiveness": 1.0},
                "message": "",
            },
            {"turn": 4, "action_type": "turn_end", "pokemon": "", "details": {}, "message": ""},
        ],
    }

    migrated = migrate_log_data(legacy)
    move_entries = [e for e in migrated["entries"] if e["action_type"] == "move"]
    assert len(move_entries) == 1
