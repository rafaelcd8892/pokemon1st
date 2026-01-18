import random
from models.pokemon import Pokemon
from models.enums import Status
import config

def apply_confusion_damage(pokemon: Pokemon) -> int:
    """
    Calculates confusion self-damage in Gen1.
    Returns damage dealt to self (40 base power typeless physical attack)
    """
    # Gen1 confusion: 40 base power, uses own Attack vs own Defense
    attack = pokemon.base_stats.attack
    defense = pokemon.base_stats.defense
    level = pokemon.level

    # Simplified Gen1 confusion damage formula
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
        if random.random() < config.FREEZE_THAW_CHANCE:
            pokemon.status = Status.NONE
            print(f"{pokemon.name} se descongeló!")
            return True
        print(f"{pokemon.name} está congelado!")
        return False
    
    if pokemon.status == Status.SLEEP:
        pokemon.sleep_counter -= 1
        if pokemon.sleep_counter <= 0:
            pokemon.status = Status.NONE
            print(f"{pokemon.name} despertó!")
            return True
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
    
    if pokemon.status == Status.POISON:
        poison_damage = max(1, pokemon.max_hp // config.POISON_DAMAGE_FRACTION)
        pokemon.take_damage(poison_damage)
        print(f"{pokemon.name} sufre {poison_damage} de daño por envenenamiento!")
