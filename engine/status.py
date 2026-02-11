import random
from models.pokemon import Pokemon
from models.enums import Status
from engine.stat_modifiers import get_modified_attack, get_modified_defense
from engine.battle_logger import get_battle_logger
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

def apply_status_effects(pokemon: Pokemon) -> bool:
    """
    Aplica efectos de estado al inicio del turno.
    Retorna True si el Pokémon puede atacar, False si no.
    """
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
                return False

    if pokemon.status == Status.FREEZE:
        # Gen 1: Frozen Pokemon never thaw on their own.
        # They can only be thawed by being hit by a Fire-type move.
        print(f"{pokemon.name} está congelado!")
        return False
    
    if pokemon.status == Status.SLEEP:
        pokemon.sleep_counter -= 1
        if pokemon.sleep_counter <= 0:
            pokemon.status = Status.NONE
            print(f"{pokemon.name} despertó!")
            # Gen 1: Pokemon cannot attack on the turn it wakes up
            return False
        print(f"{pokemon.name} está dormido!")
        return False
    
    if pokemon.status == Status.PARALYSIS:
        if random.random() < config.PARALYSIS_FAIL_CHANCE:
            print(f"{pokemon.name} está paralizado!")
            return False
    
    return True

def apply_end_turn_status_damage(pokemon: Pokemon):
    """Aplica daño de estado al final del turno"""
    if pokemon.status == Status.BURN:
        burn_damage = max(1, pokemon.max_hp // config.BURN_DAMAGE_FRACTION)
        pokemon.take_damage(burn_damage)
        print(f"{pokemon.name} sufre {burn_damage} de daño por quemadura!")
        blog = get_battle_logger()
        if blog:
            blog.log_effect("burn", pokemon.name, damage=burn_damage)

    if pokemon.status == Status.POISON:
        poison_damage = max(1, pokemon.max_hp // config.POISON_DAMAGE_FRACTION)
        pokemon.take_damage(poison_damage)
        print(f"{pokemon.name} sufre {poison_damage} de daño por envenenamiento!")
        blog = get_battle_logger()
        if blog:
            blog.log_effect("poison", pokemon.name, damage=poison_damage)
