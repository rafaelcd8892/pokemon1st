"""Pure evaluation functions for AI move / switch scoring.

All functions here are deterministic — no RNG calls, no side effects.
They use the average random roll (236/255) and never consider crits,
so AI evaluation does not consume RNG state.

Higher-difficulty AIs compose these building blocks to make decisions.
"""

from dataclasses import dataclass, field
from typing import Optional

from models.pokemon import Pokemon
from models.move import Move
from models.enums import MoveCategory, Status, Type
from engine.type_chart import get_effectiveness
from engine.gen_mechanics import is_physical
from engine.stat_modifiers import get_modified_attack, get_modified_defense
from engine.damage import calculate_base_damage, get_stab_multiplier
from engine.stat_modifiers import get_modified_speed
from engine.move_effects import (
    FIXED_DAMAGE_MOVES,
    LEVEL_DAMAGE_MOVES,
    OHKO_MOVES,
    SELF_DESTRUCT_MOVES,
    TWO_TURN_MOVES,
    RECOVERY_MOVES,
    HP_DRAIN_MOVES,
)

# Average random roll in Gen 1: (217 + 255) / 2 ≈ 236
_AVG_ROLL = 236
_ROLL_DIVISOR = 255


@dataclass
class MoveScore:
    """Result of evaluating a single move against a target."""
    move: Move
    estimated_damage: int = 0
    effectiveness: float = 1.0
    is_immune: bool = False
    is_status: bool = False
    is_self_destruct: bool = False
    is_two_turn: bool = False
    is_recovery: bool = False
    is_drain: bool = False
    has_status_effect: bool = False
    # Composite score used for ranking (higher = better)
    score: float = 0.0


def estimate_damage(attacker: Pokemon, defender: Pokemon, move: Move) -> int:
    """Estimate damage without RNG — uses average roll, no crit.

    Handles special-case moves (fixed damage, level damage, OHKO).
    Returns 0 for STATUS moves and immune matchups.
    """
    # Status moves deal no damage
    if move.category == MoveCategory.STATUS:
        return 0

    # Fixed damage moves
    if move.name in FIXED_DAMAGE_MOVES:
        effectiveness = get_effectiveness(move.type, defender.types)
        if effectiveness == 0:
            return 0
        return FIXED_DAMAGE_MOVES[move.name]

    # Level-based damage moves
    if move.name in LEVEL_DAMAGE_MOVES:
        effectiveness = get_effectiveness(move.type, defender.types)
        if effectiveness == 0:
            return 0
        return attacker.level

    # OHKO moves — estimate as defender's current HP if speed allows
    if move.name in OHKO_MOVES:
        if attacker.base_stats.speed < defender.base_stats.speed:
            return 0  # Will fail
        return defender.current_hp

    # Standard damage formula (no crit, avg roll)
    phys = is_physical(move)
    attack = get_modified_attack(attacker, phys)
    defense = get_modified_defense(defender, phys)
    defense = max(1, defense)

    base = calculate_base_damage(attacker.level, move.power, attack, defense)

    stab = get_stab_multiplier(move.type, attacker.types)
    effectiveness = get_effectiveness(move.type, defender.types)

    if effectiveness == 0:
        return 0

    damage = int(base * stab * effectiveness * (_AVG_ROLL / _ROLL_DIVISOR))

    # Burn halves physical damage
    if attacker.status == Status.BURN and phys:
        damage = int(damage * 0.5)

    return max(1, damage)


def evaluate_move(attacker: Pokemon, defender: Pokemon, move: Move) -> MoveScore:
    """Score a single move against a target.

    The composite *score* field blends estimated damage with move properties
    so that callers can simply sort by score and pick the best.
    """
    ms = MoveScore(move=move)

    effectiveness = get_effectiveness(move.type, defender.types)
    ms.effectiveness = effectiveness
    ms.is_immune = (effectiveness == 0 and move.category != MoveCategory.STATUS)
    ms.is_status = (move.category == MoveCategory.STATUS)
    ms.is_self_destruct = move.name in SELF_DESTRUCT_MOVES
    ms.is_two_turn = move.name in TWO_TURN_MOVES
    ms.is_recovery = move.name in RECOVERY_MOVES
    ms.is_drain = move.name in HP_DRAIN_MOVES
    ms.has_status_effect = (
        move.status_effect is not None
        and move.status_chance > 0
    )

    ms.estimated_damage = estimate_damage(attacker, defender, move)

    # ── Composite score ──────────────────────────────────────────
    score = float(ms.estimated_damage)

    # Bonus for status moves if the opponent has no status condition
    if ms.is_status and ms.has_status_effect and defender.status == Status.NONE:
        score += 40.0

    # Bonus for stat-changing moves that target self (e.g. Swords Dance)
    if ms.is_status and move.stat_changes and move.target_self:
        score += 30.0

    # Small bonus for super-effective, penalty for resisted
    if effectiveness >= 2.0:
        score *= 1.2
    elif 0 < effectiveness < 1.0:
        score *= 0.8

    # Penalise self-destruct (risky)
    if ms.is_self_destruct:
        score *= 0.5

    # Penalise two-turn moves (telegraphed)
    if ms.is_two_turn:
        score *= 0.7

    # Recovery bonus when HP is low
    if ms.is_recovery:
        hp_ratio = attacker.current_hp / attacker.max_hp if attacker.max_hp > 0 else 1.0
        if hp_ratio < 0.5:
            score += 50.0 * (1.0 - hp_ratio)

    ms.score = score
    return ms


