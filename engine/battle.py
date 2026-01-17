import random
from models.pokemon import Pokemon
from models.move import Move
from engine.damage import calculate_damage
from engine.status import apply_status_effects, apply_end_turn_status_damage

def execute_turn(attacker: Pokemon, defender: Pokemon, move: Move):
    """Ejecuta un turno de batalla completo"""
    print(f"\n{attacker.name} usa {move.name}!")
    
    # Chequear PP
    if not move.has_pp():
        print(f"¡No hay PP para {move.name}!")
        return
    
    move.use()
    
    # Chequear efectos de estado
    if not apply_status_effects(attacker):
        return
    
    # Chequear accuracy
    if random.randint(1, 100) > move.accuracy:
        print(f"¡El ataque falló!")
        return
    
    # Calcular daño
    damage, is_critical, effectiveness = calculate_damage(attacker, defender, move)
    
    if damage > 0:
        defender.take_damage(damage)
        
        if is_critical:
            print(f"¡Golpe crítico!")
        
        if effectiveness > 1:
            print(f"¡Es súper efectivo!")
        elif effectiveness < 1 and effectiveness > 0:
            print(f"No es muy efectivo...")
        elif effectiveness == 0:
            print(f"No afecta a {defender.name}...")
        
        print(f"{defender.name} recibe {damage} de daño! (HP: {defender.current_hp}/{defender.max_hp})")
        
        # Aplicar efecto de estado
        if move.status_effect and random.randint(1, 100) <= move.status_chance:
            if defender.apply_status(move.status_effect):
                print(f"¡{defender.name} está {move.status_effect.value}!")
    
    # Daño por estado al final del turno
    apply_end_turn_status_damage(attacker)

def determine_turn_order(pokemon1: Pokemon, pokemon2: Pokemon) -> tuple[Pokemon, Pokemon]:
    """Determina quién ataca primero basado en Speed"""
    if pokemon1.base_stats.speed > pokemon2.base_stats.speed:
        return pokemon1, pokemon2
    elif pokemon2.base_stats.speed > pokemon1.base_stats.speed:
        return pokemon2, pokemon1
    else:
        # En caso de empate, aleatorio
        return random.choice([(pokemon1, pokemon2), (pokemon2, pokemon1)])

