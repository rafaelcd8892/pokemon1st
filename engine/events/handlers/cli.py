"""CLI Handler - Renders battle events to the terminal with colors"""

from typing import Optional
from ..types import (
    BattleEvent, EventType,
    BattleStartEvent, BattleEndEvent, TurnStartEvent, TurnEndEvent,
    MoveUsedEvent, DamageDealtEvent, CriticalHitEvent, EffectivenessEvent,
    MoveMissedEvent, MoveFailedEvent, MoveNoEffectEvent,
    MultiHitStrikeEvent, MultiHitCompleteEvent,
    StatusAppliedEvent, StatusCuredEvent, StatusDamageEvent,
    StatusPreventedActionEvent, ConfusionSelfHitEvent,
    StatChangedEvent, StatLimitReachedEvent,
    ScreenActivatedEvent, ScreenExpiredEvent, ScreenBlockedEvent, ScreenReducedDamageEvent,
    PokemonHealedEvent, PokemonFaintedEvent, HPDrainedEvent,
    PokemonTrappedEvent, TrapDamageEvent, TrapEscapedEvent,
    SubstituteCreatedEvent, SubstituteBrokeEvent, SubstituteBlockedEvent,
    RechargeNeededEvent, ChargingMoveEvent, RageIncreasedEvent,
    LeechSeedPlantedEvent, LeechSeedDamageEvent, MistProtectionEvent,
    MoveDisabledEvent, MoveReenabledEvent, InfoEvent,
)
from ..bus import BattleEventBus


