import logging
from models.enums import BattleFormat
from engine.team_battle import TeamBattle, BattleAction, Team
from settings.battle_config import BattleMode, MovesetMode, BattleSettings, TeamSelectMode
from engine.ai import create_ai, BattleAI, TrainerProfile, TrainerStyle

logger = logging.getLogger(__name__)

from engine.rng import get_rng, RNGContext
from data.data_loader import (
    get_kanto_pokemon_list,
    create_move,
    get_moveset_for_pokemon,
    create_pokemon_with_ruleset
)

from ui.selection import (
    interactive_pokemon_selection,
    interactive_team_selection,
    interactive_team_selection_with_settings,
    select_battle_action,
    select_switch,
    filter_pokemon_by_ruleset
)

from ui.menus import main_menu


# Map TrainerStyle enum to TrainerProfile factory methods
_STYLE_TO_PROFILE = {
    TrainerStyle.BALANCED: TrainerProfile.balanced,
    TrainerStyle.OFFENSIVE: TrainerProfile.offensive,
    TrainerStyle.DEFENSIVE: TrainerProfile.defensive,
    TrainerStyle.STATUS_FOCUSED: TrainerProfile.status_focused,
    # TYPE_SPECIALIST requires types — handled separately
}


def _make_profile(style: TrainerStyle) -> TrainerProfile:
    """Create a TrainerProfile from a TrainerStyle enum value."""
    factory = _STYLE_TO_PROFILE.get(style)
    if factory:
        return factory()
    return TrainerProfile.balanced()


def get_player_action(team: Team, opponent_team: Team, battle_log=None) -> BattleAction:
    """Get the player's action through the UI"""
    result = select_battle_action(team, opponent_team, battle_log=battle_log)

    if result is None:
        # Default to first available move
        for move in team.active_pokemon.moves:
            if move.has_pp():
                return BattleAction.attack(move)
        return BattleAction.attack(team.active_pokemon.moves[0])

    action_type, data = result

    if action_type == "attack":
        move = team.active_pokemon.moves[data]
        return BattleAction.attack(move)
    else:
        # Switch - need to select which Pokemon
        switch_idx = select_switch(team)
        if switch_idx is not None:
            return BattleAction.switch(switch_idx)
        # If cancelled, default to attack
        for move in team.active_pokemon.moves:
            if move.has_pp():
                return BattleAction.attack(move)
        return BattleAction.attack(team.active_pokemon.moves[0])


def get_player_forced_switch(team: Team) -> int:
    """Handle forced switch for player"""
    print(f"\n{team.active_pokemon.name} se debilitó!")
    switch_idx = select_switch(team)
    if switch_idx is not None:
        return switch_idx
    # Default to first available
    available = team.get_available_switches()
    return available[0][0] if available else 0


def derive_battle_format(ruleset) -> BattleFormat:
    """Derive BattleFormat from a ruleset's max_team_size."""
    if ruleset.max_team_size == 1:
        return BattleFormat.SINGLE
    elif ruleset.max_team_size <= 3:
        return BattleFormat.TRIPLE
    else:
        return BattleFormat.FULL


