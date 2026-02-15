"""Buffered Event Handler — collects formatted event messages into a ring buffer.

Used by the enhanced move-selection UI to show a battle log panel
without printing to stdout (which would break curses).
"""

from typing import List, Optional
from ..types import (
    BattleEvent, EventType,
    MoveUsedEvent, DamageDealtEvent, CriticalHitEvent, EffectivenessEvent,
    MoveMissedEvent, MoveFailedEvent, MoveNoEffectEvent,
    MultiHitCompleteEvent,
    StatusAppliedEvent, StatusCuredEvent, StatusDamageEvent,
    StatusPreventedActionEvent, ConfusionSelfHitEvent,
    StatChangedEvent,
    PokemonFaintedEvent, PokemonHealedEvent, HPDrainedEvent,
    InfoEvent,
)
from ..bus import BattleEventBus


def format_event_plain_text(event: BattleEvent) -> Optional[str]:
    """
    Convert a battle event to a plain-text string (no ANSI codes).

    Returns None for event types that don't need a log line.
    """
    et = event.event_type

    if et == EventType.MOVE_USED:
        e: MoveUsedEvent = event
        if e.is_continuation:
            return f"{e.attacker_name} continúa usando {e.move_name}!"
        return f"{e.attacker_name} usa {e.move_name}!"

    if et == EventType.DAMAGE_DEALT:
        e: DamageDealtEvent = event
        return f"{e.defender_name} recibe {e.damage} de daño! (HP: {e.defender_hp}/{e.defender_max_hp})"

    if et == EventType.CRITICAL_HIT:
        return "¡Golpe crítico!"

    if et == EventType.EFFECTIVENESS:
        e: EffectivenessEvent = event
        if e.multiplier >= 2:
            return "¡Es súper efectivo!"
        elif 0 < e.multiplier <= 0.5:
            return "No es muy efectivo..."
        return None

    if et == EventType.MOVE_MISSED:
        e: MoveMissedEvent = event
        return f"¡El ataque de {e.attacker_name} falló!"

    if et == EventType.MOVE_FAILED:
        e: MoveFailedEvent = event
        if e.reason == "disabled":
            return f"¡{e.move_name} está deshabilitado!"
        return "¡Pero falló!"

    if et == EventType.MOVE_NO_EFFECT:
        e: MoveNoEffectEvent = event
        return f"No afecta a {e.defender_name}..."

    if et == EventType.MULTI_HIT_COMPLETE:
        e: MultiHitCompleteEvent = event
        return f"¡Golpeó {e.total_hits} veces! Daño total: {e.total_damage}"

    if et == EventType.STATUS_APPLIED:
        e: StatusAppliedEvent = event
        status_msgs = {
            "burn": f"¡{e.pokemon_name} fue quemado!",
            "freeze": f"¡{e.pokemon_name} fue congelado!",
            "paralysis": f"¡{e.pokemon_name} fue paralizado!",
            "poison": f"¡{e.pokemon_name} fue envenenado!",
            "sleep": f"¡{e.pokemon_name} se durmió!",
            "confusion": f"¡{e.pokemon_name} está confundido!",
        }
        return status_msgs.get(e.status, f"¡{e.pokemon_name} fue afectado por {e.status}!")

    if et == EventType.STATUS_CURED:
        e: StatusCuredEvent = event
        return f"¡{e.pokemon_name} se curó de {e.status}!"

    if et == EventType.STATUS_DAMAGE:
        e: StatusDamageEvent = event
        return f"{e.pokemon_name} sufre {e.damage} de daño por {e.status}!"

    if et == EventType.STATUS_PREVENTED_ACTION:
        e: StatusPreventedActionEvent = event
        status_msgs = {
            "sleep": f"{e.pokemon_name} está dormido!",
            "freeze": f"{e.pokemon_name} está congelado!",
            "paralysis": f"¡{e.pokemon_name} está paralizado! No se puede mover!",
        }
        return status_msgs.get(e.status, f"{e.pokemon_name} no puede moverse!")

    if et == EventType.CONFUSION_SELF_HIT:
        e: ConfusionSelfHitEvent = event
        return f"¡{e.pokemon_name} se hirió a sí mismo! ({e.damage} daño)"

    if et == EventType.STAT_CHANGED:
        e: StatChangedEvent = event
        stat_names = {
            "attack": "Ataque", "defense": "Defensa",
            "special": "Especial", "speed": "Velocidad",
            "accuracy": "Precisión", "evasion": "Evasión",
        }
        stat = stat_names.get(e.stat, e.stat)
        direction = "subió" if e.stages > 0 else "bajó"
        intensity = " mucho" if abs(e.stages) >= 2 else ""
        return f"¡{stat} de {e.pokemon_name} {direction}{intensity}!"

    if et == EventType.POKEMON_FAINTED:
        e: PokemonFaintedEvent = event
        return f"¡{e.pokemon_name} se debilitó!"

    if et == EventType.POKEMON_HEALED:
        e: PokemonHealedEvent = event
        return f"¡{e.pokemon_name} recuperó {e.amount} HP!"

    if et == EventType.HP_DRAINED:
        e: HPDrainedEvent = event
        return f"¡{e.target_name} absorbió {e.amount} HP!"

    if et == EventType.INFO:
        e: InfoEvent = event
        return e.message

    return None


class BufferedEventHandler:
    """
    Collects formatted event messages into a ring buffer.

    Subscribes to a BattleEventBus and converts events to plain-text
    log lines. Used by the curses UI to display a battle log panel.
    """

    def __init__(self, bus: BattleEventBus, max_lines: int = 50):
        self._messages: list[str] = []
        self._max_lines = max_lines
        bus.subscribe(self.handle_event)

    def handle_event(self, event: BattleEvent) -> None:
        """Format and buffer an event."""
        msg = format_event_plain_text(event)
        if msg:
            self._messages.append(msg)
            if len(self._messages) > self._max_lines:
                self._messages.pop(0)

    def get_recent(self, n: int = 10) -> list[str]:
        """Return the last n messages."""
        return self._messages[-n:]

    def clear(self) -> None:
        """Clear the buffer."""
        self._messages.clear()
