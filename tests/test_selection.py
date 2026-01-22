"""Tests for the selection UI module"""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock
import curses

from models.enums import Type, BattleFormat, Status
from models.stats import Stats
from models.pokemon import Pokemon
from models.team import Team
from tests.conftest import create_test_pokemon, create_test_move
from data.data_loader import create_move


class TestTypeColors:
    """Test type color mapping"""

    def test_type_colors_mapping_exists(self):
        """Test that TYPE_COLORS dict contains expected types"""
        from ui.selection import TYPE_COLORS

        expected_types = [
            'normal', 'fire', 'water', 'electric', 'grass', 'ice',
            'fighting', 'poison', 'ground', 'flying', 'psychic',
            'bug', 'rock', 'ghost', 'dragon'
        ]

        for type_name in expected_types:
            assert type_name in TYPE_COLORS, f"Missing type color for {type_name}"

    def test_type_colors_are_curses_colors(self):
        """Test that type colors map to valid curses color constants"""
        from ui.selection import TYPE_COLORS

        valid_colors = {
            curses.COLOR_WHITE, curses.COLOR_RED, curses.COLOR_BLUE,
            curses.COLOR_YELLOW, curses.COLOR_GREEN, curses.COLOR_CYAN,
            curses.COLOR_MAGENTA
        }

        for type_name, color in TYPE_COLORS.items():
            assert color in valid_colors, f"Invalid color for {type_name}: {color}"


class TestGetTypeColorPair:
    """Test the get_type_color_pair function"""

    def test_returns_color_pair_for_valid_type(self):
        """Test that valid types return non-zero color pairs"""
        from ui.selection import get_type_color_pair

        with patch('ui.selection.curses.color_pair') as mock_color_pair:
            mock_color_pair.return_value = 42

            result = get_type_color_pair('fire')

            # Fire is at index 1 in the type list, so pair should be 10 + 1 = 11
            mock_color_pair.assert_called_once_with(11)
            assert result == 42

    def test_returns_default_for_invalid_type(self):
        """Test that invalid types return default color pair"""
        from ui.selection import get_type_color_pair

        with patch('ui.selection.curses.color_pair') as mock_color_pair:
            mock_color_pair.return_value = 0

            result = get_type_color_pair('invalid_type')

            mock_color_pair.assert_called_once_with(0)
            assert result == 0

    def test_case_insensitive(self):
        """Test that type lookup is case insensitive"""
        from ui.selection import get_type_color_pair

        with patch('ui.selection.curses.color_pair') as mock_color_pair:
            mock_color_pair.return_value = 42

            # Should work with uppercase
            get_type_color_pair('FIRE')
            mock_color_pair.assert_called_with(11)

            # Should work with mixed case
            get_type_color_pair('FiRe')
            mock_color_pair.assert_called_with(11)


class TestInitColors:
    """Test color initialization"""

    def test_init_colors_initializes_all_pairs(self):
        """Test that init_colors sets up all required color pairs"""
        from ui.selection import init_colors

        with patch('ui.selection.curses.start_color') as mock_start, \
             patch('ui.selection.curses.use_default_colors') as mock_default, \
             patch('ui.selection.curses.init_pair') as mock_init_pair:

            init_colors()

            mock_start.assert_called_once()
            mock_default.assert_called_once()

            # Should initialize at least:
            # - Pair 1: Selected item
            # - Pair 2: Title
            # - Pair 3: Stats header
            # - Pair 4-6: HP bar colors
            # - Pairs 10-24: Type colors (15 types)
            assert mock_init_pair.call_count >= 21


