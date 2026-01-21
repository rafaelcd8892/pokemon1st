"""Tests for the event system"""

import pytest
from engine.events import (
    BattleEventBus, EventType,
    BattleStartEvent, BattleEndEvent, TurnStartEvent,
    MoveUsedEvent, DamageDealtEvent, CriticalHitEvent,
    StatusAppliedEvent, StatChangedEvent,
    get_event_bus, set_event_bus, reset_event_bus,
)
from engine.events.handlers import CLIHandler


class TestBattleEventBus:
    """Test the event bus functionality"""

    def test_emit_and_history(self):
        """Test that emitted events are recorded in history"""
        bus = BattleEventBus()

        bus.emit(BattleStartEvent(turn=0, pokemon1_name="Pikachu", pokemon2_name="Charizard"))
        bus.emit(TurnStartEvent(turn=1))
        bus.emit(MoveUsedEvent(turn=1, attacker_name="Pikachu", move_name="Thunderbolt"))

        history = bus.get_history()
        assert len(history) == 3

        assert history[0].event_type == EventType.BATTLE_START
        assert history[1].event_type == EventType.TURN_START
        assert history[2].event_type == EventType.MOVE_USED

    def test_subscribe_to_all_events(self):
        """Test subscribing to all events"""
        bus = BattleEventBus()
        received = []

        def handler(event):
            received.append(event)

        bus.subscribe(handler)  # No event_type = all events

        bus.emit(BattleStartEvent(turn=0, pokemon1_name="A", pokemon2_name="B"))
        bus.emit(MoveUsedEvent(turn=1, attacker_name="A", move_name="Tackle"))

        assert len(received) == 2

    def test_subscribe_to_specific_event(self):
        """Test subscribing to a specific event type"""
        bus = BattleEventBus()
        received = []

        def handler(event):
            received.append(event)

        bus.subscribe(handler, EventType.MOVE_USED)

        bus.emit(BattleStartEvent(turn=0, pokemon1_name="A", pokemon2_name="B"))
        bus.emit(MoveUsedEvent(turn=1, attacker_name="A", move_name="Tackle"))
        bus.emit(DamageDealtEvent(turn=1, attacker_name="A", defender_name="B", damage=20))

        # Should only receive MOVE_USED
        assert len(received) == 1
        assert received[0].event_type == EventType.MOVE_USED

    def test_filter_history_by_type(self):
        """Test filtering history by event type"""
        bus = BattleEventBus()

        bus.emit(BattleStartEvent(turn=0, pokemon1_name="A", pokemon2_name="B"))
        bus.emit(MoveUsedEvent(turn=1, attacker_name="A", move_name="Tackle"))
        bus.emit(DamageDealtEvent(turn=1, attacker_name="A", defender_name="B", damage=20))
        bus.emit(MoveUsedEvent(turn=1, attacker_name="B", move_name="Scratch"))

        move_events = bus.get_history(event_type=EventType.MOVE_USED)
        assert len(move_events) == 2

        damage_events = bus.get_history(event_type=EventType.DAMAGE_DEALT)
        assert len(damage_events) == 1

    def test_filter_history_by_turn(self):
        """Test filtering history by turn number"""
        bus = BattleEventBus()

        bus.emit(TurnStartEvent(turn=1))
        bus.emit(MoveUsedEvent(turn=1, attacker_name="A", move_name="Tackle"))
        bus.emit(TurnStartEvent(turn=2))
        bus.emit(MoveUsedEvent(turn=2, attacker_name="A", move_name="Scratch"))
        bus.emit(MoveUsedEvent(turn=2, attacker_name="B", move_name="Bite"))

        turn1_events = bus.get_history(turn=1)
        assert len(turn1_events) == 2

        turn2_events = bus.get_history(turn=2)
        assert len(turn2_events) == 3

    def test_unsubscribe(self):
        """Test unsubscribing a handler"""
        bus = BattleEventBus()
        received = []

        def handler(event):
            received.append(event)

        bus.subscribe(handler)
        bus.emit(MoveUsedEvent(turn=1, attacker_name="A", move_name="Tackle"))
        assert len(received) == 1

        bus.unsubscribe(handler)
        bus.emit(MoveUsedEvent(turn=1, attacker_name="A", move_name="Scratch"))
        assert len(received) == 1  # Still 1, handler was removed

    def test_clear_history(self):
        """Test clearing event history"""
        bus = BattleEventBus()

        bus.emit(MoveUsedEvent(turn=1, attacker_name="A", move_name="Tackle"))
        bus.emit(MoveUsedEvent(turn=1, attacker_name="B", move_name="Scratch"))

        assert len(bus.get_history()) == 2

        bus.clear_history()
        assert len(bus.get_history()) == 0

    def test_get_last_event(self):
        """Test getting the most recent event"""
        bus = BattleEventBus()

        bus.emit(MoveUsedEvent(turn=1, attacker_name="A", move_name="Tackle"))
        bus.emit(DamageDealtEvent(turn=1, attacker_name="A", defender_name="B", damage=20))

        last = bus.get_last_event()
        assert last.event_type == EventType.DAMAGE_DEALT

        last_move = bus.get_last_event(EventType.MOVE_USED)
        assert last_move.attacker_name == "A"

    def test_history_disabled(self):
        """Test that history can be disabled"""
        bus = BattleEventBus(record_history=False)

        bus.emit(MoveUsedEvent(turn=1, attacker_name="A", move_name="Tackle"))
        bus.emit(MoveUsedEvent(turn=1, attacker_name="B", move_name="Scratch"))

        assert len(bus.get_history()) == 0

    def test_export_history(self):
        """Test exporting history as dictionaries"""
        bus = BattleEventBus()

        bus.emit(BattleStartEvent(turn=0, pokemon1_name="Pikachu", pokemon2_name="Charizard"))

        exported = bus.export_history()
        assert len(exported) == 1
        assert exported[0]['event_type'] == 'BATTLE_START'
        assert exported[0]['turn'] == 0


