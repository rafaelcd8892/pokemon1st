import random
import time
from models.enums import Type
from models.stats import Stats
from models.pokemon import Pokemon
from engine.battle import execute_turn, determine_turn_order, apply_end_of_turn_effects
<<<<<<< Updated upstream
=======
from engine.team_battle import (
    TeamBattle, BattleAction,
    create_random_team, get_random_ai_action, get_random_forced_switch
)
from settings.battle_config import BattleMode, MovesetMode, BattleSettings
>>>>>>> Stashed changes

from data.data_loader import (
    get_pokemon_data,
    get_kanto_pokemon_list,
    get_pokemon_moves_gen1,
    get_pokemon_weaknesses_resistances,
    create_move,
    get_moveset_for_pokemon
)

<<<<<<< Updated upstream
from ui.selection import interactive_pokemon_selection


def select_pokemon_from_list():
    """
    Permite al usuario seleccionar un Pokémon de la lista de Kanto usando enter.
    """
    kanto_list = get_kanto_pokemon_list()
    print("Pokémon disponibles (Kanto):")
    for idx, name in enumerate(kanto_list, 1):
        print(f"{idx}. {name.capitalize()}")
    while True:
        try:
            sel = int(input("\nSelecciona el número de Pokémon: "))
            if 1 <= sel <= len(kanto_list):
                name = kanto_list[sel-1]
                break
        except ValueError:
            pass
        print("Opción inválida. Intenta de nuevo.")
    poke_data = get_pokemon_data(name)
    print(f"\nPokémon: {poke_data['name']}")
    print(f"Tipos: {', '.join(poke_data['types'])}")
    # Mostrar debilidades y resistencias
    type_info = get_pokemon_weaknesses_resistances(poke_data['types'])
    print(f"Debilidades: {', '.join(type_info['weaknesses']) if type_info['weaknesses'] else 'Ninguna'}")
    print(f"Resistencias: {', '.join(type_info['resistances']) if type_info['resistances'] else 'Ninguna'}")
    print(f"Inmunidades: {', '.join(type_info['immunities']) if type_info['immunities'] else 'Ninguna'}")
    print("Stats:")
    for stat, value in poke_data['stats'].items():
        print(f"  {stat}: {value}")
    moves_gen1 = get_pokemon_moves_gen1(name)
    print(f"Movimientos Gen 1 disponibles: {', '.join(moves_gen1[:20])} ...")
    moves = []
    while len(moves) < 4:
        move_name = input(f"Selecciona el movimiento {len(moves)+1}: ").strip().lower()
        if move_name not in moves_gen1:
            print("Movimiento no válido para este Pokémon en Gen 1. Intenta de nuevo.")
            continue
        move = create_move(move_name)
        moves.append(move)
    stats = Stats(
        hp=poke_data['stats'].get('hp', 100),
        attack=poke_data['stats'].get('attack', 50),
        defense=poke_data['stats'].get('defense', 50),
        special=poke_data['stats'].get('special-attack', 50),
        speed=poke_data['stats'].get('speed', 50)
    )
    types = [getattr(Type, t.upper(), Type.NORMAL) for t in poke_data['types']]
    return Pokemon(poke_data['name'], types, stats, moves, level=50)

def select_random_pokemon_and_moves():
    """
    Selecciona aleatoriamente un Pokémon y 4 movimientos válidos de Gen 1.
    """
    kanto_list = get_kanto_pokemon_list()
    name = random.choice(kanto_list)
    poke_data = get_pokemon_data(name)
    moves_gen1 = get_pokemon_moves_gen1(name)
    moves_selected = random.sample(moves_gen1, min(4, len(moves_gen1)))
    moves = []
    for move_name in moves_selected:
        move = create_move(move_name)
        moves.append(move)
    stats = Stats(
        hp=poke_data['stats'].get('hp', 100),
        attack=poke_data['stats'].get('attack', 50),
        defense=poke_data['stats'].get('defense', 50),
        special=poke_data['stats'].get('special-attack', 50),
        speed=poke_data['stats'].get('speed', 50)
    )
    types = [getattr(Type, t.upper(), Type.NORMAL) for t in poke_data['types']]
    print(f"Pokémon aleatorio: {poke_data['name'].capitalize()} | Movimientos: {', '.join([m.name for m in moves])}")
    return Pokemon(poke_data['name'], types, stats, moves, level=50)

