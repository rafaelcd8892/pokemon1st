import random
from models.pokemon import Pokemon
from models.move import Move
from models.enums import MoveCategory, Status
from engine.type_chart import get_effectiveness
import config

def calculate_damage(attacker: Pokemon, defender: Pokemon, move: Move) -> tuple[int, bool, float]:
    """
    Calcula el daño usando la fórmula de Gen 1.
    Retorna: (damage, is_critical, effectiveness)
    """
    if move.category == MoveCategory.STATUS:
        return 0, False, 1.0
    
    # Determinar si es crítico (Gen 1: BaseSpeed/512)
    crit_chance = attacker.base_stats.speed / 512
    is_critical = random.random() < crit_chance
    
    # Stats de ataque y defensa
    if move.category == MoveCategory.PHYSICAL:
        attack = attacker.base_stats.attack
        defense = defender.base_stats.defense
    else:  # SPECIAL
        attack = attacker.base_stats.special
        defense = defender.base_stats.special
    
    # Crítico ignora modificadores de stats en Gen 1
    if is_critical:
        attack *= config.CRIT_MULTIPLIER
    
    # Cálculo base: ((((2 * Level / 5 + 2) * Power * A/D) / 50) + 2)
    level_component = (2 * attacker.level / 5 + 2)
    damage = ((level_component * move.power * attack / defense) / 50) + 2
    
    # STAB (Same Type Attack Bonus)
    stab = config.STAB_MULTIPLIER if move.type in attacker.types else 1.0
    
    # Efectividad de tipos
    effectiveness = get_effectiveness(move.type, defender.types)
    
    # Random factor (Gen 1: 217-255 / 255)
    random_factor = random.randint(config.MIN_RANDOM_FACTOR, config.MAX_RANDOM_FACTOR) / config.RANDOM_DIVISOR
    
    # Aplicar modificadores
    damage = int(damage * stab * effectiveness * random_factor)
    
    # Burn reduce daño físico en Gen 1
    if attacker.status == Status.BURN and move.category == MoveCategory.PHYSICAL:
        damage = int(damage * config.BURN_ATTACK_MULTIPLIER)
    
    return max(1, damage), is_critical, effectiveness