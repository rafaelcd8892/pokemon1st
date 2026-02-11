"""Battle engine for executing turns and handling combat mechanics."""

import random
import logging
from models.pokemon import Pokemon

logger = logging.getLogger(__name__)
from models.move import Move
from models.enums import MoveCategory, StatType, Status, Type
from engine.damage import calculate_damage
from engine.status import apply_status_effects, apply_end_turn_status_damage
from engine.stat_modifiers import get_stat_change_message, get_modified_speed, get_accuracy_multiplier
from engine.display import format_pokemon_status, format_move_name
from engine.move_effects import (
    is_special_move, execute_special_move,
    apply_leech_seed_damage, decrement_screen_turns,
    TWO_TURN_MOVES, TRAPPING_MOVES, get_multi_hit_count
)
from engine.battle_logger import get_battle_logger

SELF_TARGET_LOG_MOVES = {
    "Agility",
    "Amnesia",
    "Barrier",
    "Conversion",
    "Focus Energy",
    "Growth",
    "Harden",
    "Light Screen",
    "Meditate",
    "Minimize",
    "Mist",
    "Recover",
    "Reflect",
    "Rest",
    "Soft Boiled",
    "Substitute",
    "Swords Dance",
    "Withdraw",
}


# =============================================================================
# Turn Execution - Main Entry Point
# =============================================================================

def execute_turn(attacker: Pokemon, defender: Pokemon, move: Move, all_moves: list = None):
    """
    Execute a complete battle turn.

    Args:
        attacker: The Pokemon using the move
        defender: The Pokemon being targeted
        move: The move being used
        all_moves: List of all available moves (for Metronome/Mirror Move)
    """
    logger.debug(f"Turn: {attacker.name} using {move.name} against {defender.name}")

    # Handle recharge state (e.g., after Hyper Beam)
    if _handle_recharge_state(attacker):
        return

    # Gen 1: Trapped Pokemon (Wrap, Bind, etc.) cannot act
    if attacker.is_trapped and (
        attacker.trap_turns <= 0 or (attacker.trapped_by is not None and not attacker.trapped_by.is_alive())
    ):
        attacker.is_trapped = False
        attacker.trap_turns = 0
        attacker.trapped_by = None

    if attacker.is_trapped:
        print(f"\n{attacker.name} está atrapado y no puede moverse!")
        return

    # Check for locked/charging moves and get the actual move to use
    move, is_multi_turn, is_charging = _get_active_move(attacker, move)

    # Check status effects before announcing move
    can_attack = apply_status_effects(attacker)
    if not can_attack:
        _handle_status_prevented_attack(attacker, is_multi_turn)
        return

    # Announce the move being used
    if not _announce_move(attacker, move, is_multi_turn, is_charging):
        return  # Move was disabled

    # Track last move and use PP
    attacker.last_move_used = move.name
    if not move.has_pp():
        print(f"¡No hay PP para {move.name}!")
        return
    move.use()

    # Check if defender is semi-invulnerable
    if defender.is_semi_invulnerable:
        print(f"¡El ataque falló! ({defender.name} está fuera de alcance)")
        _log_move_event(
            attacker,
            defender,
            move,
            damage=0,
            effectiveness=1.0,
            move_result="blocked_by_invulnerability",
        )
        return

    # Check accuracy
    if not _check_accuracy(attacker, defender, move):
        return

    # Handle special moves with unique effects
    # Skip special handling if this is the execution turn of a charge move
    # (is_charging means we already charged last turn and now attack normally)
    if is_special_move(move) and not is_charging:
        _handle_special_move(attacker, defender, move, all_moves)
        return

    # Handle normal attack (includes charge move execution)
    _execute_normal_attack(attacker, defender, move)


# =============================================================================
# Pre-Attack Phase Handlers
# =============================================================================

def _handle_recharge_state(attacker: Pokemon) -> bool:
    """
    Handle recharge state (e.g., after Hyper Beam).

    Returns:
        True if the Pokemon must recharge (turn ends), False otherwise
    """
    if attacker.must_recharge:
        print(f"\n{attacker.name} debe recargar!")
        attacker.must_recharge = False
        return True
    return False


