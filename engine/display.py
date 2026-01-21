"""Utilidades UI visuales"""

from models.enums import StatType, Type, Status

class Colors:
    """Codigios de color ANSI"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'
    BLACK = '\033[30m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    # Background colors for type badges
    BG_RED = '\033[41m'
    BG_BLUE = '\033[44m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'
    BG_BLACK = '\033[40m'
    # Extended colors (256-color mode)
    ORANGE = '\033[38;5;208m'
    BG_ORANGE = '\033[48;5;208m'
    BROWN = '\033[38;5;94m'
    BG_BROWN = '\033[48;5;94m'
    PINK = '\033[38;5;213m'
    BG_PINK = '\033[48;5;213m'
    PURPLE = '\033[38;5;129m'
    BG_PURPLE = '\033[48;5;129m'
    GRAY = '\033[38;5;245m'
    BG_GRAY = '\033[48;5;245m'
    BG_LIGHT_BLUE = '\033[48;5;117m'
    BG_DARK_PURPLE = '\033[48;5;54m'
    BG_LIME = '\033[48;5;118m'
    BG_DARK_BROWN = '\033[48;5;52m'
    BG_LAVENDER = '\033[48;5;183m'


# Type color mapping for badges
TYPE_COLORS = {
    Type.NORMAL: (Colors.BG_GRAY, Colors.WHITE),
    Type.FIRE: (Colors.BG_RED, Colors.WHITE),
    Type.WATER: (Colors.BG_BLUE, Colors.WHITE),
    Type.ELECTRIC: (Colors.BG_YELLOW, Colors.BLACK),
    Type.GRASS: (Colors.BG_GREEN, Colors.WHITE),
    Type.ICE: (Colors.BG_CYAN, Colors.BLACK),
    Type.FIGHTING: (Colors.BG_DARK_BROWN, Colors.WHITE),
    Type.POISON: (Colors.BG_PURPLE, Colors.WHITE),
    Type.GROUND: (Colors.BG_BROWN, Colors.WHITE),
    Type.FLYING: (Colors.BG_LIGHT_BLUE, Colors.BLACK),
    Type.PSYCHIC: (Colors.BG_PINK, Colors.BLACK),
    Type.BUG: (Colors.BG_LIME, Colors.BLACK),
    Type.ROCK: (Colors.BG_BROWN, Colors.WHITE),
    Type.GHOST: (Colors.BG_DARK_PURPLE, Colors.WHITE),
    Type.DRAGON: (Colors.BG_PURPLE, Colors.WHITE),
}

# Status ailment colors and symbols
STATUS_DISPLAY = {
    Status.NONE: None,
    Status.BURN: (Colors.RED, "BRN"),
    Status.FREEZE: (Colors.CYAN, "FRZ"),
    Status.PARALYSIS: (Colors.YELLOW, "PAR"),
    Status.POISON: (Colors.MAGENTA, "PSN"),
    Status.SLEEP: (Colors.GRAY, "SLP"),
    Status.CONFUSION: (Colors.MAGENTA, "CNF"),
}

def format_type_badge(pokemon_type: Type) -> str:
    """
    Creates a colored badge for a Pokemon type.

    Args:
        pokemon_type: The Type enum value

    Returns:
        Colored badge string like [FIRE] or [WATER]
    """
    bg_color, fg_color = TYPE_COLORS.get(pokemon_type, (Colors.BG_GRAY, Colors.WHITE))
    type_name = pokemon_type.value[:3].upper()  # Shortened: FIR, WAT, ELE, etc.
    return f"{bg_color}{fg_color}{type_name}{Colors.RESET}"


def format_type_badges(pokemon) -> str:
    """
    Creates colored type badges for a Pokemon.

    Args:
        pokemon: Pokemon object with types attribute

    Returns:
        String with colored type badges like [FIR][FLY]
    """
    badges = [format_type_badge(t) for t in pokemon.types]
    return "".join(badges)


# Foreground type colors for move names
TYPE_FG_COLORS = {
    Type.NORMAL: Colors.WHITE,
    Type.FIRE: Colors.RED,
    Type.WATER: Colors.BLUE,
    Type.ELECTRIC: Colors.YELLOW,
    Type.GRASS: Colors.GREEN,
    Type.ICE: Colors.CYAN,
    Type.FIGHTING: Colors.BROWN,
    Type.POISON: Colors.PURPLE,
    Type.GROUND: Colors.BROWN,
    Type.FLYING: Colors.CYAN,
    Type.PSYCHIC: Colors.PINK,
    Type.BUG: Colors.GREEN,
    Type.ROCK: Colors.BROWN,
    Type.GHOST: Colors.PURPLE,
    Type.DRAGON: Colors.PURPLE,
}


def format_move_name(move) -> str:
    """
    Formats a move name with its type color.

    Args:
        move: Move object with name and type attributes

    Returns:
        Colored move name string
    """
    color = TYPE_FG_COLORS.get(move.type, Colors.WHITE)
    return f"{Colors.BOLD}{color}{move.name}{Colors.RESET}"


def format_status_ailment(pokemon) -> str:
    """
    Creates a colored status ailment indicator.

    Args:
        pokemon: Pokemon object with status attribute

    Returns:
        Colored status string like [PAR] or empty string if no status
    """
    status_info = STATUS_DISPLAY.get(pokemon.status)
    if status_info is None:
        # Check for confusion (it's tracked separately)
        if hasattr(pokemon, 'confusion_turns') and pokemon.confusion_turns > 0:
            color, text = STATUS_DISPLAY[Status.CONFUSION]
            return f" {color}[{text}]{Colors.RESET}"
        return ""

    color, text = status_info
    result = f" {color}[{text}]{Colors.RESET}"

    # Also show confusion if present alongside another status
    if hasattr(pokemon, 'confusion_turns') and pokemon.confusion_turns > 0:
        cnf_color, cnf_text = STATUS_DISPLAY[Status.CONFUSION]
        result += f" {cnf_color}[{cnf_text}]{Colors.RESET}"

    return result


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
    Formats a Pokemon's full status display including name, types, HP, status, and stat stages.

    Args:
        pokemon: Pokemon object with name, types, current_hp, max_hp, status, and stat_stages

    Returns:
        Formatted string with all Pokemon status info

    Example:
        >>> format_pokemon_status(pikachu)
        'Pikachu [ELE] [████████████████░░░░] 80/100 HP [PAR]'
        '  ATK ↑↑ | SPD ↓'
    """
    # Type badges
    type_badges = format_type_badges(pokemon)

    # Health bar
    health_bar = create_health_bar(pokemon.current_hp, pokemon.max_hp)

    # Status ailment
    status_display = format_status_ailment(pokemon)

    # Stat stages
    stat_display = format_stat_stages(pokemon)

    # Build the display
    line1 = f"{Colors.BOLD}{pokemon.name}{Colors.RESET} {type_badges} {health_bar}{status_display}"

    if stat_display:
        return f"{line1}\n  {stat_display}"
    else:
        return line1
