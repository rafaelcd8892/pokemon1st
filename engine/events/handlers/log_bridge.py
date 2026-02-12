"""Log Bridge Handler - Converts battle events into BattleLogger entries.

Subscribes to the event bus and writes log entries for event types that are
NOT already handled by manual blog.log_*() calls (to avoid duplicates).
"""

from typing import Optional
from ..types import (
    BattleEvent, EventType,
    MoveFailedEvent, MoveNoEffectEvent,
    MultiHitStrikeEvent, MultiHitCompleteEvent,
    StatusPreventedActionEvent, ConfusionSelfHitEvent, StatusCuredEvent, StatusDamageEvent,
    StatLimitReachedEvent,
    ScreenActivatedEvent, ScreenExpiredEvent, ScreenBlockedEvent, ScreenReducedDamageEvent,
    PokemonHealedEvent, HPDrainedEvent,
    PokemonTrappedEvent, TrapDamageEvent, TrapEscapedEvent,
    SubstituteCreatedEvent, SubstituteBrokeEvent, SubstituteBlockedEvent,
    RechargeNeededEvent, ChargingMoveEvent, RageIncreasedEvent,
    LeechSeedPlantedEvent, LeechSeedDamageEvent, MistProtectionEvent,
    MoveDisabledEvent, MoveReenabledEvent,
)
from ..bus import BattleEventBus


