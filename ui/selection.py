"""Curses-based interactive selection UI for Pokemon and moves"""

import curses
from typing import Optional
from data.data_loader import (
    get_pokemon_data,
    get_kanto_pokemon_list,
    get_pokemon_moves_gen1,
    get_pokemon_moves_with_source,
    get_pokemon_weaknesses_resistances,
    create_move,
    get_moveset_for_pokemon
)
from models.enums import Type, BattleFormat
from models.stats import Stats
from models.pokemon import Pokemon
from models.team import Team
from settings.battle_config import BattleMode, MovesetMode, BattleSettings


# Type color pairs for curses (foreground colors)
TYPE_COLORS = {
    'normal': curses.COLOR_WHITE,
    'fire': curses.COLOR_RED,
    'water': curses.COLOR_BLUE,
    'electric': curses.COLOR_YELLOW,
    'grass': curses.COLOR_GREEN,
    'ice': curses.COLOR_CYAN,
    'fighting': curses.COLOR_RED,
    'poison': curses.COLOR_MAGENTA,
    'ground': curses.COLOR_YELLOW,
    'flying': curses.COLOR_CYAN,
    'psychic': curses.COLOR_MAGENTA,
    'bug': curses.COLOR_GREEN,
    'rock': curses.COLOR_YELLOW,
    'ghost': curses.COLOR_MAGENTA,
    'dragon': curses.COLOR_MAGENTA,
}


def init_colors():
    """Initialize curses color pairs"""
    curses.start_color()
    curses.use_default_colors()

    # Color pair 1: Selected item (black on white)
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    # Color pair 2: Title (cyan)
    curses.init_pair(2, curses.COLOR_CYAN, -1)
    # Color pair 3: Stats header (yellow)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    # Color pair 4: HP bar green
    curses.init_pair(4, curses.COLOR_GREEN, -1)
    # Color pair 5: HP bar yellow
    curses.init_pair(5, curses.COLOR_YELLOW, -1)
    # Color pair 6: HP bar red
    curses.init_pair(6, curses.COLOR_RED, -1)
    # Type colors (pairs 10-25)
    type_list = ['normal', 'fire', 'water', 'electric', 'grass', 'ice',
                 'fighting', 'poison', 'ground', 'flying', 'psychic',
                 'bug', 'rock', 'ghost', 'dragon']
    for i, t in enumerate(type_list):
        curses.init_pair(10 + i, TYPE_COLORS.get(t, curses.COLOR_WHITE), -1)


def get_type_color_pair(type_name: str) -> int:
    """Get curses color pair for a type"""
    type_list = ['normal', 'fire', 'water', 'electric', 'grass', 'ice',
                 'fighting', 'poison', 'ground', 'flying', 'psychic',
                 'bug', 'rock', 'ghost', 'dragon']
    try:
        idx = type_list.index(type_name.lower())
        return curses.color_pair(10 + idx)
    except ValueError:
        return curses.color_pair(0)


def draw_pokemon_list(stdscr, pokemon_list: list, selected_idx: int, scroll_offset: int,
                      list_height: int, search_query: str = ""):
    """Draw the scrollable Pokemon list"""
    max_y, max_x = stdscr.getmaxyx()
    list_width = max_x // 2 - 2

    # Draw border and title
    stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
    stdscr.addstr(0, 1, "═" * (list_width))
    stdscr.addstr(1, 1, " SELECCIONA TU POKÉMON ")
    stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

    # Search box
    stdscr.addstr(2, 1, f"Buscar: {search_query}_" + " " * (list_width - len(search_query) - 10))

    # Filter list based on search
    if search_query:
        filtered_list = [(i, p) for i, p in enumerate(pokemon_list)
                        if search_query.lower() in p.lower()]
    else:
        filtered_list = list(enumerate(pokemon_list))

    # Draw list items
    visible_items = filtered_list[scroll_offset:scroll_offset + list_height]

    for i, (orig_idx, poke_name) in enumerate(visible_items):
        y = 4 + i
        if y >= max_y - 1:
            break

        # Get Pokemon data for type display
        try:
            poke_data = get_pokemon_data(poke_name)
            types = poke_data.get('types', ['normal'])
        except:
            types = ['normal']

        # Build display string
        display_name = poke_name.capitalize()[:15].ljust(15)

        # Highlight selected
        if orig_idx == selected_idx:
            stdscr.attron(curses.color_pair(1))
            stdscr.addstr(y, 1, f" {display_name} ")
            stdscr.attroff(curses.color_pair(1))
        else:
            stdscr.addstr(y, 1, f" {display_name} ")

        # Draw type badges
        x_offset = 18
        for t in types[:2]:
            color = get_type_color_pair(t)
            stdscr.attron(color | curses.A_BOLD)
            stdscr.addstr(y, x_offset, f"[{t[:3].upper()}]")
            stdscr.attroff(color | curses.A_BOLD)
            x_offset += 6

    # Scrollbar indicator
    if len(filtered_list) > list_height:
        scroll_pos = int((scroll_offset / max(1, len(filtered_list) - list_height)) * (list_height - 1))
        for i in range(list_height):
            char = "█" if i == scroll_pos else "│"
            stdscr.addstr(4 + i, list_width - 1, char)

    return filtered_list


def draw_pokemon_preview(stdscr, pokemon_name: str):
    """Draw Pokemon details on the right side"""
    max_y, max_x = stdscr.getmaxyx()
    start_x = max_x // 2 + 1
    preview_width = max_x // 2 - 2

    # Helper to safely write to screen with bounds checking
    def safe_addstr(row, col, text):
        if 0 <= row < max_y - 1 and 0 <= col < max_x - 1:
            try:
                stdscr.addstr(row, col, text[:max_x - col - 1])
            except curses.error:
                pass  # Ignore if still can't write

    try:
        poke_data = get_pokemon_data(pokemon_name)
    except:
        return

    # Title
    stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
    safe_addstr(0, start_x, "═" * preview_width)
    safe_addstr(1, start_x, f" {pokemon_name.upper()} ")
    stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

    # Types
    types = poke_data.get('types', ['normal'])
    safe_addstr(3, start_x, "Tipos: ")
    x_offset = start_x + 7
    for t in types:
        color = get_type_color_pair(t)
        stdscr.attron(color | curses.A_BOLD)
        if 3 < max_y - 1:
            safe_addstr(3, x_offset, f"[{t.upper()}]")
        stdscr.attroff(color | curses.A_BOLD)
        x_offset += len(t) + 3

    # Stats
    stats = poke_data.get('stats', {})
    stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
    safe_addstr(5, start_x, "ESTADÍSTICAS:")
    stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)

    stat_names = [('hp', 'HP'), ('attack', 'ATK'), ('defense', 'DEF'),
                  ('special-attack', 'SPC'), ('speed', 'SPD')]

    for i, (stat_key, stat_name) in enumerate(stat_names):
        row = 7 + i
        if row >= max_y - 1:
            break  # Stop drawing stats if we're out of vertical space

        value = stats.get(stat_key, 50)
        bar_length = min(20, value // 8)  # Scale to ~20 chars max

        # Color based on stat value
        if value >= 100:
            color = curses.color_pair(4)  # Green
        elif value >= 70:
            color = curses.color_pair(5)  # Yellow
        else:
            color = curses.color_pair(6)  # Red

        safe_addstr(row, start_x, f"{stat_name}: {str(value).rjust(3)} ")
        stdscr.attron(color)
        safe_addstr(row, start_x + 10, "█" * bar_length)
        stdscr.attroff(color)

    # Type effectiveness - only draw if we have enough vertical space
    type_info = get_pokemon_weaknesses_resistances(types)

    if 14 < max_y - 1:
        stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
        safe_addstr(14, start_x, "DEBILIDADES:")
        stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)

    if 15 < max_y - 1:
        weaknesses = type_info.get('weaknesses', [])[:6]
        x_off = start_x
        for w in weaknesses:
            color = get_type_color_pair(w)
            stdscr.attron(color)
            if x_off + len(w) + 3 < max_x:
                safe_addstr(15, x_off, f"[{w[:3].upper()}]")
            stdscr.attroff(color)
            x_off += 6

    if 17 < max_y - 1:
        stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
        safe_addstr(17, start_x, "RESISTENCIAS:")
        stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)

    if 18 < max_y - 1:
        resistances = type_info.get('resistances', [])[:6]
        x_off = start_x
        for r in resistances:
            color = get_type_color_pair(r)
            stdscr.attron(color)
            if x_off + len(r) + 3 < max_x:
                safe_addstr(18, x_off, f"[{r[:3].upper()}]")
            stdscr.attroff(color)
            x_off += 6

    # Instructions - always try to show at bottom
    if max_y >= 4:
        safe_addstr(max_y - 3, start_x, "↑/↓: Navegar | ENTER: Seleccionar")
    if max_y >= 3:
        safe_addstr(max_y - 2, start_x, "Escribe para buscar | ESC: Salir")


