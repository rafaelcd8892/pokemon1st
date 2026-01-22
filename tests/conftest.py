"""Pytest configuration and shared fixtures"""

import pytest
from typing import List, Optional

from models.pokemon import Pokemon
from models.stats import Stats
from models.move import Move
from models.enums import Type, Status, MoveCategory
from engine.events import BattleEventBus, BattleEvent, reset_event_bus, set_event_bus
from data.data_loader import get_pokemon_data, create_move, get_pokemon_moves_gen1


@pytest.fixture
def event_bus():
    """Provides a fresh event bus for each test"""
    bus = BattleEventBus(record_history=True)
    set_event_bus(bus)
    yield bus
    reset_event_bus()


@pytest.fixture
def captured_events(event_bus):
    """Captures all events emitted during a test"""
    events: List[BattleEvent] = []

    def capture(event: BattleEvent):
        events.append(event)

    event_bus.subscribe(capture)
    return events


def create_test_pokemon(
    name: str = "TestMon",
    types: Optional[List[Type]] = None,
    hp: int = 100,
    attack: int = 100,
    defense: int = 100,
    special: int = 100,
    speed: int = 100,
    moves: Optional[List[Move]] = None,
    level: int = 50,
) -> Pokemon:
    """
    Factory function to create Pokemon for testing.

    Args:
        name: Pokemon name
        types: List of types (defaults to [NORMAL])
        hp: Base HP stat
        attack: Base Attack stat
        defense: Base Defense stat
        special: Base Special stat
        speed: Base Speed stat
        moves: List of moves (defaults to Tackle)
        level: Pokemon level

    Returns:
        Configured Pokemon instance
    """
    if types is None:
        types = [Type.NORMAL]

    if moves is None:
        moves = [create_test_move()]

    stats = Stats(hp=hp, attack=attack, defense=defense, special=special, speed=speed)
    # Use legacy mode (use_calculated_stats=False) for tests that expect raw stats
    return Pokemon(name, types, stats, moves, level=level, use_calculated_stats=False)


def create_test_move(
    name: str = "Test Move",
    move_type: Type = Type.NORMAL,
    category: MoveCategory = MoveCategory.PHYSICAL,
    power: int = 50,
    accuracy: int = 100,
    pp: int = 35,
    status_effect: Optional[Status] = None,
    status_chance: int = 0,
) -> Move:
    """
    Factory function to create moves for testing.

    Args:
        name: Move name
        move_type: Move type
        category: Physical/Special/Status
        power: Base power
        accuracy: Accuracy percentage
        pp: Power points
        status_effect: Optional status effect
        status_chance: Chance to apply status (0-100)

    Returns:
        Configured Move instance
    """
    return Move(
        name=name,
        type=move_type,
        category=category,
        power=power,
        accuracy=accuracy,
        pp=pp,
        max_pp=pp,
        status_effect=status_effect,
        status_chance=status_chance,
    )


@pytest.fixture
def pikachu():
    """Standard Pikachu for testing"""
    poke_data = get_pokemon_data('pikachu')
    moves = [
        create_move('thunderbolt'),
        create_move('thunder-wave'),
        create_move('quick-attack'),
        create_move('agility'),
    ]
    stats = Stats(
        hp=poke_data['stats']['hp'],
        attack=poke_data['stats']['attack'],
        defense=poke_data['stats']['defense'],
        special=poke_data['stats']['special-attack'],
        speed=poke_data['stats']['speed'],
    )
    types = [Type[t.upper()] for t in poke_data['types']]
    return Pokemon(poke_data['name'], types, stats, moves, level=50)


@pytest.fixture
def charizard():
    """Standard Charizard for testing"""
    poke_data = get_pokemon_data('charizard')
    moves = [
        create_move('flamethrower'),
        create_move('fire-spin'),
        create_move('slash'),
        create_move('fly'),
    ]
    stats = Stats(
        hp=poke_data['stats']['hp'],
        attack=poke_data['stats']['attack'],
        defense=poke_data['stats']['defense'],
        special=poke_data['stats']['special-attack'],
        speed=poke_data['stats']['speed'],
    )
    types = [Type[t.upper()] for t in poke_data['types']]
    return Pokemon(poke_data['name'], types, stats, moves, level=50)


@pytest.fixture
def blastoise():
    """Standard Blastoise for testing"""
    poke_data = get_pokemon_data('blastoise')
    moves = [
        create_move('surf'),
        create_move('ice-beam'),
        create_move('skull-bash'),
        create_move('withdraw'),
    ]
    stats = Stats(
        hp=poke_data['stats']['hp'],
        attack=poke_data['stats']['attack'],
        defense=poke_data['stats']['defense'],
        special=poke_data['stats']['special-attack'],
        speed=poke_data['stats']['speed'],
    )
    types = [Type[t.upper()] for t in poke_data['types']]
    return Pokemon(poke_data['name'], types, stats, moves, level=50)


@pytest.fixture
def gengar():
    """Standard Gengar for testing (Ghost/Poison)"""
    poke_data = get_pokemon_data('gengar')
    moves = [
        create_move('shadow-ball') if 'shadow-ball' in get_pokemon_moves_gen1('gengar') else create_move('night-shade'),
        create_move('hypnosis'),
        create_move('dream-eater'),
        create_move('confuse-ray'),
    ]
    stats = Stats(
        hp=poke_data['stats']['hp'],
        attack=poke_data['stats']['attack'],
        defense=poke_data['stats']['defense'],
        special=poke_data['stats']['special-attack'],
        speed=poke_data['stats']['speed'],
    )
    types = [Type[t.upper()] for t in poke_data['types']]
    return Pokemon(poke_data['name'], types, stats, moves, level=50)
