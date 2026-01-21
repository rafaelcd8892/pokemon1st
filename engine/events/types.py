"""Battle event types - immutable dataclasses representing all battle occurrences"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum, auto


class EventType(Enum):
    """Enumeration of all event types for filtering and subscription"""
    # Battle flow
    BATTLE_START = auto()
    BATTLE_END = auto()
    TURN_START = auto()
    TURN_END = auto()

    # Combat
    MOVE_USED = auto()
    DAMAGE_DEALT = auto()
    CRITICAL_HIT = auto()
    MOVE_MISSED = auto()
    MOVE_FAILED = auto()
    MOVE_NO_EFFECT = auto()
    EFFECTIVENESS = auto()

    # Multi-hit
    MULTI_HIT_STRIKE = auto()
    MULTI_HIT_COMPLETE = auto()

    # Status
    STATUS_APPLIED = auto()
    STATUS_CURED = auto()
    STATUS_DAMAGE = auto()
    STATUS_PREVENTED_ACTION = auto()
    CONFUSION_SELF_HIT = auto()

    # Stats
    STAT_CHANGED = auto()
    STAT_LIMIT_REACHED = auto()

    # Screens and effects
    SCREEN_ACTIVATED = auto()
    SCREEN_EXPIRED = auto()
    SCREEN_BLOCKED = auto()
    SCREEN_REDUCED_DAMAGE = auto()

    # HP changes
    POKEMON_HEALED = auto()
    POKEMON_FAINTED = auto()
    HP_DRAINED = auto()

    # Special mechanics
    POKEMON_TRAPPED = auto()
    TRAP_DAMAGE = auto()
    TRAP_ESCAPED = auto()
    SUBSTITUTE_CREATED = auto()
    SUBSTITUTE_BROKE = auto()
    SUBSTITUTE_BLOCKED = auto()
    RECHARGE_NEEDED = auto()
    CHARGING_MOVE = auto()
    RAGE_INCREASED = auto()
    LEECH_SEED_PLANTED = auto()
    LEECH_SEED_DAMAGE = auto()
    MIST_PROTECTION = auto()
    MOVE_DISABLED = auto()
    MOVE_REENABLED = auto()

    # Info/debug
    INFO = auto()


@dataclass(frozen=True)
class BattleEvent:
    """Base class for all battle events"""
    event_type: EventType
    turn: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization"""
        return {
            'event_type': self.event_type.name,
            'turn': self.turn,
        }


# ============== Battle Flow Events ==============

@dataclass(frozen=True)
class BattleStartEvent(BattleEvent):
    """Emitted when a battle begins"""
    pokemon1_name: str = ""
    pokemon2_name: str = ""
    event_type: EventType = field(default=EventType.BATTLE_START, init=False)


@dataclass(frozen=True)
class BattleEndEvent(BattleEvent):
    """Emitted when a battle ends"""
    winner_name: Optional[str] = None  # None if tie
    reason: str = ""  # "fainted", "forfeit", "turn_limit"
    event_type: EventType = field(default=EventType.BATTLE_END, init=False)


@dataclass(frozen=True)
class TurnStartEvent(BattleEvent):
    """Emitted at the start of each turn"""
    event_type: EventType = field(default=EventType.TURN_START, init=False)


@dataclass(frozen=True)
class TurnEndEvent(BattleEvent):
    """Emitted at the end of each turn"""
    pokemon1_hp: int = 0
    pokemon1_max_hp: int = 0
    pokemon2_hp: int = 0
    pokemon2_max_hp: int = 0
    event_type: EventType = field(default=EventType.TURN_END, init=False)


# ============== Combat Events ==============

@dataclass(frozen=True)
class MoveUsedEvent(BattleEvent):
    """Emitted when a Pokemon uses a move"""
    attacker_name: str = ""
    move_name: str = ""
    move_type: str = ""
    is_continuation: bool = False  # For multi-turn moves
    event_type: EventType = field(default=EventType.MOVE_USED, init=False)