def run_battle(pokemon1: Pokemon, pokemon2: Pokemon, max_turns: int = 50):
    """Ejecuta una batalla completa"""
    from engine.display import format_pokemon_status
    print("=== BATALLA POKÉMON ===")
    print(format_pokemon_status(pokemon1))
    print(format_pokemon_status(pokemon2))
    
    turn = 1
    while pokemon1.is_alive() and pokemon2.is_alive() and turn <= max_turns:
        print(f"\n--- Turno {turn} ---")
        
        # Determinar orden por speed
        first, second = determine_turn_order(pokemon1, pokemon2)
        
        # Seleccionar movimientos aleatoriamente
        first_move = random.choice(first.moves)
        second_move = random.choice(second.moves)
        
        # Turno del primero
        execute_turn(first, second, first_move)
        time.sleep(3)
        
        # Turno del segundo (si sigue vivo)
        if second.is_alive():
            execute_turn(second, first, second_move)
            time.sleep(3)

        # Apply end of turn effects (Leech Seed, screen expiration, etc.)
        apply_end_of_turn_effects(pokemon1, pokemon2)

        turn += 1
    
    print("\n=== FIN DE LA BATALLA ===")
    if pokemon1.is_alive() and not pokemon2.is_alive():
        print(f"¡{pokemon1.name} gana!")
    elif pokemon2.is_alive() and not pokemon1.is_alive():
        print(f"¡{pokemon2.name} gana!")
    elif pokemon1.is_alive() and pokemon2.is_alive():
        print("¡La batalla terminó en empate por límite de turnos!")
    else:
        print("¡Ambos Pokémon se debilitaron!")