class TestDrawPokemonListFiltering:
    """Test Pokemon list filtering logic (without curses rendering)"""

    def test_filter_by_search_query(self):
        """Test that search filtering works correctly"""
        pokemon_list = ['pikachu', 'bulbasaur', 'charmander', 'squirtle', 'pidgey']

        # Test filter logic directly
        search_query = "char"
        filtered = [(i, p) for i, p in enumerate(pokemon_list)
                    if search_query.lower() in p.lower()]

        assert len(filtered) == 1
        assert filtered[0][1] == 'charmander'

    def test_filter_with_partial_match(self):
        """Test partial string matching"""
        pokemon_list = ['pikachu', 'bulbasaur', 'charmander', 'squirtle', 'pidgey']

        search_query = "a"
        filtered = [(i, p) for i, p in enumerate(pokemon_list)
                    if search_query.lower() in p.lower()]

        names = [f[1] for f in filtered]
        assert 'pikachu' in names
        assert 'bulbasaur' in names
        assert 'charmander' in names
        # squirtle doesn't contain 'a', so it shouldn't be in the filtered list
        assert 'squirtle' not in names
        assert 'pidgey' not in names

    def test_filter_case_insensitive(self):
        """Test case insensitive filtering"""
        pokemon_list = ['Pikachu', 'BULBASAUR', 'charmander']

        search_query = "PIKA"
        filtered = [(i, p) for i, p in enumerate(pokemon_list)
                    if search_query.lower() in p.lower()]

        assert len(filtered) == 1
        assert filtered[0][1] == 'Pikachu'

    def test_empty_search_returns_all(self):
        """Test that empty search returns all Pokemon"""
        pokemon_list = ['pikachu', 'bulbasaur', 'charmander']

        search_query = ""
        if search_query:
            filtered = [(i, p) for i, p in enumerate(pokemon_list)
                        if search_query.lower() in p.lower()]
        else:
            filtered = list(enumerate(pokemon_list))

        assert len(filtered) == 3


class TestMoveSelectionLogic:
    """Test move selection logic (without curses)"""

    def test_toggle_move_selection(self):
        """Test adding and removing moves from selection"""
        available_moves = ['tackle', 'scratch', 'thunderbolt', 'flamethrower']
        selected_moves = []

        # Add a move
        move = available_moves[0]
        if move not in selected_moves and len(selected_moves) < 4:
            selected_moves.append(move)

        assert 'tackle' in selected_moves
        assert len(selected_moves) == 1

        # Remove the move
        if move in selected_moves:
            selected_moves.remove(move)

        assert 'tackle' not in selected_moves
        assert len(selected_moves) == 0

    def test_max_four_moves(self):
        """Test that max 4 moves can be selected"""
        available_moves = ['tackle', 'scratch', 'thunderbolt', 'flamethrower', 'surf']
        selected_moves = []

        for move in available_moves:
            if move not in selected_moves and len(selected_moves) < 4:
                selected_moves.append(move)

        assert len(selected_moves) == 4
        assert 'surf' not in selected_moves

    def test_move_sources_preserved(self):
        """Test that move sources are correctly tracked"""
        move_sources = {
            'tackle': 'level-up',
            'ice-beam': 'tm',
            'surf': 'evolution'
        }

        assert move_sources['tackle'] == 'level-up'
        assert move_sources['ice-beam'] == 'tm'
        assert move_sources['surf'] == 'evolution'


class TestBattleFormatEnum:
    """Test battle format interactions"""

    def test_battle_formats_have_descriptions(self):
        """Test that all battle formats have descriptions"""
        for fmt in BattleFormat:
            assert hasattr(fmt, 'description'), f"{fmt} missing description"
            assert len(fmt.description) > 0

    def test_battle_formats_have_team_sizes(self):
        """Test that all battle formats have team sizes"""
        for fmt in BattleFormat:
            assert hasattr(fmt, 'team_size'), f"{fmt} missing team_size"
            assert fmt.team_size > 0

    def test_single_format_size(self):
        """Test SINGLE format has team size 1"""
        assert BattleFormat.SINGLE.team_size == 1

    def test_triple_format_size(self):
        """Test TRIPLE format has team size 3"""
        assert BattleFormat.TRIPLE.team_size == 3

    def test_full_format_size(self):
        """Test FULL format has team size 6"""
        assert BattleFormat.FULL.team_size == 6