def _get_active_move(attacker: Pokemon, move: Move) -> tuple[Move, bool, bool]:
    """
    Determine the actual move to use, handling multi-turn and charging moves.

    Args:
        attacker: The attacking Pokemon
        move: The originally selected move

    Returns:
        Tuple of (actual_move, is_multi_turn, is_charging)
    """
    is_multi_turn = False
    is_charging = False

    # Check if locked into a multi-turn move (Thrash, Petal-Dance)
    if attacker.multi_turn_move:
        move = attacker.multi_turn_move
        attacker.multi_turn_counter -= 1
        is_multi_turn = True
    # Check if charging a two-turn move
    elif attacker.is_charging:
        move = attacker.charging_move
        attacker.is_charging = False
        attacker.charging_move = None
        attacker.is_semi_invulnerable = False
        is_charging = True

    return move, is_multi_turn, is_charging


def _handle_status_prevented_attack(attacker: Pokemon, is_multi_turn: bool):
    """Handle the case when status prevents an attack."""
    # Reset multi-turn if interrupted by status
    if is_multi_turn and attacker.multi_turn_counter <= 0:
        attacker.multi_turn_move = None
        attacker.confusion_turns = random.randint(2, 5)
        print(f"¡{attacker.name} está confundido por el cansancio!")


def _announce_move(attacker: Pokemon, move: Move, is_multi_turn: bool, is_charging: bool) -> bool:
    """
    Announce the move being used.

    Returns:
        True if the move can proceed, False if it was disabled
    """
    move_display = format_move_name(move)

    if is_multi_turn:
        print(f"\n{attacker.name} continúa usando {move_display}!")
        if attacker.multi_turn_counter <= 0:
            # End multi-turn, become confused
            attacker.multi_turn_move = None
            attacker.confusion_turns = random.randint(2, 5)
            print(f"¡{attacker.name} está confundido por el cansancio!")
    elif is_charging:
        print(f"\n{attacker.name} ataca con {move_display}!")
    else:
        # Check if move is disabled
        if attacker.disabled_move and move.name == attacker.disabled_move:
            print(f"\n{attacker.name} intenta usar {move_display}!")
            print(f"¡{move.name} está deshabilitado!")
            return False
        print(f"\n{attacker.name} usa {move_display}!")

    return True