=======
from ui.selection import (
    interactive_pokemon_selection,
    interactive_team_selection,
    interactive_team_selection_with_settings,
    select_battle_format,
    select_battle_action,
    select_switch,
    select_battle_mode,
    select_moveset_mode,
    select_battle_settings,
    create_pokemon_with_moveset
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


def run_team_battle(player_team: Team, opponent_team: Team, battle_format: BattleFormat,
                    settings: BattleSettings):
    """Run a team battle with the new engine"""
    battle = TeamBattle(
        player_team, opponent_team, battle_format,
        action_delay=settings.action_delay
    )

    # Determine action handlers based on battle mode
    if settings.is_autobattle():
        # Both teams controlled by AI
        get_player = get_random_ai_action
        get_opponent = get_random_ai_action
        get_switch = get_random_forced_switch
        logger.info(f"Starting autobattle ({settings.battle_mode.description})")
    else:
        # Player controls their team
        get_player = get_player_action
        get_opponent = get_random_ai_action
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


def create_team_with_moveset(size: int, trainer_name: str, moveset_mode: MovesetMode) -> Team:
    """Create a random team with movesets based on the selected mode"""
    kanto_list = get_kanto_pokemon_list()
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
        poke_data = get_pokemon_data(name)
        moves_selected = get_moveset_for_pokemon(name, mode_str)
        moves = [create_move(m) for m in moves_selected]

        stats = Stats(
            hp=poke_data['stats'].get('hp', 100),
            attack=poke_data['stats'].get('attack', 50),
            defense=poke_data['stats'].get('defense', 50),
            special=poke_data['stats'].get('special-attack', 50),
            speed=poke_data['stats'].get('speed', 50)
        )
        types = [getattr(Type, t.upper(), Type.NORMAL) for t in poke_data['types']]

        pokemon = Pokemon(poke_data['name'], types, stats, moves, level=50)
        pokemon_list.append(pokemon)

        logger.debug(f"Created {name} with moves: {[m.name for m in moves]}")

    return Team(pokemon_list, trainer_name)


def main():
    """Main entry point"""
    logger.info("Starting Pokemon Gen 1 Battle Simulator")
    print("═" * 50)
    print("       POKÉMON GEN 1 BATTLE SIMULATOR")
    print("═" * 50)

    # Step 1: Select battle format
    print("\nSelecciona el formato de batalla...")
    battle_format = select_battle_format()

    if battle_format is None:
        logger.info("Selection cancelled by user")
        print("\nSelección cancelada. ¡Hasta luego!")
        return

    logger.info(f"Battle format selected: {battle_format.description}")
    print(f"\nFormato seleccionado: {battle_format.description}")

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

    # Step 4: Team selection based on mode
    if settings.is_autobattle():
        # Auto-generate both teams for autobattle/watch mode
        print(f"\nGenerando equipos aleatorios...")

        player_team = create_team_with_moveset(battle_format.team_size, "Equipo 1", moveset_mode)
        opponent_team = create_team_with_moveset(battle_format.team_size, "Equipo 2", moveset_mode)

        print(f"\n{player_team.name}:")
        for i, poke in enumerate(player_team.pokemon):
            print(f"  {i+1}. {poke.name} - {', '.join([m.name for m in poke.moves])}")

        print(f"\n{opponent_team.name}:")
        for i, poke in enumerate(opponent_team.pokemon):
            print(f"  {i+1}. {poke.name} - {', '.join([m.name for m in poke.moves])}")

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
                    pokemon = create_pokemon_with_moveset(pokemon_name, moveset_mode)
                else:
                    pokemon = None

            if pokemon is None:
                logger.info("Selection cancelled by user")
                print("\nSelección cancelada. ¡Hasta luego!")
                return

            logger.info(f"Player selected: {pokemon.name} with moves {[m.name for m in pokemon.moves]}")
            print(f"\nTu Pokémon: {pokemon.name}")
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
                print(f"  {i+1}. {poke.name} - {', '.join([m.name for m in poke.moves])}")

        # Generate opponent team with same moveset mode
        print(f"\nGenerando equipo rival...")
        opponent_team = create_team_with_moveset(battle_format.team_size, "Oponente", moveset_mode)

        print(f"\nEquipo rival:")
        for i, poke in enumerate(opponent_team.pokemon):
            print(f"  {i+1}. {poke.name} - {', '.join([m.name for m in poke.moves])}")

    # Step 5: Start the battle
    if settings.is_autobattle():
        print(f"\n{'═' * 50}")
        print(f"  Modo: {battle_mode.description}")
        print(f"  Delay entre acciones: {settings.action_delay}s")
        print(f"{'═' * 50}")
        input("\nPresiona ENTER para comenzar la batalla...")
    else:
        input("\nPresiona ENTER para comenzar la batalla...")

    logger.info("Battle starting")
    run_team_battle(player_team, opponent_team, battle_format, settings)
    logger.info("Battle ended")

>>>>>>> Stashed changes

if __name__ == "__main__":
    print("=== BATALLA POKÉMON GEN 1 ===\n")

    # Use interactive UI for player's Pokemon selection
    pokemon1 = interactive_pokemon_selection()

    if pokemon1 is None:
        print("Selección cancelada. ¡Hasta luego!")
    else:
        print(f"\nTu Pokémon: {pokemon1.name.capitalize()}")
        print(f"Movimientos: {', '.join([m.name for m in pokemon1.moves])}")

        print("\nEl rival será aleatorio...")
        pokemon2 = select_random_pokemon_and_moves()

        input("\nPresiona ENTER para comenzar la batalla...")
        run_battle(pokemon1, pokemon2)