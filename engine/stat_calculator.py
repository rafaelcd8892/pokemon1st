"""
Gen 1 stat calculation formulas.

This module implements the authentic Gen 1 stat calculation formulas
that determine a Pokemon's actual stats based on:
- Base stats (species-specific)
- IVs (Individual Values / DVs)
- EVs (Effort Values) - optional, defaults to max
- Level

References:
- https://bulbapedia.bulbagarden.net/wiki/Stat#Generation_I_and_II
"""

import math
from typing import Optional

from models.stats import Stats
from models.ivs import IVs


# Default EV value - max EVs for competitive battles
# In Gen 1, EVs range from 0 to 65535 per stat
MAX_STAT_EV = 65535
ZERO_EV = 0


def calculate_hp(base: int, iv: int, ev: int, level: int) -> int:
    """
    Calculate HP stat using Gen 1 formula.

    Formula:
        HP = floor(((Base + IV) * 2 + floor(sqrt(EV) / 4)) * Level / 100) + Level + 10

    Args:
        base: Species base HP stat
        iv: HP Individual Value (0-15)
        ev: HP Effort Value (0-65535)
        level: Pokemon level (1-100)

    Returns:
        Calculated HP stat
    """
    ev_component = math.floor(math.sqrt(ev) / 4)
    return math.floor(((base + iv) * 2 + ev_component) * level / 100) + level + 10


def calculate_other_stat(base: int, iv: int, ev: int, level: int) -> int:
    """
    Calculate non-HP stat using Gen 1 formula.

    Formula:
        Stat = floor(((Base + IV) * 2 + floor(sqrt(EV) / 4)) * Level / 100) + 5

    Args:
        base: Species base stat
        iv: Individual Value for this stat (0-15)
        ev: Effort Value for this stat (0-65535)
        level: Pokemon level (1-100)

    Returns:
        Calculated stat value
    """
    ev_component = math.floor(math.sqrt(ev) / 4)
    return math.floor(((base + iv) * 2 + ev_component) * level / 100) + 5


def calculate_stats(
    base_stats: Stats,
    ivs: IVs,
    level: int,
    evs: Optional[dict] = None,
    use_max_evs: bool = True
) -> Stats:
    """
    Calculate all stats from base stats, IVs, level, and EVs.

    Args:
        base_stats: Species base stats
        ivs: Individual Values
        level: Pokemon level (1-100)
        evs: Optional dict mapping stat name to EV value.
             Keys: 'hp', 'attack', 'defense', 'special', 'speed'
        use_max_evs: If True and evs is None, use max EVs (competitive).
                     If False and evs is None, use zero EVs (untrained).

    Returns:
        Calculated Stats object with final stat values
    """
    # Determine EV values
    if evs is None:
        default_ev = MAX_STAT_EV if use_max_evs else ZERO_EV
        evs = {
            'hp': default_ev,
            'attack': default_ev,
            'defense': default_ev,
            'special': default_ev,
            'speed': default_ev
        }

    return Stats(
        hp=calculate_hp(base_stats.hp, ivs.hp, evs.get('hp', 0), level),
        attack=calculate_other_stat(base_stats.attack, ivs.attack, evs.get('attack', 0), level),
        defense=calculate_other_stat(base_stats.defense, ivs.defense, evs.get('defense', 0), level),
        special=calculate_other_stat(base_stats.special, ivs.special, evs.get('special', 0), level),
        speed=calculate_other_stat(base_stats.speed, ivs.speed, evs.get('speed', 0), level)
    )


def calculate_stat_at_level(
    base: int,
    iv: int,
    ev: int,
    level: int,
    is_hp: bool = False
) -> int:
    """
    Calculate a single stat at a given level.

    Convenience function for calculating individual stats.

    Args:
        base: Base stat value
        iv: Individual Value (0-15)
        ev: Effort Value (0-65535)
        level: Pokemon level (1-100)
        is_hp: True if calculating HP, False for other stats

    Returns:
        Calculated stat value
    """
    if is_hp:
        return calculate_hp(base, iv, ev, level)
    return calculate_other_stat(base, iv, ev, level)
