#!/usr/bin/env python3
"""Migrate legacy battle logs to the current audit contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

try:
    from scripts.validate_battle_log import SELF_TARGET_MOVES, validate_log_data
except ModuleNotFoundError:
    from validate_battle_log import SELF_TARGET_MOVES, validate_log_data


def _group_by_turn(entries: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
    by_turn: Dict[int, List[Dict[str, Any]]] = {}
    for e in entries:
        by_turn.setdefault(int(e.get("turn", 0)), []).append(e)
    return by_turn


def _latest_hp_before(entries: List[Dict[str, Any]], pokemon: str, turn: int) -> int | None:
    hp_val: int | None = None
    for e in entries:
        e_turn = int(e.get("turn", 0))
        if e_turn >= turn:
            break
        if e.get("action_type") == "hp" and e.get("pokemon") == pokemon:
            details = e.get("details", {})
            hp_val = details.get("current_hp")
    return hp_val


def migrate_log_data(data: Dict[str, Any]) -> Dict[str, Any]:
    entries = data.get("entries", [])

    # Normalize shape.
    for e in entries:
        e.setdefault("details", {})
        e.setdefault("message", "")

    # Fix self-target move semantics.
    for e in entries:
        if e.get("action_type") != "move":
            continue
        move = e.get("details", {}).get("move")
        if move in SELF_TARGET_MOVES:
            e["target"] = e.get("pokemon")
        if move in {"Explosion", "Self Destruct"}:
            e.setdefault("details", {})["self_faint"] = True

    by_turn = _group_by_turn(entries)
    migrated_entries: List[Dict[str, Any]] = []

    # Rebuild per turn to insert boundaries and synthetic causal events.
    for turn in sorted(by_turn.keys()):
        turn_entries = by_turn[turn]
        if turn == 0:
            migrated_entries.extend(turn_entries)
            continue

        has_turn_start = any(e.get("action_type") == "turn_start" for e in turn_entries)
        has_turn_end = any(e.get("action_type") == "turn_end" for e in turn_entries)

        if not has_turn_start:
            migrated_entries.append(
                {
                    "turn": turn,
                    "action_type": "turn_start",
                    "pokemon": "",
                    "target": None,
                    "details": {"migrated": True},
                    "message": f"TURN {turn} START (migrated)",
                }
            )

        # Handle invalid switch into fainted: transform switch -> info to preserve chronology.
        switch_targets = [e.get("pokemon") for e in turn_entries if e.get("action_type") == "switch"]
        fainted_this_turn = {
            e.get("pokemon")
            for e in turn_entries
            if e.get("action_type") == "hp" and e.get("details", {}).get("current_hp") == 0
        }

        dedupe_seen = set()
        for e in turn_entries:
            if e.get("action_type") == "move":
                d = e.get("details", {})
                dedupe_key = (
                    e.get("pokemon"),
                    e.get("target"),
                    d.get("move"),
                    d.get("damage"),
                    d.get("critical"),
                    d.get("effectiveness"),
                    d.get("result", "resolved"),
                )
                if dedupe_key in dedupe_seen:
                    continue
                dedupe_seen.add(dedupe_key)
            if e.get("action_type") == "switch" and e.get("pokemon") in fainted_this_turn:
                e["action_type"] = "info"
                e["message"] = (
                    f"Legacy invalid switch normalized: sent-in {e.get('pokemon')} had 0 HP"
                )
                e.setdefault("details", {})["migrated_from"] = "switch"
            migrated_entries.append(e)

        # Ensure faint has a causal event in same turn.
        current_turn_entries = [e for e in migrated_entries if int(e.get("turn", 0)) == turn]
        fainted = [e.get("pokemon") for e in current_turn_entries if e.get("action_type") == "faint"]

        for p in fainted:
            has_cause = False
            for e in current_turn_entries:
                et = e.get("action_type")
                if et == "move" and e.get("target") == p and e.get("details", {}).get("damage", 0) > 0:
                    has_cause = True
                    break
                if et == "effect" and e.get("pokemon") == p and e.get("details", {}).get("damage", 0) > 0:
                    has_cause = True
                    break
                if et == "move" and e.get("pokemon") == p and e.get("details", {}).get("self_faint") is True:
                    has_cause = True
                    break

            if not has_cause:
                prev_hp = _latest_hp_before(entries, p, turn)
                synthetic_damage = prev_hp if isinstance(prev_hp, int) and prev_hp > 0 else 1
                migrated_entries.append(
                    {
                        "turn": turn,
                        "action_type": "effect",
                        "pokemon": p,
                        "target": None,
                        "details": {
                            "effect": "legacy_untracked_faint_cause",
                            "damage": synthetic_damage,
                            "migrated": True,
                        },
                        "message": "Synthetic causal effect added by migration",
                    }
                )

        if not has_turn_end:
            migrated_entries.append(
                {
                    "turn": turn,
                    "action_type": "turn_end",
                    "pokemon": "",
                    "target": None,
                    "details": {"migrated": True},
                    "message": f"TURN {turn} END (migrated)",
                }
            )

    data.setdefault("metadata", {})["audit_migrated"] = True
    data["metadata"]["audit_migration_version"] = 1
    data["entries"] = migrated_entries
    return data


def migrate_file(path: Path, inplace: bool = True) -> tuple[int, int]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    before = len([a for a in validate_log_data(data) if a["level"] == "ERROR"])
    migrated = migrate_log_data(data)
    after = len([a for a in validate_log_data(migrated) if a["level"] == "ERROR"])

    if inplace:
        backup = path.with_suffix(path.suffix + ".bak")
        if not backup.exists():
            path.replace(backup)
        with path.open("w", encoding="utf-8") as f:
            json.dump(migrated, f, indent=2)
    return before, after


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate battle logs to audit contract")
    parser.add_argument("target", type=Path, help="JSON file or directory containing battle logs")
    parser.add_argument("--dry-run", action="store_true", help="Do not write changes")
    args = parser.parse_args()

    if args.target.is_file():
        files = [args.target]
    else:
        files = sorted(args.target.glob("*.json"))

    total_before = 0
    total_after = 0

    for f in files:
        with f.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        before = len([a for a in validate_log_data(data) if a["level"] == "ERROR"])

        migrated = migrate_log_data(data)
        after = len([a for a in validate_log_data(migrated) if a["level"] == "ERROR"])

        if not args.dry_run:
            backup = f.with_suffix(f.suffix + ".bak")
            if not backup.exists():
                f.replace(backup)
            with f.open("w", encoding="utf-8") as out:
                json.dump(migrated, out, indent=2)

        total_before += before
        total_after += after
        mode = "DRY" if args.dry_run else "MIGRATED"
        print(f"[{mode}] {f.name}: errors {before} -> {after}")

    print(f"Total errors: {total_before} -> {total_after}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