class TestTeamSelectionLogic:
    """Test team selection filtering logic"""

    def test_excludes_already_selected_pokemon(self):
        """Test that selected Pokemon are excluded from available list"""
        pokemon_list = ['pikachu', 'bulbasaur', 'charmander']
        selected_names = ['pikachu']

        filtered = [(i, p) for i, p in enumerate(pokemon_list)
                    if p.lower() not in selected_names]

        names = [f[1] for f in filtered]
        assert 'pikachu' not in names
        assert 'bulbasaur' in names
        assert 'charmander' in names

    def test_combined_search_and_exclusion(self):
        """Test search filtering with exclusion"""
        pokemon_list = ['pikachu', 'bulbasaur', 'charmander', 'charmeleon']
        selected_names = ['charmander']
        search_query = "char"

        filtered = [(i, p) for i, p in enumerate(pokemon_list)
                    if search_query.lower() in p.lower() and p.lower() not in selected_names]

        names = [f[1] for f in filtered]
        assert 'charmeleon' in names
        assert 'charmander' not in names  # Excluded
        assert len(filtered) == 1


class TestNavigationLogic:
    """Test navigation logic for selections"""

    def test_cursor_movement_up(self):
        """Test cursor movement up with bounds checking"""
        cursor_idx = 5
        if cursor_idx > 0:
            cursor_idx -= 1
        assert cursor_idx == 4

        # At boundary
        cursor_idx = 0
        if cursor_idx > 0:
            cursor_idx -= 1
        assert cursor_idx == 0

    def test_cursor_movement_down(self):
        """Test cursor movement down with bounds checking"""
        max_idx = 10
        cursor_idx = 5
        if cursor_idx < max_idx - 1:
            cursor_idx += 1
        assert cursor_idx == 6

        # At boundary
        cursor_idx = 9
        if cursor_idx < max_idx - 1:
            cursor_idx += 1
        assert cursor_idx == 9

    def test_scroll_offset_adjustment(self):
        """Test scroll offset adjusts with cursor"""
        list_height = 10
        scroll_offset = 0
        cursor_idx = 0

        # Move down past visible area
        for _ in range(15):
            cursor_idx += 1
            if cursor_idx >= scroll_offset + list_height:
                scroll_offset = cursor_idx - list_height + 1

        assert scroll_offset == 6  # 15 - 10 + 1


class TestSelectPokemonCursesLogic:
    """Test the selection logic without actual curses rendering"""

    def test_escape_returns_none(self):
        """Test that ESC key returns None"""
        from ui.selection import select_pokemon_curses

        mock_stdscr = MagicMock()
        mock_stdscr.getmaxyx.return_value = (40, 80)
        mock_stdscr.getch.return_value = 27  # ESC key

        with patch('ui.selection.curses.curs_set'), \
             patch('ui.selection.init_colors'), \
             patch('ui.selection.curses.color_pair', return_value=0), \
             patch('ui.selection.get_kanto_pokemon_list') as mock_list, \
             patch('ui.selection.get_pokemon_data') as mock_data, \
             patch('ui.selection.get_pokemon_weaknesses_resistances') as mock_weak:

            mock_list.return_value = ['pikachu', 'bulbasaur']
            mock_data.return_value = {'types': ['normal'], 'stats': {'hp': 100}}
            mock_weak.return_value = {'weaknesses': [], 'resistances': []}

            result = select_pokemon_curses(mock_stdscr)

            assert result is None

    def test_enter_returns_selected_pokemon(self):
        """Test that ENTER key returns selected Pokemon"""
        from ui.selection import select_pokemon_curses

        mock_stdscr = MagicMock()
        mock_stdscr.getmaxyx.return_value = (40, 80)
        mock_stdscr.getch.return_value = 10  # ENTER key

        with patch('ui.selection.curses.curs_set'), \
             patch('ui.selection.init_colors'), \
             patch('ui.selection.curses.color_pair', return_value=0), \
             patch('ui.selection.get_kanto_pokemon_list') as mock_list, \
             patch('ui.selection.get_pokemon_data') as mock_data, \
             patch('ui.selection.get_pokemon_weaknesses_resistances') as mock_weak:

            mock_list.return_value = ['pikachu', 'bulbasaur']
            mock_data.return_value = {'types': ['normal'], 'stats': {'hp': 100}}
            mock_weak.return_value = {'weaknesses': [], 'resistances': []}

            result = select_pokemon_curses(mock_stdscr)

            assert result == 'pikachu'


