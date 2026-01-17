import random
from models.enums import Type, Status, MoveCategory
from models.stats import Stats
from models.move import Move
from models.pokemon import Pokemon
from engine.battle import execute_turn, determine_turn_order

def create_sample_pokemon():
    """Crea Pokémon de ejemplo para la batalla"""
    # Movimientos de Pikachu
    thunderbolt = Move("Thunderbolt", Type.ELECTRIC, MoveCategory.SPECIAL, 95, 100, 15, 15)
    thunder_wave = Move("Thunder Wave", Type.ELECTRIC, MoveCategory.STATUS, 0, 100, 20, 20, Status.PARALYSIS, 100)
    quick_attack = Move("Quick Attack", Type.NORMAL, MoveCategory.PHYSICAL, 40, 100, 30, 30)
    
    # Movimientos de Blastoise
    surf = Move("Surf", Type.WATER, MoveCategory.SPECIAL, 95, 100, 15, 15)
    ice_beam = Move("Ice Beam", Type.ICE, MoveCategory.SPECIAL, 95, 100, 10, 10, Status.FREEZE, 10)
    hydro_pump = Move("Hydro Pump", Type.WATER, MoveCategory.SPECIAL, 120, 80, 5, 5)
    
    # Crear Pokémon
    pikachu = Pokemon(
        "Pikachu",
        [Type.ELECTRIC],
        Stats(hp=95, attack=85, defense=70, special=85, speed=120),
        [thunderbolt, thunder_wave, quick_attack],
        level=50
    )
    
    blastoise = Pokemon(
        "Blastoise",
        [Type.WATER],
        Stats(hp=158, attack=103, defense=120, special=105, speed=98),
        [surf, ice_beam, hydro_pump],
        level=50
    )
    
    return pikachu, blastoise

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
        
        # Turno del segundo (si sigue vivo)
        if second.is_alive():
            execute_turn(second, first, second_move)
        
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
    pikachu, blastoise = create_sample_pokemon()
    run_battle(pikachu, blastoise)