class LogBridgeHandler:
    """
    Converts BattleEvents from the event bus into BattleLogger entries.

    Only handles event types NOT already covered by manual blog.log_*() calls.
    Skipped types (handled manually): BATTLE_START, BATTLE_END, TURN_START,
    TURN_END, MOVE_USED, DAMAGE_DEALT, CRITICAL_HIT, EFFECTIVENESS,
    MOVE_MISSED, STATUS_APPLIED, STAT_CHANGED, POKEMON_FAINTED (these are
    already written to the logger by direct calls in battle.py/team_battle.py).
    """

    def __init__(self, bus: BattleEventBus, logger, enabled: bool = True):
        self.enabled = enabled
        self._logger = logger
        self._bus = bus
        if bus and enabled:
            bus.subscribe(self.handle_event)

    def handle_event(self, event: BattleEvent) -> None:
        if not self.enabled or not self._logger or not self._logger.enabled:
            return

        handler_map = {
            EventType.MOVE_FAILED: self._handle_move_failed,
            EventType.MOVE_NO_EFFECT: self._handle_move_no_effect,
            EventType.MULTI_HIT_STRIKE: self._handle_multi_hit_strike,
            EventType.MULTI_HIT_COMPLETE: self._handle_multi_hit_complete,
            EventType.STATUS_PREVENTED_ACTION: self._handle_status_prevented,
            EventType.CONFUSION_SELF_HIT: self._handle_confusion_self_hit,
            EventType.STATUS_CURED: self._handle_status_cured,
            EventType.STATUS_DAMAGE: self._handle_status_damage,
            EventType.STAT_LIMIT_REACHED: self._handle_stat_limit,
            EventType.SCREEN_ACTIVATED: self._handle_screen_activated,
            EventType.SCREEN_EXPIRED: self._handle_screen_expired,
            EventType.SCREEN_BLOCKED: self._handle_screen_blocked,
            EventType.SCREEN_REDUCED_DAMAGE: self._handle_screen_reduced,
            EventType.POKEMON_HEALED: self._handle_pokemon_healed,
            EventType.HP_DRAINED: self._handle_hp_drained,
            EventType.POKEMON_TRAPPED: self._handle_pokemon_trapped,
            EventType.TRAP_DAMAGE: self._handle_trap_damage,
            EventType.TRAP_ESCAPED: self._handle_trap_escaped,
            EventType.SUBSTITUTE_CREATED: self._handle_substitute_created,
            EventType.SUBSTITUTE_BROKE: self._handle_substitute_broke,
            EventType.SUBSTITUTE_BLOCKED: self._handle_substitute_blocked,
            EventType.RECHARGE_NEEDED: self._handle_recharge_needed,
            EventType.CHARGING_MOVE: self._handle_charging_move,
            EventType.RAGE_INCREASED: self._handle_rage_increased,
            EventType.LEECH_SEED_PLANTED: self._handle_leech_seed_planted,
            EventType.LEECH_SEED_DAMAGE: self._handle_leech_seed_damage,
            EventType.MIST_PROTECTION: self._handle_mist_protection,
            EventType.MOVE_DISABLED: self._handle_move_disabled,
            EventType.MOVE_REENABLED: self._handle_move_reenabled,
        }

        handler = handler_map.get(event.event_type)
        if handler:
            handler(event)

    def _log(self, action_type: str, pokemon: str = "", details: dict = None, message: str = "",
             pokemon_side: str = None):
        from engine.battle_logger import BattleLogEntry
        entry = BattleLogEntry(
            turn=self._logger._current_turn,
            action_type=action_type,
            pokemon=pokemon,
            pokemon_side=pokemon_side,
            details=details or {},
            message=message,
        )
        self._logger.entries.append(entry)

    # --- Combat ---

    def _handle_move_failed(self, event: MoveFailedEvent):
        self._log("event_move_failed", event.attacker_name,
                  details={"move": event.move_name, "reason": event.reason})

    def _handle_move_no_effect(self, event: MoveNoEffectEvent):
        self._log("event_no_effect", event.attacker_name,
                  details={"move": event.move_name, "target": event.defender_name})

    # --- Multi-hit ---

    def _handle_multi_hit_strike(self, event: MultiHitStrikeEvent):
        self._log("event_multi_hit_strike", event.attacker_name,
                  details={"hit_number": event.hit_number, "damage": event.damage,
                           "is_critical": event.is_critical, "target": event.defender_name})

    def _handle_multi_hit_complete(self, event: MultiHitCompleteEvent):
        self._log("event_multi_hit_complete", event.attacker_name,
                  details={"total_hits": event.total_hits, "total_damage": event.total_damage})

    # --- Status ---

    def _handle_status_prevented(self, event: StatusPreventedActionEvent):
        self._log("event_status_prevented", event.pokemon_name,
                  details={"status": event.status})

    def _handle_confusion_self_hit(self, event: ConfusionSelfHitEvent):
        self._log("event_confusion_self_hit", event.pokemon_name,
                  details={"damage": event.damage, "current_hp": event.current_hp,
                           "max_hp": event.max_hp})

    def _handle_status_cured(self, event: StatusCuredEvent):
        self._log("event_status_cured", event.pokemon_name,
                  details={"status": event.status, "reason": event.reason})

    def _handle_status_damage(self, event: StatusDamageEvent):
        self._log("event_status_damage", event.pokemon_name,
                  details={"status": event.status, "damage": event.damage,
                           "current_hp": event.current_hp, "max_hp": event.max_hp})

    # --- Stats ---

    def _handle_stat_limit(self, event: StatLimitReachedEvent):
        self._log("event_stat_limit", event.pokemon_name,
                  details={"stat": event.stat, "at_max": event.at_max})

    # --- Screens ---

    def _handle_screen_activated(self, event: ScreenActivatedEvent):
        self._log("event_screen_activated", event.pokemon_name,
                  details={"screen": event.screen})

    def _handle_screen_expired(self, event: ScreenExpiredEvent):
        self._log("event_screen_expired", event.pokemon_name,
                  details={"screen": event.screen})

    def _handle_screen_blocked(self, event: ScreenBlockedEvent):
        self._log("event_screen_blocked", event.pokemon_name,
                  details={"screen": event.screen})

    def _handle_screen_reduced(self, event: ScreenReducedDamageEvent):
        self._log("event_screen_reduced", event.pokemon_name,
                  details={"screen": event.screen})

    # --- HP ---

    def _handle_pokemon_healed(self, event: PokemonHealedEvent):
        self._log("event_healed", event.pokemon_name,
                  details={"amount": event.amount, "current_hp": event.current_hp,
                           "max_hp": event.max_hp, "source": event.source})

    def _handle_hp_drained(self, event: HPDrainedEvent):
        self._log("event_hp_drained", event.source_name,
                  details={"target": event.target_name, "amount": event.amount})

    # --- Trapping ---

    def _handle_pokemon_trapped(self, event: PokemonTrappedEvent):
        self._log("event_trapped", event.pokemon_name,
                  details={"move": event.move_name})

    def _handle_trap_damage(self, event: TrapDamageEvent):
        self._log("event_trap_damage", event.pokemon_name,
                  details={"damage": event.damage, "current_hp": event.current_hp,
                           "max_hp": event.max_hp})

    def _handle_trap_escaped(self, event: TrapEscapedEvent):
        self._log("event_trap_escaped", event.pokemon_name)

    # --- Substitute ---

    def _handle_substitute_created(self, event: SubstituteCreatedEvent):
        self._log("event_substitute_created", event.pokemon_name,
                  details={"hp_cost": event.hp_cost})

    def _handle_substitute_broke(self, event: SubstituteBrokeEvent):
        self._log("event_substitute_broke", event.pokemon_name)

    def _handle_substitute_blocked(self, event: SubstituteBlockedEvent):
        self._log("event_substitute_blocked", event.pokemon_name)

    # --- Special mechanics ---

    def _handle_recharge_needed(self, event: RechargeNeededEvent):
        self._log("event_recharge_needed", event.pokemon_name,
                  details={"move": event.move_name})

    def _handle_charging_move(self, event: ChargingMoveEvent):
        self._log("event_charging_move", event.pokemon_name,
                  details={"move": event.move_name, "message_key": event.message_key})

    def _handle_rage_increased(self, event: RageIncreasedEvent):
        self._log("event_rage_increased", event.pokemon_name)

    def _handle_leech_seed_planted(self, event: LeechSeedPlantedEvent):
        self._log("event_leech_seed_planted", event.pokemon_name)

    def _handle_leech_seed_damage(self, event: LeechSeedDamageEvent):
        self._log("event_leech_seed_damage", event.pokemon_name,
                  details={"healer": event.healer_name, "damage": event.damage})

    def _handle_mist_protection(self, event: MistProtectionEvent):
        self._log("event_mist_protection", event.pokemon_name,
                  details={"stat": event.stat})

    def _handle_move_disabled(self, event: MoveDisabledEvent):
        self._log("event_move_disabled", event.pokemon_name,
                  details={"move": event.move_name})

    def _handle_move_reenabled(self, event: MoveReenabledEvent):
        self._log("event_move_reenabled", event.pokemon_name,
                  details={"move": event.move_name})