def run_team_battle(player_team: Team, opponent_team: Team, battle_format: BattleFormat,
                    settings: BattleSettings):
    """Run a team battle with the new engine"""
    from engine.events.handlers.buffer import BufferedEventHandler
    from engine.events.bus import get_event_bus

    # Extract clauses from ruleset if available
    clauses = None
    if settings.ruleset and settings.ruleset.clauses.any_active():
        clauses = settings.ruleset.clauses

    battle = TeamBattle(
        player_team, opponent_team, battle_format,
        action_delay=settings.action_delay,
        clauses=clauses
    )

    # Create a buffered handler for the battle log panel
    buffer = BufferedEventHandler(get_event_bus())

    # Create AI instances via the AI framework
    opponent_profile = _make_profile(settings.opponent_trainer_style)
    opponent_ai = create_ai(
        settings.opponent_ai_difficulty, clauses=clauses, profile=opponent_profile
    )

    # Determine action handlers based on battle mode
    if settings.is_autobattle():
        # Both teams controlled by AI
        player_profile = _make_profile(settings.player_trainer_style)
        player_ai = create_ai(
            settings.player_ai_difficulty, clauses=clauses, profile=player_profile
        )
        get_player = player_ai.choose_action
        get_opponent = opponent_ai.choose_action
        get_switch = lambda team: (
            player_ai.choose_forced_switch(team) if team == player_team
            else opponent_ai.choose_forced_switch(team)
        )
        logger.info(f"Starting autobattle ({settings.battle_mode.description})")
    else:
        # Player controls their team — pass battle log for enhanced UI
        get_player = lambda t, o: get_player_action(t, o, battle_log=buffer.get_recent(8))
        get_opponent = opponent_ai.choose_action
        get_switch = lambda team: (
            get_player_forced_switch(team) if team == player_team
            else opponent_ai.choose_forced_switch(team)
        )
        logger.info("Starting player vs AI battle")

    # Build action revision hook for Millennium Eye AI
    ai_instances = [opponent_ai]
    if settings.is_autobattle():
        ai_instances.append(player_ai)

    def _on_actions_chosen(a1, a2):
        """Notify AIs of opponent actions and allow revision."""
        # Notify each AI what the opponent chose
        if settings.is_autobattle():
            player_ai.notify_opponent_action(a2)
            opponent_ai.notify_opponent_action(a1)
            revised1 = player_ai.revise_action()
            revised2 = opponent_ai.revise_action()
            return (revised1 or a1), (revised2 or a2)
        else:
            opponent_ai.notify_opponent_action(a1)
            revised2 = opponent_ai.revise_action()
            return a1, (revised2 or a2)

    # Only pass the hook if any AI supports revision
    needs_hook = any(
        hasattr(ai, 'revise_action') and type(ai).revise_action is not BattleAI.revise_action
        for ai in ai_instances
    )

    winner = battle.run_battle(
        get_player_action=get_player,
        get_opponent_action=get_opponent,
        get_forced_switch=get_switch,
        on_actions_chosen=_on_actions_chosen if needs_hook else None,
    )

    return winner


def create_team_with_moveset(size: int, trainer_name: str, moveset_mode: MovesetMode,
                              ruleset=None, profile: TrainerProfile = None) -> Team:
    """Create a team with movesets based on the selected mode, ruleset, and profile.

    If a non-balanced TrainerProfile is provided, delegates to the
    profile-aware team builder for biased Pokemon/moveset selection.
    """
    mode_map = {
        MovesetMode.RANDOM: "random",
        MovesetMode.PRESET: "preset",
        MovesetMode.SMART_RANDOM: "smart_random",
        MovesetMode.MANUAL: "random"  # Fallback for AI teams
    }
    mode_str = mode_map.get(moveset_mode, "random")

    # Use profile-aware builder when a non-balanced profile is provided
    if profile is not None and profile.style != TrainerStyle.BALANCED:
        from engine.ai.team_builder import build_team_for_profile
        return build_team_for_profile(size, trainer_name, mode_str, profile, ruleset)

    # Standard unbiased path
    kanto_list = get_kanto_pokemon_list()

    # Filter Pokemon by ruleset restrictions
    if ruleset is not None:
        kanto_list = filter_pokemon_by_ruleset(kanto_list, ruleset)

    selected_names = get_rng().sample(kanto_list, min(size, len(kanto_list)), RNGContext.TEAM_GENERATION)

    pokemon_list = []
    for name in selected_names:
        moves_selected = get_moveset_for_pokemon(name, mode_str)
        moves = [create_move(m) for m in moves_selected]

        pokemon = create_pokemon_with_ruleset(name, moves, ruleset=ruleset)
        pokemon_list.append(pokemon)

        logger.debug(f"Created {name} with moves: {[m.name for m in moves]}")

    return Team(pokemon_list, trainer_name)


