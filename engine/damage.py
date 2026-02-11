import random
from models.pokemon import Pokemon
from models.move import Move
from models.enums import MoveCategory, Status, Type
from engine.type_chart import get_effectiveness
from engine.stat_modifiers import get_modified_attack, get_modified_defense
import config

def calculate_critical_hit(attacker: Pokemon) -> bool:
    """Determines if attack is critical using Gen1 formula: BaseSpeed/512"""
    # Gen 1 uses species base Speed for crit chance, not level-calculated battle Speed.
    speed_for_crit = attacker.species_base_stats.speed if hasattr(attacker, "species_base_stats") else attacker.base_stats.speed
    crit_chance = speed_for_crit / 512

    # Gen 1 Focus Energy bug: crit chance is divided by 4 instead of increased
    if hasattr(attacker, 'focus_energy') and attacker.focus_energy:
        crit_chance /= 4

    # Cap at 100%
    crit_chance = min(crit_chance, 1.0)

    return random.random() < crit_chance

def get_attack_defense_stats(attacker: Pokemon, defender: Pokemon, move: Move) -> tuple[int, int]:
    """Selects appropriate attack/defense stats based on move category with stat stages applied"""
    is_physical = (move.category == MoveCategory.PHYSICAL)

    # Get stats with stat stage modifiers applied
    attack = get_modified_attack(attacker, is_physical)
    defense = get_modified_defense(defender, is_physical)

    return attack, defense

def calculate_base_damage(level: int, power: int, attack: int, defense: int) -> float:
    """Gen1 base damage formula: ((((2*Level/5+2)*Power*A/D)/50)+2)"""
    level_component = (2 * level / 5 + 2)
    return ((level_component * power * attack / defense) / 50) + 2

def get_stab_multiplier(move_type: Type, attacker_types: list[Type]) -> float:
    """Returns STAB multiplier (1.5 if type matches, 1.0 otherwise)"""
    return config.STAB_MULTIPLIER if move_type in attacker_types else 1.0

def get_random_factor() -> float:
    """Gen1 random factor: 217-255 / 255"""
    return random.randint(config.MIN_RANDOM_FACTOR, config.MAX_RANDOM_FACTOR) / config.RANDOM_DIVISOR

def apply_burn_modifier(damage: int, attacker: Pokemon, move: Move) -> int:
    """Halves physical damage if attacker is burned (Gen1 mechanic)"""
    if attacker.status == Status.BURN and move.category == MoveCategory.PHYSICAL:
        return int(damage * config.BURN_ATTACK_MULTIPLIER)
    return damage

def calculate_damage(attacker: Pokemon, defender: Pokemon, move: Move,
                     defense_modifier: float = 1.0) -> tuple[int, bool, float]:
    """
    Calcula el daño usando la fórmula de Gen 1.
    Retorna: (damage, is_critical, effectiveness)

    Args:
        defense_modifier: Multiplier applied to defense stat (e.g., 0.5 for Explosion)
    """
    # STATUS moves deal no damage
    if move.category == MoveCategory.STATUS:
        return 0, False, 1.0

    # Calculate critical hit
    is_critical = calculate_critical_hit(attacker)

    # Get appropriate stats (Gen 1 critical hits ignore stat stage modifiers)
    if is_critical:
        if move.category == MoveCategory.PHYSICAL:
            attack = attacker.base_stats.attack
            defense = defender.base_stats.defense
        else:
            attack = attacker.base_stats.special
            defense = defender.base_stats.special
    else:
        attack, defense = get_attack_defense_stats(attacker, defender, move)

    # Apply defense modifier (e.g., Explosion/Self-Destruct halves defense)
    if defense_modifier != 1.0:
        defense = max(1, int(defense * defense_modifier))

    if is_critical:
        attack *= config.CRIT_MULTIPLIER

    # Calculate base damage
    damage = calculate_base_damage(attacker.level, move.power, attack, defense)

    # Apply all multipliers
    stab = get_stab_multiplier(move.type, attacker.types)
    effectiveness = get_effectiveness(move.type, defender.types)
    random_factor = get_random_factor()

    # If type effectiveness is 0 (immunity), no damage is dealt
    if effectiveness == 0:
        return 0, is_critical, effectiveness

    damage = int(damage * stab * effectiveness * random_factor)
    damage = apply_burn_modifier(damage, attacker, move)

    # Minimum 1 damage for non-immune hits
    return max(1, damage), is_critical, effectiveness
