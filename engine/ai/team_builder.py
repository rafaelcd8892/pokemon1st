"""Profile-biased team building.

Builds a team of Pokemon with movesets biased by a TrainerProfile:

- **Offensive** profiles prefer high-Attack/Speed Pokemon and high-power moves.
- **Defensive** profiles prefer bulky Pokemon with recovery and screens.
- **Status-focused** profiles ensure at least one status move per Pokemon.
- **Type specialists** restrict the pool to Pokemon matching their types.
- **Balanced** profiles use the standard unbiased `create_team_with_moveset`
  selection (a thin wrapper over data_loader).

The team builder is intentionally simple — it does weighted sampling of
Pokemon and post-filters movesets.  It reuses existing data_loader
functions for Pokemon creation and move lookup.
"""

from typing import Optional

from models.team import Team
from models.enums import Type
from engine.rng import get_rng, RNGContext
from engine.ai.trainer_class import TrainerProfile, TrainerStyle
from data.data_loader import (
    get_kanto_pokemon_list,
    get_pokemon_data,
    get_move_data,
    get_moveset_for_pokemon,
    create_move,
    create_pokemon_with_ruleset,
)
from ui.selection import filter_pokemon_by_ruleset


def build_team_for_profile(
    size: int,
    trainer_name: str,
    moveset_mode: str,
    profile: TrainerProfile,
    ruleset=None,
) -> Team:
    """Build a team biased by the given TrainerProfile.

    Args:
        size: Number of Pokemon on the team.
        trainer_name: Display name for the team.
        moveset_mode: One of "random", "preset", "smart_random".
        profile: TrainerProfile controlling selection biases.
        ruleset: Optional Ruleset for level/restriction enforcement.

    Returns:
        A ready-to-battle Team instance.
    """
    pool = _get_pokemon_pool(profile, ruleset)
    if not pool:
        pool = get_kanto_pokemon_list()

    selected_names = _weighted_pokemon_selection(pool, size, profile)

    pokemon_list = []
    for name in selected_names:
        moves_selected = _biased_moveset(name, moveset_mode, profile)
        moves = [create_move(m) for m in moves_selected]
        pokemon = create_pokemon_with_ruleset(name, moves, ruleset=ruleset)
        pokemon_list.append(pokemon)

    return Team(pokemon_list, trainer_name)


# ---------------------------------------------------------------------------
# Pokemon pool filtering
# ---------------------------------------------------------------------------

def _get_pokemon_pool(profile: TrainerProfile, ruleset=None) -> list[str]:
    """Return the candidate Pokemon list, filtered by ruleset and type."""
    pool = get_kanto_pokemon_list()

    if ruleset is not None:
        pool = filter_pokemon_by_ruleset(pool, ruleset)

    # Type specialist: keep only Pokemon that have at least one matching type
    if profile.specialist_types:
        specialist_names = set(t.value.lower() for t in profile.specialist_types)
        filtered = []
        for name in pool:
            try:
                poke_data = get_pokemon_data(name)
                poke_types = {t.lower() for t in poke_data['types']}
                if poke_types & specialist_names:
                    filtered.append(name)
            except ValueError:
                continue
        if filtered:
            pool = filtered

    return pool


# ---------------------------------------------------------------------------
# Weighted Pokemon selection
# ---------------------------------------------------------------------------

def _weighted_pokemon_selection(
    pool: list[str],
    size: int,
    profile: TrainerProfile,
) -> list[str]:
    """Select Pokemon from pool with weights derived from profile.

    Each candidate gets a weight based on how well its base stats align
    with the profile's stat weights.  Higher weight → more likely to be
    picked.  Selection is without replacement.
    """
    rng = get_rng()

    if len(pool) <= size:
        return list(pool)

    weights = []
    for name in pool:
        w = _score_pokemon_for_profile(name, profile)
        weights.append(w)

    # Weighted sampling without replacement
    selected: list[str] = []
    remaining_indices = list(range(len(pool)))
    remaining_weights = list(weights)

    for _ in range(size):
        if not remaining_indices:
            break
        idx = _weighted_choice(remaining_indices, remaining_weights, rng)
        selected.append(pool[idx])
        # Remove chosen entry
        pos = remaining_indices.index(idx)
        remaining_indices.pop(pos)
        remaining_weights.pop(pos)

    return selected


def _score_pokemon_for_profile(name: str, profile: TrainerProfile) -> float:
    """Score a Pokemon based on how well it matches the profile preferences."""
    try:
        data = get_pokemon_data(name)
    except ValueError:
        return 1.0

    stats = data['stats']
    attack = stats.get('attack', 50)
    defense = stats.get('defense', 50)
    speed = stats.get('speed', 50)
    hp = stats.get('hp', 50)

    # Weighted sum of stats based on profile preferences.
    # Defense weight also accounts for HP (bulk = defense + HP).
    score = (
        attack * profile.attack_weight
        + (defense + hp * 0.5) * profile.defense_weight
        + speed * profile.speed_weight
    )

    # Normalize so balanced profile (all 1.0) gives roughly base stat total
    return max(score, 1.0)


