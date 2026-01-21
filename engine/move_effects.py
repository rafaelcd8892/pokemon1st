"""Special move effects for moves with unique mechanics"""

import random
from models.pokemon import Pokemon
from models.move import Move
from models.enums import Status, Type

# Moves with fixed damage (ignore stats)
FIXED_DAMAGE_MOVES = {
    "Dragon-Rage": 40,
    "Sonic-Boom": 20,
}

# HP drain moves (heal 50% of damage dealt)
HP_DRAIN_MOVES = {"Absorb", "Mega-Drain", "Leech-Life"}

# Dream Eater - only works on sleeping targets, heals 50%
DREAM_EATER_MOVE = "Dream-Eater"

# Self-destruct moves (user faints)
SELF_DESTRUCT_MOVES = {"Explosion", "Self-Destruct"}

# Crash damage moves (take damage if miss)
CRASH_DAMAGE_MOVES = {"High-Jump-Kick", "Jump-Kick"}

# Two-turn moves (charge first turn, attack second)
TWO_TURN_MOVES = {
    "Hyper-Beam": {"recharge": True},      # Attack then recharge
    "Solar-Beam": {"charge": True},         # Charge then attack
    "Dig": {"charge": True, "semi_invulnerable": True},
    "Fly": {"charge": True, "semi_invulnerable": True},
    "Skull-Bash": {"charge": True, "defense_boost": True},
    "Sky-Attack": {"charge": True},
    "Razor-Wind": {"charge": True},
}

# Multi-turn moves (2-3 turns, then confusion)
MULTI_TURN_MOVES = {"Thrash", "Petal-Dance"}

# Rage - increases attack when hit
RAGE_MOVE = "Rage"

# Trapping moves (prevent switching, deal damage each turn)
TRAPPING_MOVES = {"Wrap", "Bind", "Clamp", "Fire-Spin"}

# Multi-hit moves (2-5 hits with Gen 1 distribution: 37.5%, 37.5%, 12.5%, 12.5%)
MULTI_HIT_MOVES = {"Fury-Attack", "Fury-Swipes", "Pin-Missile", "Spike-Cannon", "Barrage", "Comet-Punch", "Double-Slap"}

# Fixed 2-hit moves
DOUBLE_HIT_MOVES = {"Double-Kick", "Bonemerang"}

# Twineedle - 2 hits with poison chance on each
TWINEEDLE_MOVE = "Twineedle"

# Moves that deal damage equal to user's level
LEVEL_DAMAGE_MOVES = {"Night-Shade", "Seismic-Toss"}

# OHKO moves (one-hit knockout)
OHKO_MOVES = {"Guillotine", "Horn-Drill"}

# Moves that heal the user
RECOVERY_MOVES = {
    "Recover": 0.5,      # Heals 50% of max HP
    "Soft-Boiled": 0.5,  # Heals 50% of max HP
}

# Screen moves (reduce damage)
SCREEN_MOVES = {"Light-Screen", "Reflect"}

# Moves with unique special effects
SPECIAL_EFFECT_MOVES = {
    "Super-Fang",    # Deals 50% of target's current HP
    "Haze",          # Resets all stat stages
    "Rest",          # Full heal + sleep
    "Leech-Seed",    # Drains HP each turn
    "Mist",          # Prevents stat reductions
    "Focus-Energy",  # Increases crit rate
    "Substitute",    # Creates decoy
    "Counter",       # Returns 2x physical damage
    "Disable",       # Disables a move
    "Metronome",     # Uses random move
    "Mirror-Move",   # Copies opponent's last move
    "Transform",     # Copies opponent
    "Splash",        # Does nothing
    "Teleport",      # Does nothing in battle
    "Roar",          # Does nothing in 1v1 trainer battle
    "Whirlwind",     # Does nothing in 1v1 trainer battle
    "Conversion",    # Changes type (Porygon only)
}

# All moves that need special handling
ALL_SPECIAL_MOVES = (
    set(FIXED_DAMAGE_MOVES.keys()) |
    LEVEL_DAMAGE_MOVES |
    OHKO_MOVES |
    set(RECOVERY_MOVES.keys()) |
    SCREEN_MOVES |
    SPECIAL_EFFECT_MOVES |
    HP_DRAIN_MOVES |
    {DREAM_EATER_MOVE} |
    SELF_DESTRUCT_MOVES |
    CRASH_DAMAGE_MOVES |
    set(TWO_TURN_MOVES.keys()) |
    MULTI_TURN_MOVES |
    {RAGE_MOVE} |
    TRAPPING_MOVES |
    MULTI_HIT_MOVES |
    DOUBLE_HIT_MOVES |
    {TWINEEDLE_MOVE}
)


