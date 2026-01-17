import requests

POKEAPI_BASE_URL = "https://pokeapi.co/api/v2/"

def get_type_relations(type_name):
    """
    Devuelve las debilidades, resistencias e inmunidades de un tipo.
    """
    url = f"{POKEAPI_BASE_URL}type/{type_name.lower()}/"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    relations = data["damage_relations"]
    return {
        "double_damage_from": [t["name"].capitalize() for t in relations["double_damage_from"]],
        "half_damage_from": [t["name"].capitalize() for t in relations["half_damage_from"]],
        "no_damage_from": [t["name"].capitalize() for t in relations["no_damage_from"]]
    }

def get_pokemon_weaknesses_resistances(type_list):
    """
    Recibe una lista de tipos y calcula las debilidades, resistencias e inmunidades combinadas.
    """
    weaknesses = set()
    resistances = set()
    immunities = set()
    for t in type_list:
        rel = get_type_relations(t)
        weaknesses.update(rel["double_damage_from"])
        resistances.update(rel["half_damage_from"])
        immunities.update(rel["no_damage_from"])
    # Si un tipo es debilidad y resistencia, se anulan (neutral)
    weaknesses -= resistances
    weaknesses -= immunities
    resistances -= immunities
    return {
        "weaknesses": sorted(list(weaknesses)),
        "resistances": sorted(list(resistances)),
        "immunities": sorted(list(immunities))
    }