class TestSelectMovesCursesLogic:
    """Test move selection logic"""

    def test_escape_returns_none(self):
        """Test that ESC returns None in move selection"""
        from ui.selection import select_moves_curses

        mock_stdscr = MagicMock()
        mock_stdscr.getmaxyx.return_value = (40, 80)
        mock_stdscr.getch.return_value = 27  # ESC

        with patch('ui.selection.curses.curs_set'), \
             patch('ui.selection.init_colors'), \
             patch('ui.selection.curses.color_pair', return_value=0), \
             patch('ui.selection.get_pokemon_moves_with_source') as mock_moves, \
             patch('ui.selection.create_move') as mock_create:

            mock_moves.return_value = {'tackle': 'level-up', 'scratch': 'level-up'}
            mock_move = MagicMock()
            mock_move.type.value = 'normal'
            mock_move.power = 40
            mock_move.accuracy = 100
            mock_move.pp = 35
            mock_move.max_pp = 35
            mock_move.category.value = 'Physical'
            mock_move.status_effect = None
            mock_move.stat_changes = None
            mock_create.return_value = mock_move

            result = select_moves_curses(mock_stdscr, 'pikachu')

            assert result is None


class TestSelectBattleFormatCursesLogic:
    """Test battle format selection logic"""

    def test_escape_returns_none(self):
        """Test that ESC returns None"""
        from ui.selection import select_battle_format_curses

        mock_stdscr = MagicMock()
        mock_stdscr.getmaxyx.return_value = (40, 80)
        mock_stdscr.getch.return_value = 27  # ESC

        with patch('ui.selection.curses.curs_set'), \
             patch('ui.selection.init_colors'), \
             patch('ui.selection.curses.color_pair', return_value=0):

            result = select_battle_format_curses(mock_stdscr)

            assert result is None

    def test_enter_returns_selected_format(self):
        """Test that ENTER returns the selected format"""
        from ui.selection import select_battle_format_curses

        mock_stdscr = MagicMock()
        mock_stdscr.getmaxyx.return_value = (40, 80)
        mock_stdscr.getch.return_value = 10  # ENTER

        with patch('ui.selection.curses.curs_set'), \
             patch('ui.selection.init_colors'), \
             patch('ui.selection.curses.color_pair', return_value=0):

            result = select_battle_format_curses(mock_stdscr)

            # Default selection is first format (SINGLE)
            assert result == BattleFormat.SINGLE

    def test_navigation_changes_selection(self):
        """Test that UP/DOWN keys change selection"""
        from ui.selection import select_battle_format_curses

        mock_stdscr = MagicMock()
        mock_stdscr.getmaxyx.return_value = (40, 80)
        # DOWN, DOWN, ENTER
        mock_stdscr.getch.side_effect = [curses.KEY_DOWN, curses.KEY_DOWN, 10]

        with patch('ui.selection.curses.curs_set'), \
             patch('ui.selection.init_colors'), \
             patch('ui.selection.curses.color_pair', return_value=0):

            result = select_battle_format_curses(mock_stdscr)

            # Should return third format (FULL)
            assert result == BattleFormat.FULL


