"""
Battle Logger - Records individual battle logs for debugging and analysis.

Creates timestamped log files for each battle with detailed action records.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict

_ANSI_RE = re.compile(r'\033\[[0-9;]*m')


LOGS_DIR = Path(__file__).parent.parent / "logs" / "battles"


@dataclass
class BattleLogEntry:
    """A single entry in the battle log."""
    turn: int
    action_type: str  # "move", "switch", "damage", "status", "effect", "info"
    pokemon: str
    pokemon_side: Optional[str] = None
    target: Optional[str] = None
    target_side: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    message: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class BattleLogger:
    """
    Logger for recording individual battle events.

    Creates a detailed log file for each battle that can be used
    for debugging and analysis.
    """
    _SIDE_COLORS = {
        "P1": "\033[96m",  # cyan
        "P2": "\033[91m",  # red
    }
    _COLOR_RESET = "\033[0m"

    def __init__(self, battle_id: Optional[str] = None, enabled: bool = True,
                 log_dir: Optional[Path] = None):
        """
        Initialize battle logger.

        Args:
            battle_id: Optional custom battle ID. If None, uses timestamp.
            enabled: If False, logging is disabled (no-op).
            log_dir: Optional custom directory for log files. Defaults to LOGS_DIR.
        """
        self.enabled = enabled
        if not enabled:
            return

        # Create logs directory
        output_dir = log_dir or LOGS_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate battle ID with microseconds to avoid collisions in batch mode
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        self.battle_id = battle_id or f"battle_{timestamp}"

        # Log file path
        self.log_file = output_dir / f"{self.battle_id}.log"
        self.json_file = output_dir / f"{self.battle_id}.json"

        # In-memory log entries
        self.entries: List[BattleLogEntry] = []
        self.metadata: Dict[str, Any] = {
            "battle_id": self.battle_id,
            "start_time": timestamp,
            "team1": [],
            "team2": [],
        }

        self._current_turn = 0
        self._file_handle = open(self.log_file, "w", encoding="utf-8")

        # Write header
        self._write_line("=" * 60)
        self._write_line(f"POKEMON GEN 1 BATTLE LOG")
        self._write_line(f"Battle ID: {self.battle_id}")
        self._write_line(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self._write_line("=" * 60)
        self._write_line("")

    def _write_line(self, line: str):
        """Write a line to the log file, stripping ANSI color codes."""
        if self.enabled and self._file_handle:
            self._file_handle.write(_ANSI_RE.sub('', line) + "\n")
            self._file_handle.flush()

    def _format_actor(self, name: str, side: Optional[str]) -> str:
        """Format actor labels with side prefix and optional ANSI color."""
        if not side:
            return name
        prefix = f"[{side}]"
        color = self._SIDE_COLORS.get(side, "")
        if color:
            prefix = f"{color}{prefix}{self._COLOR_RESET}"
        return f"{prefix} {name}"

    def set_teams(self, team1_pokemon: List[str], team2_pokemon: List[str],
                  team1_name: str = "Team 1", team2_name: str = "Team 2"):
        """Record the teams at battle start."""
        if not self.enabled:
            return

        self.metadata["team1"] = team1_pokemon
        self.metadata["team2"] = team2_pokemon
        self.metadata["team1_name"] = team1_name
        self.metadata["team2_name"] = team2_name

        self._write_line(f"{team1_name}: {', '.join(team1_pokemon)}")
        self._write_line(f"{team2_name}: {', '.join(team2_pokemon)}")
        self._write_line("")
        self._write_line("-" * 60)

    def start_turn(self, turn_number: int):
        """Mark the start of a new turn."""
        if not self.enabled:
            return

        self._current_turn = turn_number
        self.entries.append(
            BattleLogEntry(
                turn=self._current_turn,
                action_type="turn_start",
                pokemon="",
                message=f"TURN {turn_number} START",
            )
        )
        self._write_line("")
        self._write_line(f"=== TURN {turn_number} ===")

    def end_turn(self):
        """Mark end of current turn (audit marker)."""
        if not self.enabled:
            return

        self.entries.append(
            BattleLogEntry(
                turn=self._current_turn,
                action_type="turn_end",
                pokemon="",
                message=f"TURN {self._current_turn} END",
            )
        )

    def log_state_snapshot(self, pokemon1, pokemon2,
                           pokemon1_side: Optional[str] = None,
                           pokemon2_side: Optional[str] = None):
        """Record full battle state at turn boundary for auditability."""
        if not self.enabled:
            return

        def _snapshot(p):
            from models.enums import Status
            snapshot = {
                "name": p.name,
                "hp": p.current_hp,
                "max_hp": p.max_hp,
                "status": p.status.value if p.status and p.status != Status.NONE else "none",
            }
            # Only include non-zero stat stages
            stages = {}
            for stat, val in p.stat_stages.items():
                if val != 0:
                    stages[stat.value if hasattr(stat, 'value') else str(stat)] = val
            if stages:
                snapshot["stat_stages"] = stages
            # Volatile effects (only include when active)
            if getattr(p, 'confusion_turns', 0) > 0:
                snapshot["confusion_turns"] = p.confusion_turns
            if getattr(p, 'is_seeded', False):
                snapshot["is_seeded"] = True
            if getattr(p, 'has_reflect', False):
                snapshot["has_reflect"] = True
                snapshot["reflect_turns"] = getattr(p, 'reflect_turns', 0)
            if getattr(p, 'has_light_screen', False):
                snapshot["has_light_screen"] = True
                snapshot["light_screen_turns"] = getattr(p, 'light_screen_turns', 0)
            if getattr(p, 'has_mist', False):
                snapshot["has_mist"] = True
                snapshot["mist_turns"] = getattr(p, 'mist_turns', 0)
            if getattr(p, 'substitute_hp', 0) > 0:
                snapshot["substitute_hp"] = p.substitute_hp
            if getattr(p, 'is_trapped', False):
                snapshot["is_trapped"] = True
                snapshot["trap_turns"] = getattr(p, 'trap_turns', 0)
            if getattr(p, 'is_charging', False):
                snapshot["is_charging"] = True
            if getattr(p, 'must_recharge', False):
                snapshot["must_recharge"] = True
            if getattr(p, 'disabled_move', None):
                snapshot["disabled_move"] = p.disabled_move
                snapshot["disable_turns"] = getattr(p, 'disable_turns', 0)
            if getattr(p, 'focus_energy', False):
                snapshot["focus_energy"] = True
            if getattr(p, 'is_raging', False):
                snapshot["is_raging"] = True
            if getattr(p, 'is_transformed', False):
                snapshot["is_transformed"] = True
            return snapshot

        p1_snap = _snapshot(pokemon1)
        p2_snap = _snapshot(pokemon2)

        entry = BattleLogEntry(
            turn=self._current_turn,
            action_type="state_snapshot",
            pokemon="",
            details={
                "p1": p1_snap,
                "p2": p2_snap,
            }
        )
        self.entries.append(entry)

        # Compact log line
        def _fmt(s):
            hp_pct = f"{s['hp']}/{s['max_hp']}"
            parts = [f"{s['name']}:{hp_pct}"]
            if s.get("status", "none") != "none":
                parts.append(s["status"])
            stages = s.get("stat_stages", {})
            if stages:
                stage_str = ",".join(f"{k}:{'+' if v > 0 else ''}{v}" for k, v in stages.items())
                parts.append(f"[{stage_str}]")
            return " ".join(parts)

        self._write_line(f"  State: P1={_fmt(p1_snap)} | P2={_fmt(p2_snap)}")

    def log_turn_order(self, first_name: str, second_name: str,
                       first_speed: int, second_speed: int,
                       first_side: Optional[str] = None,
                       second_side: Optional[str] = None,
                       reason: str = "speed"):
        """Record why one Pokemon acts before another."""
        if not self.enabled:
            return

        entry = BattleLogEntry(
            turn=self._current_turn,
            action_type="turn_order",
            pokemon=first_name,
            pokemon_side=first_side,
            target=second_name,
            target_side=second_side,
            details={
                "first_speed": first_speed,
                "second_speed": second_speed,
                "reason": reason,
            }
        )
        self.entries.append(entry)

        reason_str = {"speed": "faster", "speed_tie_random": "speed tie (random)", "switch_priority": "switch priority"}.get(reason, reason)
        self._write_line(f"  Order: {first_name}(spd:{first_speed}) > {second_name}(spd:{second_speed}) [{reason_str}]")

    def log_move(self, pokemon: str, move: str, target: str,
                 damage: int = 0, is_critical: bool = False,
                 effectiveness: float = 1.0, message: str = "",
                 pokemon_side: Optional[str] = None,
                 target_side: Optional[str] = None,
                 move_result: str = "resolved",
                 extra_details: Optional[Dict[str, Any]] = None):
        """Log a move being used."""
        if not self.enabled:
            return

        details = {
            "move": move,
            "damage": damage,
            "critical": is_critical,
            "effectiveness": effectiveness,
            "result": move_result,
        }
        if extra_details:
            details.update(extra_details)

        entry = BattleLogEntry(
            turn=self._current_turn,
            action_type="move",
            pokemon=pokemon,
            pokemon_side=pokemon_side,
            target=target,
            target_side=target_side,
            details=details,
            message=message
        )
        self.entries.append(entry)

        # Write to file
        actor_label = self._format_actor(pokemon, pokemon_side)
        target_label = self._format_actor(target, target_side) if target else target
        line = f"{actor_label} used {move}"
        if target and target != pokemon:
            line += f" on {target_label}"
        self._write_line(line)

        if damage > 0:
            crit_str = " (CRITICAL!)" if is_critical else ""
            eff_str = ""
            if effectiveness > 1:
                eff_str = " (Super effective!)"
            elif effectiveness < 1 and effectiveness > 0:
                eff_str = " (Not very effective...)"
            elif effectiveness == 0:
                eff_str = " (No effect)"
            # Compact damage breakdown line
            bd = extra_details.get("damage_breakdown") if extra_details else None
            cap_str = ""
            if bd and damage < bd.get("final_damage", damage):
                cap_str = f" (capped from {bd['final_damage']})"
            self._write_line(f"  -> {damage} damage{crit_str}{eff_str}{cap_str}")
            if bd:
                parts = [f"pwr:{bd['move_power']}"]
                parts.append(f"atk:{bd['attack_stat']}")
                parts.append(f"def:{bd['defense_stat']}")
                if bd.get("stab", 1.0) != 1.0:
                    parts.append(f"STAB:{bd['stab']}x")
                if bd.get("effectiveness", 1.0) != 1.0:
                    parts.append(f"eff:{bd['effectiveness']}x")
                if bd.get("is_critical"):
                    parts.append("CRIT")
                if bd.get("burn_modifier", 1.0) != 1.0:
                    parts.append("BURN")
                parts.append(f"roll:{bd['random_roll']}")
                self._write_line(f"     ({', '.join(parts)})")

        if message:
            self._write_line(f"  {message}")
        if move_result != "resolved":
            self._write_line(f"  -> result: {move_result}")

    def log_status(self, pokemon: str, status: str, applied: bool = True,
                   source: str = "", pokemon_side: Optional[str] = None):
        """Log a status condition change."""
        if not self.enabled:
            return

        entry = BattleLogEntry(
            turn=self._current_turn,
            action_type="status",
            pokemon=pokemon,
            pokemon_side=pokemon_side,
            details={
                "status": status,
                "applied": applied,
                "source": source,
            }
        )
        self.entries.append(entry)

        actor_label = self._format_actor(pokemon, pokemon_side)
        if applied:
            self._write_line(f"  {actor_label} is now {status}")
        else:
            self._write_line(f"  {actor_label}'s {status} wore off")

    def log_stat_change(self, pokemon: str, stat: str, stages: int):
        """Log a stat stage change."""
        if not self.enabled:
            return

        entry = BattleLogEntry(
            turn=self._current_turn,
            action_type="stat_change",
            pokemon=pokemon,
            details={"stat": stat, "stages": stages}
        )
        self.entries.append(entry)

        direction = "rose" if stages > 0 else "fell"
        amount = "sharply " if abs(stages) >= 2 else ""
        self._write_line(f"  {pokemon}'s {stat} {amount}{direction}!")

    def log_move_prevented(self, pokemon: str, move: str, reason: str,
                           pokemon_side: Optional[str] = None,
                           extra_details: Optional[Dict[str, Any]] = None):
        """Log a move that was prevented from executing, with the specific reason."""
        if not self.enabled:
            return

        details = {"move": move, "reason": reason}
        if extra_details:
            details.update(extra_details)

        entry = BattleLogEntry(
            turn=self._current_turn,
            action_type="move_prevented",
            pokemon=pokemon,
            pokemon_side=pokemon_side,
            details=details,
        )
        self.entries.append(entry)

        reason_msgs = {
            "frozen": "is frozen solid",
            "asleep": "is fast asleep",
            "sleep_wake": "woke up but can't act (Gen 1)",
            "paralyzed": "is fully paralyzed",
            "confused_self_hit": "hurt itself in confusion",
            "disabled": f"{move} is disabled",
            "recharging": "must recharge",
            "trapped": "is trapped and can't move",
            "semi_invulnerable": "target is out of reach",
            "type_immune": "has no effect (type immunity)",
        }
        msg = reason_msgs.get(reason, reason)
        actor_label = self._format_actor(pokemon, pokemon_side)
        self._write_line(f"  {actor_label} {msg}")

    def log_switch(self, team: str, pokemon_out: str, pokemon_in: str,
                   pokemon_side: Optional[str] = None):
        """Log a Pokemon switch."""
        if not self.enabled:
            return

        entry = BattleLogEntry(
            turn=self._current_turn,
            action_type="switch",
            pokemon=pokemon_in,
            pokemon_side=pokemon_side,
            details={"pokemon_out": pokemon_out, "team": team}
        )
        self.entries.append(entry)

        out_label = self._format_actor(pokemon_out, pokemon_side)
        in_label = self._format_actor(pokemon_in, pokemon_side)
        self._write_line(f"{team}: {out_label} switched out, {in_label} sent in")

    def log_faint(self, pokemon: str, pokemon_side: Optional[str] = None):
        """Log a Pokemon fainting."""
        if not self.enabled:
            return

        entry = BattleLogEntry(
            turn=self._current_turn,
            action_type="faint",
            pokemon=pokemon,
            pokemon_side=pokemon_side,
        )
        self.entries.append(entry)

        actor_label = self._format_actor(pokemon, pokemon_side)
        self._write_line(f"  {actor_label} fainted!")

    def log_hp(self, pokemon: str, current_hp: int, max_hp: int,
               pokemon_side: Optional[str] = None):
        """Log HP status."""
        if not self.enabled:
            return

        entry = BattleLogEntry(
            turn=self._current_turn,
            action_type="hp",
            pokemon=pokemon,
            pokemon_side=pokemon_side,
            details={"current_hp": current_hp, "max_hp": max_hp}
        )
        self.entries.append(entry)

        pct = (current_hp / max_hp * 100) if max_hp > 0 else 0
        actor_label = self._format_actor(pokemon, pokemon_side)
        self._write_line(f"  {actor_label}: {current_hp}/{max_hp} HP ({pct:.1f}%)")

    def log_effect(self, effect: str, pokemon: str = "", damage: int = 0,
                   message: str = "", pokemon_side: Optional[str] = None):
        """Log a special effect (Leech Seed, weather, etc.)."""
        if not self.enabled:
            return

        entry = BattleLogEntry(
            turn=self._current_turn,
            action_type="effect",
            pokemon=pokemon,
            pokemon_side=pokemon_side,
            details={"effect": effect, "damage": damage},
            message=message
        )
        self.entries.append(entry)

        actor_label = self._format_actor(pokemon, pokemon_side) if pokemon else pokemon
        if message:
            self._write_line(f"  {message}")
        elif damage > 0:
            self._write_line(f"  {actor_label} took {damage} damage from {effect}")

    def log_info(self, message: str):
        """Log general information."""
        if not self.enabled:
            return

        entry = BattleLogEntry(
            turn=self._current_turn,
            action_type="info",
            pokemon="",
            message=message
        )
        self.entries.append(entry)

        self._write_line(message)

    def log_miss(self, pokemon: str, move: str, pokemon_side: Optional[str] = None):
        """Log a move missing."""
        if not self.enabled:
            return

        entry = BattleLogEntry(
            turn=self._current_turn,
            action_type="miss",
            pokemon=pokemon,
            pokemon_side=pokemon_side,
            details={"move": move}
        )
        self.entries.append(entry)

        actor_label = self._format_actor(pokemon, pokemon_side)
        self._write_line(f"  {actor_label}'s {move} missed!")

    def _compute_summary(self) -> Dict[str, Any]:
        """Compute per-Pokemon aggregate stats from log entries."""
        pokemon_stats: Dict[str, Dict[str, Any]] = {}

        def _ensure(name: str):
            if name and name not in pokemon_stats:
                pokemon_stats[name] = {
                    "damage_dealt": 0,
                    "damage_taken": 0,
                    "residual_damage": 0,
                    "moves_used": 0,
                    "crits_landed": 0,
                    "times_fainted": 0,
                    "turns_active": 0,
                }

        # Track which Pokemon are active per turn for turns_active
        active_per_turn: Dict[int, set] = {}

        for e in self.entries:
            atype = e.action_type
            poke = e.pokemon
            target = e.target
            details = e.details

            if atype == "move":
                _ensure(poke)
                pokemon_stats[poke]["moves_used"] += 1
                dmg = details.get("damage", 0)
                if dmg > 0:
                    pokemon_stats[poke]["damage_dealt"] += dmg
                    if target:
                        _ensure(target)
                        pokemon_stats[target]["damage_taken"] += dmg
                if details.get("critical"):
                    pokemon_stats[poke]["crits_landed"] += 1

            elif atype == "miss":
                _ensure(poke)
                pokemon_stats[poke]["moves_used"] += 1

            elif atype == "effect":
                dmg = details.get("damage", 0)
                if dmg > 0 and poke:
                    _ensure(poke)
                    pokemon_stats[poke]["residual_damage"] += dmg

            elif atype == "faint":
                if poke:
                    _ensure(poke)
                    pokemon_stats[poke]["times_fainted"] += 1

            elif atype == "state_snapshot":
                p1 = details.get("p1", {})
                p2 = details.get("p2", {})
                turn = e.turn
                if p1.get("name"):
                    _ensure(p1["name"])
                    active_per_turn.setdefault(turn, set()).add(p1["name"])
                if p2.get("name"):
                    _ensure(p2["name"])
                    active_per_turn.setdefault(turn, set()).add(p2["name"])

        for _turn, names in active_per_turn.items():
            for name in names:
                if name in pokemon_stats:
                    pokemon_stats[name]["turns_active"] += 1

        return {"per_pokemon": pokemon_stats}

    def end_battle(self, winner: Optional[str] = None, reason: str = ""):
        """Mark the end of the battle and save the log."""
        if not self.enabled:
            return

        summary = self._compute_summary()
        self.metadata["end_time"] = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.metadata["winner"] = winner
        self.metadata["total_turns"] = self._current_turn
        self.metadata["reason"] = reason
        self.metadata["summary"] = summary

        self._write_line("")
        self._write_line("=" * 60)
        if winner:
            self._write_line(f"WINNER: {winner}")
        else:
            self._write_line("RESULT: Draw")
        self._write_line(f"Total turns: {self._current_turn}")

        # Write summary table
        per_pokemon = summary.get("per_pokemon", {})
        if per_pokemon:
            self._write_line("")
            self._write_line("--- Battle Summary ---")
            self._write_line(f"{'Pokemon':<16} {'Dealt':>6} {'Taken':>6} {'Resid':>6} {'Moves':>5} {'Crits':>5} {'KOs':>3} {'Turns':>5}")
            self._write_line("-" * 68)
            for name, stats in per_pokemon.items():
                self._write_line(
                    f"{name:<16} {stats['damage_dealt']:>6} {stats['damage_taken']:>6} "
                    f"{stats['residual_damage']:>6} {stats['moves_used']:>5} "
                    f"{stats['crits_landed']:>5} {stats['times_fainted']:>3} "
                    f"{stats['turns_active']:>5}"
                )

        self._write_line("")
        self._write_line(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self._write_line("=" * 60)

        # Close file
        if self._file_handle:
            self._file_handle.close()
            self._file_handle = None

        # Save JSON version
        self._save_json()

        print(f"\nBattle log saved to: {self.log_file}")

    def _save_json(self):
        """Save the battle log as JSON for programmatic analysis."""
        data = {
            "metadata": self.metadata,
            "entries": [e.to_dict() for e in self.entries]
        }
        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def __del__(self):
        """Ensure file is closed on deletion."""
        if hasattr(self, '_file_handle') and self._file_handle:
            self._file_handle.close()


# Global logger instance for the current battle
_current_logger: Optional[BattleLogger] = None


def get_battle_logger() -> Optional[BattleLogger]:
    """Get the current battle logger."""
    return _current_logger


def start_battle_log(battle_id: Optional[str] = None, enabled: bool = True,
                     log_dir: Optional[Path] = None) -> BattleLogger:
    """Start logging a new battle."""
    global _current_logger
    _current_logger = BattleLogger(battle_id, enabled, log_dir=log_dir)
    return _current_logger


def end_battle_log(winner: Optional[str] = None, reason: str = ""):
    """End the current battle log."""
    global _current_logger
    if _current_logger:
        _current_logger.end_battle(winner, reason)
        _current_logger = None