@dataclass(frozen=True)
class DamageDealtEvent(BattleEvent):
    """Emitted when damage is dealt to a Pokemon"""
    attacker_name: str = ""
    defender_name: str = ""
    damage: int = 0
    defender_hp: int = 0
    defender_max_hp: int = 0
    move_name: str = ""
    event_type: EventType = field(default=EventType.DAMAGE_DEALT, init=False)


@dataclass(frozen=True)
class CriticalHitEvent(BattleEvent):
    """Emitted when a critical hit occurs"""
    attacker_name: str = ""
    event_type: EventType = field(default=EventType.CRITICAL_HIT, init=False)


@dataclass(frozen=True)
class EffectivenessEvent(BattleEvent):
    """Emitted to indicate move effectiveness"""
    multiplier: float = 1.0  # 0, 0.25, 0.5, 1, 2, 4
    event_type: EventType = field(default=EventType.EFFECTIVENESS, init=False)


@dataclass(frozen=True)
class MoveMissedEvent(BattleEvent):
    """Emitted when a move misses"""
    attacker_name: str = ""
    move_name: str = ""
    defender_name: str = ""
    reason: str = ""  # "accuracy", "evasion", "protected", "underground", "flying"
    event_type: EventType = field(default=EventType.MOVE_MISSED, init=False)


@dataclass(frozen=True)
class MoveFailedEvent(BattleEvent):
    """Emitted when a move fails for various reasons"""
    attacker_name: str = ""
    move_name: str = ""
    reason: str = ""  # "no_pp", "disabled", "no_target", etc.
    event_type: EventType = field(default=EventType.MOVE_FAILED, init=False)


@dataclass(frozen=True)
class MoveNoEffectEvent(BattleEvent):
    """Emitted when a move has no effect (type immunity)"""
    attacker_name: str = ""
    move_name: str = ""
    defender_name: str = ""
    event_type: EventType = field(default=EventType.MOVE_NO_EFFECT, init=False)


# ============== Multi-hit Events ==============

@dataclass(frozen=True)
class MultiHitStrikeEvent(BattleEvent):
    """Emitted for each strike of a multi-hit move"""
    attacker_name: str = ""
    defender_name: str = ""
    hit_number: int = 0
    damage: int = 0
    is_critical: bool = False
    event_type: EventType = field(default=EventType.MULTI_HIT_STRIKE, init=False)


@dataclass(frozen=True)
class MultiHitCompleteEvent(BattleEvent):
    """Emitted when a multi-hit move completes"""
    attacker_name: str = ""
    total_hits: int = 0
    total_damage: int = 0
    event_type: EventType = field(default=EventType.MULTI_HIT_COMPLETE, init=False)


# ============== Status Events ==============

@dataclass(frozen=True)
class StatusAppliedEvent(BattleEvent):
    """Emitted when a status condition is applied"""
    pokemon_name: str = ""
    status: str = ""  # "burn", "freeze", "paralysis", "poison", "sleep", "confusion"
    source: str = ""  # move name or effect that caused it
    event_type: EventType = field(default=EventType.STATUS_APPLIED, init=False)


@dataclass(frozen=True)
class StatusCuredEvent(BattleEvent):
    """Emitted when a status condition is cured"""
    pokemon_name: str = ""
    status: str = ""
    reason: str = ""  # "natural", "move", "item"
    event_type: EventType = field(default=EventType.STATUS_CURED, init=False)


@dataclass(frozen=True)
class StatusDamageEvent(BattleEvent):
    """Emitted when a Pokemon takes damage from status (burn, poison)"""
    pokemon_name: str = ""
    status: str = ""
    damage: int = 0
    current_hp: int = 0
    max_hp: int = 0
    event_type: EventType = field(default=EventType.STATUS_DAMAGE, init=False)