class Colors:
    """ANSI color codes"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'


class CLIHandler:
    """
    Renders battle events to the terminal.

    Subscribes to a BattleEventBus and prints formatted messages
    for each event type.
    """

    def __init__(self, bus: Optional[BattleEventBus] = None, enabled: bool = True):
        """
        Initialize the CLI handler.

        Args:
            bus: Event bus to subscribe to. If None, must call subscribe_to() later.
            enabled: If False, no output will be printed.
        """
        self.enabled = enabled
        self._bus = bus
        if bus:
            self.subscribe_to(bus)

    def subscribe_to(self, bus: BattleEventBus) -> None:
        """Subscribe to all events on the given bus"""
        self._bus = bus
        bus.subscribe(self.handle_event)

    def handle_event(self, event: BattleEvent) -> None:
        """Main event handler - dispatches to specific handlers"""
        if not self.enabled:
            return

        handler_map = {
            EventType.BATTLE_START: self._handle_battle_start,
            EventType.BATTLE_END: self._handle_battle_end,
            EventType.TURN_START: self._handle_turn_start,
            EventType.TURN_END: self._handle_turn_end,
            EventType.MOVE_USED: self._handle_move_used,
            EventType.DAMAGE_DEALT: self._handle_damage_dealt,
            EventType.CRITICAL_HIT: self._handle_critical_hit,
            EventType.EFFECTIVENESS: self._handle_effectiveness,
            EventType.MOVE_MISSED: self._handle_move_missed,
            EventType.MOVE_FAILED: self._handle_move_failed,
            EventType.MOVE_NO_EFFECT: self._handle_move_no_effect,
            EventType.MULTI_HIT_STRIKE: self._handle_multi_hit_strike,
            EventType.MULTI_HIT_COMPLETE: self._handle_multi_hit_complete,
            EventType.STATUS_APPLIED: self._handle_status_applied,
            EventType.STATUS_CURED: self._handle_status_cured,
            EventType.STATUS_DAMAGE: self._handle_status_damage,
            EventType.STATUS_PREVENTED_ACTION: self._handle_status_prevented,
            EventType.CONFUSION_SELF_HIT: self._handle_confusion_self_hit,
            EventType.STAT_CHANGED: self._handle_stat_changed,
            EventType.STAT_LIMIT_REACHED: self._handle_stat_limit,
            EventType.SCREEN_ACTIVATED: self._handle_screen_activated,
            EventType.SCREEN_EXPIRED: self._handle_screen_expired,
            EventType.SCREEN_BLOCKED: self._handle_screen_blocked,
            EventType.SCREEN_REDUCED_DAMAGE: self._handle_screen_reduced,
            EventType.POKEMON_HEALED: self._handle_pokemon_healed,
            EventType.POKEMON_FAINTED: self._handle_pokemon_fainted,
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
            EventType.INFO: self._handle_info,
        }

        handler = handler_map.get(event.event_type)
        if handler:
            handler(event)

    # ============== Battle Flow ==============

    def _handle_battle_start(self, event: BattleStartEvent) -> None:
        print(f"\n{Colors.BOLD}=== BATALLA POKÉMON ==={Colors.RESET}")
        print(f"{event.pokemon1_name} vs {event.pokemon2_name}\n")

    def _handle_battle_end(self, event: BattleEndEvent) -> None:
        print(f"\n{Colors.BOLD}=== FIN DE LA BATALLA ==={Colors.RESET}")
        if event.winner_name:
            print(f"{Colors.GREEN}¡{event.winner_name} gana!{Colors.RESET}")
        elif event.reason == "turn_limit":
            print(f"{Colors.YELLOW}¡La batalla terminó en empate por límite de turnos!{Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}¡Ambos Pokémon cayeron!{Colors.RESET}")

    def _handle_turn_start(self, event: TurnStartEvent) -> None:
        print(f"\n{Colors.CYAN}--- Turno {event.turn} ---{Colors.RESET}")

    def _handle_turn_end(self, event: TurnEndEvent) -> None:
        # Optional: show HP summary at end of turn
        pass

    # ============== Combat ==============

    def _handle_move_used(self, event: MoveUsedEvent) -> None:
        if event.is_continuation:
            print(f"{Colors.BOLD}{event.attacker_name}{Colors.RESET} continúa usando {Colors.YELLOW}{event.move_name}{Colors.RESET}!")
        else:
            print(f"\n{Colors.BOLD}{event.attacker_name}{Colors.RESET} usa {Colors.YELLOW}{event.move_name}{Colors.RESET}!")

    def _handle_damage_dealt(self, event: DamageDealtEvent) -> None:
        print(f"{event.defender_name} recibe {Colors.RED}{event.damage}{Colors.RESET} de daño! (HP: {event.defender_hp}/{event.defender_max_hp})")

    def _handle_critical_hit(self, event: CriticalHitEvent) -> None:
        print(f"{Colors.YELLOW}¡Golpe crítico!{Colors.RESET}")

    def _handle_effectiveness(self, event: EffectivenessEvent) -> None:
        if event.multiplier >= 2:
            print(f"{Colors.GREEN}¡Es súper efectivo!{Colors.RESET}")
        elif event.multiplier <= 0.5 and event.multiplier > 0:
            print(f"{Colors.RED}No es muy efectivo...{Colors.RESET}")

    def _handle_move_missed(self, event: MoveMissedEvent) -> None:
        if event.reason in ("underground", "flying"):
            print(f"¡El ataque falló! ({event.defender_name} está fuera de alcance)")
        else:
            print(f"¡El ataque de {event.attacker_name} falló!")

    def _handle_move_failed(self, event: MoveFailedEvent) -> None:
        if event.reason == "disabled":
            print(f"¡{event.move_name} está deshabilitado!")
        elif event.reason == "no_pp":
            print(f"¡{event.move_name} no tiene PP!")
        else:
            print(f"¡Pero falló!")

    def _handle_move_no_effect(self, event: MoveNoEffectEvent) -> None:
        print(f"No afecta a {event.defender_name}...")

    # ============== Multi-hit ==============

    def _handle_multi_hit_strike(self, event: MultiHitStrikeEvent) -> None:
        crit_text = f" {Colors.YELLOW}¡Crítico!{Colors.RESET}" if event.is_critical else ""
        print(f"  Golpe {event.hit_number}: {event.damage} de daño{crit_text}")

    def _handle_multi_hit_complete(self, event: MultiHitCompleteEvent) -> None:
        print(f"¡Golpeó {Colors.BOLD}{event.total_hits}{Colors.RESET} veces! Daño total: {Colors.RED}{event.total_damage}{Colors.RESET}")

    # ============== Status ==============

    def _handle_status_applied(self, event: StatusAppliedEvent) -> None:
        status_messages = {
            "burn": f"¡{event.pokemon_name} fue quemado!",
            "freeze": f"¡{event.pokemon_name} fue congelado!",
            "paralysis": f"¡{event.pokemon_name} fue paralizado!",
            "poison": f"¡{event.pokemon_name} fue envenenado!",
            "sleep": f"¡{event.pokemon_name} se durmió!",
            "confusion": f"¡{event.pokemon_name} está confundido!",
        }
        msg = status_messages.get(event.status, f"¡{event.pokemon_name} fue afectado por {event.status}!")
        print(f"{Colors.MAGENTA}{msg}{Colors.RESET}")

    def _handle_status_cured(self, event: StatusCuredEvent) -> None:
        status_messages = {
            "freeze": f"¡{event.pokemon_name} se descongeló!",
            "sleep": f"¡{event.pokemon_name} despertó!",
            "confusion": f"¡{event.pokemon_name} ya no está confundido!",
        }
        msg = status_messages.get(event.status, f"¡{event.pokemon_name} se curó de {event.status}!")
        print(f"{Colors.GREEN}{msg}{Colors.RESET}")

    def _handle_status_damage(self, event: StatusDamageEvent) -> None:
        status_messages = {
            "burn": f"{event.pokemon_name} sufre {event.damage} de daño por quemadura!",
            "poison": f"{event.pokemon_name} sufre {event.damage} de daño por envenenamiento!",
        }
        msg = status_messages.get(event.status, f"{event.pokemon_name} sufre {event.damage} de daño!")
        print(f"{Colors.MAGENTA}{msg}{Colors.RESET}")

    def _handle_status_prevented(self, event: StatusPreventedActionEvent) -> None:
        status_messages = {
            "sleep": f"{event.pokemon_name} está dormido!",
            "freeze": f"{event.pokemon_name} está congelado!",
            "paralysis": f"¡{event.pokemon_name} está paralizado! No se puede mover!",
        }
        msg = status_messages.get(event.status, f"{event.pokemon_name} no puede moverse!")
        print(f"{Colors.YELLOW}{msg}{Colors.RESET}")

    def _handle_confusion_self_hit(self, event: ConfusionSelfHitEvent) -> None:
        print(f"{Colors.MAGENTA}¡{event.pokemon_name} está confundido!{Colors.RESET}")
        print(f"¡Se hirió a sí mismo por {event.damage} de daño!")

    # ============== Stats ==============

    def _handle_stat_changed(self, event: StatChangedEvent) -> None:
        stat_names = {
            "attack": "Ataque",
            "defense": "Defensa",
            "special": "Especial",
            "speed": "Velocidad",
            "accuracy": "Precisión",
            "evasion": "Evasión",
        }
        stat_name = stat_names.get(event.stat, event.stat)

        if event.stages > 0:
            intensity = "mucho " if abs(event.stages) >= 2 else ""
            print(f"{Colors.GREEN}¡El {stat_name} de {event.pokemon_name} subió {intensity}!{Colors.RESET}")
        else:
            intensity = "mucho " if abs(event.stages) >= 2 else ""
            print(f"{Colors.RED}¡El {stat_name} de {event.pokemon_name} bajó {intensity}!{Colors.RESET}")

    def _handle_stat_limit(self, event: StatLimitReachedEvent) -> None:
        stat_names = {
            "attack": "Ataque",
            "defense": "Defensa",
            "special": "Especial",
            "speed": "Velocidad",
            "accuracy": "Precisión",
            "evasion": "Evasión",
        }
        stat_name = stat_names.get(event.stat, event.stat)
        direction = "más" if event.at_max else "menos"
        print(f"{Colors.YELLOW}¡El {stat_name} de {event.pokemon_name} no puede subir {direction}!{Colors.RESET}")

    # ============== Screens ==============

    def _handle_screen_activated(self, event: ScreenActivatedEvent) -> None:
        screen_names = {
            "reflect": "Reflect",
            "light_screen": "Light Screen",
            "mist": "Mist",
        }
        screen = screen_names.get(event.screen, event.screen)
        print(f"{Colors.CYAN}¡{event.pokemon_name} levantó {screen}!{Colors.RESET}")

    def _handle_screen_expired(self, event: ScreenExpiredEvent) -> None:
        screen_names = {
            "reflect": "Reflect",
            "light_screen": "Light Screen",
            "mist": "Mist",
        }
        screen = screen_names.get(event.screen, event.screen)
        print(f"{Colors.DIM}El {screen} de {event.pokemon_name} se desvaneció.{Colors.RESET}")

    def _handle_screen_blocked(self, event: ScreenBlockedEvent) -> None:
        print(f"¡{event.screen} ya está activo!")

    def _handle_screen_reduced(self, event: ScreenReducedDamageEvent) -> None:
        screen_names = {
            "reflect": "Reflect",
            "light_screen": "Light Screen",
        }
        screen = screen_names.get(event.screen, event.screen)
        print(f"{Colors.CYAN}¡{screen} reduce el daño!{Colors.RESET}")

    # ============== HP Changes ==============

    def _handle_pokemon_healed(self, event: PokemonHealedEvent) -> None:
        print(f"{Colors.GREEN}¡{event.pokemon_name} recuperó {event.amount} HP!{Colors.RESET} (HP: {event.current_hp}/{event.max_hp})")

    def _handle_pokemon_fainted(self, event: PokemonFaintedEvent) -> None:
        print(f"{Colors.RED}¡{event.pokemon_name} se debilitó!{Colors.RESET}")

    def _handle_hp_drained(self, event: HPDrainedEvent) -> None:
        print(f"{Colors.GREEN}¡{event.target_name} absorbió {event.amount} HP de {event.source_name}!{Colors.RESET}")

    # ============== Special Mechanics ==============

    def _handle_pokemon_trapped(self, event: PokemonTrappedEvent) -> None:
        print(f"¡{event.pokemon_name} está atrapado por {event.move_name}!")

    def _handle_trap_damage(self, event: TrapDamageEvent) -> None:
        print(f"¡{event.pokemon_name} sigue atrapado y recibe {event.damage} de daño!")

    def _handle_trap_escaped(self, event: TrapEscapedEvent) -> None:
        print(f"¡{event.pokemon_name} se liberó!")

    def _handle_substitute_created(self, event: SubstituteCreatedEvent) -> None:
        print(f"¡{event.pokemon_name} creó un sustituto!")

    def _handle_substitute_broke(self, event: SubstituteBrokeEvent) -> None:
        print(f"¡El sustituto de {event.pokemon_name} se rompió!")

    def _handle_substitute_blocked(self, event: SubstituteBlockedEvent) -> None:
        print(f"¡El sustituto absorbió el daño!")

    def _handle_recharge_needed(self, event: RechargeNeededEvent) -> None:
        print(f"{event.pokemon_name} debe recargar!")

    def _handle_charging_move(self, event: ChargingMoveEvent) -> None:
        charge_messages = {
            "dig_underground": f"¡{event.pokemon_name} se escondió bajo tierra!",
            "fly_high": f"¡{event.pokemon_name} voló muy alto!",
            "skull_bash_defense": f"¡{event.pokemon_name} baja la cabeza!",
            "sky_attack_glow": f"¡{event.pokemon_name} está brillando!",
            "solar_beam_absorb": f"¡{event.pokemon_name} está absorbiendo luz!",
            "razor_wind_charge": f"¡{event.pokemon_name} está cargando energía!",
        }
        msg = charge_messages.get(event.message_key, f"¡{event.pokemon_name} está preparando {event.move_name}!")
        print(f"{Colors.CYAN}{msg}{Colors.RESET}")

    def _handle_rage_increased(self, event: RageIncreasedEvent) -> None:
        print(f"{Colors.RED}¡La furia de {event.pokemon_name} aumenta!{Colors.RESET}")

    def _handle_leech_seed_planted(self, event: LeechSeedPlantedEvent) -> None:
        print(f"¡{event.pokemon_name} fue plantado con Leech Seed!")

    def _handle_leech_seed_damage(self, event: LeechSeedDamageEvent) -> None:
        print(f"¡Leech Seed drena {event.damage} HP de {event.pokemon_name}!")

    def _handle_mist_protection(self, event: MistProtectionEvent) -> None:
        print(f"{Colors.CYAN}¡Mist protege a {event.pokemon_name}!{Colors.RESET}")

    def _handle_move_disabled(self, event: MoveDisabledEvent) -> None:
        print(f"¡{event.move_name} de {event.pokemon_name} fue deshabilitado!")

    def _handle_move_reenabled(self, event: MoveReenabledEvent) -> None:
        print(f"¡{event.move_name} de {event.pokemon_name} ya no está deshabilitado!")

    def _handle_info(self, event: InfoEvent) -> None:
        print(f"{Colors.DIM}{event.message}{Colors.RESET}")