def _check_accuracy(attacker: Pokemon, defender: Pokemon, move: Move) -> bool:
    """
    Check if the move hits based on accuracy.

    Returns:
        True if the move hits, False if it misses
    """
    # Always-hit moves (accuracy 0 means never misses)
    if move.accuracy == 0:
        return True

    accuracy_multiplier = get_accuracy_multiplier(attacker, defender)
    final_accuracy = move.accuracy * accuracy_multiplier

    if random.randint(1, 100) > final_accuracy:
        print(f"¡El ataque falló!")
        blog = get_battle_logger()
        if blog:
            blog.log_miss(attacker.name, move.name, pokemon_side=_pokemon_side(attacker))
        # Handle crash damage for High-Jump-Kick/Jump-Kick
        if move.name in ("High Jump Kick", "Jump Kick"):
            crash_damage = max(1, attacker.max_hp // 8)
            attacker.take_damage(crash_damage)
            print(f"¡{attacker.name} se estrelló y recibió {crash_damage} de daño!")
            print(f"  {format_pokemon_status(attacker)}")
        return False
    return True


# =============================================================================
# Special Move Handlers
# =============================================================================

def _handle_special_move(attacker: Pokemon, defender: Pokemon, move: Move, all_moves: list):
    """Handle moves with special effects (fixed damage, OHKO, recovery, etc.)."""
    damage, message = execute_special_move(attacker, defender, move, all_moves)

    # Dispatch to appropriate handler based on damage code
    handlers = {
        -1: _handle_metronome_mirror_move,
        -2: _handle_hp_drain_move,
        -3: _handle_self_destruct_move,
        -4: _handle_crash_damage_move,
        -5: _handle_recharge_move,
        -6: _handle_charge_move,
        -7: _handle_multi_turn_move,
        -8: _handle_rage_move,
        -9: _handle_trapping_move,
        -10: _handle_multi_hit_move,
        -11: _handle_double_hit_move,
        -12: _handle_twineedle_move,
    }

    handler = handlers.get(damage)
    if handler and "|" in message:
        # For special utility moves with delegated behavior, log invocation when
        # no direct damage record is guaranteed by handler.
        if damage == -1:
            _log_move_event(attacker, defender, move, damage=0, effectiveness=1.0)
        handler(attacker, defender, move, message, all_moves)
    elif message:
        print(message)
        if damage > 0:
            actual_damage = apply_damage_to_target(defender, damage, False)
            _log_move_event(attacker, defender, move, damage=actual_damage, effectiveness=1.0)
            if actual_damage > 0:
                print(f"  {format_pokemon_status(defender)}")
        elif damage == 0 and message:
            # Keep target resolution centralized for audit consistency.
            _log_move_event(attacker, defender, move, damage=0, effectiveness=1.0)
            print(f"  {format_pokemon_status(attacker)}")


def _handle_metronome_mirror_move(attacker: Pokemon, defender: Pokemon, move: Move,
                                   message: str, all_moves: list):
    """Handle Metronome/Mirror Move (execute a random/copied move)."""
    msg_parts = message.split("|")
    print(msg_parts[0])  # Print the "Metronome chose X!" message
    chosen_move_name = msg_parts[1]

    if all_moves:
        for m in all_moves:
            if m.name == chosen_move_name:
                execute_turn(attacker, defender, m, all_moves)
                return


def _handle_hp_drain_move(attacker: Pokemon, defender: Pokemon, move: Move,
                          message: str, all_moves: list):
    """Handle HP drain moves (Absorb, Mega Drain, etc.)."""
    actual_damage, is_crit, effectiveness = calculate_damage(attacker, defender, move)

    if effectiveness == 0:
        print(f"No afecta a {defender.name}...")
        _log_move_event(attacker, defender, move, damage=0, is_critical=is_crit, effectiveness=0)
        return

    actual_damage = apply_damage_to_target(defender, actual_damage, False)
    _log_move_event(attacker, defender, move, damage=actual_damage, is_critical=is_crit, effectiveness=effectiveness)
    _print_damage_messages(is_crit, effectiveness, defender.name)

    if actual_damage > 0:
        print(f"{defender.name} recibe {actual_damage} de daño!")
        print(f"  {format_pokemon_status(defender)}")
        # Heal attacker for 50% of damage dealt
        heal_amount = max(1, actual_damage // 2)
        actual_heal = min(heal_amount, attacker.max_hp - attacker.current_hp)
        attacker.current_hp += actual_heal
        print(f"¡{attacker.name} absorbió {actual_heal} HP!")
        print(f"  {format_pokemon_status(attacker)}")


def _handle_self_destruct_move(attacker: Pokemon, defender: Pokemon, move: Move,
                                message: str, all_moves: list):
    """Handle Explosion/Self-Destruct (user faints, halves defender's defense)."""
    # Gen 1: Explosion/Self-Destruct halves the defender's Defense in the formula
    actual_damage, is_crit, effectiveness = calculate_damage(
        attacker, defender, move, defense_modifier=0.5
    )

    if effectiveness == 0:
        print(f"No afecta a {defender.name}...")
        _log_move_event(
            attacker,
            defender,
            move,
            damage=0,
            is_critical=is_crit,
            effectiveness=0,
            extra_details={"self_faint": True},
        )
    else:
        actual_damage = apply_damage_to_target(defender, actual_damage, True)
        _log_move_event(
            attacker,
            defender,
            move,
            damage=actual_damage,
            is_critical=is_crit,
            effectiveness=effectiveness,
            extra_details={"self_faint": True},
        )
        _print_damage_messages(is_crit, effectiveness, defender.name)
        if actual_damage > 0:
            print(f"{defender.name} recibe {actual_damage} de daño!")
            print(f"  {format_pokemon_status(defender)}")

    # User faints
    attacker.current_hp = 0
    print(f"¡{attacker.name} se debilitó por la explosión!")


def _handle_crash_damage_move(attacker: Pokemon, defender: Pokemon, move: Move,
                               message: str, all_moves: list):
    """Handle moves with crash damage on hit (normal damage calculation)."""
    actual_damage, is_crit, effectiveness = calculate_damage(attacker, defender, move)

    if effectiveness == 0:
        print(f"No afecta a {defender.name}...")
        _log_move_event(attacker, defender, move, damage=0, is_critical=is_crit, effectiveness=0)
        return

    actual_damage = apply_damage_to_target(defender, actual_damage, True)
    _log_move_event(attacker, defender, move, damage=actual_damage, is_critical=is_crit, effectiveness=effectiveness)
    _print_damage_messages(is_crit, effectiveness, defender.name)

    if actual_damage > 0:
        print(f"{defender.name} recibe {actual_damage} de daño!")
        print(f"  {format_pokemon_status(defender)}")


def _handle_recharge_move(attacker: Pokemon, defender: Pokemon, move: Move,
                          message: str, all_moves: list):
    """Handle recharge moves like Hyper Beam."""
    actual_damage, is_crit, effectiveness = calculate_damage(attacker, defender, move)

    if effectiveness == 0:
        print(f"No afecta a {defender.name}...")
        _log_move_event(attacker, defender, move, damage=0, is_critical=is_crit, effectiveness=0)
        return

    is_physical = move.category == MoveCategory.PHYSICAL
    actual_damage = apply_damage_to_target(defender, actual_damage, is_physical)
    _log_move_event(attacker, defender, move, damage=actual_damage, is_critical=is_crit, effectiveness=effectiveness)
    _print_damage_messages(is_crit, effectiveness, defender.name)

    if actual_damage > 0:
        print(f"{defender.name} recibe {actual_damage} de daño!")
        print(f"  {format_pokemon_status(defender)}")
        # Gen 1: Must recharge next turn, but skip recharge if target faints
        if defender.is_alive():
            attacker.must_recharge = True


def _handle_charge_move(attacker: Pokemon, defender: Pokemon, move: Move,
                        message: str, all_moves: list):
    """Handle charge moves like Solar Beam, Dig, Fly."""
    move_name = message.split("|")[1]
    move_data = TWO_TURN_MOVES.get(move_name, {})

    attacker.is_charging = True
    attacker.charging_move = move
    _log_move_event(
        attacker,
        defender,
        move,
        damage=0,
        effectiveness=1.0,
        move_result="charge_start",
    )

    if move_data.get("semi_invulnerable"):
        attacker.is_semi_invulnerable = True
        if move_name == "Dig":
            print(f"¡{attacker.name} se escondió bajo tierra!")
        else:
            print(f"¡{attacker.name} voló muy alto!")
    elif move_data.get("defense_boost"):
        # Skull Bash raises defense
        attacker.modify_stat_stage(StatType.DEFENSE, 1)
        print(f"¡{attacker.name} está preparando el ataque!")
    else:
        print(f"¡{attacker.name} está cargando energía!")


def _handle_multi_turn_move(attacker: Pokemon, defender: Pokemon, move: Move,
                             message: str, all_moves: list):
    """Handle multi-turn moves like Thrash, Petal-Dance."""
    # Start multi-turn attack (2-3 turns)
    attacker.multi_turn_move = move
    attacker.multi_turn_counter = random.randint(2, 3)
    # Deal damage normally
    _deal_damage_with_messages(attacker, defender, move)


def _handle_rage_move(attacker: Pokemon, defender: Pokemon, move: Move,
                      message: str, all_moves: list):
    """Handle Rage (attack increases when hit)."""
    attacker.is_raging = True
    # Deal damage normally
    _deal_damage_with_messages(attacker, defender, move)


def _handle_trapping_move(attacker: Pokemon, defender: Pokemon, move: Move,
                          message: str, all_moves: list):
    """Handle trapping moves like Wrap, Bind."""
    # Start trapping (2-5 turns in Gen 1)
    if not defender.is_trapped:
        defender.is_trapped = True
        defender.trap_turns = random.randint(2, 5)
        defender.trapped_by = attacker

    actual_damage, is_crit, effectiveness = calculate_damage(attacker, defender, move)

    if effectiveness == 0:
        print(f"No afecta a {defender.name}...")
        _log_move_event(attacker, defender, move, damage=0, is_critical=is_crit, effectiveness=0)
        defender.is_trapped = False
        defender.trap_turns = 0
        defender.trapped_by = None
        return

    actual_damage = apply_damage_to_target(defender, actual_damage, True)
    _log_move_event(attacker, defender, move, damage=actual_damage, is_critical=is_crit, effectiveness=effectiveness)
    _print_damage_messages(is_crit, effectiveness, defender.name)

    if actual_damage > 0:
        print(f"{defender.name} recibe {actual_damage} de daño!")
        print(f"¡{defender.name} está atrapado por {move.name}!")
        print(f"  {format_pokemon_status(defender)}")


def _handle_multi_hit_move(attacker: Pokemon, defender: Pokemon, move: Move,
                           message: str, all_moves: list):
    """Handle multi-hit moves like Fury Attack, Pin Missile (2-5 hits)."""
    _execute_multi_hit_attack(attacker, defender, move, get_multi_hit_count())


def _handle_double_hit_move(attacker: Pokemon, defender: Pokemon, move: Move,
                            message: str, all_moves: list):
    """Handle fixed 2-hit moves like Double Kick, Bonemerang."""
    _execute_multi_hit_attack(attacker, defender, move, 2)


def _handle_twineedle_move(attacker: Pokemon, defender: Pokemon, move: Move,
                           message: str, all_moves: list):
    """Handle Twineedle (2 hits with 20% poison chance each)."""
    _execute_multi_hit_attack(attacker, defender, move, 2, poison_chance=20)


# =============================================================================
# Attack Execution Helpers
# =============================================================================

def _deal_damage_with_messages(attacker: Pokemon, defender: Pokemon, move: Move):
    """Calculate and apply damage with appropriate messages."""
    actual_damage, is_crit, effectiveness = calculate_damage(attacker, defender, move)

    if effectiveness == 0:
        print(f"No afecta a {defender.name}...")
        return

    actual_damage = apply_damage_to_target(defender, actual_damage, True)
    _print_damage_messages(is_crit, effectiveness, defender.name)
    _log_move_event(attacker, defender, move, damage=actual_damage, is_critical=is_crit, effectiveness=effectiveness)

    if actual_damage > 0:
        print(f"{defender.name} recibe {actual_damage} de daño!")
        print(f"  {format_pokemon_status(defender)}")
        # Gen 1: Fire-type moves thaw frozen targets
        if defender.status == Status.FREEZE and move.type == Type.FIRE:
            defender.status = Status.NONE
            print(f"¡{defender.name} se descongeló!")


def _execute_multi_hit_attack(attacker: Pokemon, defender: Pokemon, move: Move,
                               num_hits: int, poison_chance: int = 0):
    """
    Execute a multi-hit attack.

    Args:
        attacker: The attacking Pokemon
        defender: The defending Pokemon
        move: The move being used
        num_hits: Number of hits to attempt
        poison_chance: Chance to poison per hit (0-100), 0 means no poison
    """
    total_damage = 0
    is_physical = move.category == MoveCategory.PHYSICAL
    hits = 0
    effectiveness = 1  # Track for message at end

    for hit in range(num_hits):
        if not defender.is_alive():
            break

        hit_damage, is_crit, effectiveness = calculate_damage(attacker, defender, move)

        if effectiveness == 0:
            print(f"No afecta a {defender.name}...")
            _log_move_event(attacker, defender, move, damage=0, effectiveness=0)
            return

        hit_damage = apply_damage_to_target(defender, hit_damage, is_physical)
        total_damage += hit_damage
        hits += 1

        if is_crit:
            print(f"¡Golpe {hit + 1}: Crítico!")

        # Handle poison chance (for Twineedle)
        if poison_chance > 0 and defender.substitute_hp == 0 and defender.status == Status.NONE:
            if random.randint(1, 100) <= poison_chance:
                defender.status = Status.POISON
                print(f"¡{defender.name} fue envenenado!")

    # Print effectiveness message once at the end
    if effectiveness > 1:
        print("¡Es súper efectivo!")
    elif effectiveness < 1:
        print("No es muy efectivo...")

    print(f"¡Golpeó {hits} veces! Daño total: {total_damage}")
    print(f"  {format_pokemon_status(defender)}")
    _log_move_event(attacker, defender, move, damage=total_damage, effectiveness=effectiveness)


def _print_damage_messages(is_crit: bool, effectiveness: float, defender_name: str):
    """Print critical hit and effectiveness messages."""
    if is_crit:
        print("¡Golpe crítico!")
    if effectiveness > 1:
        print("¡Es súper efectivo!")
    elif effectiveness < 1 and effectiveness > 0:
        print("No es muy efectivo...")


def _execute_normal_attack(attacker: Pokemon, defender: Pokemon, move: Move):
    """Execute a standard attack with damage calculation and effects."""
    from engine.type_chart import get_effectiveness

    damage, is_critical, effectiveness = calculate_damage(attacker, defender, move)

    # For STATUS moves, calculate_damage returns effectiveness=1.0 without checking the type chart.
    # We must check type immunity separately so e.g. Thunder Wave can't paralyze Ground types.
    # Self-targeting status moves should always be treated as effective.
    if move.category == MoveCategory.STATUS:
        effectiveness = 1.0 if move.target_self else get_effectiveness(move.type, defender.types)

    # Check immunity first — no damage, no secondary effects
    if effectiveness == 0:
        print(f"No afecta a {defender.name}...")
        _log_move_event(attacker, defender, move, damage=0, effectiveness=0,
                        target_override=(attacker if move.target_self else defender))
        return

    # Apply screens (Reflect/Light Screen reduce damage by half)
    is_physical = move.category == MoveCategory.PHYSICAL
    damage = _apply_screen_reduction(defender, damage, is_physical, is_critical)

    if damage > 0:
        # Track damage for Counter
        defender.last_damage_taken = damage
        defender.last_damage_physical = is_physical
        defender.last_damage_move_type = move.type

        # Apply damage (respecting Substitute)
        actual_damage = apply_damage_to_target(defender, damage, is_physical)

        _print_damage_messages(is_critical, effectiveness, defender.name)

        _log_move_event(attacker, defender, move,
                        damage=actual_damage, is_critical=is_critical,
                        effectiveness=effectiveness,
                        target_override=(attacker if move.target_self else defender))

        if actual_damage > 0:
            print(f"{defender.name} recibe {actual_damage} de daño!")
            print(f"  {format_pokemon_status(defender)}")
            # Rage: Attack increases when hit
            if defender.is_raging:
                defender.modify_stat_stage(StatType.ATTACK, 1)
                print(f"¡La furia de {defender.name} aumenta!")
            # Gen 1: Fire-type moves thaw frozen targets
            if defender.status == Status.FREEZE and move.type == Type.FIRE:
                defender.status = Status.NONE
                print(f"¡{defender.name} se descongeló!")
    else:
        # STATUS/self-target moves with 0 damage
        _log_move_event(attacker, defender, move,
                        damage=0, effectiveness=effectiveness,
                        target_override=(attacker if move.target_self else defender))

    # Apply status effect
    _apply_move_status_effect(defender, move)

    # Apply stat changes
    _apply_move_stat_changes(attacker, defender, move)


def _apply_screen_reduction(defender: Pokemon, damage: int, is_physical: bool, is_critical: bool) -> int:
    """Apply screen damage reduction (Reflect/Light Screen)."""
    # Gen 1 critical hits ignore Reflect/Light Screen
    if is_critical:
        return damage
    if is_physical and defender.has_reflect:
        print("¡Reflect reduce el daño!")
        return damage // 2
    elif not is_physical and defender.has_light_screen:
        print("¡Light Screen reduce el daño!")
        return damage // 2
    return damage


def _apply_move_status_effect(defender: Pokemon, move: Move):
    """Apply the move's status effect if applicable."""
    # Status moves don't work through Substitute, and don't apply to fainted Pokemon
    if defender.substitute_hp == 0 and defender.is_alive():
        if move.status_effect and random.randint(1, 100) <= move.status_chance:
            if defender.apply_status(move.status_effect):
                print(f"¡{defender.name} está {move.status_effect.value}!")
                print(f"  {format_pokemon_status(defender)}")
                blog = get_battle_logger()
                if blog:
                    blog.log_status(
                        defender.name, move.status_effect.value,
                        applied=True, source=move.name,
                        pokemon_side=_pokemon_side(defender)
                    )
            elif defender.status != Status.NONE:
                print(f"¡{defender.name} ya tiene un estado alterado!")
                blog = get_battle_logger()
                if blog:
                    blog.log_status(
                        defender.name, move.status_effect.value,
                        applied=False, source=move.name,
                        pokemon_side=_pokemon_side(defender)
                    )


def _apply_move_stat_changes(attacker: Pokemon, defender: Pokemon, move: Move):
    """Apply the move's stat changes if applicable."""
    if not move.stat_changes:
        return

    target = attacker if move.target_self else defender

    # Don't apply stat changes to fainted Pokemon
    if not target.is_alive():
        return

    # Check Mist (prevents stat reductions on the protected Pokemon)
    if not move.target_self and target.has_mist:
        has_negative = any(change < 0 for change in move.stat_changes.values())
        if has_negative:
            print(f"¡Mist protege a {target.name} de la reducción de estadísticas!")
            return

    for stat, change in move.stat_changes.items():
        actual_change, hit_limit = target.modify_stat_stage(stat, change)
        message = get_stat_change_message(target, stat, actual_change, hit_limit)
        if message:
            print(message)

    print(f"  {format_pokemon_status(target)}")


# =============================================================================
# Damage Application
# =============================================================================

def apply_damage_to_target(target: Pokemon, damage: int, is_physical: bool) -> int:
    """
    Apply damage to target, respecting Substitute.

    Args:
        target: The Pokemon receiving damage
        damage: Amount of damage to deal
        is_physical: Whether the damage is physical (unused but kept for API compatibility)

    Returns:
        Actual damage dealt to the Pokemon (0 if absorbed by Substitute)
    """
    if target.substitute_hp > 0:
        target.substitute_hp -= damage
        if target.substitute_hp <= 0:
            target.substitute_hp = 0
            print(f"¡El sustituto de {target.name} se rompió!")
        else:
            print(f"¡El sustituto absorbió el daño!")
        return 0
    else:
        hp_before = target.current_hp
        target.take_damage(damage)
        return hp_before - target.current_hp


# =============================================================================
# End-of-Turn Effects
# =============================================================================

def apply_end_of_turn_effects(pokemon1: Pokemon, pokemon2: Pokemon):
    """
    Apply all end-of-turn effects for both Pokemon.
    Call this at the end of each turn in the battle loop.
    """
    messages = []

    # Leech Seed damage
    messages.extend(_apply_leech_seed_effects(pokemon1, pokemon2))
    messages.extend(_apply_leech_seed_effects(pokemon2, pokemon1))

    # Trapping damage (Wrap, Bind, etc.)
    messages.extend(_apply_trapping_effects(pokemon1, pokemon2))
    messages.extend(_apply_trapping_effects(pokemon2, pokemon1))

    # Status damage (burn/poison)
    apply_end_turn_status_damage(pokemon1)
    apply_end_turn_status_damage(pokemon2)

    # Decrement screen turns
    messages.extend(decrement_screen_turns(pokemon1))
    messages.extend(decrement_screen_turns(pokemon2))

    # Print all messages
    for msg in messages:
        print(msg)


def _apply_leech_seed_effects(seeded: Pokemon, seeder: Pokemon) -> list[str]:
    """Apply Leech Seed damage and healing."""
    messages = []
    if seeded.is_seeded:
        hp_before = seeded.current_hp
        msg = apply_leech_seed_damage(seeded, seeder)
        if msg:
            messages.append(msg)
            messages.append(f"  {format_pokemon_status(seeded)}")
            blog = get_battle_logger()
            if blog:
                drain = hp_before - seeded.current_hp
                blog.log_effect("leech_seed", seeded.name, damage=drain, pokemon_side=_pokemon_side(seeded))
    return messages


def _apply_trapping_effects(trapped: Pokemon, trapper: Pokemon) -> list[str]:
    """Apply trapping move damage (Wrap, Bind, etc.)."""
    messages = []
    if trapped.is_trapped:
        if trapped.trap_turns <= 0:
            trapped.is_trapped = False
            trapped.trap_turns = 0
            trapped.trapped_by = None
            messages.append(f"¡{trapped.name} se liberó!")
            return messages

        if trapped.trapped_by is None:
            trapped.trap_turns -= 1
            if trapped.trap_turns <= 0:
                trapped.is_trapped = False
                trapped.trapped_by = None
                messages.append(f"¡{trapped.name} se liberó!")
            return messages

        if not trapped.trapped_by.is_alive():
            trapped.is_trapped = False
            trapped.trap_turns = 0
            trapped.trapped_by = None
            messages.append(f"¡{trapped.name} se liberó!")
            return messages

        # If battle context no longer matches the original trapper, clear stale trap state.
        if trapped.trapped_by != trapper:
            trapped.is_trapped = False
            trapped.trap_turns = 0
            trapped.trapped_by = None
            messages.append(f"¡{trapped.name} se liberó!")
            return messages

        trapped.trap_turns -= 1
        # In Gen 1, trapping moves deal damage each turn
        trap_damage = max(1, trapped.max_hp // 16)
        trapped.take_damage(trap_damage)
        messages.append(f"¡{trapped.name} sigue atrapado y recibe {trap_damage} de daño!")
        messages.append(f"  {format_pokemon_status(trapped)}")
        blog = get_battle_logger()
        if blog:
            blog.log_effect("trapping", trapped.name, damage=trap_damage, pokemon_side=_pokemon_side(trapped))
        if trapped.trap_turns <= 0:
            trapped.is_trapped = False
            trapped.trapped_by = None
            messages.append(f"¡{trapped.name} se liberó!")
    return messages


# =============================================================================
# Turn Order
# =============================================================================

def determine_turn_order(pokemon1: Pokemon, pokemon2: Pokemon) -> tuple[Pokemon, Pokemon]:
    """
    Determine who attacks first based on Speed (with stat stages applied).

    Args:
        pokemon1: First Pokemon
        pokemon2: Second Pokemon

    Returns:
        Tuple of (first_attacker, second_attacker)
    """
    speed1 = get_modified_speed(pokemon1)
    speed2 = get_modified_speed(pokemon2)

    if speed1 > speed2:
        return pokemon1, pokemon2
    elif speed2 > speed1:
        return pokemon2, pokemon1
    else:
        # Speed tie - random order
        result = random.choice([(pokemon1, pokemon2), (pokemon2, pokemon1)])
        logger.debug(f"Speed tie, random order: {result[0].name} goes first")
        return result
def _pokemon_side(pokemon: Pokemon) -> str | None:
    """Return side tag if available (P1/P2)."""
    return getattr(pokemon, "battle_side", None)


def _resolve_log_target(
    attacker: Pokemon,
    defender: Pokemon,
    move: Move,
    target_override: Pokemon | None,
) -> Pokemon:
    if target_override is not None:
        return target_override
    if move.target_self or move.name in SELF_TARGET_LOG_MOVES:
        return attacker
    return defender


def _log_move_event(attacker: Pokemon, defender: Pokemon, move: Move,
                    damage: int = 0, is_critical: bool = False,
                    effectiveness: float = 1.0, message: str = "",
                    target_override: Pokemon | None = None,
                    move_result: str = "resolved",
                    extra_details: dict | None = None):
    """Unified move logging with side-aware metadata."""
    blog = get_battle_logger()
    if not blog:
        return

    target = _resolve_log_target(attacker, defender, move, target_override)
    blog.log_move(
        attacker.name,
        move.name,
        target.name,
        damage=damage,
        is_critical=is_critical,
        effectiveness=effectiveness,
        message=message,
        pokemon_side=_pokemon_side(attacker),
        target_side=_pokemon_side(target),
        move_result=move_result,
        extra_details=extra_details,
    )