def evaluate_all_moves(
    attacker: Pokemon, defender: Pokemon, moves: list[Move]
) -> list[MoveScore]:
    """Evaluate every move and return a list sorted best-first (descending score)."""
    scores = [evaluate_move(attacker, defender, m) for m in moves]
    scores.sort(key=lambda s: s.score, reverse=True)
    return scores


# ======================================================================
# Phase 2 — advanced evaluation functions
# ======================================================================


def threat_score(attacker: Pokemon, defender: Pokemon) -> float:
    """How threatening is *attacker* to *defender*?

    Returns the best estimated damage from any of attacker's moves,
    normalised by defender's current HP.  A value >= 1.0 means the
    attacker can potentially KO the defender in one hit.

    Pure function — no RNG.
    """
    if defender.current_hp <= 0:
        return 0.0

    best_damage = 0
    for m in attacker.moves:
        if m.has_pp():
            dmg = estimate_damage(attacker, defender, m)
            if dmg > best_damage:
                best_damage = dmg

    return best_damage / defender.current_hp


def score_switch_target(
    candidate: Pokemon,
    opponent_active: Pokemon,
    own_active: Pokemon,
) -> float:
    """Score a potential switch-in candidate against the opponent's active.

    Blends four factors:
    1. **Defensive typing** — how well does the candidate resist the
       opponent's best move?  (lower incoming threat = higher score)
    2. **Offensive potential** — can the candidate hit the opponent
       super-effectively?
    3. **HP remaining** — healthier candidates score higher.
    4. **Speed advantage** — outspeeding the opponent is valuable.

    Returns a float where higher is better.  Not normalised to any
    specific range — used for relative comparison only.
    """
    score = 0.0

    # 1. Defensive: inverse of threat from opponent
    incoming_threat = threat_score(opponent_active, candidate)
    # Clamp so a 0-threat situation doesn't dominate
    score += max(0.0, 1.0 - incoming_threat) * 40.0

    # 2. Offensive: best damage candidate can deal
    best_damage = 0
    best_eff = 0.0
    for m in candidate.moves:
        if m.has_pp():
            dmg = estimate_damage(candidate, opponent_active, m)
            eff = get_effectiveness(m.type, opponent_active.types)
            if dmg > best_damage:
                best_damage = dmg
                best_eff = eff
    score += best_damage * 0.3
    if best_eff >= 2.0:
        score += 20.0

    # 3. HP — prefer healthy switch-ins
    hp_ratio = candidate.current_hp / candidate.max_hp if candidate.max_hp > 0 else 0.0
    score += hp_ratio * 20.0

    # 4. Speed advantage
    cand_speed = get_modified_speed(candidate)
    opp_speed = get_modified_speed(opponent_active)
    if cand_speed > opp_speed:
        score += 10.0

    return score


def should_switch(
    team: 'Team',
    opponent_active: Pokemon,
    threshold: float = 0.35,
) -> tuple[bool, Optional[int]]:
    """Decide whether the active Pokemon should switch out.

    Considers:
    - How threatened the active Pokemon is (incoming threat).
    - Whether a meaningfully better switch-in exists.

    Args:
        team: The AI's team (uses active + reserves).
        opponent_active: The opponent's current Pokemon.
        threshold: Minimum threat level to consider switching (0-1+).

    Returns:
        (should_switch, best_switch_index) — index is None when
        switching is not recommended or not possible.
    """
    from models.team import Team  # local to avoid circular at module level

    active = team.active_pokemon
    if not team.can_switch():
        return False, None

    # How threatened is our active Pokemon?
    incoming = threat_score(opponent_active, active)
    if incoming < threshold:
        return False, None  # Not threatened enough to switch

    # Score current active's position
    active_score = score_switch_target(active, opponent_active, active)

    # Find best switch-in
    available = team.get_available_switches()
    best_idx: Optional[int] = None
    best_score = active_score  # Must beat current position

    for idx, candidate in available:
        s = score_switch_target(candidate, opponent_active, active)
        if s > best_score:
            best_score = s
            best_idx = idx

    if best_idx is not None:
        return True, best_idx

    return False, None
