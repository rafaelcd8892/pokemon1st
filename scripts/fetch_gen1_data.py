#!/usr/bin/env python3
"""
One-time script to fetch Gen 1 Pokemon data from PokeAPI and save to local JSON files.
Run this once to generate the data files, then the app will use local data only.
"""

import json
import requests
import time
from pathlib import Path

POKEAPI_BASE_URL = "https://pokeapi.co/api/v2/"
DATA_DIR = Path(__file__).parent.parent / "data"

# Gen 1 status effects and their chances for specific moves
# This is curated data since PokeAPI doesn't have accurate Gen 1 effect chances
MOVE_STATUS_EFFECTS = {
    # 100% status moves
    "thunder-wave": {"status": "PARALYSIS", "chance": 100},
    "stun-spore": {"status": "PARALYSIS", "chance": 100},
    "glare": {"status": "PARALYSIS", "chance": 100},
    "hypnosis": {"status": "SLEEP", "chance": 100},
    "sleep-powder": {"status": "SLEEP", "chance": 100},
    "sing": {"status": "SLEEP", "chance": 100},
    "lovely-kiss": {"status": "SLEEP", "chance": 100},
    "spore": {"status": "SLEEP", "chance": 100},
    "toxic": {"status": "POISON", "chance": 100},
    "poison-powder": {"status": "POISON", "chance": 100},
    "poison-gas": {"status": "POISON", "chance": 100},
    "confuse-ray": {"status": "CONFUSION", "chance": 100},
    "supersonic": {"status": "CONFUSION", "chance": 100},

    # Damaging moves with status chances
    "body-slam": {"status": "PARALYSIS", "chance": 30},
    "lick": {"status": "PARALYSIS", "chance": 30},
    "thunder": {"status": "PARALYSIS", "chance": 10},
    "thunderbolt": {"status": "PARALYSIS", "chance": 10},
    "thunder-shock": {"status": "PARALYSIS", "chance": 10},
    "thunder-punch": {"status": "PARALYSIS", "chance": 10},
    "fire-blast": {"status": "BURN", "chance": 30},
    "flamethrower": {"status": "BURN", "chance": 10},
    "ember": {"status": "BURN", "chance": 10},
    "fire-punch": {"status": "BURN", "chance": 10},
    "blizzard": {"status": "FREEZE", "chance": 10},
    "ice-beam": {"status": "FREEZE", "chance": 10},
    "ice-punch": {"status": "FREEZE", "chance": 10},
    "poison-sting": {"status": "POISON", "chance": 30},
    "sludge": {"status": "POISON", "chance": 30},
    "smog": {"status": "POISON", "chance": 40},
    "psybeam": {"status": "CONFUSION", "chance": 10},
    "confusion": {"status": "CONFUSION", "chance": 10},
    "dizzy-punch": {"status": "CONFUSION", "chance": 20},
}

# Gen 1 stat-modifying moves
MOVE_STAT_CHANGES = {
    # Attack modifiers
    "swords-dance": {"changes": {"ATTACK": 2}, "target_self": True},
    "sharpen": {"changes": {"ATTACK": 1}, "target_self": True},
    "meditate": {"changes": {"ATTACK": 1}, "target_self": True},
    "growl": {"changes": {"ATTACK": -1}, "target_self": False},

    # Defense modifiers
    "harden": {"changes": {"DEFENSE": 1}, "target_self": True},
    "withdraw": {"changes": {"DEFENSE": 1}, "target_self": True},
    "defense-curl": {"changes": {"DEFENSE": 1}, "target_self": True},
    "acid-armor": {"changes": {"DEFENSE": 2}, "target_self": True},
    "barrier": {"changes": {"DEFENSE": 2}, "target_self": True},
    "leer": {"changes": {"DEFENSE": -1}, "target_self": False},
    "tail-whip": {"changes": {"DEFENSE": -1}, "target_self": False},
    "screech": {"changes": {"DEFENSE": -2}, "target_self": False},

    # Speed modifiers
    "agility": {"changes": {"SPEED": 2}, "target_self": True},
    "string-shot": {"changes": {"SPEED": -1}, "target_self": False},

    # Special modifiers
    "amnesia": {"changes": {"SPECIAL": 2}, "target_self": True},
    "growth": {"changes": {"SPECIAL": 1}, "target_self": True},

    # Accuracy/Evasion modifiers
    "double-team": {"changes": {"EVASION": 1}, "target_self": True},
    "minimize": {"changes": {"EVASION": 1}, "target_self": True},
    "sand-attack": {"changes": {"ACCURACY": -1}, "target_self": False},
    "smokescreen": {"changes": {"ACCURACY": -1}, "target_self": False},
    "flash": {"changes": {"ACCURACY": -1}, "target_self": False},
    "kinesis": {"changes": {"ACCURACY": -1}, "target_self": False},
}