def _weighted_choice(indices: list[int], weights: list[float], rng) -> int:
    """Pick one index with probability proportional to weight."""
    total = sum(weights)
    if total <= 0:
        return rng.choice(indices, RNGContext.TEAM_GENERATION)

    threshold = rng.random(RNGContext.TEAM_GENERATION) * total
    cumulative = 0.0
    for i, w in enumerate(weights):
        cumulative += w
        if cumulative >= threshold:
            return indices[i]
    return indices[-1]


# ---------------------------------------------------------------------------
# Moveset biasing
# ---------------------------------------------------------------------------

def _biased_moveset(
    pokemon_name: str,
    base_mode: str,
    profile: TrainerProfile,
    count: int = 4,
) -> list[str]:
    """Get a moveset for a Pokemon, biased by trainer profile.

    Strategy:
    1. Get a base moveset using the standard mode.
    2. If the profile has strong preferences, post-filter or augment.
    """
    from engine.move_effects import RECOVERY_MOVES, SCREEN_MOVES
    from data.data_loader import get_pokemon_moves_gen1

    rng = get_rng()

    # Start with the standard moveset selection
    base_moves = get_moveset_for_pokemon(pokemon_name, base_mode)

    # Balanced profile: no bias, return as-is
    if profile.style == TrainerStyle.BALANCED:
        return base_moves

    # Get the full move pool for potential substitutions
    all_available = get_pokemon_moves_gen1(pokemon_name)
    if len(all_available) <= count:
        return base_moves  # Can't be picky with a tiny pool

    # Categorize available moves
    damaging = []
    status = []
    recovery_or_screen = []
    high_power = []

    for move_name in all_available:
        try:
            mdata = get_move_data(move_name)
            power = mdata.get('power') or 0
            category = mdata['category'].lower()

            # Normalize name for set comparison
            display_name = mdata['name']

            if category == 'status' or power == 0:
                if display_name in RECOVERY_MOVES or display_name in SCREEN_MOVES:
                    recovery_or_screen.append(move_name)
                else:
                    status.append(move_name)
            else:
                damaging.append(move_name)
                if power >= 80:
                    high_power.append(move_name)
        except ValueError:
            continue

    result = list(base_moves)

    if profile.style == TrainerStyle.OFFENSIVE:
        result = _bias_offensive(result, damaging, high_power, status, count, rng)
    elif profile.style == TrainerStyle.DEFENSIVE:
        result = _bias_defensive(result, recovery_or_screen, status, count, rng)
    elif profile.style == TrainerStyle.STATUS_FOCUSED:
        result = _bias_status(result, status, recovery_or_screen, count, rng)

    return result[:count]


def _bias_offensive(
    base: list[str],
    damaging: list[str],
    high_power: list[str],
    status: list[str],
    count: int,
    rng,
) -> list[str]:
    """Offensive bias: replace status moves with high-power attacks."""
    result = []
    used = set()

    # Keep damaging moves from base
    for m in base:
        try:
            mdata = get_move_data(m)
            power = mdata.get('power') or 0
            if power > 0:
                result.append(m)
                used.add(m)
        except ValueError:
            result.append(m)
            used.add(m)

    # Fill with high-power moves
    candidates = [m for m in high_power if m not in used]
    rng.shuffle(candidates, RNGContext.TEAM_GENERATION)
    for m in candidates:
        if len(result) >= count:
            break
        result.append(m)
        used.add(m)

    # Still need more? Use any remaining damaging moves
    candidates = [m for m in damaging if m not in used]
    rng.shuffle(candidates, RNGContext.TEAM_GENERATION)
    for m in candidates:
        if len(result) >= count:
            break
        result.append(m)

    return result


def _bias_defensive(
    base: list[str],
    recovery_or_screen: list[str],
    status: list[str],
    count: int,
    rng,
) -> list[str]:
    """Defensive bias: ensure at least one recovery/screen move."""
    result = list(base)
    used = set(result)

    # Check if base already has recovery/screen
    has_defensive = any(m in recovery_or_screen for m in result)

    if not has_defensive and recovery_or_screen:
        # Replace the weakest (last) move with a recovery/screen move
        available = [m for m in recovery_or_screen if m not in used]
        if available:
            pick = rng.choice(available, RNGContext.TEAM_GENERATION)
            if len(result) >= count:
                result[-1] = pick
            else:
                result.append(pick)

    return result


def _bias_status(
    base: list[str],
    status: list[str],
    recovery_or_screen: list[str],
    count: int,
    rng,
) -> list[str]:
    """Status bias: ensure at least 2 status/support moves."""
    result = list(base)
    used = set(result)

    # Count existing status moves
    status_count = 0
    for m in result:
        try:
            mdata = get_move_data(m)
            power = mdata.get('power') or 0
            if power == 0:
                status_count += 1
        except ValueError:
            pass

    # Need at least 2 status/support moves
    target = 2
    all_support = status + recovery_or_screen
    available = [m for m in all_support if m not in used]
    rng.shuffle(available, RNGContext.TEAM_GENERATION)

    while status_count < target and available:
        pick = available.pop(0)
        if len(result) >= count:
            # Replace last damaging move
            for i in range(len(result) - 1, -1, -1):
                try:
                    mdata = get_move_data(result[i])
                    if (mdata.get('power') or 0) > 0:
                        result[i] = pick
                        status_count += 1
                        break
                except ValueError:
                    continue
        else:
            result.append(pick)
            status_count += 1

    return result
