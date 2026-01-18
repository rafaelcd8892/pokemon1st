import random
from models.pokemon import Pokemon
from models.move import Move
from engine.damage import calculate_damage
from engine.status import apply_status_effects, apply_end_turn_status_damage
from engine.stat_modifiers import get_stat_change_message, get_modified_speed

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
        
        print(f"{defender.name} recibe {damage} de daño!")
        print(f"  {defender.get_health_bar()}")
        
        # Aplicar efecto de estado
        if move.status_effect and random.randint(1, 100) <= move.status_chance:
            if defender.apply_status(move.status_effect):
                print(f"¡{defender.name} está {move.status_effect.value}!")

    # Aplicar cambios de stats del movimiento
    if move.stat_changes:
        target = attacker if move.target_self else defender
        for stat, change in move.stat_changes.items():
            actual_change, hit_limit = target.modify_stat_stage(stat, change)
            message = get_stat_change_message(target, stat, actual_change, hit_limit)
            if message:
                print(message)
        # Show updated stat display
        from engine.display import format_stat_stages
        stat_display = format_stat_stages(target)
        if stat_display:
            print(f"  {stat_display}")

    # Daño por estado al final del turno
    apply_end_turn_status_damage(attacker)

def determine_turn_order(pokemon1: Pokemon, pokemon2: Pokemon) -> tuple[Pokemon, Pokemon]:
    """Determina quién ataca primero basado en Speed (con stat stages aplicados)"""
    speed1 = get_modified_speed(pokemon1)
    speed2 = get_modified_speed(pokemon2)

    if speed1 > speed2:
        return pokemon1, pokemon2
    elif speed2 > speed1:
        return pokemon2, pokemon1
    else:
        # En caso de empate, aleatorio
        return random.choice([(pokemon1, pokemon2), (pokemon2, pokemon1)])

