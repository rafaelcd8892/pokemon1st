import requests

POKEAPI_BASE_URL = "https://pokeapi.co/api/v2/"


def get_kanto_pokemon_list():
    """
    Devuelve la lista de nombres de Pokémon de la Pokédex de Kanto (Gen 1).
    """
    url = f"{POKEAPI_BASE_URL}pokedex/2/"  # Kanto
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return [entry["pokemon_species"]["name"] for entry in data["pokemon_entries"]]


def get_pokemon_moves_gen1(name_or_id):
    """
    Devuelve los movimientos que un Pokémon puede aprender por nivel en Gen 1 (Red/Blue/Yellow).
    """
    url = f"{POKEAPI_BASE_URL}pokemon/{name_or_id}/"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    moves = []
    for move in data["moves"]:
        for vgd in move["version_group_details"]:
            # Gen 1: red-blue (id=1), yellow (id=2)
            if vgd["version_group"]["name"] in ["red-blue", "yellow"] and vgd["move_learn_method"]["name"] == "level-up":
                moves.append(move["move"]["name"])
    return list(set(moves))
