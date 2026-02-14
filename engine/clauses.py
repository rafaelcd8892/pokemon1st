"""
Battle clause enforcement for Pokemon Gen 1.

Pure functions that check whether moves or effects are allowed
under active battle clauses. No side effects — fully testable.

Enforcement points:
- OHKO/Evasion clauses: checked at move selection time (before execution)
- Sleep/Freeze clauses: checked at status application time (move still deals damage)
"""

from models.enums import Status

# Moves banned by OHKO Clause
OHKO_MOVES = {"Fissure", "Guillotine", "Horn Drill"}

# Moves banned by Evasion Clause
EVASION_MOVES = {"Double Team", "Minimize"}


def check_sleep_clause(defender_team: list, clauses) -> tuple[bool, str]:
    """
    Check if Sleep Clause allows putting another Pokemon to sleep.

    Sleep Clause: Only one opponent Pokemon may be asleep (from moves) at a time.
    Self-induced sleep (Rest) does not count.

    Args:
        defender_team: List of Pokemon on the defending side
        clauses: BattleClauses instance

    Returns:
        (allowed, reason) — allowed=True means the sleep can proceed
    """
    if not clauses.sleep_clause:
        return True, ""

    for pokemon in defender_team:
        if pokemon.status == Status.SLEEP and pokemon.is_alive():
            return False, "Sleep Clause: another Pokemon on the team is already asleep"

    return True, ""


def check_freeze_clause(defender_team: list, clauses) -> tuple[bool, str]:
    """
    Check if Freeze Clause allows freezing another Pokemon.

    Freeze Clause: Only one opponent Pokemon may be frozen at a time.

    Args:
        defender_team: List of Pokemon on the defending side
        clauses: BattleClauses instance

    Returns:
        (allowed, reason) — allowed=True means the freeze can proceed
    """
    if not clauses.freeze_clause:
        return True, ""

    for pokemon in defender_team:
        if pokemon.status == Status.FREEZE and pokemon.is_alive():
            return False, "Freeze Clause: another Pokemon on the team is already frozen"

    return True, ""


def check_ohko_clause(move, clauses) -> tuple[bool, str]:
    """
    Check if OHKO Clause allows using this move.

    OHKO Clause: Bans Fissure, Guillotine, and Horn Drill.

    Args:
        move: The Move being used
        clauses: BattleClauses instance

    Returns:
        (allowed, reason) — allowed=True means the move can proceed
    """
    if not clauses.ohko_clause:
        return True, ""

    if move.name in OHKO_MOVES:
        return False, f"OHKO Clause: {move.name} is banned"

    return True, ""


def check_evasion_clause(move, clauses) -> tuple[bool, str]:
    """
    Check if Evasion Clause allows using this move.

    Evasion Clause: Bans Double Team and Minimize.

    Args:
        move: The Move being used
        clauses: BattleClauses instance

    Returns:
        (allowed, reason) — allowed=True means the move can proceed
    """
    if not clauses.evasion_clause:
        return True, ""

    if move.name in EVASION_MOVES:
        return False, f"Evasion Clause: {move.name} is banned"

    return True, ""


def check_move_clauses(move, clauses) -> tuple[bool, str]:
    """
    Check all move-level clauses (OHKO + Evasion).

    These clauses block the move entirely before execution.

    Args:
        move: The Move being used
        clauses: BattleClauses instance

    Returns:
        (allowed, reason) — allowed=True means the move can proceed
    """
    allowed, reason = check_ohko_clause(move, clauses)
    if not allowed:
        return allowed, reason

    return check_evasion_clause(move, clauses)


def check_status_clause(status_effect, defender_team: list, clauses) -> tuple[bool, str]:
    """
    Check if a status effect is allowed by clauses (Sleep/Freeze).

    These clauses allow the move to execute and deal damage,
    but prevent the secondary status effect from being applied.

    Args:
        status_effect: The Status enum being applied
        defender_team: List of Pokemon on the defending side
        clauses: BattleClauses instance

    Returns:
        (allowed, reason) — allowed=True means the status can be applied
    """
    if status_effect == Status.SLEEP:
        return check_sleep_clause(defender_team, clauses)

    if status_effect == Status.FREEZE:
        return check_freeze_clause(defender_team, clauses)

    return True, ""


def is_move_banned_by_clauses(move, clauses) -> bool:
    """
    Quick check if a move is entirely banned by clauses.

    Used by AI move filtering to exclude banned moves from selection.

    Args:
        move: The Move to check
        clauses: BattleClauses instance

    Returns:
        True if the move is banned
    """
    allowed, _ = check_move_clauses(move, clauses)
    return not allowed