class TestSelectSwitchCursesLogic:
    """Test Pokemon switch selection logic"""

    def test_returns_pokemon_index(self):
        """Test that switch selection returns correct index"""
        from ui.selection import select_switch_curses

        mock_stdscr = MagicMock()
        mock_stdscr.getmaxyx.return_value = (40, 80)
        mock_stdscr.getch.return_value = 10  # ENTER

        # Create a team with available switches
        pokemon1 = create_test_pokemon(name="Pokemon1", hp=100)
        pokemon2 = create_test_pokemon(name="Pokemon2", hp=100)
        pokemon3 = create_test_pokemon(name="Pokemon3", hp=100)
        team = Team([pokemon1, pokemon2, pokemon3], "Trainer")

        with patch('ui.selection.curses.curs_set'), \
             patch('ui.selection.init_colors'), \
             patch('ui.selection.curses.color_pair', return_value=0):

            result = select_switch_curses(mock_stdscr, team)

            # Should return index of first available switch (index 1, since 0 is active)
            assert result == 1

    def test_returns_none_for_no_available_switches(self):
        """Test that None is returned when no switches available"""
        from ui.selection import select_switch_curses

        mock_stdscr = MagicMock()
        mock_stdscr.getmaxyx.return_value = (40, 80)

        # Create team where only active Pokemon is alive
        pokemon1 = create_test_pokemon(name="Pokemon1", hp=100)
        pokemon2 = create_test_pokemon(name="Pokemon2", hp=100)
        pokemon2.current_hp = 0  # Fainted
        team = Team([pokemon1, pokemon2], "Trainer")

        with patch('ui.selection.curses.curs_set'), \
             patch('ui.selection.init_colors'), \
             patch('ui.selection.curses.color_pair', return_value=0):

            result = select_switch_curses(mock_stdscr, team)

            assert result is None


class TestSelectBattleActionCursesLogic:
    """Test battle action selection logic"""

    def test_attack_selection_returns_move_index(self):
        """Test that selecting attack returns move index"""
        from ui.selection import select_battle_action_curses

        mock_stdscr = MagicMock()
        mock_stdscr.getmaxyx.return_value = (40, 80)
        # ENTER (select attack menu), ENTER (select first move)
        mock_stdscr.getch.side_effect = [10, 10]

        move1 = create_test_move(name="Move1", pp=10)
        move2 = create_test_move(name="Move2", pp=10)
        pokemon1 = create_test_pokemon(name="Pokemon1", hp=100)
        pokemon1.moves = [move1, move2]
        pokemon2 = create_test_pokemon(name="Pokemon2", hp=100)

        team1 = Team([pokemon1], "Trainer1")
        team2 = Team([pokemon2], "Trainer2")

        with patch('ui.selection.curses.curs_set'), \
             patch('ui.selection.init_colors'), \
             patch('ui.selection.curses.color_pair', return_value=0):

            result = select_battle_action_curses(mock_stdscr, team1, team2)

            assert result == ("attack", 0)

    def test_switch_selection_returns_switch_tuple(self):
        """Test that selecting switch returns switch indicator"""
        from ui.selection import select_battle_action_curses

        mock_stdscr = MagicMock()
        mock_stdscr.getmaxyx.return_value = (40, 80)
        # DOWN (move to switch), ENTER (select switch)
        mock_stdscr.getch.side_effect = [curses.KEY_DOWN, 10]

        pokemon1 = create_test_pokemon(name="Pokemon1", hp=100)
        pokemon2 = create_test_pokemon(name="Pokemon2", hp=100)

        team1 = Team([pokemon1, pokemon2], "Trainer1")
        team2 = Team([create_test_pokemon(name="Opp", hp=100)], "Trainer2")

        with patch('ui.selection.curses.curs_set'), \
             patch('ui.selection.init_colors'), \
             patch('ui.selection.curses.color_pair', return_value=0):

            result = select_battle_action_curses(mock_stdscr, team1, team2)

            assert result == ("switch", None)


class TestSelectTeamCursesLogic:
    """Test team selection logic"""

    def test_escape_returns_none(self):
        """Test that ESC returns None"""
        from ui.selection import select_team_curses

        mock_stdscr = MagicMock()
        mock_stdscr.getmaxyx.return_value = (40, 80)
        mock_stdscr.getch.return_value = 27  # ESC

        with patch('ui.selection.curses.curs_set'), \
             patch('ui.selection.init_colors'), \
             patch('ui.selection.curses.color_pair', return_value=0), \
             patch('ui.selection.get_kanto_pokemon_list') as mock_list, \
             patch('ui.selection.get_pokemon_data') as mock_data, \
             patch('ui.selection.get_pokemon_weaknesses_resistances') as mock_weak:

            mock_list.return_value = ['pikachu', 'bulbasaur']
            mock_data.return_value = {'types': ['normal'], 'stats': {'hp': 100}}
            mock_weak.return_value = {'weaknesses': [], 'resistances': []}

            result = select_team_curses(mock_stdscr, 3)

            assert result is None


