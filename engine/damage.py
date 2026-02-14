import random
from dataclasses import dataclass
from typing import Optional
from models.pokemon import Pokemon
from models.move import Move
from models.enums import MoveCategory, StatType, Status, Type
from engine.type_chart import get_effectiveness
from engine.stat_modifiers import get_modified_attack, get_modified_defense
from engine.gen_mechanics import is_physical as _is_physical_move
import config


@dataclass
class DamageBreakdown:
    """Complete audit trail for a damage calculation."""
    # Move info
    move_name: str = ""
    move_power: int = 0
    move_category: str = ""  # "physical" or "special"
    move_type: str = ""

    # Attacker/defender context
    attacker_name: str = ""
    defender_name: str = ""
    attacker_level: int = 0

    # Stats used in calculation
    attack_stat: int = 0        # final attack value (after stages/crit)
    defense_stat: int = 0       # final defense value (after stages/crit/modifier)
    attack_base: int = 0        # base stat before stage modifiers
    defense_base: int = 0       # base stat before stage modifiers
    attack_stage: int = 0       # -6 to +6
    defense_stage: int = 0      # -6 to +6

    # Modifiers
    is_critical: bool = False
    stab: float = 1.0
    effectiveness: float = 1.0
    random_roll: int = 0        # raw roll 217-255
    burn_modifier: float = 1.0
    defense_modifier: float = 1.0

    # Calculation result
    base_damage: float = 0.0    # from formula before multipliers
    final_damage: int = 0       # after all multipliers

    def to_dict(self) -> dict:
        return {
            "move_power": self.move_power,
            "move_category": self.move_category,
            "move_type": self.move_type,
            "attacker_level": self.attacker_level,
            "attack_stat": self.attack_stat,
            "defense_stat": self.defense_stat,
            "attack_base": self.attack_base,
            "defense_base": self.defense_base,
            "attack_stage": self.attack_stage,
            "defense_stage": self.defense_stage,
            "is_critical": self.is_critical,
            "stab": self.stab,
            "effectiveness": self.effectiveness,
            "random_roll": self.random_roll,
            "burn_modifier": self.burn_modifier,
            "defense_modifier": self.defense_modifier,
            "base_damage": round(self.base_damage, 2),
            "final_damage": self.final_damage,
        }


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
    is_physical = _is_physical_move(move)

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

def get_random_factor_with_roll() -> tuple[float, int]:
    """Gen1 random factor with raw roll for audit trail."""
    roll = random.randint(config.MIN_RANDOM_FACTOR, config.MAX_RANDOM_FACTOR)
    return roll / config.RANDOM_DIVISOR, roll

def apply_burn_modifier(damage: int, attacker: Pokemon, move: Move) -> int:
    """Halves physical damage if attacker is burned (Gen1 mechanic)"""
    if attacker.status == Status.BURN and _is_physical_move(move):
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
    damage, is_critical, effectiveness, _ = calculate_damage_with_breakdown(
        attacker, defender, move, defense_modifier
    )
    return damage, is_critical, effectiveness


def calculate_damage_with_breakdown(
    attacker: Pokemon, defender: Pokemon, move: Move,
    defense_modifier: float = 1.0
) -> tuple[int, bool, float, Optional[DamageBreakdown]]:
    """
    Calcula el daño usando la fórmula de Gen 1 with full audit breakdown.
    Retorna: (damage, is_critical, effectiveness, breakdown)

    The breakdown is None for STATUS moves (no damage calculation).
    """
    # STATUS moves deal no damage
    if move.category == MoveCategory.STATUS:
        return 0, False, 1.0, None

    breakdown = DamageBreakdown(
        move_name=move.name,
        move_power=move.power,
        move_category="physical" if _is_physical_move(move) else "special",
        move_type=move.type.value if hasattr(move.type, 'value') else str(move.type),
        attacker_name=attacker.name,
        defender_name=defender.name,
        attacker_level=attacker.level,
        defense_modifier=defense_modifier,
    )

    # Calculate critical hit
    is_critical = calculate_critical_hit(attacker)
    breakdown.is_critical = is_critical

    # Capture stat stages — resolved via gen_mechanics (Gen 1: type-based)
    is_physical = _is_physical_move(move)
    if is_physical:
        breakdown.attack_stage = attacker.stat_stages.get(StatType.ATTACK, 0)
        breakdown.defense_stage = defender.stat_stages.get(StatType.DEFENSE, 0)
        breakdown.attack_base = attacker.base_stats.attack
        breakdown.defense_base = defender.base_stats.defense
    else:
        breakdown.attack_stage = attacker.stat_stages.get(StatType.SPECIAL, 0)
        breakdown.defense_stage = defender.stat_stages.get(StatType.SPECIAL, 0)
        breakdown.attack_base = attacker.base_stats.special
        breakdown.defense_base = defender.base_stats.special

    # Get appropriate stats (Gen 1 critical hits ignore stat stage modifiers)
    if is_critical:
        if is_physical:
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

    breakdown.attack_stat = attack
    breakdown.defense_stat = defense

    # Calculate base damage
    damage = calculate_base_damage(attacker.level, move.power, attack, defense)
    breakdown.base_damage = damage

    # Apply all multipliers
    stab = get_stab_multiplier(move.type, attacker.types)
    effectiveness = get_effectiveness(move.type, defender.types)
    random_factor, random_roll = get_random_factor_with_roll()

    breakdown.stab = stab
    breakdown.effectiveness = effectiveness
    breakdown.random_roll = random_roll

    # If type effectiveness is 0 (immunity), no damage is dealt
    if effectiveness == 0:
        breakdown.final_damage = 0
        return 0, is_critical, effectiveness, breakdown

    damage = int(damage * stab * effectiveness * random_factor)

    # Apply burn modifier
    burn_mod = 1.0
    if attacker.status == Status.BURN and _is_physical_move(move):
        burn_mod = config.BURN_ATTACK_MULTIPLIER
    breakdown.burn_modifier = burn_mod
    damage = apply_burn_modifier(damage, attacker, move)

    # Minimum 1 damage for non-immune hits
    final_damage = max(1, damage)
    breakdown.final_damage = final_damage
    return final_damage, is_critical, effectiveness, breakdown
