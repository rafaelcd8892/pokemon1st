import random
import time
from models.enums import Type
from models.stats import Stats
from models.pokemon import Pokemon
from engine.battle import execute_turn, determine_turn_order, apply_end_of_turn_effects

from data.data_loader import (
    get_pokemon_data,
    get_kanto_pokemon_list,
    get_pokemon_moves_gen1,
    get_pokemon_weaknesses_resistances,
    create_move
)

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