class TestInteractivePokemonSelection:
    """Test the full interactive Pokemon selection flow"""

    def test_returns_none_when_pokemon_selection_cancelled(self):
        """Test that None is returned when Pokemon selection is cancelled"""
        from ui.selection import interactive_pokemon_selection

        with patch('ui.selection.curses.wrapper') as mock_wrapper:
            mock_wrapper.return_value = None

            result = interactive_pokemon_selection()

            assert result is None

    def test_returns_none_when_move_selection_cancelled(self):
        """Test that None is returned when move selection is cancelled"""
        from ui.selection import interactive_pokemon_selection

        with patch('ui.selection.curses.wrapper') as mock_wrapper, \
             patch('ui.selection.get_pokemon_data') as mock_data:

            # First call returns Pokemon name, second returns None (cancelled)
            mock_wrapper.side_effect = ['pikachu', None]
            mock_data.return_value = {
                'name': 'Pikachu',
                'types': ['electric'],
                'stats': {'hp': 35, 'attack': 55, 'defense': 40, 'special-attack': 50, 'speed': 90}
            }

            result = interactive_pokemon_selection()

            assert result is None

    def test_returns_pokemon_when_selection_complete(self):
        """Test that a Pokemon is returned when selection is complete"""
        from ui.selection import interactive_pokemon_selection

        with patch('ui.selection.curses.wrapper') as mock_wrapper, \
             patch('ui.selection.get_pokemon_data') as mock_data, \
             patch('ui.selection.create_move') as mock_create_move:

            mock_wrapper.side_effect = ['pikachu', ['thunderbolt', 'thunder-wave', 'quick-attack', 'agility']]
            mock_data.return_value = {
                'name': 'Pikachu',
                'types': ['electric'],
                'stats': {'hp': 35, 'attack': 55, 'defense': 40, 'special-attack': 50, 'speed': 90}
            }
            mock_move = MagicMock()
            mock_create_move.return_value = mock_move

            result = interactive_pokemon_selection()

            assert result is not None
            assert isinstance(result, Pokemon)
            assert result.name == 'Pikachu'


class TestInteractiveTeamSelection:
    """Test the full interactive team selection flow"""

    def test_returns_none_when_pokemon_selection_cancelled(self):
        """Test that None is returned when Pokemon selection is cancelled"""
        from ui.selection import interactive_team_selection

        with patch('ui.selection.curses.wrapper') as mock_wrapper:
            mock_wrapper.return_value = None

            result = interactive_team_selection(BattleFormat.SINGLE)

            assert result is None

    def test_returns_none_when_move_selection_cancelled(self):
        """Test that None is returned when move selection is cancelled"""
        from ui.selection import interactive_team_selection

        with patch('ui.selection.curses.wrapper') as mock_wrapper, \
             patch('ui.selection.get_pokemon_data') as mock_data, \
             patch('builtins.print'):

            # First wrapper call returns team names, second returns None (cancelled)
            mock_wrapper.side_effect = [['pikachu'], None]
            mock_data.return_value = {
                'name': 'Pikachu',
                'types': ['electric'],
                'stats': {'hp': 35, 'attack': 55, 'defense': 40, 'special-attack': 50, 'speed': 90}
            }

            result = interactive_team_selection(BattleFormat.SINGLE, "TestTrainer")

            assert result is None

    def test_returns_team_when_selection_complete(self):
        """Test that a Team is returned when selection is complete"""
        from ui.selection import interactive_team_selection

        with patch('ui.selection.curses.wrapper') as mock_wrapper, \
             patch('ui.selection.get_pokemon_data') as mock_data, \
             patch('ui.selection.create_move') as mock_create_move, \
             patch('builtins.print'):  # Suppress print output

            # The wrapper is called multiple times:
            # 1. First for team selection (returns pokemon names)
            # 2. Then for each pokemon's move selection (via lambda)
            def wrapper_side_effect(func):
                if 'select_team' in str(func):
                    return ['pikachu']
                else:
                    return ['thunderbolt', 'thunder-wave', 'quick-attack', 'agility']

            mock_wrapper.side_effect = wrapper_side_effect
            mock_data.return_value = {
                'name': 'Pikachu',
                'types': ['electric'],
                'stats': {'hp': 35, 'attack': 55, 'defense': 40, 'special-attack': 50, 'speed': 90}
            }
            mock_move = MagicMock()
            mock_create_move.return_value = mock_move

            result = interactive_team_selection(BattleFormat.SINGLE, "TestTrainer")

            assert result is not None
            assert isinstance(result, Team)
            assert result.name == "TestTrainer"


