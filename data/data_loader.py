"""
Local data loader for Pokemon Gen 1 data.
Replaces PokeAPI calls with local JSON file lookups.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from models.enums import Type, Status, MoveCategory, StatType
from models.stats import Stats
from models.move import Move

DATA_DIR = Path(__file__).parent
logger = logging.getLogger(__name__)

# Cache loaded data
_pokemon_cache: Optional[dict] = None
_moves_cache: Optional[dict] = None
_learnsets_cache: Optional[dict] = None
_presets_cache: Optional[dict] = None


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


def _get_presets_data() -> dict:
    """Load and cache preset_movesets.json."""
    global _presets_cache
    if _presets_cache is None:
        try:
            _presets_cache = _load_json('preset_movesets.json')
        except FileNotFoundError:
            logger.warning("preset_movesets.json not found, using empty presets")
            _presets_cache = {}
    return _presets_cache


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


# =============================================================================
# Moveset Selection Functions
# =============================================================================

def get_preset_moveset(pokemon_name: str, variant: str = "competitive") -> Optional[list[str]]:
    """
    Get a preset moveset for a Pokemon.

    Args:
        pokemon_name: Name of the Pokemon
        variant: Which preset variant ("competitive" or "alternative")

    Returns:
        List of move names, or None if no preset exists
    """
    presets = _get_presets_data()
    name = pokemon_name.lower()

    if name not in presets:
        return None

    pokemon_presets = presets[name]
    if variant in pokemon_presets:
        return pokemon_presets[variant]
    elif "competitive" in pokemon_presets:
        return pokemon_presets["competitive"]

    return None


def get_random_moveset(pokemon_name: str, count: int = 4) -> list[str]:
    """
    Get a random moveset from available moves.

    Args:
        pokemon_name: Name of the Pokemon
        count: Number of moves to select (default 4)

    Returns:
        List of move names
    """
    import random
    available_moves = get_pokemon_moves_gen1(pokemon_name)
    return random.sample(available_moves, min(count, len(available_moves)))


def get_smart_random_moveset(pokemon_name: str, count: int = 4) -> list[str]:
    """
    Get a smart random moveset that ensures variety:
    - At least one STAB move if available
    - Mix of damaging and status moves
    - Avoids duplicate types where possible

    Args:
        pokemon_name: Name of the Pokemon
        count: Number of moves to select (default 4)

    Returns:
        List of move names
    """
    import random

    available_moves = get_pokemon_moves_gen1(pokemon_name)
    if len(available_moves) <= count:
        return available_moves

    # Get Pokemon types for STAB check
    try:
        poke_data = get_pokemon_data(pokemon_name)
        pokemon_types = [t.lower() for t in poke_data['types']]
    except ValueError:
        pokemon_types = []

    # Categorize available moves
    stab_damaging = []
    other_damaging = []
    status_moves = []

    for move_name in available_moves:
        try:
            move_data = get_move_data(move_name)
            move_type = move_data['type'].lower()
            category = move_data['category'].lower()
            power = move_data.get('power') or 0

            if category == 'status' or power == 0:
                status_moves.append(move_name)
            elif move_type in pokemon_types:
                stab_damaging.append(move_name)
            else:
                other_damaging.append(move_name)
        except ValueError:
            # If move data not found, add to other
            other_damaging.append(move_name)

    selected = []
    types_used = set()

    # 1. Pick at least one STAB move if available
    if stab_damaging:
        move = random.choice(stab_damaging)
        selected.append(move)
        stab_damaging.remove(move)
        try:
            types_used.add(get_move_data(move)['type'].lower())
        except ValueError:
            pass

    # 2. Pick 1-2 status moves for variety (if available)
    status_count = min(random.randint(1, 2), len(status_moves), count - len(selected) - 1)
    if status_count > 0:
        status_picks = random.sample(status_moves, status_count)
        selected.extend(status_picks)
        for m in status_picks:
            status_moves.remove(m)

    # 3. Fill remaining slots with damaging moves, preferring type variety
    remaining_damaging = stab_damaging + other_damaging
    random.shuffle(remaining_damaging)

    for move_name in remaining_damaging:
        if len(selected) >= count:
            break
        try:
            move_type = get_move_data(move_name)['type'].lower()
            # Prefer moves of different types
            if move_type not in types_used or len(selected) >= count - 1:
                selected.append(move_name)
                types_used.add(move_type)
        except ValueError:
            selected.append(move_name)

    # If still need more, add from status or any remaining
    remaining = [m for m in available_moves if m not in selected]
    while len(selected) < count and remaining:
        move = random.choice(remaining)
        selected.append(move)
        remaining.remove(move)

    return selected[:count]


def get_moveset_for_pokemon(pokemon_name: str, mode: str = "random") -> list[str]:
    """
    Get a moveset for a Pokemon based on the selection mode.

    Args:
        pokemon_name: Name of the Pokemon
        mode: One of "random", "preset", "smart_random"

    Returns:
        List of move names
    """
    if mode == "preset":
        preset = get_preset_moveset(pokemon_name)
        if preset:
            # Validate all moves exist in Pokemon's learnset
            available = get_pokemon_moves_gen1(pokemon_name)
            valid_moves = [m for m in preset if m in available]
            if len(valid_moves) >= 4:
                return valid_moves[:4]
        # Fall back to smart random if no valid preset
        return get_smart_random_moveset(pokemon_name)

    elif mode == "smart_random":
        return get_smart_random_moveset(pokemon_name)

    else:  # random
        return get_random_moveset(pokemon_name)


# =============================================================================
# Pokemon Factory Function
# =============================================================================

def create_pokemon_with_ruleset(
    name: str,
    moves: list,
    ruleset=None,
    level: int = None,
    ivs=None,
) -> 'Pokemon':
    """
    Create a Pokemon respecting ruleset rules.

    This factory function creates a Pokemon with stats calculated according
    to Gen 1 formulas, respecting any ruleset constraints.

    Args:
        name: Pokemon name (e.g., "Pikachu")
        moves: List of Move objects
        ruleset: Optional Ruleset for validation and defaults.
                 If None, uses STANDARD_RULES.
        level: Override level (otherwise uses ruleset default)
        ivs: Override IVs (otherwise uses ruleset setting - perfect or random)

    Returns:
        Configured Pokemon instance

    Example:
        from data.data_loader import create_pokemon_with_ruleset, create_move
        from models.ruleset import LITTLE_CUP_RULES

        moves = [create_move('tackle'), create_move('thunder-wave')]
        pikachu = create_pokemon_with_ruleset('pikachu', moves, LITTLE_CUP_RULES)
        # Creates a level 5 Pikachu with Little Cup stats
    """
    from models.pokemon import Pokemon
    from models.ivs import IVs

    # Import ruleset lazily to avoid circular imports
    if ruleset is None:
        from models.ruleset import STANDARD_RULES
        ruleset = STANDARD_RULES

    # Get Pokemon data
    poke_data = get_pokemon_data(name)

    # Determine level
    if level is None:
        level = ruleset.default_level

    # Determine IVs based on ruleset
    if ivs is None:
        ivs = IVs.perfect() if ruleset.perfect_ivs else IVs.random()

    # Determine EVs based on ruleset
    if ruleset.max_evs:
        evs = None  # None means use max EVs (default)
    else:
        evs = {'hp': 0, 'attack': 0, 'defense': 0, 'special': 0, 'speed': 0}

    # Create base stats from data
    base_stats = Stats(
        hp=poke_data['stats'].get('hp', 100),
        attack=poke_data['stats'].get('attack', 50),
        defense=poke_data['stats'].get('defense', 50),
        special=poke_data['stats'].get('special-attack', 50),
        speed=poke_data['stats'].get('speed', 50)
    )

    # Parse types
    types = [getattr(Type, t.upper(), Type.NORMAL) for t in poke_data['types']]

    return Pokemon(
        name=poke_data['name'],
        types=types,
        stats=base_stats,
        moves=moves,
        level=level,
        ivs=ivs,
        evs=evs,
        use_calculated_stats=ruleset.use_calculated_stats
    )
