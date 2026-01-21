"""
Local data loader for Pokemon Gen 1 data.
Replaces PokeAPI calls with local JSON file lookups.
"""

import json
from pathlib import Path
from typing import Optional

from models.enums import Type, Status, MoveCategory, StatType
from models.stats import Stats
from models.move import Move

DATA_DIR = Path(__file__).parent

# Cache loaded data
_pokemon_cache: Optional[dict] = None
_moves_cache: Optional[dict] = None
_learnsets_cache: Optional[dict] = None


def _load_json(filename: str) -> dict:
    """Load and parse JSON file."""
    with open(DATA_DIR / filename, 'r', encoding='utf-8') as f:
        return json.load(f)


def _get_pokemon_data() -> dict:
    """Load and cache pokemon.json."""
    global _pokemon_cache
    if _pokemon_cache is None:
        _pokemon_cache = _load_json('pokemon.json')
    return _pokemon_cache


def _get_moves_data() -> dict:
    """Load and cache moves.json."""
    global _moves_cache
    if _moves_cache is None:
        _moves_cache = _load_json('moves.json')
    return _moves_cache


def _get_learnsets_data() -> dict:
    """Load and cache learnsets.json."""
    global _learnsets_cache
    if _learnsets_cache is None:
        _learnsets_cache = _load_json('learnsets.json')
    return _learnsets_cache


def get_kanto_pokemon_list() -> list[str]:
    """Returns list of all 151 Kanto Pokemon names."""
    data = _get_pokemon_data()
    return [p['name'].lower() for p in data['pokemon']]


def get_pokemon_data(name_or_id) -> dict:
    """
    Get Pokemon data by name or ID.
    Returns dict with name, types, and stats matching the old API format.
    """
    data = _get_pokemon_data()
    search = str(name_or_id).lower()

    for pokemon in data['pokemon']:
        if str(pokemon['id']) == search or pokemon['name'].lower() == search:
            return {
                'name': pokemon['name'],
                'types': [t.capitalize() for t in pokemon['types']],
                'stats': {
                    'hp': pokemon['base_stats']['hp'],
                    'attack': pokemon['base_stats']['attack'],
                    'defense': pokemon['base_stats']['defense'],
                    'special-attack': pokemon['base_stats']['special'],
                    'speed': pokemon['base_stats']['speed']
                }
            }
    raise ValueError(f"Pokemon not found: {name_or_id}")


def get_pokemon_moves_gen1(name_or_id) -> list[str]:
    """Get list of Gen 1 learnable moves for a Pokemon."""
    data = _get_learnsets_data()
    name = str(name_or_id).lower()
    learnset = data['learnsets'].get(name, {})
    # Support both old format (list) and new format (dict with sources)
    if isinstance(learnset, list):
        return learnset
    return list(learnset.keys())


def get_pokemon_moves_with_source(name_or_id) -> dict[str, str]:
    """
    Get Gen 1 learnable moves for a Pokemon with their source.
    Returns dict mapping move_name -> source (level-up, tm, evolution)
    """
    data = _get_learnsets_data()
    name = str(name_or_id).lower()
    learnset = data['learnsets'].get(name, {})
    # Support both old format (list) and new format (dict with sources)
    if isinstance(learnset, list):
        return {move: "level-up" for move in learnset}
    return learnset


def get_move_data(move_name: str) -> dict:
    """
    Get move data by name.
    Returns dict matching the old API format.
    """
    data = _get_moves_data()
    # Normalize name: handle both "thunder-wave" and "Thunder Wave" formats
    normalized = move_name.lower().replace(' ', '-')

    for move in data['moves']:
        move_normalized = move['name'].lower().replace(' ', '-')
        if move_normalized == normalized:
            return {
                'name': move['name'].replace('-', ' ').title(),
                'type': move['type'].capitalize(),
                'category': move['category'].capitalize(),
                'power': move['power'],
                'accuracy': move['accuracy'],
                'pp': move['pp'],
                'status_effect': move.get('status_effect'),
                'status_chance': move.get('status_chance', 0),
                'stat_changes': move.get('stat_changes'),
                'target_self': move.get('target_self', False)
            }
    raise ValueError(f"Move not found: {move_name}")


def create_move(move_name: str) -> Move:
    """
    Create a Move object directly from move name.
    This is a convenience function that combines get_move_data and Move creation.
    """
    move_data = get_move_data(move_name)
    return create_move_from_data(move_data)


def create_move_from_data(move_data: dict) -> Move:
    """Create a Move object from move data dict."""
    type_enum = getattr(Type, move_data['type'].upper(), Type.NORMAL)
    category_enum = getattr(MoveCategory, move_data['category'].upper(), MoveCategory.STATUS)

    status_enum = None
    if move_data.get('status_effect'):
        status_enum = getattr(Status, move_data['status_effect'], None)

    stat_changes = {}
    if move_data.get('stat_changes'):
        for stat_name, value in move_data['stat_changes'].items():
            stat_changes[StatType[stat_name]] = value

    return Move(
        name=move_data['name'],
        type=type_enum,
        category=category_enum,
        power=move_data.get('power') or 0,
        accuracy=move_data.get('accuracy') or 100,
        pp=move_data.get('pp') or 10,
        max_pp=move_data.get('pp') or 10,
        status_effect=status_enum,
        status_chance=move_data.get('status_chance', 0),
        stat_changes=stat_changes,
        target_self=move_data.get('target_self', False)
    )


def get_pokemon_weaknesses_resistances(types: list[str]) -> dict:
    """
    Calculate weaknesses, resistances, and immunities for a Pokemon's types.
    Uses the local TYPE_CHART from engine/type_chart.py
    """
    from engine.type_chart import TYPE_CHART

    weaknesses = set()
    resistances = set()
    immunities = set()

    # Convert type strings to Type enums
    type_enums = [getattr(Type, t.upper(), None) for t in types]
    type_enums = [t for t in type_enums if t is not None]

    # Check each attacking type
    for attacking_type in Type:
        multiplier = 1.0
        for defending_type in type_enums:
            if defending_type in TYPE_CHART.get(attacking_type, {}):
                multiplier *= TYPE_CHART[attacking_type][defending_type]

        if multiplier == 0:
            immunities.add(attacking_type.value)
        elif multiplier >= 2:
            weaknesses.add(attacking_type.value)
        elif multiplier <= 0.5:
            resistances.add(attacking_type.value)

    return {
        'weaknesses': sorted(list(weaknesses)),
        'resistances': sorted(list(resistances)),
        'immunities': sorted(list(immunities))
    }
