from models.enums import Type

TYPE_CHART = {
    Type.NORMAL: {Type.ROCK: 0.5, Type.GHOST: 0},
    Type.FIRE: {Type.FIRE: 0.5, Type.WATER: 0.5, Type.GRASS: 2, Type.ICE: 2, Type.BUG: 2, Type.ROCK: 0.5, Type.DRAGON: 0.5},
    Type.WATER: {Type.FIRE: 2, Type.WATER: 0.5, Type.GRASS: 0.5, Type.GROUND: 2, Type.ROCK: 2, Type.DRAGON: 0.5},
    Type.ELECTRIC: {Type.WATER: 2, Type.ELECTRIC: 0.5, Type.GRASS: 0.5, Type.GROUND: 0, Type.FLYING: 2, Type.DRAGON: 0.5},
    Type.GRASS: {Type.FIRE: 0.5, Type.WATER: 2, Type.GRASS: 0.5, Type.POISON: 0.5, Type.GROUND: 2, Type.FLYING: 0.5, Type.BUG: 0.5, Type.ROCK: 2, Type.DRAGON: 0.5},
    Type.ICE: {Type.WATER: 0.5, Type.GRASS: 2, Type.ICE: 0.5, Type.GROUND: 2, Type.FLYING: 2, Type.DRAGON: 2},
    Type.FIGHTING: {Type.NORMAL: 2, Type.ICE: 2, Type.POISON: 0.5, Type.FLYING: 0.5, Type.PSYCHIC: 0.5, Type.BUG: 0.5, Type.ROCK: 2, Type.GHOST: 0},
    Type.POISON: {Type.GRASS: 2, Type.POISON: 0.5, Type.GROUND: 0.5, Type.BUG: 2, Type.ROCK: 0.5, Type.GHOST: 0.5},
    Type.GROUND: {Type.FIRE: 2, Type.ELECTRIC: 2, Type.GRASS: 0.5, Type.POISON: 2, Type.FLYING: 0, Type.BUG: 0.5, Type.ROCK: 2},
    Type.FLYING: {Type.ELECTRIC: 0.5, Type.GRASS: 2, Type.FIGHTING: 2, Type.BUG: 2, Type.ROCK: 0.5},
    Type.PSYCHIC: {Type.FIGHTING: 2, Type.POISON: 2, Type.PSYCHIC: 0.5},
    Type.BUG: {Type.FIRE: 0.5, Type.GRASS: 2, Type.FIGHTING: 0.5, Type.POISON: 2, Type.FLYING: 0.5, Type.PSYCHIC: 2, Type.GHOST: 0.5},
    Type.ROCK: {Type.FIRE: 2, Type.ICE: 2, Type.FIGHTING: 0.5, Type.GROUND: 0.5, Type.FLYING: 2, Type.BUG: 2},
    Type.GHOST: {Type.NORMAL: 0, Type.PSYCHIC: 0, Type.GHOST: 2},
    Type.DRAGON: {Type.DRAGON: 2},
}

def get_effectiveness(move_type: Type, target_types: list[Type]) -> float:
    """Calcula el multiplicador de efectividad del tipo"""
    multiplier = 1.0
    chart = TYPE_CHART.get(move_type, {})
    for t_type in target_types:
        multiplier *= chart.get(t_type, 1.0)
    return multiplier

