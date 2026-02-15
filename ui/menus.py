"""Main menu and navigation for Pokemon Gen 1 Battle Simulator"""

import curses
from typing import Optional

from settings.battle_config import (
    BattleSettings, BattleMode, MovesetMode, TeamSelectMode,
    WAITING_TIME_OPTIONS,
)
from engine.ai.difficulty import AIDifficulty
from engine.ai.trainer_class import TrainerStyle
from models.enums import BattleFormat
from models.ruleset import ALL_RULESETS
from ui.selection import init_colors, select_custom_ruleset_curses


# Display names for AI difficulty levels (Spanish UI)
AI_DIFFICULTY_NAMES = [
    "Default",         # DEFAULT — random moves
    "Fácil",           # EASY
    "Medio",           # MEDIUM
    "Competitivo",     # COMPETITIVE
    "Predictivo",      # PREDICTIVE
    "Millennium Eye",  # MILLENNIUM_EYE
]

# AIDifficulty members in UI order (must match AI_DIFFICULTY_NAMES)
_AI_DIFFICULTY_VALUES = list(AIDifficulty)

# Display names for trainer styles (Spanish UI) — TYPE_SPECIALIST excluded
TRAINER_STYLE_NAMES = [
    "Equilibrado",  # BALANCED
    "Ofensivo",     # OFFENSIVE
    "Defensivo",    # DEFENSIVE
    "Status",       # STATUS_FOCUSED
]

# TrainerStyle members in UI order (excluding TYPE_SPECIALIST)
_TRAINER_STYLE_VALUES = [
    TrainerStyle.BALANCED,
    TrainerStyle.OFFENSIVE,
    TrainerStyle.DEFENSIVE,
    TrainerStyle.STATUS_FOCUSED,
]


# =============================================================================
# Drawing helpers
# =============================================================================

def _safe_addstr(stdscr, row, col, text, *args):
    """Write text to screen with bounds checking."""
    max_y, max_x = stdscr.getmaxyx()
    if 0 <= row < max_y and 0 <= col < max_x:
        try:
            stdscr.addstr(row, col, text[:max_x - col - 1], *args)
        except curses.error:
            pass


# =============================================================================
# Main Menu
# =============================================================================

MAIN_MENU_OPTIONS = [
    ("Iniciar Batalla", "Configura y comienza una batalla Pokémon"),
    ("Modo Historia", "Próximamente..."),
    ("Salir", "Cerrar el simulador"),
]


