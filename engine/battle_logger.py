"""
Battle Logger - Records individual battle logs for debugging and analysis.

Creates timestamped log files for each battle with detailed action records.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict


LOGS_DIR = Path(__file__).parent.parent / "logs" / "battles"


@dataclass
class BattleLogEntry:
    """A single entry in the battle log."""
    turn: int
    action_type: str  # "move", "switch", "damage", "status", "effect", "info"
    pokemon: str
    target: Optional[str] = None
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

    def __init__(self, battle_id: Optional[str] = None, enabled: bool = True):
        """
        Initialize battle logger.

        Args:
            battle_id: Optional custom battle ID. If None, uses timestamp.
            enabled: If False, logging is disabled (no-op).
        """
        self.enabled = enabled
        if not enabled:
            return

        # Create logs directory
        LOGS_DIR.mkdir(parents=True, exist_ok=True)

        # Generate battle ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.battle_id = battle_id or f"battle_{timestamp}"

        # Log file path
        self.log_file = LOGS_DIR / f"{self.battle_id}.log"
        self.json_file = LOGS_DIR / f"{self.battle_id}.json"

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
        """Write a line to the log file."""
        if self.enabled and self._file_handle:
            self._file_handle.write(line + "\n")
            self._file_handle.flush()

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
        self._write_line("")
        self._write_line(f"=== TURN {turn_number} ===")

    def log_move(self, pokemon: str, move: str, target: str,
                 damage: int = 0, is_critical: bool = False,
                 effectiveness: float = 1.0, message: str = ""):
        """Log a move being used."""
        if not self.enabled:
            return

        entry = BattleLogEntry(
            turn=self._current_turn,
            action_type="move",
            pokemon=pokemon,
            target=target,
            details={
                "move": move,
                "damage": damage,
                "critical": is_critical,
                "effectiveness": effectiveness,
            },
            message=message
        )
        self.entries.append(entry)

        # Write to file
        line = f"{pokemon} used {move}"
        if target and target != pokemon:
            line += f" on {target}"
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
            self._write_line(f"  -> {damage} damage{crit_str}{eff_str}")

        if message:
            self._write_line(f"  {message}")

    def log_status(self, pokemon: str, status: str, applied: bool = True,
                   source: str = ""):
        """Log a status condition change."""
        if not self.enabled:
            return

        entry = BattleLogEntry(
            turn=self._current_turn,
            action_type="status",
            pokemon=pokemon,
            details={
                "status": status,
                "applied": applied,
                "source": source,
            }
        )
        self.entries.append(entry)

        if applied:
            self._write_line(f"  {pokemon} is now {status}")
        else:
            self._write_line(f"  {pokemon}'s {status} wore off")

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

    def log_switch(self, team: str, pokemon_out: str, pokemon_in: str):
        """Log a Pokemon switch."""
        if not self.enabled:
            return

        entry = BattleLogEntry(
            turn=self._current_turn,
            action_type="switch",
            pokemon=pokemon_in,
            details={"pokemon_out": pokemon_out, "team": team}
        )
        self.entries.append(entry)

        self._write_line(f"{team}: {pokemon_out} switched out, {pokemon_in} sent in")

    def log_faint(self, pokemon: str):
        """Log a Pokemon fainting."""
        if not self.enabled:
            return

        entry = BattleLogEntry(
            turn=self._current_turn,
            action_type="faint",
            pokemon=pokemon
        )
        self.entries.append(entry)

        self._write_line(f"  {pokemon} fainted!")

    def log_hp(self, pokemon: str, current_hp: int, max_hp: int):
        """Log HP status."""
        if not self.enabled:
            return

        entry = BattleLogEntry(
            turn=self._current_turn,
            action_type="hp",
            pokemon=pokemon,
            details={"current_hp": current_hp, "max_hp": max_hp}
        )
        self.entries.append(entry)

        pct = (current_hp / max_hp * 100) if max_hp > 0 else 0
        self._write_line(f"  {pokemon}: {current_hp}/{max_hp} HP ({pct:.1f}%)")

    def log_effect(self, effect: str, pokemon: str = "", damage: int = 0,
                   message: str = ""):
        """Log a special effect (Leech Seed, weather, etc.)."""
        if not self.enabled:
            return

        entry = BattleLogEntry(
            turn=self._current_turn,
            action_type="effect",
            pokemon=pokemon,
            details={"effect": effect, "damage": damage},
            message=message
        )
        self.entries.append(entry)

        if message:
            self._write_line(f"  {message}")
        elif damage > 0:
            self._write_line(f"  {pokemon} took {damage} damage from {effect}")

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

    def log_miss(self, pokemon: str, move: str):
        """Log a move missing."""
        if not self.enabled:
            return

        entry = BattleLogEntry(
            turn=self._current_turn,
            action_type="miss",
            pokemon=pokemon,
            details={"move": move}
        )
        self.entries.append(entry)

        self._write_line(f"  {pokemon}'s {move} missed!")

    def end_battle(self, winner: Optional[str] = None, reason: str = ""):
        """Mark the end of the battle and save the log."""
        if not self.enabled:
            return

        self.metadata["end_time"] = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.metadata["winner"] = winner
        self.metadata["total_turns"] = self._current_turn
        self.metadata["reason"] = reason

        self._write_line("")
        self._write_line("=" * 60)
        if winner:
            self._write_line(f"WINNER: {winner}")
        else:
            self._write_line("RESULT: Draw")
        self._write_line(f"Total turns: {self._current_turn}")
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


def start_battle_log(battle_id: Optional[str] = None, enabled: bool = True) -> BattleLogger:
    """Start logging a new battle."""
    global _current_logger
    _current_logger = BattleLogger(battle_id, enabled)
    return _current_logger


def end_battle_log(winner: Optional[str] = None, reason: str = ""):
    """End the current battle log."""
    global _current_logger
    if _current_logger:
        _current_logger.end_battle(winner, reason)
        _current_logger = None