@dataclass(frozen=True)
class StatusPreventedActionEvent(BattleEvent):
    """Emitted when status prevents a Pokemon from acting"""
    pokemon_name: str = ""
    status: str = ""  # "sleep", "freeze", "paralysis"
    event_type: EventType = field(default=EventType.STATUS_PREVENTED_ACTION, init=False)


@dataclass(frozen=True)
class ConfusionSelfHitEvent(BattleEvent):
    """Emitted when a confused Pokemon hits itself"""
    pokemon_name: str = ""
    damage: int = 0
    current_hp: int = 0
    max_hp: int = 0
    event_type: EventType = field(default=EventType.CONFUSION_SELF_HIT, init=False)


# ============== Stat Events ==============

@dataclass(frozen=True)
class StatChangedEvent(BattleEvent):
    """Emitted when a Pokemon's stat stage changes"""
    pokemon_name: str = ""
    stat: str = ""  # "attack", "defense", "special", "speed", "accuracy", "evasion"
    stages: int = 0  # positive = raise, negative = lower
    new_stage: int = 0  # current stage after change (-6 to +6)
    source: str = ""  # move name or effect that caused it
    event_type: EventType = field(default=EventType.STAT_CHANGED, init=False)


@dataclass(frozen=True)
class StatLimitReachedEvent(BattleEvent):
    """Emitted when a stat can't go higher/lower"""
    pokemon_name: str = ""
    stat: str = ""
    at_max: bool = True  # True if at +6, False if at -6
    event_type: EventType = field(default=EventType.STAT_LIMIT_REACHED, init=False)


# ============== Screen Events ==============

@dataclass(frozen=True)
class ScreenActivatedEvent(BattleEvent):
    """Emitted when a screen (Reflect, Light Screen, Mist) is activated"""
    pokemon_name: str = ""
    screen: str = ""  # "reflect", "light_screen", "mist"
    event_type: EventType = field(default=EventType.SCREEN_ACTIVATED, init=False)


@dataclass(frozen=True)
class ScreenExpiredEvent(BattleEvent):
    """Emitted when a screen expires"""
    pokemon_name: str = ""
    screen: str = ""
    event_type: EventType = field(default=EventType.SCREEN_EXPIRED, init=False)


@dataclass(frozen=True)
class ScreenBlockedEvent(BattleEvent):
    """Emitted when trying to set up an already active screen"""
    pokemon_name: str = ""
    screen: str = ""
    event_type: EventType = field(default=EventType.SCREEN_BLOCKED, init=False)


@dataclass(frozen=True)
class ScreenReducedDamageEvent(BattleEvent):
    """Emitted when a screen reduces incoming damage"""
    pokemon_name: str = ""
    screen: str = ""
    event_type: EventType = field(default=EventType.SCREEN_REDUCED_DAMAGE, init=False)


# ============== HP Change Events ==============

@dataclass(frozen=True)
class PokemonHealedEvent(BattleEvent):
    """Emitted when a Pokemon is healed"""
    pokemon_name: str = ""
    amount: int = 0
    current_hp: int = 0
    max_hp: int = 0
    source: str = ""  # move name or "drain", "leech_seed", etc.
    event_type: EventType = field(default=EventType.POKEMON_HEALED, init=False)


@dataclass(frozen=True)
class PokemonFaintedEvent(BattleEvent):
    """Emitted when a Pokemon faints"""
    pokemon_name: str = ""
    cause: str = ""  # "damage", "recoil", "status", "self_destruct"
    event_type: EventType = field(default=EventType.POKEMON_FAINTED, init=False)


@dataclass(frozen=True)
class HPDrainedEvent(BattleEvent):
    """Emitted when HP is drained from one Pokemon to another"""
    source_name: str = ""
    target_name: str = ""
    amount: int = 0
    event_type: EventType = field(default=EventType.HP_DRAINED, init=False)


# ============== Special Mechanic Events ==============

@dataclass(frozen=True)
class PokemonTrappedEvent(BattleEvent):
    """Emitted when a Pokemon becomes trapped"""
    pokemon_name: str = ""
    move_name: str = ""
    event_type: EventType = field(default=EventType.POKEMON_TRAPPED, init=False)