def draw_main_menu(stdscr, selected_idx: int):
    """Render the main menu screen."""
    stdscr.clear()
    max_y, max_x = stdscr.getmaxyx()
    center_x = max_x // 2

    # Title banner
    title_lines = [
        "═══════════════════════════════════════════",
        "      POKÉMON GEN 1 BATTLE SIMULATOR       ",
        "═══════════════════════════════════════════",
    ]
    for i, line in enumerate(title_lines):
        stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
        _safe_addstr(stdscr, 2 + i, center_x - len(line) // 2, line)
        stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

    # Menu options
    for i, (label, desc) in enumerate(MAIN_MENU_OPTIONS):
        y = 8 + i * 3
        is_placeholder = (label == "Modo Historia")

        if i == selected_idx:
            stdscr.attron(curses.color_pair(1))
            _safe_addstr(stdscr, y, center_x - 20, f" ► {label} ")
            stdscr.attroff(curses.color_pair(1))
        else:
            if is_placeholder:
                stdscr.attron(curses.A_DIM)
            _safe_addstr(stdscr, y, center_x - 20, f"   {label} ")
            if is_placeholder:
                stdscr.attroff(curses.A_DIM)

        # Description line
        if is_placeholder:
            stdscr.attron(curses.A_DIM)
        _safe_addstr(stdscr, y + 1, center_x - 20, f"   {desc}")
        if is_placeholder:
            stdscr.attroff(curses.A_DIM)

    # Instructions
    _safe_addstr(stdscr, max_y - 3, center_x - 15, "↑/↓: Navegar")
    _safe_addstr(stdscr, max_y - 2, center_x - 15, "ENTER: Seleccionar")


def select_main_menu_curses(stdscr) -> Optional[int]:
    """Main menu selection. Returns 0=battle, 1=story, 2=quit, None=quit."""
    curses.curs_set(0)
    init_colors()

    selected_idx = 0

    while True:
        draw_main_menu(stdscr, selected_idx)
        stdscr.refresh()

        key = stdscr.getch()

        if key == 27:  # ESC
            return 2  # Quit
        elif key == curses.KEY_UP:
            selected_idx = max(0, selected_idx - 1)
        elif key == curses.KEY_DOWN:
            selected_idx = min(len(MAIN_MENU_OPTIONS) - 1, selected_idx + 1)
        elif key == 10:  # Enter
            if selected_idx == 1:
                # Story mode — placeholder, show message briefly
                _safe_addstr(stdscr, max_y := stdscr.getmaxyx()[0],
                             0, "", 0)  # no-op to get max_y
                max_y, max_x = stdscr.getmaxyx()
                stdscr.attron(curses.color_pair(5) | curses.A_BOLD)
                _safe_addstr(stdscr, max_y // 2, max_x // 2 - 12, "¡Próximamente...!")
                stdscr.attroff(curses.color_pair(5) | curses.A_BOLD)
                stdscr.refresh()
                curses.napms(1200)
                continue
            return selected_idx


# =============================================================================
# Start Battle Sub-menu
# =============================================================================

START_BATTLE_OPTIONS = [
    ("START NOW!", "Poke Cup 3v3, IA vs IA, equipos aleatorios"),
    ("Batalla Personalizada", "Configura todos los detalles de la batalla"),
    ("Volver", "Regresar al menú principal"),
]


def draw_start_battle_menu(stdscr, selected_idx: int):
    """Render the start battle sub-menu."""
    stdscr.clear()
    max_y, max_x = stdscr.getmaxyx()
    center_x = max_x // 2

    # Title
    title_lines = [
        "═══════════════════════════════════",
        "        INICIAR BATALLA            ",
        "═══════════════════════════════════",
    ]
    for i, line in enumerate(title_lines):
        stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
        _safe_addstr(stdscr, 2 + i, center_x - len(line) // 2, line)
        stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

    # Options
    for i, (label, desc) in enumerate(START_BATTLE_OPTIONS):
        y = 8 + i * 3

        if i == selected_idx:
            if i == 0:
                # START NOW! gets special green highlight
                stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
                _safe_addstr(stdscr, y, center_x - 20, f" ► {label} ")
                stdscr.attroff(curses.color_pair(4) | curses.A_BOLD)
            else:
                stdscr.attron(curses.color_pair(1))
                _safe_addstr(stdscr, y, center_x - 20, f" ► {label} ")
                stdscr.attroff(curses.color_pair(1))
        else:
            if i == 0:
                stdscr.attron(curses.color_pair(4))
                _safe_addstr(stdscr, y, center_x - 20, f"   {label} ")
                stdscr.attroff(curses.color_pair(4))
            else:
                _safe_addstr(stdscr, y, center_x - 20, f"   {label} ")

        _safe_addstr(stdscr, y + 1, center_x - 20, f"   {desc}")

    # Instructions
    _safe_addstr(stdscr, max_y - 3, center_x - 15, "↑/↓: Navegar")
    _safe_addstr(stdscr, max_y - 2, center_x - 15, "ENTER: Seleccionar | ESC: Volver")


def select_start_battle_curses(stdscr) -> Optional[int]:
    """Start battle sub-menu. Returns 0=quick, 1=custom, 2=back, None=back."""
    curses.curs_set(0)
    init_colors()

    selected_idx = 0

    while True:
        draw_start_battle_menu(stdscr, selected_idx)
        stdscr.refresh()

        key = stdscr.getch()

        if key == 27:  # ESC
            return 2  # Back
        elif key == curses.KEY_UP:
            selected_idx = max(0, selected_idx - 1)
        elif key == curses.KEY_DOWN:
            selected_idx = min(len(START_BATTLE_OPTIONS) - 1, selected_idx + 1)
        elif key == 10:  # Enter
            return selected_idx


# =============================================================================
# Custom Battle Configuration Form
# =============================================================================

def _build_config_fields(mode_idx: int = 0):
    """Build the field definitions for the custom battle config form.

    Args:
        mode_idx: Current mode index. 0 = IA vs IA, 1 = Jugador vs IA.
                  Controls visibility of player AI fields.
    """
    ruleset_names = [r.name for r in ALL_RULESETS] + ["Personalizado"]
    format_names = ["1v1", "3v3", "6v6"]
    mode_names = ["IA vs IA", "Jugador vs IA"]
    waiting_names = [label for _, label in WAITING_TIME_OPTIONS]
    team_select_names = ["Aleatorio", "Elegir"]
    moveset_names = [m.description for m in MovesetMode]

    # Player AI fields are only active in autobattle mode (mode_idx == 0)
    is_autobattle = (mode_idx == 0)
    player_field_type = "cycle" if is_autobattle else "placeholder"
    player_ai_options = AI_DIFFICULTY_NAMES if is_autobattle else ["N/A (Jugador)"]
    player_style_options = TRAINER_STYLE_NAMES if is_autobattle else ["N/A (Jugador)"]

    fields = [
        ("Reglas",           "ruleset_idx",       "cycle",             ruleset_names),
        ("Formato",          "format_idx",        "cycle",             format_names),
        ("Modo",             "mode_idx",          "cycle",             mode_names),
        ("IA Oponente",      "opp_ai_idx",        "cycle",             AI_DIFFICULTY_NAMES),
        ("Estilo Oponente",  "opp_style_idx",     "cycle",             TRAINER_STYLE_NAMES),
        ("IA Jugador",       "player_ai_idx",     player_field_type,   player_ai_options),
        ("Estilo Jugador",   "player_style_idx",  player_field_type,   player_style_options),
        ("Tiempo de Espera", "waiting_time_idx",  "cycle",             waiting_names),
        ("Equipo",           "team_select_idx",   "cycle",             team_select_names),
        ("Movimientos",      "moveset_idx",       "cycle",             moveset_names),
    ]
    return fields


def _default_config() -> dict:
    """Default config values for the custom battle form."""
    return {
        "ruleset_idx": 1,          # Poke Cup
        "format_idx": 1,           # 3v3
        "mode_idx": 0,             # IA vs IA
        "opp_ai_idx": 0,           # Default AI
        "opp_style_idx": 0,        # Equilibrado
        "player_ai_idx": 0,        # Default AI
        "player_style_idx": 0,     # Equilibrado
        "waiting_time_idx": 1,     # 3 seconds
        "team_select_idx": 0,      # Aleatorio
        "moveset_idx": 3,          # Smart Random
    }


def draw_custom_battle_config(stdscr, config: dict, cursor_idx: int, fields: list):
    """Render the custom battle configuration form."""
    stdscr.clear()
    max_y, max_x = stdscr.getmaxyx()
    center_x = max_x // 2

    # Title
    title_width = 40
    stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
    _safe_addstr(stdscr, 1, center_x - title_width // 2, "═" * title_width)
    _safe_addstr(stdscr, 2, center_x - 14, " BATALLA PERSONALIZADA ")
    _safe_addstr(stdscr, 3, center_x - title_width // 2, "═" * title_width)
    stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

    for i, (label, key, field_type, options) in enumerate(fields):
        y = 5 + i * 2
        if y >= max_y - 5:
            break

        is_placeholder = (field_type == "placeholder")

        # Label
        if i == cursor_idx:
            stdscr.attron(curses.color_pair(1))
            _safe_addstr(stdscr, y, center_x - 22, f" ► {label.ljust(20)} ")
            stdscr.attroff(curses.color_pair(1))
        else:
            if is_placeholder:
                stdscr.attron(curses.A_DIM)
            _safe_addstr(stdscr, y, center_x - 22, f"   {label.ljust(20)} ")
            if is_placeholder:
                stdscr.attroff(curses.A_DIM)

        # Value with arrows
        idx = config[key]
        val_str = options[idx] if idx < len(options) else "?"

        if is_placeholder:
            stdscr.attron(curses.A_DIM)
            _safe_addstr(stdscr, y, center_x + 2, f"  {val_str}  ")
            stdscr.attroff(curses.A_DIM)
        else:
            stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
            _safe_addstr(stdscr, y, center_x + 2, f"◄ {val_str:^16} ►")
            stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)

    # Confirm button
    confirm_y = 5 + len(fields) * 2 + 1
    if confirm_y < max_y - 3:
        if cursor_idx == len(fields):
            stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
            _safe_addstr(stdscr, confirm_y, center_x - 12, " ► ─── INICIAR BATALLA ─── ")
            stdscr.attroff(curses.color_pair(4) | curses.A_BOLD)
        else:
            _safe_addstr(stdscr, confirm_y, center_x - 12, "   ─── INICIAR BATALLA ─── ")

    # Instructions
    _safe_addstr(stdscr, max_y - 3, center_x - 20, "↑/↓: Navegar | ←/→: Cambiar valor")
    _safe_addstr(stdscr, max_y - 2, center_x - 20, "ENTER: Confirmar | ESC: Volver")


def _config_to_settings(config: dict, fields: list) -> Optional[BattleSettings]:
    """Convert the config form dict into a BattleSettings object."""
    # Resolve ruleset
    ruleset_idx = config["ruleset_idx"]
    rulesets_with_custom = ALL_RULESETS  # Custom handled separately
    if ruleset_idx < len(ALL_RULESETS):
        ruleset = ALL_RULESETS[ruleset_idx]
    else:
        # Custom was selected but not built yet — should have been handled
        # in the form loop. Fall back to Standard.
        from models.ruleset import STANDARD_RULES
        ruleset = STANDARD_RULES

    # Resolve battle format
    format_map = {0: BattleFormat.SINGLE, 1: BattleFormat.TRIPLE, 2: BattleFormat.FULL}
    battle_format = format_map.get(config["format_idx"], BattleFormat.TRIPLE)

    # Resolve battle mode
    mode_map = {0: BattleMode.AUTOBATTLE, 1: BattleMode.PLAYER_VS_AI}
    battle_mode = mode_map.get(config["mode_idx"], BattleMode.AUTOBATTLE)

    # Resolve waiting time
    waiting_idx = config["waiting_time_idx"]
    if waiting_idx < len(WAITING_TIME_OPTIONS):
        action_delay = WAITING_TIME_OPTIONS[waiting_idx][0]
    else:
        action_delay = 3.0

    # Resolve team selection
    team_map = {0: TeamSelectMode.RANDOM, 1: TeamSelectMode.MANUAL}
    team_select = team_map.get(config["team_select_idx"], TeamSelectMode.RANDOM)

    # Resolve moveset mode
    moveset_modes = list(MovesetMode)
    moveset_idx = config["moveset_idx"]
    moveset_mode = moveset_modes[moveset_idx] if moveset_idx < len(moveset_modes) else MovesetMode.SMART_RANDOM

    # Resolve AI difficulty and trainer style
    opp_ai_idx = config.get("opp_ai_idx", 0)
    opp_ai = _AI_DIFFICULTY_VALUES[opp_ai_idx] if opp_ai_idx < len(_AI_DIFFICULTY_VALUES) else AIDifficulty.DEFAULT

    opp_style_idx = config.get("opp_style_idx", 0)
    opp_style = _TRAINER_STYLE_VALUES[opp_style_idx] if opp_style_idx < len(_TRAINER_STYLE_VALUES) else TrainerStyle.BALANCED

    player_ai_idx = config.get("player_ai_idx", 0)
    player_ai = _AI_DIFFICULTY_VALUES[player_ai_idx] if player_ai_idx < len(_AI_DIFFICULTY_VALUES) else AIDifficulty.DEFAULT

    player_style_idx = config.get("player_style_idx", 0)
    player_style = _TRAINER_STYLE_VALUES[player_style_idx] if player_style_idx < len(_TRAINER_STYLE_VALUES) else TrainerStyle.BALANCED

    return BattleSettings(
        battle_mode=battle_mode,
        moveset_mode=moveset_mode,
        action_delay=action_delay,
        ruleset=ruleset,
        battle_format=battle_format,
        team_select_mode=team_select,
        opponent_ai_difficulty=opp_ai,
        opponent_trainer_style=opp_style,
        player_ai_difficulty=player_ai,
        player_trainer_style=player_style,
    )


def select_custom_battle_curses(stdscr) -> Optional[BattleSettings]:
    """Interactive custom battle configuration form."""
    curses.curs_set(0)
    init_colors()

    config = _default_config()
    fields = _build_config_fields(config["mode_idx"])
    total_options = len(fields) + 1  # +1 for confirm button
    cursor_idx = 0

    while True:
        draw_custom_battle_config(stdscr, config, cursor_idx, fields)
        stdscr.refresh()

        key = stdscr.getch()

        if key == 27:  # ESC
            return None
        elif key == curses.KEY_UP:
            cursor_idx = max(0, cursor_idx - 1)
        elif key == curses.KEY_DOWN:
            cursor_idx = min(total_options - 1, cursor_idx + 1)
        elif key in (curses.KEY_LEFT, curses.KEY_RIGHT) and cursor_idx < len(fields):
            label, field_key, field_type, options = fields[cursor_idx]
            if field_type == "cycle":
                delta = 1 if key == curses.KEY_RIGHT else -1
                config[field_key] = (config[field_key] + delta) % len(options)

                # When mode changes, rebuild fields (player AI visibility toggles)
                if field_key == "mode_idx":
                    # Reset player AI indices when switching to Jugador vs IA
                    if config["mode_idx"] == 1:  # Jugador vs IA
                        config["player_ai_idx"] = 0
                        config["player_style_idx"] = 0
                    fields = _build_config_fields(config["mode_idx"])
                    total_options = len(fields) + 1
                    cursor_idx = min(cursor_idx, total_options - 1)

                # If ruleset is "Personalizado", open custom ruleset editor
                if field_key == "ruleset_idx" and config[field_key] == len(ALL_RULESETS):
                    custom = select_custom_ruleset_curses(stdscr)
                    if custom is not None:
                        # Insert custom ruleset temporarily
                        ALL_RULESETS.append(custom)
                        config["ruleset_idx"] = len(ALL_RULESETS) - 1
                        # Rebuild fields to pick up new name
                        fields = _build_config_fields(config["mode_idx"])
                    else:
                        # Cancelled — revert to previous
                        config["ruleset_idx"] = (config["ruleset_idx"] - delta) % len(
                            fields[cursor_idx][3])
        elif key == 10:  # Enter
            if cursor_idx == len(fields):
                return _config_to_settings(config, fields)


# =============================================================================
# Public API — main_menu()
# =============================================================================

def main_menu() -> Optional[BattleSettings]:
    """
    Run the full main menu flow.

    Returns:
        BattleSettings if the user configured and confirmed a battle,
        or None if the user chose to quit.
    """
    while True:
        choice = curses.wrapper(select_main_menu_curses)

        if choice is None or choice == 2:
            # Quit
            return None

        if choice == 0:
            # Start Battle sub-menu
            while True:
                sub_choice = curses.wrapper(select_start_battle_curses)

                if sub_choice is None or sub_choice == 2:
                    # Back to main menu
                    break

                if sub_choice == 0:
                    # START NOW! — instant battle
                    return BattleSettings.quick_start()

                if sub_choice == 1:
                    # Custom battle config
                    settings = curses.wrapper(select_custom_battle_curses)
                    if settings is not None:
                        return settings
                    # If cancelled, stay in sub-menu
