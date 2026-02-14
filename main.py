import random
import logging
from models.enums import BattleFormat
from engine.team_battle import (
    TeamBattle, BattleAction, Team,
    get_random_ai_action, get_random_forced_switch
)
from settings.battle_config import BattleMode, MovesetMode, BattleSettings

logger = logging.getLogger(__name__)

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
    select_battle_mode,
    select_moveset_mode,
    select_ruleset,
    filter_pokemon_by_ruleset
)


def get_player_action(team: Team, opponent_team: Team) -> BattleAction:
    """Get the player's action through the UI"""
    result = select_battle_action(team, opponent_team)

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
    # Extract clauses from ruleset if available
    clauses = None
    if settings.ruleset and settings.ruleset.clauses.any_active():
        clauses = settings.ruleset.clauses

    battle = TeamBattle(
        player_team, opponent_team, battle_format,
        action_delay=settings.action_delay,
        clauses=clauses
    )

    # Determine action handlers based on battle mode
    if settings.is_autobattle():
        # Both teams controlled by AI — pass clauses for move filtering
        get_player = lambda t, o: get_random_ai_action(t, o, clauses=clauses)
        get_opponent = lambda t, o: get_random_ai_action(t, o, clauses=clauses)
        get_switch = get_random_forced_switch
        logger.info(f"Starting autobattle ({settings.battle_mode.description})")
    else:
        # Player controls their team
        get_player = get_player_action
        get_opponent = lambda t, o: get_random_ai_action(t, o, clauses=clauses)
        get_switch = lambda team: (
            get_player_forced_switch(team) if team == player_team
            else get_random_forced_switch(team)
        )
        logger.info("Starting player vs AI battle")

    winner = battle.run_battle(
        get_player_action=get_player,
        get_opponent_action=get_opponent,
        get_forced_switch=get_switch
    )

    return winner