@dataclass(frozen=True)
class TrapDamageEvent(BattleEvent):
    """Emitted when a trapped Pokemon takes damage"""
    pokemon_name: str = ""
    damage: int = 0
    current_hp: int = 0
    max_hp: int = 0
    event_type: EventType = field(default=EventType.TRAP_DAMAGE, init=False)


@dataclass(frozen=True)
class TrapEscapedEvent(BattleEvent):
    """Emitted when a Pokemon escapes a trap"""
    pokemon_name: str = ""
    event_type: EventType = field(default=EventType.TRAP_ESCAPED, init=False)


@dataclass(frozen=True)
class SubstituteCreatedEvent(BattleEvent):
    """Emitted when a Substitute is created"""
    pokemon_name: str = ""
    hp_cost: int = 0
    event_type: EventType = field(default=EventType.SUBSTITUTE_CREATED, init=False)


@dataclass(frozen=True)
class SubstituteBrokeEvent(BattleEvent):
    """Emitted when a Substitute breaks"""
    pokemon_name: str = ""
    event_type: EventType = field(default=EventType.SUBSTITUTE_BROKE, init=False)


@dataclass(frozen=True)
class SubstituteBlockedEvent(BattleEvent):
    """Emitted when a Substitute blocks damage"""
    pokemon_name: str = ""
    event_type: EventType = field(default=EventType.SUBSTITUTE_BLOCKED, init=False)


@dataclass(frozen=True)
class RechargeNeededEvent(BattleEvent):
    """Emitted when a Pokemon needs to recharge"""
    pokemon_name: str = ""
    move_name: str = ""
    event_type: EventType = field(default=EventType.RECHARGE_NEEDED, init=False)


@dataclass(frozen=True)
class ChargingMoveEvent(BattleEvent):
    """Emitted when a Pokemon is charging a two-turn move"""
    pokemon_name: str = ""
    move_name: str = ""
    message_key: str = ""  # "dig_underground", "fly_high", "charging", etc.
    event_type: EventType = field(default=EventType.CHARGING_MOVE, init=False)


@dataclass(frozen=True)
class RageIncreasedEvent(BattleEvent):
    """Emitted when Rage increases attack"""
    pokemon_name: str = ""
    event_type: EventType = field(default=EventType.RAGE_INCREASED, init=False)


@dataclass(frozen=True)
class LeechSeedPlantedEvent(BattleEvent):
    """Emitted when Leech Seed is planted"""
    pokemon_name: str = ""
    event_type: EventType = field(default=EventType.LEECH_SEED_PLANTED, init=False)


@dataclass(frozen=True)
class LeechSeedDamageEvent(BattleEvent):
    """Emitted when Leech Seed drains HP"""
    pokemon_name: str = ""
    healer_name: str = ""
    damage: int = 0
    event_type: EventType = field(default=EventType.LEECH_SEED_DAMAGE, init=False)


@dataclass(frozen=True)
class MistProtectionEvent(BattleEvent):
    """Emitted when Mist protects against stat reduction"""
    pokemon_name: str = ""
    stat: str = ""
    event_type: EventType = field(default=EventType.MIST_PROTECTION, init=False)


@dataclass(frozen=True)
class MoveDisabledEvent(BattleEvent):
    """Emitted when a move is disabled"""
    pokemon_name: str = ""
    move_name: str = ""
    event_type: EventType = field(default=EventType.MOVE_DISABLED, init=False)


@dataclass(frozen=True)
class MoveReenabledEvent(BattleEvent):
    """Emitted when a disabled move is re-enabled"""
    pokemon_name: str = ""
    move_name: str = ""
    event_type: EventType = field(default=EventType.MOVE_REENABLED, init=False)


@dataclass(frozen=True)
class InfoEvent(BattleEvent):
    """Generic info event for debugging or custom messages"""
    message: str = ""
    event_type: EventType = field(default=EventType.INFO, init=False)
