
import random
import time
from models.enums import Type, Status, MoveCategory
from models.stats import Stats
from models.move import Move
from models.pokemon import Pokemon
from engine.battle import execute_turn, determine_turn_order

from pokeapi_client import get_pokemon_data, get_move_data
from pokeapi_kanto import get_kanto_pokemon_list, get_pokemon_moves_gen1
from pokeapi_types import get_pokemon_weaknesses_resistances


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
    for i in range(4):
        move_name = input(f"Selecciona el movimiento {i+1}: ").strip().lower()
        if move_name not in moves_gen1:
            print("Movimiento no válido para este Pokémon en Gen 1. Intenta de nuevo.")
            continue
        move_data = get_move_data(move_name)
        type_enum = getattr(Type, move_data['type'].upper(), Type.NORMAL)
        cat_enum = getattr(MoveCategory, move_data['category'].upper(), MoveCategory.STATUS)
        status_enum = None
        if cat_enum == MoveCategory.STATUS:
            if 'paralysis' in move_name:
                status_enum = Status.PARALYSIS
            elif 'burn' in move_name:
                status_enum = Status.BURN
            elif 'freeze' in move_name:
                status_enum = Status.FREEZE
            elif 'poison' in move_name:
                status_enum = Status.POISON
            elif 'sleep' in move_name:
                status_enum = Status.SLEEP
        move = Move(
            move_data['name'],
            type_enum,
            cat_enum,
            move_data['power'] or 0,
            move_data['accuracy'] or 100,
            move_data['pp'] or 10,
            move_data['pp'] or 10,
            status_enum,
            100 if status_enum else 0
        )
        moves.append(move)
        if len(moves) == 4:
            break
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
        move_data = get_move_data(move_name)
        type_enum = getattr(Type, move_data['type'].upper(), Type.NORMAL)
        cat_enum = getattr(MoveCategory, move_data['category'].upper(), MoveCategory.STATUS)
        status_enum = None
        if cat_enum == MoveCategory.STATUS:
            if 'paralysis' in move_name:
                status_enum = Status.PARALYSIS
            elif 'burn' in move_name:
                status_enum = Status.BURN
            elif 'freeze' in move_name:
                status_enum = Status.FREEZE
            elif 'poison' in move_name:
                status_enum = Status.POISON
            elif 'sleep' in move_name:
                status_enum = Status.SLEEP
        move = Move(
            move_data['name'],
            type_enum,
            cat_enum,
            move_data['power'] or 0,
            move_data['accuracy'] or 100,
            move_data['pp'] or 10,
            move_data['pp'] or 10,
            status_enum,
            100 if status_enum else 0
        )
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

def run_battle(pokemon1: Pokemon, pokemon2: Pokemon, max_turns: int = 10):
    """Ejecuta una batalla completa"""
    print("=== BATALLA POKÉMON ===")
    print(f"{pokemon1.name} (HP: {pokemon1.current_hp}/{pokemon1.max_hp})")
    print(f"{pokemon2.name} (HP: {pokemon2.current_hp}/{pokemon2.max_hp})")
    
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
    print("Selecciona tu Pokémon:")
    pokemon1 = select_pokemon_from_list()
    print("\nEl rival será aleatorio...")
    pokemon2 = select_random_pokemon_and_moves()
    run_battle(pokemon1, pokemon2)