def is_special_move(move: Move) -> bool:
    """Check if a move has special handling"""
    return move.name in ALL_SPECIAL_MOVES


def execute_special_move(attacker: Pokemon, defender: Pokemon, move: Move, all_moves: list = None) -> tuple[int, str]:
    """
    Execute a special move effect.

    Args:
        attacker: The attacking Pokemon
        defender: The defending Pokemon
        move: The move being used
        all_moves: List of all available moves (for Metronome)

    Returns:
        tuple: (damage_dealt, message) - damage is 0 for non-damaging effects
    """
    # Fixed damage moves
    if move.name in FIXED_DAMAGE_MOVES:
        damage = FIXED_DAMAGE_MOVES[move.name]
        return damage, f"¡{move.name} inflige {damage} puntos de daño fijo!"

    # Level-based damage moves
    if move.name in LEVEL_DAMAGE_MOVES:
        damage = attacker.level
        return damage, f"¡{move.name} inflige {damage} puntos de daño!"

    # OHKO moves
    if move.name in OHKO_MOVES:
        # In Gen 1, OHKO moves fail if attacker's speed < defender's speed
        if attacker.base_stats.speed < defender.base_stats.speed:
            return 0, "¡El ataque falló! (El objetivo es más rápido)"
        damage = defender.current_hp  # KO damage
        return damage, "¡Es un golpe de un solo golpe!"

    # Super-Fang - deals 50% of target's current HP
    if move.name == "Super-Fang":
        damage = max(1, defender.current_hp // 2)
        return damage, f"¡{move.name} reduce los HP a la mitad!"

    # Recovery moves
    if move.name in RECOVERY_MOVES:
        heal_percent = RECOVERY_MOVES[move.name]
        heal_amount = int(attacker.max_hp * heal_percent)
        actual_heal = min(heal_amount, attacker.max_hp - attacker.current_hp)
        attacker.current_hp = min(attacker.max_hp, attacker.current_hp + heal_amount)
        if actual_heal > 0:
            return 0, f"¡{attacker.name} recuperó {actual_heal} HP!"
        else:
            return 0, f"¡{attacker.name} ya tiene los HP al máximo!"

    # Haze - reset all stat stages for both Pokemon
    if move.name == "Haze":
        attacker.reset_stat_stages()
        defender.reset_stat_stages()
        # Also clear confusion and volatile status
        attacker.confusion_turns = 0
        defender.confusion_turns = 0
        # Clear Leech Seed
        attacker.is_seeded = False
        defender.is_seeded = False
        # Clear Focus Energy
        attacker.focus_energy = False
        defender.focus_energy = False
        return 0, "¡Todas las modificaciones de estadísticas fueron eliminadas!"

    # Rest - full heal + sleep for 2 turns
    if move.name == "Rest":
        if attacker.current_hp == attacker.max_hp:
            return 0, f"¡{attacker.name} ya tiene los HP al máximo!"
        heal_amount = attacker.max_hp - attacker.current_hp
        attacker.current_hp = attacker.max_hp
        attacker.status = Status.SLEEP
        attacker.sleep_counter = 2  # Rest always sleeps for exactly 2 turns in Gen 1
        return 0, f"¡{attacker.name} recuperó todos sus HP y se durmió!"

    # Leech Seed - plants a seed that drains HP each turn
    if move.name == "Leech-Seed":
        # Grass types are immune
        if Type.GRASS in defender.types:
            return 0, f"¡No afecta a {defender.name}! (tipo Planta)"
        if defender.is_seeded:
            return 0, f"¡{defender.name} ya está plantado!"
        defender.is_seeded = True
        return 0, f"¡{defender.name} fue plantado con Leech Seed!"

    # Light Screen - reduces special damage for 5 turns
    if move.name == "Light-Screen":
        if attacker.has_light_screen:
            return 0, "¡Light Screen ya está activo!"
        attacker.has_light_screen = True
        attacker.light_screen_turns = 5
        return 0, f"¡{attacker.name} levantó Light Screen!"

    # Reflect - reduces physical damage for 5 turns
    if move.name == "Reflect":
        if attacker.has_reflect:
            return 0, "¡Reflect ya está activo!"
        attacker.has_reflect = True
        attacker.reflect_turns = 5
        return 0, f"¡{attacker.name} levantó Reflect!"

    # Mist - prevents stat reductions for 5 turns
    if move.name == "Mist":
        if attacker.has_mist:
            return 0, "¡Mist ya está activo!"
        attacker.has_mist = True
        attacker.mist_turns = 5
        return 0, f"¡{attacker.name} está protegido por Mist!"

    # Focus Energy - increases critical hit ratio
    if move.name == "Focus-Energy":
        if attacker.focus_energy:
            return 0, f"¡{attacker.name} ya está concentrado!"
        attacker.focus_energy = True
        # Note: In Gen 1, Focus Energy was bugged and actually DIVIDED crit rate by 4
        # We implement the intended behavior (multiply by 4)
        return 0, f"¡{attacker.name} se está concentrando!"

    # Substitute - creates a decoy with 25% of user's HP
    if move.name == "Substitute":
        if attacker.substitute_hp > 0:
            return 0, f"¡{attacker.name} ya tiene un sustituto!"
        hp_cost = attacker.max_hp // 4
        if attacker.current_hp <= hp_cost:
            return 0, f"¡{attacker.name} no tiene suficiente HP para crear un sustituto!"
        attacker.current_hp -= hp_cost
        attacker.substitute_hp = hp_cost + 1  # Substitute has HP equal to cost + 1
        return 0, f"¡{attacker.name} creó un sustituto!"

    # Counter - returns 2x the physical damage received
    if move.name == "Counter":
        if not attacker.last_damage_physical or attacker.last_damage_taken == 0:
            return 0, "¡Pero falló!"
        damage = attacker.last_damage_taken * 2
        return damage, f"¡Counter devuelve {damage} de daño!"

    # Disable - disables one of the opponent's moves
    if move.name == "Disable":
        if defender.disabled_move:
            return 0, f"¡{defender.name} ya tiene un movimiento deshabilitado!"
        # Pick a random move from defender
        available_moves = [m for m in defender.moves if m.pp > 0]
        if not available_moves:
            return 0, "¡Pero falló!"
        disabled = random.choice(available_moves)
        defender.disabled_move = disabled.name
        defender.disable_turns = random.randint(1, 8)  # Gen 1: 1-8 turns
        return 0, f"¡{disabled.name} de {defender.name} fue deshabilitado!"

    # Metronome - uses a random move
    if move.name == "Metronome":
        if all_moves is None:
            return 0, "¡Pero falló! (No hay movimientos disponibles)"
        # Exclude certain moves from Metronome
        excluded = {"Metronome", "Struggle", "Mirror-Move"}
        valid_moves = [m for m in all_moves if m.name not in excluded]
        if not valid_moves:
            return 0, "¡Pero falló!"
        chosen_move = random.choice(valid_moves)
        # Return special code to indicate Metronome chose a move
        return -1, f"¡Metronome eligió {chosen_move.name}!|{chosen_move.name}"

    # Mirror Move - uses the opponent's last move
    if move.name == "Mirror-Move":
        if defender.last_move_used is None:
            return 0, "¡Pero falló! (El oponente no ha usado ningún movimiento)"
        # Return special code to indicate Mirror Move
        return -1, f"¡Mirror Move copia {defender.last_move_used}!|{defender.last_move_used}"

    # Transform - copies the opponent completely
    if move.name == "Transform":
        # Copy stats (except HP)
        attacker.base_stats.attack = defender.base_stats.attack
        attacker.base_stats.defense = defender.base_stats.defense
        attacker.base_stats.special = defender.base_stats.special
        attacker.base_stats.speed = defender.base_stats.speed
        # Copy types
        attacker.types = defender.types.copy()
        # Copy stat stages
        for stat in attacker.stat_stages:
            attacker.stat_stages[stat] = defender.stat_stages[stat]
        # Copy moves (with 5 PP each in Gen 1)
        attacker.moves = []
        for m in defender.moves:
            copied_move = Move(
                name=m.name, type=m.type, category=m.category,
                power=m.power, accuracy=m.accuracy, pp=5, max_pp=5,
                status_effect=m.status_effect, status_chance=m.status_chance,
                stat_changes=m.stat_changes.copy() if m.stat_changes else {},
                target_self=m.target_self
            )
            attacker.moves.append(copied_move)
        return 0, f"¡{attacker.name} se transformó en {defender.name}!"

    # Conversion - changes user's type to match one of their moves
    if move.name == "Conversion":
        if attacker.moves:
            new_type = attacker.moves[0].type  # Gen 1: uses first move's type
            attacker.types = [new_type]
            return 0, f"¡{attacker.name} cambió su tipo a {new_type.value}!"
        return 0, "¡Pero falló!"

    # Moves that intentionally do nothing
    if move.name == "Splash":
        return 0, "¡No pasó nada!"

    if move.name == "Teleport":
        return 0, "¡No pasó nada! (No se puede huir de una batalla de entrenador)"

    if move.name in ("Roar", "Whirlwind"):
        return 0, "¡Pero falló! (No tiene efecto en batallas 1 vs 1)"

    # HP Drain moves - these return a special code to indicate drain
    # The actual damage calculation happens in battle.py, we just flag it
    if move.name in HP_DRAIN_MOVES:
        return -2, f"DRAIN|{move.name}"

    # Dream Eater - only works on sleeping targets
    if move.name == DREAM_EATER_MOVE:
        if defender.status != Status.SLEEP:
            return 0, "¡Pero falló! (El objetivo no está dormido)"
        return -2, f"DRAIN|{move.name}"

    # Self-destruct moves - user faints after attack
    if move.name in SELF_DESTRUCT_MOVES:
        return -3, f"SELF_DESTRUCT|{move.name}"

    # Crash damage moves - handled in battle.py for miss case
    if move.name in CRASH_DAMAGE_MOVES:
        return -4, f"CRASH|{move.name}"

    # Two-turn moves
    if move.name in TWO_TURN_MOVES:
        move_data = TWO_TURN_MOVES[move.name]
        if move_data.get("recharge"):
            # Hyper Beam: attack, then recharge next turn
            return -5, f"RECHARGE|{move.name}"
        else:
            # Charge moves: charge first, attack second
            return -6, f"CHARGE|{move.name}"

    # Multi-turn moves (Thrash, Petal-Dance)
    if move.name in MULTI_TURN_MOVES:
        return -7, f"MULTI_TURN|{move.name}"

    # Rage
    if move.name == RAGE_MOVE:
        return -8, f"RAGE|{move.name}"

    # Trapping moves
    if move.name in TRAPPING_MOVES:
        return -9, f"TRAP|{move.name}"

    # Multi-hit moves (2-5 hits)
    if move.name in MULTI_HIT_MOVES:
        return -10, f"MULTI_HIT|{move.name}"

    # Fixed 2-hit moves
    if move.name in DOUBLE_HIT_MOVES:
        return -11, f"DOUBLE_HIT|{move.name}"

    # Twineedle (2 hits with poison chance)
    if move.name == TWINEEDLE_MOVE:
        return -12, f"TWINEEDLE|{move.name}"

    # Fallback - shouldn't reach here
    return 0, ""


def get_multi_hit_count() -> int:
    """
    Returns number of hits for multi-hit moves using Gen 1 distribution.
    2 hits: 37.5% (3/8)
    3 hits: 37.5% (3/8)
    4 hits: 12.5% (1/8)
    5 hits: 12.5% (1/8)
    """
    roll = random.randint(1, 8)
    if roll <= 3:
        return 2
    elif roll <= 6:
        return 3
    elif roll == 7:
        return 4
    else:
        return 5


def apply_leech_seed_damage(seeded_pokemon: Pokemon, seed_owner: Pokemon) -> str:
    """
    Apply Leech Seed damage at end of turn.

    Returns:
        Message describing the effect
    """
    if not seeded_pokemon.is_seeded or not seeded_pokemon.is_alive():
        return ""

    # Drain 1/16 of max HP (minimum 1)
    drain = max(1, seeded_pokemon.max_hp // 16)
    actual_drain = min(drain, seeded_pokemon.current_hp)

    seeded_pokemon.current_hp -= actual_drain

    # Heal the seed owner
    if seed_owner.is_alive():
        heal = min(actual_drain, seed_owner.max_hp - seed_owner.current_hp)
        seed_owner.current_hp += heal

    return f"¡Leech Seed drena {actual_drain} HP de {seeded_pokemon.name}!"


def decrement_screen_turns(pokemon: Pokemon) -> list[str]:
    """
    Decrement screen turns at end of turn.

    Returns:
        List of messages for expired screens
    """
    messages = []

    if pokemon.has_reflect:
        pokemon.reflect_turns -= 1
        if pokemon.reflect_turns <= 0:
            pokemon.has_reflect = False
            messages.append(f"¡El Reflect de {pokemon.name} se desvaneció!")

    if pokemon.has_light_screen:
        pokemon.light_screen_turns -= 1
        if pokemon.light_screen_turns <= 0:
            pokemon.has_light_screen = False
            messages.append(f"¡El Light Screen de {pokemon.name} se desvaneció!")

    if pokemon.has_mist:
        pokemon.mist_turns -= 1
        if pokemon.mist_turns <= 0:
            pokemon.has_mist = False
            messages.append(f"¡El Mist de {pokemon.name} se desvaneció!")

    if pokemon.disable_turns > 0:
        pokemon.disable_turns -= 1
        if pokemon.disable_turns <= 0:
            messages.append(f"¡{pokemon.disabled_move} de {pokemon.name} ya no está deshabilitado!")
            pokemon.disabled_move = None

    return messages