def select_pokemon_curses(stdscr) -> Optional[str]:
    """Interactive Pokemon selection with curses"""
    curses.curs_set(0)  # Hide cursor
    init_colors()

    pokemon_list = get_kanto_pokemon_list()
    selected_idx = 0
    scroll_offset = 0
    search_query = ""

    while True:
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()
        list_height = max_y - 6

        # Draw list and get filtered results
        filtered_list = draw_pokemon_list(stdscr, pokemon_list, selected_idx,
                                          scroll_offset, list_height, search_query)

        # Find current selection in filtered list
        current_name = pokemon_list[selected_idx] if selected_idx < len(pokemon_list) else ""

        # Draw preview
        draw_pokemon_preview(stdscr, current_name)

        stdscr.refresh()

        # Handle input
        key = stdscr.getch()

        if key == 27:  # ESC
            return None
        elif key == curses.KEY_UP:
            if selected_idx > 0:
                selected_idx -= 1
                # Adjust scroll if needed
                filtered_idx = next((i for i, (orig, _) in enumerate(filtered_list)
                                    if orig == selected_idx), 0)
                if filtered_idx < scroll_offset:
                    scroll_offset = max(0, filtered_idx)
        elif key == curses.KEY_DOWN:
            if selected_idx < len(pokemon_list) - 1:
                selected_idx += 1
                # Adjust scroll if needed
                filtered_idx = next((i for i, (orig, _) in enumerate(filtered_list)
                                    if orig == selected_idx), 0)
                if filtered_idx >= scroll_offset + list_height:
                    scroll_offset = filtered_idx - list_height + 1
        elif key == 10:  # Enter
            return current_name
        elif key == curses.KEY_BACKSPACE or key == 127:
            search_query = search_query[:-1]
            # Reset selection to first match
            if search_query:
                for i, name in enumerate(pokemon_list):
                    if search_query.lower() in name.lower():
                        selected_idx = i
                        scroll_offset = 0
                        break
        elif 32 <= key <= 126:  # Printable characters
            search_query += chr(key)
            # Jump to first match
            for i, name in enumerate(pokemon_list):
                if search_query.lower() in name.lower():
                    selected_idx = i
                    scroll_offset = 0
                    break


def draw_move_list(stdscr, moves: list, selected_moves: list, cursor_idx: int,
                   scroll_offset: int, list_height: int, move_sources: dict = None):
    """Draw the move selection list"""
    max_y, max_x = stdscr.getmaxyx()
    list_width = max_x // 2 - 2

    # Title
    stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
    stdscr.addstr(0, 1, "═" * list_width)
    stdscr.addstr(1, 1, f" SELECCIONA 4 MOVIMIENTOS ({len(selected_moves)}/4) ")
    stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

    # Draw list
    visible_moves = moves[scroll_offset:scroll_offset + list_height]

    for i, move_name in enumerate(visible_moves):
        actual_idx = scroll_offset + i
        y = 3 + i
        if y >= max_y - 1:
            break

        # Check if already selected
        is_selected = move_name in selected_moves
        is_cursor = actual_idx == cursor_idx

        # Get move source
        source = move_sources.get(move_name, "level-up") if move_sources else "level-up"

        # Get move data for type
        try:
            move_data = create_move(move_name)
            move_type = move_data.type.value.lower()
            power = move_data.power
            accuracy = move_data.accuracy
        except:
            move_type = 'normal'
            power = 0
            accuracy = 100

        # Build display with source indicator
        marker = "●" if is_selected else " "
        # Source indicator: TM for TM moves, EVO for evolution moves, nothing for level-up
        if source == "tm":
            source_tag = "TM "
        elif source == "evolution":
            source_tag = "EVO"
        else:
            source_tag = "   "

        display = f"{marker} {move_name.capitalize()[:15].ljust(15)}"

        if is_cursor:
            stdscr.attron(curses.color_pair(1))
            stdscr.addstr(y, 1, display)
            stdscr.attroff(curses.color_pair(1))
        else:
            stdscr.addstr(y, 1, display)

        # Source tag (dimmed for TM/EVO)
        if source == "tm":
            stdscr.attron(curses.color_pair(5))  # Yellow for TM
            stdscr.addstr(y, 18, source_tag)
            stdscr.attroff(curses.color_pair(5))
        elif source == "evolution":
            stdscr.attron(curses.color_pair(4))  # Green for EVO
            stdscr.addstr(y, 18, source_tag)
            stdscr.attroff(curses.color_pair(4))
        else:
            stdscr.addstr(y, 18, source_tag)

        # Type badge
        color = get_type_color_pair(move_type)
        stdscr.attron(color | curses.A_BOLD)
        stdscr.addstr(y, 22, f"[{move_type[:3].upper()}]")
        stdscr.attroff(color | curses.A_BOLD)

        # Power/Accuracy
        if power > 0:
            stdscr.addstr(y, 29, f"P:{power:3}")
        else:
            stdscr.addstr(y, 29, "P: --")
        stdscr.addstr(y, 36, f"A:{accuracy:3}")


