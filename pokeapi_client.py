import requests

POKEAPI_BASE_URL = "https://pokeapi.co/api/v2/"

def get_pokemon_data(name_or_id):
    """
    Obtiene datos de un Pokémon desde la PokeAPI.
    Retorna dict con nombre, tipos, stats y movimientos.
    """
    url = f"{POKEAPI_BASE_URL}pokemon/{name_or_id}/"
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(f"No se encontró el Pokémon: {name_or_id}")
    data = response.json()
    # Nombre
    name = data["name"].capitalize()
    # Tipos
    types = [t["type"]["name"].capitalize() for t in data["types"]]
    # Stats
    stats = {s["stat"]["name"]: s["base_stat"] for s in data["stats"]}
    # Movimientos
    moves = [m["move"]["name"] for m in data["moves"]]
    return {
        "name": name,
        "types": types,
        "stats": stats,
        "moves": moves
    }

def get_move_data(move_name):
    """
    Obtiene datos de un movimiento desde la PokeAPI.
    Retorna dict con nombre, tipo, categoría, poder, precisión, pp.
    """
    url = f"{POKEAPI_BASE_URL}move/{move_name}/"
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(f"No se encontró el movimiento: {move_name}")
    data = response.json()
    name = data["name"].capitalize()
    type_ = data["type"]["name"].capitalize()
    category = data["damage_class"]["name"].capitalize()
    power = data["power"]
    accuracy = data["accuracy"]
    pp = data["pp"]
    return {
        "name": name,
        "type": type_,
        "category": category,
        "power": power,
        "accuracy": accuracy,
        "pp": pp
    }