def main():
    """Main entry point"""
    logger.info("Starting Pokemon Gen 1 Battle Simulator")

    settings = main_menu()
    if settings is None:
        print("\n¡Hasta luego!")
        return

    ruleset = settings.ruleset
    battle_format = settings.battle_format
    moveset_mode = settings.moveset_mode

    # Build profiles for team generation
    player_profile = _make_profile(settings.player_trainer_style)
    opponent_profile = _make_profile(settings.opponent_trainer_style)

    # Team generation based on settings
    if settings.is_autobattle() or settings.team_select_mode == TeamSelectMode.RANDOM:
        # Auto-generate both teams
        team1_name = "Equipo 1" if settings.is_autobattle() else "Jugador"
        team2_name = "Equipo 2" if settings.is_autobattle() else "Oponente"

        print(f"\nGenerando equipos aleatorios...")

        player_team = create_team_with_moveset(
            battle_format.team_size, team1_name, moveset_mode,
            ruleset=ruleset, profile=player_profile)
        opponent_team = create_team_with_moveset(
            battle_format.team_size, team2_name, moveset_mode,
            ruleset=ruleset, profile=opponent_profile)

        print(f"\n{player_team.name}:")
        for i, poke in enumerate(player_team.pokemon):
            print(f"  {i+1}. {poke.name} (Lv.{poke.level}) - {', '.join([m.name for m in poke.moves])}")

        print(f"\n{opponent_team.name}:")
        for i, poke in enumerate(opponent_team.pokemon):
            print(f"  {i+1}. {poke.name} (Lv.{poke.level}) - {', '.join([m.name for m in poke.moves])}")
    else:
        # Player selects their team
        if battle_format == BattleFormat.SINGLE:
            print("\nSelecciona tu Pokémon...")

            if moveset_mode == MovesetMode.MANUAL:
                pokemon = interactive_pokemon_selection()
            else:
                import curses
                from ui.selection import select_pokemon_curses
                eligible = filter_pokemon_by_ruleset(get_kanto_pokemon_list(), ruleset) if ruleset else None
                pokemon_name = curses.wrapper(lambda stdscr: select_pokemon_curses(stdscr, eligible))
                if pokemon_name:
                    moves_selected = get_moveset_for_pokemon(pokemon_name,
                        {"random": "random", "preset": "preset",
                         "smart_random": "smart_random"}.get(moveset_mode.value, "random"))
                    moves = [create_move(m) for m in moves_selected]
                    pokemon = create_pokemon_with_ruleset(pokemon_name, moves, ruleset=ruleset)
                else:
                    pokemon = None

            if pokemon is None:
                logger.info("Selection cancelled by user")
                print("\nSelección cancelada. ¡Hasta luego!")
                return

            logger.info(f"Player selected: {pokemon.name} with moves {[m.name for m in pokemon.moves]}")
            print(f"\nTu Pokémon: {pokemon.name} (Lv.{pokemon.level})")
            print(f"Movimientos: {', '.join([m.name for m in pokemon.moves])}")

            player_team = Team([pokemon], "Jugador")
        else:
            print(f"\nSelecciona {battle_format.team_size} Pokémon para tu equipo...")

            if moveset_mode == MovesetMode.MANUAL:
                player_team = interactive_team_selection(battle_format, "Jugador")
            else:
                player_team = interactive_team_selection_with_settings(
                    battle_format, moveset_mode, "Jugador", ruleset=ruleset
                )

            if player_team is None:
                logger.info("Selection cancelled by user")
                print("\nSelección cancelada. ¡Hasta luego!")
                return

            logger.info(f"Player team: {[p.name for p in player_team.pokemon]}")
            print(f"\nTu equipo:")
            for i, poke in enumerate(player_team.pokemon):
                print(f"  {i+1}. {poke.name} (Lv.{poke.level}) - {', '.join([m.name for m in poke.moves])}")

        # Generate opponent team
        print(f"\nGenerando equipo rival...")
        opponent_team = create_team_with_moveset(
            battle_format.team_size, "Oponente", moveset_mode,
            ruleset=ruleset, profile=opponent_profile)

        print(f"\nEquipo rival:")
        for i, poke in enumerate(opponent_team.pokemon):
            print(f"  {i+1}. {poke.name} (Lv.{poke.level}) - {', '.join([m.name for m in poke.moves])}")

    # Pre-battle summary
    print(f"\n{'═' * 50}")
    print(f"  Reglas: {ruleset.name}")
    print(f"  Modo: {settings.battle_mode.description}")
    if ruleset.clauses.any_active():
        print(f"  Cláusulas: {', '.join(ruleset.clauses.get_active_list())}")
    print(f"  Delay entre acciones: {settings.action_delay}s")
    print(f"{'═' * 50}")
    input("\nPresiona ENTER para comenzar la batalla...")

    logger.info("Battle starting")
    run_team_battle(player_team, opponent_team, battle_format, settings)
    logger.info("Battle ended")


if __name__ == "__main__":
    main()