def create_team_with_moveset(size: int, trainer_name: str, moveset_mode: MovesetMode,
                              ruleset=None) -> Team:
    """Create a random team with movesets based on the selected mode and ruleset"""
    kanto_list = get_kanto_pokemon_list()

    # Filter Pokemon by ruleset restrictions
    if ruleset is not None:
        kanto_list = filter_pokemon_by_ruleset(kanto_list, ruleset)

    selected_names = random.sample(kanto_list, min(size, len(kanto_list)))

    pokemon_list = []
    mode_map = {
        MovesetMode.RANDOM: "random",
        MovesetMode.PRESET: "preset",
        MovesetMode.SMART_RANDOM: "smart_random",
        MovesetMode.MANUAL: "random"  # Fallback for AI teams
    }
    mode_str = mode_map.get(moveset_mode, "random")

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
    print("═" * 50)
    print("       POKÉMON GEN 1 BATTLE SIMULATOR")
    print("═" * 50)

    # Step 1: Select ruleset (replaces format selection)
    print("\nSelecciona las reglas de batalla...")
    ruleset = select_ruleset()

    if ruleset is None:
        logger.info("Selection cancelled by user")
        print("\nSelección cancelada. ¡Hasta luego!")
        return

    # Derive battle format from ruleset
    battle_format = derive_battle_format(ruleset)

    logger.info(f"Ruleset selected: {ruleset.name} ({ruleset.get_description()})")
    print(f"\nReglas: {ruleset.get_description()}")
    print(f"Formato: {battle_format.description}")

    # Step 2: Select battle mode (Player vs AI, Autobattle, Watch)
    print("\nSelecciona el modo de batalla...")
    battle_mode = select_battle_mode()

    if battle_mode is None:
        logger.info("Selection cancelled by user")
        print("\nSelección cancelada. ¡Hasta luego!")
        return

    logger.info(f"Battle mode selected: {battle_mode.description}")
    print(f"\nModo seleccionado: {battle_mode.description}")

    # Step 3: Select moveset mode
    print("\nSelecciona cómo quieres elegir los movimientos...")
    moveset_mode = select_moveset_mode()

    if moveset_mode is None:
        logger.info("Selection cancelled by user")
        print("\nSelección cancelada. ¡Hasta luego!")
        return

    logger.info(f"Moveset mode selected: {moveset_mode.description}")
    print(f"\nModo de movimientos: {moveset_mode.description}")

    # Create battle settings
    if battle_mode == BattleMode.WATCH:
        settings = BattleSettings.for_watch_mode()
    elif battle_mode == BattleMode.AUTOBATTLE:
        settings = BattleSettings.for_autobattle()
    else:
        settings = BattleSettings.default()
    settings.moveset_mode = moveset_mode
    settings.ruleset = ruleset

    # Step 4: Team selection based on mode
    if settings.is_autobattle():
        # Auto-generate both teams for autobattle/watch mode
        print(f"\nGenerando equipos aleatorios...")

        player_team = create_team_with_moveset(
            battle_format.team_size, "Equipo 1", moveset_mode, ruleset=ruleset)
        opponent_team = create_team_with_moveset(
            battle_format.team_size, "Equipo 2", moveset_mode, ruleset=ruleset)

        print(f"\n{player_team.name}:")
        for i, poke in enumerate(player_team.pokemon):
            print(f"  {i+1}. {poke.name} (Lv.{poke.level}) - {', '.join([m.name for m in poke.moves])}")

        print(f"\n{opponent_team.name}:")
        for i, poke in enumerate(opponent_team.pokemon):
            print(f"  {i+1}. {poke.name} (Lv.{poke.level}) - {', '.join([m.name for m in poke.moves])}")

    else:
        # Player selects their team
        if battle_format == BattleFormat.SINGLE:
            # Single Pokemon selection
            print("\nSelecciona tu Pokémon...")

            if moveset_mode == MovesetMode.MANUAL:
                pokemon = interactive_pokemon_selection()
            else:
                # Use curses to select Pokemon, then auto-assign moves
                import curses
                from ui.selection import select_pokemon_curses
                pokemon_name = curses.wrapper(select_pokemon_curses)
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
            # Multi-Pokemon team selection
            print(f"\nSelecciona {battle_format.team_size} Pokémon para tu equipo...")

            if moveset_mode == MovesetMode.MANUAL:
                player_team = interactive_team_selection(battle_format, "Jugador")
            else:
                player_team = interactive_team_selection_with_settings(
                    battle_format, moveset_mode, "Jugador"
                )

            if player_team is None:
                logger.info("Selection cancelled by user")
                print("\nSelección cancelada. ¡Hasta luego!")
                return

            logger.info(f"Player team: {[p.name for p in player_team.pokemon]}")
            print(f"\nTu equipo:")
            for i, poke in enumerate(player_team.pokemon):
                print(f"  {i+1}. {poke.name} (Lv.{poke.level}) - {', '.join([m.name for m in poke.moves])}")

        # Generate opponent team with same moveset mode and ruleset
        print(f"\nGenerando equipo rival...")
        opponent_team = create_team_with_moveset(
            battle_format.team_size, "Oponente", moveset_mode, ruleset=ruleset)

        print(f"\nEquipo rival:")
        for i, poke in enumerate(opponent_team.pokemon):
            print(f"  {i+1}. {poke.name} (Lv.{poke.level}) - {', '.join([m.name for m in poke.moves])}")

    # Step 5: Start the battle
    if settings.is_autobattle():
        print(f"\n{'═' * 50}")
        print(f"  Reglas: {ruleset.name}")
        print(f"  Modo: {battle_mode.description}")
        if ruleset.clauses.any_active():
            print(f"  Cláusulas: {', '.join(ruleset.clauses.get_active_list())}")
        print(f"  Delay entre acciones: {settings.action_delay}s")
        print(f"{'═' * 50}")
        input("\nPresiona ENTER para comenzar la batalla...")
    else:
        if ruleset.clauses.any_active():
            print(f"\nCláusulas activas: {', '.join(ruleset.clauses.get_active_list())}")
        input("\nPresiona ENTER para comenzar la batalla...")

    logger.info("Battle starting")
    run_team_battle(player_team, opponent_team, battle_format, settings)
    logger.info("Battle ended")


if __name__ == "__main__":
    main()
