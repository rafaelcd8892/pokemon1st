"""Stat stage modification system for Pokemon battles"""

from models.enums import StatType
from models.pokemon import Pokemon

# Gen1 stat stage fractions as (numerator, denominator) pairs
# Applied using integer math: stat * numerator // denominator
# Stages range from -6 to +6
STAT_STAGE_FRACTIONS = {
    -6: (2, 8),
    -5: (2, 7),
    -4: (2, 6),
    -3: (2, 5),
    -2: (2, 4),
    -1: (2, 3),
     0: (2, 2),
     1: (3, 2),
     2: (4, 2),
     3: (5, 2),
     4: (6, 2),
     5: (7, 2),
     6: (8, 2),
}

# Float multipliers for accuracy/evasion stages (applied to percentage, not integer stats)
STAT_STAGE_MULTIPLIERS = {
    -6: 2/8, -5: 2/7, -4: 2/6, -3: 2/5, -2: 2/4, -1: 2/3,
     0: 1.0,
     1: 3/2,  2: 4/2,  3: 5/2,  4: 6/2,  5: 7/2,  6: 8/2,
}

def get_stat_multiplier(stage: int) -> float:
    """
    Returns the float multiplier for accuracy/evasion stages.

    Args:
        stage: Stat stage from -6 to +6

    Returns:
        Multiplier to apply to accuracy/evasion
    """
    stage = max(-6, min(6, stage))
    return STAT_STAGE_MULTIPLIERS[stage]

def apply_stat_stage_to_stat(base_stat: int, stage: int) -> int:
    """
    Applies stat stage to a stat using Gen 1 integer math.
    Uses integer multiplication and floor division for accuracy.

    Args:
        base_stat: The base stat value
        stage: Stat stage from -6 to +6

    Returns:
        Modified stat value
    """
    stage = max(-6, min(6, stage))
    numerator, denominator = STAT_STAGE_FRACTIONS[stage]
    return base_stat * numerator // denominator

def get_modified_attack(pokemon: Pokemon, is_physical: bool) -> int:
    """
    Gets attack stat with stat stage modifications applied.

    Args:
        pokemon: The attacking Pokemon
        is_physical: True for physical attack, False for special

    Returns:
        Modified attack stat
    """
    if is_physical:
        base_stat = pokemon.base_stats.attack
        stage = pokemon.stat_stages[StatType.ATTACK]
    else:
        base_stat = pokemon.base_stats.special
        stage = pokemon.stat_stages[StatType.SPECIAL]

    return apply_stat_stage_to_stat(base_stat, stage)

def get_modified_defense(pokemon: Pokemon, is_physical: bool) -> int:
    """
    Gets defense stat with stat stage modifications applied.

    Args:
        pokemon: The defending Pokemon
        is_physical: True for physical defense, False for special

    Returns:
        Modified defense stat
    """
    if is_physical:
        base_stat = pokemon.base_stats.defense
        stage = pokemon.stat_stages[StatType.DEFENSE]
    else:
        base_stat = pokemon.base_stats.special
        stage = pokemon.stat_stages[StatType.SPECIAL]

    return apply_stat_stage_to_stat(base_stat, stage)

def get_modified_speed(pokemon: Pokemon) -> int:
    """
    Gets speed stat with stat stage modifications applied.
    In Gen 1, Paralysis also quarters Speed.

    Args:
        pokemon: The Pokemon

    Returns:
        Modified speed stat
    """
    from models.enums import Status
    base_stat = pokemon.base_stats.speed
    stage = pokemon.stat_stages[StatType.SPEED]
    modified = apply_stat_stage_to_stat(base_stat, stage)

    # Gen 1: Paralysis quarters Speed
    if pokemon.status == Status.PARALYSIS:
        modified = modified // 4

    return max(1, modified)

def get_accuracy_multiplier(attacker: Pokemon, defender: Pokemon) -> float:
    """
    Gets accuracy multiplier based on attacker's accuracy and defender's evasion stages.

    Args:
        attacker: The attacking Pokemon
        defender: The defending Pokemon

    Returns:
        Multiplier to apply to move accuracy
    """
    # Net stage = attacker accuracy - defender evasion
    net_stage = attacker.stat_stages[StatType.ACCURACY] - defender.stat_stages[StatType.EVASION]
    net_stage = max(-6, min(6, net_stage))

    return get_stat_multiplier(net_stage)

def get_stat_change_message(pokemon: Pokemon, stat: StatType, change: int, hit_limit: bool) -> str:
    """
    Generates a message describing the stat change.

    Args:
        pokemon: The Pokemon whose stat changed
        stat: The stat that changed
        change: The amount of change
        hit_limit: Whether the stat hit its limit

    Returns:
        Formatted message string
    """
    if change == 0:
        if hit_limit:
            return f"¡{pokemon.name}'s {stat.value} won't go any {'higher' if pokemon.stat_stages[stat] > 0 else 'lower'}!"
        return ""

    stat_name = stat.value
    pokemon_name = pokemon.name

    if abs(change) >= 2:
        degree = "sharply" if change > 0 else "harshly"
    else:
        degree = ""

    direction = "rose" if change > 0 else "fell"

    if degree:
        return f"¡{pokemon_name}'s {stat_name} {direction} {degree}!"
    else:
        return f"¡{pokemon_name}'s {stat_name} {direction}!"