def fetch_kanto_pokemon_list():
    """Fetch all 151 Kanto Pokemon names."""
    print("Fetching Kanto Pokemon list...")
    url = f"{POKEAPI_BASE_URL}pokedex/2/"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return [entry["pokemon_species"]["name"] for entry in data["pokemon_entries"]]


def fetch_pokemon_data(name):
    """Fetch a single Pokemon's data."""
    url = f"{POKEAPI_BASE_URL}pokemon/{name}/"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def fetch_move_data(move_name):
    """Fetch a single move's data."""
    url = f"{POKEAPI_BASE_URL}move/{move_name}/"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    return response.json()


def get_gen1_moves_with_source(pokemon_data):
    """Extract Gen 1 moves from Pokemon data with their learn method."""
    moves = {}  # move_name -> source
    for move in pokemon_data["moves"]:
        for vgd in move["version_group_details"]:
            if vgd["version_group"]["name"] in ["red-blue", "yellow"]:
                move_name = move["move"]["name"]
                method = vgd["move_learn_method"]["name"]

                # Map learn methods to our categories
                if method == "level-up":
                    source = "level-up"
                elif method == "machine":
                    source = "tm"
                else:
                    continue  # Skip other methods for now

                # Prefer level-up over TM if pokemon can learn both ways
                if move_name not in moves or source == "level-up":
                    moves[move_name] = source
    return moves


def get_evolution_chain(species_name):
    """Fetch the evolution chain for a species and return all pre-evolutions."""
    try:
        # First get the species data to find the evolution chain
        url = f"{POKEAPI_BASE_URL}pokemon-species/{species_name}/"
        response = requests.get(url)
        if response.status_code != 200:
            return []
        species_data = response.json()

        # Get the evolution chain
        chain_url = species_data["evolution_chain"]["url"]
        response = requests.get(chain_url)
        if response.status_code != 200:
            return []
        chain_data = response.json()

        # Walk the chain to find pre-evolutions
        pre_evolutions = []
        current = chain_data["chain"]

        def find_in_chain(node, target, path):
            """Recursively find target in evolution chain and return path to it."""
            if node["species"]["name"] == target:
                return path
            for evo in node.get("evolves_to", []):
                result = find_in_chain(evo, target, path + [node["species"]["name"]])
                if result is not None:
                    return result
            return None

        path = find_in_chain(current, species_name, [])
        return path if path else []

    except Exception as e:
        print(f"  Error getting evolution chain for {species_name}: {e}")
        return []


def transform_pokemon(api_data):
    """Transform PokeAPI Pokemon data to our format."""
    stats = {s["stat"]["name"]: s["base_stat"] for s in api_data["stats"]}

    # Convert to Gen 1 format (single Special stat from special-attack)
    return {
        "id": api_data["id"],
        "name": api_data["name"].capitalize(),
        "types": [t["type"]["name"].upper() for t in api_data["types"]],
        "base_stats": {
            "hp": stats.get("hp", 50),
            "attack": stats.get("attack", 50),
            "defense": stats.get("defense", 50),
            "special": stats.get("special-attack", 50),  # Gen 1 uses single Special
            "speed": stats.get("speed", 50)
        }
    }


