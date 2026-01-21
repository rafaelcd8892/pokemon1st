"""Battle Event Bus - Central hub for emitting and subscribing to battle events"""

from typing import Callable, Dict, List, Optional, Type, Any
from .types import BattleEvent, EventType


# Type alias for event handlers
EventHandler = Callable[[BattleEvent], None]


class BattleEventBus:
    """
    Central event bus for battle events.

    Supports:
    - Subscribing handlers to specific event types or all events
    - Emitting events to all subscribed handlers
    - Maintaining event history for replay/logging
    - Filtering events by type
    """

    def __init__(self, record_history: bool = True):
        """
        Initialize the event bus.

        Args:
            record_history: If True, all events are stored in history
        """
        self._handlers: Dict[Optional[EventType], List[EventHandler]] = {}
        self._history: List[BattleEvent] = []
        self._record_history = record_history
        self._current_turn = 0

    @property
    def current_turn(self) -> int:
        """Get the current turn number"""
        return self._current_turn

    @current_turn.setter
    def current_turn(self, value: int) -> None:
        """Set the current turn number"""
        self._current_turn = value

    def subscribe(
        self,
        handler: EventHandler,
        event_type: Optional[EventType] = None
    ) -> None:
        """
        Subscribe a handler to events.

        Args:
            handler: Callable that receives BattleEvent
            event_type: Specific event type to subscribe to, or None for all events
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def unsubscribe(
        self,
        handler: EventHandler,
        event_type: Optional[EventType] = None
    ) -> None:
        """
        Unsubscribe a handler from events.

        Args:
            handler: The handler to remove
            event_type: The event type to unsubscribe from
        """
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
            except ValueError:
                pass

    def emit(self, event: BattleEvent) -> None:
        """
        Emit an event to all subscribed handlers.

        Args:
            event: The event to emit
        """
        # Record in history
        if self._record_history:
            self._history.append(event)

        # Call type-specific handlers
        event_type = event.event_type
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                handler(event)

        # Call global handlers (subscribed to None)
        if None in self._handlers:
            for handler in self._handlers[None]:
                handler(event)

    def get_history(
        self,
        event_type: Optional[EventType] = None,
        turn: Optional[int] = None
    ) -> List[BattleEvent]:
        """
        Get event history, optionally filtered.

        Args:
            event_type: Filter by event type
            turn: Filter by turn number

        Returns:
            List of matching events
        """
        result = self._history

        if event_type is not None:
            result = [e for e in result if e.event_type == event_type]

        if turn is not None:
            result = [e for e in result if e.turn == turn]

        return result

    def clear_history(self) -> None:
        """Clear the event history"""
        self._history.clear()

    def clear_handlers(self) -> None:
        """Remove all handlers"""
        self._handlers.clear()

    def reset(self) -> None:
        """Reset the event bus completely"""
        self.clear_history()
        self.clear_handlers()
        self._current_turn = 0

    def get_events_by_type(self, event_type: EventType) -> List[BattleEvent]:
        """Convenience method to get all events of a specific type"""
        return self.get_history(event_type=event_type)

    def get_last_event(
        self,
        event_type: Optional[EventType] = None
    ) -> Optional[BattleEvent]:
        """Get the most recent event, optionally of a specific type"""
        events = self.get_history(event_type=event_type)
        return events[-1] if events else None

    def export_history(self) -> List[Dict[str, Any]]:
        """Export history as list of dictionaries for serialization"""
        return [event.to_dict() for event in self._history]


# Global event bus instance (can be replaced for testing)
_global_bus: Optional[BattleEventBus] = None


def get_event_bus() -> BattleEventBus:
    """Get the global event bus instance, creating if needed"""
    global _global_bus
    if _global_bus is None:
        _global_bus = BattleEventBus()
    return _global_bus


def set_event_bus(bus: BattleEventBus) -> None:
    """Set the global event bus instance (useful for testing)"""
    global _global_bus
    _global_bus = bus


def reset_event_bus() -> None:
    """Reset the global event bus"""
    global _global_bus
    if _global_bus is not None:
        _global_bus.reset()
    _global_bus = None
