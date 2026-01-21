"""Curses-based interactive selection UI for Pokemon and moves"""

import curses
from typing import Optional
from data.data_loader import (
    get_pokemon_data,
    get_kanto_pokemon_list,
    get_pokemon_moves_gen1,
    get_pokemon_moves_with_source,
    get_pokemon_weaknesses_resistances,
    create_move
)
from models.enums import Type
from models.stats import Stats
from models.pokemon import Pokemon


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

    try:
        poke_data = get_pokemon_data(pokemon_name)
    except:
        return

    # Title
    stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
    stdscr.addstr(0, start_x, "═" * preview_width)
    stdscr.addstr(1, start_x, f" {pokemon_name.upper()} ")
    stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

    # Types
    types = poke_data.get('types', ['normal'])
    stdscr.addstr(3, start_x, "Tipos: ")
    x_offset = start_x + 7
    for t in types:
        color = get_type_color_pair(t)
        stdscr.attron(color | curses.A_BOLD)
        stdscr.addstr(3, x_offset, f"[{t.upper()}]")
        stdscr.attroff(color | curses.A_BOLD)
        x_offset += len(t) + 3

    # Stats
    stats = poke_data.get('stats', {})
    stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
    stdscr.addstr(5, start_x, "ESTADÍSTICAS:")
    stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)

    stat_names = [('hp', 'HP'), ('attack', 'ATK'), ('defense', 'DEF'),
                  ('special-attack', 'SPC'), ('speed', 'SPD')]

    for i, (stat_key, stat_name) in enumerate(stat_names):
        value = stats.get(stat_key, 50)
        bar_length = min(20, value // 8)  # Scale to ~20 chars max

        # Color based on stat value
        if value >= 100:
            color = curses.color_pair(4)  # Green
        elif value >= 70:
            color = curses.color_pair(5)  # Yellow
        else:
            color = curses.color_pair(6)  # Red

        stdscr.addstr(7 + i, start_x, f"{stat_name}: {str(value).rjust(3)} ")
        stdscr.attron(color)
        stdscr.addstr(7 + i, start_x + 10, "█" * bar_length)
        stdscr.attroff(color)

    # Type effectiveness
    type_info = get_pokemon_weaknesses_resistances(types)

    stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
    stdscr.addstr(14, start_x, "DEBILIDADES:")
    stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)

    weaknesses = type_info.get('weaknesses', [])[:6]
    x_off = start_x
    for w in weaknesses:
        color = get_type_color_pair(w)
        stdscr.attron(color)
        if x_off + len(w) + 3 < max_x:
            stdscr.addstr(15, x_off, f"[{w[:3].upper()}]")
        stdscr.attroff(color)
        x_off += 6

    stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
    stdscr.addstr(17, start_x, "RESISTENCIAS:")
    stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)

    resistances = type_info.get('resistances', [])[:6]
    x_off = start_x
    for r in resistances:
        color = get_type_color_pair(r)
        stdscr.attron(color)
        if x_off + len(r) + 3 < max_x:
            stdscr.addstr(18, x_off, f"[{r[:3].upper()}]")
        stdscr.attroff(color)
        x_off += 6

    # Instructions
    stdscr.addstr(max_y - 3, start_x, "↑/↓: Navegar | ENTER: Seleccionar")
    stdscr.addstr(max_y - 2, start_x, "Escribe para buscar | ESC: Salir")


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


if __name__ == "__main__":
    # Test the selection UI
    pokemon = interactive_pokemon_selection()
    if pokemon:
        print(f"\nSeleccionaste: {pokemon.name}")
        print(f"Tipos: {[t.value for t in pokemon.types]}")
        print(f"Movimientos: {[m.name for m in pokemon.moves]}")
    else:
        print("Selección cancelada")