def transform_move(api_data):
    """Transform PokeAPI move data to our format."""
    move_name = api_data["name"]

    # Get status effect info
    status_info = MOVE_STATUS_EFFECTS.get(move_name, {})
    status_effect = status_info.get("status")
    status_chance = status_info.get("chance", 0)

    # Get stat change info
    stat_info = MOVE_STAT_CHANGES.get(move_name, {})
    stat_changes = stat_info.get("changes")
    target_self = stat_info.get("target_self", False)

    # Map damage class to our category names
    category_map = {
        "physical": "PHYSICAL",
        "special": "SPECIAL",
        "status": "STATUS"
    }

    return {
        "name": api_data["name"].replace("-", " ").title().replace(" ", "-"),
        "type": api_data["type"]["name"].upper(),
        "category": category_map.get(api_data["damage_class"]["name"], "STATUS"),
        "power": api_data["power"] or 0,
        "accuracy": api_data["accuracy"] or 100,
        "pp": api_data["pp"] or 10,
        "status_effect": status_effect,
        "status_chance": status_chance,
        "stat_changes": stat_changes,
        "target_self": target_self
    }


def main():
    DATA_DIR.mkdir(exist_ok=True)

    # Fetch Kanto Pokemon list
    kanto_pokemon = fetch_kanto_pokemon_list()
    print(f"Found {len(kanto_pokemon)} Kanto Pokemon")

    pokemon_list = []
    learnsets = {}  # name -> {move_name: source}
    all_moves = set()

    # First pass: Fetch each Pokemon and their direct moves
    pokemon_data_cache = {}
    for i, name in enumerate(kanto_pokemon):
        print(f"Fetching {name} ({i+1}/{len(kanto_pokemon)})...")
        try:
            data = fetch_pokemon_data(name)
            pokemon_data_cache[name] = data
            pokemon_list.append(transform_pokemon(data))

            # Get Gen 1 moves with source
            gen1_moves = get_gen1_moves_with_source(data)
            learnsets[name] = gen1_moves
            all_moves.update(gen1_moves.keys())

            time.sleep(0.1)  # Be nice to the API
        except Exception as e:
            print(f"  Error fetching {name}: {e}")

    # Second pass: Add moves from pre-evolutions
    print("\nAdding evolution line moves...")
    for name in kanto_pokemon:
        if name not in learnsets:
            continue

        pre_evos = get_evolution_chain(name)
        for pre_evo in pre_evos:
            if pre_evo in learnsets:
                # Add pre-evolution moves as "evolution" source
                for move_name, source in learnsets[pre_evo].items():
                    if move_name not in learnsets[name]:
                        learnsets[name][move_name] = "evolution"
                        all_moves.add(move_name)
        time.sleep(0.05)  # Be nice to the API

    # Sort Pokemon by ID
    pokemon_list.sort(key=lambda p: p["id"])

    # Fetch all unique moves
    print(f"\nFetching {len(all_moves)} unique moves...")
    moves_list = []
    for i, move_name in enumerate(sorted(all_moves)):
        print(f"Fetching move: {move_name} ({i+1}/{len(all_moves)})...")
        try:
            data = fetch_move_data(move_name)
            if data:
                moves_list.append(transform_move(data))
            time.sleep(0.05)  # Be nice to the API
        except Exception as e:
            print(f"  Error fetching move {move_name}: {e}")

    # Sort moves alphabetically
    moves_list.sort(key=lambda m: m["name"])

    # Write JSON files
    print("\nWriting JSON files...")

    with open(DATA_DIR / "pokemon.json", "w", encoding="utf-8") as f:
        json.dump({"pokemon": pokemon_list}, f, indent=2, ensure_ascii=False)
    print(f"  Written: pokemon.json ({len(pokemon_list)} Pokemon)")

    with open(DATA_DIR / "moves.json", "w", encoding="utf-8") as f:
        json.dump({"moves": moves_list}, f, indent=2, ensure_ascii=False)
    print(f"  Written: moves.json ({len(moves_list)} moves)")

    with open(DATA_DIR / "learnsets.json", "w", encoding="utf-8") as f:
        json.dump({"learnsets": learnsets}, f, indent=2, ensure_ascii=False)
    print(f"  Written: learnsets.json ({len(learnsets)} learnsets)")

    # Print some stats
    total_tm = sum(1 for ls in learnsets.values() for s in ls.values() if s == "tm")
    total_evo = sum(1 for ls in learnsets.values() for s in ls.values() if s == "evolution")
    total_level = sum(1 for ls in learnsets.values() for s in ls.values() if s == "level-up")
    print(f"\n  Move breakdown: {total_level} level-up, {total_tm} TM, {total_evo} evolution")

    print("\nDone!")


if __name__ == "__main__":
    main()
