"""Utilidades UI visuales"""

from models.enums import StatType

class Colors:
    """Codigios de color ANSI"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

def get_hp_color(hp_percentage: float) -> str:
    """Seleccion de color basado en HP restante"""
    if hp_percentage > 50:
        return Colors.GREEN
    elif hp_percentage > 20:
        return Colors.YELLOW
    else:
        return Colors.RED

def create_health_bar(current_hp: int, max_hp: int, bar_length: int = 20) -> str:
    """
    Crear una barra visual

    Args:
        current_hp: HP actual
        max_hp: HP maximo
        bar_length: Tamano de la barra basado en valores (default 20)

    Returns:
        Barra coloreada basada en valores

    Example:
        >>> create_health_bar(80, 100, 20)
        '[████████████████░░░░] 80/100 HP'
    """
    if max_hp <= 0:
        return f"[{'░' * bar_length}] 0/0 HP"

    hp_percentage = (current_hp / max_hp) * 100
    filled_length = int((current_hp / max_hp) * bar_length)

    # Create bar components
    filled_bar = '█' * filled_length
    empty_bar = '░' * (bar_length - filled_length)

    # Get appropriate color
    color = get_hp_color(hp_percentage)

    # Format HP values
    hp_text = f"{current_hp}/{max_hp} HP"

    # Combine with color
    bar = f"{color}[{filled_bar}{empty_bar}]{Colors.RESET} {hp_text}"

    return bar

def get_stat_stage_arrow(stage: int) -> str:
    """
    Returns arrow symbols for stat stage display.

    Args:
        stage: Stat stage from -6 to +6

    Returns:
        Arrow symbol(s) representing the stat change
    """
    if stage >= 3:
        return "↑↑↑"
    elif stage == 2:
        return "↑↑"
    elif stage == 1:
        return "↑"
    elif stage == 0:
        return "↔"
    elif stage == -1:
        return "↓"
    elif stage == -2:
        return "↓↓"
    else:  # -3 or lower
        return "↓↓↓"

def get_stat_stage_color(stage: int) -> str:
    """Returns color for stat stage display"""
    if stage > 0:
        return Colors.GREEN
    elif stage < 0:
        return Colors.RED
    else:
        return Colors.DIM

def format_stat_stages(pokemon) -> str:
    """
    Formats stat stage changes for display.

    Args:
        pokemon: Pokemon object with stat_stages attribute

    Returns:
        Formatted string showing stat modifications with arrows

    Example:
        >>> format_stat_stages(pikachu)
        'ATK ↑↑ | DEF ↔ | SPD ↑'
    """
    # Map StatType to short names
    stat_names = {
        StatType.ATTACK: "ATK",
        StatType.DEFENSE: "DEF",
        StatType.SPECIAL: "SPC",
        StatType.SPEED: "SPD",
        StatType.ACCURACY: "ACC",
        StatType.EVASION: "EVA"
    }

    parts = []
    for stat_type in [StatType.ATTACK, StatType.DEFENSE, StatType.SPECIAL, StatType.SPEED]:
        stage = pokemon.stat_stages[stat_type]
        if stage != 0:  # Only show modified stats
            arrow = get_stat_stage_arrow(stage)
            color = get_stat_stage_color(stage)
            stat_name = stat_names[stat_type]
            parts.append(f"{color}{stat_name} {arrow}{Colors.RESET}")

    # Also show accuracy/evasion if modified
    if pokemon.stat_stages[StatType.ACCURACY] != 0:
        stage = pokemon.stat_stages[StatType.ACCURACY]
        arrow = get_stat_stage_arrow(stage)
        color = get_stat_stage_color(stage)
        parts.append(f"{color}ACC {arrow}{Colors.RESET}")

    if pokemon.stat_stages[StatType.EVASION] != 0:
        stage = pokemon.stat_stages[StatType.EVASION]
        arrow = get_stat_stage_arrow(stage)
        color = get_stat_stage_color(stage)
        parts.append(f"{color}EVA {arrow}{Colors.RESET}")

    if not parts:
        return ""

    return " | ".join(parts)

def format_pokemon_status(pokemon) -> str:
    """
    Formats a Pokemon's name and health bar for display.

    Args:
        pokemon: Pokemon object with current_hp, max_hp, and name attributes

    Returns:
        Formatted string with name and colored health bar

    Example:
        >>> format_pokemon_status(pikachu)
        'Pikachu [████████████████░░░░] 80/100 HP'
    """
    health_bar = create_health_bar(pokemon.current_hp, pokemon.max_hp)
    stat_display = format_stat_stages(pokemon)

    if stat_display:
        return f"{Colors.BOLD}{pokemon.name}{Colors.RESET} {health_bar}\n  {stat_display}"
    else:
        return f"{Colors.BOLD}{pokemon.name}{Colors.RESET} {health_bar}"
