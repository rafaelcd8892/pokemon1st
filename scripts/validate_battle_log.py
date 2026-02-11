#!/usr/bin/env python3
"""Validate battle log JSON against audit invariants."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

SELF_TARGET_MOVES = {
    "Agility",
    "Barrier",
    "Amnesia",
    "Reflect",
    "Light Screen",
    "Recover",
    "Rest",
    "Soft Boiled",
    "Substitute",
    "Swords Dance",
    "Withdraw",
    "Harden",
    "Growth",
    "Meditate",
    "Minimize",
}


def _group_by_turn(entries: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
    by_turn: Dict[int, List[Dict[str, Any]]] = {}
    for e in entries:
        by_turn.setdefault(int(e.get("turn", 0)), []).append(e)
    return by_turn


def validate_log_data(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    anomalies: List[Dict[str, Any]] = []
    entries = data.get("entries", [])
    by_turn = _group_by_turn(entries)

    def add(level: str, turn: int, code: str, message: str):
        anomalies.append({"level": level, "turn": turn, "code": code, "message": message})

    # Invariant: turn boundaries present for active turns
    for turn, turn_entries in sorted(by_turn.items()):
        if turn == 0:
            continue
        types = {e.get("action_type") for e in turn_entries}
        if "turn_start" not in types:
            add("ERROR", turn, "missing_turn_start", "Turn has no turn_start marker")
        if "turn_end" not in types:
            add("ERROR", turn, "missing_turn_end", "Turn has no turn_end marker")

    # Invariant: hp range valid
    for e in entries:
        if e.get("action_type") != "hp":
            continue
        turn = int(e.get("turn", 0))
        details = e.get("details", {})
        cur = details.get("current_hp")
        max_hp = details.get("max_hp")
        if cur is None or max_hp is None:
            add("ERROR", turn, "hp_missing_fields", "HP event missing current_hp/max_hp")
            continue
        if cur < 0 or cur > max_hp:
            add("ERROR", turn, "hp_out_of_range", f"HP out of range: {cur}/{max_hp}")

    # Invariant: self-target semantic consistency
    for e in entries:
        if e.get("action_type") != "move":
            continue
        turn = int(e.get("turn", 0))
        details = e.get("details", {})
        move = details.get("move")
        actor = e.get("pokemon")
        target = e.get("target")
        if move in SELF_TARGET_MOVES and target and target != actor:
            add(
                "ERROR",
                turn,
                "invalid_self_target",
                f"{move} should target self ({actor}) but targets {target}",
            )

    # Invariant: switch cannot send in already fainted Pokemon
    for turn, turn_entries in sorted(by_turn.items()):
        for i, e in enumerate(turn_entries):
            if e.get("action_type") != "switch":
                continue
            p = e.get("pokemon")
            first_hp = None
            for next_e in turn_entries[i + 1 :]:
                if next_e.get("action_type") == "hp" and next_e.get("pokemon") == p:
                    first_hp = next_e
                    break
            if first_hp is None:
                add("WARN", turn, "switch_missing_hp_snapshot", f"Switch has no immediate HP snapshot: {p}")
                continue
            cur = first_hp.get("details", {}).get("current_hp")
            if cur is not None and cur <= 0:
                add("ERROR", turn, "switch_into_fainted", f"Switch sent in fainted Pokemon: {p}")

    # Invariant: duplicate move events in same turn are suspicious.
    for turn, turn_entries in sorted(by_turn.items()):
        seen: set[tuple[Any, ...]] = set()
        for e in turn_entries:
            if e.get("action_type") != "move":
                continue
            details = e.get("details", {})
            key = (
                e.get("pokemon"),
                e.get("pokemon_side"),
                e.get("target"),
                e.get("target_side"),
                details.get("move"),
                details.get("damage"),
                details.get("critical"),
                details.get("effectiveness"),
                details.get("result", "resolved"),
            )
            if key in seen:
                add("ERROR", turn, "duplicate_move_event", f"Duplicated move event: {details.get('move')} by {e.get('pokemon')}")
                continue
            seen.add(key)

    # Invariant: faint should have causal event in same turn
    for turn, turn_entries in sorted(by_turn.items()):
        fainted = [e.get("pokemon") for e in turn_entries if e.get("action_type") == "faint"]
        if not fainted:
            continue

        for p in fainted:
            causal = False
            for e in turn_entries:
                et = e.get("action_type")
                if et == "move" and e.get("target") == p and e.get("details", {}).get("damage", 0) > 0:
                    causal = True
                    break
                if et == "effect" and e.get("pokemon") == p and e.get("details", {}).get("damage", 0) > 0:
                    causal = True
                    break
                if et == "move" and e.get("pokemon") == p and e.get("details", {}).get("self_faint") is True:
                    causal = True
                    break
            if not causal:
                add("ERROR", turn, "faint_without_cause", f"{p} fainted without causal damage event in same turn")

    return anomalies


def validate_log_file(path: Path) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data, validate_log_data(data)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate battle log JSON audit invariants")
    parser.add_argument("log_json", type=Path, help="Path to battle log .json file")
    args = parser.parse_args()

    data, anomalies = validate_log_file(args.log_json)
    battle_id = data.get("metadata", {}).get("battle_id", args.log_json.name)

    print(f"Battle: {battle_id}")
    if not anomalies:
        print("No anomalies found.")
        return 0

    errors = 0
    for a in anomalies:
        print(f"[{a['level']}] turn={a['turn']} code={a['code']} :: {a['message']}")
        if a["level"] == "ERROR":
            errors += 1

    print(f"Total anomalies: {len(anomalies)} (errors: {errors})")
    return 1 if errors > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
