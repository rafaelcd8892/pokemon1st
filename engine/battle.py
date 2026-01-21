import random

from logging_config import get_logger

logger = get_logger(__name__)

from models.pokemon import Pokemon
from models.move import Move
from models.enums import MoveCategory
from engine.damage import calculate_damage
from engine.status import apply_status_effects, apply_end_turn_status_damage
from engine.stat_modifiers import get_stat_change_message, get_modified_speed, get_accuracy_multiplier
from engine.display import format_pokemon_status, format_move_name
from engine.move_effects import (
    is_special_move, execute_special_move,
    apply_leech_seed_damage, decrement_screen_turns,
    TWO_TURN_MOVES, TRAPPING_MOVES, get_multi_hit_count
)
from models.enums import StatType, Status


def execute_turn(attacker: Pokemon, defender: Pokemon, move: Move, all_moves: list = None):
    """Ejecuta un turno de batalla completo"""
    logger.debug(f"Turn: {attacker.name} using {move.name} against {defender.name}")

    # Check if must recharge (Hyper Beam)
    if attacker.must_recharge:
        print(f"\n{attacker.name} debe recargar!")
        attacker.must_recharge = False
        return

    # Check if locked into a multi-turn move (Thrash, Petal-Dance)
    is_multi_turn = False
    is_charging = False
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

    # Check status effects BEFORE announcing move (so we don't show move if can't attack)
    can_attack = apply_status_effects(attacker)

    # If Pokemon can't attack due to status, don't announce the move
    if not can_attack:
        # Reset multi-turn if interrupted by status
        if is_multi_turn and attacker.multi_turn_counter <= 0:
            attacker.multi_turn_move = None
            attacker.confusion_turns = random.randint(2, 5)
            print(f"¡{attacker.name} está confundido por el cansancio!")
        return

    # Now announce the move (Pokemon can attack)
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
            return

        print(f"\n{attacker.name} usa {move_display}!")

    # Track last move used (for Mirror Move)
    attacker.last_move_used = move.name

    # Chequear PP
    if not move.has_pp():
        print(f"¡No hay PP para {move.name}!")
        return

    move.use()

    # Check if defender is semi-invulnerable (Dig/Fly)
    if defender.is_semi_invulnerable:
        print(f"¡El ataque falló! ({defender.name} está fuera de alcance)")
        return

    # Chequear accuracy (applying accuracy/evasion stat stages)
    accuracy_multiplier = get_accuracy_multiplier(attacker, defender)
    final_accuracy = move.accuracy * accuracy_multiplier
    if random.randint(1, 100) > final_accuracy:
        print(f"¡El ataque falló!")
        # Handle crash damage for High-Jump-Kick/Jump-Kick
        if move.name in ("High-Jump-Kick", "Jump-Kick"):
            crash_damage = max(1, attacker.max_hp // 8)
            attacker.take_damage(crash_damage)
            print(f"¡{attacker.name} se estrelló y recibió {crash_damage} de daño!")
            print(f"  {format_pokemon_status(attacker)}")
        return

    # Handle special moves (fixed damage, OHKO, recovery, etc.)
    if is_special_move(move):
        damage, message = execute_special_move(attacker, defender, move, all_moves)

        # Handle Metronome/Mirror Move (damage = -1 means execute another move)
        if damage == -1 and "|" in message:
            msg_parts = message.split("|")
            print(msg_parts[0])  # Print the "Metronome chose X!" message
            chosen_move_name = msg_parts[1]
            # Find and execute the chosen move
            if all_moves:
                for m in all_moves:
                    if m.name == chosen_move_name:
                        # Recursively execute the chosen move
                        execute_turn(attacker, defender, m, all_moves)
                        return
            return

        # Handle HP drain moves (-2)
        if damage == -2 and "|" in message:
            # Calculate normal damage, then heal attacker
            actual_damage, is_crit, effectiveness = calculate_damage(attacker, defender, move)
            if effectiveness == 0:
                print(f"No afecta a {defender.name}...")
                return
            actual_damage = apply_damage_to_target(defender, actual_damage, False)
            if is_crit:
                print("¡Golpe crítico!")
            if effectiveness > 1:
                print("¡Es súper efectivo!")
            elif effectiveness < 1:
                print("No es muy efectivo...")
            if actual_damage > 0:
                print(f"{defender.name} recibe {actual_damage} de daño!")
                print(f"  {format_pokemon_status(defender)}")
                # Heal attacker for 50% of damage dealt
                heal_amount = max(1, actual_damage // 2)
                actual_heal = min(heal_amount, attacker.max_hp - attacker.current_hp)
                attacker.current_hp += actual_heal
                print(f"¡{attacker.name} absorbió {actual_heal} HP!")
                print(f"  {format_pokemon_status(attacker)}")
            return

        # Handle self-destruct moves (-3)
        if damage == -3 and "|" in message:
            # Calculate and deal damage (defense is halved in Gen 1)
            actual_damage, is_crit, effectiveness = calculate_damage(attacker, defender, move)
            # In Gen 1, Explosion/Self-Destruct halves defense
            actual_damage *= 2
            if effectiveness == 0:
                print(f"No afecta a {defender.name}...")
            else:
                actual_damage = apply_damage_to_target(defender, actual_damage, True)
                if is_crit:
                    print("¡Golpe crítico!")
                if effectiveness > 1:
                    print("¡Es súper efectivo!")
                elif effectiveness < 1:
                    print("No es muy efectivo...")
                if actual_damage > 0:
                    print(f"{defender.name} recibe {actual_damage} de daño!")
                    print(f"  {format_pokemon_status(defender)}")
            # User faints
            attacker.current_hp = 0
            print(f"¡{attacker.name} se debilitó por la explosión!")
            return

        # Handle crash damage moves (-4) - normal attack, crash handled on miss above
        if damage == -4 and "|" in message:
            # Normal damage calculation
            actual_damage, is_crit, effectiveness = calculate_damage(attacker, defender, move)
            if effectiveness == 0:
                print(f"No afecta a {defender.name}...")
                return
            actual_damage = apply_damage_to_target(defender, actual_damage, True)
            if is_crit:
                print("¡Golpe crítico!")
            if effectiveness > 1:
                print("¡Es súper efectivo!")
            elif effectiveness < 1:
                print("No es muy efectivo...")
            if actual_damage > 0:
                print(f"{defender.name} recibe {actual_damage} de daño!")
                print(f"  {format_pokemon_status(defender)}")
            return

        # Handle recharge moves (-5) like Hyper Beam
        if damage == -5 and "|" in message:
            # Normal damage calculation
            actual_damage, is_crit, effectiveness = calculate_damage(attacker, defender, move)
            if effectiveness == 0:
                print(f"No afecta a {defender.name}...")
                return
            actual_damage = apply_damage_to_target(defender, actual_damage, move.category == MoveCategory.PHYSICAL)
            if is_crit:
                print("¡Golpe crítico!")
            if effectiveness > 1:
                print("¡Es súper efectivo!")
            elif effectiveness < 1:
                print("No es muy efectivo...")
            if actual_damage > 0:
                print(f"{defender.name} recibe {actual_damage} de daño!")
                print(f"  {format_pokemon_status(defender)}")
            # Must recharge next turn (only if damage was dealt in Gen 1)
            if actual_damage > 0:
                attacker.must_recharge = True
            return

        # Handle charge moves (-6) like Solar Beam, Dig, Fly
        if damage == -6 and "|" in message:
            move_name = message.split("|")[1]
            move_data = TWO_TURN_MOVES.get(move_name, {})
            attacker.is_charging = True
            attacker.charging_move = move
            if move_data.get("semi_invulnerable"):
                attacker.is_semi_invulnerable = True
                print(f"¡{attacker.name} se escondió bajo tierra!" if move_name == "Dig" else f"¡{attacker.name} voló muy alto!")
            elif move_data.get("defense_boost"):
                # Skull Bash raises defense
                attacker.modify_stat_stage(StatType.DEFENSE, 1)
                print(f"¡{attacker.name} está preparando el ataque!")
            else:
                print(f"¡{attacker.name} está cargando energía!")
            return

        # Handle multi-turn moves (-7) like Thrash, Petal-Dance
        if damage == -7 and "|" in message:
            # Start multi-turn attack (2-3 turns)
            attacker.multi_turn_move = move
            attacker.multi_turn_counter = random.randint(2, 3)
            # Fall through to deal damage normally
            pass
        # Handle Rage (-8)
        elif damage == -8 and "|" in message:
            attacker.is_raging = True
            # Fall through to deal damage normally
            pass
        # Handle trapping moves (-9) like Wrap, Bind
        elif damage == -9 and "|" in message:
            # Start trapping (2-5 turns in Gen 1)
            if not defender.is_trapped:
                defender.is_trapped = True
                defender.trap_turns = random.randint(2, 5)
                defender.trapped_by = attacker
            # Deal damage
            actual_damage, is_crit, effectiveness = calculate_damage(attacker, defender, move)
            if effectiveness == 0:
                print(f"No afecta a {defender.name}...")
                defender.is_trapped = False
                defender.trap_turns = 0
                defender.trapped_by = None
                return
            actual_damage = apply_damage_to_target(defender, actual_damage, True)
            if is_crit:
                print("¡Golpe crítico!")
            if effectiveness > 1:
                print("¡Es súper efectivo!")
            elif effectiveness < 1:
                print("No es muy efectivo...")
            if actual_damage > 0:
                print(f"{defender.name} recibe {actual_damage} de daño!")
                print(f"¡{defender.name} está atrapado por {move.name}!")
                print(f"  {format_pokemon_status(defender)}")
            return

        # For damage codes -7 and -8 that fell through, deal normal damage
        if damage in (-7, -8):
            actual_damage, is_crit, effectiveness = calculate_damage(attacker, defender, move)
            if effectiveness == 0:
                print(f"No afecta a {defender.name}...")
                return
            actual_damage = apply_damage_to_target(defender, actual_damage, True)
            if is_crit:
                print("¡Golpe crítico!")
            if effectiveness > 1:
                print("¡Es súper efectivo!")
            elif effectiveness < 1:
                print("No es muy efectivo...")
            if actual_damage > 0:
                print(f"{defender.name} recibe {actual_damage} de daño!")
                print(f"  {format_pokemon_status(defender)}")
            return

        # Handle multi-hit moves (-10) like Fury Attack, Pin Missile
        if damage == -10 and "|" in message:
            num_hits = get_multi_hit_count()
            total_damage = 0
            is_physical = move.category == MoveCategory.PHYSICAL

            for hit in range(num_hits):
                if not defender.is_alive():
                    break
                hit_damage, is_crit, effectiveness = calculate_damage(attacker, defender, move)
                if effectiveness == 0:
                    print(f"No afecta a {defender.name}...")
                    return
                hit_damage = apply_damage_to_target(defender, hit_damage, is_physical)
                total_damage += hit_damage
                if is_crit:
                    print(f"¡Golpe {hit + 1}: Crítico!")

            if effectiveness > 1:
                print("¡Es súper efectivo!")
            elif effectiveness < 1:
                print("No es muy efectivo...")
            print(f"¡Golpeó {num_hits} veces! Daño total: {total_damage}")
            print(f"  {format_pokemon_status(defender)}")
            return

        # Handle fixed 2-hit moves (-11) like Double Kick, Bonemerang
        if damage == -11 and "|" in message:
            total_damage = 0
            is_physical = move.category == MoveCategory.PHYSICAL
            hits = 0

            for hit in range(2):
                if not defender.is_alive():
                    break
                hit_damage, is_crit, effectiveness = calculate_damage(attacker, defender, move)
                if effectiveness == 0:
                    print(f"No afecta a {defender.name}...")
                    return
                hit_damage = apply_damage_to_target(defender, hit_damage, is_physical)
                total_damage += hit_damage
                hits += 1
                if is_crit:
                    print(f"¡Golpe {hit + 1}: Crítico!")

            if effectiveness > 1:
                print("¡Es súper efectivo!")
            elif effectiveness < 1:
                print("No es muy efectivo...")
            print(f"¡Golpeó {hits} veces! Daño total: {total_damage}")
            print(f"  {format_pokemon_status(defender)}")
            return

        # Handle Twineedle (-12) - 2 hits with 20% poison chance each
        if damage == -12 and "|" in message:
            total_damage = 0
            is_physical = True  # Twineedle is physical
            hits = 0

            for hit in range(2):
                if not defender.is_alive():
                    break
                hit_damage, is_crit, effectiveness = calculate_damage(attacker, defender, move)
                if effectiveness == 0:
                    print(f"No afecta a {defender.name}...")
                    return
                hit_damage = apply_damage_to_target(defender, hit_damage, is_physical)
                total_damage += hit_damage
                hits += 1
                if is_crit:
                    print(f"¡Golpe {hit + 1}: Crítico!")
                # 20% poison chance per hit (only if no substitute and no existing status)
                if defender.substitute_hp == 0 and defender.status == Status.NONE:
                    if random.randint(1, 100) <= 20:
                        defender.status = Status.POISON
                        print(f"¡{defender.name} fue envenenado!")

            if effectiveness > 1:
                print("¡Es súper efectivo!")
            elif effectiveness < 1:
                print("No es muy efectivo...")
            print(f"¡Golpeó {hits} veces! Daño total: {total_damage}")
            print(f"  {format_pokemon_status(defender)}")
            return

        if message:
            print(message)
        if damage > 0:
            # Apply damage (respecting Substitute)
            damage = apply_damage_to_target(defender, damage, False)
            if damage > 0:
                print(f"  {format_pokemon_status(defender)}")
        elif damage == 0 and message:
            # Show attacker status for self-targeting moves like Recover/Rest
            print(f"  {format_pokemon_status(attacker)}")
        return

    # Calcular daño normal
    damage, is_critical, effectiveness = calculate_damage(attacker, defender, move)

    # Apply screens (Reflect/Light Screen reduce damage by half)
    is_physical = move.category == MoveCategory.PHYSICAL
    if is_physical and defender.has_reflect:
        damage = damage // 2
        print("¡Reflect reduce el daño!")
    elif not is_physical and defender.has_light_screen:
        damage = damage // 2
        print("¡Light Screen reduce el daño!")

    if damage > 0:
        # Track damage for Counter
        defender.last_damage_taken = damage
        defender.last_damage_physical = is_physical

        # Apply damage (respecting Substitute)
        actual_damage = apply_damage_to_target(defender, damage, is_physical)

        if is_critical:
            print(f"¡Golpe crítico!")

        if effectiveness > 1:
            print(f"¡Es súper efectivo!")
        elif effectiveness < 1 and effectiveness > 0:
            print(f"No es muy efectivo...")
        elif effectiveness == 0:
            print(f"No afecta a {defender.name}...")

        if actual_damage > 0:
            print(f"{defender.name} recibe {actual_damage} de daño!")
            print(f"  {format_pokemon_status(defender)}")
            # Rage: Attack increases when hit
            if defender.is_raging:
                defender.modify_stat_stage(StatType.ATTACK, 1)
                print(f"¡La furia de {defender.name} aumenta!")

    # Aplicar efecto de estado (outside damage block for status moves like Thunder-Wave)
    # Status moves don't work through Substitute, and don't apply to fainted Pokemon
    if defender.substitute_hp == 0 and defender.is_alive():
        if move.status_effect and random.randint(1, 100) <= move.status_chance:
            if defender.apply_status(move.status_effect):
                print(f"¡{defender.name} está {move.status_effect.value}!")
                print(f"  {format_pokemon_status(defender)}")
            elif defender.status != Status.NONE:
                # Already has a status - show message
                print(f"¡{defender.name} ya tiene un estado alterado!")

    # Aplicar cambios de stats del movimiento (skip if target fainted)
    if move.stat_changes:
        target = attacker if move.target_self else defender

        # Don't apply stat changes to fainted Pokemon
        if not target.is_alive():
            return

        # Check Mist (prevents stat reductions on the protected Pokemon)
        if not move.target_self and target.has_mist:
            # Check if any change is negative
            has_negative = any(change < 0 for change in move.stat_changes.values())
            if has_negative:
                print(f"¡Mist protege a {target.name} de la reducción de estadísticas!")
                return

        for stat, change in move.stat_changes.items():
            actual_change, hit_limit = target.modify_stat_stage(stat, change)
            message = get_stat_change_message(target, stat, actual_change, hit_limit)
            if message:
                print(message)
        # Show updated Pokemon status
        print(f"  {format_pokemon_status(target)}")

    # Daño por estado al final del turno
    apply_end_turn_status_damage(attacker)


def apply_damage_to_target(target: Pokemon, damage: int, is_physical: bool) -> int:
    """
    Apply damage to target, respecting Substitute.

    Returns:
        Actual damage dealt to the Pokemon (0 if absorbed by Substitute)
    """
    if target.substitute_hp > 0:
        # Damage goes to Substitute
        target.substitute_hp -= damage
        if target.substitute_hp <= 0:
            target.substitute_hp = 0
            print(f"¡El sustituto de {target.name} se rompió!")
        else:
            print(f"¡El sustituto absorbió el daño!")
        return 0
    else:
        target.take_damage(damage)
        return damage


def apply_end_of_turn_effects(pokemon1: Pokemon, pokemon2: Pokemon):
    """
    Apply all end-of-turn effects for both Pokemon.
    Call this at the end of each turn in the battle loop.
    """
    messages = []

    # Leech Seed damage
    if pokemon1.is_seeded:
        msg = apply_leech_seed_damage(pokemon1, pokemon2)
        if msg:
            messages.append(msg)
            messages.append(f"  {format_pokemon_status(pokemon1)}")

    if pokemon2.is_seeded:
        msg = apply_leech_seed_damage(pokemon2, pokemon1)
        if msg:
            messages.append(msg)
            messages.append(f"  {format_pokemon_status(pokemon2)}")

    # Trapping damage (Wrap, Bind, etc.)
    for trapped, trapper in [(pokemon1, pokemon2), (pokemon2, pokemon1)]:
        if trapped.is_trapped and trapped.trapped_by == trapper:
            trapped.trap_turns -= 1
            # In Gen 1, trapping moves deal damage each turn
            trap_damage = max(1, trapped.max_hp // 16)
            trapped.take_damage(trap_damage)
            messages.append(f"¡{trapped.name} sigue atrapado y recibe {trap_damage} de daño!")
            messages.append(f"  {format_pokemon_status(trapped)}")
            if trapped.trap_turns <= 0:
                trapped.is_trapped = False
                trapped.trapped_by = None
                messages.append(f"¡{trapped.name} se liberó!")

    # Decrement screen turns
    screen_msgs = decrement_screen_turns(pokemon1)
    messages.extend(screen_msgs)

    screen_msgs = decrement_screen_turns(pokemon2)
    messages.extend(screen_msgs)

    # Print all messages
    for msg in messages:
        print(msg)


def determine_turn_order(pokemon1: Pokemon, pokemon2: Pokemon) -> tuple[Pokemon, Pokemon]:
    """Determina quién ataca primero basado en Speed (con stat stages aplicados)"""
    speed1 = get_modified_speed(pokemon1)
    speed2 = get_modified_speed(pokemon2)
    logger.debug(f"Speed comparison: {pokemon1.name}={speed1}, {pokemon2.name}={speed2}")

    if speed1 > speed2:
        return pokemon1, pokemon2
    elif speed2 > speed1:
        return pokemon2, pokemon1
    else:
        # En caso de empate, aleatorio
        result = random.choice([(pokemon1, pokemon2), (pokemon2, pokemon1)])
        logger.debug(f"Speed tie, random order: {result[0].name} goes first")
        return result
