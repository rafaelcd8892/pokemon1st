#!/usr/bin/env python3
"""Batch battle runner with automatic log validation.

Runs N battles using AI-controlled teams, validates every generated log,
and reports aggregate statistics and anomalies.

Usage:
    python scripts/batch_battle.py --battles 100 --format 3v3 --moveset smart_random
    python scripts/batch_battle.py --battles 50 --format 6v6 --stop-on-error
    python scripts/batch_battle.py --battles 10 --seed 42 --verbose
"""

from __future__ import annotations

import argparse
import io
import json
import os
import random
import sys
import time
from collections import Counter
from contextlib import redirect_stdout
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from models.enums import BattleFormat, Type
from models.stats import Stats
from models.pokemon import Pokemon
from models.team import Team
from engine.team_battle import TeamBattle, get_random_ai_action, get_random_forced_switch
from data.data_loader import (
    get_kanto_pokemon_list,
    get_pokemon_data,
    get_moveset_for_pokemon,
    create_move,
)
from scripts.validate_battle_log import validate_log_data

# Default output directory for batch logs
BATCH_LOGS_DIR = PROJECT_ROOT / "logs" / "batch"

FORMAT_MAP = {
    "1v1": BattleFormat.SINGLE,
    "3v3": BattleFormat.TRIPLE,
    "6v6": BattleFormat.FULL,
}


def create_team(size: int, name: str, moveset_mode: str) -> Team:
    """Create a random team with the given moveset mode."""
    kanto_list = get_kanto_pokemon_list()
    selected_names = random.sample(kanto_list, min(size, len(kanto_list)))

    pokemon_list = []
    for poke_name in selected_names:
        poke_data = get_pokemon_data(poke_name)
        moves_selected = get_moveset_for_pokemon(poke_name, moveset_mode)
        moves = [create_move(m) for m in moves_selected]

        stats = Stats(
            hp=poke_data["stats"].get("hp", 100),
            attack=poke_data["stats"].get("attack", 50),
            defense=poke_data["stats"].get("defense", 50),
            special=poke_data["stats"].get("special-attack", 50),
            speed=poke_data["stats"].get("speed", 50),
        )
        types = [getattr(Type, t.upper(), Type.NORMAL) for t in poke_data["types"]]
        pokemon = Pokemon(poke_data["name"], types, stats, moves, level=50)
        pokemon_list.append(pokemon)

    return Team(pokemon_list, name)


def run_single_battle(
    battle_format: BattleFormat,
    moveset_mode: str,
    log_dir: Path,
    verbose: bool = False,
) -> dict:
    """Run one battle and return results.

    Returns dict with keys: battle_id, winner, turns, anomalies, team1, team2
    """
    team1 = create_team(battle_format.team_size, "Team 1", moveset_mode)
    team2 = create_team(battle_format.team_size, "Team 2", moveset_mode)

    team1_names = [p.name for p in team1.pokemon]
    team2_names = [p.name for p in team2.pokemon]

    # Run battle, suppressing stdout from the engine
    stdout_target = sys.stdout if verbose else io.StringIO()
    with redirect_stdout(stdout_target):
        battle = TeamBattle(
            team1, team2,
            battle_format=battle_format,
            action_delay=0,
            log_dir=log_dir,
        )
        battle_id = battle.battle_logger.battle_id
        winner = battle.run_battle(
            get_player_action=get_random_ai_action,
            get_opponent_action=get_random_ai_action,
            get_forced_switch=get_random_forced_switch,
        )

    # Load and validate the JSON log
    json_path = log_dir / f"{battle_id}.json"
    anomalies = []
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            log_data = json.load(f)
        anomalies = validate_log_data(log_data)

    return {
        "battle_id": battle_id,
        "winner": winner.name if winner else "Draw",
        "turns": battle.turn_count,
        "anomalies": anomalies,
        "team1": team1_names,
        "team2": team2_names,
    }