class TestGlobalEventBus:
    """Test the global event bus functions"""

    def test_get_event_bus_creates_instance(self):
        """Test that get_event_bus creates a bus if none exists"""
        reset_event_bus()
        bus = get_event_bus()
        assert bus is not None
        assert isinstance(bus, BattleEventBus)

    def test_get_event_bus_returns_same_instance(self):
        """Test that get_event_bus returns the same instance"""
        reset_event_bus()
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        assert bus1 is bus2

    def test_set_event_bus(self):
        """Test setting a custom event bus"""
        reset_event_bus()
        custom_bus = BattleEventBus()
        set_event_bus(custom_bus)

        assert get_event_bus() is custom_bus


class TestEventDataclasses:
    """Test event dataclass properties"""

    def test_events_are_immutable(self):
        """Test that events cannot be modified after creation"""
        event = MoveUsedEvent(turn=1, attacker_name="Pikachu", move_name="Thunderbolt")

        with pytest.raises(AttributeError):
            event.attacker_name = "Charizard"

    def test_event_to_dict(self):
        """Test converting events to dictionaries"""
        event = DamageDealtEvent(
            turn=1,
            attacker_name="Pikachu",
            defender_name="Charizard",
            damage=50,
            defender_hp=150,
            defender_max_hp=200,
            move_name="Thunderbolt"
        )

        d = event.to_dict()
        assert d['event_type'] == 'DAMAGE_DEALT'
        assert d['turn'] == 1

    def test_battle_start_event_fields(self):
        """Test BattleStartEvent has correct fields"""
        event = BattleStartEvent(
            turn=0,
            pokemon1_name="Pikachu",
            pokemon2_name="Charizard"
        )

        assert event.event_type == EventType.BATTLE_START
        assert event.pokemon1_name == "Pikachu"
        assert event.pokemon2_name == "Charizard"
        assert event.turn == 0

    def test_damage_dealt_event_fields(self):
        """Test DamageDealtEvent has correct fields"""
        event = DamageDealtEvent(
            turn=1,
            attacker_name="Pikachu",
            defender_name="Charizard",
            damage=85,
            defender_hp=115,
            defender_max_hp=200,
            move_name="Thunderbolt"
        )

        assert event.event_type == EventType.DAMAGE_DEALT
        assert event.damage == 85
        assert event.defender_hp == 115


class TestCLIHandler:
    """Test the CLI event handler"""

    def test_handler_receives_events(self, capsys):
        """Test that CLI handler prints event messages"""
        bus = BattleEventBus()
        handler = CLIHandler(bus)

        bus.emit(BattleStartEvent(turn=0, pokemon1_name="Pikachu", pokemon2_name="Charizard"))

        captured = capsys.readouterr()
        assert "BATALLA POKÉMON" in captured.out
        assert "Pikachu" in captured.out
        assert "Charizard" in captured.out

    def test_handler_can_be_disabled(self, capsys):
        """Test that handler can be disabled"""
        bus = BattleEventBus()
        handler = CLIHandler(bus, enabled=False)

        bus.emit(BattleStartEvent(turn=0, pokemon1_name="Pikachu", pokemon2_name="Charizard"))

        captured = capsys.readouterr()
        assert captured.out == ""

    def test_handler_prints_damage(self, capsys):
        """Test damage event output"""
        bus = BattleEventBus()
        handler = CLIHandler(bus)

        bus.emit(DamageDealtEvent(
            turn=1,
            attacker_name="Pikachu",
            defender_name="Charizard",
            damage=50,
            defender_hp=150,
            defender_max_hp=200,
            move_name="Thunderbolt"
        ))

        captured = capsys.readouterr()
        assert "Charizard" in captured.out
        assert "50" in captured.out
        assert "150/200" in captured.out

    def test_handler_prints_critical_hit(self, capsys):
        """Test critical hit event output"""
        bus = BattleEventBus()
        handler = CLIHandler(bus)

        bus.emit(CriticalHitEvent(turn=1, attacker_name="Pikachu"))

        captured = capsys.readouterr()
        assert "crítico" in captured.out.lower()

    def test_handler_prints_status_applied(self, capsys):
        """Test status application event output"""
        bus = BattleEventBus()
        handler = CLIHandler(bus)

        bus.emit(StatusAppliedEvent(turn=1, pokemon_name="Charizard", status="paralysis"))

        captured = capsys.readouterr()
        assert "paralizado" in captured.out.lower()
