import random
import time

from logging_config import setup_logging, get_logger

# Initialize logging before other imports
setup_logging()
logger = get_logger(__name__)

from models.enums import Type, BattleFormat
from models.stats import Stats
from models.pokemon import Pokemon
from models.team import Team
from engine.battle import execute_turn, determine_turn_order, apply_end_of_turn_effects
from engine.team_battle import (
    TeamBattle, BattleAction,
    create_random_team, get_random_ai_action, get_random_forced_switch
)

from data.data_loader import (
    get_pokemon_data,
    get_kanto_pokemon_list,
    get_pokemon_moves_gen1,
    get_pokemon_weaknesses_resistances,
    create_move
)

from ui.selection import (
    interactive_pokemon_selection,
    interactive_team_selection,
    select_battle_format,
    select_battle_action,
    select_switch
)


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
    logger.debug(f"Random Pokemon selected: {name}")
    poke_data = get_pokemon_data(name)
    moves_gen1 = get_pokemon_moves_gen1(name)
    moves_selected = random.sample(moves_gen1, min(4, len(moves_gen1)))
    logger.debug(f"Moves selected: {moves_selected}")
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
    """Ejecuta una batalla 1v1 clásica (legacy)"""
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


def run_team_battle(player_team: Team, opponent_team: Team, battle_format: BattleFormat):
    """Run a team battle with the new engine"""
    battle = TeamBattle(player_team, opponent_team, battle_format)

    winner = battle.run_battle(
        get_player_action=get_player_action,
        get_opponent_action=get_random_ai_action,
        get_forced_switch=lambda team: (
            get_player_forced_switch(team) if team == player_team
            else get_random_forced_switch(team)
        )
    )

    return winner


def main():
    """Main entry point"""
    logger.info("Starting Pokemon Gen 1 Battle Simulator")
    print("═" * 50)
    print("       POKÉMON GEN 1 BATTLE SIMULATOR")
    print("═" * 50)

    # Select battle format
    print("\nSelecciona el formato de batalla...")
    battle_format = select_battle_format()

    if battle_format is None:
        logger.info("Selection cancelled by user")
        print("\nSelección cancelada. ¡Hasta luego!")
        return

    logger.info(f"Battle format selected: {battle_format.description}")
    print(f"\nFormato seleccionado: {battle_format.description}")

    # Different flow based on format
    if battle_format == BattleFormat.SINGLE:
        # Legacy 1v1 flow with single Pokemon selection
        print("\nSelecciona tu Pokémon...")
        pokemon = interactive_pokemon_selection()

        if pokemon is None:
            logger.info("Selection cancelled by user")
            print("\nSelección cancelada. ¡Hasta luego!")
            return

        logger.info(f"Player selected: {pokemon.name} with moves {[m.name for m in pokemon.moves]}")
        print(f"\nTu Pokémon: {pokemon.name}")
        print(f"Movimientos: {', '.join([m.name for m in pokemon.moves])}")

        # Create single-Pokemon teams
        player_team = Team([pokemon], "Jugador")
        opponent_team = create_random_team(1, "Oponente")

        print(f"\nEl rival: {opponent_team.active_pokemon.name}")
        print(f"Movimientos: {', '.join([m.name for m in opponent_team.active_pokemon.moves])}")

        input("\nPresiona ENTER para comenzar la batalla...")
        logger.info("Battle starting")

        run_team_battle(player_team, opponent_team, battle_format)

    else:
        # Multi-Pokemon team selection
        print(f"\nSelecciona {battle_format.team_size} Pokémon para tu equipo...")
        player_team = interactive_team_selection(battle_format, "Jugador")

        if player_team is None:
            logger.info("Selection cancelled by user")
            print("\nSelección cancelada. ¡Hasta luego!")
            return

        logger.info(f"Player team: {[p.name for p in player_team.pokemon]}")
        print(f"\nTu equipo:")
        for i, poke in enumerate(player_team.pokemon):
            print(f"  {i+1}. {poke.name} - {', '.join([m.name for m in poke.moves])}")

        # Create random opponent team
        print(f"\nGenerando equipo rival...")
        opponent_team = create_random_team(battle_format.team_size, "Oponente")

        print(f"\nEquipo rival:")
        for i, poke in enumerate(opponent_team.pokemon):
            print(f"  {i+1}. {poke.name} - {', '.join([m.name for m in poke.moves])}")

        input("\nPresiona ENTER para comenzar la batalla...")
        logger.info("Team battle starting")

        run_team_battle(player_team, opponent_team, battle_format)

    logger.info("Battle ended")


if __name__ == "__main__":
    main()