def print_summary(results: list[dict], elapsed: float):
    """Print aggregate summary of all battles."""
    total = len(results)
    total_turns = sum(r["turns"] for r in results)
    avg_turns = total_turns / total if total else 0

    # Win distribution
    wins = Counter(r["winner"] for r in results)

    # Anomaly aggregation
    all_anomalies = []
    battles_with_errors = []
    for r in results:
        for a in r["anomalies"]:
            all_anomalies.append(a)
            if a["level"] == "ERROR" and r["battle_id"] not in [b["id"] for b in battles_with_errors]:
                battles_with_errors.append({"id": r["battle_id"], "errors": []})
        for a in r["anomalies"]:
            if a["level"] == "ERROR":
                for b in battles_with_errors:
                    if b["id"] == r["battle_id"]:
                        b["errors"].append(a)

    error_count = sum(1 for a in all_anomalies if a["level"] == "ERROR")
    warn_count = sum(1 for a in all_anomalies if a["level"] == "WARN")
    anomaly_codes = Counter(a["code"] for a in all_anomalies)

    # Print report
    print("\n" + "=" * 60)
    print("  BATCH BATTLE REPORT")
    print("=" * 60)

    print(f"\n  Battles run:     {total}")
    print(f"  Total time:      {elapsed:.1f}s ({elapsed/total:.2f}s per battle)" if total else "")
    print(f"  Average turns:   {avg_turns:.1f}")
    print(f"  Total turns:     {total_turns}")

    print(f"\n  --- Win Distribution ---")
    for name, count in wins.most_common():
        pct = count / total * 100
        bar = "#" * int(pct / 2)
        print(f"  {name:<12} {count:>4} ({pct:5.1f}%) {bar}")

    print(f"\n  --- Validation ---")
    print(f"  Errors:   {error_count}")
    print(f"  Warnings: {warn_count}")

    if anomaly_codes:
        print(f"\n  --- Anomaly Breakdown ---")
        for code, count in anomaly_codes.most_common():
            level = "ERR" if any(
                a["level"] == "ERROR" for a in all_anomalies if a["code"] == code
            ) else "WRN"
            print(f"  [{level}] {code}: {count}")

    if battles_with_errors:
        print(f"\n  --- Battles With Errors ({len(battles_with_errors)}) ---")
        for b in battles_with_errors[:10]:
            error_codes = [e["code"] for e in b["errors"]]
            print(f"  {b['id']}: {', '.join(error_codes)}")
        if len(battles_with_errors) > 10:
            print(f"  ... and {len(battles_with_errors) - 10} more")

    print("\n" + "=" * 60)

    return error_count


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run batch Pokemon battles with automatic log validation"
    )
    parser.add_argument(
        "--battles", "-n", type=int, default=10,
        help="Number of battles to run (default: 10)",
    )
    parser.add_argument(
        "--format", "-f", choices=["1v1", "3v3", "6v6"], default="3v3",
        help="Battle format (default: 3v3)",
    )
    parser.add_argument(
        "--moveset", "-m",
        choices=["random", "preset", "smart_random"],
        default="smart_random",
        help="Moveset selection mode (default: smart_random)",
    )
    parser.add_argument(
        "--seed", "-s", type=int, default=None,
        help="Base random seed for reproducibility",
    )
    parser.add_argument(
        "--stop-on-error", action="store_true",
        help="Stop on first ERROR-level anomaly",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show battle output (very noisy)",
    )
    parser.add_argument(
        "--output-dir", "-o", type=Path, default=None,
        help="Custom output directory for logs (default: logs/batch/)",
    )
    args = parser.parse_args()

    battle_format = FORMAT_MAP[args.format]
    log_dir = args.output_dir or BATCH_LOGS_DIR
    log_dir.mkdir(parents=True, exist_ok=True)

    # Suppress logging noise in batch mode
    import logging
    logging.getLogger().setLevel(logging.WARNING)

    print(f"Running {args.battles} battles ({args.format}, {args.moveset} movesets)")
    print(f"Logs: {log_dir}")
    if args.seed is not None:
        print(f"Base seed: {args.seed}")
    print()

    results = []
    start_time = time.time()

    for i in range(args.battles):
        # Seed RNG per battle for reproducibility
        if args.seed is not None:
            random.seed(args.seed + i)

        result = run_single_battle(
            battle_format, args.moveset, log_dir, verbose=args.verbose
        )
        results.append(result)

        # Progress indicator
        errors = sum(1 for a in result["anomalies"] if a["level"] == "ERROR")
        warns = sum(1 for a in result["anomalies"] if a["level"] == "WARN")
        status = "OK" if errors == 0 else f"ERR({errors})"
        if warns > 0 and errors == 0:
            status = f"WARN({warns})"

        print(
            f"  [{i+1:>{len(str(args.battles))}}/{args.battles}] "
            f"{result['battle_id']} "
            f"turns={result['turns']:>3} "
            f"winner={result['winner']:<12} "
            f"{status}"
        )

        if args.stop_on_error and errors > 0:
            print(f"\n  Stopping due to --stop-on-error (battle {result['battle_id']})")
            for a in result["anomalies"]:
                if a["level"] == "ERROR":
                    print(f"    [{a['level']}] turn={a['turn']} {a['code']}: {a['message']}")
            break

    elapsed = time.time() - start_time
    error_count = print_summary(results, elapsed)

    return 1 if error_count > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