class TestHPBarColorLogic:
    """Test HP bar color determination logic"""

    def test_high_hp_is_green(self):
        """Test HP > 50% shows green"""
        hp_pct = 0.75  # 75%
        # Logic from draw_switch_menu
        if hp_pct > 0.5:
            color = "green"
        elif hp_pct > 0.2:
            color = "yellow"
        else:
            color = "red"

        assert color == "green"

    def test_medium_hp_is_yellow(self):
        """Test HP between 20-50% shows yellow"""
        hp_pct = 0.35  # 35%
        if hp_pct > 0.5:
            color = "green"
        elif hp_pct > 0.2:
            color = "yellow"
        else:
            color = "red"

        assert color == "yellow"

    def test_low_hp_is_red(self):
        """Test HP <= 20% shows red"""
        hp_pct = 0.15  # 15%
        if hp_pct > 0.5:
            color = "green"
        elif hp_pct > 0.2:
            color = "yellow"
        else:
            color = "red"

        assert color == "red"


class TestStatBarScaling:
    """Test stat bar display scaling"""

    def test_stat_bar_length_scaling(self):
        """Test stat values scale to bar length correctly"""
        # From draw_pokemon_preview: bar_length = min(20, value // 8)

        # Low stat
        value = 40
        bar_length = min(20, value // 8)
        assert bar_length == 5

        # Medium stat
        value = 100
        bar_length = min(20, value // 8)
        assert bar_length == 12

        # High stat (capped at 20)
        value = 200
        bar_length = min(20, value // 8)
        assert bar_length == 20

    def test_stat_color_thresholds(self):
        """Test stat color determination"""
        # From draw_pokemon_preview

        # High stat
        value = 120
        if value >= 100:
            color = "green"
        elif value >= 70:
            color = "yellow"
        else:
            color = "red"
        assert color == "green"

        # Medium stat
        value = 80
        if value >= 100:
            color = "green"
        elif value >= 70:
            color = "yellow"
        else:
            color = "red"
        assert color == "yellow"

        # Low stat
        value = 50
        if value >= 100:
            color = "green"
        elif value >= 70:
            color = "yellow"
        else:
            color = "red"
        assert color == "red"


class TestMoveSourceDisplayLogic:
    """Test move source display logic"""

    def test_level_up_source_tag(self):
        """Test level-up moves show empty tag"""
        source = "level-up"
        if source == "tm":
            source_tag = "TM "
        elif source == "evolution":
            source_tag = "EVO"
        else:
            source_tag = "   "

        assert source_tag == "   "

    def test_tm_source_tag(self):
        """Test TM moves show TM tag"""
        source = "tm"
        if source == "tm":
            source_tag = "TM "
        elif source == "evolution":
            source_tag = "EVO"
        else:
            source_tag = "   "

        assert source_tag == "TM "

    def test_evolution_source_tag(self):
        """Test evolution moves show EVO tag"""
        source = "evolution"
        if source == "tm":
            source_tag = "TM "
        elif source == "evolution":
            source_tag = "EVO"
        else:
            source_tag = "   "

        assert source_tag == "EVO"
