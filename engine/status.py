import random
from models.pokemon import Pokemon
from models.enums import Status
from engine.stat_modifiers import get_modified_attack, get_modified_defense
from engine.battle_logger import get_battle_logger
from engine.events import get_event_bus
from engine.events.types import (
    StatusPreventedActionEvent, ConfusionSelfHitEvent,
    StatusDamageEvent, StatusCuredEvent,
)
import config

def apply_confusion_damage(pokemon: Pokemon) -> int:
    """
    Calculates confusion self-damage in Gen1.
    Returns damage dealt to self (40 base power typeless physical attack).
    Stat stage modifiers ARE applied in Gen 1.
    """
    # Gen1 confusion: 40 base power, uses own Attack vs own Defense with stat stages
    attack = get_modified_attack(pokemon, is_physical=True)
    defense = get_modified_defense(pokemon, is_physical=True)
    level = pokemon.level

    # Gen1 confusion damage formula
    damage = ((2 * level / 5 + 2) * 40 * attack / defense) / 50 + 2
    return int(damage)

def apply_status_effects(pokemon: Pokemon) -> tuple[bool, str | None]:
    """
    Aplica efectos de estado al inicio del turno.
    Retorna (can_attack, reason) where reason is the prevention cause or None.
    """
    blog = get_battle_logger()
    side = getattr(pokemon, "battle_side", None)

    # Check confusion first (happens before major status)
    if pokemon.is_confused():
        pokemon.confusion_turns -= 1
        if pokemon.confusion_turns <= 0:
            print(f"{pokemon.name} snapped out of confusion!")
        else:
            print(f"{pokemon.name} is confused!")
            # 50% chance to hurt itself
            if random.random() < 0.5:
                confusion_damage = apply_confusion_damage(pokemon)
                pokemon.take_damage(confusion_damage)
                print(f"{pokemon.name} hurt itself in confusion for {confusion_damage} damage!")
                bus = get_event_bus()
                bus.emit(ConfusionSelfHitEvent(
                    turn=bus.current_turn, pokemon_name=pokemon.name,
                    damage=confusion_damage, current_hp=pokemon.current_hp,
                    max_hp=pokemon.max_hp))
                if blog:
                    blog.log_move_prevented(
                        pokemon.name, "", "confused_self_hit",
                        pokemon_side=side,
                        extra_details={"confusion_damage": confusion_damage,
                                       "hp_after": pokemon.current_hp,
                                       "max_hp": pokemon.max_hp})
                    blog.log_effect("confusion_self_hit", pokemon.name,
                                    damage=confusion_damage, pokemon_side=side)
                return False, "confused_self_hit"

    if pokemon.status == Status.FREEZE:
        # Gen 1: Frozen Pokemon never thaw on their own.
        # They can only be thawed by being hit by a Fire-type move.
        print(f"{pokemon.name} está congelado!")
        bus = get_event_bus()
        bus.emit(StatusPreventedActionEvent(
            turn=bus.current_turn, pokemon_name=pokemon.name, status="freeze"))
        if blog:
            blog.log_move_prevented(pokemon.name, "", "frozen", pokemon_side=side)
        return False, "frozen"

    if pokemon.status == Status.SLEEP:
        pokemon.sleep_counter -= 1
        if pokemon.sleep_counter <= 0:
            pokemon.status = Status.NONE
            print(f"{pokemon.name} despertó!")
            bus = get_event_bus()
            bus.emit(StatusCuredEvent(
                turn=bus.current_turn, pokemon_name=pokemon.name,
                status="sleep", reason="natural"))
            bus.emit(StatusPreventedActionEvent(
                turn=bus.current_turn, pokemon_name=pokemon.name, status="sleep_wake"))
            # Gen 1: Pokemon cannot attack on the turn it wakes up
            if blog:
                blog.log_move_prevented(pokemon.name, "", "sleep_wake", pokemon_side=side)
            return False, "sleep_wake"
        print(f"{pokemon.name} está dormido!")
        bus = get_event_bus()
        bus.emit(StatusPreventedActionEvent(
            turn=bus.current_turn, pokemon_name=pokemon.name, status="sleep"))
        if blog:
            blog.log_move_prevented(pokemon.name, "", "asleep", pokemon_side=side)
        return False, "asleep"

    if pokemon.status == Status.PARALYSIS:
        if random.random() < config.PARALYSIS_FAIL_CHANCE:
            print(f"{pokemon.name} está paralizado!")
            bus = get_event_bus()
            bus.emit(StatusPreventedActionEvent(
                turn=bus.current_turn, pokemon_name=pokemon.name, status="paralysis"))
            if blog:
                blog.log_move_prevented(pokemon.name, "", "paralyzed", pokemon_side=side)
            return False, "paralyzed"

    return True, None

def apply_end_turn_status_damage(pokemon: Pokemon):
    """Aplica daño de estado al final del turno"""
    if not pokemon.is_alive():
        return

    if pokemon.status == Status.BURN:
        burn_damage = max(1, pokemon.max_hp // config.BURN_DAMAGE_FRACTION)
        pokemon.take_damage(burn_damage)
        print(f"{pokemon.name} sufre {burn_damage} de daño por quemadura!")
        bus = get_event_bus()
        bus.emit(StatusDamageEvent(
            turn=bus.current_turn, pokemon_name=pokemon.name, status="burn",
            damage=burn_damage, current_hp=pokemon.current_hp, max_hp=pokemon.max_hp))
        blog = get_battle_logger()
        if blog:
            blog.log_effect("burn", pokemon.name, damage=burn_damage, pokemon_side=getattr(pokemon, "battle_side", None))

    if pokemon.status == Status.POISON:
        poison_damage = max(1, pokemon.max_hp // config.POISON_DAMAGE_FRACTION)
        pokemon.take_damage(poison_damage)
        print(f"{pokemon.name} sufre {poison_damage} de daño por envenenamiento!")
        bus = get_event_bus()
        bus.emit(StatusDamageEvent(
            turn=bus.current_turn, pokemon_name=pokemon.name, status="poison",
            damage=poison_damage, current_hp=pokemon.current_hp, max_hp=pokemon.max_hp))
        blog = get_battle_logger()
        if blog:
            blog.log_effect("poison", pokemon.name, damage=poison_damage, pokemon_side=getattr(pokemon, "battle_side", None))
