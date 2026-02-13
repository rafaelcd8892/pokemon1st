"""Golden test utilities — shared by scripts/run_golden.py and tests/test_golden.py.

Provides scenario discovery, team construction, battle execution,
log normalization, and structural comparison.
"""

from __future__ import annotations

import copy
import io
import json
import math
import random
import sys
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).parent.parent
SCENARIOS_DIR = PROJECT_ROOT / "tests" / "scenarios"
GOLDEN_DIR = PROJECT_ROOT / "tests" / "golden"

# Ensure project root is importable
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.data_loader import get_pokemon_data, create_move
from engine.team_battle import TeamBattle, get_random_ai_action, get_random_forced_switch
from models.enums import BattleFormat, Type
from models.pokemon import Pokemon
from models.stats import Stats
from models.team import Team

FORMAT_MAP = {
    "1v1": BattleFormat.SINGLE,
    "3v3": BattleFormat.TRIPLE,
    "6v6": BattleFormat.FULL,
}

# Fields stripped from logs before comparison (volatile across runs)
VOLATILE_METADATA_FIELDS = {"battle_id", "start_time", "end_time"}

# Relative tolerance for float comparisons
FLOAT_REL_TOL = 1e-9


# ---------------------------------------------------------------------------
# Scenario discovery & loading
# ---------------------------------------------------------------------------

def discover_scenarios() -> list[Path]:
    """Return sorted list of ``tests/scenarios/*.json`` files."""
    if not SCENARIOS_DIR.is_dir():
        return []
    return sorted(SCENARIOS_DIR.glob("*.json"))


def load_scenario(path: Path) -> dict:
    """Parse and do basic validation on a scenario JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        scenario = json.load(f)

    required = {"name", "seed", "format", "team1", "team2"}
    missing = required - set(scenario.keys())
    if missing:
        raise ValueError(f"Scenario {path.name} missing keys: {missing}")

    if scenario["format"] not in FORMAT_MAP:
        raise ValueError(
            f"Scenario {path.name}: unknown format '{scenario['format']}' "
            f"(expected one of {list(FORMAT_MAP)})"
        )

    for side in ("team1", "team2"):
        team = scenario[side]
        if "pokemon" not in team or not team["pokemon"]:
            raise ValueError(f"Scenario {path.name}: {side} has no pokemon")

    return scenario


# ---------------------------------------------------------------------------
# Team construction
# ---------------------------------------------------------------------------

def build_team_from_spec(team_spec: dict) -> Team:
    """Build a ``Team`` from a scenario team specification.

    Each pokemon entry needs at minimum ``species`` and ``moves``.
    Optional: ``level`` (default 50).
    """
    pokemon_list: list[Pokemon] = []

    for poke_spec in team_spec["pokemon"]:
        species = poke_spec["species"]
        poke_data = get_pokemon_data(species)

        moves = [create_move(m) for m in poke_spec["moves"]]
        level = poke_spec.get("level", 50)

        stats = Stats(
            hp=poke_data["stats"].get("hp", 100),
            attack=poke_data["stats"].get("attack", 50),
            defense=poke_data["stats"].get("defense", 50),
            special=poke_data["stats"].get("special-attack", 50),
            speed=poke_data["stats"].get("speed", 50),
        )
        types = [getattr(Type, t.upper(), Type.NORMAL) for t in poke_data["types"]]
        pokemon = Pokemon(poke_data["name"], types, stats, moves, level=level)
        pokemon_list.append(pokemon)

    return Team(pokemon_list, team_spec.get("name", "Trainer"))


# ---------------------------------------------------------------------------
# Battle execution
# ---------------------------------------------------------------------------

def run_scenario(scenario: dict, log_dir: Path) -> dict:
    """Seed RNG, build teams, run a ``TeamBattle``, return parsed JSON log.

    The battle log JSON is written to *log_dir* and then loaded back
    so callers get the exact same structure that would be stored as a
    golden baseline.
    """
    import logging
    logging.getLogger().setLevel(logging.WARNING)

    random.seed(scenario["seed"])

    team1 = build_team_from_spec(scenario["team1"])
    team2 = build_team_from_spec(scenario["team2"])

    battle_format = FORMAT_MAP[scenario["format"]]

    # Suppress stdout from the battle engine
    with redirect_stdout(io.StringIO()):
        battle = TeamBattle(
            team1,
            team2,
            battle_format=battle_format,
            action_delay=0,
            enable_battle_log=True,
            log_dir=log_dir,
        )
        battle_id = battle.battle_logger.battle_id
        battle.run_battle(
            get_player_action=get_random_ai_action,
            get_opponent_action=get_random_ai_action,
            get_forced_switch=get_random_forced_switch,
        )

    json_path = log_dir / f"{battle_id}.json"
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Log normalization
# ---------------------------------------------------------------------------

def normalize_log(log_data: dict) -> dict:
    """Return a deep copy with volatile fields removed.

    Strips ``battle_id``, ``start_time``, ``end_time`` from metadata
    so that two runs with the same seed can be compared cleanly.
    """
    normalized = copy.deepcopy(log_data)

    meta = normalized.get("metadata", {})
    for field in VOLATILE_METADATA_FIELDS:
        meta.pop(field, None)

    return normalized


# ---------------------------------------------------------------------------
# Golden filename helper
# ---------------------------------------------------------------------------

def golden_filename(scenario: dict) -> str:
    """Return ``<name>__seed_<N>.json``."""
    return f"{scenario['name']}__seed_{scenario['seed']}.json"


# ---------------------------------------------------------------------------
# Structural comparison
# ---------------------------------------------------------------------------

def compare_logs(expected: Any, actual: Any, path: str = "") -> list[str]:
    """Recursively compare two log structures.

    Returns a list of human-readable difference messages such as:
        ``entries[3].details.damage: expected 45, got 47``

    Float values are compared with relative tolerance.
    """
    diffs: list[str] = []

    if isinstance(expected, dict) and isinstance(actual, dict):
        all_keys = set(expected) | set(actual)
        for key in sorted(all_keys):
            child_path = f"{path}.{key}" if path else key
            if key not in expected:
                diffs.append(f"{child_path}: unexpected key (got {_fmt(actual[key])})")
            elif key not in actual:
                diffs.append(f"{child_path}: missing key (expected {_fmt(expected[key])})")
            else:
                diffs.extend(compare_logs(expected[key], actual[key], child_path))

    elif isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            diffs.append(
                f"{path}: list length differs: expected {len(expected)}, got {len(actual)}"
            )
        for i in range(min(len(expected), len(actual))):
            diffs.extend(compare_logs(expected[i], actual[i], f"{path}[{i}]"))

    elif isinstance(expected, float) or isinstance(actual, float):
        try:
            exp_f = float(expected)
            act_f = float(actual)
        except (TypeError, ValueError):
            if expected != actual:
                diffs.append(f"{path}: expected {_fmt(expected)}, got {_fmt(actual)}")
        else:
            if not math.isclose(exp_f, act_f, rel_tol=FLOAT_REL_TOL):
                diffs.append(f"{path}: expected {_fmt(expected)}, got {_fmt(actual)}")

    elif expected != actual:
        diffs.append(f"{path}: expected {_fmt(expected)}, got {_fmt(actual)}")

    return diffs


def _fmt(value: Any) -> str:
    """Short repr for diff messages."""
    if isinstance(value, str):
        return repr(value)
    return str(value)