def draw_move_preview(stdscr, move_name: str, pokemon_name: str, move_source: str = "level-up"):
    """Draw move details on the right side"""
    max_y, max_x = stdscr.getmaxyx()
    start_x = max_x // 2 + 1
    preview_width = max_x // 2 - 2

    try:
        move = create_move(move_name)
    except:
        return

    # Title
    stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
    stdscr.addstr(0, start_x, "═" * preview_width)
    stdscr.addstr(1, start_x, f" {move_name.upper()} ")
    stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

    # Source indicator
    if move_source == "tm":
        stdscr.attron(curses.color_pair(5) | curses.A_BOLD)  # Yellow
        stdscr.addstr(2, start_x, "[TM] Máquina Técnica")
        stdscr.attroff(curses.color_pair(5) | curses.A_BOLD)
    elif move_source == "evolution":
        stdscr.attron(curses.color_pair(4) | curses.A_BOLD)  # Green
        stdscr.addstr(2, start_x, "[EVO] Línea evolutiva")
        stdscr.attroff(curses.color_pair(4) | curses.A_BOLD)

    # Type
    move_type = move.type.value.lower()
    color = get_type_color_pair(move_type)
    stdscr.addstr(4, start_x, "Tipo: ")
    stdscr.attron(color | curses.A_BOLD)
    stdscr.addstr(4, start_x + 6, f"[{move_type.upper()}]")
    stdscr.attroff(color | curses.A_BOLD)

    # Category
    category = move.category.value
    stdscr.addstr(5, start_x, f"Categoría: {category}")

    # Stats
    stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
    stdscr.addstr(7, start_x, "ESTADÍSTICAS:")
    stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)

    power_str = str(move.power) if move.power > 0 else "--"
    stdscr.addstr(8, start_x, f"Poder:     {power_str}")
    stdscr.addstr(9, start_x, f"Precisión: {move.accuracy}%")
    stdscr.addstr(10, start_x, f"PP:        {move.pp}")

    # Status effect
    if move.status_effect:
        stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
        stdscr.addstr(12, start_x, "EFECTO:")
        stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)
        stdscr.addstr(13, start_x, f"{move.status_effect.value} ({move.status_chance}%)")

    # Stat changes
    if move.stat_changes:
        stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
        stdscr.addstr(15, start_x, "CAMBIOS DE STATS:")
        stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)
        y = 16
        for stat, change in move.stat_changes.items():
            sign = "+" if change > 0 else ""
            stdscr.addstr(y, start_x, f"  {stat}: {sign}{change}")
            y += 1

    # Instructions
    stdscr.addstr(max_y - 3, start_x, "↑/↓: Navegar | ESPACIO: Seleccionar")
    stdscr.addstr(max_y - 2, start_x, "ENTER: Confirmar | ESC: Cancelar")


def select_moves_curses(stdscr, pokemon_name: str) -> Optional[list]:
    """Interactive move selection with curses"""
    curses.curs_set(0)
    init_colors()

    move_sources = get_pokemon_moves_with_source(pokemon_name)
    available_moves = list(move_sources.keys())
    selected_moves = []
    cursor_idx = 0
    scroll_offset = 0

    while True:
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()
        list_height = max_y - 5

        # Draw move list
        draw_move_list(stdscr, available_moves, selected_moves, cursor_idx,
                      scroll_offset, list_height, move_sources)

        # Draw preview
        current_move = available_moves[cursor_idx] if cursor_idx < len(available_moves) else ""
        current_source = move_sources.get(current_move, "level-up")
        draw_move_preview(stdscr, current_move, pokemon_name, current_source)

        stdscr.refresh()

        # Handle input
        key = stdscr.getch()

        if key == 27:  # ESC
            return None
        elif key == curses.KEY_UP:
            if cursor_idx > 0:
                cursor_idx -= 1
                if cursor_idx < scroll_offset:
                    scroll_offset = cursor_idx
        elif key == curses.KEY_DOWN:
            if cursor_idx < len(available_moves) - 1:
                cursor_idx += 1
                if cursor_idx >= scroll_offset + list_height:
                    scroll_offset = cursor_idx - list_height + 1
        elif key == ord(' '):  # Space to toggle selection
            move = available_moves[cursor_idx]
            if move in selected_moves:
                selected_moves.remove(move)
            elif len(selected_moves) < 4:
                selected_moves.append(move)
        elif key == 10:  # Enter to confirm
            if len(selected_moves) == 4:
                return selected_moves


def interactive_pokemon_selection() -> Optional[Pokemon]:
    """Main function to run the interactive Pokemon selection"""
    # Select Pokemon
    pokemon_name = curses.wrapper(select_pokemon_curses)
    if not pokemon_name:
        return None

    # Get Pokemon data
    poke_data = get_pokemon_data(pokemon_name)

    # Select moves
    selected_move_names = curses.wrapper(lambda stdscr: select_moves_curses(stdscr, pokemon_name))
    if not selected_move_names:
        return None

    # Create moves
    moves = [create_move(name) for name in selected_move_names]

    # Create Pokemon
    stats = Stats(
        hp=poke_data['stats'].get('hp', 100),
        attack=poke_data['stats'].get('attack', 50),
        defense=poke_data['stats'].get('defense', 50),
        special=poke_data['stats'].get('special-attack', 50),
        speed=poke_data['stats'].get('speed', 50)
    )
    types = [getattr(Type, t.upper(), Type.NORMAL) for t in poke_data['types']]

    return Pokemon(poke_data['name'], types, stats, moves, level=50)


def draw_battle_format_menu(stdscr, selected_idx: int):
    """Draw the battle format selection menu"""
    stdscr.clear()
    max_y, max_x = stdscr.getmaxyx()

    formats = list(BattleFormat)

    # Title
    title = "═" * 40
    stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
    stdscr.addstr(2, max_x // 2 - 20, title)
    stdscr.addstr(3, max_x // 2 - 15, " SELECCIONA EL FORMATO DE BATALLA ")
    stdscr.addstr(4, max_x // 2 - 20, title)
    stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

    # Options
    for i, fmt in enumerate(formats):
        y = 7 + i * 3

        if i == selected_idx:
            stdscr.attron(curses.color_pair(1))
            stdscr.addstr(y, max_x // 2 - 15, f" ► {fmt.description} ")
            stdscr.attroff(curses.color_pair(1))
        else:
            stdscr.addstr(y, max_x // 2 - 15, f"   {fmt.description} ")

        # Description
        desc = ""
        if fmt == BattleFormat.SINGLE:
            desc = "Batalla clásica con un solo Pokémon"
        elif fmt == BattleFormat.TRIPLE:
            desc = "Elige 3 Pokémon para tu equipo"
        elif fmt == BattleFormat.FULL:
            desc = "Batalla completa con 6 Pokémon"

        stdscr.addstr(y + 1, max_x // 2 - 15, f"   {desc}")

    # Instructions
    stdscr.addstr(max_y - 3, max_x // 2 - 15, "↑/↓: Navegar")
    stdscr.addstr(max_y - 2, max_x // 2 - 15, "ENTER: Seleccionar | ESC: Salir")


def select_battle_format_curses(stdscr) -> Optional[BattleFormat]:
    """Interactive battle format selection"""
    curses.curs_set(0)
    init_colors()

    formats = list(BattleFormat)
    selected_idx = 0

    while True:
        draw_battle_format_menu(stdscr, selected_idx)
        stdscr.refresh()

        key = stdscr.getch()

        if key == 27:  # ESC
            return None
        elif key == curses.KEY_UP:
            selected_idx = max(0, selected_idx - 1)
        elif key == curses.KEY_DOWN:
            selected_idx = min(len(formats) - 1, selected_idx + 1)
        elif key == 10:  # Enter
            return formats[selected_idx]


def draw_team_selection(stdscr, team_pokemon: list, max_size: int,
                       pokemon_list: list, selected_idx: int, scroll_offset: int,
                       list_height: int, search_query: str = ""):
    """Draw the team selection UI"""
    max_y, max_x = stdscr.getmaxyx()
    list_width = max_x // 2 - 2

    # Draw border and title
    stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
    stdscr.addstr(0, 1, "═" * list_width)
    stdscr.addstr(1, 1, f" SELECCIONA TU EQUIPO ({len(team_pokemon)}/{max_size}) ")
    stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

    # Search box
    stdscr.addstr(2, 1, f"Buscar: {search_query}_" + " " * (list_width - len(search_query) - 10))

    # Already selected Pokemon (top of right panel)
    start_x = max_x // 2 + 1
    stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
    stdscr.addstr(0, start_x, "TU EQUIPO:")
    stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)

    for i, poke in enumerate(team_pokemon):
        stdscr.addstr(2 + i, start_x, f"  {i+1}. {poke.name}")
        # Show types
        x_off = start_x + 20
        for t in poke.types[:2]:
            color = get_type_color_pair(t.value)
            stdscr.attron(color | curses.A_BOLD)
            stdscr.addstr(2 + i, x_off, f"[{t.value[:3].upper()}]")
            stdscr.attroff(color | curses.A_BOLD)
            x_off += 6

    # Filter list based on search and already selected
    selected_names = [p.name.lower() for p in team_pokemon]
    if search_query:
        filtered_list = [(i, p) for i, p in enumerate(pokemon_list)
                        if search_query.lower() in p.lower() and p.lower() not in selected_names]
    else:
        filtered_list = [(i, p) for i, p in enumerate(pokemon_list)
                        if p.lower() not in selected_names]

    # Draw list items
    visible_items = filtered_list[scroll_offset:scroll_offset + list_height]

    for i, (orig_idx, poke_name) in enumerate(visible_items):
        y = 4 + i
        if y >= max_y - 1:
            break

        # Get Pokemon data for type display
        try:
            poke_data = get_pokemon_data(poke_name)
            types = poke_data.get('types', ['normal'])
        except Exception:
            types = ['normal']

        # Build display string
        display_name = poke_name.capitalize()[:15].ljust(15)

        # Highlight selected
        if orig_idx == selected_idx:
            stdscr.attron(curses.color_pair(1))
            stdscr.addstr(y, 1, f" {display_name} ")
            stdscr.attroff(curses.color_pair(1))
        else:
            stdscr.addstr(y, 1, f" {display_name} ")

        # Draw type badges
        x_offset = 18
        for t in types[:2]:
            color = get_type_color_pair(t)
            stdscr.attron(color | curses.A_BOLD)
            stdscr.addstr(y, x_offset, f"[{t[:3].upper()}]")
            stdscr.attroff(color | curses.A_BOLD)
            x_offset += 6

    # Instructions
    stdscr.addstr(max_y - 3, 1, "↑/↓: Navegar | ENTER: Agregar Pokémon")
    stdscr.addstr(max_y - 2, 1, "BACKSPACE: Quitar último | ESC: Cancelar")
    if len(team_pokemon) == max_size:
        stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
        stdscr.addstr(max_y - 1, 1, "Presiona ENTER para continuar a seleccionar movimientos")
        stdscr.attroff(curses.color_pair(4) | curses.A_BOLD)

    return filtered_list


def select_team_curses(stdscr, team_size: int) -> Optional[list[str]]:
    """Interactive team selection"""
    curses.curs_set(0)
    init_colors()

    pokemon_list = get_kanto_pokemon_list()
    team_pokemon: list[Pokemon] = []
    selected_idx = 0
    scroll_offset = 0
    search_query = ""

    while True:
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()
        list_height = max_y - 6

        # Draw team selection
        filtered_list = draw_team_selection(
            stdscr, team_pokemon, team_size, pokemon_list,
            selected_idx, scroll_offset, list_height, search_query
        )

        # Draw preview for current selection
        if filtered_list:
            # Find current selection in filtered list
            current_filtered_idx = next(
                (i for i, (orig, _) in enumerate(filtered_list) if orig == selected_idx),
                0
            )
            if current_filtered_idx < len(filtered_list):
                current_name = filtered_list[current_filtered_idx][1]
            else:
                current_name = pokemon_list[selected_idx] if selected_idx < len(pokemon_list) else ""
        else:
            current_name = pokemon_list[selected_idx] if selected_idx < len(pokemon_list) else ""

        # Draw Pokemon preview in lower right
        if current_name:
            draw_pokemon_preview(stdscr, current_name)

        stdscr.refresh()

        # Handle input
        key = stdscr.getch()

        if key == 27:  # ESC
            return None
        elif key == curses.KEY_UP:
            if selected_idx > 0:
                selected_idx -= 1
                # Adjust scroll if selection moved above visible area
                filtered_idx = next((i for i, (orig, _) in enumerate(filtered_list)
                                    if orig == selected_idx), 0)
                if filtered_idx < scroll_offset:
                    scroll_offset = max(0, filtered_idx)
        elif key == curses.KEY_DOWN:
            if selected_idx < len(pokemon_list) - 1:
                selected_idx += 1
                # Adjust scroll if selection moved below visible area
                filtered_idx = next((i for i, (orig, _) in enumerate(filtered_list)
                                    if orig == selected_idx), 0)
                if filtered_idx >= scroll_offset + list_height:
                    scroll_offset = filtered_idx - list_height + 1
        elif key == curses.KEY_BACKSPACE or key == 127:
            if search_query:
                search_query = search_query[:-1]
            elif team_pokemon:
                # Remove last Pokemon from team
                team_pokemon.pop()
        elif key == 10:  # Enter
            if len(team_pokemon) == team_size:
                # Team is complete, return names
                return [p.name.lower() for p in team_pokemon]
            elif filtered_list and len(team_pokemon) < team_size:
                # Find the currently selected Pokemon from filtered list
                current_filtered_idx = next(
                    (i for i, (orig, _) in enumerate(filtered_list) if orig == selected_idx),
                    0
                )
                if current_filtered_idx < len(filtered_list):
                    poke_name = filtered_list[current_filtered_idx][1]
                    # Create a temporary Pokemon to add to team
                    poke_data = get_pokemon_data(poke_name)
                    stats = Stats(
                        hp=poke_data['stats'].get('hp', 100),
                        attack=poke_data['stats'].get('attack', 50),
                        defense=poke_data['stats'].get('defense', 50),
                        special=poke_data['stats'].get('special-attack', 50),
                        speed=poke_data['stats'].get('speed', 50)
                    )
                    types = [getattr(Type, t.upper(), Type.NORMAL) for t in poke_data['types']]
                    temp_pokemon = Pokemon(poke_data['name'], types, stats, [], level=50)
                    team_pokemon.append(temp_pokemon)
                    search_query = ""
        elif 32 <= key <= 126:  # Printable characters
            search_query += chr(key)
            # Jump to first match
            for i, name in enumerate(pokemon_list):
                if search_query.lower() in name.lower():
                    selected_idx = i
                    scroll_offset = 0
                    break


def interactive_team_selection(battle_format: BattleFormat, trainer_name: str = "Jugador") -> Optional[Team]:
    """
    Full interactive team selection for a battle format.

    Args:
        battle_format: The battle format (determines team size)
        trainer_name: Name for the trainer

    Returns:
        A Team with selected Pokemon and moves, or None if cancelled
    """
    team_size = battle_format.team_size

    # Select Pokemon for the team
    pokemon_names = curses.wrapper(lambda stdscr: select_team_curses(stdscr, team_size))
    if not pokemon_names:
        return None

    # Now select moves for each Pokemon
    team_pokemon = []
    for i, poke_name in enumerate(pokemon_names):
        poke_data = get_pokemon_data(poke_name)

        print(f"\nSeleccionando movimientos para {poke_data['name']} ({i+1}/{team_size})...")

        # Select moves using existing move selection UI
        selected_move_names = curses.wrapper(lambda stdscr: select_moves_curses(stdscr, poke_name))
        if not selected_move_names:
            return None

        # Create the Pokemon
        moves = [create_move(name) for name in selected_move_names]
        stats = Stats(
            hp=poke_data['stats'].get('hp', 100),
            attack=poke_data['stats'].get('attack', 50),
            defense=poke_data['stats'].get('defense', 50),
            special=poke_data['stats'].get('special-attack', 50),
            speed=poke_data['stats'].get('speed', 50)
        )
        types = [getattr(Type, t.upper(), Type.NORMAL) for t in poke_data['types']]
        pokemon = Pokemon(poke_data['name'], types, stats, moves, level=50)
        team_pokemon.append(pokemon)

    return Team(team_pokemon, trainer_name)


def select_battle_format() -> Optional[BattleFormat]:
    """Select the battle format"""
    return curses.wrapper(select_battle_format_curses)


def draw_switch_menu(stdscr, team: Team, title: str = "ELIGE UN POKÉMON"):
    """Draw the switch Pokemon menu"""
    stdscr.clear()
    max_y, max_x = stdscr.getmaxyx()
    init_colors()

    # Title
    stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
    stdscr.addstr(1, max_x // 2 - 15, "═" * 30)
    stdscr.addstr(2, max_x // 2 - len(title) // 2, title)
    stdscr.addstr(3, max_x // 2 - 15, "═" * 30)
    stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)


def select_switch_curses(stdscr, team: Team) -> Optional[int]:
    """Interactive switch selection"""
    curses.curs_set(0)
    init_colors()

    available = team.get_available_switches()
    if not available:
        return None

    selected_idx = 0

    while True:
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()

        # Title
        stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
        stdscr.addstr(1, max_x // 2 - 15, "═" * 30)
        stdscr.addstr(2, max_x // 2 - 12, " ELIGE UN POKÉMON ")
        stdscr.addstr(3, max_x // 2 - 15, "═" * 30)
        stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

        # Draw available Pokemon
        for i, (idx, poke) in enumerate(available):
            y = 6 + i * 2
            hp_pct = poke.current_hp / poke.max_hp

            # HP color
            if hp_pct > 0.5:
                hp_color = curses.color_pair(4)  # Green
            elif hp_pct > 0.2:
                hp_color = curses.color_pair(5)  # Yellow
            else:
                hp_color = curses.color_pair(6)  # Red

            if i == selected_idx:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(y, max_x // 2 - 20, f" ► {poke.name.ljust(15)} ")
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(y, max_x // 2 - 20, f"   {poke.name.ljust(15)} ")

            # HP bar
            stdscr.attron(hp_color)
            hp_bar = "█" * int(hp_pct * 10) + "░" * (10 - int(hp_pct * 10))
            stdscr.addstr(y, max_x // 2 + 2, f"[{hp_bar}]")
            stdscr.attroff(hp_color)

            stdscr.addstr(y, max_x // 2 + 15, f"{poke.current_hp}/{poke.max_hp}")

            # Status
            if poke.status.value != "None":
                stdscr.addstr(y + 1, max_x // 2 - 17, f"   Estado: {poke.status.value}")

        # Instructions
        stdscr.addstr(max_y - 2, max_x // 2 - 15, "↑/↓: Navegar | ENTER: Seleccionar")

        stdscr.refresh()
        key = stdscr.getch()

        if key == 27:  # ESC - can't cancel forced switch
            pass
        elif key == curses.KEY_UP:
            selected_idx = max(0, selected_idx - 1)
        elif key == curses.KEY_DOWN:
            selected_idx = min(len(available) - 1, selected_idx + 1)
        elif key == 10:  # Enter
            return available[selected_idx][0]


def select_switch(team: Team) -> Optional[int]:
    """Select a Pokemon to switch to"""
    return curses.wrapper(lambda stdscr: select_switch_curses(stdscr, team))


def draw_battle_action_menu(stdscr, team: Team, opponent_team: Team):
    """Draw the battle action selection menu"""
    max_y, max_x = stdscr.getmaxyx()
    init_colors()

    active = team.active_pokemon
    opponent = opponent_team.active_pokemon

    # Battle status
    stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
    stdscr.addstr(1, 2, f"Tu Pokémon: {active.name}")
    stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

    # HP bars
    hp_pct = active.current_hp / active.max_hp
    if hp_pct > 0.5:
        color = curses.color_pair(4)
    elif hp_pct > 0.2:
        color = curses.color_pair(5)
    else:
        color = curses.color_pair(6)

    stdscr.attron(color)
    hp_bar = "█" * int(hp_pct * 20) + "░" * (20 - int(hp_pct * 20))
    stdscr.addstr(2, 2, f"[{hp_bar}] {active.current_hp}/{active.max_hp}")
    stdscr.attroff(color)

    # Opponent
    stdscr.attron(curses.color_pair(6))
    stdscr.addstr(1, max_x - 30, f"Oponente: {opponent.name}")
    stdscr.attroff(curses.color_pair(6))

    opp_pct = opponent.current_hp / opponent.max_hp
    if opp_pct > 0.5:
        color = curses.color_pair(4)
    elif opp_pct > 0.2:
        color = curses.color_pair(5)
    else:
        color = curses.color_pair(6)

    stdscr.attron(color)
    opp_bar = "█" * int(opp_pct * 20) + "░" * (20 - int(opp_pct * 20))
    stdscr.addstr(2, max_x - 30, f"[{opp_bar}] {opponent.current_hp}/{opponent.max_hp}")
    stdscr.attroff(color)


def select_battle_action_curses(stdscr, team: Team, opponent_team: Team) -> Optional[tuple[str, any]]:
    """
    Interactive battle action selection.

    Returns:
        ("attack", move_index) or ("switch", pokemon_index) or None
    """
    curses.curs_set(0)
    init_colors()

    active = team.active_pokemon
    mode = "main"  # "main", "moves", "switch"
    selected_idx = 0

    while True:
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()

        draw_battle_action_menu(stdscr, team, opponent_team)

        if mode == "main":
            # Main menu
            stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
            stdscr.addstr(5, max_x // 2 - 10, "¿Qué quieres hacer?")
            stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)

            options = ["Atacar", "Cambiar Pokémon"]
            for i, opt in enumerate(options):
                y = 8 + i * 2
                if i == selected_idx:
                    stdscr.attron(curses.color_pair(1))
                    stdscr.addstr(y, max_x // 2 - 10, f" ► {opt} ")
                    stdscr.attroff(curses.color_pair(1))
                else:
                    stdscr.addstr(y, max_x // 2 - 10, f"   {opt} ")

            stdscr.addstr(max_y - 2, 2, "↑/↓: Navegar | ENTER: Seleccionar")

        elif mode == "moves":
            # Move selection
            stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
            stdscr.addstr(5, 2, "Selecciona un movimiento:")
            stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)

            for i, move in enumerate(active.moves):
                y = 7 + i * 2
                pp_text = f"PP: {move.pp}/{move.max_pp}"
                power_text = f"Poder: {move.power}" if move.power > 0 else "Poder: --"

                # Type color
                type_color = get_type_color_pair(move.type.value)

                if i == selected_idx:
                    stdscr.attron(curses.color_pair(1))
                    stdscr.addstr(y, 2, f" ► {move.name.ljust(15)} ")
                    stdscr.attroff(curses.color_pair(1))
                else:
                    stdscr.addstr(y, 2, f"   {move.name.ljust(15)} ")

                # Type badge
                stdscr.attron(type_color | curses.A_BOLD)
                stdscr.addstr(y, 22, f"[{move.type.value[:3].upper()}]")
                stdscr.attroff(type_color | curses.A_BOLD)

                # PP and power
                if move.pp == 0:
                    stdscr.attron(curses.color_pair(6))  # Red for no PP
                stdscr.addstr(y, 30, pp_text)
                if move.pp == 0:
                    stdscr.attroff(curses.color_pair(6))

                stdscr.addstr(y, 45, power_text)

            stdscr.addstr(max_y - 2, 2, "↑/↓: Navegar | ENTER: Seleccionar | ESC: Volver")

        stdscr.refresh()
        key = stdscr.getch()

        if key == 27:  # ESC
            if mode == "main":
                pass  # Can't cancel
            else:
                mode = "main"
                selected_idx = 0
        elif key == curses.KEY_UP:
            if mode == "main":
                selected_idx = max(0, selected_idx - 1)
            elif mode == "moves":
                selected_idx = max(0, selected_idx - 1)
        elif key == curses.KEY_DOWN:
            if mode == "main":
                selected_idx = min(1, selected_idx + 1)
            elif mode == "moves":
                selected_idx = min(len(active.moves) - 1, selected_idx + 1)
        elif key == 10:  # Enter
            if mode == "main":
                if selected_idx == 0:  # Attack
                    mode = "moves"
                    selected_idx = 0
                else:  # Switch
                    if team.can_switch():
                        return ("switch", None)
                    else:
                        # Can't switch, flash message
                        pass
            elif mode == "moves":
                move = active.moves[selected_idx]
                if move.has_pp():
                    return ("attack", selected_idx)


def select_battle_action(team: Team, opponent_team: Team) -> Optional[tuple[str, any]]:
    """
    Select a battle action (attack or switch).

    Returns:
        ("attack", move_index) or ("switch", None)
    """
    return curses.wrapper(lambda stdscr: select_battle_action_curses(stdscr, team, opponent_team))


# =============================================================================
# Battle Mode and Moveset Mode Selection
# =============================================================================

def draw_battle_mode_menu(stdscr, selected_idx: int):
    """Draw the battle mode selection menu"""
    stdscr.clear()
    max_y, max_x = stdscr.getmaxyx()

    modes = list(BattleMode)

    # Title
    title_width = 40
    stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
    stdscr.addstr(2, max_x // 2 - title_width // 2, "═" * title_width)
    stdscr.addstr(3, max_x // 2 - 15, " MODO DE BATALLA ")
    stdscr.addstr(4, max_x // 2 - title_width // 2, "═" * title_width)
    stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

    # Options
    for i, mode in enumerate(modes):
        y = 7 + i * 3

        if i == selected_idx:
            stdscr.attron(curses.color_pair(1))
            stdscr.addstr(y, max_x // 2 - 20, f" ► {mode.description} ")
            stdscr.attroff(curses.color_pair(1))
        else:
            stdscr.addstr(y, max_x // 2 - 20, f"   {mode.description} ")

        # Extra description
        extra = ""
        if mode == BattleMode.PLAYER_VS_AI:
            extra = "Controlas tu equipo, la IA controla el rival"
        elif mode == BattleMode.AUTOBATTLE:
            extra = "La IA controla ambos equipos (3s entre turnos)"
        elif mode == BattleMode.WATCH:
            extra = "Modo espectador con pausas más largas (4s)"

        stdscr.addstr(y + 1, max_x // 2 - 20, f"   {extra}")

    # Instructions
    stdscr.addstr(max_y - 3, max_x // 2 - 15, "↑/↓: Navegar")
    stdscr.addstr(max_y - 2, max_x // 2 - 15, "ENTER: Seleccionar | ESC: Salir")


def select_battle_mode_curses(stdscr) -> Optional[BattleMode]:
    """Interactive battle mode selection"""
    curses.curs_set(0)
    init_colors()

    modes = list(BattleMode)
    selected_idx = 0

    while True:
        draw_battle_mode_menu(stdscr, selected_idx)
        stdscr.refresh()

        key = stdscr.getch()

        if key == 27:  # ESC
            return None
        elif key == curses.KEY_UP:
            selected_idx = max(0, selected_idx - 1)
        elif key == curses.KEY_DOWN:
            selected_idx = min(len(modes) - 1, selected_idx + 1)
        elif key == 10:  # Enter
            return modes[selected_idx]


def select_battle_mode() -> Optional[BattleMode]:
    """Select the battle mode"""
    return curses.wrapper(select_battle_mode_curses)


def draw_moveset_mode_menu(stdscr, selected_idx: int):
    """Draw the moveset mode selection menu"""
    stdscr.clear()
    max_y, max_x = stdscr.getmaxyx()

    modes = list(MovesetMode)

    # Title
    title_width = 44
    stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
    stdscr.addstr(2, max_x // 2 - title_width // 2, "═" * title_width)
    stdscr.addstr(3, max_x // 2 - 17, " SELECCIÓN DE MOVIMIENTOS ")
    stdscr.addstr(4, max_x // 2 - title_width // 2, "═" * title_width)
    stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

    # Options
    for i, mode in enumerate(modes):
        y = 7 + i * 3

        if i == selected_idx:
            stdscr.attron(curses.color_pair(1))
            stdscr.addstr(y, max_x // 2 - 22, f" ► {mode.description} ")
            stdscr.attroff(curses.color_pair(1))
        else:
            stdscr.addstr(y, max_x // 2 - 22, f"   {mode.description} ")

        # Extra description
        extra = ""
        if mode == MovesetMode.MANUAL:
            extra = "Elige cada movimiento manualmente"
        elif mode == MovesetMode.RANDOM:
            extra = "4 movimientos aleatorios del pool disponible"
        elif mode == MovesetMode.PRESET:
            extra = "Movesets competitivos predefinidos"
        elif mode == MovesetMode.SMART_RANDOM:
            extra = "Aleatorio pero asegura STAB y variedad"

        stdscr.addstr(y + 1, max_x // 2 - 22, f"   {extra}")

    # Instructions
    stdscr.addstr(max_y - 3, max_x // 2 - 15, "↑/↓: Navegar")
    stdscr.addstr(max_y - 2, max_x // 2 - 15, "ENTER: Seleccionar | ESC: Salir")


def select_moveset_mode_curses(stdscr) -> Optional[MovesetMode]:
    """Interactive moveset mode selection"""
    curses.curs_set(0)
    init_colors()

    modes = list(MovesetMode)
    selected_idx = 0

    while True:
        draw_moveset_mode_menu(stdscr, selected_idx)
        stdscr.refresh()

        key = stdscr.getch()

        if key == 27:  # ESC
            return None
        elif key == curses.KEY_UP:
            selected_idx = max(0, selected_idx - 1)
        elif key == curses.KEY_DOWN:
            selected_idx = min(len(modes) - 1, selected_idx + 1)
        elif key == 10:  # Enter
            return modes[selected_idx]


def select_moveset_mode() -> Optional[MovesetMode]:
    """Select the moveset selection mode"""
    return curses.wrapper(select_moveset_mode_curses)


def select_battle_settings() -> Optional[BattleSettings]:
    """
    Interactive selection of all battle settings.

    Returns:
        BattleSettings configured based on user choices, or None if cancelled
    """
    # Select battle mode first
    battle_mode = select_battle_mode()
    if battle_mode is None:
        return None

    # Select moveset mode
    moveset_mode = select_moveset_mode()
    if moveset_mode is None:
        return None

    # Create settings based on selections
    if battle_mode == BattleMode.WATCH:
        settings = BattleSettings.for_watch_mode()
        settings.moveset_mode = moveset_mode
    elif battle_mode == BattleMode.AUTOBATTLE:
        settings = BattleSettings.for_autobattle()
        settings.moveset_mode = moveset_mode
    else:
        settings = BattleSettings.default()
        settings.moveset_mode = moveset_mode

    return settings


def create_pokemon_with_moveset(pokemon_name: str, moveset_mode: MovesetMode) -> Optional[Pokemon]:
    """
    Create a Pokemon with moves selected based on the moveset mode.

    Args:
        pokemon_name: Name of the Pokemon
        moveset_mode: How to select moves

    Returns:
        Pokemon with moves, or None if manual selection was cancelled
    """
    poke_data = get_pokemon_data(pokemon_name)

    # Get moves based on mode
    if moveset_mode == MovesetMode.MANUAL:
        selected_move_names = curses.wrapper(lambda stdscr: select_moves_curses(stdscr, pokemon_name))
        if not selected_move_names:
            return None
    else:
        # Use auto-selection
        mode_map = {
            MovesetMode.RANDOM: "random",
            MovesetMode.PRESET: "preset",
            MovesetMode.SMART_RANDOM: "smart_random"
        }
        selected_move_names = get_moveset_for_pokemon(pokemon_name, mode_map.get(moveset_mode, "random"))

    # Create moves
    moves = [create_move(name) for name in selected_move_names]

    # Create Pokemon
    stats = Stats(
        hp=poke_data['stats'].get('hp', 100),
        attack=poke_data['stats'].get('attack', 50),
        defense=poke_data['stats'].get('defense', 50),
        special=poke_data['stats'].get('special-attack', 50),
        speed=poke_data['stats'].get('speed', 50)
    )
    types = [getattr(Type, t.upper(), Type.NORMAL) for t in poke_data['types']]

    return Pokemon(poke_data['name'], types, stats, moves, level=50)


def interactive_team_selection_with_settings(
    battle_format: BattleFormat,
    moveset_mode: MovesetMode,
    trainer_name: str = "Jugador"
) -> Optional[Team]:
    """
    Full interactive team selection with configurable moveset mode.

    Args:
        battle_format: The battle format (determines team size)
        moveset_mode: How to select movesets
        trainer_name: Name for the trainer

    Returns:
        A Team with selected Pokemon and moves, or None if cancelled
    """
    team_size = battle_format.team_size

    # Select Pokemon for the team
    pokemon_names = curses.wrapper(lambda stdscr: select_team_curses(stdscr, team_size))
    if not pokemon_names:
        return None

    # Now create Pokemon with movesets based on mode
    team_pokemon = []
    for i, poke_name in enumerate(pokemon_names):
        if moveset_mode == MovesetMode.MANUAL:
            poke_data = get_pokemon_data(poke_name)
            print(f"\nSeleccionando movimientos para {poke_data['name']} ({i+1}/{team_size})...")

        pokemon = create_pokemon_with_moveset(poke_name, moveset_mode)
        if pokemon is None:
            return None

        team_pokemon.append(pokemon)

        # Show what was selected for non-manual modes
        if moveset_mode != MovesetMode.MANUAL:
            print(f"  {pokemon.name}: {', '.join([m.name for m in pokemon.moves])}")

    return Team(team_pokemon, trainer_name)


# =============================================================================
# Ruleset Selection
# =============================================================================

def draw_ruleset_menu(stdscr, selected_idx: int):
    """Draw the ruleset selection menu"""
    from models.ruleset import ALL_RULESETS
    stdscr.clear()
    max_y, max_x = stdscr.getmaxyx()

    rulesets = ALL_RULESETS

    # Title
    title_width = 44
    stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
    stdscr.addstr(1, max_x // 2 - title_width // 2, "═" * title_width)
    stdscr.addstr(2, max_x // 2 - 17, " SELECCIONA LAS REGLAS DE BATALLA ")
    stdscr.addstr(3, max_x // 2 - title_width // 2, "═" * title_width)
    stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

    # Options
    for i, ruleset in enumerate(rulesets):
        y = 5 + i * 2
        if y >= max_y - 4:
            break

        if i == selected_idx:
            stdscr.attron(curses.color_pair(1))
            stdscr.addstr(y, max_x // 2 - 22, f" ► {ruleset.name.ljust(20)} ")
            stdscr.attroff(curses.color_pair(1))
        else:
            stdscr.addstr(y, max_x // 2 - 22, f"   {ruleset.name.ljust(20)} ")

        # Description on same line
        desc = ruleset.get_description()
        # Remove the name from description since we already show it
        desc_parts = desc.split(" | ")[1:]
        desc_short = " | ".join(desc_parts) if desc_parts else ""
        stdscr.addstr(y, max_x // 2 + 2, desc_short[:max_x - max_x // 2 - 4])

    # Custom option
    custom_y = 5 + len(rulesets) * 2
    if custom_y < max_y - 4:
        if selected_idx == len(rulesets):
            stdscr.attron(curses.color_pair(1))
            stdscr.addstr(custom_y, max_x // 2 - 22, f" ► {'Personalizado...'.ljust(20)} ")
            stdscr.attroff(curses.color_pair(1))
        else:
            stdscr.addstr(custom_y, max_x // 2 - 22, f"   {'Personalizado...'.ljust(20)} ")
        stdscr.addstr(custom_y, max_x // 2 + 2, "Configura tus propias reglas")

    # Instructions
    stdscr.addstr(max_y - 3, max_x // 2 - 15, "↑/↓: Navegar")
    stdscr.addstr(max_y - 2, max_x // 2 - 15, "ENTER: Seleccionar | ESC: Salir")


def select_ruleset_curses(stdscr) -> 'Optional[Ruleset]':
    """Interactive ruleset selection"""
    from models.ruleset import ALL_RULESETS
    curses.curs_set(0)
    init_colors()

    rulesets = ALL_RULESETS
    total_options = len(rulesets) + 1  # +1 for Custom
    # Default to Prime Cup (index 2)
    selected_idx = 2

    while True:
        draw_ruleset_menu(stdscr, selected_idx)
        stdscr.refresh()

        key = stdscr.getch()

        if key == 27:  # ESC
            return None
        elif key == curses.KEY_UP:
            selected_idx = max(0, selected_idx - 1)
        elif key == curses.KEY_DOWN:
            selected_idx = min(total_options - 1, selected_idx + 1)
        elif key == 10:  # Enter
            if selected_idx < len(rulesets):
                return rulesets[selected_idx]
            else:
                # Custom ruleset
                custom = select_custom_ruleset_curses(stdscr)
                if custom is not None:
                    return custom
                # If cancelled, stay in ruleset menu


def select_ruleset():
    """Select a ruleset (public wrapper)"""
    return curses.wrapper(select_ruleset_curses)


# =============================================================================
# Custom Ruleset Editor
# =============================================================================

def draw_custom_ruleset_editor(stdscr, config: dict, cursor_idx: int):
    """Draw the custom ruleset editor form"""
    stdscr.clear()
    max_y, max_x = stdscr.getmaxyx()

    # Title
    title_width = 40
    stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
    stdscr.addstr(1, max_x // 2 - title_width // 2, "═" * title_width)
    stdscr.addstr(2, max_x // 2 - 14, " REGLAS PERSONALIZADAS ")
    stdscr.addstr(3, max_x // 2 - title_width // 2, "═" * title_width)
    stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

    fields = [
        ("Nivel Mínimo", "min_level", "number", 1, 100),
        ("Nivel Máximo", "max_level", "number", 1, 100),
        ("Nivel por Defecto", "default_level", "number", 1, 100),
        ("Tamaño del Equipo", "max_team_size", "number", 1, 6),
        ("Límite Suma Niveles", "level_sum_limit", "optional_number", 0, 600),
        ("Legendarios", "allow_legendaries", "toggle", None, None),
        ("Solo Básicos", "basic_pokemon_only", "toggle", None, None),
        ("Sleep Clause", "sleep_clause", "toggle", None, None),
        ("Freeze Clause", "freeze_clause", "toggle", None, None),
        ("OHKO Clause", "ohko_clause", "toggle", None, None),
        ("Evasion Clause", "evasion_clause", "toggle", None, None),
    ]

    for i, (label, key, field_type, min_val, max_val) in enumerate(fields):
        y = 5 + i
        if y >= max_y - 4:
            break

        # Label
        if i == cursor_idx:
            stdscr.attron(curses.color_pair(1))
            stdscr.addstr(y, max_x // 2 - 22, f" ► {label.ljust(22)} ")
            stdscr.attroff(curses.color_pair(1))
        else:
            stdscr.addstr(y, max_x // 2 - 22, f"   {label.ljust(22)} ")

        # Value
        value = config[key]
        if field_type == "toggle":
            val_str = "SÍ" if value else "NO"
            color = curses.color_pair(4) if value else curses.color_pair(6)
            stdscr.attron(color | curses.A_BOLD)
            stdscr.addstr(y, max_x // 2 + 4, f"◄ {val_str:3} ►")
            stdscr.attroff(color | curses.A_BOLD)
        elif field_type == "optional_number":
            if value is None or value == 0:
                stdscr.addstr(y, max_x // 2 + 4, "◄ --- ►")
            else:
                stdscr.addstr(y, max_x // 2 + 4, f"◄ {value:3} ►")
        else:
            stdscr.addstr(y, max_x // 2 + 4, f"◄ {value:3} ►")

    # Confirm option
    confirm_y = 5 + len(fields) + 1
    if confirm_y < max_y - 3:
        if cursor_idx == len(fields):
            stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
            stdscr.addstr(confirm_y, max_x // 2 - 8, " ► CONFIRMAR ")
            stdscr.attroff(curses.color_pair(4) | curses.A_BOLD)
        else:
            stdscr.addstr(confirm_y, max_x // 2 - 8, "   CONFIRMAR ")

    # Instructions
    stdscr.addstr(max_y - 3, max_x // 2 - 20, "↑/↓: Navegar | ←/→: Cambiar valor")
    stdscr.addstr(max_y - 2, max_x // 2 - 20, "ENTER: Confirmar | ESC: Cancelar")


def select_custom_ruleset_curses(stdscr) -> 'Optional[Ruleset]':
    """Interactive custom ruleset editor"""
    from models.ruleset import Ruleset, CupType, BattleClauses
    curses.curs_set(0)
    init_colors()

    # Default config values
    config = {
        "min_level": 1,
        "max_level": 100,
        "default_level": 50,
        "max_team_size": 3,
        "level_sum_limit": None,
        "allow_legendaries": True,
        "basic_pokemon_only": False,
        "sleep_clause": False,
        "freeze_clause": False,
        "ohko_clause": False,
        "evasion_clause": False,
    }

    fields = [
        ("Nivel Mínimo", "min_level", "number", 1, 100),
        ("Nivel Máximo", "max_level", "number", 1, 100),
        ("Nivel por Defecto", "default_level", "number", 1, 100),
        ("Tamaño del Equipo", "max_team_size", "number", 1, 6),
        ("Límite Suma Niveles", "level_sum_limit", "optional_number", 0, 600),
        ("Legendarios", "allow_legendaries", "toggle", None, None),
        ("Solo Básicos", "basic_pokemon_only", "toggle", None, None),
        ("Sleep Clause", "sleep_clause", "toggle", None, None),
        ("Freeze Clause", "freeze_clause", "toggle", None, None),
        ("OHKO Clause", "ohko_clause", "toggle", None, None),
        ("Evasion Clause", "evasion_clause", "toggle", None, None),
    ]

    total_options = len(fields) + 1  # +1 for confirm button
    cursor_idx = 0

    while True:
        draw_custom_ruleset_editor(stdscr, config, cursor_idx)
        stdscr.refresh()

        key = stdscr.getch()

        if key == 27:  # ESC
            return None
        elif key == curses.KEY_UP:
            cursor_idx = max(0, cursor_idx - 1)
        elif key == curses.KEY_DOWN:
            cursor_idx = min(total_options - 1, cursor_idx + 1)
        elif key in (curses.KEY_LEFT, curses.KEY_RIGHT) and cursor_idx < len(fields):
            _, field_key, field_type, min_val, max_val = fields[cursor_idx]
            if field_type == "toggle":
                config[field_key] = not config[field_key]
            elif field_type == "number":
                delta = 1 if key == curses.KEY_RIGHT else -1
                config[field_key] = max(min_val, min(max_val, config[field_key] + delta))
            elif field_type == "optional_number":
                current = config[field_key] or 0
                delta = 5 if key == curses.KEY_RIGHT else -5
                new_val = current + delta
                if new_val <= 0:
                    config[field_key] = None
                else:
                    config[field_key] = min(max_val, new_val)
        elif key == 10:  # Enter
            if cursor_idx == len(fields):
                # Confirm — build the Ruleset
                clauses = BattleClauses(
                    sleep_clause=config["sleep_clause"],
                    freeze_clause=config["freeze_clause"],
                    ohko_clause=config["ohko_clause"],
                    evasion_clause=config["evasion_clause"],
                )
                return Ruleset(
                    name="Custom",
                    cup_type=CupType.CUSTOM,
                    min_level=config["min_level"],
                    max_level=config["max_level"],
                    default_level=config["default_level"],
                    max_team_size=config["max_team_size"],
                    level_sum_limit=config["level_sum_limit"],
                    allow_legendaries=config["allow_legendaries"],
                    basic_pokemon_only=config["basic_pokemon_only"],
                    clauses=clauses,
                )


# =============================================================================
# Pokemon Filtering by Ruleset
# =============================================================================

def filter_pokemon_by_ruleset(pokemon_list: list[str], ruleset) -> list[str]:
    """
    Filter a list of Pokemon names by ruleset restrictions.

    Checks: banned list, legendaries, basic-only, and height/weight.

    Args:
        pokemon_list: List of Pokemon names (lowercase)
        ruleset: Ruleset to filter against

    Returns:
        Filtered list of allowed Pokemon names
    """
    from models.ruleset import BASIC_POKEMON, LEGENDARY_POKEMON

    filtered = []
    for name in pokemon_list:
        name_lower = name.lower()

        # Check banned
        if name_lower in {p.lower() for p in ruleset.banned_pokemon}:
            continue

        # Check allowed whitelist
        if ruleset.allowed_pokemon is not None:
            if name_lower not in {p.lower() for p in ruleset.allowed_pokemon}:
                continue

        # Check legendaries
        if not ruleset.allow_legendaries and name_lower in LEGENDARY_POKEMON:
            continue

        # Check basic-only
        if ruleset.basic_pokemon_only and name_lower not in BASIC_POKEMON:
            continue

        # Check height/weight restrictions
        if ruleset.max_height_m is not None or ruleset.max_weight_kg is not None:
            try:
                from data.data_loader import get_pokemon_physical_data
                physical = get_pokemon_physical_data(name)
                valid, _ = ruleset.validate_pokemon_physical(
                    name, physical['height'], physical['weight']
                )
                if not valid:
                    continue
            except (ValueError, KeyError):
                pass  # If no physical data, allow through

        filtered.append(name)

    return filtered


if __name__ == "__main__":
    # Test the selection UI
    pokemon = interactive_pokemon_selection()
    if pokemon:
        print(f"\nSeleccionaste: {pokemon.name}")
        print(f"Tipos: {[t.value for t in pokemon.types]}")
        print(f"Movimientos: {[m.name for m in pokemon.moves]}")
    else:
        print("Selección cancelada")
